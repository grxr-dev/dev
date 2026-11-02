"""One post-terminal managed install + exact seq135 receipt; no Send or cursor API.

Original tray, source migration journal/rollback, instance lock and receipt kernel
are reused. Later claims require the NEW loaded content proof build. No old DOM
receipt gate; one temporary-add-on Reload/tab refresh may be needed after install.
"""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import postturn_receipt134 as owner
from receipt135 import receipt,KERNEL

r=owner.r;m=r.m
AREA=r.RUNTIME/'inbox-composer135-deployment'
TASK='MuseInbox-Composer135-Deploy-Once'
BUILD='inbox-composer-user-proof-20261102-01'
METHOD='composer_hash_single_send_new_user_uuid_v1'
owner.AREA=AREA;owner.TASK=TASK;owner.owner.AREA=AREA;owner.owner.TASK=TASK
r.AREA=AREA;r.PROOF_BUILD=BUILD

def record(phase,**fields):
 value={'phase':phase,'at':time.time(),**fields};m.save(AREA/'state.json',m.sealed(value));return value

def installed(plan):
 if m.checked_binding(r.BRIDGE)!=plan['new_binding'] or json.loads((r.RUNTIME/'inbox_future.json').read_text())!=plan['new_policy']:raise ValueError('new coherent source/policy not installed')
 if m.state_hashes(r.BRIDGE)!=plan['protected']:raise ValueError('historical HOLD/native state changed')

def queue():
 sys.path.insert(0,str(r.BRIDGE));from inbox_queue import InboxQueue
 q=InboxQueue(r.RUNTIME/'inbox_future_queue.json');e=q._entries.get(receipt.TARGET)
 if q.fingerprint()!=receipt.FINGERPRINT or not e or e['state']!='NEEDS_REVIEW' or e['attempt_count']!=1 or e['text_sha256']!=receipt.TEXT_SHA or e['outcome'].get('send_intent') is not True or 'operator_receipt' in e['outcome']:raise ValueError('exact seq135 queue changed; no receipt')
 if any(e['state']=='DELIVERING' for e in q._entries.values()) or json.loads((r.RUNTIME/'inbox_native_recovery.json').read_text()) is not None:raise ValueError('active delivery/ACK; no install')
 return q

def validated():
 r.managed.AREA=AREA
 a=m.read_sealed(AREA/'activation.json');r.managed.verify_tools(a)
 return a,m.read_sealed(AREA/'plan.json')

def wait_loaded(plan):
 started=time.time()*1000
 m.save(r.RUNTIME/'inbox_binding_probe.json',{'probe_id':uuid.uuid4().hex,'binding_identity':plan['new_binding']['identity']})
 until=time.monotonic()+3600
 while time.monotonic()<until:
  installed(plan)
  try:
   value=json.loads((r.RUNTIME/'inbox_binding_readiness.json').read_text())
   if value.get('observed_ms',0)>=started and r.checked_readiness(value,plan,value.get('probe_id'),time.time()*1000):return value
  except (ValueError,OSError,KeyError):pass
  time.sleep(5)
 raise ValueError('new loaded extension/native/content proof pending; no later old-build Send possible')

def objects(record):
 # Only Jarvis-labelled replies. Never interpret our own request as its ACK.
 text=record.get('body','')
 if record.get('user',{}).get('login')!='grxr-dev' or not text.startswith('[JARVIS'):return []
 values=[];decoder=json.JSONDecoder()
 for i,c in enumerate(text):
  if c!='{':continue
  try:v,_=decoder.raw_decode(text[i:])
  except ValueError:continue
  if isinstance(v,dict):values.append(v)
 return values

def vm_ack(plan,after,action,minimum,timeout=600):
 created=owner.gh(['repos/grxr-dev/codex-relay/issues/comments/'+str(after)])['created_at']
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  for comment in owner.gh(['repos/grxr-dev/codex-relay/issues/45/comments?per_page=100&since='+created]):
   if comment['id']<=after:continue
   for v in objects(comment):
    if v.get('action')==action and v.get('in_reply_to')==after and v.get('binding_identity')==plan['new_binding']['identity'] and v.get('seal')==plan['new_policy']['seal'] and v.get('lane_id')==plan['new_policy']['lane_id'] and type(v.get('future_cursor')) is int and v['future_cursor']>=minimum and v.get('historical_state_unchanged') is True:return {'comment_id':comment['id'],**v}
  time.sleep(15)
 raise ValueError('independent Jarvis typed gate/cursor proof pending; no invented VM success')

def monitor(plan,after):
 until=time.monotonic()+600
 while time.monotonic()<until:
  installed(plan);q=json.loads((r.RUNTIME/'inbox_future_queue.json').read_text())
  later=[e for e in q['entries'].values() if (e.get('outcome') or {}).get('_future',{}).get('source',{}).get('sequence',0)>=136]
  failed=[e for e in later if e['state'] in ('NEEDS_REVIEW','FAILED_PERMANENT')]
  if failed:
   e=min(failed,key=lambda e:e['outcome']['_future']['source']['sequence'])
   result=record('STOPPED_ON_NEW_REVIEW',sequence=e['outcome']['_future']['source']['sequence'],delivery_id=e['delivery_id'],reason=e['last_error'],attempt_count=e['attempt_count'],receipt135_committed=True)
   owner.post('[CODEX → JARVIS] STOP: first new failure under composer/UUID policy; no further receipts or retries. Preserve exact incident, monitor-only. '+json.dumps(result));return
  auto={e['outcome']['_future']['source']['sequence']:e for e in later if e['state']=='DELIVERED' and e['attempt_count']==1 and e['outcome'].get('verification_method')==METHOD and e['outcome'].get('composer_sha256')==e['text_sha256'] and e['outcome'].get('observed_sha256') is None and e['outcome'].get('send_intent') is True and e['outcome'].get('send_count')==1 and e['outcome'].get('user_turn_uuid') and 'operator_receipt' not in e['outcome']}
  if 136 in auto and 137 in auto:
   proof=vm_ack(plan,after,'COMPOSER_POLICY_CURSOR_PROOF',137)
   result=record('LIVE_AUTOMATIC_DELIVERY_PROVEN',receipt135_committed=True,automatic_sequences=sorted(auto),vm_proof=proof,legacy_unchanged=True)
   owner.post('[CODEX → JARVIS / CHATGPT] LIVE automatic composer/UUID delivery proven; no rendered SHA claimed. '+json.dumps(result));return
  time.sleep(5)
 record('LOADED_ALIGNED_RECEIPT_COMMITTED_PROOF_PENDING',receipt135_committed=True)
 owner.post('[CODEX → JARVIS] Loaded/aligned new policy and135 receipt committed; waiting on actual136+ delivery proof, not claiming completion. No additional receipt/Send/retry.')

def run():
 import msvcrt
 plan=m.read_sealed(AREA/'plan.json');os.environ['PATH']=str(Path(plan['gh_path']).parent)+os.pathsep+os.environ.get('PATH','')
 with (AREA/'worker.lock').open('a+b') as lock:
  lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  committed=False;deployed=False
  try:
   if m.read_sealed(AREA/'state.json')['phase']!='ARMED':raise ValueError('one invocation already consumed')
   a,plan=validated();life=r.managed.lifecycle();proof=owner.owner.prove_independent_scheduler(life,Path(__file__))
   record('WAITING_FOR_CURRENT_TURN',**proof)
   until=time.monotonic()+1800
   while True:
    validated();h=r.managed.http()
    if life.process(a['tray']['pid'])!=a['tray'] or life.process(h['bridge_pid'])!=a['old']:raise ValueError('pinned tray/bridge changed')
    if owner.owner.terminal_idle(a,h):break
    if time.monotonic()>until:raise ValueError('terminal/outbox/idle not reached; no changes')
    time.sleep(3)
   operator=owner.gh(['repos/grxr-dev/codex-relay/issues/comments/'+str(receipt.COMMENT)]);receipt.authority(operator)
   raw=(AREA/'retained-135.jsonl').read_bytes();receipt.trace_proof(raw)
   with r.managed.exclusive_stopped(life,a):
    queue()
    # Source-only rollback before receipt commit; never rolls back queue history.
    r.transaction(lambda:m.install(r.BRIDGE,r.STAGE,AREA,True),lambda:m.save(r.RUNTIME/'inbox_future.json',plan['new_policy']),lambda:installed(plan),lambda:m.atomic(r.RUNTIME/'inbox_future.json',(AREA/'backup/future.json').read_bytes()),lambda:m.rollback(r.BRIDGE,AREA,plan,True))
    deployed=True
    q=queue()
    from inbox_future import source
    trusted=source(r.RUNTIME,plan['old_policy'],receipt.TARGET,q._entries[receipt.TARGET]['text'])
    if trusted!=plan['trusted_source']:raise ValueError('original seq135 provenance changed')
    m.atomic(AREA/'future-queue.before.json',q.path.read_bytes())
    result=receipt.reconcile(q,receipt.TARGET,receipt.FINGERPRINT,plan['old_binding_public'],plan['old_lane'],trusted,raw,operator,exclusive=True)
    committed=True;m.save(AREA/'receipt-result.json',m.sealed(result));installed(plan)
   record('INSTALLED_RECEIPT135_COMMITTED_WAITING_LOADED_BUILD',**result,new_identity=plan['new_binding']['identity'],new_seal=plan['new_policy']['seal'])
   alignment=owner.post('[CODEX → JARVIS] INSTALLED new composer/UUID policy and exact seq135 OPERATOR receipt COMMITTED (no resend). Original lane/cutoffs/recipient/epoch/HOLD and historical hashes unchanged. New binding '+plan['new_binding']['identity']+'; new lane seal '+plan['new_policy']['seal']+'; lane '+plan['new_policy']['lane_id']+'. Update ONLY existing activation/quarantine source identity/seal, no cursor edits, one writer. Reply [JARVIS] with JSON action=COMPOSER_POLICY_GATE_ALIGNED, in_reply_to=THIS comment ID, binding_identity, seal, lane_id, future_cursor>=134, historical_state_unchanged=true. Let existing worker advance naturally only against this source. New Windows claim gate REQUIRES loaded '+BUILD+'. Browser action if pending: Reload existing Jarvis Inbox V1 in about:debugging and refresh the bound ChatGPT tab ONCE; no manual Send. After136+137 automatically ACK, reply again to THIS comment with action=COMPOSER_POLICY_CURSOR_PROOF and actual cursor>136, same identity/seal/lane/history fields.')
   ready=wait_loaded(plan);record('NEW_BUILD_LOADED',receipt135_committed=True,observed_ms=ready['observed_ms'],alignment_request=alignment)
   ack=vm_ack(plan,alignment,'COMPOSER_POLICY_GATE_ALIGNED',134)
   record('LOADED_AND_VM_ALIGNED',receipt135_committed=True,vm_proof=ack)
   monitor(plan,alignment)
  except Exception as error:
   result=record('STOPPED',reason=str(error) if type(error) is ValueError else type(error).__name__,installed=deployed,receipt135_committed=committed,no_automatic_retry=True)
   try:owner.post('[CODEX → JARVIS / CHATGPT] Composer135 one-shot stopped; no retry/bulk receipt. Inspect exact installed/receipt status. '+json.dumps(result))
   except Exception:pass
  finally:
   try:owner.owner.scheduler("$s=New-Object -ComObject Schedule.Service;$s.Connect();$s.GetFolder([string][char]92).GetTask('"+TASK+"').Enabled=$false")
   except Exception:pass
   lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

def arm():
 if AREA.exists():raise ValueError('existing one-shot retained; never rearm')
 old=m.checked_binding(r.BRIDGE);cfg=json.loads((r.RUNTIME/'inbox_future.json').read_text());q=queue()
 receipt.scope(cfg['binding'],r.lane_public(cfg))
 operator=owner.gh(['repos/grxr-dev/codex-relay/issues/comments/'+str(receipt.COMMENT)]);receipt.authority(operator)
 raw=(r.RUNTIME/'inbox_verifier_incidents'/(receipt.sha(receipt.TARGET.encode())+'.jsonl')).read_bytes();receipt.trace_proof(raw)
 from inbox_future import source
 trusted=source(r.RUNTIME,cfg,receipt.TARGET,q._entries[receipt.TARGET]['text'])
 components={name:m.sha(r.STAGE/name) for name in old['components']}
 new=copy.deepcopy(old);new['components']=components;new['identity']=m.digest({k:v for k,v in new.items() if k!='identity'})
 policy=copy.deepcopy(cfg);policy['binding']={k:new[k] for k in cfg['binding']};policy['seal']=m.digest({k:v for k,v in policy.items() if k!='seal'})
 if {k:v for k,v in new.items() if k not in ('identity','components')}!={k:v for k,v in old.items() if k not in ('identity','components')} or {k:v for k,v in policy.items() if k not in ('binding','seal')}!={k:v for k,v in cfg.items() if k not in ('binding','seal')}:raise ValueError('immutable binding/lane fields changed')
 h=r.managed.http();active=h.get('active_async_request') or {}
 if h.get('turn_active') is not True or not active.get('codex_turn_id'):raise ValueError('exact active authorizing turn required')
 life=r.managed.lifecycle();proc=life.process(h['bridge_pid']);tray=life.process(json.loads((r.RUNTIME/'tray.json').read_text())['pid'])
 if proc['parent']!=tray['pid']:raise ValueError('original tray ownership required')
 pythonw=Path(sys.executable).with_name('pythonw.exe');gh_path=shutil.which('gh')
 if not pythonw.is_file() or not gh_path:raise ValueError('existing windowless runtime missing')
 AREA.mkdir();m.atomic(AREA/'retained-135.jsonl',raw)
 for name,want in old['components'].items():
  if m.sha(r.BRIDGE/name)!=want:raise ValueError('old source changed')
  m.atomic(AREA/'backup'/name,(r.BRIDGE/name).read_bytes())
 for name,src in [('binding.json','inbox_binding.json'),('future.json','inbox_future.json')]:m.atomic(AREA/'backup'/name,(r.RUNTIME/src).read_bytes())
 plan={'schema':'inbox-source-migration/1','authorization':'composer-proof policy + exactly135 owner receipt','old_binding_sha256':m.sha(r.RUNTIME/'inbox_binding.json'),'old_identity':old['identity'],'new_binding':new,'new_sources':components,'original_sources':old['components'],'protected':m.state_hashes(r.BRIDGE),'old_policy':cfg,'new_policy':policy,'old_binding_public':cfg['binding'],'old_lane':r.lane_public(cfg),'trusted_source':trusted,'future_queue_sha256':m.sha(q.path),'gh_path':gh_path}
 m.save(AREA/'plan.json',m.sealed(plan))
 files=[Path(__file__),Path(owner.__file__),Path(owner.owner.__file__),Path(r.__file__),Path(r.managed.__file__),Path(m.__file__),r.managed.LIFECYCLE,r.managed.PIPE,Path(__file__).with_name('receipt135.py'),KERNEL,AREA/'retained-135.jsonl',pythonw,Path(gh_path)]
 tools={str(p.resolve()):m.sha(p) for p in files};tools.update({str((r.STAGE/name).resolve()):want for name,want in components.items()})
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':proc,'tray':tray,'tools':tools,'migration_plan_sha256':m.sha(AREA/'plan.json')}
 m.save(AREA/'activation.json',m.sealed(a));record('ARMED',new_identity=new['identity'],new_seal=policy['seal'],no_effect_before_terminal=True)
 def ps(s):return str(s).replace("'","''")
 args=subprocess.list2cmdline([str(Path(__file__).resolve()),'run'])
 script=f"""$ErrorActionPreference='Stop';$s=New-Object -ComObject Schedule.Service;$s.Connect();$f=$s.GetFolder([string][char]92);$d=$s.NewTask(0)
$d.RegistrationInfo.Description='ONE post-terminal composer proof install +135 receipt, original tray owner, no Send'
$u=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;$d.Principal.UserId=$u;$d.Principal.LogonType=3;$d.Principal.RunLevel=0
$d.Settings.Enabled=$true;$d.Settings.AllowDemandStart=$true;$d.Settings.MultipleInstances=2;$d.Settings.DisallowStartIfOnBatteries=$false;$d.Settings.StopIfGoingOnBatteries=$false;$d.Settings.ExecutionTimeLimit='PT2H'
$a=$d.Actions.Create(0);$a.Path='{ps(pythonw)}';$a.Arguments='{ps(args)}';$a.WorkingDirectory='{ps(r.ROOT)}'
$t=$f.RegisterTaskDefinition('{TASK}',$d,2,$u,$null,3,$null);$i=$t.Run($null);Write-Output $i.InstanceGuid"""
 instance=owner.owner.scheduler(script)
 m.save(AREA/'registration.json',{'instance':instance,'task_name':TASK,'at':time.time()})
 until=time.monotonic()+20
 while time.monotonic()<until:
  state=m.read_sealed(AREA/'state.json')
  if state['phase']=='WAITING_FOR_CURRENT_TURN':print(json.dumps(state));return
  if state['phase']=='STOPPED':raise ValueError('one-shot stopped before effect: '+state['reason'])
  time.sleep(.5)
 raise ValueError('independent worker heartbeat unproven; never rearm')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('arm','run'));args=parser.parse_args()
 if args.action=='arm':arm()
 else:
  with (AREA/'worker-console.log').open('x',encoding='utf-8',buffering=1) as log:sys.stdout=log;sys.stderr=log;run()
