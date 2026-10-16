"""Read-only build/route activation proof. No restart, token logging or admin mutation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge', type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.bridge.resolve()
    sys.path.insert(0, str(root))
    from reliability import LOADED_HASHES
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://127.0.0.1:8766/health', timeout=10) as response:
            health = json.load(response)
        capability = health.get('capabilities')
        loaded = capability is not None and capability.get('loaded_modules') == LOADED_HASHES
        record = json.loads((root / '.runtime/process.json').read_text())
        owner_matches = record['pid'] == health['bridge_pid'] and record['started_at'] == health['bridge_started_at']
        value = {'windows_loopback': 'HEALTHY', 'vm_to_host': 'NOT_TESTED', 'build_activated': loaded,
                 'owner_matches': owner_matches, 'pid': health['bridge_pid'], 'active_turn': health['turn_active'],
                 'restart_allowed_now': not health['turn_active'],
                 'admin_supersede_loaded': bool(capability and '/local/inbox/admin/supersede-watchdog' in capability.get('admin_routes', [])),
                 'continuity_gate': 'CLOSED_PENDING_CROSS_SIDE_ACCEPTANCE'}
        print(json.dumps(value, sort_keys=True))
        return 0 if loaded and owner_matches else 2
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'windows_loopback': 'ERROR', 'error': type(error).__name__, 'vm_to_host': 'UNKNOWN'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
