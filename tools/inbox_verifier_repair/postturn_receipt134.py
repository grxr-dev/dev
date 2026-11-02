"""ONE authorized seq134 receipt, after this turn is terminal. No Send/source install.

Reuses #110 scheduler ancestry, terminal/outbox, original tray/idle shutdown,
instance lock and the pinned receipt kernel. No old-message DOM gate.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import postturn_receipt as owner
from receipt134 import receipt, KERNEL

r=owner.r
AREA=r.RUNTIME/'inbox-seq134-postturn'
TASK='MuseInbox-Seq134-Receipt-Once'
owner.AREA=AREA
owner.TASK=TASK
PROTECTED=('inbox_queue.json','inbox_readiness_request.json','inbox_native_recovery.json','inbox_binding.json','inbox_future.json')

def record(phase,**details):
 value={'phase':phase,'at':time.time(),**details};r.m.save(AREA/'state.json',r.m.sealed(value));return value

def gh(args,body=None):
 p=subprocess.run(['gh','api',*args],input=None if body is None else json.dumps({'body':body}),capture_output=True,encoding='utf-8',timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if p.returncode:raise ValueError('GitHub control channel unavailable')
 return json.loads(p.stdout)

def post(body):
 return gh(['repos/grxr-dev/codex-relay/issues/45/comments','--method','POST','--input','-'],body)['id']

def scope():
 sys.path.insert(0,str(r.BRIDGE))
 from inbox_binding import load,public
 from inbox_future import config,lane_public
 binding=public(load(r.RUNTIME));cfg=config(r.RUNTIME);lane=lane_public(cfg)
 receipt.scope(binding,lane)
 return binding,cfg,lane

def preflight():
 from inbox_queue import InboxQueue
 q=InboxQueue(r.RUNTIME/'inbox_future_queue.json')
 e=q._entries.get(receipt.TARGET)
 if q.fingerprint()!=receipt.FINGERPRINT or not e or e['state']!='NEEDS_REVIEW' or e['attempt_count']!=1 or e['text_sha256']!=receipt.TEXT_SHA or receipt.sha(e['text'].encode())!=receipt.TEXT_SHA or e['outcome'].get('send_intent') is not True or 'operator_receipt' in e['outcome']:
  raise ValueError('pinned seq134 queue/state changed; no receipt')
 if any(e['state']=='DELIVERING' for e in q._entries.values()) or json.loads((r.RUNTIME/'inbox_native_recovery.json').read_text()) is not None:raise ValueError('delivery/native ACK active; no receipt')
 return q

def validated():
 r.managed.AREA=AREA
 a=r.m.read_sealed(AREA/'activation.json');r.managed.verify_tools(a)
 plan=r.m.read_sealed(AREA/'plan.json')
 if any(r.m.sha(r.RUNTIME/n)!=v for n,v in plan['protected'].items()):raise ValueError('protected source/lane/history changed')
 scope();return a,plan

def monitor():
 deadline=time.monotonic()+600
 while time.monotonic()<deadline:
  value=json.loads((r.RUNTIME/'inbox_future_queue.json').read_text())
  entries=[e for e in value['entries'].values() if (e.get('outcome') or {}).get('_future',{}).get('source',{}).get('sequence',0)>=135]
  reviews=[e for e in entries if e['state'] in ('NEEDS_REVIEW','FAILED_PERMANENT')]
  delivered=[(e['outcome']['_future']['source']['sequence'],e['state'],e['attempt_count']) for e in entries if e['state']=='DELIVERED']
  if reviews:
   e=min(reviews,key=lambda e:e['outcome']['_future']['source']['sequence'])
   result=record('STOPPED_ON_NEW_REVIEW',receipt134_committed=True,sequence=e['outcome']['_future']['source']['sequence'],delivery_id=e['delivery_id'],state=e['state'],attempt_count=e['attempt_count'],reason=e['last_error'],new_receipt_or_resend=False)
   post('[CODEX → JARVIS / CHATGPT] Seq134 operator receipt committed; STOP on first later failed verification. No bulk attestations/retry. Please retain exact incident and monitor-only. '+json.dumps(result));return
  if any(seq==135 for seq,_,_ in delivered):
   result=record('SEQ135_AUTOMATIC_DELIVERED',receipt134_committed=True,delivered=delivered)
   post('[CODEX → JARVIS / CHATGPT] Read-only Windows proof: seq135 automatically DELIVERED after seq134 operator receipt. Please report actual VM future cursor and historical hashes; no manual cursor change. '+json.dumps(result));return
  time.sleep(5)
 record('RECEIPT_COMMITTED_WORKER_PROOF_PENDING',receipt134_committed=True)
 post('[CODEX → JARVIS / CHATGPT] Seq134 receipt committed; read-only worker proof timed out. No additional receipt/Send/retry. Please report actual future cursor and next entry state.')

def run():
 import msvcrt
 plan=r.m.read_sealed(AREA/'plan.json');os.environ['PATH']=str(Path(plan['gh_path']).parent)+os.pathsep+os.environ.get('PATH','')
 with (AREA/'worker.lock').open('a+b') as lock:
  lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  committed=False
  try:
   if r.m.read_sealed(AREA/'state.json')['phase']!='ARMED':raise ValueError('one invocation already consumed')
   a,plan=validated();life=r.managed.lifecycle();proof=owner.prove_independent_scheduler(life,Path(__file__))
   record('WAITING_FOR_CURRENT_TURN',**proof,no_effect_before_terminal=True)
   until=time.monotonic()+1800
   while True:
    validated();health=r.managed.http()
    if life.process(a['tray']['pid'])!=a['tray'] or life.process(health['bridge_pid'])!=a['old']:raise ValueError('pinned tray/bridge identity changed')
    if owner.terminal_idle(a,health):break
    if time.monotonic()>until:raise ValueError('terminal/idle deadline expired; no receipt')
    time.sleep(3)
   operator=gh(['repos/grxr-dev/codex-relay/issues/comments/'+str(receipt.COMMENT)])
   receipt.authority(operator);raw=(AREA/'retained-134.jsonl').read_bytes();receipt.trace_proof(raw)
   # Original tray gracefully shuts down ONLY after published terminal + idle.
   # Existing instance byte lock excludes every online queue owner.
   with r.managed.exclusive_stopped(life,a):
    validated();binding,cfg,lane=scope();q=preflight()
    from inbox_future import source
    trusted=source(r.RUNTIME,cfg,receipt.TARGET,q._entries[receipt.TARGET]['text'])
    if trusted!=plan['trusted_source']:raise ValueError('trusted completion changed')
    r.m.atomic(AREA/'future-queue.before.json',q.path.read_bytes())
    result=receipt.reconcile(q,receipt.TARGET,receipt.FINGERPRINT,binding,lane,trusted,raw,operator,exclusive=True)
    committed=True;validated()
    r.m.save(AREA/'receipt-result.json',r.m.sealed(result))
   record('RECEIPT_COMMITTED',**result)
   post('[CODEX → JARVIS / CHATGPT] Seq134 OPERATOR-ATTESTED RECEIPT COMMITTED under original managed owner/queue locks; not an automatic browser ACK. ID/history/failed evidence/attempt1 preserved. No Send, permit, rearm, cursor, source/seal/extension/VM change. Original tray resumes. Existing future_worker may advance naturally; stop on first new NEEDS_REVIEW, no bulk receipts. Please ACK actual VM cursor and seq135 result. '+json.dumps(result))
   monitor()
  except Exception as error:
   result=record('FAILED_CLOSED',reason=str(error) if type(error) is ValueError else type(error).__name__,receipt134_committed=committed,no_automatic_retry=True)
   try:post('[CODEX → JARVIS / CHATGPT] One-shot seq134 owner action stopped; no retry. Inspect atomic receipt before any further action. '+json.dumps(result))
   except Exception:pass
  finally:
   try:owner.scheduler("$s=New-Object -ComObject Schedule.Service;$s.Connect();$s.GetFolder([string][char]92).GetTask('"+TASK+"').Enabled=$false")
   except Exception:pass
   lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)

def arm():
 if (AREA/'plan.json').exists():raise ValueError('existing one-shot retained; never rearm')
 binding,cfg,lane=scope();q=preflight()
 operator=gh(['repos/grxr-dev/codex-relay/issues/comments/'+str(receipt.COMMENT)]);receipt.authority(operator)
 raw=(r.RUNTIME/'inbox_verifier_incidents'/(receipt.sha(receipt.TARGET.encode())+'.jsonl')).read_bytes();receipt.trace_proof(raw)
 from inbox_future import source
 trusted=source(r.RUNTIME,cfg,receipt.TARGET,q._entries[receipt.TARGET]['text'])
 health=r.managed.http();active=health.get('active_async_request') or {}
 if health.get('turn_active') is not True or not active.get('codex_turn_id'):raise ValueError('exact active turn required for post-terminal authorization')
 life=r.managed.lifecycle();old=life.process(health['bridge_pid']);tray=life.process(json.loads((r.RUNTIME/'tray.json').read_text())['pid'])
 if old['parent']!=tray['pid']:raise ValueError('original tray ownership required')
 pythonw=Path(sys.executable).with_name('pythonw.exe');gh_path=shutil.which('gh')
 if not pythonw.is_file() or not gh_path:raise ValueError('existing windowless Python/GitHub CLI missing')
 AREA.mkdir(parents=True,exist_ok=False)
 r.m.atomic(AREA/'retained-134.jsonl',raw)
 plan={'schema':'seq134-postterminal-receipt/1','authorization':'current owner task; #45/6565241702','trusted_source':trusted,'queue_fingerprint':receipt.FINGERPRINT,'protected':{n:r.m.sha(r.RUNTIME/n) for n in PROTECTED},'gh_path':gh_path,'source_install':False,'send':False}
 r.m.save(AREA/'plan.json',r.m.sealed(plan))
 paths=[Path(__file__).resolve(),Path(owner.__file__),Path(r.__file__),Path(r.managed.__file__),Path(r.m.__file__),r.managed.LIFECYCLE,r.managed.PIPE,Path(__file__).with_name('receipt134.py'),KERNEL,AREA/'retained-134.jsonl',pythonw,Path(gh_path)]
 tools={str(p.resolve()):r.m.sha(p) for p in paths};tools.update({str((r.BRIDGE/n).resolve()):v for n,v in json.loads((r.RUNTIME/'inbox_binding.json').read_text())['components'].items()})
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':old,'tray':tray,'tools':tools,'migration_plan_sha256':r.m.sha(AREA/'plan.json')}
 r.m.save(AREA/'activation.json',r.m.sealed(a));record('ARMED',no_effect_before_terminal=True)
 def ps(s):return str(s).replace("'","''")
 arguments=subprocess.list2cmdline([str(Path(__file__).resolve()),'run'])
 script=f"""$ErrorActionPreference='Stop';$s=New-Object -ComObject Schedule.Service;$s.Connect();$f=$s.GetFolder([string][char]92);$d=$s.NewTask(0)
$d.RegistrationInfo.Description='ONE seq134 operator receipt after exact terminal/outbox/idle; no Send/install'
$u=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;$d.Principal.UserId=$u;$d.Principal.LogonType=3;$d.Principal.RunLevel=0
$d.Settings.Enabled=$true;$d.Settings.AllowDemandStart=$true;$d.Settings.MultipleInstances=2;$d.Settings.DisallowStartIfOnBatteries=$false;$d.Settings.StopIfGoingOnBatteries=$false;$d.Settings.ExecutionTimeLimit='PT1H'
$a=$d.Actions.Create(0);$a.Path='{ps(pythonw)}';$a.Arguments='{ps(arguments)}';$a.WorkingDirectory='{ps(r.ROOT)}'
$t=$f.RegisterTaskDefinition('{TASK}',$d,2,$u,$null,3,$null);$i=$t.Run($null);Write-Output $i.InstanceGuid"""
 instance=owner.scheduler(script)
 if not instance.startswith('{'):raise ValueError('scheduler instance identity unavailable')
 r.m.save(AREA/'registration.json',{'instance':instance,'task_name':TASK,'at':time.time()})
 until=time.monotonic()+20
 while time.monotonic()<until:
  state=r.m.read_sealed(AREA/'state.json')
  if state['phase']=='WAITING_FOR_CURRENT_TURN':print(json.dumps(state));return
  if state['phase']=='FAILED_CLOSED':raise ValueError('one-shot failed before effect: '+state['reason'])
  time.sleep(.5)
 raise ValueError('worker heartbeat unavailable; inspect state, never rearm')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('arm','run'));args=parser.parse_args()
 if args.action=='arm':arm()
 else:
  with (AREA/'worker-console.log').open('x',encoding='utf-8',buffering=1) as log:
   sys.stdout=log;sys.stderr=log;run()
