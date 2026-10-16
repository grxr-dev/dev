"""Loaded-build capabilities and durable worker telemetry; no inference or approvals."""
import hashlib
import json
import os
import re
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent
MODULES = ('bridge.py', 'reliability.py', 'relay_v2.py', 'relay_state.py', 'github_bus.py',
           'completions.py', 'inbox_local.py', 'inbox_queue.py', 'inbox_supersession.py')
LOADED_HASHES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in MODULES}
BUILD_ID = hashlib.sha256(json.dumps(LOADED_HASHES, sort_keys=True).encode()).hexdigest()
PUBLIC_ROUTES = {'GET': ['/health', '/capabilities', '/events/completions?after=N', '/results/{request_id}',
                        '/requests/active', '/requests/{request_id}', '/routes/status', '/chatgpt-inbox/{delivery_id}',
                        '/browser/events?after=N'],
                 'POST': ['/relay', '/echo', '/browser/ack', '/chatgpt-inbox']}
ADMIN_ROUTES = ['/local/inbox/admin/recovery-once', '/local/inbox/admin/supersede-watchdog']


def capabilities(bridge, server, started):
    inbox = getattr(server, 'inbox', None)
    counts = {}
    if inbox:
        with inbox.queue.lock:
            for entry in inbox.queue._entries.values():
                counts[entry['state']] = counts.get(entry['state'], 0) + 1
    return {'schema': 'muse-capabilities/1', 'pid': os.getpid(), 'started_at': started,
            'build_id': BUILD_ID, 'loaded_modules': LOADED_HASHES,
            'bind': {'relay': list(server.server_address), 'inbox': ['127.0.0.1', 18741] if inbox else None},
            'routes': PUBLIC_ROUTES, 'admin_routes': ADMIN_ROUTES if inbox else [],
            'admin_loaded': bool(inbox), 'queue_summary': counts,
            'inbox_delivery_degraded': not inbox or any(counts.get(state, 0) for state in
                ('NEEDS_REVIEW', 'FAILED_PERMANENT', 'FAILED_RETRYABLE')),
            'continuity_healthy': None, 'continuity_status': 'JARVIS_HEALTH_REQUIRED',
            'inbox_worker': dict(bridge.inbox_worker_health.value) if getattr(bridge,'inbox_worker_health',None) else None,
            'windows_loopback': 'HEALTHY', 'vm_to_host': 'NOT_OBSERVED',
            'active_turn': bridge.turn_lock.locked(), 'restart_allowed': not bridge.turn_lock.locked()}


class WorkerHealth:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.value = {'schema': 'muse-worker-health/1', 'last_success': None, 'last_error': None, 'failures': 0}
        if self.path.exists():
            value = json.loads(self.path.read_text(encoding='utf-8'))
            if value.get('schema') != self.value['schema']:
                raise ValueError('worker_health_schema')
            self.value = value

    def record(self, error=None, **fields):
        with self.lock:
            value = dict(self.value, observed_at=time.time(), last_error=error, **fields)
            value.update(worker=self.path.stem,pid=os.getpid(),build=BUILD_ID)
            value['failures'] = self.value['failures'] + 1 if error else 0
            if not error:
                value['last_success'] = time.time()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(self.path.name + '.' + str(os.getpid()) + '.tmp')
            with temporary.open('w', encoding='utf-8') as handle:
                json.dump(value, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            self.value = value
            return value


def assert_capability(value, operation, expected_pid=None, expected_build=None):
    if value.get('schema') != 'muse-capabilities/1':
        raise ValueError('capabilities_not_loaded_restart_required')
    if expected_pid is not None and value.get('pid') != expected_pid:
        raise ValueError('stale_pid')
    if expected_build is not None and value.get('build_id') != expected_build:
        raise ValueError('stale_build')
    if not value.get('admin_loaded') or operation not in value.get('admin_routes', []):
        raise ValueError('admin_operation_not_loaded')


def dispatch_paused(request):
    return request.get('request_id', '').startswith('brainage-task-')


def usage_reset(error):
    if not isinstance(error, dict):
        return None, 'RESET_TIME_REQUIRED'
    for name in ('resetsAt', 'reset_at', 'resetAt'):
        value = error.get(name)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            return str(value), 'RETRY_WAIT'
    match = re.search(r'try again at ([^\n]+?)\.(?:\s|$)', str(error.get('message', '')), re.IGNORECASE)
    if match:
        return match.group(1), 'RESET_ZONE_REQUIRED'
    return None, 'RESET_TIME_REQUIRED'
