"""Authenticated-evidence ROM-free fixture. Never opens images or launches a game runner."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
sys.path.insert(0, str(ROOT / 'tools/task_aw6'))
from check import verify_chain

spec = importlib.util.spec_from_file_location('aw5_decode', ROOT / 'tools/task_aw5/analyze.py')
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw8') and not output.exists()
    output.mkdir(parents=True)
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = {key: value for key, value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    logs = []
    own_sources = {str(path.relative_to(ROOT)): sha(path) for path in HERE.iterdir()
                   if path.suffix in ['.cpp', '.h', '.py'] or path.name in ['CMakeLists.txt', 'README.md']}

    def run(command, expected=0):
        child = subprocess.run(list(map(str, command)), cwd=ROOT, env=environment,
                               capture_output=True, text=True, errors='replace', timeout=600)
        logs.append({'command': list(map(str, command)), 'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
        assert child.returncode == expected, child.stdout + child.stderr
        return child.stdout

    authority = '01fe942d8d42b0dc819acf92836c7cfb845a6470'
    run(['git', 'merge-base', '--is-ancestor', authority, 'HEAD'])
    assert run(['git', 'branch', '--show-current']).strip() == 'codex/brainage'
    assert run(['git', '-C', SOURCE.parents[1], 'rev-parse', 'HEAD']).strip() == '3a57236bb23d25dcb4caad7d58d733311062ff5e'
    capture = ROOT / 'local/task-aw5/capture-001/capture.jsonl'
    assert sha(capture) == '303f069c8d7f4e36da31aaab6b2810cc34e06b0eaee5ced7fcf67e463146327a'
    rows = [json.loads(line) for line in capture.read_text().splitlines()]
    snapshot = next(row for row in rows if row['event'] == 'canonical_snapshot')
    canonical = bytes.fromhex(snapshot['canonical_hex'])
    assert hashlib.sha256(canonical).hexdigest() == snapshot['sha256'] == '0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c'
    assert rows[-1]['event'] == 'failure' and rows[-1]['reason'] == 'pending yield/unclassified poll mode'
    fields, identities = decoder.decode(canonical)
    assert len(fields) == 361 and len(identities) == 5
    aw5 = json.loads((ROOT / 'docs/BrainAge_TaskAW5_Result.json').read_text())
    assert identities['rom'] == aw5['authority']['ROM_SHA1']
    assert identities['mainram'] == aw5['memory_and_save']['RAM_sha256']
    assert identities['dtcm'] == aw5['memory_and_save']['DTCM_sha256']
    assert identities['save'] == aw5['memory_and_save']['before_after_live_save_sha256']
    certificate = json.loads((ROOT / 'tools/task_aw6/certificate.json').read_text())
    assert hashlib.sha256(json.dumps(certificate['certificate'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == certificate['sha256']
    for name, digest in certificate['certificate']['runtime_source_sha256'].items():
        path = ROOT / name.replace('\\', '/')
        if path.name not in ['tier3.cpp', 'task_au_setup.inc']:
            assert sha(path) == digest, name
    for name in ['runtime.inc', 'scheduler.inc', 'bus.inc', 'io.inc', 'cp15.inc']:
        assert (SOURCE / 'aw3' / name).read_text().splitlines() == (ROOT / 'tools/task_aw3' / name).read_text().splitlines()
    assert (SOURCE / 'aw6/prefix.h').read_text().splitlines() == (ROOT / 'tools/task_aw6/prefix.h').read_text().splitlines()
    assert (SOURCE / 'aw7/integration.h').read_text().splitlines() == (ROOT / 'tools/task_aw7/integration.h').read_text().splitlines()
    setup = (SOURCE / 'task_au_setup.inc').read_text()
    assert setup.index('AU forbidden STRH not dispatched') < setup.index('task_aw7::handoff()') < setup.index('if (task_aw3::armed)')
    protected = [capture, ROOT / 'local/task-aw5/live-attempt.lock', ROOT / 'build/task-aw5-capture-002/nds_runner.exe',
                 ROOT / 'build/task-o-sdl-runner/nds_runner.exe', ROOT / 'build/task-u-runner/nds_runner.exe']
    protected += [SOURCE / name for name in ['runtime_arm.cpp', 'io.cpp', 'bus.cpp', 'scheduler.cpp', 'cp15.cpp', 'tier3.cpp', 'task_au_setup.inc']]
    protected += list((SOURCE / 'aw3').glob('*.inc')) + [SOURCE / 'aw7/integration.h']
    before = {str(path.relative_to(ROOT)): sha(path) for path in protected}
    for prefix in ['tools/task_au/', 'tools/task_aw3/', 'tools/task_aw4/', 'tools/task_aw5/', 'tools/task_aw6/', 'tools/task_aw7/']:
        for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', authority, prefix], cwd=ROOT, text=True).splitlines():
            assert subprocess.check_output(['git', 'show', authority + ':' + name], cwd=ROOT).decode('utf-8-sig').splitlines() == (ROOT / name).read_text(encoding='utf-8-sig').splitlines()
    generated = output / 'generated'; generated.mkdir()
    (output / 'entry.hex').write_text(canonical.hex() + '\n')
    adapters = {}
    for name in ['bus', 'io']:
        original = (SOURCE / f'aw3/{name}.inc').read_text()
        adapted = original
        for identity in (['mainram', 'dtcm'] if name == 'bus' else ['save']):
            prefix = f'    out.hashes["{identity}"]='
            line = next(line for line in original.splitlines() if line.startswith(prefix))
            replacement = line + f'\n    out.hashes["{identity}"]=task_aw8::identity("{identity}",out.hashes.at("{identity}"));'
            assert adapted.count(line) == 1
            adapted = adapted.replace(line, replacement)
        restored = adapted
        for identity in (['mainram', 'dtcm'] if name == 'bus' else ['save']):
            restored = restored.replace(f'\n    out.hashes["{identity}"]=task_aw8::identity("{identity}",out.hashes.at("{identity}"));', '')
        assert restored == original
        (generated / f'{name}_identity.inc').write_text(adapted)
        adapters[name] = {'original_sha256': hashlib.sha256(original.encode()).hexdigest(), 'adapted_sha256': hashlib.sha256(adapted.encode()).hexdigest()}
    for name in ['runtime_arm', 'bus', 'io', 'scheduler', 'spu', 'cp15']:
        original = (SOURCE / f'{name}.cpp').read_text(encoding='utf-8-sig')
        copied = original
        if name in ['bus', 'io']:
            anchor = f'#include "aw3/{name}.inc"'
            assert copied.count(anchor) == 1
            copied = copied.replace(anchor, f'#include "{name}_identity.inc"')
        if name == 'io':
            for signature in ['uint32_t nds_io_read(uint32_t addr, uint32_t width) {', 'void nds_io_write(uint32_t addr, uint32_t value, uint32_t width) {']:
                assert copied.count(signature) == 1
                copied = copied.replace(signature, signature + '\n    task_aw3::fail("AW8 forbidden actual IO entry before MMIO body");')
        (generated / f'aw8_{"runtime" if name == "runtime_arm" else name}.cpp').write_text(copied, encoding='utf-8')
    provenance = {'AW5_commit': 'e366a8b8811668ae9bd22bd34b661799c6058bad', 'capture_sha256': sha(capture),
                  'canonical_sha256': snapshot['sha256'], 'identities': identities, 'scalars': 361, 'identity_adapters': adapters,
                  'production_sources_changed': False, 'raw_images_used': False, 'historical_metadata_binding_not_new_image_hash_measurement': True,
                  'test_copy_IO_entry_trips_before_any_body_effect': True}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    build = output / 'build'
    run([tool / 'cmake.exe', '-S', HERE, '-B', build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release', '-DAW8_GENERATED=' + generated.as_posix()])
    run([tool / 'cmake.exe', '--build', build, '-j', '4'])
    executable = build / 'aw8_provider_test.exe'
    modes = ['inspect', 'success', 'AU-guard', 'entry-cap', 'ordinal', 'cycle', 'cap', 'hint', 'debt', 'cpu', 'bank',
             'arm7', 'event', 'irq', 'rtc', 'timer', 'device', 'divider', 'save', 'mainram', 'dtcm', 'code', 'latch',
             'journal', 'journal-source', 'rom', 'framework', 'real-bus', 'real-MMIO', 'address', 'width', 'value',
             'extra', 'reorder', 'missing', 'forbidden-fetch', 'forbidden-account', 'forbidden-dispatch', 'old-halt', 'service',
             'torn-sample', 'rebind', 'unsealed', 'raw-IO-read', 'raw-IO-write']
    modes += ['cost-' + str(index) for index in range(11)]
    children = []
    success_proof = {}
    for mode in modes:
        directory = output / mode; directory.mkdir()
        expected = 0 if mode == 'inspect' else 73 if mode == 'success' else 79
        run([executable, mode, output / 'entry.hex', directory], expected)
        audit = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        count = verify_chain(audit)
        snapshots = [row for row in audit if row['event'] == 'canonical_snapshot']
        assert snapshots[0]['sha256'] == snapshot['sha256']
        if mode == 'success':
            assert count == 69 and audit[-1]['event'] == 'terminal'
            assert snapshots[-1]['sha256'] == certificate['certificate']['final_canonical_sha256']
            assert snapshots[0]['canonical_hex'] == snapshots[1]['canonical_hex']
            writes, commits = [], []
            for row in audit:
                if row['event'] == 'canonical_snapshot':
                    observed, hashes = decoder.decode(bytes.fromhex(row['canonical_hex']))
                    assert hashes == identities
                elif row['event'] == 'observation':
                    assert row['accepted'] and row['pc'] != 0x020019b4
                    if row['kind'] == 2 and row['write']:
                        writes.append({'pc': row['pc'], 'address': row['address'], 'width': row['width'], 'value': row['value'],
                                       'cycle': observed['cycle9'], 'deadline': observed['div.deadline'],
                                       'serial': observed['capture.serial'], 'cap': observed['slice_cap']})
                    if row['kind'] == 3:
                        commits.append({'cost': row['value'], 'cycle': observed['cycle9']})
            assert [row['deadline'] for row in writes] == [1708437894, 1708437899, 1708437905, 1708437909, 1708437913]
            assert [row['serial'] for row in writes] == list(range(502, 507))
            assert all(row['cap'] == 3416875778 for row in writes)
            assert [row['cost'] for row in commits] == [8, 1, 8, 1, 3, 8, 8, 8, 4, 4, 3]
            assert observed['cycle9'] == 3416875777 and observed['r15'] == 0x020019b4
            success_proof = {'writes': writes, 'commits': commits, 'final_digest': snapshots[-1]['sha256'],
                             'identities_unchanged': True, 'retired': sum(row.get('kind') == 4 for row in audit)}
        elif mode != 'inspect':
            assert audit[-1]['event'] == 'failure'
        if mode != 'inspect':
            for sentinel in ['scheduler', 'device', 'IRQ', 'ARM7', 'guest', 'halt', 'shutdown', 'persistence', 'real-bus', 'real-MMIO', 'forbidden']:
                assert not (directory / sentinel).exists(), (mode, sentinel)
        children.append({'mode': mode, 'exit': expected, 'observations': count, 'reason': audit[-1].get('reason')})
    identity_children = []
    for name, digest in identities.items():
        changed = canonical.replace(digest.encode(), (('0' if digest[0] != '0' else '1') + digest[1:]).encode())
        assert changed != canonical
        path = output / f'tampered-{name}.hex'; path.write_text(changed.hex() + '\n')
        directory = output / f'identity-{name}'; directory.mkdir()
        run([executable, 'success', path, directory], 79)
        audit = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        assert audit[-1]['event'] == 'failure' and audit[-1]['reason'] == 'AW5 canonical authentication'
        assert not any(row['event'] == 'entry' or row['event'] == 'observation' for row in audit)
        assert not (directory / 'shutdown').exists() and not (directory / 'persistence').exists()
        identity_children.append(name)
    default_binary = output / 'aw8-default.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-I' + str(SOURCE), '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'),
         ROOT / 'tools/task_aw7/disabled.cpp', ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', default_binary])
    run([default_binary])
    denied = subprocess.run([str(tool / 'g++.exe'), '-std=c++20', '-fsyntax-only', '-I' + str(SOURCE),
                            '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), str(HERE / 'binding.h')],
                           capture_output=True, text=True, env=environment, timeout=60)
    assert denied.returncode != 0 and 'test-executable-only' in denied.stderr
    assert before == {str(path.relative_to(ROOT)): sha(path) for path in protected}
    assert own_sources == {name: sha(ROOT / name) for name in own_sources}
    result = {'task': 'AW8', 'actual_provider_entry_matches_AW5': True, 'children': children, 'provenance': provenance,
              'actual_provider_69_observation_success': True, 'preserved_artifacts': before,
              'success_proof': success_proof, 'identity_tamper_children': identity_children,
              'default_build_arming_rejected': True, 'production_binding_header_rejected': True,
              'fixture_sources_sha256': own_sources, 'fixture_executable_sha256': sha(executable),
              'generated_sources_sha256': {str(path.relative_to(output)): sha(path) for path in generated.iterdir()},
              'runtime_bus_still_closed': True, 'BrainAge_execution': False, 'AX_executed': False}
    (output / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'process_controls': len(children), 'actual_provider_69_observation_success': True}, indent=2))


if __name__ == '__main__':
    main()
