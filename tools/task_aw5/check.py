"""Focused ROM-free capture-wrapper certification and retained AU preflight."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'local/ndsrecomp/runner/src'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw5') and not output.exists()
    output.mkdir(parents=True)
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = {key: value for key, value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    commands = []

    def run(command, expected=0):
        child = subprocess.run(list(map(str, command)), cwd=ROOT, env=environment,
                               capture_output=True, text=True, errors='replace', timeout=300)
        commands.append({'command': list(map(str, command)), 'exit': child.returncode,
                         'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        assert child.returncode == expected, child.stdout + child.stderr
        return child.stdout

    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'codex/brainage'
    authority = '0bb63e407f1caaa001e1e63a578547af3eddc7b9'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == authority
    for prefix in ['tools/task_au/', 'tools/task_aw2/', 'tools/task_aw3/', 'tools/task_aw4/']:
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', authority, prefix], cwd=ROOT, text=True).splitlines()
        for name in names:
            historical = subprocess.check_output(['git', 'show', authority + ':' + name], cwd=ROOT).decode('utf-8-sig')
            assert historical.splitlines() == (ROOT / name).read_text(encoding='utf-8-sig').splitlines(), name
    prior = json.loads((ROOT / 'local/task-aw4/certification-004/tests.json').read_text())
    assert prior['brainage_guest_execution'] is False
    for name, wanted in prior['sources'].items():
        assert sha(ROOT / 'tools/task_aw4' / name) == wanted
    run(['python', ROOT / 'tools/task_aw5/install.py'])
    setup = (SOURCE / 'task_au_setup.inc').read_text(encoding='utf-8-sig')
    baseline = (ROOT / 'tools/task_au/setup.inc').read_text(encoding='utf-8-sig')
    added = '        if (task_aw3::armed) {\n            if (task_aw5::selected()) task_aw5::handoff();\n            task_aw3::handoff();\n        }\n'
    assert setup.replace('#include "aw3/bridge.h"\n', '').replace(added, '').splitlines() == baseline.splitlines()
    tier = (SOURCE / 'tier3.cpp').read_text(encoding='utf-8-sig')
    assert tier.index('brainage_task_au::control(ic)') < tier.index('pre-MMIO handoff returned; AX forbidden') < tier.index('const bool covered = nds_has_bank') < tier.index('++g_stats.instructions') < tier.index('r = Interpreter::step')
    for width in [8, 16, 32]:
        write = next(line for line in tier.splitlines() if line.strip().startswith('void write' + str(width)) and 'override' in line)
        access = 'bus_write_u' + str(width) + '(a, v)'
        assert write.count(access) == 1 and write.index('brainage_task_au::memory_before') < write.index(access) < write.index('brainage_task_au::memory_after')
        read = next(line for line in tier.splitlines() if ('read' + str(width) + ' ' in line or 'read' + str(width) + '(' in line) and 'override' in line)
        access = 'bus_read_u' + str(width)
        assert read.count(access) == 1 and read.index('brainage_task_au::memory_read') < read.index(access)
    for tag in ['aq', 'as', 'au']:
        assert json.loads((ROOT / 'local' / ('task-' + tag) / 'preflight.json').read_text())['safe']
    expected = json.loads((ROOT / 'tools/task_au/expected.json').read_text())
    as_result = json.loads((ROOT / 'docs/BrainAge_TaskAS_Result.json').read_text())
    for name, wanted in expected['entry_hashes'].items():
        filename = 'decision-after.sav' if name == 'save' else 'decision-after-' + name + '.bin'
        assert sha(ROOT / as_result['authoritative_path'] / filename) == wanted
    binary = output / 'capture-test.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-I' + str(SOURCE),
         '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), ROOT / 'tools/task_aw5/test.cpp',
         ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', binary])
    results = []
    for mode in ['terminal', 'missing', 'yield', 'cap', 'save', 'readiness', 'journal', 'bad-au', 'legacy', 'disabled']:
        directory = output / mode
        directory.mkdir()
        expected_exit = 73 if mode in ['terminal', 'legacy'] else 99 if mode == 'disabled' else 79
        run([binary, mode, directory], expected_exit)
        rows = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
        if mode == 'disabled':
            assert not rows and (directory / 'old-halt').exists()
        else:
            expected_event = 'aw5_capture_terminal' if mode == 'terminal' else 'capture_only_terminal' if mode == 'legacy' else 'failure'
            assert rows[-1]['event'] == expected_event
            assert not (directory / 'old-halt').exists()
        for name in ['post-boundary-instruction', 'scheduler-tail', 'device-tail', 'IRQ-tail', 'ARM7-tail', 'destructor', 'persistence-shutdown']:
            assert not (directory / name).exists()
        if mode == 'terminal':
            snapshots = [row for row in rows if row['event'] == 'canonical_snapshot']
            assert len(snapshots) == 2 and snapshots[0] == snapshots[1]
            for row in snapshots:
                assert hashlib.sha256(bytes.fromhex(row['canonical_hex'])).hexdigest() == row['sha256']
        results.append({'mode': mode, 'exit': expected_exit, 'reason': rows[-1].get('reason') if rows else 'disabled legacy path'})
    for name, filename in [('AU', 'tools/task_au/guard_test.cpp'), ('AS', 'tools/task_as/guard_test.cpp'), ('AO', 'tools/task_ao/guard_test.cpp'), ('policy', 'tools/task_y/policy_test.cpp')]:
        executable = output / (name + '.exe')
        run([tool / 'g++.exe', '-std=c++17', '-O2', '-I' + str(ROOT / 'tools/brainage_custom'), ROOT / filename, '-o', executable])
        run([executable])
    result = {'safe': True, 'authority': authority, 'model_children': results,
              'AU_guards_unchanged': True, 'single_bus_call_and_guard_order': True,
              'prior_AW4_certification_bound': True, 'retained_images_verified': True,
              'guest_execution': False, 'AX_activation': False}
    (output / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
