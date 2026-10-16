"""Private GitHub issue courier. Non-AI; no token extraction or uncertain POST retries."""
import json
import os
import re
import subprocess
import threading
from relay_state import compact,sha
from reliability import dispatch_paused

class BusError(Exception):pass

class GHClient:
    def __init__(self,repo):self.repo=repo;self.stop=None
    def call(self,path,method='GET',data=None):
        if self.stop and self.stop.is_set():raise BusError('adapter_stopping')
        if not path.startswith('repos/'+self.repo+'/') and path!='repos/'+self.repo and path!='user':
            raise BusError('endpoint_not_allowed')
        env=dict(os.environ)
        for key in ('GH_DEBUG','GH_HOST','GH_TOKEN','GITHUB_TOKEN','GH_ENTERPRISE_TOKEN','GITHUB_ENTERPRISE_TOKEN'):env.pop(key,None)
        # Existing gh credential store only; never invoke auth token or echo stderr.
        args=['gh','api','--hostname','github.com','--method',method,path,
              '-H','Accept: application/vnd.github+json']
        if data is not None:args+=['--input','-']
        try:
            proc=subprocess.run(args,input=compact(data).encode('utf-8') if data is not None else None,
              stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,timeout=10,
              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if proc.returncode:raise BusError('github_request_failed')
            if len(proc.stdout)>16*1024*1024:raise BusError('github_response_limit')
            return json.loads(proc.stdout) if proc.stdout else None
        except (OSError,subprocess.TimeoutExpired,ValueError):raise BusError('github_request_failed') from None
    def private(self):
        r=self.call('repos/'+self.repo)
        if self.repo.lower()=='grxr-dev/dev' or r.get('full_name')!=self.repo or r.get('private') is not True or r.get('archived'):
            raise BusError('dedicated_private_repository_required')
    def pages(self,suffix):
        rows=[]
        for page in range(1,4):
            part=self.call('repos/'+self.repo+'/'+suffix+('&' if '?' in suffix else '?')+'per_page=100&page='+str(page))
            if not isinstance(part,list):raise BusError('invalid_github_response')
            rows+=part
            if len(part)<100:return rows
        raise BusError('github_page_bound_exceeded')

def parse_issue(issue,author,routes):
    if issue.get('pull_request') is not None or issue.get('user',{}).get('login')!=author:
        raise ValueError('unexpected_author_or_pull_request')
    body=issue.get('body')
    if not isinstance(body,str) or '\r' in body or body.startswith('\ufeff'):
        raise ValueError('canonical_utf8_lf_required')
    body.encode('utf-8',errors='strict')
    lines=body.split('\n',6)
    if len(lines)!=7 or lines[0]!='---' or lines[1]!='codex_relay_version: 1' or lines[3]!='thread_key: main' or lines[5]!='---':
        raise ValueError('invalid_envelope')
    if not lines[2].startswith('request_id: ') or not lines[4].startswith('route_id: '):raise ValueError('invalid_envelope')
    ident=lines[2][12:];route=lines[4][10:];message=lines[6]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',ident):raise ValueError('invalid_request_id')
    if route not in routes:raise ValueError('unsupported_route_id')
    if issue.get('title')!='[CODEX RELAY] '+ident:raise ValueError('invalid_title')
    req={'request_id':ident,'thread_key':'main','route_id':route,'message':message}
    if len(compact(req).encode('utf-8'))>65536:raise ValueError('body_too_large')
    return req

class GitHubBus:
    def __init__(self,bridge,config,client=None):
        self.bridge=bridge;self.ledger=bridge.completions.ledger;self.config=config
        self.repo=config['repo'];self.author=config['expected_author'];self.client=client or GHClient(self.repo)
        self.status='disabled';self.actor=None;self.stop=threading.Event()
        if isinstance(self.client,GHClient):self.client.stop=self.stop
    def tick(self):
        self.client.private() # Revalidate privacy before each poll and any writes.
        if self.actor is None:self.actor=self.client.call('user')['login']
        if self.actor!=self.author:raise BusError('github_credential_actor_mismatch')
        issues=self.client.pages('issues?state=open&sort=created&direction=asc')
        for issue in issues:
            if not str(issue.get('title','')).startswith('[CODEX RELAY]'):continue
            try:
                req=parse_issue(issue,self.author,self.bridge.allowed_routes())
                self.ledger.intake(req,self.repo,issue['number'])
            except (ValueError,UnicodeError) as exc:
                safe={'request_id_conflict','unexpected_author_or_pull_request','canonical_utf8_lf_required','invalid_envelope','invalid_request_id','unsupported_route_id','invalid_title','body_too_large','inbox_capacity'}
                code='canonical_utf8_lf_required' if isinstance(exc,UnicodeError) else str(exc) if str(exc) in safe else 'invalid_envelope'
                self.ledger.error(self.repo+'#'+str(issue.get('number')),code)
                if code=='request_id_conflict':
                    self.freeze(req['request_id'],code)
        self.deliver()
        if not self.stop.is_set() and self.bridge.accepting_work and not self.bridge.turn_lock.locked() and self.bridge.health()['relay_ready']:
            with self.ledger.lock:
                pinned=self.ledger.db.execute("SELECT COALESCE(SUM(length(CAST(body AS BLOB))),0) FROM github_outbox WHERE state!='CLOSED'").fetchone()[0]
            if pinned>=32*1024*1024:raise BusError('github_delivery_capacity_requires_review')
            req=self.ledger.claim(blocked=dispatch_paused)
            if req:
                saved=self.ledger.get(req['request_id'])
                try:
                    live=self.client.call('repos/'+self.repo+'/issues/'+str(saved['github_issue_number']))
                    checked=parse_issue(live,self.author,self.bridge.allowed_routes())
                    if checked!=req:raise ValueError('issue_changed_before_dispatch')
                except (ValueError,UnicodeError):
                    self.bridge.completions.finish(req,409,{'ok':False,'status':'github_envelope_conflict','response':'','error':'Issue changed before dispatch; use a new request_id'})
                    return
                status,payload=self.bridge.submit(req,source='github')
                if payload.get('status') in ('busy','stopping','intentional_pause'):
                    with self.ledger.lock,self.ledger.db:
                        self.ledger.db.execute("UPDATE github_inbox SET state='QUEUED' WHERE request_id=?",(req['request_id'],))
                        self.ledger.db.execute("UPDATE requests SET state='QUEUED' WHERE request_id=?",(req['request_id'],))
                elif not self.ledger.get(req['request_id'])['terminal_at'] and status!=202:
                    self.bridge.completions.finish(req,status,payload)
        self.status='polling'
    def freeze(self,ident,reason):
        with self.ledger.lock:
            row=self.ledger.db.execute("SELECT request_json FROM github_inbox WHERE request_id=? AND state='QUEUED'",(ident,)).fetchone()
        if row:
            req=json.loads(row['request_json'])
            self.bridge.completions.finish(req,409,{'ok':False,'status':reason,'response':'','error':'Hard request identity conflict; use a new request_id'})
            with self.ledger.lock,self.ledger.db:self.ledger.db.execute("UPDATE github_inbox SET state='CONFLICT' WHERE request_id=?",(ident,))

    def deliver(self):
        with self.ledger.lock:
            rows=self.ledger.db.execute("SELECT DISTINCT r.* FROM requests r JOIN github_outbox o USING(request_id) WHERE r.delivery_state!='GITHUB_CLOSED' AND o.state!='CLOSED'").fetchall()
        for row in rows:
            if self.stop.is_set():return
            number=row['github_issue_number'];base='repos/'+self.repo+'/issues/'+str(number)
            self.client.private()
            comments=self.client.pages('issues/'+str(number)+'/comments')
            with self.ledger.lock:
                parts=self.ledger.db.execute('SELECT * FROM github_outbox WHERE request_id=? ORDER BY part',(row['request_id'],)).fetchall()
            complete=True
            for part in parts:
                if self.stop.is_set():return
                matches=[c for c in comments if c.get('body')==part['body'] and c.get('user',{}).get('login')==self.actor]
                if len(matches)>1:raise BusError('duplicate_result_comments_require_review')
                if matches:
                    self.mark(row['request_id'],part['part'],'VERIFIED',matches[0]['id']);continue
                if part['state']!='PENDING':
                    # A crash or uncertain network write can never produce a second POST.
                    complete=False;continue
                self.mark(row['request_id'],part['part'],'POSTING')
                try:
                    result=self.client.call(base+'/comments','POST',{'body':part['body']})
                    if result.get('body')!=part['body'] or result.get('user',{}).get('login')!=self.actor:
                        raise BusError('result_comment_verification_failed')
                    self.mark(row['request_id'],part['part'],'VERIFIED',result['id'])
                except Exception:
                    self.mark(row['request_id'],part['part'],'UNCERTAIN');raise
            if complete:
                issue=self.client.call(base)
                if issue.get('state')!='closed':self.client.call(base,'PATCH',{'state':'closed'})
                if self.client.call(base).get('state')!='closed':raise BusError('issue_close_not_verified')
                with self.ledger.lock,self.ledger.db:
                    self.ledger.db.execute("UPDATE github_outbox SET state='CLOSED',body='' WHERE request_id=?",(row['request_id'],))
    def mark(self,ident,part,state,comment=None):
        with self.ledger.lock,self.ledger.db:
            self.ledger.db.execute('UPDATE github_outbox SET state=?,comment_id=COALESCE(?,comment_id) WHERE request_id=? AND part=?',(state,comment,ident,part))
