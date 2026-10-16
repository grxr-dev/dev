"""Local V2 configuration, bounded read-only recovery, and adapter lifecycle."""
import json
import hashlib
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit
from relay_state import compact,sha
from github_bus import GitHubBus
from reliability import WorkerHealth

V2_SOURCE_SHA256=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in ('relay_v2.py','relay_state.py','github_bus.py','completions.py'))).hexdigest()

DEFAULT_CONFIG={'version':1,'github':{'enabled':False,'repo':'grxr-dev/codex-relay',
    'expected_author':'grxr-dev','poll_seconds':10,'credential_source':'gh'},
    'browser':{'enabled':False,'conversation_url':'','credential_target':'MuseCodexRelay/browser/v1'}}

def valid_conversation(url):
    return isinstance(url,str) and bool(re.fullmatch(r'https://chatgpt\.com/(?:g/[A-Za-z0-9_-]+/)?c/[A-Za-z0-9-]+',url))

def load_config(path):
    c=json.loads(path.read_text(encoding='utf-8')) if path.exists() else json.loads(compact(DEFAULT_CONFIG))
    if set(c)!={'version','github','browser'} or c['version']!=1:raise ValueError('invalid_v2_config')
    g=c['github'];b=c['browser']
    if set(g)!=set(DEFAULT_CONFIG['github']) or set(b)!=set(DEFAULT_CONFIG['browser']):raise ValueError('invalid_v2_config')
    if type(g['enabled']) is not bool or type(b['enabled']) is not bool:raise ValueError('invalid_enable_flag')
    if g['repo']!='grxr-dev/codex-relay' or g['expected_author']!='grxr-dev' or g['credential_source']!='gh':raise ValueError('dedicated_repo_required')
    if type(g['poll_seconds']) is not int or not 10<=g['poll_seconds']<=300:raise ValueError('invalid_poll_interval')
    if b['credential_target']!='MuseCodexRelay/browser/v1':raise ValueError('invalid_credential_target')
    if b['enabled'] and not valid_conversation(b['conversation_url']):raise ValueError('exact_normal_chat_required')
    return c

def credential_read(target):
    # Windows generic credential; returned only to the local HTTP server.
    import ctypes
    from ctypes import wintypes
    class Credential(ctypes.Structure):
        _fields_=[('Flags',wintypes.DWORD),('Type',wintypes.DWORD),('TargetName',wintypes.LPWSTR),
          ('Comment',wintypes.LPWSTR),('LastWritten',wintypes.FILETIME),('CredentialBlobSize',wintypes.DWORD),
          ('CredentialBlob',ctypes.POINTER(ctypes.c_byte)),('Persist',wintypes.DWORD),('AttributeCount',wintypes.DWORD),
          ('Attributes',ctypes.c_void_p),('TargetAlias',wintypes.LPWSTR),('UserName',wintypes.LPWSTR)]
    ptr=ctypes.POINTER(Credential)();api=ctypes.WinDLL('advapi32',use_last_error=True)
    api.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(Credential))]
    api.CredReadW.restype=wintypes.BOOL;api.CredFree.argtypes=[ctypes.c_void_p]
    if not api.CredReadW(target,1,0,ctypes.byref(ptr)):raise ValueError('browser_credential_missing')
    try:
        token=ctypes.string_at(ptr.contents.CredentialBlob,ptr.contents.CredentialBlobSize).decode('utf-8')
        if not re.fullmatch(r'[A-Za-z0-9_-]{64,256}',token):raise ValueError('browser_credential_invalid')
        return token
    finally:api.CredFree(ptr)

def recover(bridge):
    store=bridge.completions;ledger=store.ledger
    with store.lock:pending=[dict(r) for r in store.db.execute('SELECT * FROM pending')]
    for row in pending:
        req={'request_id':row['request_id'],'thread_key':row['thread_key'],'route_id':row['route_id']}
        outcome=None;fact='persisted_turn_not_found'
        if row['thread_id'] and row['turn_id']:
            try:
                cursor=None
                for _ in range(3):
                    page=bridge.rpc.call('thread/turns/list',{'threadId':row['thread_id'],'itemsView':'full',
                      'limit':16,'sortDirection':'desc','cursor':cursor},timeout=10)
                    turn=next((t for t in page['data'] if t['id']==row['turn_id']),None)
                    if turn:
                        fact='persisted_'+turn['status']
                        if turn['status']=='inProgress':
                            bridge.human_review_required=True;bridge.stop_reason='reconciliation_active_turn'
                            ledger.state(row['request_id'],'running');break
                        if turn['status'] in ('completed','failed','interrupted'):
                            finals=[i['text'] for i in turn.get('items',[]) if i.get('type')=='agentMessage' and i.get('phase')=='final_answer']
                            if turn['status']=='completed' and not finals:
                                fact='completed_result_unavailable';break
                            text=''.join(finals)
                            outcome={'ok':turn['status']=='completed','status':turn['status'],
                              'response':text,'response_sha256':sha(text),'codex_thread_id':row['thread_id'],
                              'codex_turn_id':row['turn_id'],**({'error':turn.get('error')} if turn['status']!='completed' else {})}
                        break
                    cursor=page.get('nextCursor')
                    if not cursor:break
            except Exception:fact='app_server_readback_unavailable'
        with store.lock,store.db:
            store.db.execute('UPDATE requests SET reconciliation=? WHERE request_id=?',(fact,row['request_id']))
        if fact=='persisted_inProgress':continue # Keep identity and globally block inference, never replay.
        if outcome is None:
            outcome={'ok':False,'status':'interrupted','response':'','response_sha256':sha(''),
              'error':fact+'; no automatic replay; use a new request_id'}
        store.finish(req,200 if outcome['ok'] else 503,dict(outcome,**req))
    # Reconcile prior stream/process loss too. Preserve the originally delivered
    # failure as history; expose the exact readback separately, never replay it.
    with store.lock:
        lost=store.db.execute("SELECT * FROM requests WHERE state IN ('APP_SERVER_LOST','TRANSPORT_LOST') AND reconciliation IS NULL ORDER BY submitted_at DESC LIMIT 8").fetchall()
    for row in lost:
        fact='readback_unavailable';payload=None
        if row['codex_thread_id'] and row['codex_turn_id']:
            try:
                page=bridge.rpc.call('thread/turns/list',{'threadId':row['codex_thread_id'],'itemsView':'full','limit':16,'sortDirection':'desc'},timeout=10)
                turn=next((t for t in page['data'] if t['id']==row['codex_turn_id']),None)
                if turn:
                    fact='persisted_'+turn['status']
                    if turn['status']=='inProgress':
                        bridge.human_review_required=True;bridge.stop_reason='reconciliation_active_turn'
                    elif turn['status'] in ('completed','failed','interrupted'):
                        finals=[i['text'] for i in turn.get('items',[]) if i.get('type')=='agentMessage' and i.get('phase')=='final_answer']
                        if turn['status']!='completed' or finals:
                            text=''.join(finals)
                            payload={'request_id':row['request_id'],'status':turn['status'],'response':text,'response_sha256':sha(text),'error':turn.get('error'),'source':'persisted_app_server_readback'}
                else:fact='persisted_turn_not_in_bounded_window'
            except Exception:pass
        with store.lock,store.db:
            store.db.execute('UPDATE requests SET reconciliation=? WHERE request_id=?',(fact,row['request_id']))
            if payload is not None:
                encoded=compact(payload).encode('utf-8')
                if len(encoded)<=store.max_result_bytes:
                    from completions import timestamp
                    store.db.execute('INSERT OR REPLACE INTO reconciled_results VALUES(?,?,?,?)',(row['request_id'],encoded,sha(compact(payload)),timestamp()))
    # Crash between dispatch claim and durable turn reservation is ambiguous.
    with store.lock:
        ambiguous=store.db.execute("SELECT r.*,i.request_json FROM requests r JOIN github_inbox i USING(request_id) WHERE r.state='DISPATCHING'").fetchall()
    for row in ambiguous:
        req=json.loads(row['request_json'])
        store.finish(req,503,{'ok':False,'status':'interrupted','error':'ambiguous_dispatch_after_restart; no replay',
          'response':'','response_sha256':sha('')})

class Service:
    def __init__(self,bridge,config):
        self.bridge=bridge;self.config=config;self.stop=threading.Event();self.thread=None
        self.bus=GitHubBus(bridge,config['github']) if config['github']['enabled'] else None
        if self.bus:
            self.bus.stop=self.stop
            if hasattr(self.bus.client,'stop'):self.bus.client.stop=self.stop
        self.status='disabled';self.error=None;self.browser_error=None
        self.worker_health=WorkerHealth(bridge.completions.path.with_name('github-worker-health.json'))
        ledger=bridge.completions.ledger
        ledger.browser_enabled=config['browser']['enabled'];ledger.conversation=config['browser']['conversation_url']
    def start(self):
        if not self.bus:return
        def run():
            while not self.stop.is_set():
                delay=self.config['github']['poll_seconds']
                try:
                    self.bus.tick();self.status=self.bus.status;self.error=None
                    with self.bus.ledger.lock:
                        backlog=self.bus.ledger.db.execute("SELECT count(*) FROM github_outbox WHERE state!='CLOSED'").fetchone()[0]
                    self.worker_health.record(state='HEALTHY',github_delivery=self.bridge.completions.summary(),
                        backlog=backlog,local_high_water=self.bridge.completions.summary()['latest_sequence'],
                        next_retry_seconds=delay,inbox_dependency='NOT_REQUIRED',brainage_continuity='INTENTIONAL_PAUSE_AFTER_AW16')
                except Exception as exc:
                    self.status='blocked';self.error=str(exc) if str(exc) in ('dedicated_private_repository_required','github_credential_actor_mismatch','github_request_failed','github_page_bound_exceeded') else 'adapter_requires_review'
                    try:
                        value=self.worker_health.record(error=self.error,state='DEGRADED')
                        delay=min(300,delay*2**min(value['failures'],5))
                    except OSError:
                        self.error='worker_health_persistence_failed'
                        print('Relay GitHub worker health persistence failed; worker degraded',flush=True)
                self.stop.wait(delay)
        self.thread=threading.Thread(target=run,name='Relay-V2-GitHub',daemon=True);self.thread.start()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=35)
    def snapshot(self):
        errors=self.bridge.completions.ledger.errors()
        return {'version':1,'source_sha256':V2_SOURCE_SHA256,'browser_error':self.browser_error,'github_enabled':self.config['github']['enabled'],'github_status':self.status,'validation_error_count':len(errors),'latest_validation_error':errors[0]['code'] if errors else None,'github_error':self.error,
          'browser_enabled':self.config['browser']['enabled'],'worker_health':dict(self.worker_health.value)}
