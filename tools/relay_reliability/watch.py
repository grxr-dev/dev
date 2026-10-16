"""Explicitly installed observer. Never dispatches tasks or delivers to a browser."""
import argparse
import json
from pathlib import Path
import sys
import time

from continuity import Store, Poller, atomic_status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge-source', type=Path, required=True)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    arguments = parser.parse_args()
    sys.path.insert(0, str(arguments.bridge_source.resolve()))
    from github_bus import GHClient
    store = Store(arguments.store)
    poller = Poller(store, GHClient('grxr-dev/codex-relay'), 'grxr-dev/codex-relay', 'grxr-dev')
    try:
        while True:
            exit_code = 0
            try:
                poller.tick()
                with store.db:
                    state = store.scan('grxr-dev/codex-relay', 'brainage-task-', paused=True)
                    store.health('continuity_watchdog', **state, last_success=time.time(), last_error=None)
            except Exception:
                exit_code = 1
            value = store.snapshot()
            atomic_status(str(arguments.store) + '.health.json', value)
            print(json.dumps(value, sort_keys=True), flush=True)
            if arguments.once:
                return exit_code
            time.sleep(value['workers'].get('github_poller', {}).get('next_retry_seconds', 10))
    finally:
        store.close()


if __name__ == '__main__':
    sys.exit(main())
