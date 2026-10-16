"""ROM-free source-coupled scheduler-fence tests. Never execute a runner."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

from hooks import ROOT, write_overlay

HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
sys.path.insert(0, str(ROOT / 'tools/task_aw11'))
import state


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output):
    prior = module('aw11_sources', ROOT / 'tools/task_aw11/check.py')
    evidence = output / 'source-proof'
    evidence.mkdir()
    protected, functions = prior.source_fragments(evidence)
    overlay = output / 'overlay'
    original, patched, hashes = write_overlay(overlay, SOURCE)
    for name in original:
        protected[str((SOURCE / name).relative_to(ROOT))] = sha(SOURCE / name)
    parser = module('aw12_source_parser', ROOT / 'tools/task_aw6/check.py')
    extract = parser.function
    (output / 'run_slice.inc').write_text(extract(patched['scheduler.cpp'], 'void run_slice(int cpu, uint32_t quantum)') + '\n')
    unwind = [extract(original['runtime_arm.cpp'], signature) for signature in [
        'extern "C" void nds_clear_unwinding(void)', 'void nds_preserve_unwind_state()', 'void nds_restore_unwind_state()']]
    (output / 'runtime_unwind.inc').write_text('\n'.join(unwind) + '\n')
    for owner in ['runtime', 'scheduler']:
        getter = ROOT / ('tools/task_aw3/' + owner + '.inc')
        (output / (owner + '_getter.inc')).write_text(extract(getter.read_text(), 'void ' + owner + '_snapshot(') + '\n')
    for name, source, signature in [('gpu_facade.inc', 'gpu3d.cpp', 'Snapshot runtime_gpu_observation()'),
                                    ('saved_facade.inc', 'runtime_arm.cpp', 'bool runtime_saved_unwind()')]:
        (output / name).write_text(extract(patched[source], signature) + '\n')
    hook = '        if (task_aw12::tier3_exit()) { sync_out(ic); nds_preserve_unwind_state(); task_aw12::preserved(); break; }'
    require(patched['tier3.cpp'].count(hook) == 1, 'exact Tier-3 escape hook')
    require(patched['tier3.cpp'].index(hook) < patched['tier3.cpp'].index('if (poll_after && !ic.cpsr.i'), 'escape dominates IRQ')
    (output / 'tier3_exit.inc').write_text(hook + '\n')
    start = patched['scheduler.cpp'].index('    task_aw12::pre_device_fence();')
    end = patched['scheduler.cpp'].index('    nds_gpu3d_run(g_slot[0].cycles);', start) + len('    nds_gpu3d_run(g_slot[0].cycles);')
    fence = patched['scheduler.cpp'][start:end]
    require(fence.index('pre_device_fence') < fence.index('Kind::device') < fence.index('nds_tick_timers') < fence.index('nds_gpu3d_run'), 'pre-device ordering')
    (output / 'fence.inc').write_text(fence + '\n')
    require(patched['runtime_arm.cpp'].count('task_aw12::Frame aw12_frame(g_static_guard!=nullptr,g_tail_dispatch!=nullptr);') == 1, 'exact dispatch ownership hook')
    gpu_header = ROOT / 'local/ndsrecomp/runner/vendor/melonds/GPU3D.h'
    protected[str(gpu_header.relative_to(ROOT))] = sha(gpu_header)
    fifo = gpu_header.with_name('FIFO.h')
    protected[str(fifo.relative_to(ROOT))] = sha(fifo)
    for name in ['emu_profile.h', 'dispatch_timing.h']:
        protected[str((SOURCE / name).relative_to(ROOT))] = sha(SOURCE / name)
    (output / 'terminal.hex').write_text(state.validate(state.load()).hex())
    readonly = [name for name, owner in state.load()['field_owners'] if owner in ['bus', 'io', 'cp15']]
    require(len(readonly) == 267, 'immutable metadata ownership partition')
    (output / 'immutable_keys.inc').write_text(',\n'.join(json.dumps(name) for name in readonly) + '\n')
    audit = ROOT / 'local/task-aw9/attempt-001/capture.jsonl'
    require(sha(audit) == 'cfa3acc3e55bd2abf8504f662ded00ac4ea14c3fa617a89b9f3ae6fc0e545f8b', 'immutable historical audit')
    protected[str(audit.relative_to(ROOT))] = sha(audit)
    records = [json.loads(line) for line in audit.read_text().splitlines()]
    first = next(record for record in records if record.get('event') == 'canonical_snapshot')
    initial = bytes.fromhex(first['canonical_hex'])
    require(hashlib.sha256(initial).hexdigest() == '0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c', 'authenticated 361-field historical entry')
    (output / 'initial.hex').write_text(initial.hex())
    return protected, functions, hashes, overlay


def run(command, output, name):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
    (output / (name + '.json')).write_text(json.dumps({'command': [str(item) for item in command],
        'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2))
    return result


def inspect_audit(path, success):
    records = [json.loads(line) for line in path.read_text().splitlines()]
    require(records and records[-1]['event'] == ('terminal' if success else 'failure'), 'flushed terminal/failure audit')
    require(not any('SENTINEL' in line for line in path.read_text().splitlines()), 'no audit sentinel')
    if not success:
        return {'reason': records[-1].get('reason')}
    expected = ['yield_requested', 'tier3_exit', 'unwind_preserved', 'slice_consumed', 'slot_saved',
                'pre_device_fence', 'gpu_observed', 'scheduler_admitted_capture_only']
    types = ['canonical_snapshot', 'observation']
    for label in expected:
        types.append('canonical_snapshot')
        if label in ['gpu_observed', 'scheduler_admitted_capture_only']:
            types.append('gpu_snapshot')
        types.append(label)
    types.append('terminal')
    require([record['event'] for record in records] == types, 'exact complete audit record order')
    previous = state.FINAL
    core = None
    gpu = b'AW2S\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    labels = []
    observed = []
    empty = state.encode([], [])
    old_events = 0
    bound_frame = None
    for record in records:
        if record['event'] == 'canonical_snapshot':
            core = bytes.fromhex(record['canonical_hex'])
        elif record['event'] == 'gpu_snapshot':
            gpu = bytes.fromhex(record['canonical_hex'])
            require(hashlib.sha256(gpu).hexdigest() == record['sha256'], 'GPU canonical digest')
        elif record['event'] in expected:
            index = len(labels)
            require(record['event'] == expected[index] and record['index'] == index and
                    record['phase'] == [1, 2, 3, 4, 5, 6, 6, 7][index], 'exact fence transcript order/phase')
            if bound_frame is None:
                bound_frame = record['frame']
            require(record['previous'] == previous and record['ticket'] == 1 and record['frame'] == bound_frame and bound_frame > 0, 'chained one-use identity')
            require(record['frame_depth'] == (1 if index < 3 else 0) and record['saved_valid'] == (index == 2), 'preserved ownership/latch')
            extra = gpu if index >= 6 else empty
            material = previous.encode() + core + extra
            material += struct.pack('<QQBBIQ', index, 1, record['phase'], record['saved_valid'], record['frame_depth'], bound_frame)
            encoded = record['event'].encode()
            material += struct.pack('<H', len(encoded)) + encoded
            require(hashlib.sha256(material).hexdigest() == record['chain'], 'independent chained canonical identity')
            fields, identities = state.decode(core)
            values = {name: value for name, width, value in fields}
            expected_fields = {name: value for name, width, value in state.load()['fields']}
            if index >= 2:
                expected_fields['unwinding'] = 1
            if index >= 4:
                expected_fields['slot9.cycle'] = expected_fields['cycle9']
            require(values == expected_fields and identities == state.load()['identities'], 'all 411 fields/five identities protected')
            previous = record['chain']; labels.append(record['event'])
            observed.append({'event': record['event'], 'core_sha256': hashlib.sha256(core).hexdigest(), 'chain': previous})
        elif record['event'] == 'observation':
            require(old_events == 0 and not labels and record['index'] == 68 and record['kind'] == 4 and
                    record['pc'] == 0x020019b0 and record['accepted'], 'original AW7 terminal guards dominate handoff')
            require(hashlib.sha256(core).hexdigest() == state.FINAL, 'original terminal snapshot bound')
            old_events += 1
        else:
            require(record['event'] == 'terminal', 'unknown/extra/reordered event')
    require(old_events == 1 and labels == expected and records[-1]['events'] == 8 and records[-1]['chain'] == previous, 'complete success transcript')
    require(records[-1]['guest_instructions'] == 0 and records[-1]['MMIO'] == 0, 'zero guest/MMIO audit')
    return {'observations': observed, 'gpu_sha256': hashlib.sha256(gpu).hexdigest(), 'bound_frame': bound_frame}


def runtime_syntax(output, overlay, compiler):
    includes = [overlay, SOURCE, ROOT / 'build/task-o-sdl-runner/generated', SOURCE.parent / 'vendor/melonds',
                ROOT / 'local/ndsrecomp/recompiler/armv4t', ROOT / 'local/ndsrecomp/external/arm-recomp-core/common',
                ROOT / 'local/ndsrecomp/recompiler/support', ROOT / 'local/ndsrecomp/vendor/freebios',
                ROOT / 'local/recomp-ui/src', ROOT / 'local/recomp-ui/src/common',
                ROOT / 'local/toolchain/SDL3-3.4.18/x86_64-w64-mingw32/include']
    flags = [str(compiler), '-std=c++20', '-fsyntax-only'] + ['-I' + str(path) for path in includes]
    outcomes = {}
    for name in ['runtime_arm.cpp', 'scheduler.cpp', 'tier3.cpp', 'gpu3d.cpp']:
        for build, defines in [('default', []), ('diagnostic', ['-DAW12_DIAGNOSTIC_CAPTURE_ONLY'])]:
            result = run(flags + defines + [str(overlay / name)], output, 'syntax-' + build + '-' + name)
            require(result.returncode == 0, 'actual runtime overlay syntax: ' + build + '/' + name)
            outcomes[build + '/' + name] = result.returncode
    return outcomes


def audit_negatives(output):
    records = [json.loads(line) for line in (output / 'success.jsonl').read_text().splitlines()]
    mutations = []
    for label in ['yield_requested', 'tier3_exit', 'unwind_preserved', 'slice_consumed', 'slot_saved',
                  'pre_device_fence', 'gpu_observed', 'scheduler_admitted_capture_only']:
        position = next(index for index, item in enumerate(records) if item['event'] == label)
        mutations.append(('missing-' + label, records[:position] + records[position+1:]))
        mutations.append(('duplicate-' + label, records[:position] + [records[position]] + records[position:]))
    import copy
    changed = copy.deepcopy(records)
    changed[3]['chain'] = '0' * 64
    mutations.append(('chain', changed))
    changed = copy.deepcopy(records)
    changed[3]['frame'] += 1
    mutations.append(('frame', changed))
    mutations.append(('reorder', list(reversed(records))))
    for name, changed in mutations:
        path = output / ('tampered-' + name + '.jsonl')
        path.write_text('\n'.join(json.dumps(row) for row in changed) + '\n')
        failed = False
        try:
            inspect_audit(path, True)
        except ValueError:
            failed = True
        require(failed, 'independent audit must reject ' + name)
    return len(mutations)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    require(output.is_relative_to(ROOT / 'local/task-aw12') and not output.exists(), 'fresh local evidence directory')
    output.mkdir(parents=True)
    tested_inputs = {name: sha(HERE / name) for name in ['controller.h', 'gpu.h', 'hooks.py', 'fixture.h', 'inspect.cpp', 'check.py']}
    protected, functions, overlay_hashes, overlay = prepare(output)
    compiler = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    flags = [str(compiler), '-std=c++20', '-O2', '-I' + str(output), '-I' + str(overlay), '-I' + str(SOURCE),
             '-I' + str(SOURCE.parent), '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support')]
    binaries = {}
    for name, defines in [('diagnostic', ['-DAW12_DIAGNOSTIC_CAPTURE_ONLY']), ('default', [])]:
        binary = output / (name + '.exe')
        result = run(flags + defines + [str(HERE / 'inspect.cpp'), '-o', str(binary)], output, 'compile-' + name)
        require(result.returncode == 0, 'focused rail compilation: compile-' + name + '.json')
        binaries[name] = binary
    syntax = output / 'gpu-type.cpp'
    syntax.write_text('#include "vendor/melonds/GPU3D.h"\n#include "aw12/gpu.h"\n'
                      'task_aw2::Snapshot project(const melonDS::GPU3D& device) { return task_aw12::gpu_project(device,0,1); }\n')
    result = run(flags + ['-fsyntax-only', str(syntax)], output, 'actual-gpu-type')
    require(result.returncode == 0, 'actual GPU3D/FIFO passive type compatibility')
    runtime_compiles = runtime_syntax(output, overlay, compiler)
    terminal = output / 'terminal.hex'
    initial = output / 'initial.hex'
    result = run([str(binaries['diagnostic']), 'units', str(terminal), str(initial), str(output / 'unused')], output, 'units')
    require(result.returncode == 0, 'focused native unit assertions')
    units = json.loads(result.stdout)
    matrix = ['success', 'runtime-facade', 'prior-frames', 'duplicate-offer', 'stale-after', 'frame-serial', 'forbidden-fetch', 'reorder', 'early-fence',
              'irq', 'arm7', 'scheduler', 'device', 'timer', 'hint', 'cost-drift', 'duplicate-exit', 'unexpected-service',
              'unexpected-arm7', 'unexpected-irq', 'skip-exit', 'saved-corrupt', 'missing-fence', 'duplicate-fence',
              'duplicate-save', 'gpu-command', 'gpu-fifo', 'gpu-stall', 'gpu-busy', 'gpu-latent', 'gpu-ahead', 'gpu-debt',
              'omit-gpu', 'gpu-width', 'gpu-torn', 'omit-core', 'static-guard', 'nested', 'spent', 'cap-short', 'cap-long',
              'stale-entry', 'old-bus-count', 'missing-old-event', 'bank', 'journal', 'thread', 'tail-parent', 'disabled']
    outcomes = {}
    for mode in matrix:
        audit = output / (mode + '.jsonl')
        binary = binaries['default' if mode == 'disabled' else 'diagnostic']
        result = run([str(binary), mode, str(terminal), str(initial), str(audit)], output, 'child-' + mode)
        success = mode in ['success', 'runtime-facade', 'prior-frames']
        expected = 0 if mode == 'disabled' else 73 if success else 79
        require(result.returncode == expected, mode + ' disposal/disabled exit: see child-' + mode + '.json')
        require('SENTINEL' not in result.stdout + result.stderr, mode + ' no post-terminal/persistence/shutdown/service sentinel')
        outcomes[mode] = {'exit': result.returncode}
        if mode != 'disabled':
            outcomes[mode].update(inspect_audit(audit, success))
    for name, identity in protected.items():
        require(sha(ROOT / name) == identity, 'original source/evidence/locks untouched: ' + name)
    audit_cases = audit_negatives(output)
    require(all(sha(HERE / name) == identity for name, identity in tested_inputs.items()), 'test input source changed during certification')
    summary = {'task': 'AW12', 'native_assertions': units['assertions'], 'children': len(matrix),
               'disposal_successes': 3, 'disposal_failures': len(matrix)-4, 'default_children': 1,
               'outcomes': outcomes, 'original_source_hashes': protected, 'source_function_hashes': functions,
               'overlay_hashes': overlay_hashes, 'runtime_syntax': runtime_compiles, 'guest_instructions': 0, 'MMIO': 0,
               'tested_inputs_sha256': tested_inputs, 'audit_negative_cases': audit_cases,
               'historical_GPU_values_known': False, 'all_passed': True}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'all_passed': True, 'native_assertions': units['assertions'], 'children': len(matrix)}))


if __name__ == '__main__':
    main()
