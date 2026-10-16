"""Export reviewed infrastructure source, never runtime state or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

FILES = ('bridge.py', 'reliability.py', 'relay_v2.py', 'relay_state.py', 'github_bus.py', 'completions.py',
         'inbox_local.py', 'inbox_queue.py', 'inbox_supersession.py', 'TrayController.cs', 'Stop-Bridge.ps1',
         'inbox-v1/recover_once.py', 'inbox-v1/supersede_watchdog.py')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    hashes = {}
    for name in FILES:
        source = args.bridge / name
        destination = here / 'runtime' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    (here / 'runtime-manifest.json').write_text(json.dumps({'schema': 'relay-runtime-source/1', 'files': hashes}, indent=2)+'\n')


if __name__ == '__main__':
    main()
