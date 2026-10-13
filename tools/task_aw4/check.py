"""ROM-free AW4 certification. Never launches a game runner or opens game images."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def verify_chain(rows):
    previous = None
    snapshot = None
    observations = 0
    for row in rows:
        if row['event'] == 'canonical_snapshot':
            snapshot = bytes.fromhex(row['canonical_hex'])
            assert hashlib.sha256(snapshot).hexdigest() == row['sha256']
        if row['event'] == 'preflight':
            previous = row['entry']
        if row['event'] == 'observation':
            assert row['index'] == observations and row['previous'] == previous
            if row['accepted']:
                material = previous.encode('ascii') + snapshot
                material += struct.pack('<QIIIII?', observations, row['kind'], row['pc'], row['address'], row['width'], row['value'], row['write'])
                assert hashlib.sha256(material).hexdigest() == row['chain']
                previous = row['chain']
            else:
                assert row['chain'] == previous
            observations += 1
    return observations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    output = Path(parser.parse_args().output).resolve()
    assert output.is_relative_to((ROOT / 'local/task-aw4').resolve()) and not output.exists()
    output.mkdir(parents=True)
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = dict(os.environ)
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    for key in list(environment):
        if key.startswith('NDS_'):
            del environment[key]
    logs = []

    def run(command, expected=0):
        child = subprocess.run([str(value) for value in command], cwd=ROOT, env=environment,
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
        logs.append({'command': [str(value) for value in command], 'exit': child.returncode,
                     'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
        assert child.returncode == expected, child.stdout + child.stderr
        return child.stdout

    source = ROOT / 'local/ndsrecomp/runner/src'
    protected = ['runtime_arm.cpp', 'tier3.cpp', 'task_au_setup.inc', 'scheduler.cpp', 'bus.cpp', 'io.cpp', 'cp15.cpp']
    before = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in protected}
    runners = [ROOT / 'build/task-o-sdl-runner/nds_runner.exe', ROOT / 'build/task-u-runner/nds_runner.exe']
    runners = [path for path in runners if path.exists()]
    executable_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in runners}
    run(['python', ROOT / 'tools/task_aw3/install.py'])
    syntax = [tool / 'g++.exe', '-std=c++20', '-fsyntax-only', '-I' + str(source),
              '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), HERE / 'production_contract.cpp']
    run(syntax)
    run(syntax + ['-DAW4_EXPECT_OVERRIDE_REJECTION=1'], 1)
    assert 'too many arguments' in logs[-1]['stderr'] and 'entry_preflight' in logs[-1]['stderr']
    build = output / 'build'
    run([tool / 'cmake.exe', '-S', HERE, '-B', build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release'])
    run([tool / 'cmake.exe', '--build', build, '-j', '4'])
    executable = build / 'aw4_provider_test.exe'
    assertions = {}
    for mode in ['unit', 'unit-banks']:
        directory = output / mode
        directory.mkdir()
        text = run([executable, mode, directory])
        assertions[mode] = int(re.search(r'assertions: (\d+)', text)[1])
    success = ['success', 'success-banks']
    failures = ['ordinal', 'journal', 'journal-extra', 'source', 'epoch', 'serial', 'old-cap', 'new-cap', 'deadline', 'import',
                'latch', 'yield', 'irq', 'arm7', 'device', 'scheduler', 'image', 'save', 'cpu', 'divider', 'debt', 'cap', 'cost',
                'missing', 'extra', 'wrong-mmio', 'guard', 'bind-torn', 'preflight-rom', 'preflight-code', 'preflight-cpu',
                'preflight-ram', 'preflight-dtcm', 'preflight-save', 'preflight-debt', 'preflight-cap']
    children = []
    for mode in success + failures + ['disabled']:
        directory = output / mode
        directory.mkdir()
        expected = 73 if mode in success else 0 if mode == 'disabled' else 79
        run([executable, mode, directory], expected)
        rows = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        observations = verify_chain(rows)
        if mode == 'disabled':
            assert not rows and (directory / 'disabled-normal-return').exists()
        else:
            assert rows[-1]['event'] == ('terminal' if mode in success else 'failure')
            if mode in success:
                assert observations == 77 and rows[-1]['events'] == 77
            assert rows[-1]['reason']
        for name in ['scheduler', 'device', 'IRQ', 'ARM7', 'guest', 'old-halt', 'shutdown', 'persistence']:
            assert not (directory / name).exists(), (mode, name)
        children.append({'mode': mode, 'exit': expected, 'observations': observations,
                         'reason': rows[-1]['reason'] if rows else 'disabled normal return', 'tail_sentinels_reached': False})
    legacy = output / 'au-guard-model.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-I' + str(source),
         '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), ROOT / 'tools/task_aw3/test.cpp',
         ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', legacy])
    handoff = []
    for mode, expected in [('terminal', 73), ('bad-au', 79), ('disabled', 99)]:
        directory = output / ('au-' + mode)
        directory.mkdir()
        run([legacy, mode, directory], expected)
        rows = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        assert (directory / 'old-halt').exists() == (mode == 'disabled')
        if mode != 'disabled':
            assert rows[-1]['event'] == ('capture_only_terminal' if mode == 'terminal' else 'failure')
        for name in ['post-boundary-instruction', 'device-tail', 'IRQ-tail', 'ARM7-tail', 'destructor', 'persistence-shutdown']:
            assert not (directory / name).exists()
        handoff.append({'mode': mode, 'exit': expected, 'old_halt_reached': mode == 'disabled', 'model_only': True})
    setup = (source / 'task_au_setup.inc').read_text(encoding='utf-8-sig')
    anchor = setup.index('if (task_aw3::armed) task_aw3::handoff();')
    assert setup.index('forbidden STRH', setup.index('au_control')) < anchor < setup.index('finish(0)', anchor)
    tier = (source / 'tier3.cpp').read_text(encoding='utf-8-sig')
    assert tier.index('pre-MMIO handoff returned; AX forbidden') < tier.index('const uint32_t code_correction')
    assert 'nds_halt' not in (HERE / 'controller.h').read_text()
    run([tool / 'ninja.exe', '-C', ROOT / 'build/task-o-sdl-runner',
         *[f'CMakeFiles/nds_runner.dir/src/{name}.cpp.obj' for name in ['runtime_arm', 'scheduler', 'bus', 'io', 'cp15', 'tier3']], '-j', '4'])
    assert before == {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in protected}
    assert executable_hashes == {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in runners}
    rows = [json.loads(line) for line in (output / 'success/audit.jsonl').read_text().splitlines()]
    altered = [dict(row) for row in rows]
    next(row for row in altered if row['event'] == 'observation')['value'] ^= 1
    try:
        verify_chain(altered)
    except AssertionError:
        pass
    else:
        raise AssertionError('audit tamper was accepted')
    result = {'task': 'AW4', 'assertions': assertions, 'children': children, 'AU_guard_model_children': handoff,
              'source_guards_unchanged': True,
              'production_authority_override_compile_rejected': True,
              'six_default_runtime_objects_compile': True, 'runner_hashes_unchanged': executable_hashes,
              'brainage_guest_execution': False, 'runtime_BrainAge_MMIO': False, 'live_capture': False, 'AX_executed': False,
              'sources': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in HERE.iterdir() if path.is_file()}}
    (output / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'assertions': assertions, 'children': len(children), 'all_passed': True}, indent=2))


if __name__ == '__main__':
    main()
