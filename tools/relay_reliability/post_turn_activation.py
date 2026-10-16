"""Single scheduled post-turn controller using the existing tray-owned managed pipe."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BRIDGE = ROOT / 'bridge'
RUNTIME = BRIDGE / '.runtime'
AREA = RUNTIME / 'post-turn-activation'
REQUEST = 'relay-resilience-post-turn-windows-activation-20261016-01'
TASK = 'MuseRelay-PostTurnActivation-20261016-01'
OLD_SOURCE = 'f2cc0cca8c661e2fe601f37050979988c3663da0d1b66672baf0d9a8f4179f65'
OLD_PID = 24184
WATCHDOG = 'jarvis-continuity-watchdog:1fe09e7e9c1dec11d6dbd2385e0fb9cb8697ab85ede379f0308cd467b361ec52'
TARGET = 'brainage-task-aw5-20261015-01:52508ca28d2650562bee990b9780e050cfbab9a3a3854699bfd05dc74d391bf4'
MODULES = ('bridge.py', 'reliability.py', 'relay_v2.py', 'relay_state.py', 'github_bus.py',
           'completions.py', 'inbox_local.py', 'inbox_queue.py', 'inbox_supersession.py')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        handle.write(canonical(value))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def process(pid):
    class Basic(ctypes.Structure):
        _fields_ = [('reserved', ctypes.c_void_p), ('peb', ctypes.c_void_p),
                    ('padding', ctypes.c_void_p * 2), ('pid', ctypes.c_void_p), ('parent', ctypes.c_void_p)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1400, False, pid)
    if not handle:
        raise RuntimeError('process_identity_unavailable')
    try:
        created, exited, kernel_time, user_time = (wintypes.FILETIME() for unused in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel_time), ctypes.byref(user_time)):
            raise RuntimeError('process_creation_unavailable')
        size = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            raise RuntimeError('process_image_unavailable')
        basic = Basic()
        required = wintypes.ULONG()
        native = ctypes.WinDLL('ntdll')
        native.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
        if native.NtQueryInformationProcess(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic), ctypes.byref(required)):
            raise RuntimeError('process_parent_unavailable')
        filetime = (created.dwHighDateTime << 32) | created.dwLowDateTime
        return {'pid': pid, 'parent': basic.parent or 0, 'image': image.value,
                'ticks': filetime + 504911232000000000, 'unix_started_at': filetime / 10000000 - 11644473600}
    finally:
        kernel.CloseHandle(handle)


def http(path='/health', local_admin=False, data=None):
    port = 18741 if local_admin else 8766
    headers = {}
    if local_admin:
        headers = {'X-Jarvis-Local': '1'}
        if path != '/local/inbox/capabilities':
            headers['X-Jarvis-Admin'] = (RUNTIME / 'inbox_recovery_admin.token').read_text(encoding='ascii').strip()
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request('http://127.0.0.1:' + str(port) + path,
        data=canonical(data).encode() if data is not None else None, headers=headers)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=90 if local_admin else 10) as response:
        raw = response.read(2*1024*1024+1)
        if len(raw) > 2*1024*1024:
            raise RuntimeError('http_response_bound')
        return json.loads(raw)


def process_exited(pid, ticks):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x101000, False, pid)
    if not handle:
        if ctypes.get_last_error() == 87:
            return True
        raise RuntimeError('old_exit_query_unavailable_not_exit_proof')
    try:
        created, exited, kernel_time, user_time = (wintypes.FILETIME() for unused in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel_time), ctypes.byref(user_time)):
            raise RuntimeError('old_exit_creation_query_failed')
        actual = ((created.dwHighDateTime << 32) | created.dwLowDateTime) + 504911232000000000
        if actual != ticks:
            raise RuntimeError('old_pid_reused_no_activation')
        result = kernel.WaitForSingleObject(handle, 0)
        if result not in (0, 258):
            raise RuntimeError('old_exit_wait_failed')
        return result == 0
    finally:
        kernel.CloseHandle(handle)


def database_sample():
    connection = sqlite3.connect((RUNTIME / 'completions.sqlite3').resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('BEGIN')
        row = connection.execute('SELECT request_id,state,terminal_at,codex_turn_id FROM requests WHERE request_id=?', (REQUEST,)).fetchone()
        active = [dict(item) for item in connection.execute('SELECT request_id,state FROM requests WHERE terminal_at IS NULL')]
        pending = connection.execute('SELECT count(*) FROM pending').fetchone()[0]
        outbox = [dict(item) for item in connection.execute('SELECT state,comment_id FROM github_outbox WHERE request_id=?', (REQUEST,))]
        return {'request': dict(row) if row else None, 'active': active, 'pending': pending, 'outbox': outbox}
    finally:
        connection.close()


def idle_reason(plan, health, sample):
    if health.get('bridge_pid') != plan['old']['pid'] or health.get('bridge_started_at') != plan['old_health_started_at']:
        return 'old_process_identity_changed'
    if health.get('bridge_source_sha256') != OLD_SOURCE:
        return 'old_loaded_build_changed'
    row = sample.get('request')
    if not row or row.get('codex_turn_id') != plan['turn_id']:
        return 'request_identity_changed'
    if not row.get('terminal_at'):
        return 'awaiting_exact_turn_terminal'
    if row.get('state') != 'COMPLETED':
        return 'exact_turn_not_successfully_completed'
    if health.get('turn_active') is not False or health.get('active_async_request') is not None:
        return 'bridge_active'
    if sample.get('active') or sample.get('pending') != 0:
        return 'other_request_active'
    if health.get('maintenance_active') or health.get('human_review_required') or not health.get('relay_ready'):
        return 'bridge_not_unambiguously_idle'
    if not sample.get('outbox') or any(part['state'] != 'CLOSED' or not part['comment_id'] for part in sample['outbox']):
        return 'awaiting_exact_result_github_publication'
    return None


def queue_sample():
    value = json.loads((RUNTIME / 'inbox_queue.json').read_text(encoding='utf-8-sig'))
    return {'watchdog': value['entries'].get(WATCHDOG), 'seq94': value['entries'].get(TARGET),
            'audit': value.get('superseded_watchdog'),
            'eligible': [key for key, entry in value['entries'].items() if entry['state'] in ('QUEUED', 'FAILED_RETRYABLE', 'DELIVERING')],
            'sha256': sha(RUNTIME / 'inbox_queue.json')}


def native(plan, mode):
    command = [str(AREA / 'managed_pipe.exe'), mode, str(plan['tray']['pid']), str(plan['old']['pid']),
               str(plan['tray']['ticks']), str(plan['old']['ticks']), plan['pipe_sha256']]
    result = subprocess.run(command, capture_output=True, timeout=15,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError('managed_channel_' + mode + '_failed')
    return json.loads(result.stdout)


def validate_sources(plan):
    for name, expected in plan['sources'].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError('armed_source_identity_changed:' + name)


def validate_capability(plan, health):
    capability = health.get('capabilities') or {}
    if health.get('bridge_pid') == plan['old']['pid'] or health.get('bridge_started_at', 0) <= plan['old_health_started_at']:
        raise RuntimeError('new_process_identity_not_proven')
    if capability.get('schema') != 'muse-capabilities/1' or capability.get('loaded_modules') != plan['modules']:
        raise RuntimeError('new_loaded_modules_mismatch')
    if capability.get('build_id') != plan['build_id'] or capability.get('pid') != health['bridge_pid']:
        raise RuntimeError('new_build_or_pid_mismatch')
    if capability.get('bind') != {'relay': ['127.0.0.1', 8766], 'inbox': ['127.0.0.1', 18741]}:
        raise RuntimeError('listener_manifest_mismatch')
    if not capability.get('admin_loaded') or '/local/inbox/admin/supersede-watchdog' not in capability.get('admin_routes', []):
        raise RuntimeError('supersession_capability_not_loaded')
    if capability.get('routes') != plan['routes'] or health.get('relay_ready') is not True:
        raise RuntimeError('route_manifest_or_readiness_mismatch')
    if health.get('relay_v2', {}).get('browser_enabled') is not False:
        raise RuntimeError('unexpected_browser_activation')
    return capability


def record(state, phase, **values):
    state.update(values, phase=phase, observed_at=time.time())
    state.setdefault('events', []).append({'phase': phase, 'at': state['observed_at']})
    atomic(AREA / 'evidence.json', state)


def wait_and_shutdown(plan, state):
    stable = []
    last_reason = None
    while time.time() < plan['deadline']:
        validate_sources(plan)
        try:
            health, sample = http(), database_sample()
            reason = idle_reason(plan, health, sample)
            if process(plan['old']['pid']) != plan['old'] or process(plan['tray']['pid']) != plan['tray']:
                raise RuntimeError('process_or_parent_identity_changed')
        except (OSError, ValueError, sqlite3.Error) as error:
            reason = 'passive_sample_unavailable:' + type(error).__name__
        if reason:
            stable = []
            if reason != last_reason:
                record(state, 'WAITING_FOR_TERMINAL', waiting_reason=reason)
                last_reason = reason
            if reason in ('old_process_identity_changed', 'old_loaded_build_changed', 'request_identity_changed', 'exact_turn_not_successfully_completed'):
                raise RuntimeError(reason)
            time.sleep(5)
            continue
        stable.append({'at': time.time(), 'health': {key: health.get(key) for key in
            ('bridge_pid', 'bridge_started_at', 'bridge_source_sha256', 'turn_active', 'active_async_request', 'maintenance_active')}, 'database': sample})
        if len(stable) < 4 or stable[-1]['at'] - stable[0]['at'] < 15:
            time.sleep(5)
            continue
        native(plan, 'probe')
        if idle_reason(plan, http(), database_sample()):
            stable = []
            time.sleep(5)
            continue
        record(state, 'IDLE_PROVEN', idle_transcript=stable, waiting_reason=None)
        record(state, 'MANAGED_IDLE_SHUTDOWN_REQUESTED')
        state['managed_command'] = native(plan, 'shutdown-if-idle')
        exit_deadline = time.time() + 120
        while time.time() < exit_deadline:
            if process_exited(plan['old']['pid'], plan['old']['ticks']):
                record(state, 'OLD_PROCESS_EXIT_PROVEN', old_exit_observed_at=time.time())
                return
            try:
                current = http()
                if current.get('bridge_pid') == plan['old']['pid'] and current.get('relay_ready') is True and current.get('turn_active') is True:
                    record(state, 'WAITING_FOR_TERMINAL', waiting_reason='new_turn_race_managed_if_idle_refused')
                    stable = []
                    break
            except (OSError, ValueError):
                pass
            time.sleep(1)
        else:
            raise RuntimeError('old_process_did_not_exit_no_force_kill')
    raise RuntimeError('idle_deadline_expired_no_action')


def report(state):
    sys.path.insert(0, str(BRIDGE))
    sys.path.insert(0, str(HERE))
    from github_bus import GHClient
    from continuity import Store, signal
    client = GHClient('grxr-dev/codex-relay')
    client.private()
    if client.call('user')['login'] != 'grxr-dev':
        raise RuntimeError('github_actor_mismatch')
    store = Store(AREA / 'report.sqlite3')
    try:
        body = '[WINDOWS-ACTIVATION-RESULT]\n' + canonical({
            'request_id': REQUEST, 'phase': state['phase'], 'old_pid': state['old']['pid'],
            'new_pid': state.get('new_health', {}).get('bridge_pid'),
            'new_started_at': state.get('new_health', {}).get('bridge_started_at'),
            'build_id': state.get('capability', {}).get('build_id'),
            'watchdog_disposition': (state.get('queue_after', {}).get('audit') or {}).get('disposition'),
            'seq94_preflight': state.get('seq94_preflight'), 'local_health': state.get('local_health'),
            'remote_transport': 'NOT_TESTED_BY_WINDOWS_ACTIVATOR', 'error': state.get('error'),
            'brainage_pause_after': 'AW16', 'aw17_created_or_authorized': False,
            'evidence': str(AREA / 'evidence.json')})
        state['github_comment_id'] = signal(store, client, 'grxr-dev/codex-relay', REQUEST + ':' + state['phase'], body)
    finally:
        store.close()


def scheduler_instances():
    script = '''
$ErrorActionPreference = 'Stop'
$service = New-Object -ComObject Schedule.Service
$service.Connect()
$task = $service.GetFolder([string][char]92).GetTask(''' + "'" + TASK + "'" + ''')
$instances = @($task.GetInstances(0) | ForEach-Object { @{instance=$_.InstanceGuid; engine_pid=$_.EnginePID; state=$_.State} })
@{state=$task.State; instances=$instances; action=$task.Definition.Actions.Item(1).Path; arguments=$task.Definition.Actions.Item(1).Arguments; logon_type=$task.Definition.Principal.LogonType} | ConvertTo-Json -Depth 5 -Compress
'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
        capture_output=True, timeout=20, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return json.loads(result.stdout)


def prove_scheduler(ancestors):
    for unused in range(10):
        if (AREA / 'registration.json').exists():
            break
        time.sleep(1)
    registration = json.loads((AREA / 'registration.json').read_text())
    metadata = scheduler_instances()
    expected_arguments = subprocess.list2cmdline([str(Path(__file__)), '--run'])
    if Path(metadata['action']) != Path(sys.executable).with_name('pythonw.exe') or metadata['arguments'] != expected_arguments or metadata['logon_type'] != 3:
        raise RuntimeError('scheduled_action_identity_changed')
    matches = [item for item in metadata['instances'] if item['instance'].lower() == registration['instance'].lower()]
    if len(matches) != 1 or matches[0]['state'] != 4:
        raise RuntimeError('scheduled_instance_not_unique_running')
    related = {ancestor['pid'] for ancestor in ancestors} | {ancestor['parent'] for ancestor in ancestors}
    if matches[0]['engine_pid'] not in related or matches[0]['engine_pid'] in (0, OLD_PID):
        raise RuntimeError('scheduler_engine_not_bound_to_worker')
    return metadata


def run():
    import msvcrt
    AREA.mkdir(parents=True, exist_ok=True)
    with (AREA / 'worker.lock').open('a+b') as lock:
        lock.seek(0)
        if lock.read(1) == b'':
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return
        plan = json.loads((AREA / 'plan.json').read_text(encoding='utf-8'))
        state = json.loads((AREA / 'evidence.json').read_text(encoding='utf-8'))
        if state['phase'] not in ('ARMED', 'WAITING_FOR_TERMINAL'):
            return
        try:
            validate_sources(plan)
            ancestors = []
            current = process(os.getpid())
            for unused in range(16):
                ancestors.append(current)
                if current['pid'] == plan['old']['pid'] or Path(current['image']).name.lower() == 'codex.exe':
                    raise RuntimeError('worker_not_independent_of_bridge_codex_tree')
                if not current['parent'] or current['parent'] == current['pid']:
                    break
                try:
                    current = process(current['parent'])
                except RuntimeError:
                    break
            scheduler_proof = prove_scheduler(ancestors)
            record(state, 'WAITING_FOR_TERMINAL', helper_pid=os.getpid(), ancestry=ancestors, scheduler_proof=scheduler_proof)
            wait_and_shutdown(plan, state)
            deadline = time.time() + 180
            while time.time() < deadline:
                try:
                    health = http()
                    capability = validate_capability(plan, health)
                    new_process = process(health['bridge_pid'])
                    if new_process['parent'] != plan['tray']['pid']:
                        raise RuntimeError('new_bridge_not_owned_by_existing_tray')
                    break
                except (OSError, ValueError, RuntimeError):
                    time.sleep(2)
            else:
                raise RuntimeError('managed_tray_did_not_activate_exact_build_no_manual_process_start')
            record(state, 'ACTIVATION_PROVEN', new_health=health, new_process=new_process,
                   capability=capability, local_health='HEALTHY', remote_transport='NOT_TESTED')
            local_capability = http('/local/inbox/capabilities', True)
            if local_capability.get('pid') != health['bridge_pid'] or local_capability.get('build_id') != plan['build_id']:
                raise RuntimeError('local_admin_listener_identity_mismatch')
            before = queue_sample()
            state['queue_before'] = before
            if not before['audit']:
                status = http('/local/inbox/admin/supersede-watchdog', True)
                if not status.get('evidence_verified') or status.get('proof_sha256') != plan['supersession_proof_sha256']:
                    raise RuntimeError('supersession_provenance_not_verified')
                if before['watchdog'] != plan['watchdog_before']:
                    raise RuntimeError('watchdog_entry_changed_since_arm')
                record(state, 'SUPERSESSION_POSTING', supersession_status=status)
                try:
                    state['supersession_response'] = http('/local/inbox/admin/supersede-watchdog', True,
                        {'delivery_id': WATCHDOG, 'expected_fingerprint': status['queue_fingerprint'],
                         'expected_proof_sha256': status['proof_sha256']})
                except (OSError, ValueError):
                    state['supersession_response'] = 'UNCERTAIN_READ_AUDIT_ONLY_NO_RESEND'
            after = queue_sample()
            audit = after['audit'] or {}
            if audit.get('disposition') != 'SUPERSEDED' or audit.get('delivery_id') != WATCHDOG or audit.get('proof_sha256') != plan['supersession_proof_sha256'] or hashlib.sha256(canonical(audit.get('proof')).encode()).hexdigest() != plan['supersession_proof_sha256'] or audit.get('entry_before') != plan['watchdog_before']:
                raise RuntimeError('audited_supersession_not_proven_no_resend')
            outcome = after['watchdog'].get('outcome') or {}
            if after['watchdog']['state'] != 'FAILED_PERMANENT' or outcome.get('state') != 'SUPERSEDED' or outcome.get('authorization_id') != audit.get('authorization_id') or after['watchdog'].get('delivered_at') is not None or after['watchdog']['attempt_count'] != 0:
                raise RuntimeError('unexpected_watchdog_delivery_or_attempt')
            if after['seq94'] != plan['seq94_before']:
                raise RuntimeError('seq94_mutated_unexpectedly')
            record(state, 'SUCCESS', queue_after=after, seq94_preflight={
                'state': after['seq94']['state'], 'attempt_count': after['seq94']['attempt_count'],
                'eligible_blockers': after['eligible'], 'queue_unblocked': not after['eligible'],
                'fresh_readiness_still_required': True, 'recovery_or_resend_performed': False})
        except Exception as error:
            record(state, 'FAILED_CLOSED', error=str(error) if isinstance(error, RuntimeError) else type(error).__name__)
        try:
            report(state)
        except Exception as error:
            state['github_report_error'] = type(error).__name__
        atomic(AREA / 'evidence.json', state)


def arm(repair=False):
    AREA.mkdir(parents=True, exist_ok=True)
    if (AREA / 'plan.json').exists():
        existing = json.loads((AREA / 'plan.json').read_text(encoding='utf-8'))
        if existing['request_id'] != REQUEST:
            raise RuntimeError('different_existing_one_shot_preserved')
        if repair:
            prior = json.loads((AREA / 'evidence.json').read_text())
            if prior.get('phase') != 'FAILED_CLOSED' or prior.get('error') != 'scheduled_independent_process_ancestry_not_proven' or any(event['phase'] not in ('ARMED', 'FAILED_CLOSED') for event in prior.get('events', [])):
                raise RuntimeError('pre_effect_repair_not_proven')
            metadata = scheduler_instances()
            if metadata['instances'] or metadata['state'] != 3:
                raise RuntimeError('prior_scheduled_instance_not_finished')
            health = http()
            if health['bridge_pid'] != existing['old']['pid'] or (health.get('active_async_request') or {}).get('request_id') != REQUEST or not health['turn_active']:
                raise RuntimeError('same_turn_no_action_repair_not_proven')
            queue = queue_sample()
            if queue['audit'] or queue['watchdog'] != existing['watchdog_before'] or queue['seq94'] != existing['seq94_before']:
                raise RuntimeError('pre_effect_queue_identity_changed')
            for name, expected in existing['sources'].items():
                if Path(name) != Path(__file__).relative_to(ROOT) and sha(ROOT / name) != expected:
                    raise RuntimeError('unrelated_armed_input_changed')
            archive = AREA / 'pre-effect-failure-001'
            archive.mkdir(exist_ok=False)
            for name in ('plan.json', 'evidence.json', 'registration.json'):
                with (archive / name).open('xb') as destination:
                    destination.write((AREA / name).read_bytes()); destination.flush(); os.fsync(destination.fileno())
            existing['pre_effect_repair'] = {'prior_plan_sha256': sha(archive / 'plan.json'),
                'prior_evidence_sha256': sha(archive / 'evidence.json'), 'at': time.time(), 'reason': prior['error']}
            existing['sources'][str(Path(__file__).relative_to(ROOT)).replace('\\', '/')] = sha(Path(__file__))
            atomic(AREA / 'plan.json', existing)
            record({'old': existing['old'], 'request_id': REQUEST, 'brainage_pause_after': 'AW16',
                    'pre_effect_failure_archive': str(archive)}, 'ARMED')
            script = "$ErrorActionPreference='Stop';$service=New-Object -ComObject Schedule.Service;$service.Connect();$task=$service.GetFolder([string][char]92).GetTask('" + TASK + "');$instance=$task.Run($null);Write-Output $instance.InstanceGuid"
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                capture_output=True, timeout=20, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            atomic(AREA / 'registration.json', {'task_name': TASK, 'instance': result.stdout.decode().strip(), 'registered_at': time.time()})
            for unused in range(30):
                current = json.loads((AREA / 'evidence.json').read_text())
                if current.get('phase') == 'FAILED_CLOSED':
                    raise RuntimeError('repaired_worker_failed:' + current.get('error', 'unknown'))
                if current.get('phase') == 'WAITING_FOR_TERMINAL' and current.get('helper_pid'):
                    print(canonical({'armed': True, 'task_name': TASK, 'helper_pid': current['helper_pid'], 'evidence': str(AREA / 'evidence.json')}))
                    return
                time.sleep(1)
            raise RuntimeError('repaired_worker_heartbeat_not_observed')
        print((AREA / 'evidence.json').read_text(encoding='utf-8'))
        return
    sys.path.insert(0, str(BRIDGE))
    from inbox_supersession import SupersessionPolicy, proof_sha
    from reliability import PUBLIC_ROUTES
    manifest = json.loads((HERE / 'runtime-manifest.json').read_text())
    authoritative = json.loads(subprocess.check_output(['git', 'show', 'e7746ae8de45a8ca899064e3d3db2f94fa7169d4:tools/relay_reliability/runtime-manifest.json'], cwd=ROOT / 'dev'))
    if manifest != authoritative or any(sha(BRIDGE / name) != expected for name, expected in manifest['files'].items()):
        raise RuntimeError('authoritative_hardening_source_manifest_mismatch')
    health = http()
    active = health.get('active_async_request') or {}
    if active.get('request_id') != REQUEST or health.get('bridge_pid') != OLD_PID or health.get('bridge_source_sha256') != OLD_SOURCE or health.get('turn_active') is not True:
        raise RuntimeError('exact_active_arming_turn_or_old_build_mismatch')
    old = process(health['bridge_pid'])
    process_record = json.loads((RUNTIME / 'process.json').read_text())
    if process_record['pid'] != old['pid'] or process_record['started_at'] != health['bridge_started_at'] or Path(process_record['script']) != BRIDGE / 'bridge.py':
        raise RuntimeError('managed_process_record_mismatch')
    tray_record = json.loads((RUNTIME / 'tray.json').read_text())
    tray = process(tray_record['pid'])
    if old['parent'] != tray['pid'] or tray_record['bridge_pid'] != old['pid'] or Path(tray['image']).name.lower() != 'powershell.exe':
        raise RuntimeError('existing_managed_tray_ownership_not_verified')
    channels = subprocess.run([str(AREA / 'managed_pipe.exe'), 'probe', str(tray['pid']), str(old['pid']),
        str(tray['ticks']), str(old['ticks']), '-'], capture_output=True, timeout=15, check=True)
    proof = SupersessionPolicy(RUNTIME).verify()
    queue = queue_sample()
    if queue['watchdog']['state'] != 'QUEUED' or queue['watchdog']['attempt_count'] != 0 or queue['audit']:
        raise RuntimeError('exact_unattempted_watchdog_not_available')
    modules = {name: sha(BRIDGE / name) for name in MODULES}
    source_paths = [Path(__file__), HERE / 'managed_pipe.cs', AREA / 'managed_pipe.exe',
                    HERE / 'continuity.py', HERE / 'runtime-manifest.json'] + [BRIDGE / name for name in MODULES]
    source_paths += [BRIDGE / name for name in ('inbox_recovery.py', 'inbox_wire.py', 'inbox_api.py')]
    source_paths += [RUNTIME / name for name in ('relay-v2.json', 'inbox-v1.json', 'inbox_readiness_request.json')]
    plan = {'schema': 'post-turn-activation/1', 'request_id': REQUEST, 'turn_id': active['codex_turn_id'],
            'old': old, 'tray': tray, 'old_health_started_at': health['bridge_started_at'],
            'pipe_sha256': json.loads(channels.stdout)['pipe_sha256'], 'modules': modules,
            'build_id': hashlib.sha256(json.dumps(modules, sort_keys=True).encode()).hexdigest(),
            'sources': {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in source_paths},
            'routes': PUBLIC_ROUTES, 'supersession_proof_sha256': proof_sha(proof),
            'watchdog_before': queue['watchdog'], 'seq94_before': queue['seq94'],
            'deadline': time.time() + 6*3600, 'armed_at': time.time(), 'task_name': TASK}
    with (AREA / 'plan.json').open('x', encoding='utf-8') as handle:
        handle.write(canonical(plan)); handle.flush(); os.fsync(handle.fileno())
    state = {'schema': 'post-turn-activation-evidence/1', 'request_id': REQUEST, 'old': old,
             'old_health_started_at': health['bridge_started_at'], 'old_source': OLD_SOURCE,
             'expected_build_id': plan['build_id'], 'brainage_pause_after': 'AW16', 'no_active_turn_restart': True}
    record(state, 'ARMED')
    name = TASK.replace("'", "''")
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    if not pythonw.is_file():
        raise RuntimeError('hidden_pythonw_runtime_required')
    executable = str(pythonw).replace("'", "''")
    arguments = subprocess.list2cmdline([str(Path(__file__)), '--run']).replace("'", "''")
    script = f'''
$ErrorActionPreference = 'Stop'
$service = New-Object -ComObject Schedule.Service
$service.Connect()
$folder = $service.GetFolder([string][char]92)
$definition = $service.NewTask(0)
$definition.RegistrationInfo.Description = 'One-use exact post-turn Muse managed activation; no Brain Age successor'
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$definition.Principal.UserId = $identity
$definition.Principal.LogonType = 3
$definition.Principal.RunLevel = 0
$definition.Settings.Enabled = $true
$definition.Settings.AllowDemandStart = $true
$definition.Settings.MultipleInstances = 2
$definition.Settings.DisallowStartIfOnBatteries = $false
$definition.Settings.StopIfGoingOnBatteries = $false
$definition.Settings.ExecutionTimeLimit = 'PT8H'
$action = $definition.Actions.Create(0)
$action.Path = '{executable}'
$action.Arguments = '{arguments}'
$action.WorkingDirectory = '{str(ROOT).replace(chr(39), chr(39)*2)}'
$registered = $folder.RegisterTaskDefinition('{name}', $definition, 2, $identity, $null, 3, $null)
$instance = $registered.Run($null)
Write-Output $instance.InstanceGuid
'''
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
            capture_output=True, timeout=30, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        state['scheduled_instance'] = result.stdout.decode().strip()
        if not state['scheduled_instance'].startswith('{'):
            raise RuntimeError('scheduled_instance_identity_unavailable')
        atomic(AREA / 'registration.json', {'task_name': TASK, 'instance': state['scheduled_instance'], 'registered_at': time.time()})
    except Exception:
        record(state, 'ARMING_FAILED', error='scheduled_task_registration_failed_no_restart')
        raise
    for unused in range(30):
        current = json.loads((AREA / 'evidence.json').read_text(encoding='utf-8'))
        if current.get('phase') == 'FAILED_CLOSED':
            raise RuntimeError('scheduled_worker_failed:' + current.get('error', 'unknown'))
        if current.get('phase') == 'WAITING_FOR_TERMINAL' and current.get('helper_pid'):
            state['helper_pid'] = current['helper_pid']
            break
        time.sleep(1)
    else:
        raise RuntimeError('scheduled_worker_heartbeat_not_observed')
    print(canonical({'armed': True, 'task_name': TASK, 'instance': state['scheduled_instance'],
                     'helper_pid': state['helper_pid'],
                     'evidence': str(AREA / 'evidence.json'), 'no_restart_during_active_turn': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--arm', action='store_true')
    choice.add_argument('--run', action='store_true')
    choice.add_argument('--repair-pre-effect', action='store_true')
    options = parser.parse_args()
    arm(repair=options.repair_pre_effect) if options.arm or options.repair_pre_effect else run()
