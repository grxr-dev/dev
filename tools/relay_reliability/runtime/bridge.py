"""Muse's fixed-workspace loopback relay. Python standard library only."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import hmac
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import threading
import time
from urllib.parse import urlsplit, parse_qs, unquote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from monitor import MonitorState, MonitorServer
from approvals import Approvals, ApprovalError, response_policy
from diagnostics import Diagnostics, safe_error
from completions import CompletionStore
from inbox_api import InboxApi
from inbox_queue import InboxQueue
from inbox_local import LocalInboxServer, read_body as read_inbox_body
from relay_v2 import recover as recover_requests, Service as V2Service, load_config, credential_read
from reliability import capabilities, dispatch_paused, WorkerHealth

BASE = Path(__file__).resolve().parent
INSTALL = json.loads((BASE / 'workspace.json').read_text(encoding='utf-8-sig'))
WORKSPACE = INSTALL['workspace']
MAX_BODY = 65536
PROCESS_STARTED = time.time()
# Captured once at import: disk edits must not make old processes claim the new build.
SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
PROBE = 'Reply exactly CODEX_BRIDGE_PROBE_OK. Do not run commands or modify files.'
DEFAULT_ROUTE = 'sol-high'
APPROVAL_POLICY = 'on-request'
APPROVAL_REVIEWER = 'auto_review'

def workspace_sandbox():
    return {'type': 'workspaceWrite', 'writableRoots': [WORKSPACE], 'networkAccess': False,
            'excludeTmpdirEnvVar': True, 'excludeSlashTmp': True}

ROUTES = {
    'sol-high': {'model': 'gpt-6.1-sol', 'effort': 'high'},
    'sol-medium': {'model': 'gpt-6.1-sol', 'effort': 'medium'},
    'sol-light': {'model': 'gpt-6.1-sol', 'effort': 'low'},  # Explicit workflow alias, never fallback.
    'astra-medium-new': {'model': 'gpt-6-astra', 'effort': 'medium'},
    'astra-medium': {'model': 'gpt-6-astra', 'effort': 'medium'},
}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def atomic_json(file, value):
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, file)


class BridgeError(Exception):
    pass


class ModelPolicyError(BridgeError):
    """A local/catalog mismatch must block before thread mutation or inference."""
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


class RPC:
    """Private, bridge-owned stdio process; no RPC methods exposed over HTTP."""
    def __init__(self, executable=INSTALL['codex_executable'], experimental=True):
        self.pending = {}
        self.events = queue.Queue()
        self.lock = threading.Lock()
        self.serial = 0
        self.closed = False
        self.reader_state = 'starting'
        self.writer_state = 'open'
        self.close_reason = None
        self.transport_error_class = None
        self.transport_error = None
        self.last_method = None
        self.proc = subprocess.Popen(
            [executable, 'app-server', '--listen', 'stdio://'], cwd=WORKSPACE,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding='utf-8', bufsize=1,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.call('initialize', {'clientInfo': {'name': 'muse_workspace_bridge',
                      'title': 'Muse Workspace Bridge', 'version': '1.0.0'},
                      'capabilities': {'experimentalApi': experimental}})
            self.notify('initialized', {})
        except Exception:
            self.close()
            raise

    def _read(self):
        self.reader_state = 'open'
        try:
            for line in self.proc.stdout:
                event = json.loads(line)
                if 'id' in event and 'method' not in event:
                    with self.lock:
                        waiter = self.pending.get(event['id'])
                    if waiter:
                        waiter.put(event)
                else:
                    self.events.put(event)
        except Exception as exc:
            self.reader_state = 'error'
            self.transport_error_class = type(exc).__name__
            self.transport_error = safe_error(exc)
        finally:
            if self.reader_state != 'error':
                self.reader_state = 'eof'
            self.closed = True
            with self.lock:
                for waiter in self.pending.values():
                    waiter.put({'error': {'message': 'App Server disconnected'}})
            self.events.put({'method': '__disconnected'})

    def send(self, event):
        with self.lock:
            if self.closed or self.proc.poll() is not None:
                raise BridgeError('App Server unavailable')
            self.last_method = event.get('method')
            try:
                self.proc.stdin.write(json.dumps(event, ensure_ascii=False) + '\n')
                self.proc.stdin.flush()
            except (OSError, ValueError) as exc:
                self.writer_state = 'broken'
                self.transport_error_class = type(exc).__name__
                self.transport_error = safe_error(exc)
                raise BridgeError('App Server stdin transport broke') from exc

    def notify(self, method, params):
        self.send({'method': method, 'params': params})

    def call(self, method, params, timeout=30):
        with self.lock:
            self.serial += 1
            ident = self.serial
            waiter = queue.Queue()
            self.pending[ident] = waiter
        try:
            self.send({'id': ident, 'method': method, 'params': params})
            try:
                answer = waiter.get(timeout=timeout)
            except queue.Empty:
                raise BridgeError('App Server RPC timeout: ' + method)
            if 'error' in answer:
                raise BridgeError(answer['error'].get('message', 'App Server RPC failed'))
            return answer['result']
        finally:
            with self.lock:
                self.pending.pop(ident, None)

    def close(self):
        self.close_reason = self.close_reason or 'local_shutdown'
        self.writer_state = 'closed'
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        self.closed = True


class Bridge:
    def __init__(self, state_file=None, rpc_factory=RPC, timeout=None, emit_diagnostics=False, approval_timeout=600):
        self.state_file = state_file or BASE / '.runtime' / 'thread.json'
        self.rpc_factory = rpc_factory
        self.rpc = None
        self.thread_id = None
        self.version = INSTALL['codex_version']
        self.timeout = timeout  # Optional explicit hard turn limit; production default is unlimited.
        self.submit_lock = threading.Lock()
        self.worker = None
        self.active_request_id = None
        self.turn_lock = threading.Lock()
        self.monitor = MonitorState(WORKSPACE)
        self.approvals = Approvals(self.monitor, approval_timeout)
        self.monitor.approvals = self.approvals
        self.accepting_work = True
        self.operation = 'startup'
        self.human_review_required = False
        self.stop_reason = None
        self.maintenance_active = False
        self._last_ready = False
        self.diagnostics = Diagnostics(self.state_file.with_name('diagnostics.json'), emit_diagnostics)
        self.monitor.diagnostics = self.local_diagnostics
        self.error = None
        self.thread_status = 'not_created'
        self.route_id = DEFAULT_ROUTE
        self.requested_model = ROUTES[DEFAULT_ROUTE]['model']
        self.requested_effort = ROUTES[DEFAULT_ROUTE]['effort']
        self.allowed_models = sorted({route['model'] for route in ROUTES.values()})
        self.sol_thread_id = None
        self.astra_state_file = self.state_file.with_name(self.state_file.stem + '-astra.json')
        self.thread_state_files = {
            'sol-high': self.state_file,  # Legacy main file keeps the original High identity.
            'sol-medium': self.state_file.with_name(self.state_file.stem + '-sol-medium.json'),
            'sol-light': self.state_file.with_name(self.state_file.stem + '-sol-light.json'),
            'astra-latest': self.astra_state_file,
        }
        self.threads = {}
        self.route_errors = {}
        self.prepared_threads = {}
        self.monitor.routing = self.routing_snapshot
        self.model_catalog = []
        self.catalog_status = 'not_checked'
        self.catalog_checked_at = None
        self.model_status = 'not_checked'
        self.model_error = None
        self.active_model = None
        self.active_effort = None
        self.backend_rejections = {}
        if self.state_file.exists():
            state = json.loads(self.state_file.read_text(encoding='utf-8'))
            if state.get('workspace') != WORKSPACE or state.get('thread_key') != 'main':
                raise BridgeError('Persisted workspace identity mismatch')
            self.thread_id = state['thread_id']
            self.thread_status = 'saved'
            self.sol_thread_id = self.thread_id
            self.threads['sol-high'] = {'id': self.thread_id, 'status': 'saved', 'model': None, 'effort': None}
        for alias in ('sol-medium', 'sol-light'):
            file = self.thread_state_files[alias]
            if file.exists():
                state = json.loads(file.read_text(encoding='utf-8'))
                if state.get('workspace') != WORKSPACE or state.get('thread_key') != alias:
                    raise BridgeError('Persisted route workspace identity mismatch')
                self.threads[alias] = {'id': state['thread_id'], 'status': 'saved',
                                       'model': state.get('model'), 'effort': state.get('effort'),
                                       **({'replaced_thread': state['replaced_thread']} if 'replaced_thread' in state else {})}
        if self.astra_state_file.exists():
            state = json.loads(self.astra_state_file.read_text(encoding='utf-8'))
            if state.get('workspace') != WORKSPACE or state.get('thread_key') != 'astra-latest':
                raise BridgeError('Persisted Astra workspace identity mismatch')
            self.threads['astra-latest'] = {'id': state['thread_id'], 'status': 'saved',
                                          'model': state.get('model'), 'effort': state.get('effort'),
                                       **({'replaced_thread': state['replaced_thread']} if 'replaced_thread' in state else {})}

        self.completions = CompletionStore(self.state_file.with_name("completions.sqlite3"), recover_pending=False)
        self.monitor.relay_v2_errors = self.completions.ledger.errors
        self.monitor.durable_requests = self.completions.ledger.history
        self.v2 = None
        self.monitor.completions = self.completions.summary
        self.monitor.request_state = self._approval_state
        self.monitor.hard_turn_timeout_seconds = self.timeout

    def connect(self):
        self.operation = 'app_server_connect'
        try:
            self.rpc = self.rpc_factory()
            self.prepared_threads.clear()
            recover_requests(self)
            if self.completions.active():
                self.resolve_model_policy()
                return True  # Read-only recovery found an active turn; never resume/mutate it.
            try:
                # Migrate only known identities; never create Medium/Light/Astra here.
                for alias in list(self.threads):
                    self._select_route('astra-medium' if alias == 'astra-latest' else alias)
                    try:
                        self.ensure_thread()
                    except ModelPolicyError:
                        pass  # An unrelated route mismatch must not overwrite another identity.
                self._select_route(DEFAULT_ROUTE)
                if self.thread_id:
                    self.ensure_thread()
                else:
                    self.resolve_model_policy()
            except ModelPolicyError:
                # Retain a healthy private RPC for diagnostics. Relay stays blocked.
                pass
            self.error = None
            return True
        except Exception as exc:
            self.error = safe_error(exc)
            self._diagnose('connect_failed', type(exc).__name__, safe_error(exc))
            if self.rpc:
                self.rpc.close()
            self.rpc = None
            return False

    def _select_route(self, route_id):
        if not isinstance(route_id, str) or route_id not in ROUTES:
            self._model_block('invalid_route', 'Unknown symbolic route_id')
        self.route_id = route_id
        self.requested_model = ROUTES[route_id]['model']
        self.requested_effort = ROUTES[route_id]['effort']
        row = self.threads.get(self.thread_alias(), {})
        self.thread_id = None if route_id == 'astra-medium-new' else row.get('id')
        self.active_model = row.get('model') if self.thread_id else None
        self.active_effort = row.get('effort') if self.thread_id else None
        self.thread_status = row.get('status', 'not_created') if self.thread_id else 'not_created'

    def thread_alias(self):
        return 'astra-latest' if self.route_id in ('astra-medium-new', 'astra-medium') else self.route_id

    def known_threads(self):
        return {alias: dict(row) for alias, row in list(self.threads.items())}

    def routing_snapshot(self):
        return {'selected_route': self.route_id, 'route_id': self.route_id, 'thread_alias': self.thread_alias(),
                'thread_id': self.thread_id, 'model': self.active_model, 'effort': self.active_effort,
                'requested_model': self.requested_model, 'requested_effort': self.requested_effort,
                'persistent_threads': self.known_threads(), 'approval_policy': APPROVAL_POLICY,
                'approvals_reviewer': APPROVAL_REVIEWER}

    def _route_status(self, route_id):
        route = ROUTES[route_id]
        matches = [row for row in self.model_catalog if row['model'] == route['model']]
        if self.catalog_status != 'resolved':
            return 'catalog_unavailable'
        if len(matches) != 1:
            return 'model_unavailable'
        efforts = [entry.get('reasoningEffort') for entry in matches[0].get('supportedReasoningEfforts') or []
                   if isinstance(entry, dict)]
        if route['effort'] not in efforts:
            return 'effort_unavailable'
        if route['model'] in self.backend_rejections:
            return 'backend_unavailable'
        if route_id in self.route_errors:
            return self.route_errors[route_id]['status']
        if route_id == 'astra-medium' and not self.threads.get('astra-latest', {}).get('id'):
            return 'astra_thread_missing'
        return 'available'

    def _model_block(self, status, message, error_class='ModelPolicyError'):
        message = safe_error(message)
        self.model_status = status
        self.model_error = message
        if status in ('thread_model_mismatch', 'thread_identity_mismatch'):
            self.route_errors[self.route_id] = {'status': status, 'message': message}
        self._diagnose(status, error_class, safe_error(message))
        raise ModelPolicyError(status, message)

    def resolve_model_policy(self, source=None):
        """Read the actual private server catalog; no substitution or model turn."""
        if source:
            self.operation = source
        self.model_status = 'checking'
        self.model_error = None
        rows, cursor, seen = [], None, set()
        try:
            for _ in range(20):
                params = {'includeHidden': True, 'limit': 100}
                if cursor is not None:
                    params['cursor'] = cursor
                result = self.rpc.call('model/list', params)
                page = result.get('data')
                if not isinstance(page, list):
                    raise BridgeError('Invalid model/list response')
                for entry in page:
                    if not isinstance(entry, dict) or not isinstance(entry.get('model'), str):
                        raise BridgeError('Invalid model/list entry')
                    rows.append({key: entry.get(key) for key in (
                        'id', 'model', 'displayName', 'hidden', 'isDefault',
                        'defaultReasoningEffort', 'supportedReasoningEfforts')})
                cursor = result.get('nextCursor')
                if cursor is None:
                    break
                if not isinstance(cursor, str) or cursor in seen:
                    raise BridgeError('Invalid model/list cursor')
                seen.add(cursor)
            else:
                raise BridgeError('Model catalog pagination limit exceeded')
        except Exception as exc:
            self.model_catalog = []  # Never authorize using stale catalog data.
            self.catalog_status = 'unavailable'
            self._model_block('catalog_unavailable', 'Cannot resolve model catalog: ' + str(exc), type(exc).__name__)
        self.model_catalog = rows
        self.catalog_status = 'resolved'
        self.catalog_checked_at = time.time()
        if not isinstance(self.requested_model, str) or self.requested_model not in self.allowed_models:
            self._model_block('model_not_allowed', 'Requested model is not locally allowlisted')
        matches = [entry for entry in rows if entry['model'] == self.requested_model]
        if len(matches) != 1:
            self._model_block('model_unavailable',
                'Requested model ' + self.requested_model + ' is absent or ambiguous in this App Server catalog; no fallback')
        efforts = matches[0].get('supportedReasoningEfforts') or []
        allowed_efforts = [e.get('reasoningEffort') for e in efforts if isinstance(e, dict)]
        if not isinstance(self.requested_effort, str) or self.requested_effort not in allowed_efforts:
            self._model_block('effort_unavailable', 'Requested reasoning effort is not advertised for ' + self.requested_model)
        if self.requested_model in self.backend_rejections:
            self._model_block('backend_unavailable', self.backend_rejections[self.requested_model])
        self.model_status = 'catalog_supported'
        return matches[0]

    def _read_thread_metadata(self):
        try:
            result = self.rpc.call('thread/read', {'threadId': self.thread_id, 'includeTurns': False})
        except BridgeError as exc:
            if str(exc) != 'thread not loaded: ' + self.thread_id:
                raise
            # A cold thread is not evidence of loss. Load without model/effort
            # overrides; only an explicit missing-rollout response allows replacement.
            result = self.rpc.call('thread/resume', {'threadId': self.thread_id})
        self._check_cwd(result)
        self.active_model = result['thread'].get('model')
        self.active_effort = result['thread'].get('reasoningEffort')
        return result

    def _check_cwd(self, result):
        actual = result.get('thread', {}).get('cwd')
        if actual != WORKSPACE or ('cwd' in result and result['cwd'] != WORKSPACE):
            self.human_review_required = True
            self.stop_reason = 'workspace_mismatch'
            raise BridgeError('Codex thread cwd mismatch; refusing relay')

    def ensure_thread(self, fresh=False):
        if not self.rpc or self.rpc.closed:
            raise BridgeError('App Server unavailable; restart bridge')
        self.resolve_model_policy()  # Must pass before thread/start or thread/resume.
        alias = self.thread_alias()
        fresh = self.route_id == 'astra-medium-new'
        row = self.threads.get(alias, {})
        expected_id = None if fresh else row.get('id')
        if self.route_id == 'astra-medium' and not expected_id:
            self._model_block('astra_thread_missing', 'No astra-latest thread exists; explicitly select astra-medium-new first')
        self.thread_id = expected_id
        if alias != 'sol-high' and expected_id and expected_id == self.sol_thread_id:
            self._model_block('thread_identity_mismatch', 'Route alias points to the High thread; refusing resume')
        policy = {'cwd': WORKSPACE, 'model': self.requested_model,
                  'config': {'model_reasoning_effort': self.requested_effort}, 'sandbox': 'workspace-write',
                  'runtimeWorkspaceRoots': [WORKSPACE],
                  'approvalPolicy': APPROVAL_POLICY, 'approvalsReviewer': APPROVAL_REVIEWER}
        replacement = None
        cached = False
        if expected_id:
            try:
                before = self._read_thread_metadata()
                thread = before['thread']
                if thread.get('id') != expected_id:
                    self._model_block('thread_identity_mismatch', 'App Server read an unexpected route thread identity')
                if (thread.get('model'), thread.get('reasoningEffort')) != (self.requested_model, self.requested_effort):
                    self._model_block('thread_model_mismatch', 'Persisted ' + alias + ' thread model/effort differs from selected route; refusing resume and inference')
                if thread.get('status', {}).get('type') == 'active':
                    self.human_review_required = True
                    self.stop_reason = 'saved_thread_active'
                    raise BridgeError('Saved thread is still active; refusing another turn')
                path = thread.get('path')
                if expected_id in self.prepared_threads and path and not Path(path).is_file():
                    result = {**self.prepared_threads[expected_id], 'thread': thread}
                    cached = True  # Same RPC's verified, zero-turn thread is still loaded.
                else:
                    result = self.rpc.call('thread/resume', {'threadId': expected_id, **policy})
                self.thread_status = 'prepared' if cached else 'resumed'
            except BridgeError as exc:
                if str(exc) != 'no rollout found for thread id ' + expected_id:
                    raise  # Transport, model, permission and ambiguous errors are not missing threads.
                if self.human_review_required or (self.completions.active() or {}).get('codex_thread_id') == expected_id:
                    raise BridgeError('Missing route thread has unresolved work; refusing replacement') from exc
                if self.route_id == 'astra-medium':
                    self._model_block('astra_thread_missing', 'Saved Astra rollout is missing; explicitly select astra-medium-new')
                replacement = {'thread_id': expected_id, 'reason': 'rollout_missing'}
                atomic_json(self.thread_state_files[alias].with_suffix('.missing.json'),
                            {'thread_key': alias, 'workspace': WORKSPACE, **replacement})
                expected_id = None
        if not expected_id:
            result = self.rpc.call('thread/start', {**policy, 'ephemeral': False})
            self.thread_status = 'created'
        self._check_cwd(result)
        returned_id = result['thread']['id']
        if expected_id and returned_id != expected_id:
            self._model_block('thread_identity_mismatch', 'App Server resumed an unexpected thread identity')
        if not expected_id and any(returned_id == known['id'] for known in self.threads.values()):
            self._model_block('thread_identity_mismatch', 'New route thread reused an existing persistent identity')
        if cached:
            self._verify_thread_permissions(result)
        else:
            result = self._configure_thread_permissions(returned_id, initial=result if not expected_id else None)
        self._check_cwd(result)
        if result['thread']['id'] != returned_id:
            raise BridgeError('Permission readback changed thread identity; refusing relay')
        self.active_model = result.get('model')
        self.active_effort = result.get('reasoningEffort')
        if (self.active_model, self.active_effort) != (self.requested_model, self.requested_effort):
            self._model_block('thread_model_mismatch', 'App Server did not honor explicit model/effort; refusing inference')
        self.model_status = 'ready'
        self.route_errors.pop(self.route_id, None)
        self.thread_id = returned_id
        if alias == 'sol-high':
            self.sol_thread_id = returned_id
            # Preserve the legacy file/schema and never write it for Medium/Light/Astra.
            state = {'thread_key': 'main', 'thread_id': returned_id, 'workspace': WORKSPACE}
        else:
            state = {'thread_key': alias, 'thread_id': returned_id, 'workspace': WORKSPACE,
                     'model': self.active_model, 'effort': self.active_effort}
        if replacement or row.get('replaced_thread'):
            state['replaced_thread'] = replacement or row['replaced_thread']
        atomic_json(self.thread_state_files[alias], state)
        self.threads[alias] = {'id': returned_id, 'model': self.active_model,
                               'effort': self.active_effort, 'status': self.thread_status,
                               'approval_policy': result['approvalPolicy'],
                               'approvals_reviewer': result['approvalsReviewer'],
                               'sandbox_policy': result['sandbox'], 'permissions_verified': True,
                               **({'replaced_thread': state['replaced_thread']} if 'replaced_thread' in state else {})}
        return result

    def _verify_thread_permissions(self, value):
        sandbox = value.get('sandboxPolicy', value.get('sandbox', {}))
        roots = sandbox.get('writableRoots', [])
        if (value.get('approvalPolicy') != APPROVAL_POLICY or value.get('approvalsReviewer') != APPROVAL_REVIEWER
                or sandbox.get('type') != 'workspaceWrite' or sandbox.get('networkAccess') is not False
                or sandbox.get('excludeTmpdirEnvVar') is not True or sandbox.get('excludeSlashTmp') is not True
                or not isinstance(roots, list) or any(not isinstance(root,str) or os.path.normcase(os.path.normpath(root)) != os.path.normcase(os.path.normpath(WORKSPACE)) for root in roots)):
            raise BridgeError('App Server did not honor bounded auto-review permissions; refusing inference')

    def _configure_thread_permissions(self, thread_id, initial=None):
        # Fresh zero-turn threads have no resumable rollout yet. The settings event
        # is authoritative for their live effective permissions; don't resume them.
        held = []
        if initial is not None:
            while True:
                try: event = self.rpc.events.get_nowait()
                except queue.Empty: break
                if event.get('method') != 'thread/settings/updated': held.append(event)
        try:
            self.rpc.call('thread/settings/update', {'threadId': thread_id, 'approvalPolicy': APPROVAL_POLICY,
                'approvalsReviewer': APPROVAL_REVIEWER, 'sandboxPolicy': workspace_sandbox()})
            if initial is None:
                readback = self.rpc.call('thread/resume', {'threadId': thread_id})
            else:
                deadline = time.monotonic() + 3
                settings = None
                while time.monotonic() < deadline:
                    try: event = self.rpc.events.get(timeout=min(.1, max(.001, deadline-time.monotonic())))
                    except queue.Empty: continue
                    if event.get('method') == 'thread/settings/updated' and event.get('params', {}).get('threadId') == thread_id:
                        settings = event['params']['threadSettings']; break
                    held.append(event)
                if settings is None:
                    raise BridgeError('Fresh thread effective settings not verified; refusing inference')
                if settings.get('cwd') != WORKSPACE:
                    raise BridgeError('Fresh thread settings cwd mismatch; refusing inference')
                readback = {**initial, 'cwd': settings['cwd'], 'model': settings.get('model'),
                    'reasoningEffort': settings.get('effort'), 'approvalPolicy': settings.get('approvalPolicy'),
                    'approvalsReviewer': settings.get('approvalsReviewer'), 'sandbox': settings.get('sandboxPolicy')}
            self._verify_thread_permissions(readback)
            if initial is not None:
                self.prepared_threads[thread_id] = readback
            return readback
        finally:
            for event in held: self.rpc.events.put(event)

    def recovery_status(self):
        if self.human_review_required:
            return {'recoverable': False, 'reason': self.stop_reason or 'human_review_required',
                    'message': 'Human review required; no automatic restart or request replay'}
        if not self.accepting_work:
            return {'recoverable': False, 'reason': 'shutdown', 'message': 'Bridge stopping'}
        if DEFAULT_ROUTE in self.route_errors or self.backend_rejections:
            return {'recoverable': False, 'reason': self.model_status, 'message': 'Model/thread policy requires human review'}
        if not self.rpc or self.rpc.closed or self.rpc.proc.poll() is not None:
            return {'recoverable': True, 'reason': 'rpc_transport_unavailable', 'message': 'Private App Server/RPC unavailable'}
        if self.approvals.pending():
            return {'recoverable': False, 'reason': 'approval_required',
                    'message': 'Awaiting a local human decision; same turn remains active'}
        if self.catalog_status != 'resolved':
            return {'recoverable': True, 'reason': 'catalog_refresh_failed',
                    'message': safe_error(self.model_error or 'Catalog is not resolved')}
        if self._route_status(DEFAULT_ROUTE) != 'available':
            return {'recoverable': False, 'reason': self._route_status(DEFAULT_ROUTE), 'message': 'Default Sol route unavailable; no fallback'}
        return {'recoverable': False, 'reason': 'none', 'message': 'Ready'}

    def rpc_snapshot(self):
        rpc = self.rpc
        return {'process_alive': bool(rpc and rpc.proc.poll() is None),
            'process_id': getattr(getattr(rpc, 'proc', None), 'pid', None),
            'exit_code': rpc.proc.poll() if rpc else None,
            'rpc_closed': bool(not rpc or rpc.closed),
            'reader_state': getattr(rpc, 'reader_state', 'unknown'),
            'writer_state': getattr(rpc, 'writer_state', 'unknown'),
            'close_reason': self.stop_reason or getattr(rpc, 'close_reason', None),
            'transport_error_class': getattr(rpc, 'transport_error_class', None),
            'transport_error': getattr(rpc, 'transport_error', None),
            'last_method': getattr(rpc, 'last_method', None)}

    def _diagnose(self, reason, error_class=None, message=None, source=None):
        self.diagnostics.record({'reason': reason, 'source': source or self.operation, 'last_operation': self.operation,
            'error_class': error_class, 'message': message,
            'rpc': self.rpc_snapshot(), 'catalog_status': self.catalog_status,
            'catalog_rows': len(self.model_catalog), 'model_list_result': self.catalog_status,
            'requested_model': self.requested_model, 'requested_effort': self.requested_effort,
            'thread_status': self.thread_status, 'thread_id': self.thread_id,
            'turn_active': self.turn_lock.locked() and not self.maintenance_active,
            'human_review_required': self.human_review_required})

    def local_diagnostics(self):
        return {'records': self.diagnostics.snapshot(), 'rpc': self.rpc_snapshot(),
                'recovery': self.recovery_status()}

    def refresh_catalog(self):
        # Never contend with a relay preflight or a running turn.
        if not self.accepting_work or self.human_review_required or not self.turn_lock.acquire(blocking=False):
            return False
        self.maintenance_active = True
        try:
            if not self.rpc or self.rpc.closed or self.rpc.proc.poll() is not None:
                return False
            self.resolve_model_policy(source='periodic_refresh')
            self.health()  # Record a READY -> NOT READY transition locally.
            return True
        except ModelPolicyError:
            self.health()
            return False
        finally:
            self.maintenance_active = False
            self.turn_lock.release()

    def stop_if_idle(self):
        if not self.turn_lock.acquire(blocking=False):
            return False
        try:
            self.accepting_work = False
            return True
        finally:
            self.turn_lock.release()

    def health(self):
        available = bool(self.rpc and not self.rpc.closed and self.rpc.proc.poll() is None)
        ready = bool(self.accepting_work and not self.human_review_required and available
                     and self._route_status(DEFAULT_ROUTE) == 'available'
                     and DEFAULT_ROUTE not in self.route_errors)
        if self._last_ready and not ready:
            failure = self.recovery_status()
            self._diagnose('ready_to_not_ready', message=failure['reason'] + ': ' + failure['message'], source='health_poll')
        self._last_ready = ready
        return {'ok': True, 'bridge_healthy': True, 'codex_available': available,
                'bridge_source_sha256': SOURCE_SHA256, 'bridge_pid': os.getpid(),
                'bridge_started_at': PROCESS_STARTED,
                'recovery': self.recovery_status(), 'human_review_required': self.human_review_required,
                'approval_pending': self.approvals.pending(), 'approval_timeout_seconds': self.approvals.timeout,
                'rpc_process_alive': bool(self.rpc and self.rpc.proc.poll() is None),
                'rpc_process_id': getattr(getattr(self.rpc, 'proc', None), 'pid', None),
                'rpc_exit_code': self.rpc.proc.poll() if self.rpc else None,
                'maintenance_active': self.maintenance_active,
                'codex_version': self.version, 'codex_executable': INSTALL['codex_executable'],
                'model': self.active_model, 'reasoning_effort': self.active_effort,
                'requested_model': self.requested_model, 'requested_reasoning_effort': self.requested_effort,
                'model_status': self.model_status, 'model_error': self.model_error,
                'default_route': DEFAULT_ROUTE,
                'allowed_routes': {rid: {**route, 'status': self._route_status(rid)} for rid, route in ROUTES.items()},
                'active_route': self.route_id, 'selected_route': self.route_id,
                'threads': {**self.known_threads(), **({'main': dict(self.threads['sol-high'])} if 'sol-high' in self.threads else {})},
                'route_thread_aliases': {rid: 'astra-latest' if rid.startswith('astra-') else rid for rid in ROUTES},
                'route_errors': dict(self.route_errors), 'active_thread_alias': self.thread_alias(),
                'relay_ready': ready,
                'model_catalog_status': self.catalog_status, 'model_catalog_checked_at': self.catalog_checked_at,
                'model_catalog': self.model_catalog, 'allowed_models': self.allowed_models,
                'workspace': WORKSPACE,
                'thread_key': 'main' if self.thread_id else None,
                'codex_thread_id': self.thread_id, 'thread_status': self.thread_status,
                'turn_active': self.turn_lock.locked() and not self.maintenance_active, 'sandbox': 'workspace-write',
                'approval_policy': APPROVAL_POLICY, 'approvals_reviewer': APPROVAL_REVIEWER,
                'effective_approval_settings': self.threads.get(self.thread_alias(), {}),
                'connectivity_error': self.error,
                'active_async_request': self.completions.active() if self.completions else None,
                'last_terminal_request': self.completions.summary() if self.completions else None,
                'hard_turn_timeout_seconds': self.timeout,
                'relay_v2': self.v2.snapshot() if self.v2 else {'github_enabled':False,'browser_enabled':False}}

    def _interrupt(self, turn_id, human_review=True):
        self.human_review_required = human_review
        self.stop_reason = 'approval_required' if human_review else 'turn_lost'
        try:
            self.rpc.call('turn/interrupt', {'threadId': self.thread_id, 'turnId': turn_id}, timeout=10)
        finally:
            # Fail closed: even if interruption failed, no subsequent turn can start
            # on this process. No approval response or permission grant is sent.
            self.rpc.close()
            self.error = 'Turn blocked; restart bridge after human review' if human_review else 'Turn lost; no automatic replay'
            self._diagnose(self.stop_reason, message=self.error)

    def _approval_state(self, status):
        if self.active_request_id and self.completions:
            self.completions.set_state(self.active_request_id,
                'awaiting_approval' if status == 'AWAITING APPROVAL' else 'running')

    def allowed_routes(self):
        return list(ROUTES)

    def submit(self, request, source="http"):
        """HTTP submission waits for preflight/start only; worker owns the turn."""
        with self.submit_lock:
            saved=self.completions.ledger.get(request['request_id'])
            if saved and (saved['source']=='github' and source!='github' or
              saved['prompt_sha256'] and saved['prompt_sha256']!=digest(request['message']) or
              saved['route_id']!=request.get('route_id',DEFAULT_ROUTE)):
                return 409, {'ok':False,'status':'request_id_conflict','error':'No replay; request identity conflict'}
            if saved and saved['terminal_at'] and self.completions.known(request['request_id']) is None:
                return 409, {'ok':False,'status':'request_id_already_seen','error':'No replay; retained metadata only'}
            known = self.completions.known(request['request_id'])
            if known is not None:
                return known
            if dispatch_paused(request):
                return 409, {'ok':False,'status':'intentional_pause','error':'Brain Age paused after AW16; reliability gate requires explicit release'}
            if not self.accepting_work:
                return 503, {'ok':False,'status':'stopping','request_id':request['request_id'],'thread_key':'main'}
            if self.human_review_required or (self.completions.active() and not self.turn_lock.locked()):
                return 409, {'ok':False,'status':'reconciliation_required','error':'Persisted active turn requires human review; no replay'}
            if self.turn_lock.locked():
                return 409, {'ok':False,'status':'busy','request_id':request['request_id'],'thread_key':'main'}
            started = concurrent.futures.Future()
            def signal(payload):
                started.set_result((202,payload))
            def observe():
                try:
                    result = self.relay(request, on_started=signal)
                except Exception:
                    # Reserved identity remains protected if an unexpected observer
                    # failure prevents terminal recording; never replay on reconnect.
                    result = (503, {'ok':False,'status':'blocked','error':'observer_failed',
                        'request_id':request['request_id'],'thread_key':'main','response':'','response_sha256':digest('')})
                    try:
                        known=self.completions.known(request['request_id'])
                        turn_id=known[1].get('codex_turn_id') if known else None
                        if turn_id and self.rpc and not self.rpc.closed:
                            self._interrupt(turn_id,human_review=False)
                    except Exception:
                        if self.rpc:self.rpc.close()
                    try:
                        self.completions.finish(request,*result)
                    except Exception:
                        pass  # Durable reservation remains; restart reports interruption, never replay.
                    self._diagnose('observer_failed', message='Async observer failed; request cannot be replayed')
                if not started.done():
                    started.set_result(result)  # Preflight/start failure remains synchronous.
            self.worker = threading.Thread(target=observe, name='Muse-Codex-turn', daemon=True)
            self.worker.start()
            return started.result()

    def relay(self, request, on_started=None):
        if not self.accepting_work:
            return 503, {'ok': False, 'status': 'stopping', 'request_id': request['request_id'], 'thread_key': 'main'}
        if not self.turn_lock.acquire(blocking=False):
            return 409, {'ok': False, 'status': 'busy', 'request_id': request['request_id'], 'thread_key': 'main'}
        try:
            if not self.accepting_work:
                return 503, {'ok': False, 'status': 'stopping', 'request_id': request['request_id'], 'thread_key': 'main'}
            try:
                reserved = self.completions.reserve(request)
            except Exception:
                return 503, {'ok':False, 'status':'completion_storage_unavailable',
                             'request_id':request['request_id'], 'thread_key':'main'}
            if not reserved:
                return 409, {'ok':False, 'status':'request_id_already_seen', 'request_id':request['request_id'],
                             'thread_key':'main', 'error':'No replay; retrieve the retained result using GET /results/<request_id>'}
            self.active_request_id = request['request_id']
            self.operation = 'relay_preflight'
            self.approvals.reset()
            self.monitor.begin(request)
            status, payload = self._relay_locked(request, on_started)
            self.approvals.finish()
            try:
                self.completions.finish(request, status, payload)
            except Exception:
                # Return the exact accepted-turn result even if durable recording fails.
                # Pending reservation prevents a retry from starting another turn.
                payload['completion_recorded'] = False
                self._diagnose('completion_storage_failed', message='Completion could not be durably recorded; no replay')
            self.monitor.finish(status, payload)
            return status, payload
        finally:
            self.approvals.finish()
            self.active_request_id = None
            self.turn_lock.release()

    def _relay_locked(self, request, on_started=None):
        turn_id = None
        approval_failure = None
        envelope = {'request_id': request['request_id'], 'thread_key': 'main'}
        try:
            self._select_route(request.get('route_id', DEFAULT_ROUTE))
            self.monitor.context(self.requested_model, self.requested_effort, self.thread_id)
            self.ensure_thread()
            envelope.update(route_id=self.route_id, model=self.active_model, reasoning_effort=self.active_effort,
                            thread_alias=self.thread_alias())
            envelope['codex_thread_id'] = self.thread_id
            self.monitor.context(self.active_model, self.active_effort, self.thread_id)
            # Discard only pre-turn notifications. Any pending server request is a block.
            while True:
                try:
                    old = self.rpc.events.get_nowait()
                except queue.Empty:
                    break
                if 'id' in old and 'method' in old:
                    self.monitor.observe(old)
                    self.human_review_required = True
                    self.stop_reason = 'approval_required'
                    self.rpc.close()
                    self._diagnose('approval_required', message='Pending server interaction requires human review')
                    return 409, {**envelope, 'ok': False, 'status': 'approval_required',
                                 'approval': {'method': old['method']}, 'response': '',
                                 'response_sha256': digest('')}
            self.operation = 'relay_turn'
            result = self.rpc.call('turn/start', {'threadId': self.thread_id, 'cwd': WORKSPACE,
                                   'model': self.requested_model, 'effort': self.requested_effort,
                                   'approvalsReviewer': APPROVAL_REVIEWER, 'approvalPolicy': APPROVAL_POLICY,
                                   'sandboxPolicy': workspace_sandbox(), 'runtimeWorkspaceRoots': [WORKSPACE],
                                   'input': [{'type': 'text', 'text': request['message']}]})
            turn_id = result['turn']['id']
            envelope['codex_turn_id'] = turn_id
            self.completions.bind_turn(request['request_id'], self.thread_id, turn_id)
            self.monitor.turn_started(turn_id)
            if on_started:
                on_started({**envelope,'ok':True,'status':'accepted','codex_turn_id':turn_id})
            end = time.monotonic() + self.timeout if self.timeout is not None else None
            final_items, items = {}, {}
            approval_failure = None
            approval_wait = 0.0
            tick = time.monotonic()
            while True:
                now = time.monotonic()
                if self.approvals.pending():
                    waited = now - tick
                    if end is not None:
                        end += waited  # Approval wait is separate from any explicitly configured hard limit.
                    approval_wait += waited
                tick = now
                outcomes = self.approvals.dispatch(self.rpc)
                denied = [outcome for outcome in outcomes if outcome['state'] in ('timed_out', 'denied')]
                if denied:
                    approval_failure = 'approval_timeout' if any(o['state'] == 'timed_out' for o in denied) else 'approval_denied'
                    self.approvals.finish()
                    # Cancel this turn without closing the healthy App Server. No replay.
                    if any(outcome['cancel_turn'] for outcome in denied):
                        try:
                            self.rpc.call('turn/interrupt', {'threadId': self.thread_id, 'turnId': turn_id}, timeout=10)
                        except BridgeError:
                            pass  # The denial may already have ended the turn; drain completion below.
                    end = time.monotonic() + 10
                if self.rpc.closed or self.rpc.proc.poll() is not None:
                    raise BridgeError('App Server disconnected during turn')
                remaining = end - time.monotonic() if end is not None else 0.1
                if remaining <= 0:
                    raise BridgeError('Approval cancellation completion timeout' if approval_failure else 'Configured hard turn timeout')
                try:
                    event = self.rpc.events.get(timeout=min(remaining, 0.1))
                except queue.Empty:
                    continue
                method = event.get('method', '')
                params = event.get('params', {})
                if ((params.get('threadId') == self.thread_id and
                     params.get('turnId', params.get('turn', {}).get('id', turn_id)) == turn_id)
                        or ('id' in event and 'method' in event) or method in ('error', 'warning')):
                    self.monitor.observe(event)
                    self.completions.ledger.event(request['request_id'],event)
                if method == '__disconnected':
                    raise BridgeError('App Server disconnected during turn')
                if 'id' in event and 'method' in event:
                    if approval_failure:
                        denied_response = response_policy(method, params)[3]
                        self.rpc.send({'id': event['id'], **({'result': denied_response} if denied_response is not None else
                            {'error': {'code': -32601, 'message': 'Relay turn is cancelled'}})})
                        continue
                    try:
                        self.approvals.register(event, request['request_id'], self.thread_id, turn_id,
                            items.get(params.get('itemId')), max(0, 1800 - approval_wait))
                    except ApprovalError as exc:
                        # Unscoped/legacy interaction cannot acquire authority for this turn.
                        self.rpc.send({'id': event['id'], 'error': {'code': -32602,
                            'message': 'Server interaction is not bound to the active relay turn'}})
                        self.rpc.call('turn/interrupt', {'threadId': self.thread_id, 'turnId': turn_id}, timeout=10)
                        approval_failure = exc.code
                        self._diagnose('approval_rejected', error_class=exc.code, message='Request registration refused', source='approval_registration')
                        end = min(end, time.monotonic() + 10) if end is not None else time.monotonic() + 10
                    continue
                if method == 'serverRequest/resolved' and params.get('threadId') == self.thread_id:
                    self.approvals.resolved(params.get('requestId'))
                if params.get('threadId') == self.thread_id and params.get('turnId') == turn_id:
                    if method in ('item/started', 'item/completed'):
                        item = params.get('item', {})
                        if item.get('type') in ('commandExecution', 'fileChange', 'mcpToolCall', 'dynamicToolCall'):
                            items[item.get('id')] = item
                            self.approvals.update_item(item.get('id'), item)
                    elif method == 'item/fileChange/patchUpdated':
                        item_id = params.get('itemId')
                        items.setdefault(item_id, {}).update(changes=params.get('changes'))
                        self.approvals.update_item(item_id, items[item_id])
                if params.get('threadId') != self.thread_id:
                    continue
                if method == 'item/completed' and params.get('turnId') == turn_id:
                    item = params.get('item', {})
                    if item.get('type') == 'agentMessage' and item.get('phase') == 'final_answer':
                        final_items[item['id']] = item['text']
                if method == 'turn/completed' and params.get('turn', {}).get('id') == turn_id:
                    turn = params['turn']
                    # Prefer full completed items over deltas; never trim output.
                    for item in turn.get('items', []):
                        if item.get('type') == 'agentMessage' and item.get('phase') == 'final_answer':
                            final_items[item['id']] = item['text']
                    response = ''.join(final_items.values())
                    status = turn['status']
                    good = status == 'completed' and approval_failure is None
                    if approval_failure:
                        return (504 if approval_failure == 'approval_timeout' else 409), {**envelope,
                            'ok': False, 'status': approval_failure, 'error': approval_failure,
                            'response': '', 'response_sha256': digest('')}
                    if not good:
                        error_text = json.dumps(turn.get('error') or {}).lower()
                        if any(marker in error_text for marker in ('modelnotfound', 'model_not_found',
                                'model is not supported', 'model is not available', 'model_not_available')):
                            rejection = 'Backend rejected the intended model; no fallback. Human review required.'
                            self.backend_rejections[self.requested_model] = rejection
                            self.model_status = 'backend_unavailable'
                            self.model_error = rejection
                    if good and not final_items:
                        raise BridgeError('Completed turn missing final answer')
                    return (200 if good else 502), {**envelope, 'ok': good, 'status': status,
                        'response': response, 'response_sha256': digest(response),
                        **({'error': turn.get('error')} if not good else {})}
        except ModelPolicyError as exc:
            return (400 if exc.status == 'invalid_route' else 503), {**envelope,
                         'route_id': request.get('route_id', DEFAULT_ROUTE),
                         'ok': False, 'status': exc.status, 'error': str(exc),
                         'requested_model': self.requested_model,
                         'requested_reasoning_effort': self.requested_effort,
                         'response': '', 'response_sha256': digest('')}
        except Exception as exc:
            if not turn_id and self.operation == 'relay_turn' and self.rpc and not self.rpc.closed:
                # Start may have reached the server even when its response was lost.
                # Fail closed on this genuine protocol uncertainty, never replay.
                self.rpc.close()
            if turn_id and self.rpc and not self.rpc.closed:
                try:
                    self._interrupt(turn_id, human_review=False)
                except Exception:
                    self.rpc.close()
            evidence = 'APP_SERVER_LOST' if self.rpc and self.rpc.proc.poll() is not None else 'TRANSPORT_LOST' if turn_id and self.rpc and self.rpc.closed else None
            self._diagnose('relay_failed', type(exc).__name__,
                'Relay/RPC failure; full task/backend payload omitted' if turn_id or self.operation == 'relay_turn' else safe_error(exc))
            return (504 if approval_failure == 'approval_timeout' else 409 if approval_failure else 503), {**envelope, 'ok': False, 'status': approval_failure or 'blocked', 'error': approval_failure or str(exc),
                         **({'relay_evidence':evidence} if evidence else {}),
                         'response': '', 'response_sha256': digest('')}

    def close(self):
        self.accepting_work = False
        if self.v2:self.v2.close()
        self.approvals.finish()
        if self.rpc:
            self.rpc.close()
        if self.worker and self.worker is not threading.current_thread():
            self.worker.join(timeout=15)
        self.monitor.close()
        if self.completions is not None:
            self.completions.close()
            self.completions = None


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False
    def __init__(self, port, bridge, token, browser_token=None, inbox=None):
        self.bridge = bridge
        self.token = token
        if browser_token and hmac.compare_digest(token,browser_token):raise ValueError('separate_browser_token_required')
        self.browser_token = browser_token
        self.inbox = inbox
        super().__init__(('127.0.0.1', port), Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    server_version = 'MuseBridge/1.0'
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass  # No tokens, requests, or model output in logs.

    def send_json(self, status, payload):
        self.close_connection = True
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Connection', 'close')
        try:
            self.end_headers()
            self.wfile.write(data)
        except (OSError, TimeoutError):
            pass

    def authenticated(self):
        auth = self.headers.get_all('Authorization', [])
        return len(auth) == 1 and hmac.compare_digest(auth[0].encode('utf-8'),
                    ('Bearer ' + self.server.token).encode('utf-8'))

    def browser_authenticated(self):
        token=self.server.browser_token
        auth=self.headers.get_all('Authorization',[])
        return bool(token) and len(auth)==1 and hmac.compare_digest(auth[0].encode('utf-8'),('Bearer '+token).encode('utf-8'))

    def do_GET(self):
        if self.path == '/capabilities':
            if not self.authenticated():
                return self.send_json(401, {'ok':False,'error':'unauthorized'})
            return self.send_json(200, capabilities(self.server.bridge, self.server, PROCESS_STARTED))
        if self.path == '/health':
            return self.send_json(200, dict(self.server.bridge.health(), capabilities=capabilities(self.server.bridge, self.server, PROCESS_STARTED)))
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            return self.send_json(400, {'ok':False,'error':'malformed_request'})
        if parsed.path.startswith('/local/inbox/'):
            return self.send_json(404, {'ok':False,'error':'not_found'})
        if parsed.path.startswith('/chatgpt-inbox/'):
            if not self.authenticated():return self.send_json(401,{'ok':False,'error':'unauthorized'})
            if parsed.query:return self.send_json(400,{'ok':False,'error':'malformed_request'})
            if self.server.inbox is None:return self.send_json(503,{'ok':False,'error':'inbox_disabled'})
            try:return self.send_json(*self.server.inbox.get_inbox(parsed.path[len('/chatgpt-inbox/'):], True))
            except OSError:return self.send_json(503,{'ok':False,'error':'inbox_unavailable'})
        if parsed.path == '/browser/events':
            if not self.browser_authenticated():return self.send_json(401,{'ok':False,'error':'unauthorized'})
            ledger=self.server.bridge.completions.ledger
            if not ledger.browser_enabled:return self.send_json(503,{'ok':False,'error':'browser_delivery_disabled'})
            try:
                query=parse_qs(parsed.query,keep_blank_values=True,strict_parsing=True)
                if set(query)!={'after'} or len(query['after'])!=1 or not query['after'][0].isascii() or not query['after'][0].isdecimal() or len(query['after'][0])>19:raise ValueError()
                return self.send_json(200,ledger.events(int(query['after'][0])))
            except ValueError:return self.send_json(400,{'ok':False,'error':'malformed_request'})
        if parsed.path.startswith('/requests/') or parsed.path == '/routes/status':
            if not self.authenticated():return self.send_json(401,{'ok':False,'error':'unauthorized'})
            if parsed.query:return self.send_json(400,{'ok':False,'error':'malformed_request'})
            ledger=self.server.bridge.completions.ledger
            if parsed.path=='/requests/active':return self.send_json(200,{'ok':True,'requests':ledger.active()})
            if parsed.path=='/routes/status':return self.send_json(200,{'ok':True,**self.server.bridge.routing_snapshot()})
            try:ident=unquote(parsed.path[len('/requests/'):],encoding='utf-8',errors='strict')
            except UnicodeError:return self.send_json(400,{'ok':False,'error':'malformed_request'})
            if not 1<=len(ident)<=128:return self.send_json(400,{'ok':False,'error':'malformed_request'})
            row=ledger.get(ident)
            return self.send_json(200 if row else 404,{'ok':bool(row),'request':row,'reconciled_result':ledger.recovered(ident) if row else None})
        if parsed.path == '/events/completions'  or parsed.path.startswith('/results/'):
            if not self.authenticated():
                return self.send_json(401, {'ok':False,'error':'unauthorized'})
            try:
                if parsed.path == '/events/completions':
                    query=parse_qs(parsed.query,keep_blank_values=True,strict_parsing=True)
                    if set(query)!={'after'} or len(query['after'])!=1:
                        raise ValueError('bad_cursor')
                    raw=query['after'][0]
                    if not raw.isascii() or not raw.isdecimal() or len(raw)>19 or int(raw)>9223372036854775807:
                        raise ValueError('bad_cursor')
                    return self.send_json(200, self.server.bridge.completions.events(int(raw)))
                ident=unquote(parsed.path[len('/results/'):],encoding='utf-8',errors='strict')
                if parsed.query or not 1<=len(ident)<=128:
                    raise ValueError('invalid_request_id')
                status,result=self.server.bridge.completions.result(ident)
                return self.send_json(status,result)
            except (ValueError,UnicodeError):
                return self.send_json(400,{'ok':False,'error':'malformed_request'})
        return self.send_json(404, {'ok': False, 'error': 'not_found'})

    def reject_post(self, status, category, stage, public_error='malformed_request'):
        # Only fixed local categories enter diagnostics: never body, headers or exception text.
        self.server.bridge.diagnostics.record({'reason': 'post_rejected', 'source': 'http_post',
            'endpoint': self.path, 'category': category, 'stage': stage, 'http_status': status})
        return self.send_json(status, {'ok': False, 'error': public_error})

    def do_POST(self):
        if self.path == '/chatgpt-inbox':
            if not self.authenticated():return self.send_json(401,{'ok':False,'error':'unauthorized'})
            if self.server.inbox is None:return self.send_json(503,{'ok':False,'error':'inbox_disabled'})
            try:return self.send_json(*self.server.inbox.post_inbox(read_inbox_body(self), True))
            except (ValueError,UnicodeError,RecursionError):return self.send_json(400,{'ok':False,'error':'malformed_request'})
            except (TimeoutError,socket.timeout):return self.send_json(408,{'ok':False,'error':'request_timeout'})
            except OSError:return self.send_json(503,{'ok':False,'error':'inbox_unavailable'})
        if self.path not in ('/echo', '/relay', '/browser/ack'):
            return self.send_json(404, {'ok': False, 'error': 'not_found'})
        auth = self.headers.get_all('Authorization', [])
        if not (self.browser_authenticated() if self.path == '/browser/ack' else self.authenticated()):
            return self.reject_post(401, 'unauthorized', 'authentication', 'unauthorized')
        stage = 'framing'
        try:
            if self.headers.get('Transfer-Encoding') is not None:
                raise ValueError('transfer_encoding_unsupported')
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                raise ValueError('bad_content_length')
            length = int(lengths[0])
            if length > MAX_BODY:
                return self.reject_post(413, 'body_too_large', stage, 'body_too_large')
            if self.headers.get_content_type() != 'application/json':
                return self.reject_post(415, 'unsupported_content_type', stage, 'expected_application_json')
            if self.headers.get('Content-Encoding', 'identity').lower().strip() != 'identity':
                return self.reject_post(415, 'unsupported_content_encoding', stage, 'unsupported_content_encoding')
            stage = 'body'
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError('incomplete_body')
            def unique_pairs(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError('duplicate_json_key')
                    result[key] = value
                return result
            stage = 'json'
            request = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
                                 parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid_json_constant')))
            if self.path == '/browser/ack':
                ledger=self.server.bridge.completions.ledger
                if not ledger.browser_enabled:return self.send_json(503,{'ok':False,'error':'browser_delivery_disabled'})
                return self.send_json(200,ledger.ack(request))
            required = {'message'} if self.path == '/echo' else {'request_id', 'thread_key', 'message'}
            allowed = required if self.path == '/echo' else required | {'route_id'}
            stage = 'schema'
            if not isinstance(request, dict):
                raise ValueError('invalid_body_type')
            if not required <= set(request):
                raise ValueError('missing_required_fields')
            if not set(request) <= allowed:
                raise ValueError('unexpected_fields')
            if not isinstance(request['message'], str):
                raise ValueError('message_must_be_string')
            request['message'].encode('utf-8', errors='strict')
            if self.path == '/echo':
                return self.send_json(200, {'ok': True, 'message': request['message'],
                         'message_sha256': digest(request['message']), 'codex_contacted': False})
            stage = 'route'
            if 'route_id' in request and (not isinstance(request['route_id'], str) or request['route_id'] not in ROUTES):
                raise ValueError('unsupported_route_id')
            stage = 'schema'
            if request['thread_key'] != 'main':
                raise ValueError('unsupported_thread_key')
            if not isinstance(request['request_id'], str) or not 1 <= len(request['request_id']) <= 128:
                raise ValueError('invalid_request_id')
            stage = 'submission'
            status, response = self.server.bridge.submit(request)
            self.send_json(status, response)
        except (ValueError, UnicodeError, RecursionError) as exc:
            codes = {'transfer_encoding_unsupported', 'bad_content_length', 'incomplete_body',
                'duplicate_json_key', 'invalid_json_constant', 'invalid_body_type',
                'missing_required_fields', 'unexpected_fields', 'message_must_be_string',
                'unsupported_route_id', 'unsupported_thread_key', 'invalid_request_id'}
            if isinstance(exc, json.JSONDecodeError): category = 'invalid_json'
            elif isinstance(exc, UnicodeError): category = 'invalid_utf8'
            elif isinstance(exc, RecursionError): category = 'json_nesting_limit'
            else: category = str(exc) if str(exc) in codes else 'invalid_request'
            public = 'unsupported_route_id' if category == 'unsupported_route_id' else 'malformed_request'
            self.reject_post(400, category, stage, public)
        except (TimeoutError, socket.timeout):
            self.reject_post(408, 'request_timeout', stage, 'request_timeout')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--echo-only', action='store_true')
    parser.add_argument('--managed', action='store_true')
    parser.add_argument('--monitor-port', type=int, default=8767)
    parser.add_argument('--hard-turn-timeout', type=int, default=None, help='Optional hard limit in seconds, minimum 3600; default unlimited')
    args = parser.parse_args()
    if args.hard_turn_timeout is not None and args.hard_turn_timeout < 3600:
        parser.error("--hard-turn-timeout must be at least 3600 seconds")
    if str(BASE.parent) != WORKSPACE:
        raise SystemExit('Installation moved: fixed workspace mismatch')
    runtime = BASE / '.runtime'
    runtime.mkdir(exist_ok=True)
    # Windows-held lock prevents two bridge instances sharing the persistent thread.
    lock_file = (runtime / 'instance.lock').open('a+b')
    lock_file.seek(0)
    if os.name == 'nt':
        import msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit('Another bridge instance owns this workspace')
    token = os.environ.pop('MUSE_BRIDGE_TOKEN', None) if args.managed else None
    if args.managed and (not token or len(token) < 64):
        raise SystemExit('Managed launch requires a high-entropy local environment token')
    token = token or secrets.token_urlsafe(48)  # Memory only; never a token file or argv.
    bridge = Bridge(emit_diagnostics=args.managed, timeout=args.hard_turn_timeout)
    browser_token=None
    try:
        config=load_config(runtime/'relay-v2.json')
        browser_error=None
        if config['browser']['enabled']:
            try:browser_token=credential_read(config['browser']['credential_target'])
            except Exception:
                browser_error='browser_credential_missing_or_invalid'
                config['browser']['enabled']=False
        bridge.v2=V2Service(bridge,config)
        bridge.v2.browser_error=browser_error
    except Exception:
        bridge._diagnose('relay_v2_configuration_blocked',message='Relay V2 disabled; check local configuration and browser credential')
    server = Server(args.port, bridge, token, browser_token)
    inbox_server = None
    # Inbox is additive and locally opt-in. Failure never enables the remote local routes.
    inbox_config = runtime / 'inbox-v1.json'
    if inbox_config.exists():
        try:
            cfg=json.loads(inbox_config.read_text(encoding='utf-8-sig'))
            if set(cfg)!={'enabled','local_port'} or type(cfg['enabled']) is not bool or cfg['local_port']!=18741:
                raise ValueError('invalid inbox configuration')
            if cfg['enabled']:
                inbox=InboxApi(InboxQueue(runtime/'inbox_queue.json'))
                inbox_server=LocalInboxServer(cfg['local_port'],inbox)
                threading.Thread(target=inbox_server.serve_forever,daemon=True).start()
                server.inbox=inbox
                bridge.inbox_worker_health=WorkerHealth(runtime/'inbox-worker-health.json')
                def inbox_reaper():
                    while bridge.accepting_work:
                        try:
                            inbox.queue.reap_stale()
                            bridge.inbox_worker_health.record(state='HEALTHY',continuity_dependency='NONE')
                        except (OSError,ValueError):
                            try:bridge.inbox_worker_health.record(error='inbox_persistence_requires_review',state='DEGRADED')
                            except OSError:print('Inbox health persistence failed; worker degraded',flush=True)
                        time.sleep(30)
                threading.Thread(target=inbox_reaper,daemon=True).start()
        except (OSError,ValueError):
            print('Inbox V1 disabled: local configuration, queue, or listener requires review',flush=True)
    monitor_server = None
    try:
        monitor_server = MonitorServer(args.monitor_port, bridge.monitor)
        threading.Thread(target=monitor_server.serve_forever, daemon=True).start()
        if args.managed:
            import sys
            def local_control():
                for line in sys.stdin:
                    try:
                        command = json.loads(line)
                        if command == {'op': 'shutdown', 'if_idle': True}:
                            if not bridge.stop_if_idle():
                                print('CONTROL {"shutdown":"busy"}', flush=True)
                                continue
                            print('CONTROL {"shutdown":"accepted"}', flush=True)
                            break
                        if command == {'op': 'shutdown'}:
                            break
                    except (ValueError, TypeError):
                        continue
                bridge.accepting_work = False
                server.shutdown()
            threading.Thread(target=local_control, daemon=True).start()
        if not args.echo_only:
            bridge.version = subprocess.check_output([INSTALL['codex_executable'], '--version'],
                               text=True, encoding='utf-8', timeout=10,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).strip()
            bridge.connect()
        identity = {'pid': os.getpid(), 'started_at': PROCESS_STARTED, 'script': str(Path(__file__).resolve()),
                    'port': args.port, 'workspace': WORKSPACE, 'source_sha256': SOURCE_SHA256}
        atomic_json(runtime / 'process.json', identity)
        print('Local URL: http://127.0.0.1:' + str(args.port), flush=True)
        if not args.managed:
            print('Bearer token: ' + token, flush=True)
        print('Hard-locked workspace: ' + WORKSPACE, flush=True)
        print('Codex version: ' + bridge.version, flush=True)
        print('Intended model/effort: ' + str(bridge.requested_model) + '/' + str(bridge.requested_effort), flush=True)
        print('Model routing: ' + bridge.model_status, flush=True)
        if bridge.model_error:
            print('Model routing error: ' + bridge.model_error, flush=True)
        print('Codex connectivity: ' + ('connected' if bridge.health()['codex_available'] else 'unavailable'), flush=True)
        if bridge.error:
            print('Connectivity error: ' + bridge.error, flush=True)
        def catalog_refresh_loop():
            while bridge.accepting_work:
                for _ in range(60):
                    if not bridge.accepting_work:
                        return
                    time.sleep(1)
                bridge.refresh_catalog()
        threading.Thread(target=catalog_refresh_loop, daemon=True).start()
        if bridge.v2:bridge.v2.start()
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.accepting_work = False
        server.server_close()
        if inbox_server:
            inbox_server.shutdown()
            inbox_server.server_close()
        bridge.close()
        if monitor_server:
            monitor_server.shutdown()
            monitor_server.server_close()
        record = runtime / 'process.json'
        if record.exists() and json.loads(record.read_text())['pid'] == os.getpid():
            record.unlink()
        lock_file.close()


if __name__ == '__main__':
    main()
