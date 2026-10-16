"""Local administrator-only, single-target, single-extra-attempt recovery.
No browser/native administrative capability; token stays in bridge runtime.
"""
import copy,hashlib,hmac,json,os,re,secrets,time
from pathlib import Path
from inbox_queue import Conflict
TARGET='brainage-task-aw5-20261015-01:52508ca28d2650562bee990b9780e050cfbab9a3a3854699bfd05dc74d391bf4'
TEXT_SHA256='4a4270b65d7f6b55968d7352c74d166074eec02822cd69a88a4651237687778b'
BOUND='6acab580-d218-83ea-9598-0ff64dc33aa7'
BUILD='inbox-recovery-once-20261015-01'
MAX_READY_AGE_MS=60000
class RecoveryAdmin:
 def __init__(self,queue):
  self.queue=queue;self.runtime=queue.path.parent
  self.token_path=self.runtime/'inbox_recovery_admin.token'
  self.runtime.mkdir(parents=True,exist_ok=True)
  try:
   with self.token_path.open('x',encoding='ascii') as f:f.write(secrets.token_hex(32));f.flush();os.fsync(f.fileno())
  except FileExistsError:pass
  self.token=self.token_path.read_text(encoding='ascii').strip()
  if not re.fullmatch('[0-9a-f]{64}',self.token):raise ValueError('invalid local recovery admin token')
  queue._recovery_check=self.check_readiness
 def authorized(self,headers):
  values=headers.get_all('X-Jarvis-Admin',[])
  return len(values)==1 and hmac.compare_digest(values[0],self.token)
 def check_readiness(self,probe_id=None):
  try:
   p=self.runtime/'inbox_readiness_result.json'
   if p.stat().st_size>65536:raise ValueError()
   r=json.loads(p.read_text(encoding='utf-8'))
   age=self.queue.clock()*1000-r['observed_ms']
   if type(r['observed_ms']) not in (int,float) or not -5000<=age<=MAX_READY_AGE_MS:raise ValueError()
   if not isinstance(r['probe_id'],str) or not re.fullmatch('[0-9a-f]{32}',r['probe_id']):raise ValueError()
   hold=self.runtime/'inbox_readiness_request.json'
   if probe_id is None or hold.exists():
    if hold.stat().st_size>128:raise ValueError()
    request=json.loads(hold.read_text(encoding='utf-8'))
    if request!={'probe_id':r['probe_id']}:raise ValueError()
   if probe_id is not None and r['probe_id']!=probe_id:raise ValueError()
   if type(r.get('native_pid')) is not int or r['native_pid']<=0:raise ValueError()
   if r['build']!='inbox-readiness-20261015-01' or type(r['match_count']) is not int or r['match_count']!=1 or r['truncated'] is not False or r['ready'] is not True or r['reason']!='ready' or len(r['matches'])!=1:raise ValueError()
   t=r['matches'][0]
   if t['url']!='https://chatgpt.com/c/'+BOUND or t.get('hidden') is not False or t.get('discarded') is not False or t.get('incognito') is not False or type(t['id']) is not int or type(t['windowId']) is not int:raise ValueError()
   c=r['content']
   if any(c[k] is not True for k in ['reachable','bound','composer_present','composer_empty','ready']) or c['busy'] is not False or c['generation_active'] is not False:raise ValueError()
   return {k:copy.deepcopy(r[k]) for k in ['probe_id','build','observed_ms','native_pid','match_count','matches','ready','content']}
  except (OSError,ValueError,KeyError,TypeError):raise Conflict('fresh exact bound-tab readiness required; refresh no-send probe') from None
 def release_hold(self,proof):
  # Queue lock is held; PREPARED is durable and cannot be claimed.
  p=self.runtime/'inbox_readiness_request.json'
  if json.loads(p.read_text())!={'probe_id':proof['probe_id']}:raise Conflict('readiness request changed before release')
  os.replace(p,self.runtime/'inbox_recovery_readiness_authorized.json')
 def status(self):
  with self.queue.lock:
   try:ready=self.check_readiness();error=None
   except Conflict as e:ready=None;error=str(e)
   e=self.queue._entries.get(TARGET)
   return {'ok':True,'build':BUILD,'delivery_id':TARGET,'queue_fingerprint':self.queue.fingerprint(),'state':e['state'] if e else None,'attempt_count':e['attempt_count'] if e else None,'recovery_status':self.queue._recovery['status'] if self.queue._recovery else None,'ready':ready is not None,'readiness':ready,'readiness_error':error}
 def capture_evidence(self):
  files=sorted(self.runtime.glob('inbox_verifier_trace.jsonl*'))
  incident=self.runtime/'inbox_verifier_incidents'/(hashlib.sha256(TARGET.encode()).hexdigest()+'.jsonl')
  if incident.exists():files.append(incident)
  records=[];sources={};total=0
  for p in files:
   raw=p.read_bytes();total+=len(raw)
   if total>8*1024*1024:raise Conflict('prior evidence exceeds bounded capture; preserve/export before recovery')
   sources[str(p.relative_to(self.runtime))]=hashlib.sha256(raw).hexdigest()
   for line in raw.splitlines():
    try:record=json.loads(line)
    except ValueError:raise Conflict('prior evidence is malformed; preserve before recovery') from None
    if record.get('delivery_id')==TARGET:records.append({'source':str(p.relative_to(self.runtime)),'record':record})
  return {'records':records,'source_sha256':sources}
 def recover(self,body):
  if not isinstance(body,dict) or set(body)!={'delivery_id','expected_fingerprint'}:raise ValueError('exact recovery schema required')
  if not isinstance(body['expected_fingerprint'],str) or not re.fullmatch('[0-9a-f]{64}',body['expected_fingerprint']):raise ValueError('invalid fingerprint')
  return {'ok':True,'build':BUILD,**self.queue.recover_once(body['delivery_id'],body['expected_fingerprint'],self.check_readiness,self.release_hold,self.capture_evidence)}
