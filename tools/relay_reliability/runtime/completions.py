"""Bounded durable terminal relay outcomes. No Codex control or task text."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import secrets
import sqlite3
import threading

EVENT_COLUMNS = "sequence,event_id,request_id,thread_key,route_id,thread_id,turn_id,status,completed_at,unavailable_reason,failure,(result IS NOT NULL) AS result_available"
MAX_EVENTS = 256
MAX_RESULT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_RESULT_BYTES = 32 * 1024 * 1024
PAGE_SIZE = 32

def timestamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

class CompletionStore:
    def __init__(self, path, max_events=MAX_EVENTS, max_result_bytes=MAX_RESULT_BYTES,
                 max_total_bytes=MAX_TOTAL_RESULT_BYTES, recover_pending=True):
        self.lock=threading.RLock()
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(path),check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.max_events=max_events;self.max_result_bytes=max_result_bytes;self.max_total_bytes=max_total_bytes
        self.last_access=None
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS pending (
                request_id TEXT PRIMARY KEY, thread_key TEXT NOT NULL, route_id TEXT NOT NULL,
                thread_id TEXT, turn_id TEXT);
            CREATE TABLE IF NOT EXISTS completions (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                request_id TEXT UNIQUE NOT NULL, thread_key TEXT NOT NULL, route_id TEXT NOT NULL,
                thread_id TEXT, turn_id TEXT, status TEXT NOT NULL, completed_at TEXT NOT NULL,
                result BLOB, result_bytes INTEGER NOT NULL, unavailable_reason TEXT, failure TEXT);
        """)
        columns={row[1] for row in self.db.execute('PRAGMA table_info(pending)')}
        if 'state' not in columns:self.db.execute("ALTER TABLE pending ADD COLUMN state TEXT NOT NULL DEFAULT 'accepted'")
        if 'accepted_at' not in columns:self.db.execute('ALTER TABLE pending ADD COLUMN accepted_at TEXT')
        self.db.commit()
        from relay_state import Ledger
        self.ledger=Ledger(self)
        # A reserved relay from a previous process can never be replayed. Its
        # actual turn state is unknown, so report interruption explicitly.
        for row in self.db.execute('SELECT * FROM pending').fetchall() if recover_pending else []:
            payload={'ok':False,'request_id':row['request_id'],'thread_key':row['thread_key'],
                'route_id':row['route_id'],'status':'interrupted','response':'',
                'response_sha256':hashlib.sha256(b'').hexdigest(),
                'error':'relay_lost_after_restart; terminal Codex state unknown; no automatic replay'}
            self.finish(dict(row),503,payload)

    def reserve(self, request):
        with self.lock,self.db:
            saved=self.ledger.get(request['request_id'])
            if saved and saved['terminal_at']:return False
            if self.db.execute('SELECT 1 FROM completions WHERE request_id=?',(request['request_id'],)).fetchone():
                return False
            if self.db.execute('SELECT 1 FROM pending WHERE request_id=?',(request['request_id'],)).fetchone():
                return False
            self.db.execute('INSERT INTO pending(request_id,thread_key,route_id,state,accepted_at) VALUES (?,?,?,?,?)',
                (request['request_id'],request['thread_key'],request.get('route_id','sol-high'),'accepted',timestamp()))
            self.ledger.reserve(request)
            return True

    def bind_turn(self, request_id, thread_id, turn_id):
        with self.lock,self.db:
            self.db.execute("UPDATE pending SET thread_id=?,turn_id=?,state='running' WHERE request_id=?",
                (thread_id,turn_id,request_id))
            self.ledger.bind(request_id,thread_id,turn_id)

    def set_state(self, request_id, state):
        with self.lock,self.db:
            self.db.execute('UPDATE pending SET state=? WHERE request_id=?',(state,request_id))
            self.ledger.state(request_id,state)

    def known(self, request_id):
        """Idempotent submission reply: metadata only, never start/resume work."""
        from urllib.parse import quote
        with self.lock:
            row=self.db.execute('SELECT * FROM pending WHERE request_id=?',(request_id,)).fetchone()
            if row:
                return 202, {'ok':True,'request_id':row['request_id'],'thread_key':row['thread_key'],
                    'route_id':row['route_id'],'status':row['state'],'codex_thread_id':row['thread_id'],
                    'codex_turn_id':row['turn_id'],'already_submitted':True}
            row=self.db.execute('SELECT '+EVENT_COLUMNS+' FROM completions WHERE request_id=?',(request_id,)).fetchone()
            if row:
                return 200, {'ok':True,**self._event(row),'already_submitted':True,
                    'result_url':'/results/'+quote(request_id,safe='')}
            return None

    def active(self):
        with self.lock:
            row=self.db.execute('SELECT * FROM pending LIMIT 1').fetchone()
            return ({'request_id':row['request_id'],'route_id':row['route_id'],'state':row['state'],
                'codex_thread_id':row['thread_id'],'codex_turn_id':row['turn_id'],'accepted_at':row['accepted_at']} if row else None)

    def finish(self, request, http_status, payload):
        with self.lock,self.db:
            existing=self.db.execute('SELECT sequence FROM completions WHERE request_id=?',(request['request_id'],)).fetchone()
            if existing:return existing['sequence']
            pending=self.db.execute('SELECT * FROM pending WHERE request_id=?',(request['request_id'],)).fetchone()
            status=payload.get('status','failed')
            # Preserve exact terminal bridge status, including preflight failures.
            stored=copy.deepcopy(payload)
            stored.setdefault('request_id',request['request_id']);stored.setdefault('thread_key',request['thread_key'])
            stored.setdefault('response','');stored.setdefault('response_sha256',hashlib.sha256(stored['response'].encode('utf-8')).hexdigest())
            encoded=json.dumps(stored,ensure_ascii=False,separators=(',',':')).encode('utf-8')
            reason=None
            if len(encoded)>self.max_result_bytes:
                encoded=None;reason='result_exceeds_retention_limit'
            failure=None if payload.get('ok') else json.dumps({'code':status,'http_status':http_status})
            cursor=self.db.execute("""INSERT INTO completions(event_id,request_id,thread_key,route_id,
                thread_id,turn_id,status,completed_at,result,result_bytes,unavailable_reason,failure)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(secrets.token_urlsafe(24),request['request_id'],request['thread_key'],
                request.get('route_id','sol-high'),payload.get('codex_thread_id') or (pending['thread_id'] if pending else None),
                pending['turn_id'] if pending else None,status,timestamp(),encoded,len(encoded) if encoded else 0,reason,failure))
            self.db.execute('DELETE FROM pending WHERE request_id=?',(request['request_id'],))
            self.db.execute('DELETE FROM completions WHERE sequence NOT IN (SELECT sequence FROM completions ORDER BY sequence DESC LIMIT ?)',(self.max_events,))
            total=self.db.execute('SELECT COALESCE(SUM(result_bytes),0) FROM completions').fetchone()[0]
            for row in self.db.execute('SELECT sequence,result_bytes FROM completions WHERE result IS NOT NULL ORDER BY sequence').fetchall():
                if total<=self.max_total_bytes:break
                self.db.execute("UPDATE completions SET result=NULL,result_bytes=0,unavailable_reason='result_retention_evicted' WHERE sequence=?",(row['sequence'],))
                total-=row['result_bytes']
            self.db.execute("UPDATE requests SET result_available=EXISTS(SELECT 1 FROM completions c WHERE c.request_id=requests.request_id AND c.result IS NOT NULL) WHERE source IN ('http','legacy')")
            self.ledger.terminal(request,stored,encoded is not None)
            return cursor.lastrowid

    def _event(self,row):
        event={key:row[key] for key in ('sequence','event_id','request_id','thread_key','route_id','status','completed_at')}
        event.update(codex_thread_id=row['thread_id'],codex_turn_id=row['turn_id'],result_available=bool(row['result_available']))
        if row['failure']:event['failure']=json.loads(row['failure'])
        if row['unavailable_reason']:event['result_unavailable_reason']=row['unavailable_reason']
        return event

    def events(self,after):
        with self.lock:
            self.last_access=timestamp()
            bounds=self.db.execute('SELECT MIN(sequence),MAX(sequence) FROM completions').fetchone()
            latest=self.db.execute("SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name='completions'),0)").fetchone()[0]
            rows=self.db.execute('SELECT '+EVENT_COLUMNS+' FROM completions WHERE sequence>? ORDER BY sequence LIMIT ?', (after,PAGE_SIZE+1)).fetchall()
            page=rows[:PAGE_SIZE]
            return {'ok':True,'events':[self._event(row) for row in page],'latest_sequence':latest,
                'next_sequence':page[-1]['sequence'] if page else after,'has_more':len(rows)>PAGE_SIZE,
                'oldest_sequence':bounds[0], 'cursor_expired':bounds[0] is not None and after<bounds[0]-1,
                'cursor_ahead':after>latest}

    def result(self,request_id):
        with self.lock:
            active=self.db.execute('SELECT 1 FROM pending WHERE request_id=?',(request_id,)).fetchone()
            if active:return self.known(request_id)
            row=self.db.execute('SELECT * FROM completions WHERE request_id=?',(request_id,)).fetchone()
            if not row:return 404,{'ok':False,'error':'result_not_retained_or_unknown','request_id':request_id}
            if row['result'] is None:
                return 410,{'ok':False,'error':row['unavailable_reason'],'request_id':request_id,'status':row['status']}
            return 200,json.loads(bytes(row['result']).decode('utf-8'))

    def summary(self):
        with self.lock:
            row=self.db.execute('SELECT '+EVENT_COLUMNS+' FROM completions ORDER BY sequence DESC LIMIT 1').fetchone()
            return {'latest_sequence':row['sequence'] if row else 0,'latest_request_id':row['request_id'] if row else None,
                'latest_status':row['status'] if row else None,'latest_completed_at':row['completed_at'] if row else None,
                'hook_last_poll_at':self.last_access}

    def close(self):
        with self.lock:self.db.close()
