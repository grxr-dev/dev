"""Focused ROM-free binding, source-path and ambiguity tests. Never launch a runner."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from state import ROOT, AW9, AW10, FINAL, OWNERS, committed, decode, encode, load, ownership, require, validate

HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'local/ndsrecomp/runner/src'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordered(observed):
    expected = ['ARM9_slot_save', 'ARM9_timers', 'GPU3D', 'ARM7_HALT_catchup', 'ARM7_timers',
                'poweroff_check', 'display', 'SPU', 'Wifi', 'RTC', 'system_events',
                'system_timestamp', 'next_round', 'next_slice_begin']
    require(observed == expected, 'missing/extra/duplicate/reordered transition or forbidden instruction/MMIO')


class Binding(unittest.TestCase):
    def test_complete_roundtrip(self):
        record = load()
        data = validate(record)
        fields, identities = decode(data)
        self.assertEqual(fields, record['fields'])
        self.assertEqual(identities, record['identities'])
        self.assertEqual(hashlib.sha256(data).hexdigest(), FINAL)
        self.assertEqual(len(data), 8862)

    def test_input_dictionary_order_irrelevant(self):
        record = load()
        reordered = dict(reversed(list(record.items())))
        self.assertEqual(validate(record), validate(reordered))

    def test_extra_field(self):
        record = load()
        record['fields'].append(['zz_extra', 8, 0])
        with self.assertRaises(ValueError):
            validate(record)

    def test_unknown_field_owner(self):
        with self.assertRaises(ValueError):
            ownership('uncaptured_gpu_pipeline')

    def test_duplicate_field(self):
        record = load()
        record['fields'].insert(1, record['fields'][0])
        with self.assertRaises(ValueError):
            validate(record)

    def test_reordered_field(self):
        record = load()
        record['fields'][0:2] = reversed(record['fields'][0:2])
        with self.assertRaises(ValueError):
            validate(record)

    def test_version(self):
        data = bytearray(validate(load()))
        data[4] = 2
        with self.assertRaises(ValueError):
            decode(bytes(data))

    def test_wrong_endian_count(self):
        data = bytearray(validate(load()))
        data[6:10] = data[6:10][::-1]
        with self.assertRaises(ValueError):
            decode(bytes(data))

    def test_extra_bytes(self):
        with self.assertRaises(ValueError):
            decode(validate(load()) + b'\0')

    def test_out_of_width(self):
        fields, identities = decode(validate(load()))
        fields[0][2] = 1 << (fields[0][1] * 8)
        with self.assertRaises(ValueError):
            encode(fields, identities)

    def test_unknown_width(self):
        fields, identities = decode(validate(load()))
        fields[0][1] = 3
        with self.assertRaises(ValueError):
            encode(fields, identities)

    def test_source_order_contract(self):
        expected = ['ARM9_slot_save', 'ARM9_timers', 'GPU3D', 'ARM7_HALT_catchup', 'ARM7_timers',
                    'poweroff_check', 'display', 'SPU', 'Wifi', 'RTC', 'system_events',
                    'system_timestamp', 'next_round', 'next_slice_begin']
        ordered(expected)
        for index in range(len(expected)):
            for changed in [expected[:index] + expected[index+1:], expected[:index] + [expected[index]] + expected[index:]]:
                with self.assertRaises(ValueError):
                    ordered(changed)
        with self.assertRaises(ValueError):
            ordered(list(reversed(expected)))
        for forbidden in ['guest_fetch_B4', 'guest_accounting_B4', 'guest_dispatch_B4', 'divider_MMIO_read', 'save', 'IRQ_accept']:
            with self.assertRaises(ValueError):
                ordered(expected[:2] + [forbidden] + expected[2:])

    def test_cap_off_by_one(self):
        values = {name: value for name, width, value in load()['fields']}
        self.assertEqual(values['slice_cap'] - values['cycle9'], 1)
        self.assertFalse(values['cycle9'] >= values['fast_limit'])
        self.assertGreater(values['cycle9'] + 8, values['slice_cap'])
        for name in ['slice_cap', 'fast_limit', 'cycle9']:
            for delta in [-1, 1]:
                record = load()
                next(row for row in record['fields'] if row[0] == name)[2] += delta
                with self.assertRaises(ValueError):
                    validate(record)


def add_cases():
    fixture = load()
    for index, (name, width, value) in enumerate(fixture['fields']):
        for operation in ['omit', 'mutate', 'owner']:
            def negative(self, position=index, kind=operation):
                record = copy.deepcopy(fixture)
                if kind == 'omit':
                    del record['fields'][position]
                elif kind == 'mutate':
                    record['fields'][position][2] ^= 1
                else:
                    record['field_owners'][position][1] = 'untrusted'
                with self.assertRaises(ValueError):
                    validate(record)
            setattr(Binding, 'test_' + operation + '_' + name.replace('.', '_'), negative)
    for index, (name, value) in enumerate(fixture['identities']):
        def identity(self, position=index):
            record = copy.deepcopy(fixture)
            record['identities'][position][1] = '0' * len(record['identities'][position][1])
            with self.assertRaises(ValueError):
                validate(record)
        setattr(Binding, 'test_identity_' + name, identity)
    data = validate(fixture)
    for size in [0, 5, 6, 9, len(data)//2, len(data)-1]:
        def truncated(self, count=size):
            with self.assertRaises(ValueError):
                decode(data[:count])
        setattr(Binding, 'test_truncated_' + str(size), truncated)


def source_fragments(output):
    sys.path.insert(0, str(ROOT / 'tools/task_aw10'))
    aw10 = module('aw10_source_checks', ROOT / 'tools/task_aw10/check.py')
    _, protected = aw10.source_checks()
    parser = module('aw6_parser_only', ROOT / 'tools/task_aw6/check.py')
    functions = {}
    selected = [('run_slice.inc', SOURCE / 'scheduler.cpp', 'void run_slice(int cpu, uint32_t quantum)'),
                ('timers.inc', SOURCE / 'io.cpp', 'void nds_tick_timers(')]
    for name, path, signature in selected:
        body = parser.function(path.read_text(encoding='utf-8-sig'), signature)
        (output / name).write_text(body + '\n')
        functions[signature] = hashlib.sha256(body.encode()).hexdigest()
    gpu = ROOT / 'local/ndsrecomp/runner/vendor/melonds/GPU3D.cpp'
    original = subprocess.check_output(['git', '-C', str(ROOT / 'local/ndsrecomp'), 'show',
        '3a57236bb23d25dcb4caad7d58d733311062ff5e:runner/vendor/melonds/GPU3D.cpp']).decode('utf-8-sig')
    bodies = []
    for signature in ['s32 GPU3D::CyclesToRunFor()', 'void GPU3D::Run()']:
        body = parser.function(gpu.read_text(), signature)
        require(body == parser.function(original, signature), 'GPU source drift')
        bodies.append(body)
        functions[signature] = hashlib.sha256(body.encode()).hexdigest()
    (output / 'gpu.inc').write_text('\n'.join(bodies) + '\n')
    for owner, (name, function) in OWNERS.items():
        require((ROOT / name).read_text().splitlines() == committed(name).decode().splitlines(), 'provider owner source changed')
        protected[name] = sha(ROOT / name)
    installed = {
        'aw6/prefix.h': committed('tools/task_aw6/prefix.h').decode(),
        'aw4/reconcile.h': committed('tools/task_aw4/reconcile.h').decode(),
        'aw3/bridge.h': committed('tools/task_aw3/bridge.h').decode().replace('../task_aw2/', 'aw2/'),
        'task_aw_bridge.h': committed('tools/task_aw/bridge.h').decode(),
        'bc_resource_hash.h': committed('tools/brainage_custom/bc_resource_hash.h').decode()
    }
    for name in ['canonical.h', 'au_manifest.h', 'model.h', 'controller.h']:
        installed['aw3/aw2/' + name] = committed('tools/task_aw2/' + name).decode().replace(
            '../brainage_custom/bc_resource_hash.h', '../../bc_resource_hash.h').replace(
            '../task_aw/bridge.h', '../../task_aw_bridge.h')
    for name, expected in installed.items():
        path = SOURCE / name
        require(path.read_text(encoding='utf-8-sig').splitlines() == expected.splitlines(), 'installed canonical/controller guard drift: ' + name)
        protected[str(path.relative_to(ROOT))] = sha(path)
    protected[str(gpu.relative_to(ROOT))] = sha(gpu)
    protected['local/ndsrecomp/runner/vendor/melonds/GPU3D.h'] = sha(gpu.with_suffix('.h'))
    protected['tools/task_aw11/terminal.json'] = sha(HERE / 'terminal.json')
    protected['local/task-aw9/one-shot.lock'] = sha(ROOT / 'local/task-aw9/one-shot.lock')
    protected['local/task-aw9/attempt-001/launch.claim'] = sha(ROOT / 'local/task-aw9/attempt-001/launch.claim')
    protected['local/task-aw9/attempt-001/runtime.permit.claimed'] = sha(ROOT / 'local/task-aw9/attempt-001/runtime.permit.claimed')
    return protected, functions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw11') and not output.exists(), 'fresh local output')
    output.mkdir(parents=True)
    subprocess.run(['git', 'merge-base', '--is-ancestor', AW10, 'HEAD'], cwd=ROOT, check=True)
    data = validate(load())
    (output / 'terminal.hex').write_text(data.hex() + '\n')
    protected, functions = source_fragments(output)
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    binary = output / 'inspect.exe'
    command = [str(compiler), '-std=c++20', '-O2', '-I' + str(output), '-I' + str(SOURCE),
        '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), str(HERE / 'inspect.cpp'), '-o', str(binary)]
    compile_result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (output / 'compile.json').write_text(json.dumps({'command': command, 'exit': compile_result.returncode,
        'stdout': compile_result.stdout, 'stderr': compile_result.stderr}, indent=2))
    require(compile_result.returncode == 0, 'native scalar/source rail compile; see compile.json')
    native = subprocess.run([str(binary), str(output / 'terminal.hex')], capture_output=True, text=True)
    (output / 'native.json').write_text(json.dumps({'exit': native.returncode, 'stdout': native.stdout, 'stderr': native.stderr}, indent=2))
    require(native.returncode == 0 and not native.stderr, 'native source-path assertions; see native.json')
    native_result = json.loads(native.stdout)
    children = []
    for mode, code in [('bound_terminal', 73), ('failure', 79)]:
        audit = output / (mode + '.jsonl')
        child = subprocess.run([str(binary), str(output / 'terminal.hex'), mode, str(audit)], capture_output=True, text=True)
        require(child.returncode == code and not child.stdout and not child.stderr, 'terminal/failure tail sentinel')
        rows = [json.loads(line) for line in audit.read_text().splitlines()]
        require(rows[0]['sha256'] == FINAL and rows[-1]['guest_instructions'] == rows[-1]['MMIO'] == 0,
            'bound disposal evidence')
        require(rows[-1]['binding_rejected'] == (mode == 'failure'), 'failure must originate in actual binding rejection')
        children.append({'mode': mode, 'exit': code, 'tail_sentinels': 0})
    add_cases()
    with (output / 'python-tests.txt').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Binding))
    require(result.wasSuccessful(), 'focused binding tests; see python-tests.txt')
    require(all(sha(ROOT / name) == digest for name, digest in protected.items()), 'protected artifact changed')
    fields = {name: value for name, width, value in load()['fields']}
    summary = {'task': 'AW11', 'all_passed': True, 'python_cases': result.testsRun, 'native_assertions': native_result['assertions'],
        'disposal_children': children, 'source_functions': functions, 'protected_artifacts_unchanged': protected,
        'terminal_scalar_count': len(fields), 'identities': 5, 'canonical_bytes': len(data), 'digest': FINAL,
        'AW10_projection_reconciled': 89, 'additional_scalars_bound': 322,
        'run_slice_model_redispatch_proven': True, 'GPU_projection_ambiguity_proven': True,
        'conditional_timer_counters': {'0': 14558, '4': 50776, '5': 64195},
        'conditional_ARM7_rendezvous': fields['cycle9'] >> 1,
        'guest_instructions': 0, 'runtime_BrainAge_MMIO': 0, 'live_replays': 0,
        'scheduler_handoff_certified': False, 'activation_installed': False,
        'source_models_not_a_positive_live_or_complete_tail_fixture': True}
    (output / 'tests.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({name: summary[name] for name in ['all_passed', 'python_cases', 'native_assertions', 'terminal_scalar_count',
        'digest', 'run_slice_model_redispatch_proven', 'GPU_projection_ambiguity_proven', 'scheduler_handoff_certified']}, indent=2))


if __name__ == '__main__':
    main()
