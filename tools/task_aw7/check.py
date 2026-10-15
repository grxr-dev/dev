"""ROM-free integration tests. No game runner launch, ROM, save or checkpoint input."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
sys.path.insert(0, str(ROOT / 'tools/task_aw6'))
from check import verify_chain

decoder_spec = importlib.util.spec_from_file_location('aw5_decode', ROOT / 'tools/task_aw5/analyze.py')
decoder = importlib.util.module_from_spec(decoder_spec)
decoder_spec.loader.exec_module(decoder)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw7') and not output.exists()
    output.mkdir(parents=True)
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = {key: value for key, value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    logs = []

    def run(command, expected=0, cwd=ROOT):
        child = subprocess.run(command if isinstance(command, str) else list(map(str, command)), cwd=cwd, env=environment,
                               capture_output=True, text=True, errors='replace', timeout=600)
        logs.append({'command': command if isinstance(command, str) else list(map(str, command)), 'cwd': str(cwd),
                     'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
        assert child.returncode == expected, child.stdout + child.stderr
        return child.stdout

    authority = '1d4aeb1e17486b1db2276931f43a9c5d9a540f1b'
    run(['git', 'merge-base', '--is-ancestor', authority, 'HEAD'])
    assert run(['git', '-C', ROOT / 'local/ndsrecomp', 'rev-parse', 'HEAD']).strip() == '3a57236bb23d25dcb4caad7d58d733311062ff5e'
    assert run(['git', 'branch', '--show-current']).strip() == 'codex/brainage'
    certificate = json.loads((ROOT / 'tools/task_aw6/certificate.json').read_text())
    assert hashlib.sha256(json.dumps(certificate['certificate'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == certificate['sha256']
    preserved = [ROOT / 'local/task-aw5/capture-001/capture.jsonl', ROOT / 'local/task-aw5/live-attempt.lock',
                 ROOT / 'build/task-aw5-capture-002/nds_runner.exe', ROOT / 'build/task-o-sdl-runner/nds_runner.exe', ROOT / 'build/task-u-runner/nds_runner.exe']
    before = {str(path.relative_to(ROOT)): sha(path) for path in preserved}
    for prefix in ['tools/task_au/', 'tools/task_aw/', 'tools/task_aw2/', 'tools/task_aw3/', 'tools/task_aw4/', 'tools/task_aw5/', 'tools/task_aw6/']:
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', authority, prefix], cwd=ROOT, text=True).splitlines():
            assert subprocess.check_output(['git', 'show', authority + ':' + name], cwd=ROOT).decode('utf-8-sig').splitlines() == (ROOT / name).read_text(encoding='utf-8-sig').splitlines()
    run(['python', HERE / 'install.py'])
    installed = (SOURCE / 'task_au_setup.inc').read_text(encoding='utf-8-sig')
    early = '    if (task_aw7::owns()) { task_aw7::check_dispatch(); return 0; }\n'
    handoff = '        if (task_aw7::waiting()) { task_aw7::handoff(); return 0; }\n'
    old_aw3 = '        if (task_aw3::armed) {\n            if (task_aw5::selected()) task_aw5::handoff();\n            task_aw3::handoff();\n        }\n'
    original = (ROOT / 'tools/task_au/setup.inc').read_text(encoding='utf-8-sig')
    assert installed.replace('#include "aw3/bridge.h"\n', '').replace(early, '').replace(handoff, '').replace(old_aw3, '').splitlines() == original.splitlines()
    assert installed.index('AU forbidden STRH not dispatched') < installed.index(handoff) < installed.index('if (task_aw3::armed)')
    tier = (SOURCE / 'tier3.cpp').read_text(encoding='utf-8-sig')
    assert tier.count('task_aw7::runtime_access(') == 6
    assert tier.index('brainage_task_au::control(ic)') < tier.index('pre-MMIO handoff returned; AX forbidden') < tier.index('++g_stats.instructions') < tier.index('r = Interpreter::step')
    fixture = ROOT / 'local/task-aw6/certification-008'
    (output / 'model_rail.h').write_text((ROOT / 'tools/task_aw6/source_rail.h').read_text().replace('#include "prefix.h"', '#include "aw6/prefix.h"'))
    (output / 'source_model.inc').write_bytes((fixture / 'source_model.inc').read_bytes())
    (output / 'canonical.hex').write_bytes((fixture / 'canonical.hex').read_bytes())
    canonical = bytes.fromhex((output / 'canonical.hex').read_text().strip())
    assert hashlib.sha256(canonical).hexdigest() == '0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c'
    executable = output / 'aw7-model.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-Wall', '-Wextra', '-DAW7_DIAGNOSTIC_HARNESS=1', '-DAW7_ROMFREE_MODEL=1',
         '-I' + str(SOURCE), '-I' + str(output), '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'),
         HERE / 'test.cpp', ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', executable])
    unit = output / 'unit'; unit.mkdir()
    unit_text = run([executable, 'unit', output / 'canonical.hex', unit])
    assertions = int(re.search(r'AW7 assertions: (\d+)', unit_text)[1])
    modes = ['success', 'entry', 'short-entry-cap', 'AU-guard', 'hint', 'bank', 'debt', 'rtc', 'timer', 'device', 'scheduler', 'divider', 'cap', 'ordinal',
             'address', 'width', 'value', 'order', 'duplicate-access', 'runtime-MMIO', 'cost', 'final-cycle', 'missing', 'extra', 'reorder',
             'forbidden-fetch', 'forbidden-account', 'forbidden-dispatch', 'old-halt', 'disabled', 'default']
    modes += ['cost-' + str(index) for index in range(11)]
    modes += ['IRQ', 'ARM7-wake', 'hidden-latch', 'write-model', 'journal', 'journal-source', 'service']
    children = []
    success_proof = {}
    for mode in modes:
        directory = output / mode; directory.mkdir()
        expected = 73 if mode == 'success' else 99 if mode == 'disabled' else 0 if mode == 'default' else 79
        run([executable, mode, output / 'canonical.hex', directory], expected)
        rows = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        count = verify_chain(rows)
        if mode == 'success':
            assert count == 69 and rows[-1]['event'] == 'terminal'
            final = next(row for row in reversed(rows) if row['event'] == 'canonical_snapshot')
            assert final['sha256'] == 'ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526'
            writes, commits = [], []
            for row in rows:
                if row['event'] == 'canonical_snapshot':
                    fields, identities = decoder.decode(bytes.fromhex(row['canonical_hex']))
                elif row['event'] == 'observation':
                    assert row['pc'] != 0x020019b4
                    if row['kind'] == 2 and row['write']:
                        writes.append({'pc': row['pc'], 'address': row['address'], 'width': row['width'], 'value': row['value'],
                                       'cycle_before_commit': fields['cycle9'], 'divider_deadline': fields['div.deadline'],
                                       'journal_serial': fields['capture.serial'], 'cap': fields['slice_cap']})
                    if row['kind'] == 3:
                        commits.append({'pc': row['pc'], 'cost': row['value'], 'cycle': fields['cycle9']})
            assert len(writes) == 5 and [row['divider_deadline'] for row in writes] == [1708437894, 1708437899, 1708437905, 1708437909, 1708437913]
            assert [row['journal_serial'] for row in writes] == list(range(502, 507))
            assert all(row['cap'] == 3416875778 for row in writes)
            assert [row['cost'] for row in commits] == [8, 1, 8, 1, 3, 8, 8, 8, 4, 4, 3]
            assert commits[-1]['cycle'] == 3416875777
            success_proof = {'rail': 'model, not actual-provider success', 'writes': writes, 'commits': commits,
                             'final_canonical_sha256': final['sha256'], 'forbidden_successor_observations': 0}
        elif mode not in ['default', 'disabled']:
            assert rows[-1]['event'] == 'failure'
        if mode != 'default':
            for sentinel in ['scheduler', 'device', 'IRQ', 'ARM7', 'guest', 'old-halt', 'shutdown', 'persistence', 'actual-MMIO', 'forbidden-fetch']:
                assert not (directory / sentinel).exists(), (mode, sentinel)
        else:
            for sentinel in ['default-normal-return', 'shutdown', 'persistence']:
                assert (directory / sentinel).exists()
        children.append({'mode': mode, 'exit': expected, 'observations': count, 'reason': rows[-1].get('reason')})
    default_binary = output / 'aw7-default.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-I' + str(SOURCE), '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'),
         HERE / 'disabled.cpp', ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', default_binary])
    run([default_binary])
    actual_build = ROOT / 'local/task-aw4/certification-004/build'
    database = json.loads(run([tool / 'ninja.exe', '-C', actual_build, '-t', 'compdb']))
    compile_row = next(row for row in database if row['file'].endswith('/test.cpp'))
    provider_object = output / 'provider.cpp.obj'
    command = compile_row['command'].replace('-DAW4_ROMFREE_CERTIFICATION=1', '-DAW7_DIAGNOSTIC_HARNESS=1')
    command = command.replace(compile_row['file'], (HERE / 'provider.cpp').as_posix())
    command = command.replace(compile_row['output'], provider_object.as_posix()).replace(compile_row['output'].replace('/', '\\') + '.d', provider_object.as_posix() + '.d')
    run(command, cwd=actual_build)
    link = run([tool / 'ninja.exe', '-C', actual_build, '-t', 'commands', 'aw4_provider_test']).splitlines()[-1]
    link = link.replace(compile_row['output'], provider_object.as_posix()).replace('-o aw4_provider_test.exe', '-o ' + (output / 'aw7-actual-provider.exe').as_posix())
    link = link.replace('--out-implib,libaw4_provider_test.dll.a', '--out-implib,' + (output / 'provider.dll.a').as_posix())
    assert ' -o ' + (output / 'aw7-actual-provider.exe').as_posix() in link
    run(link, cwd=actual_build)
    actual = output / 'actual-provider'; actual.mkdir()
    run([output / 'aw7-actual-provider.exe', actual], 79)
    actual_rows = [json.loads(line) for line in (actual / 'audit.jsonl').read_text().splitlines()]
    assert actual_rows[-1]['event'] == 'failure' and 'hashes' in actual_rows[-1]['reason']
    assert verify_chain(actual_rows) == 0
    actual_snapshots = [row for row in actual_rows if row['event'] == 'canonical_snapshot']
    assert len(actual_snapshots) == 2 and actual_snapshots[0] == actual_snapshots[1]
    expected_fields, expected_ids = decoder.decode(canonical)
    actual_fields, actual_ids = decoder.decode(bytes.fromhex(actual_snapshots[0]['canonical_hex']))
    differing_fields = sorted(name for name in actual_fields.keys() | expected_fields.keys() if actual_fields.get(name) != expected_fields.get(name))
    differing_ids = sorted(name for name in actual_ids.keys() | expected_ids.keys() if actual_ids.get(name) != expected_ids.get(name))
    mismatch = {'actual_scalars': len(actual_fields), 'expected_scalars': len(expected_fields),
                'differing_or_missing_scalar_count': len(differing_fields), 'differing_or_missing_scalar_names': differing_fields,
                'differing_identity_classes': differing_ids, 'actual_canonical_sha256': actual_snapshots[0]['sha256'],
                'repeat_passive_snapshot_identical': True, 'readiness_success_claimed': False}
    (output / 'actual-provider-mismatches.json').write_text(json.dumps(mismatch, indent=2) + '\n')
    for name in ['actual-provider-returned', 'shutdown', 'persistence']:
        assert not (actual / name).exists()
    run([tool / 'ninja.exe', '-C', ROOT / 'build/task-o-sdl-runner', 'CMakeFiles/nds_runner.dir/src/tier3.cpp.obj', '-j', '2'])
    assert before == {str(path.relative_to(ROOT)): sha(path) for path in preserved}
    result = {'task': 'AW7', 'classification': 'PARTIAL', 'dynamic_execution_ready': False,
              'assertions': assertions, 'model_children': children, 'actual_provider_rejection': actual_rows[-1],
              'actual_provider_exact_AW5_success': False, 'model_69_observation_success': True,
              'actual_provider_mismatches': mismatch, 'default_compile_arming_rejected': True,
              'static_certificate_payload_sha256': certificate['sha256'],
              'model_success_proof': success_proof,
              'original_AU_guard_bodies_preserved': True, 'default_tier3_object_compile': True,
              'preserved_artifacts': before, 'BrainAge_execution': False, 'runtime_BrainAge_MMIO': False, 'AX_executed': False}
    (output / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['classification', 'dynamic_execution_ready', 'assertions', 'actual_provider_rejection']}, indent=2))


if __name__ == '__main__':
    main()
