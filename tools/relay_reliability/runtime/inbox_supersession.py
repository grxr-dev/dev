"""One pinned stale watchdog disposition, verified against GitHub and read-only results."""
import hashlib,json,sqlite3
from datetime import datetime
from pathlib import Path
from inbox_queue import Conflict
from github_bus import GHClient,parse_issue,BusError
WATCHDOG='jarvis-continuity-watchdog:1fe09e7e9c1dec11d6dbd2385e0fb9cb8697ab85ede379f0308cd467b361ec52'
HASH=WATCHDOG.split(':')[1]
REPO='grxr-dev/codex-relay'
TASKS=[(10,70,'c699e3a21207abaa72b8130bf54c0f189c846412'),(11,74,'b10e83d9f5e236930d7b2fd8e1b2b301e978decc'),(12,76,'b60203a9d30b3a8536395aaacdd15d126ee88399'),(13,78,'1d64040633738bc63b5f49d2718d5c30dbad801c')]
BUILD='inbox-supersede-watchdog-20261016-01'
def proof_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def instant(s):
 d=datetime.fromisoformat(s.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('timestamp timezone missing')
 return d.timestamp()
class SupersessionPolicy:
 def __init__(self,runtime,client=None):self.runtime=Path(runtime);self.client=client or GHClient(REPO)
 def verify(self):
  db=None
  try:
   self.client.private()
   if self.client.call('user')['login']!='grxr-dev':raise ValueError('unexpected GitHub actor')
   db=sqlite3.connect((self.runtime/'completions.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
   proof=[];previous=None;previous_commit=None
   for n,issue,commit in TASKS:
    request='brainage-task-aw'+str(n)+'-20261015-01'
    live=self.client.call('repos/'+REPO+'/issues/'+str(issue));parsed=parse_issue(live,'grxr-dev',{'sol-high'})
    if live.get('number')!=issue or live.get('state')!='closed' or parsed['request_id']!=request:raise ValueError('wrong issue identity/state')
    if previous_commit and previous_commit not in parsed['message']:raise ValueError('successor provenance missing')
    row=db.execute('SELECT r.*,c.sequence,c.status AS completion_status,c.completed_at,c.result,c.result_bytes,c.failure,c.unavailable_reason FROM requests r JOIN completions c USING(request_id) WHERE r.request_id=?',(request,)).fetchone()
    if row is None or row['state']!='COMPLETED' or row['source']!='github' or row['source_ref']!=REPO+'#'+str(issue) or row['github_issue_number']!=issue or row['result_available']!=1 or row['terminal_reason']!='completed' or row['prompt_sha256']!=hashlib.sha256(parsed['message'].encode()).hexdigest() or row['completion_status']!='completed' or row['failure'] is not None or row['unavailable_reason'] is not None:raise ValueError('missing authoritative completed result')
    blob=row['result']
    if not isinstance(blob,bytes) or len(blob)!=row['result_bytes']:raise ValueError('result unavailable/corrupt')
    result=json.loads(blob);text=result['response'];digest=hashlib.sha256(text.encode()).hexdigest()
    if result['request_id']!=request or result['ok'] is not True or result['status']!='completed' or digest!=result['response_sha256'] or digest!=row['result_sha256'] or commit not in text:raise ValueError('result identity/hash/commit mismatch')
    created=instant(live['created_at']);completed=instant(row['completed_at']);closed=instant(live['closed_at'])
    if created>completed or completed>closed+60 or (previous is not None and created<=previous):raise ValueError('supersession ordering invalid')
    proof.append({'request_id':request,'issue':issue,'commit':commit,'sequence':row['sequence'],'created_at':live['created_at'],'completed_at':row['completed_at'],'closed_at':live['closed_at'],'result_sha256':digest,'prompt_sha256':hashlib.sha256(parsed['message'].encode()).hexdigest()})
    previous=completed;previous_commit=commit
   return {'repo':REPO,'watchdog':WATCHDOG,'payload_sha256':HASH,'source_task':proof[0],'superseding_tasks':proof[1:]}
  except (BusError,ValueError,KeyError,TypeError,sqlite3.Error,OSError):raise Conflict('watchdog provenance/superseding completion evidence not verified') from None
  finally:
   if db is not None:db.close()
class SupersessionAdmin:
 def __init__(self,queue,policy=None):self.queue=queue;self.policy=policy or SupersessionPolicy(queue.path.parent)
 def status(self):
  with self.queue.lock:
   try:proof=self.policy.verify();error=None
   except Conflict as e:proof=None;error=str(e)
   e=self.queue._entries.get(WATCHDOG)
   return {'ok':True,'build':BUILD,'delivery_id':WATCHDOG,'state':e['state'] if e else None,'attempt_count':e['attempt_count'] if e else None,'disposition_exists':self.queue._supersession is not None,'queue_fingerprint':self.queue.fingerprint(),'proof':proof,'proof_sha256':proof_sha(proof) if proof else None,'evidence_verified':proof is not None,'error':error}
 def cancel(self,body):
  if not isinstance(body,dict) or set(body)!={'delivery_id','expected_fingerprint','expected_proof_sha256'}:raise ValueError('exact supersession schema required')
  for k in ['expected_fingerprint','expected_proof_sha256']:
   if not isinstance(body[k],str) or len(body[k])!=64:raise ValueError('invalid expected fingerprint/hash')
  return {'ok':True,'build':BUILD,**self.queue.supersede_watchdog(body['delivery_id'],body['expected_fingerprint'],body['expected_proof_sha256'],self.policy.verify)}
