"""Relay V2 metadata and delivery outbox, in the existing completion database."""
import hashlib
import json
import secrets
import time
from completions import timestamp
from reliability import usage_reset

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def compact(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))

def classification(payload):
    status=payload.get('status','failed')
    error=payload.get('error')
    info=error.get('codexErrorInfo') if isinstance(error,dict) else None
    if info=='usageLimitExceeded':return 'USAGE_EXHAUSTED','usageLimitExceeded'
    if info=='rateLimitExceeded':return 'RATE_LIMITED','rateLimitExceeded'
    if status=='completed' and payload.get('ok'):return 'COMPLETED','completed'
    if status=='interrupted':return 'INTERRUPTED','interrupted'
    if status.startswith('approval_'):return 'FAILED',status
    # Local evidence is supplied separately, never inferred from arbitrary prose.
    evidence=payload.get('relay_evidence')
    if evidence in ('APP_SERVER_LOST','TRANSPORT_LOST'):return evidence,evidence
    return 'FAILED',status

class Ledger:
    def __init__(self,store):
        self.store=store;self.db=store.db;self.lock=store.lock
        self.browser_enabled=False;self.conversation=None;self.last_event_write={}
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS requests(
          request_id TEXT PRIMARY KEY,thread_key TEXT,route_id TEXT,
          codex_thread_id TEXT,codex_turn_id TEXT,source TEXT NOT NULL,source_ref TEXT,
          prompt_sha256 TEXT,submitted_at TEXT,started_at TEXT,last_event_at TEXT,terminal_at TEXT,
          state TEXT,terminal_reason TEXT,result_available INTEGER DEFAULT 0,result_sha256 TEXT,
          delivery_state TEXT DEFAULT 'NONE',github_issue_number INTEGER,reconciliation TEXT);
        CREATE TABLE IF NOT EXISTS github_inbox(
          request_id TEXT PRIMARY KEY,request_json TEXT NOT NULL,state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS browser_outbox(
          sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE,request_id TEXT,
          event_json TEXT NOT NULL,acked_at TEXT,proof TEXT);
        CREATE TABLE IF NOT EXISTS github_outbox(
          request_id TEXT,part INTEGER,body TEXT NOT NULL,body_sha256 TEXT NOT NULL,
          state TEXT NOT NULL DEFAULT 'PENDING',comment_id INTEGER,
          PRIMARY KEY(request_id,part));
        CREATE TABLE IF NOT EXISTS reconciled_results(request_id TEXT PRIMARY KEY,payload BLOB,sha256 TEXT,checked_at TEXT);
        CREATE TABLE IF NOT EXISTS relay_v2_errors(source_ref TEXT PRIMARY KEY,code TEXT,time TEXT);
        CREATE TABLE IF NOT EXISTS usage_retry_intents(request_id TEXT PRIMARY KEY,request_json TEXT,
          prompt_sha256 TEXT,reset_at TEXT,state TEXT,error_json TEXT);
        """)
        for r in self.db.execute('SELECT * FROM completions').fetchall():
            self.db.execute("""INSERT OR IGNORE INTO requests(request_id,thread_key,route_id,
              codex_thread_id,codex_turn_id,source,submitted_at,terminal_at,state,terminal_reason,
              result_available) VALUES(?,?,?,?,?,'legacy',?,?,?,?,?)""",
              (r['request_id'],r['thread_key'],r['route_id'],r['thread_id'],r['turn_id'],
               r['completed_at'],r['completed_at'],r['status'].upper(),r['status'],int(r['result'] is not None)))
        self.db.commit()

    def reserve(self,request):
        self.db.execute("""INSERT OR IGNORE INTO requests(request_id,thread_key,route_id,source,
          prompt_sha256,submitted_at,last_event_at,state) VALUES(?,?,?,'http',?,?,?,'ACCEPTED')""",
          (request['request_id'],request['thread_key'],request.get('route_id','sol-high'),
           sha(request.get('message','')),timestamp(),timestamp()))
        self.db.execute("UPDATE requests SET state='ACCEPTED',last_event_at=? WHERE request_id=?",
                        (timestamp(),request['request_id']))
        self.db.execute("UPDATE github_inbox SET state='ACCEPTED',request_json='{}' WHERE request_id=?",
                        (request['request_id'],))

    def bind(self,ident,thread,turn):
        self.db.execute("""UPDATE requests SET codex_thread_id=?,codex_turn_id=?,started_at=?,
          last_event_at=?,state='RUNNING' WHERE request_id=?""",(thread,turn,timestamp(),timestamp(),ident))

    def state(self,ident,state):
        self.db.execute('UPDATE requests SET state=?,last_event_at=? WHERE request_id=?',
          ('APPROVAL_REQUIRED' if state=='awaiting_approval' else 'RUNNING',timestamp(),ident))
        row=self.get(ident)
        if state=='awaiting_approval' and row and row['source']=='github':
            notice=compact({'request_id':ident,'status':'APPROVAL_REQUIRED','action':'Use the existing local approval monitor; browser courier cannot approve'})
            self.browser_event(dict(row,terminal_reason='human_action_required'),notice)

    def event(self,ident,event):
        now=time.monotonic()
        if now-self.last_event_write.get(ident,0)<1 and event.get('method') not in ('turn/completed','error'):return
        self.last_event_write[ident]=now
        # Timestamp only: do not persist reasoning, raw tool arguments, or event text.
        with self.lock,self.db:
            self.db.execute('UPDATE requests SET last_event_at=? WHERE request_id=?',(timestamp(),ident))

    def terminal(self,request,payload,retained):
        self.reserve_if_missing(request)
        state,reason=classification(payload)
        if state in ('USAGE_EXHAUSTED','RATE_LIMITED'):
            saved=self.db.execute('SELECT request_json FROM github_inbox WHERE request_id=?',(request['request_id'],)).fetchone()
            original=json.loads(saved[0]) if saved and saved[0]!='{}' else request
            error=payload.get('error')
            reset,retry_state=usage_reset(error)
            self.db.execute('INSERT OR IGNORE INTO usage_retry_intents VALUES(?,?,?,?,?,?)',
                (request['request_id'],compact(original),sha(original.get('message','')),str(reset) if reset is not None else None,
                 retry_state,compact(error)))
        self.db.execute("UPDATE github_inbox SET state='TERMINAL',request_json='{}' WHERE request_id=?",(request['request_id'],))
        text=payload.get('response','') if state=='COMPLETED' else compact(payload)
        self.db.execute("""UPDATE requests SET state=?,terminal_reason=?,terminal_at=?,last_event_at=?,
          result_available=?,result_sha256=?,codex_thread_id=COALESCE(codex_thread_id,?)
          WHERE request_id=?""",(state,reason,timestamp(),timestamp(),int(retained),sha(text),
          payload.get('codex_thread_id'),request['request_id']))
        row=self.get(request['request_id'])
        if row['source']=='github':
            # Pin exact delivery text independently of bounded legacy result retention.
            parts=result_comments(row,text)
            for index,body in enumerate(parts):
                self.db.execute('INSERT OR IGNORE INTO github_outbox(request_id,part,body,body_sha256) VALUES(?,?,?,?)',
                                (row['request_id'],index,body,sha(body)))
            self.db.execute("UPDATE requests SET delivery_state='RESULT_PENDING_DELIVERY' WHERE request_id=?",(row['request_id'],))
            self.browser_event(row,text)

    def reserve_if_missing(self,request):
        if not self.db.execute('SELECT 1 FROM requests WHERE request_id=?',(request['request_id'],)).fetchone():
            self.reserve(request)

    def browser_event(self,row,text):
        # Events are durable even while browser delivery is disabled. No legacy HTTP wakeups.
        existing=self.db.execute("SELECT event_json FROM browser_outbox WHERE request_id=?",(row['request_id'],)).fetchall()
        existing=any(json.loads(r['event_json'])['status']==row['state'] for r in existing)
        if existing:return
        count,size=self.db.execute("SELECT COUNT(*),COALESCE(SUM(length(CAST(event_json AS BLOB))),0) FROM browser_outbox WHERE acked_at IS NULL").fetchone()
        if count>=128 or size+len(text.encode('utf-8'))>32*1024*1024:
            self.db.execute("UPDATE requests SET delivery_state='BROWSER_CAPACITY_BLOCKED' WHERE request_id=?",(row['request_id'],));return
        message='[CODEX → CHATGPT]\n'+text
        event={'event_id':secrets.token_urlsafe(24),'request_id':row['request_id'],'route_id':row['route_id'],
          'status':row['state'],'terminal_reason':row['terminal_reason'],'result':text,
          'result_sha256':sha(text),'message':message,'message_sha256':sha(message)}
        self.db.execute('INSERT INTO browser_outbox(event_id,request_id,event_json) VALUES(?,?,?)',
                        (event['event_id'],row['request_id'],compact(event)))

    def intake(self,request,repo,issue):
        with self.lock,self.db:
            old=self.get(request['request_id'])
            ref=repo+'#'+str(issue)
            if old:
                if old['prompt_sha256']!=sha(request['message']) or old['route_id']!=request['route_id'] or old['source_ref']!=ref:
                    raise ValueError('request_id_conflict')
                return False
            if self.db.execute('SELECT COUNT(*) FROM requests WHERE terminal_at IS NULL').fetchone()[0]>=128:raise ValueError('inbox_capacity')
            self.db.execute("""INSERT INTO requests(request_id,thread_key,route_id,source,source_ref,
              prompt_sha256,submitted_at,last_event_at,state,github_issue_number)
              VALUES(?,?,?,'github',?,?,?,?, 'QUEUED',?)""",(request['request_id'],'main',request['route_id'],ref,
              sha(request['message']),timestamp(),timestamp(),issue))
            self.db.execute("INSERT INTO github_inbox VALUES(?,?,'QUEUED')",(request['request_id'],compact(request)))
            return True

    def claim(self,blocked=None):
        with self.lock,self.db:
            rows=self.db.execute("SELECT * FROM github_inbox WHERE state='QUEUED' ORDER BY rowid LIMIT 128").fetchall()
            row=next((candidate for candidate in rows if not blocked or not blocked(json.loads(candidate['request_json']))),None)
            if not row:return None
            self.db.execute("UPDATE github_inbox SET state='DISPATCHING' WHERE request_id=?",(row['request_id'],))
            self.db.execute("UPDATE requests SET state='DISPATCHING' WHERE request_id=?",(row['request_id'],))
            return json.loads(row['request_json'])

    def get(self,ident):
        with self.lock:
            row=self.db.execute('SELECT * FROM requests WHERE request_id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def recovered(self,ident):
        with self.lock:
            row=self.db.execute('SELECT * FROM reconciled_results WHERE request_id=?',(ident,)).fetchone()
            return {'checked_at':row['checked_at'],'payload_sha256':row['sha256'],'payload':json.loads(bytes(row['payload']).decode('utf-8'))} if row else None

    def history(self):
        with self.lock:
            return [dict(r) for r in self.db.execute('SELECT * FROM requests ORDER BY submitted_at DESC LIMIT 64')]

    def active(self):
        with self.lock:
            return [dict(r) for r in self.db.execute('SELECT * FROM requests WHERE terminal_at IS NULL ORDER BY submitted_at LIMIT 128')]

    def events(self,after):
        with self.lock:
            rows=self.db.execute('SELECT * FROM browser_outbox WHERE acked_at IS NULL ORDER BY sequence LIMIT 16').fetchall()
            # Pending events cannot be skipped by an advanced client cursor.
            return {'ok':True,'events':[dict(json.loads(r['event_json']),sequence=r['sequence']) for r in rows],
              'next_sequence':rows[-1]['sequence'] if rows else after}

    def ack(self,proof):
        required={'event_id','sequence','result_sha256','message_sha256','conversation_url','user_message_id'}
        if not isinstance(proof,dict) or set(proof)!=required or any(not isinstance(proof[k],str) for k in required-{'sequence'}):
            raise ValueError('invalid_ack')
        if type(proof['sequence']) is not int or not 1<=len(proof['user_message_id'])<=256 or proof['conversation_url']!=self.conversation:
            raise ValueError('invalid_ack')
        with self.lock,self.db:
            row=self.db.execute('SELECT * FROM browser_outbox WHERE event_id=? AND sequence=?',(proof['event_id'],proof['sequence'])).fetchone()
            if not row:raise ValueError('unknown_event')
            event=json.loads(row['event_json'])
            if any(proof[k]!=event[k] for k in ('result_sha256','message_sha256')):raise ValueError('hash_mismatch')
            if row['acked_at']:
                if row['proof']!=compact(proof):raise ValueError('ack_conflict')
                return {'ok':True,'already_acknowledged':True}
            self.db.execute('UPDATE browser_outbox SET acked_at=?,proof=?,event_json=? WHERE event_id=?',(timestamp(),compact(proof),compact({k:v for k,v in event.items() if k not in ('result','message')}),proof['event_id']))
            if event['status']!='APPROVAL_REQUIRED':
                self.db.execute("UPDATE requests SET delivery_state='DELIVERED' WHERE request_id=?",(row['request_id'],))
            return {'ok':True,'already_acknowledged':False}

    def errors(self):
        with self.lock:
            return [dict(r) for r in self.db.execute('SELECT * FROM relay_v2_errors ORDER BY time DESC LIMIT 32')]

    def error(self,ref,code):
        with self.lock,self.db:
            self.db.execute('INSERT OR REPLACE INTO relay_v2_errors VALUES(?,?,?)',(ref,code,timestamp()))


def result_comments(row,text):
    header=('---\ncodex_relay_result_version: 1\nrequest_id: '+row['request_id']+
      '\nroute_id: '+row['route_id']+'\nstatus: '+row['state']+'\nterminal_reason: '+row['terminal_reason']+
      '\nresult_sha256: '+sha(text)+'\n---\n')
    message='[CODEX → CHATGPT]\n'+text
    if len((header+message).encode('utf-8'))<=60000:return [header+message]
    chunks=[];part='';size=0
    for char in message:
        n=len(char.encode('utf-8'))
        if size+n>58000:chunks.append(part);part='';size=0
        part+=char;size+=n
    if part:chunks.append(part)
    bodies=[header+'chunk: '+str(i+1)+'/'+str(len(chunks))+'\nchunk_sha256: '+sha(chunk)+'\n\n'+chunk for i,chunk in enumerate(chunks)]
    bodies.append(header+'manifest: '+compact({'message_sha256':sha(message),'chunks':[sha(c) for c in chunks]}))
    return bodies
