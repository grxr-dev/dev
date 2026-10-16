"""Reviewed source-only staging; never restarts, opens state databases, or sends messages."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--expected-current', help='reviewed SHA256 printed by dry-run; stages source only')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = args.bridge.resolve()
    manifest = json.loads((here / 'runtime-manifest.json').read_text())
    current = {}
    pending = []
    for name, expected in manifest['files'].items():
        source = (here / 'runtime' / name).resolve()
        target = (root / name).resolve()
        if not source.is_relative_to(here / 'runtime') or not target.is_relative_to(root) or source == target:
            raise ValueError('unsafe_source_or_target')
        if sha(source) != expected:
            raise ValueError('source_manifest_mismatch:' + name)
        current[name] = sha(target)
        if current[name] != expected:
            pending.append((source, target))
    fingerprint = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()
    print(json.dumps({'current_fingerprint': fingerprint, 'changes': [str(target.relative_to(root)) for source,target in pending],
                      'mode': 'SOURCE_ONLY', 'restart': False, 'queue_mutation': False}))
    if args.expected_current is None:
        return
    if args.expected_current != fingerprint:
        raise ValueError('reviewed_baseline_changed')
    backup = root / 'backups' / ('relay-reliability-' + datetime.datetime.now().strftime('%Y%m%dT%H%M%S%f'))
    if pending:
        backup.mkdir(parents=True, exist_ok=False)
    for source, target in pending:
        if sha(target) != current[str(target.relative_to(root)).replace('\\', '/')]:
            raise ValueError('concurrent_source_change')
        if target.exists():
            saved = backup / target.relative_to(root)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.stage.tmp')
        with temporary.open('wb') as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    print('Source staged. No process restarted; activation proof still required. Partial staging is recoverable by manifest recheck.')


if __name__ == '__main__':
    main()
