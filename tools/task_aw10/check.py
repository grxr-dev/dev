"""Offline tests only: Git metadata, source inspection and a ROM-free scalar rail."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from boundary import AUTHORITY, FINAL, ROOT, MAX_CYCLE, certificate, check_projection, committed
from boundary import evidence, instruction_map, no_service_path, prospective, require, status_projection

SOURCE = ROOT / 'local/ndsrecomp/runner/src'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_checks():
    spec = importlib.util.spec_from_file_location('aw6_source_parser', ROOT / 'tools/task_aw6/check.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    _, aw6, _, _ = evidence()
    build = json.loads((ROOT / 'build/task-aw9-once/build.json').read_text())
    live = json.loads(committed('docs/BrainAge_TaskAW9_Result.json'))
    require(build['runner_sha256'] == live['runner_sha256'], 'AW9 source metadata runner binding')
    for name, expected in aw6['runtime_source_sha256'].items():
        path = ROOT / name
        if path.name in ['tier3.cpp', 'task_au_setup.inc']:
            require(sha(path) == build['original_source_hashes'][path.name], 'AW9 installed hook drift: ' + name)
            if path.name == 'tier3.cpp':
                require(sha(path) == sha(ROOT / 'build/task-aw9-once/source/tier3.cpp'), 'AW9 Tier-3 source changed')
        else:
            require(sha(path) == expected, 'runtime source drift: ' + name)
    texts = {name: (SOURCE / name).read_text(encoding='utf-8-sig')
             for name in ['tier3.cpp', 'scheduler.cpp', 'runtime_arm.cpp', 'io.cpp']}
    tier = texts['tier3.cpp']
    anchors = ['const bool poll_exits = g_runtime_cycles >= g_nds_fast_limit;',
               '++g_stats.instructions[', 'runtime_code_cycles(pc & ~1u)',
               'ArmDecoder::decode(g_bus.read32', 'Interpreter::step',
               'g_runtime_cycles += cyc + runtime_deferred_cycles_take();',
               'task_aw::emit(task_aw::Kind::cycle_commit', 'const bool poll_after',
               'task_aw::emit(task_aw::Kind::retired', 'if (poll_after && !ic.cpsr.i',
               'if (poll_after && nds_slice_over())']
    positions = [tier.index(anchor) for anchor in anchors]
    require(positions == sorted(positions), 'Tier-3 access/commit/IRQ/slice ordering')
    require('g_runtime_cycles + ' not in tier[tier.index(anchors[0]):tier.index(anchors[4])],
            'new prospective Tier-3 exit requires re-review')
    scheduler = parser.function(texts['scheduler.cpp'], 'void scheduler_run_round()')
    tail = ['run_slice(0,', 'nds_tick_timers(0,', 'nds_gpu3d_run(',
            'const uint64_t rendezvous', 'run_slice(1, quantum)', 'nds_tick_timers(1,',
            'if (nds_powered_off())', 'nds_tick_display(rendezvous)', 'nds_tick_spu(rendezvous)',
            'nds_wifi_run_events(rendezvous)', 'nds_tick_rtc(rendezvous)',
            'nds_run_system_events(rendezvous)', 'g_sys_timestamp = rendezvous;\n    live_overlay_poll();']
    positions = [scheduler.index(anchor) for anchor in tail]
    require(positions == sorted(positions), 'scheduler tail source order')
    slice_body = parser.function(texts['scheduler.cpp'], 'void run_slice(int cpu, uint32_t quantum)')
    require(slice_body.index('while (g_runtime_cycles < cap') < slice_body.index('runtime_dispatch(pc | t)'),
            'slice redispatch ordering')
    require('if (nds_slice_over()) break;' in slice_body, 'retained-cap slice break')
    require(slice_body.index('g_slot[cpu].cycles = g_runtime_cycles;', slice_body.index('while (g_runtime_cycles < cap'))
            > slice_body.index('runtime_dispatch(pc | t)'), 'slot clock updates only after dispatch return')
    io_read = parser.function(texts['io.cpp'], 'uint32_t nds_io_read(')
    require('math_reg_read32(addr & ~3u)' in io_read and 'finish_div()' not in io_read,
            'math read must not run divider service')
    system_events = parser.function(texts['io.cpp'], 'void nds_run_system_events(')
    require(system_events.index('g_div_deadline <= timestamp') < system_events.index('finish_div();'),
            'divider finish event ordering')
    for name in ['tools/task_aw6/prefix.h', 'tools/task_aw7/integration.h', 'tools/task_aw/bridge.h']:
        require((ROOT / name).read_text().splitlines() == committed(name).decode().splitlines(),
                'prior full-state/readiness/owner/disposal guards changed: ' + name)
    readiness = committed('tools/task_aw6/prefix.h').decode()
    for predicate in ['IRQ acceptance/wakeup eligible', 'irq7.if', 'deferred7', 'timer.', 'rtc_processed',
                      'system_timestamp', 'slice_cap', 'fast_limit', 'hidden.yield']:
        require(predicate in readiness, 'protected readiness predicate missing: ' + predicate)
    interpreter = ROOT / 'local/ndsrecomp/external/arm-recomp-core/common/interpreter.cpp'
    relative = 'common/interpreter.cpp'
    original = subprocess.check_output(['git', '-C', str(interpreter.parents[1]), 'show', 'HEAD:' + relative])
    require(original.decode('utf-8-sig').splitlines() == interpreter.read_text(encoding='utf-8-sig').splitlines(),
            'portable interpreter drift')
    memory = interpreter.read_text()[interpreter.read_text().index('uint8_t access_w = 4;'):]
    require(memory.index('mem_cycles += bus.access_cycles') < memory.index('value = bus.read16(effective_addr);'),
            'data cost precedes read')
    header = ROOT / 'local/ndsrecomp/recompiler/armv4t/runtime_arm.h'
    combine = parser.function(header.read_text(), 'static inline uint32_t arm9_cycle_combine(')
    require(hashlib.sha256(combine.encode()).hexdigest() == aw6['source_function_sha256'][
        'runtime_arm.h:static inline uint32_t arm9_cycle_combine('], 'cycle combiner identity')
    fragments = [parser.function(texts['io.cpp'], 'uint64_t active_system_timestamp()'),
                 parser.function(texts['io.cpp'], 'uint32_t math_reg_read32('),
                 parser.function(texts['runtime_arm.cpp'], 'extern "C" int nds_slice_over('), combine]
    return '\n\n'.join(fragments), {
        str(path.relative_to(ROOT)): sha(path)
        for path in [SOURCE / name for name in texts] + [interpreter, header]
    }


class Bounds(unittest.TestCase):
    def test_exact_negative(self):
        decision = certificate()
        self.assertFalse(decision['dynamic_execution_ready'])
        self.assertEqual(decision['guest_instructions_certified'], 0)
        self.assertEqual(decision['prospective']['overrun'], 7)
        self.assertFalse(decision['full_terminal_snapshot_reconstructed'])

    def test_full_commitment_not_projection_digest(self):
        projection = evidence()[3]
        self.assertNotEqual(hashlib.sha256(json.dumps(projection, sort_keys=True).encode()).hexdigest(), FINAL)

    def test_read_map(self):
        self.assertEqual([row['opcode'] for row in instruction_map()], ['0xE1D100B0', '0xE2100902', '0x1AFFFFFC'])

    def test_projection_exact(self):
        check_projection(evidence()[3], evidence()[3])

    def test_wrong_status(self):
        with self.assertRaisesRegex(ValueError, 'wrong status'):
            status_projection(0x8001, 1708437913, 3416875777, 1)

    def test_wrong_control(self):
        with self.assertRaises(ValueError):
            status_projection(1, 1708437913, 3416875777, 1)

    def test_wrong_deadline(self):
        with self.assertRaises(ValueError):
            status_projection(0x8001, 1708437912, 3416875777, 0x8001)

    def test_due_divider(self):
        with self.assertRaisesRegex(ValueError, 'service boundary'):
            status_projection(0x8001, 1708437913, 1708437913 * 2, 0x8001)

    def test_read_counterfactual(self):
        self.assertEqual(status_projection(0x8001, 1708437913, 3416875777, 0x8001)['active_system_timestamp'], 1708437888)

    def test_cycle_overflow(self):
        with self.assertRaisesRegex(ValueError, 'overflow'):
            prospective(MAX_CYCLE - 7, MAX_CYCLE, 8)

    def test_debt_overflow(self):
        with self.assertRaisesRegex(ValueError, 'overflow'):
            prospective(MAX_CYCLE - 8, MAX_CYCLE, 8, 1)

    def test_unknown_cost(self):
        with self.assertRaises(ValueError):
            prospective(3416875777, 3416875778, 0)

    def test_debt_cannot_rescue(self):
        for debt in [0, 1, 2, 8, 128]:
            self.assertFalse(prospective(3416875777, 3416875778, 8, debt)['strictly_before_cap'])

    def test_required_readiness_not_reconstructed(self):
        decision = certificate()
        self.assertFalse(decision['full_terminal_snapshot_reconstructed'])
        self.assertFalse(decision['dynamic_execution_ready'])
        self.assertEqual(decision['entry']['full_scalar_count'], 411)

    def test_unknown_protected_field_fails(self):
        for name in ['irq9.pending', 'irq7.if', 'slot7.deferred', 'scheduler.next_event',
                     'timer.0.counter', 'rtc_processed', 'hidden.code_pc9']:
            changed = copy.deepcopy(evidence()[3])
            expected = copy.deepcopy(changed)
            changed['scalars'][name] = {'width': 8, 'value': 1}
            with self.assertRaises(ValueError):
                check_projection(changed, expected)

    def test_negative_cycle(self):
        with self.assertRaises(ValueError):
            prospective(-1, 3416875778, 8)

    def test_unexpected_service_eligibility(self):
        with self.assertRaisesRegex(ValueError, 'eligibility'):
            prospective(3416875777, 3416875778, 8, eligible=True)

    def test_hypothetical_ands(self):
        result = 0x8001 & 0x8000
        self.assertEqual(result, 0x8000)
        self.assertEqual((result >> 31, int(result == 0), 0, 0), (0, 0, 0, 0))
        self.assertEqual(0x020019bc + 8 + (-4 * 4), 0x020019b4)


def add_cases():
    projection = evidence()[3]
    for name in projection['scalars']:
        def mutant(self, field=name):
            changed = copy.deepcopy(projection)
            changed['scalars'][field]['value'] ^= 1
            with self.assertRaises(ValueError):
                check_projection(changed, projection)
        setattr(Bounds, 'test_scalar_' + name.replace('.', '_'), mutant)
    for name in ['full_state_commitment'] + list(projection['identities']):
        def identity(self, field=name):
            changed = copy.deepcopy(projection)
            if field == 'full_state_commitment':
                changed[field] = '0' * 64
            else:
                changed['identities'][field] = '0' * len(changed['identities'][field])
            with self.assertRaises(ValueError):
                check_projection(changed, projection)
        setattr(Bounds, 'test_identity_' + name, identity)
    path = ['entry_verified', 'prospective_rejected', 'audit_flush_close', 'nonreturning_disposal']
    for name in ['irq', 'arm7', 'device', 'scheduler', 'divider_completion', 'instruction_fetch',
                 'instruction_accounting', 'dispatch_020019b4', 'shutdown', 'persistence']:
        def extra(self, event=name):
            with self.assertRaises(ValueError):
                no_service_path(path[:2] + [event] + path[2:])
        setattr(Bounds, 'test_forbidden_' + name, extra)
    for index in range(len(path)):
        def missing(self, position=index):
            with self.assertRaises(ValueError):
                no_service_path(path[:position] + path[position + 1:])
        setattr(Bounds, 'test_missing_event_' + str(index), missing)
    for margin in range(11):
        def cap(self, distance=margin):
            result = prospective(3416875777, 3416875777 + distance, 8)
            self.assertEqual(result['strictly_before_cap'], distance > 8)
            self.assertEqual(result['poll_before'], distance == 0)
        setattr(Bounds, 'test_cap_margin_' + str(margin), cap)
    for cost in range(1, 10):
        def timing(self, amount=cost):
            self.assertFalse(prospective(3416875777, 3416875778, amount)['strictly_before_cap'])
        setattr(Bounds, 'test_cost_' + str(cost), timing)
    def ordered(self):
        self.assertTrue(no_service_path(path))
        with self.assertRaises(ValueError):
            no_service_path(list(reversed(path)))
    setattr(Bounds, 'test_ordered_negative_terminal', ordered)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw10') and not output.exists(), 'fresh isolated evidence directory')
    output.mkdir(parents=True)
    subprocess.run(['git', 'merge-base', '--is-ancestor', AUTHORITY, 'HEAD'], cwd=ROOT, check=True)
    fragments, source_hashes = source_checks()
    protected = [ROOT / path for path in source_hashes]
    protected += list((ROOT / 'tools/task_aw7').glob('*.*'))
    protected += [ROOT / 'tools/task_aw6/prefix.h', ROOT / 'tools/task_aw/bridge.h',
                  ROOT / 'local/task-aw9/one-shot.lock', ROOT / 'local/task-aw9/attempt-001/launch.claim',
                  ROOT / 'local/task-aw9/attempt-001/runtime.permit.claimed']
    before = {str(path.relative_to(ROOT)): sha(path) for path in protected}
    (output / 'source.inc').write_text(fragments)
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    executable = output / 'rail.exe'
    command = [str(compiler), '-std=c++20', '-O2', '-I' + str(output),
               str(ROOT / 'tools/task_aw10/rail.cpp'), '-o', str(executable)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
    native = subprocess.run([str(executable)], check=True, capture_output=True, text=True)
    require(native.stderr == 'SHUTDOWN_SENTINEL', 'disabled ordinary destructor behavior')
    native_result = json.loads(native.stdout)
    children = []
    for mode, code in [('success', 73), ('failure', 79)]:
        audit = output / (mode + '.jsonl')
        child = subprocess.run([str(executable), mode, str(audit)], capture_output=True, text=True)
        require(child.returncode == code and not child.stdout and not child.stderr, 'disposal/tail sentinel')
        row = json.loads(audit.read_text())
        require(row['guest_instructions'] == 0, 'synthetic disposal only')
        children.append({'mode': mode, 'exit': code, 'audit': row, 'tail_sentinels': 0})
    add_cases()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Bounds)
    with (output / 'tests.txt').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    require(result.wasSuccessful(), 'ROM-free unit tests; see tests.txt')
    require(all(sha(ROOT / name) == digest for name, digest in before.items()), 'protected inputs changed')
    decision = certificate()
    encoded = json.dumps(decision, sort_keys=True, separators=(',', ':')).encode()
    envelope = {'sha256': hashlib.sha256(encoded).hexdigest(), 'certificate': decision}
    (output / 'certificate.json').write_text(json.dumps(envelope, indent=2) + '\n')
    summary = {'task': 'AW10', 'python_tests': result.testsRun, 'native_scalar_checks': native_result['checks'],
               'disposal_children': children, 'all_passed': True, 'source_identity_and_order_checks': True,
               'protected_inputs_unchanged': before, 'compile_command': command, 'source_hashes': source_hashes,
               'certificate_payload_sha256': envelope['sha256'], 'projection_scalars': len(decision['entry']['scalars']),
               'full_snapshot_reconstructed': False, 'guest_execution': False, 'runtime_BrainAge_MMIO': False,
               'live_replays': 0, 'no_live_audit_or_capture_payload_opened': True,
               'limitations': 'Scalar source/model and negative certificate tests; not full-state provider/scheduler-transition certification'}
    (output / 'tests.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ['python_tests', 'native_scalar_checks', 'projection_scalars',
        'all_passed', 'full_snapshot_reconstructed', 'guest_execution', 'runtime_BrainAge_MMIO', 'certificate_payload_sha256']}, indent=2))


if __name__ == '__main__':
    main()
