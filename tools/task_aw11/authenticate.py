"""Read-only historical authentication; no replay, runner, or state-file access."""
import hashlib
import importlib.util
import json

from state import ROOT, FINAL, committed, load, require, validate


def main():
    authority = json.loads(committed('docs/BrainAge_TaskAW9_Result.json'))
    capture = ROOT / 'local/task-aw9/attempt-001/capture.jsonl'
    raw = capture.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == authority['audit_sha256'], 'AW9 audit identity')
    rows = [json.loads(line) for line in raw.splitlines()]
    spec = importlib.util.spec_from_file_location('aw6_chain_verifier', ROOT / 'tools/task_aw6/check.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    require(verifier.verify_chain(rows) == 69, 'complete AW9 canonical chain')
    observations = [row for row in rows if row['event'] == 'observation']
    require(observations[-1]['accepted'] and observations[-1]['index'] == 68 and
            observations[-1]['kind'] == 4 and observations[-1]['pc'] == 0x020019b0, 'retired terminal observation')
    snapshots = [row for row in rows if row['event'] == 'canonical_snapshot']
    require(snapshots[-1]['sha256'] == FINAL and
            bytes.fromhex(snapshots[-1]['canonical_hex']) == validate(load()), 'lossless promoted terminal metadata')
    require(rows[-1]['event'] == 'terminal' and not any(row['pc'] == 0x020019b4 for row in observations),
            'no forbidden successor observation')
    envelope = json.loads(committed('tools/task_aw8/certificate.json'))
    payload = envelope['certificate']
    require(hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == envelope['sha256'],
            'AW8 certificate')
    reference = ROOT / payload['local_evidence'] / 'success/audit.jsonl'
    reference_bytes = reference.read_bytes()
    require(hashlib.sha256(reference_bytes).hexdigest() == payload['success_audit_sha256'], 'AW8 reference identity')
    expected = [json.loads(line) for line in reference_bytes.splitlines()]
    require(verifier.verify_chain(expected) == 69, 'AW8 canonical chain')
    for event in ['canonical_snapshot', 'observation']:
        actual_sequence = [row for row in rows if row['event'] == event]
        expected_sequence = [row for row in expected if row['event'] == event]
        if event == 'canonical_snapshot':
            actual_sequence = actual_sequence[-len(expected_sequence):]
        require(actual_sequence == expected_sequence, 'AW9/AW8 exact historical full-state transcript: ' + event)
    require(hashlib.sha256(capture.read_bytes()).hexdigest() == authority['audit_sha256'], 'historical evidence changed')
    print(json.dumps({'historical_AW9_audit_sha256': authority['audit_sha256'], 'AW8_reference_exact_match': True,
        'observations': 69, 'promoted_terminal_exact_match': True, 'terminal_digest': FINAL,
        'new_guest_execution': False, 'runtime_MMIO': False}, indent=2))


if __name__ == '__main__':
    main()
