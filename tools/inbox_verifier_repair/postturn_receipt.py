"""One authorized scheduler invocation; receipt only after this turn is terminal.

Uses the existing Task Scheduler interactive-owner mechanism, managed tray idle
shutdown and bridge instance lock. No source install, browser control or Send.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import shutil
import finish_repair as r

AREA=r.RUNTIME/'inbox-seq133-postturn-110'
TASK='MuseInbox-Seq133-Receipt-110'


def record(phase,**details):
 value={'phase':phase,'at':time.time(),**details};r.m.save(AREA/'state.json',r.m.sealed(value));return value


def scheduler(script):
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=30,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 return p.stdout.strip()


def scheduler_metadata():
 return json.loads(scheduler("$ErrorActionPreference='Stop';$s=New-Object -ComObject Schedule.Service;$s.Connect();$t=$s.GetFolder([string][char]92).GetTask('"+TASK+"');@{path=$t.Definition.Actions.Item(1).Path;arguments=$t.Definition.Actions.Item(1).Arguments;logon=$t.Definition.Principal.LogonType;instances=@($t.GetInstances(0)|ForEach-Object{@{instance=$_.InstanceGuid;pid=$_.EnginePID;state=$_.State}})}|ConvertTo-Json -Depth 5 -Compress"))


def prove_independent_scheduler(life,script_path=None):
 r.managed.independent(life)
 until=time.monotonic()+10
 while not (AREA/'registration.json').exists() and time.monotonic()<until:time.sleep(.2)
 reg=json.loads((AREA/'registration.json').read_text(encoding='utf-8'))
 info=scheduler_metadata();expected=subprocess.list2cmdline([str(Path(script_path or __file__).resolve()),'run'])
 if Path(info['path'])!=Path(sys.executable).with_name('pythonw.exe') or info['arguments']!=expected or info['logon']!=3:raise ValueError('scheduled action identity mismatch')
 instances=[x for x in info['instances'] if x['instance'].lower()==reg['instance'].lower()]
 if len(instances)!=1 or instances[0]['state']!=4:raise ValueError('one running scheduled invocation required')
 related=set();current=life.process(os.getpid())
 for _ in range(24):
  related.update((current['pid'],current['parent']))
  if not current['parent']:break
  try:current=life.process(current['parent'])
  except RuntimeError:break
 if instances[0]['pid'] not in related:raise ValueError('scheduler engine ancestry not proven')
 return {'helper_pid':os.getpid(),'instance':reg['instance'],'scheduler_engine_pid':instances[0]['pid']}


def validated():
 a=r.m.read_sealed(AREA/'activation.json');r.managed.AREA=AREA;r.managed.verify_tools(a)
 plan=r.m.read_sealed(AREA/'plan.json');base=r.m.read_sealed(r.AREA/'plan.json')
 r.validate_installed(base)
 if plan['installed_identity']!=base['new_binding']['identity'] or plan['installed_seal']!=base['new_policy']['seal']:raise ValueError('installed identity changed')
 return a,plan,base


def terminal_idle(a,health):
 """No effect until exact current result is published and all active work ends."""
 try:r.managed.task_finished(a);r.managed.idle(health)
 except ValueError:return False
 return True


def wait_terminal(a,plan,life):
 until=time.monotonic()+1800
 while time.monotonic()<until:
  validated()
  health=r.managed.http()
  if life.process(a['tray']['pid'])!=a['tray'] or life.process(health['bridge_pid'])!=a['old']:raise ValueError('pinned bridge/tray process changed; no shutdown')
  if terminal_idle(a,health):return
  time.sleep(3)
 raise ValueError('idle deadline expired; no shutdown or receipt')


def run():
 import msvcrt
 plan=r.m.read_sealed(AREA/'plan.json')
 os.environ['PATH']=str(Path(plan['gh_path']).parent)+os.pathsep+os.environ.get('PATH','')
 with (AREA/'worker.lock').open('a+b') as lock:
  lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  try:
   initial=r.m.read_sealed(AREA/'state.json')
   if initial['phase']!='ARMED':raise ValueError('one invocation already used; no automatic retry')
   a,plan,base=validated();life=r.managed.lifecycle();proof=prove_independent_scheduler(life)
   record('WAITING_FOR_CURRENT_TURN',**proof,no_effect_before_terminal=True)
   wait_terminal(a,plan,life)
   # Gate alignment is an independently recorded control-channel action. It
   # changes no queue/cursor and cannot release later work while133 is held.
   ack=r.wait_vm_ack(base,plan['alignment_request_comment'])
   readiness=r.wait_probe(base)
   operator=r.github_record(r.receipt.COMMENT);r.receipt.authority(operator)
   incident=(r.AREA/'retained-133.jsonl').read_bytes();r.receipt.trace_proof(incident)
   # Exclusion also prevents a previously opened owner launcher from competing.
   with (r.AREA/'owner.lock').open('a+b') as owner:
    owner.seek(0);msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
    try:
     record('COMMITTING_ONCE',vm_alignment_comment=ack,historical_dom_gate=False)
     with r.managed.exclusive_stopped(life,a):
      r.validate_installed(base)
      if not r.checked_readiness(readiness,base,readiness['probe_id'],time.time()*1000):raise ValueError('fresh current readiness missing')
      sys.path.insert(0,str(r.BRIDGE));from inbox_future import source
      queue=r.queue_preflight(base)
      trusted=source(r.RUNTIME,base['new_policy'],r.receipt.TARGET,queue._entries[r.receipt.TARGET]['text'])
      if trusted!=base['trusted_source']:raise ValueError('trusted completion changed')
      r.m.atomic(AREA/'future-queue.before.json',queue.path.read_bytes())
      result=r.receipt.reconcile(queue,r.receipt.TARGET,r.receipt.FINGERPRINT,base['old_binding_public'],base['old_lane'],trusted,incident,operator,exclusive=True)
      r.protected(base)
      result.update(vm_alignment_comment=ack,current_content_readiness=True,historical_dom_required=False,
                    raw_model_availability_measured=False,source_reinstalled=False,new_send=False,cursor_modified=False)
      # The queue's embedded receipt is the atomic commit marker even if an
      # external audit write crashes. A second invocation fails fingerprint CAS.
      r.m.save(AREA/'receipt-result.json',r.m.sealed(result))
      r.m.save(r.AREA/'result.json',r.m.sealed(result))
     record('RECEIPT_COMMITTED',**result)
    finally:owner.seek(0);msvcrt.locking(owner.fileno(),msvcrt.LK_UNLCK,1)
   after=r.post('[CODEX → JARVIS / CHATGPT] #110 seq133 OPERATOR RECEIPT COMMITTED (not automatic browser proof). No resend, source install, cursor edit or historical queue mutation. Original tray resumes normally. Let existing worker progress naturally. Stop on the first new NEEDS_REVIEW; capture targeted trace, no further reconciliation. Reply with bare JSON action=VM_MODEL_DELIVERY_PROOF, in_reply_to=THIS comment ID, lane_id, seal, future_cursor, historical_state_unchanged=true.\n'+json.dumps(result))
   r.wait_delivery_proof(base,after)
   live=r.m.read_sealed(r.AREA/'live-validation.json')
   record('DELIVERED' if live['status']=='LIVE_AUTOMATIC_DELIVERY_PROVEN' else 'STOPPED_BEFORE_SUCCESS_PROOF',receipt_committed=True,validation=live)
  except Exception as error:
   state=record('FAILED_CLOSED',reason=str(error) if type(error) is ValueError else type(error).__name__,no_blind_retry=True)
   try:r.post('[CODEX → JARVIS / CHATGPT] #110 post-turn action STOPPED; no automatic retry or additional reconciliation. Inspect durable queue receipt before any action.\n'+json.dumps(state))
   except Exception:pass
  finally:
   # Disable this demand-only task after its single invocation; retain audit.
   try:scheduler("$s=New-Object -ComObject Schedule.Service;$s.Connect();$s.GetFolder([string][char]92).GetTask('"+TASK+"').Enabled=$false")
   except Exception:pass
   lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


def arm(comment):
 if (AREA/'plan.json').exists():raise ValueError('existing one-shot retained; never rearm')
 base=r.m.read_sealed(r.AREA/'plan.json');r.validate_installed(base)
 h=r.managed.http();active=h.get('active_async_request') or {}
 if h.get('turn_active') is not True or not active.get('codex_turn_id'):raise ValueError('exact active arming task required')
 life=r.managed.lifecycle();old=life.process(h['bridge_pid']);tray=life.process(json.loads((r.RUNTIME/'tray.json').read_text())['pid'])
 if old['parent']!=tray['pid']:raise ValueError('existing tray ownership required')
 pythonw=Path(sys.executable).with_name('pythonw.exe')
 if not pythonw.is_file():raise ValueError('installed pythonw missing')
 gh_path=shutil.which('gh')
 if not gh_path:raise ValueError('installed GitHub CLI missing')
 AREA.mkdir(parents=True,exist_ok=True)
 plan={'schema':'seq133-postturn-receipt/1','alignment_request_comment':comment,
       'installed_identity':base['new_binding']['identity'],'installed_seal':base['new_policy']['seal'],
       'current_request_id':active['request_id'],'current_turn_id':active['codex_turn_id'],
       'queue_fingerprint':r.receipt.FINGERPRINT,'no_source_install':True,'no_historical_dom_gate':True,'gh_path':gh_path}
 r.m.save(AREA/'plan.json',r.m.sealed(plan))
 paths=[Path(__file__).resolve(),Path(r.__file__).resolve(),Path(r.managed.__file__),Path(r.m.__file__),r.managed.LIFECYCLE,r.managed.PIPE,
        r.HERE/'receipt133.py',r.KERNEL,r.AREA/'plan.json',r.AREA/'retained-133.jsonl',pythonw,Path(gh_path)]
 tools={str(p.resolve()):r.m.sha(p) for p in paths};tools.update({str((r.BRIDGE/n).resolve()):v for n,v in base['new_sources'].items()})
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':old,'tray':tray,'tools':tools,'migration_plan_sha256':r.m.sha(AREA/'plan.json')}
 r.m.save(AREA/'activation.json',r.m.sealed(a));record('ARMED',no_effect_before_terminal=True)
 def ps(s):return str(s).replace("'","''")
 arguments=subprocess.list2cmdline([str(Path(__file__).resolve()),'run'])
 script=f"""$ErrorActionPreference='Stop';$s=New-Object -ComObject Schedule.Service;$s.Connect();$f=$s.GetFolder([string][char]92);$d=$s.NewTask(0)
$d.RegistrationInfo.Description='Owner-authorized #110 one pinned seq133 receipt after exact terminal/idle; no Send or source install'
$u=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;$d.Principal.UserId=$u;$d.Principal.LogonType=3;$d.Principal.RunLevel=0
$d.Settings.Enabled=$true;$d.Settings.AllowDemandStart=$true;$d.Settings.MultipleInstances=2;$d.Settings.DisallowStartIfOnBatteries=$false;$d.Settings.StopIfGoingOnBatteries=$false;$d.Settings.ExecutionTimeLimit='PT1H'
$a=$d.Actions.Create(0);$a.Path='{ps(pythonw)}';$a.Arguments='{ps(arguments)}';$a.WorkingDirectory='{ps(r.ROOT)}'
$t=$f.RegisterTaskDefinition('{TASK}',$d,2,$u,$null,3,$null);$i=$t.Run($null);Write-Output $i.InstanceGuid"""
 instance=scheduler(script)
 if not instance.startswith('{'):raise ValueError('scheduled instance identity unavailable')
 r.m.save(AREA/'registration.json',{'instance':instance,'task_name':TASK,'at':time.time()})
 until=time.monotonic()+20
 while time.monotonic()<until:
  state=r.m.read_sealed(AREA/'state.json')
  if state['phase']=='WAITING_FOR_CURRENT_TURN':print(json.dumps(state));return
  if state['phase']=='FAILED_CLOSED':raise ValueError('one-shot failed before effects: '+state['reason'])
  time.sleep(.5)
 raise ValueError('independent worker heartbeat not proven; inspect state, never rearm')


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['arm','run']);parser.add_argument('--alignment-comment',type=int);args=parser.parse_args()
 try:
  if args.action=='arm':
   if not args.alignment_comment:raise ValueError('explicit #45 alignment request required')
   arm(args.alignment_comment)
  else:
   with (AREA/'worker-console.log').open('x',encoding='utf-8',buffering=1) as log:
    before_out,before_err=sys.stdout,sys.stderr
    try:sys.stdout=log;sys.stderr=log;run()
    finally:sys.stdout=before_out;sys.stderr=before_err
 except Exception as error:
  # No payload, token or raw subprocess output in terminal/logs.
  message=str(error) if type(error) is ValueError else type(error).__name__
  print('STOP: '+message);sys.exit(1)
