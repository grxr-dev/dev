"""Focused ROM-free certification. No runner, ROM, save, state, or guest instruction is opened/executed."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SENTINELS = ['scheduler-tail', 'device-service', 'irq-acceptance', 'arm7-catchup',
             'shutdown-save', 'destructor', 'atexit', 'runtime-return']


def read_canonical(hex_text):
    data = bytes.fromhex(hex_text)
    assert data[:6] == b'AW2S\x01\x00'
    cursor = 6

    def integer(width):
        nonlocal cursor
        assert cursor+width <= len(data)
        result = int.from_bytes(data[cursor:cursor+width], 'little')
        cursor += width
        return result

    def string():
        nonlocal cursor
        size = integer(2)
        assert cursor+size <= len(data)
        value = data[cursor:cursor+size].decode('ascii')
        cursor += size
        return value

    fields, hashes = {}, {}
    for _ in range(integer(4)):
        key = string()
        width = integer(1)
        assert width in (1, 2, 4, 8) and key not in fields
        fields[key] = integer(width)
    for _ in range(integer(4)):
        key, value = string(), string()
        assert key not in hashes
        hashes[key] = value
    assert cursor == len(data)
    return fields, hashes, hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='local/task-aw2/retry-20261013/certification-001')
    args = parser.parse_args()
    output = (ROOT/args.output).resolve()
    assert output.is_relative_to((ROOT/'local/task-aw2').resolve())
    assert not output.exists(), 'Use a fresh evidence directory; never delete/overwrite evidence.'
    output.mkdir(parents=True)
    compiler = ROOT/'local/toolchain/w64devkit/bin/g++.exe'
    env = dict(os.environ)
    env['PATH'] = str(compiler.parent)+os.pathsep+env['PATH']
    log = []

    def run(command, code=0):
        process = subprocess.run([str(value) for value in command], cwd=ROOT, env=env,
                                 text=True, encoding='utf-8', errors='replace', capture_output=True)
        log.append({'command': [str(value) for value in command], 'returncode': process.returncode,
                    'stdout': process.stdout, 'stderr': process.stderr})
        (output/'commands.json').write_text(json.dumps(log, indent=2)+'\n')
        assert process.returncode == code, process.stderr or process.stdout
        return process.stdout.strip()

    run(['python', HERE/'make_manifest.py'])
    executable = output/'synthetic.exe'
    run([compiler, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror', HERE/'test.cpp', '-o', executable])
    unit = run([executable])
    native_build = output/'native-build'
    cmake = compiler.parent/'cmake.exe'
    run([cmake, '-S', HERE, '-B', native_build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release'])
    run([cmake, '--build', native_build, '-j', '4'])
    actual_executable = native_build/'aw2_runtime_test.exe'
    actual_unit = run([actual_executable])
    children = []
    cases = [('terminal', 73), ('preflight', 79), ('legacy', 79), ('wrong-mmio', 79),
             ('irq', 79), ('cost', 79), ('state', 79), ('missing', 79), ('actual-runtime-cap', 79)]
    for mode, code in cases:
        directory = output/mode
        directory.mkdir()
        run([actual_executable if mode == 'actual-runtime-cap' else executable, mode, directory], code)
        rows = [json.loads(line) for line in (directory/'audit.jsonl').read_text().splitlines()]
        assert rows[-1]['event'] == ('terminal' if mode == 'terminal' else 'failure')
        assert all(not (directory/name).exists() for name in SENTINELS)
        snapshots = []
        for row in rows:
            if row['event'] == 'canonical_snapshot':
                fields, hashes, digest = read_canonical(row['canonical_hex'])
                assert digest == row['sha256']
                snapshots.append((fields, hashes))
        if mode == 'terminal':
            assert rows[-1]['events'] == 77 and len(snapshots) == 2
            before, after = snapshots[0][0], snapshots[-1][0]
            assert before['cycle9'] == 3416875721 and after['cycle9'] == 3416875785
            assert after['r15'] == 0x020019b8 and after['div.deadline'] == 1708437913
            assert snapshots[0][1] == snapshots[-1][1]
            assert after['logical_saves'] == after['flash_commits'] == 0
        if mode == 'actual-runtime-cap':
            assert rows[-1]['events'] == 4
            assert rows[-2]['event'] == 'canonical_snapshot'
            assert snapshots[-1][0]['slice_cap'] == 3416875786
        children.append({'case': mode, 'exit_code': code, 'accepted_events': rows[-1]['events'],
                         'reason': rows[-1]['reason'], 'all_tail_shutdown_sentinels_absent': True,
                         'actual_runtime_hook': mode == 'actual-runtime-cap'})
    result = {
        'task': 'AW2', 'rom_free': True, 'brainage_guest_execution': False,
        'brainage_runtime_mmio': False, 'AX_executed': False,
        'unit': unit, 'assertions': int(re.search(r'assertions: (\d+)', unit)[1]),
        'actual_runtime_unit': actual_unit,
        'actual_runtime_checks': int(re.search(r'checks: (\d+)', actual_unit)[1]),
        'child_process_tests': children,
        'limitations': ['Positive full transcript uses a synthetic passive fixture, not reconstructed AU peripherals.',
                        'Actual-runtime child proves failure disposal inside nds_reschedule_slice, not Brain Age execution.',
                        'Device stubs abort on unsupported access; Tier-3 is not linked or run.'],
        'source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in HERE.iterdir() if path.is_file()},
    }
    (output/'commands.json').write_text(json.dumps(log, indent=2)+'\n')
    (output/'tests.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
