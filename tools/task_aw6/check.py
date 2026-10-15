"""ROM-free captured-state reconciliation. Never opens a ROM/save/state or launches a runner."""
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
SOURCE = ROOT / 'local/ndsrecomp/runner/src'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(text, signature):
    assert text.count(signature) == 1, signature
    start = text.index(signature)
    opening = text.index('{', start)
    depth = 1
    cursor = opening + 1
    while depth:
        if text.startswith('//', cursor):
            cursor = text.index('\n', cursor) + 1
            continue
        if text.startswith('/*', cursor):
            cursor = text.index('*/', cursor) + 2
            continue
        if text[cursor] in ['"', "'"]:
            quote = text[cursor]
            cursor += 1
            while text[cursor] != quote:
                cursor += 2 if text[cursor] == '\\' else 1
            cursor += 1
            continue
        depth += (text[cursor] == '{') - (text[cursor] == '}')
        cursor += 1
    return text[start:cursor]


def verify_chain(rows):
    previous = None
    canonical = None
    count = 0
    for row in rows:
        if row['event'] == 'canonical_snapshot':
            canonical = bytes.fromhex(row['canonical_hex'])
            assert hashlib.sha256(canonical).hexdigest() == row['sha256']
        elif row['event'] == 'entry':
            previous = row['sha256']
        elif row['event'] == 'observation':
            assert row['index'] == count and row['previous'] == previous
            if row['accepted']:
                material = previous.encode() + canonical + struct.pack('<QIIIII?', count, row['kind'], row['pc'], row['address'], row['width'], row['value'], row['write'])
                assert hashlib.sha256(material).hexdigest() == row['chain']
                previous = row['chain']
            else:
                assert previous == row['chain']
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    output = parser.parse_args().out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw6') and not output.exists()
    output.mkdir(parents=True)
    authority = 'e366a8b8811668ae9bd22bd34b661799c6058bad'
    subprocess.run(['git', 'merge-base', '--is-ancestor', authority, 'HEAD'], cwd=ROOT, check=True)
    assert subprocess.check_output(['git', '-C', str(SOURCE.parents[1]), 'rev-parse', 'HEAD'], text=True).strip() == '3a57236bb23d25dcb4caad7d58d733311062ff5e'
    capture = ROOT / 'local/task-aw5/capture-001/capture.jsonl'
    rows = [json.loads(line) for line in capture.read_text().splitlines()]
    snapshot = next(row for row in rows if row['event'] == 'canonical_snapshot')
    assert snapshot['sha256'] == '0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c'
    assert hashlib.sha256(bytes.fromhex(snapshot['canonical_hex'])).hexdigest() == snapshot['sha256']
    assert rows[-1]['event'] == 'failure' and rows[-1]['reason'] == 'pending yield/unclassified poll mode'
    protected = [capture, ROOT / 'local/task-aw5/live-attempt.lock', ROOT / 'build/task-aw5-capture-002/nds_runner.exe',
                 ROOT / 'build/task-o-sdl-runner/nds_runner.exe', ROOT / 'build/task-u-runner/nds_runner.exe']
    protected += [SOURCE / name for name in ['runtime_arm.cpp', 'scheduler.cpp', 'io.cpp', 'bus.cpp', 'tier3.cpp', 'task_au_setup.inc']]
    before = {str(path.relative_to(ROOT)): sha(path) for path in protected}
    build = json.loads((ROOT / 'build/task-aw5-capture-002/compile.json').read_text())
    for row in build:
        assert sha(Path(row['source'])) == row['source_sha256']
    for prefix in ['tools/task_aw2/', 'tools/task_aw3/', 'tools/task_aw4/', 'tools/task_aw5/']:
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', authority, prefix], cwd=ROOT, text=True).splitlines()
        for name in names:
            assert subprocess.check_output(['git', 'show', authority + ':' + name], cwd=ROOT).decode('utf-8-sig').splitlines() == (ROOT / name).read_text(encoding='utf-8-sig').splitlines()
    texts = {name: (SOURCE / name).read_text(encoding='utf-8-sig') for name in ['runtime_arm.cpp', 'io.cpp', 'bus.cpp', 'scheduler.cpp', 'tier3.cpp']}
    runtime_header = (ROOT / 'local/ndsrecomp/recompiler/armv4t/runtime_arm.h').read_text(encoding='utf-8-sig')
    original_header = subprocess.check_output(['git', '-C', str(SOURCE.parents[1]), 'show', 'HEAD:recompiler/armv4t/runtime_arm.h'], text=True)
    combine_signature = 'static inline uint32_t arm9_cycle_combine('
    assert function(runtime_header, combine_signature) == function(original_header, combine_signature)
    installation = json.loads((ROOT / 'local/task-aw5/installation.json').read_text())
    for name, expected_hash in installation['sources'].items():
        assert sha(SOURCE / name) == expected_hash
    selected = [('io.cpp', 'uint64_t active_system_timestamp()'), ('runtime_arm.cpp', 'void request_yield_poll()'),
                ('runtime_arm.cpp', 'extern "C" void nds_slice_begin('), ('runtime_arm.cpp', 'extern "C" void nds_reschedule_slice('),
                ('io.cpp', 'void start_div()'), ('io.cpp', 'void math_reg_write('),
                ('runtime_arm.cpp', 'extern "C" uint32_t runtime_deferred_cycles_take('),
                ('runtime_arm.cpp', 'void publish_fast_limit()'), ('bus.cpp', 'extern "C" uint32_t arm9_refill_cycles('),
                ('io.cpp', 'uint64_t nds_next_timer_overflow_time()'), ('io.cpp', 'bool nds_halt_wake_pending(')]
    fragments = [function(texts[name], signature) for name, signature in selected]
    fragments.append(function(runtime_header, 'static inline uint32_t arm9_cycle_combine('))
    rtc = function(texts['io.cpp'], 'void nds_tick_rtc(')
    due = rtc[rtc.index('    constexpr uint64_t numerator'):rtc.index('    while (g_rtc_processed_ticks')]
    fragments.append('inline uint64_t source_rtc_due(uint64_t system_cycles) {\n' + due + 'return due;\n}')
    (output / 'source_model.inc').write_text('\n\n'.join(fragments) + '\n')
    source_proof = {}
    for name, signature in selected:
        body = function(texts[name], signature)
        source_proof[name + ':' + signature] = hashlib.sha256(body.encode()).hexdigest()
    source_proof['runtime_arm.h:' + combine_signature] = hashlib.sha256(function(runtime_header, combine_signature).encode()).hexdigest()
    source_proof['io.cpp:RTC_due_expression'] = hashlib.sha256(due.encode()).hexdigest()
    tier = texts['tier3.cpp']
    assert 'g_yield_poll_hint' not in tier and 'runtime_should_yield(' not in tier and 'runtime_tick(' in tier
    assert tier.index('r = Interpreter::step') < tier.index('g_runtime_cycles += cyc + runtime_deferred_cycles_take()') < tier.index('Kind::cycle_commit') < tier.index('Kind::retired') < tier.index('if (poll_after && !ic.cpsr.i') < tier.index('if (poll_after && nds_slice_over())')
    schedule = texts['scheduler.cpp']
    start = schedule.index('void scheduler_run_round()')
    assert schedule.index('run_slice(0,', start) < schedule.index('nds_tick_timers(0,', start) < schedule.index('run_slice(1,', start) < schedule.index('nds_tick_rtc(rendezvous)', start)
    math_write = texts['io.cpp'][texts['io.cpp'].index('void nds_io_write('):]
    assert math_write.index('math_reg_write(addr, value, width)') < math_write.index('nds_tick_timers(cpu, g_runtime_cycles)')
    assert 'nds_tick_timers' not in function(texts['io.cpp'], 'void math_reg_write(')
    assert 'g_yield_poll_hint' not in function(texts['runtime_arm.cpp'], 'void publish_fast_limit()').split('{', 1)[1]
    (output / 'canonical.hex').write_text(snapshot['canonical_hex'] + '\n')
    tool = ROOT / 'local/toolchain/w64devkit/bin'
    environment = {key: value for key, value in os.environ.items() if not key.startswith('NDS_')}
    environment['PATH'] = str(tool) + os.pathsep + environment['PATH']
    logs = []

    def run(command, expected=0):
        child = subprocess.run(list(map(str, command)), cwd=ROOT, env=environment, capture_output=True, text=True, errors='replace', timeout=300)
        logs.append({'command': list(map(str, command)), 'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
        assert child.returncode == expected, child.stdout + child.stderr
        return child.stdout

    binary = output / 'aw6-test.exe'
    run([tool / 'g++.exe', '-std=c++20', '-O2', '-Wall', '-Wextra', '-I' + str(output), '-I' + str(SOURCE),
         '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), HERE / 'test.cpp',
         ROOT / 'build/task-o-sdl-runner/libnds_support.a', '-o', binary])
    unit = output / 'unit'
    unit.mkdir()
    unit_text = run([binary, 'unit', output / 'canonical.hex', unit])
    assertions = int(re.search(r'AW6 assertions: (\d+)', unit_text)[1])
    children = []
    for mode in ['success', 'entry', 'mutation', 'wrong-mmio', 'cost', 'missing', 'disabled']:
        directory = output / mode
        directory.mkdir()
        expected = 73 if mode == 'success' else 0 if mode == 'disabled' else 79
        run([binary, mode, output / 'canonical.hex', directory], expected)
        child_rows = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()] if mode != 'disabled' else []
        count = verify_chain(child_rows)
        if mode == 'success':
            assert count == 69 and child_rows[-1]['event'] == 'terminal'
        elif mode != 'disabled':
            assert child_rows[-1]['event'] == 'failure'
        else:
            assert (directory / 'disabled-normal-return').exists()
        for name in ['scheduler', 'device', 'IRQ', 'ARM7', 'guest', 'old-halt', 'shutdown', 'persistence']:
            assert not (directory / name).exists()
        children.append({'mode': mode, 'exit': expected, 'observations': count, 'reason': child_rows[-1]['reason'] if child_rows else 'normal disabled return'})
    assert before == {str(path.relative_to(ROOT)): sha(path) for path in protected}
    result = {'task': 'AW6', 'assertions': assertions, 'children': children, 'source_functions': source_proof,
              'contract_sources': {path.name: sha(path) for path in HERE.iterdir() if path.suffix in ['.h', '.cpp', '.py']},
              'protected_artifacts_unchanged': before, 'real_provider_not_linked': True,
              'actual_source_on_synthetic_scalar_rail': True, 'interpreter_and_guest_bus_not_linked': True,
              'BrainAge_guest_execution': False, 'runtime_BrainAge_MMIO': False, 'live_replay': False, 'AX_executed': False}
    (output / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'assertions': assertions, 'children': children}, indent=2))


if __name__ == '__main__':
    main()
