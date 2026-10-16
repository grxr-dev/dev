"""Focused ROM-free tests. Only metadata, source extracts and scalar test children."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from model import AUTHORITY, FENCE, GPU, ROOT, STAGES, Ledger, binding, committed
from model import conditional_next, conditional_slice_state, projections, put, require, sha, state, validate, value

HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
CORE, IDENTITIES, GPU_FIELDS, METADATA = binding()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def feed(ledger, row):
    ledger.accept(row['event'], row['core'], IDENTITIES, row['gpu'], ledger.previous)


class Proof(unittest.TestCase):
    def test_binding_and_chain(self):
        validate(CORE, IDENTITIES, GPU_FIELDS)
        self.assertEqual(len(state.encode(CORE, IDENTITIES)), 8862)
        self.assertEqual(state.decode(state.encode(CORE, IDENTITIES)), (CORE, IDENTITIES))
        self.assertEqual(METADATA['ownership']['transcript'][-1]['chain'],
                         '10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4')

    def test_full_projected_tail(self):
        ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
        for row in ledger.plan:
            feed(ledger, row)
        self.assertEqual(len(ledger.finish()), 64)
        final = ledger.plan[-1]['core']
        self.assertEqual(value(final, 'cycle9'), 3416875777)
        self.assertEqual(value(final, 'cycle7'), 1708437888)
        self.assertEqual(value(final, 'deferred7'), 2)
        self.assertEqual(value(final, 'r15'), 0x020019b4)
        self.assertEqual(value(final, 'unwinding'), 1)
        self.assertEqual(value(final, 'slice_cap'), 3416875778)
        self.assertEqual(value(final, 'ordinal9'), value(CORE, 'ordinal9'))
        self.assertEqual(value(final, 'ordinal7'), value(CORE, 'ordinal7'))
        self.assertEqual(value(final, 'service.rtc_due'), 1670410)
        self.assertEqual(value(final, 'service.rtc_processed'), 1670410)
        self.assertEqual(value(final, 'service.display_last'), 1708437888)
        changed = {row[0] for row, old in zip(final, CORE) if row != old}
        self.assertEqual(changed, {'cycle7', 'system_timestamp', 'service.display_last', 'service.rtc_due',
            'timer.0.counter', 'timer.0.accum', 'timer.4.counter', 'timer.4.accum',
            'timer.5.counter', 'timer.5.accum', *[f'timer.{index}.last' for index in range(8)]})

    def test_conditional_new_slice_not_certificate(self):
        final = projections(CORE, IDENTITIES, GPU_FIELDS)[-1]['core']
        result = conditional_next(final)
        self.assertEqual(result['ARM9_target'], 3416875826)
        self.assertEqual(result['quantum'], 49)
        self.assertTrue(result['conditional_only'])
        self.assertFalse(result['fetch_authorized'])
        self.assertEqual(result['deadlines']['div'], 1708437913)

    def test_B4_old_cap_rejects(self):
        self.assertEqual(value(CORE, 'slice_cap') - value(CORE, 'cycle9'), 1)
        self.assertEqual(value(CORE, 'cycle9') + 8 - value(CORE, 'slice_cap'), 7)

    def test_conditional_journal_reset_is_explicit(self):
        final = projections(CORE, IDENTITIES, GPU_FIELDS)[-1]['core']
        new = conditional_slice_state(final)
        self.assertEqual(len(new), 361)
        self.assertEqual(value(new, 'cap.count'), 1)
        self.assertEqual(value(new, 'capture.epoch'), 497)
        self.assertEqual(value(new, 'capture.serial'), 507)
        self.assertEqual(value(new, 'cap.0.observed_before'), 3416875778)
        self.assertEqual(value(new, 'cap.0.quantum'), 49)
        self.assertEqual(value(new, 'fast_limit'), 0)
        self.assertEqual(value(new, 'scheduler.round_epoch'), 1169)
        self.assertEqual(value(new, 'unwinding'), 1)
        self.assertEqual(value(new, 'r15'), 0x020019b4)

    def test_cap_and_epoch_off_by_one(self):
        for name in ['slice_cap', 'fast_limit', 'capture.epoch', 'capture.serial', 'scheduler.round_epoch']:
            for delta in [-1, 1]:
                changed = copy.deepcopy(CORE)
                put(changed, name, value(changed, name) + delta)
                with self.assertRaises(ValueError):
                    validate(changed, IDENTITIES, GPU_FIELDS)

    def test_missing_transcript(self):
        ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
        for row in ledger.plan[:-1]:
            feed(ledger, row)
        with self.assertRaises(ValueError):
            ledger.finish()

    def test_sticky_chain(self):
        ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
        row = ledger.plan[0]
        with self.assertRaises(ValueError):
            ledger.accept(row['event'], row['core'], IDENTITIES, row['gpu'], '0' * 64)
        with self.assertRaises(ValueError):
            feed(ledger, row)


def add_cases():
    for domain, rows in [('core', CORE), ('GPU', GPU_FIELDS)]:
        for index, row in enumerate(rows):
            for operation in ['mutate', 'omit', 'width']:
                def negative(self, position=index, kind=operation, section=domain):
                    core, identities, gpu = copy.deepcopy((CORE, IDENTITIES, GPU_FIELDS))
                    selected = core if section == 'core' else gpu
                    if kind == 'omit':
                        del selected[position]
                    elif kind == 'mutate':
                        selected[position][2] ^= 1
                    else:
                        selected[position][1] = 4 if selected[position][1] == 8 else 8
                    with self.assertRaises(ValueError):
                        validate(core, identities, gpu)
                setattr(Proof, f'test_{domain}_{index}_{operation}', negative)
    for index in range(len(IDENTITIES)):
        def identity(self, position=index):
            changed = copy.deepcopy(IDENTITIES)
            changed[position][1] = '0' * len(changed[position][1])
            with self.assertRaises(ValueError):
                validate(CORE, changed, GPU_FIELDS)
        setattr(Proof, f'test_identity_{index}', identity)
    for index in range(len(STAGES)):
        for operation in ['skip', 'duplicate', 'reorder', 'epoch', 'cap', 'readiness']:
            def transition(self, position=index, kind=operation):
                ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
                for row in ledger.plan[:position]:
                    feed(ledger, row)
                row = copy.deepcopy(ledger.plan[position])
                if kind == 'duplicate':
                    feed(ledger, row)
                elif kind == 'skip':
                    row = copy.deepcopy(ledger.plan[min(position + 1, len(STAGES) - 1)])
                    if position == len(STAGES) - 1:
                        row['event'] = 'next_slice'
                elif kind == 'reorder':
                    row['event'] = STAGES[position - 1]
                else:
                    name = {'epoch': 'capture.epoch', 'cap': 'slice_cap', 'readiness': 'irq7.if'}[kind]
                    put(row['core'], name, value(row['core'], name) + 1)
                with self.assertRaises(ValueError):
                    feed(ledger, row)
                with self.assertRaises(ValueError):
                    ledger.finish()
            setattr(Proof, f'test_stage_{index}_{operation}', transition)
    for forbidden in ['B4_fetch', 'B4_account', 'B4_dispatch', 'MMIO', 'IRQ', 'DMA', 'GPU_command',
                      'ARM7_instruction', 'save', 'new_slice', 'overlay_commit']:
        def extra(self, event=forbidden):
            ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
            for row in ledger.plan:
                feed(ledger, row)
            final = ledger.plan[-1]
            with self.assertRaises(ValueError):
                ledger.accept(event, final['core'], IDENTITIES, final['gpu'], ledger.previous)
        setattr(Proof, 'test_forbidden_' + forbidden, extra)


def sources(output):
    checks = module('aw15_aw11_source', ROOT / 'tools/task_aw11/check.py')
    protected, functions = checks.source_fragments(output)
    parser = module('aw15_parser', ROOT / 'tools/task_aw6/check.py')
    selected = [('spu.inc', 'spu.cpp', 'void nds_tick_spu('),
                ('rtc.inc', 'io.cpp', 'void nds_tick_rtc('),
                ('events.inc', 'io.cpp', 'void nds_run_system_events('),
                ('wifi.inc', 'wifi_net.cpp', 'uint64_t nds_wifi_next_event_time()'),
                ('wifi.inc', 'wifi_net.cpp', 'void nds_wifi_run_events('),
                ('overlay.inc', 'live_overlay.cpp', 'void live_overlay_poll()')]
    selected.extend([('slice_begin.inc', 'runtime_arm.cpp', 'void request_yield_poll()'),
                     ('slice_begin.inc', 'runtime_arm.cpp', 'extern "C" void nds_slice_begin(')])
    fragments = {}
    for destination, name, signature in selected:
        path = SOURCE / name
        text = path.read_text(encoding='utf-8-sig')
        body = parser.function(text, signature)
        if name in ['spu.cpp', 'wifi_net.cpp', 'live_overlay.cpp']:
            pinned = subprocess.check_output(['git', '-C', str(ROOT / 'local/ndsrecomp'), 'show',
                '3a57236bb23d25dcb4caad7d58d733311062ff5e:runner/src/' + name]).decode('utf-8-sig')
            require(body == parser.function(pinned, signature), 'pinned framework body drift: ' + signature)
        historical = ROOT / 'build/task-aw14-once/source' / name
        require(body == parser.function(historical.read_text(encoding='utf-8-sig'), signature), 'AW14 body drift: ' + signature)
        fragments.setdefault(destination, []).append(body)
        functions[signature] = sha(body.encode())
        protected[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        protected[str(historical.relative_to(ROOT))] = sha(historical.read_bytes())
    for name, bodies in fragments.items():
        (output / name).write_text('\n'.join(bodies) + '\n')
    scheduler = (SOURCE / 'scheduler.cpp').read_text(encoding='utf-8-sig')
    historical = (ROOT / 'build/task-aw14-once/source/scheduler.cpp').read_text(encoding='utf-8-sig')
    anchor = '    task_aw::emit(task_aw::Kind::device);\n    nds_tick_timers(0, g_slot[0].cycles);'
    tail = scheduler[scheduler.index(anchor):scheduler.index('\nvoid scheduler_terminal_halt_all')]
    require(tail == historical[historical.index(anchor):historical.index('\nvoid scheduler_terminal_halt_all')], 'AW14 original tail drift')
    functions['scheduler_tail_after_fence'] = sha(tail.encode())
    (output / 'scheduler_tail.txt').write_text(tail, encoding='utf-8')
    expected = ['nds_tick_timers(0,', 'nds_gpu3d_run(', 'const uint64_t rendezvous', 'run_slice(1, quantum)',
                'nds_tick_timers(1,', 'if (nds_powered_off())', 'nds_tick_display(rendezvous)',
                'nds_tick_spu(rendezvous)', 'nds_wifi_run_events(rendezvous)', 'nds_tick_rtc(rendezvous)',
                'nds_run_system_events(rendezvous)', 'g_sys_timestamp = rendezvous;\n    live_overlay_poll();']
    require([tail.index(item) for item in expected] == sorted(tail.index(item) for item in expected), 'service order')
    for signature in ['void nds_tick_display(', 'uint64_t next_scheduled_event_time()',
                      'extern "C" void nds_slice_begin(', 'void request_yield_poll()']:
        name = 'io.cpp' if 'display' in signature else 'scheduler.cpp' if 'event_time' in signature else 'runtime_arm.cpp'
        body = parser.function((SOURCE / name).read_text(encoding='utf-8-sig'), signature)
        require(body == parser.function((ROOT / 'build/task-aw14-once/source' / name).read_text(encoding='utf-8-sig'), signature), 'source relation drift')
        functions[signature] = sha(body.encode())
    owner = (ROOT / 'tools/task_aw12/controller.h').read_text()
    require('stop(true,"AW12 pre-device capture complete; no service/new slice/guest re-entry");' in owner, 'fence terminal changed')
    require('if (active()) fail("AW12 guest fetch/account/dispatch forbidden")' in owner, 'guest firewall changed')
    ledger = (ROOT / 'tools/task_aw6/prefix.h').read_text()
    require('cursor<plan->size(),"chain/order/extra event"' in ledger, 'completed ledger firewall changed')
    overlay = (SOURCE / 'live_overlay.cpp').read_text()
    require('if (!g_live.enabled) return;' in parser.function(overlay, 'void live_overlay_poll()') and
            'commit_one_ready_bank();' in parser.function(overlay, 'void live_overlay_poll_now()'), 'overlay branch proof')
    require(not any('overlay' in row[0] or 'wifi.bridge' in row[0] for row in CORE + GPU_FIELDS), 'new observed binding requires reconsideration')
    for name in ['tools/task_aw12/controller.h', 'tools/task_aw7/integration.h', 'tools/task_aw6/prefix.h',
                 'tools/task_aw14/fence.json', 'tools/task_aw14/permission.h', 'docs/BrainAge_TaskAW14_Result.json']:
        require((ROOT / name).read_bytes() == committed(name), 'guard/evidence drift: ' + name)
        protected[name] = sha((ROOT / name).read_bytes())
    return protected, functions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw15') and not output.exists(), 'fresh local output only')
    output.mkdir(parents=True)
    subprocess.run(['git', 'merge-base', '--is-ancestor', AUTHORITY, 'HEAD'], cwd=ROOT, check=True)
    protected, functions = sources(output)
    (output / 'fence.hex').write_text(state.encode(CORE, IDENTITIES).hex() + '\n')
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    binary = output / 'inspect.exe'
    command = [str(compiler), '-std=c++20', '-O2', '-I' + str(output), '-I' + str(ROOT / 'tools/task_aw11'),
               '-I' + str(SOURCE), '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), str(HERE / 'inspect.cpp'), '-o', str(binary)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (output / 'compile.json').write_text(json.dumps({'command': command, 'exit': built.returncode, 'stderr': built.stderr}, indent=2))
    require(built.returncode == 0, 'source rail compile: see compile.json')
    native = subprocess.run([str(binary), str(output / 'fence.hex')], capture_output=True, text=True)
    (output / 'native.json').write_text(json.dumps({'exit': native.returncode, 'stdout': native.stdout, 'stderr': native.stderr}, indent=2))
    require(native.returncode == 0 and not native.stderr, 'source rail tests: see native.json')
    children = []
    for mode, expected in [('model_stop', 73), ('failure', 79)]:
        audit = output / (mode + '.jsonl')
        child = subprocess.run([str(binary), str(output / 'fence.hex'), mode, str(audit)], capture_output=True, text=True)
        require(child.returncode == expected and not child.stdout and not child.stderr, 'nonreturning model disposal/sentinel')
        events = [json.loads(line) for line in audit.read_text().splitlines()]
        require(events[-1]['guest'] == events[-1]['MMIO'] == 0, 'model no-guest invariant')
        children.append({'mode': mode, 'exit': expected, 'tail_sentinels': 0, 'model_only': True})
    add_cases()
    with (output / 'python-tests.txt').open('w') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Proof))
    require(tested.wasSuccessful(), 'Python tests: see python-tests.txt')
    plan = projections(CORE, IDENTITIES, GPU_FIELDS)
    ledger = Ledger(CORE, IDENTITIES, GPU_FIELDS)
    for row in plan:
        feed(ledger, row)
    summary = {'task': 'AW15', 'classification': 'PARTIAL', 'tests_passed': True,
               'python_cases': tested.testsRun, 'native_assertions': json.loads(native.stdout)['assertions'],
               'disposal_children': children, 'source_functions': functions,
               'entry_core': FENCE, 'entry_GPU': GPU, 'core_scalars': 411, 'identities': 5, 'GPU_scalars': 19,
               'projected_tail': [{key: row[key] for key in ['event', 'core_sha256', 'GPU_sha256']} for row in plan],
               'projected_chain': ledger.finish(), 'conditional_next_slice': conditional_next(plan[-1]['core']),
               'conditional_slice_core_sha256': sha(state.encode(conditional_slice_state(plan[-1]['core']), IDENTITIES)),
               'complete_tail_new_slice_certified': False, 'dynamic_execution_ready': False,
               'runtime_changed': False, 'guest_instructions': 0, 'runtime_BrainAge_MMIO': 0, 'live_replays': 0,
               'blocker': 'No successor ownership phase after terminal AW12 fence/completed AW7 ledger; overlay poll/nullable Wi-Fi bridge auxiliary state not included in immutable fence projection. Conditional cap arithmetic is not an executable tail certificate.'}
    require(all(sha((ROOT / name).read_bytes()) == digest for name, digest in protected.items()), 'protected evidence/source mutation')
    summary['protected_artifacts_unchanged'] = protected
    (output / 'tests.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ['tests_passed', 'python_cases', 'native_assertions', 'classification', 'conditional_next_slice', 'blocker']}, indent=2))


if __name__ == '__main__':
    main()
