"""Read-only audit of the single capture; no runner launch or state normalization."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def decode(data):
    cursor = 0

    def number(width):
        nonlocal cursor
        assert cursor + width <= len(data)
        value = int.from_bytes(data[cursor:cursor + width], 'little')
        cursor += width
        return value

    def text():
        nonlocal cursor
        size = number(2)
        assert cursor + size <= len(data)
        value = data[cursor:cursor + size].decode('ascii')
        cursor += size
        return value

    assert data[:6] == b'AW2S\x01\x00'
    cursor = 6
    fields = {}
    for _ in range(number(4)):
        name = text()
        width = number(1)
        assert width in [1, 2, 4, 8] and name not in fields
        fields[name] = number(width)
    identities = {}
    for _ in range(number(4)):
        name = text()
        assert name not in identities
        identities[name] = text()
    assert cursor == len(data)
    return fields, identities


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    assert output.is_relative_to(ROOT / 'local/task-aw5') and not output.exists()
    output.mkdir(parents=True)
    captured = [json.loads(line) for line in (args.capture / 'capture.jsonl').read_text().splitlines()]
    assert captured[0]['event'] == 'aw5_handoff' and captured[-1]['event'] == 'failure'
    snapshots = [row for row in captured if row['event'] == 'canonical_snapshot']
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    canonical = bytes.fromhex(snapshot['canonical_hex'])
    assert hashlib.sha256(canonical).hexdigest() == snapshot['sha256']
    fields, identities = decode(canonical)
    audit = [json.loads(line) for line in (args.capture / 'audit.jsonl').read_text().splitlines()]
    steps = [row for row in audit if row['event'] == 'au_step']
    reads = [row for row in audit if row['event'] == 'au_read_event']
    writes = [row for row in audit if row['event'] == 'au_write_event']
    assert len(steps) == 8 and len(reads) == 9 and len(writes) == 1
    assert steps[-1]['pc'] == 0x02001980 and steps[-1]['insn9'] == 281098008
    assert fields['r15'] == 0x02001980 and fields['ordinal9'] == 281098008 and fields['ordinal7'] == 96026779
    assert fields['cycle9'] == 3416875721 and fields['cycle7'] == 1708437825
    assert fields['logical_saves'] == 0 and fields['flash_commits'] == 0 and fields['save_dirty'] == 0
    assert all(row['address'] < 0x04000000 for row in reads + writes)
    assert [row['address'] for row in reads if row['address'] == row['pc']] == [row['pc'] for row in steps[:-1]]
    assert not any(row['event'] in ['decision_stopped', 'disposable_exit'] for row in audit)
    session = json.loads((args.capture / 'session.json').read_text())
    assert session['exit_code'] == 79 and not session.get('emergency_process_termination')
    assert session['source_checkpoint_unchanged'] and session['source_save_unchanged'] and session['save_files_unchanged']
    assert hashlib.sha256((args.capture / 'source.state').read_bytes()).hexdigest() == session['checkpoint_sha256']
    assert not session['logical_request_trace_bytes'] and not session['flash_trace_bytes'] and not session['ordinary_final_save_written']
    (output / 'canonical.hex').write_text(snapshot['canonical_hex'] + '\n')
    tool = ROOT / 'local/toolchain/w64devkit/bin/g++.exe'
    binary = output / 'inspect.exe'
    commands = [[str(tool), '-std=c++20', '-O2', '-I' + str(ROOT / 'local/ndsrecomp/runner/src'),
                 '-I' + str(ROOT / 'local/ndsrecomp/recompiler/support'), str(ROOT / 'tools/task_aw5/inspect.cpp'),
                 str(ROOT / 'build/task-o-sdl-runner/libnds_support.a'), '-o', str(binary)],
                [str(binary), str(output / 'canonical.hex')]]
    logs = []
    for command in commands:
        child = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, errors='replace', timeout=120)
        logs.append({'command': command, 'exit': child.returncode, 'stdout': child.stdout, 'stderr': child.stderr})
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
        assert child.returncode == 0, child.stderr
    report = logs[-1]['stdout']
    assert 'full_schema: PASS' in report and 'AU_manifest: PASS' in report and 'journal: PASS' in report
    assert 'AW2_core_preflight: REJECT retained slice cap would return to scheduler' in report
    assert 'first_prospective_guard: REJECT ready/stale state: deferred7' in report
    assert 'modeled_cost_sum: 64' in report
    selected = {name: value for name, value in fields.items() if name.startswith(('capture.', 'hidden.', 'scheduler.', 'service.', 'div.', 'timer.'))}
    selected.update({name: fields[name] for name in ['cycle9', 'cycle7', 'ordinal9', 'ordinal7', 'deferred7', 'deferred9', 'system_timestamp', 'slice_cap', 'fast_limit', 'return_depth']})
    result = {'capture_safe': True, 'admission': 'REJECTED', 'terminal_reason': captured[-1]['reason'],
              'canonical_sha256': snapshot['sha256'], 'scalar_count': len(fields), 'identity_count': len(identities),
              'identities': identities, 'observed': selected, 'offline_checks': report.splitlines(),
              'AU_instructions': 7, 'AU_reads': 9, 'AU_writes': 1,
              'candidate_fetches': 0, 'candidate_instructions': 0, 'protected_MMIO_accesses': 0,
              'ordinary_halt_or_shutdown': False, 'forced_termination': False,
              'save_changed_bytes': 0, 'AX_certified': False, 'AX_executed': False,
              'entry_remaining_cap_cycles': fields['slice_cap'] - fields['cycle9'],
              'full_candidate_modeled_cycles': 64,
              'full_candidate_exceeds_entry_cap': fields['cycle9'] + 64 > fields['slice_cap'],
              'first_divider_deadline_if_executed': (fields['cycle9'] >> 1) + 34,
              'first_deadline_cpu_cap_if_executed': 2 * ((fields['cycle9'] >> 1) + 34)}
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['capture_safe', 'admission', 'terminal_reason', 'scalar_count', 'canonical_sha256', 'offline_checks']}, indent=2))


if __name__ == '__main__':
    main()
