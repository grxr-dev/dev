"""Explicit owner post-turn launcher, never scheduled or detached by Codex."""
import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.request
import seal_migration as migration

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];BRIDGE=ROOT/'bridge';RUNTIME=BRIDGE/'.runtime'
AREA=RUNTIME/'inbox-seal-96';STAGE=HERE/'production'
LIFECYCLE=HERE.parent/'relay_reliability/post_turn_activation.py'
PIPE=RUNTIME/'post-turn-activation/managed_pipe.exe'
BUILD='inbox-exact-one-20261101-01'
TARGET='middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878'
TEXT='1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651'


def lifecycle():
 spec=importlib.util.spec_from_file_location('existing_idle_lifecycle',LIFECYCLE)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def http(path='/health',body=None,admin=False):
 headers={'X-Jarvis-Local':'1'}
 if admin:headers['X-Jarvis-Admin']=(RUNTIME/'inbox_recovery_admin.token').read_text().strip()
 if body is not None:headers['Content-Type']='application/json'
 port=18741 if path.startswith('/local/') else 8766
 req=urllib.request.Request('http://127.0.0.1:'+str(port)+path,
     data=None if body is None else migration.canonical(body).encode(),headers=headers)
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=5) as r:raw=r.read(262145)
 if len(raw)>262144:raise ValueError('response bound exceeded')
 return json.loads(raw)
def exact_unattempted():
 q=json.loads((RUNTIME/'inbox_queue.json').read_text(encoding='utf-8-sig'));e=q['entries'][TARGET]
 if q.get('exact_one') is not None or e['state']!='QUEUED' or e['attempt_count']!=0 or e['text_sha256']!=TEXT or migration.hashlib.sha256(e['text'].encode()).hexdigest()!=TEXT:
  raise ValueError('test item/grant changed; no second authorization')
 return q
def task_finished(a):
 db=sqlite3.connect((RUNTIME/'completions.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)
 try:
  row=db.execute('SELECT state,terminal_at,codex_turn_id FROM requests WHERE request_id=?',(a['request_id'],)).fetchone()
  active=db.execute('SELECT count(*) FROM requests WHERE terminal_at IS NULL').fetchone()[0]
  pending=db.execute('SELECT count(*) FROM pending').fetchone()[0]
  out=db.execute('SELECT state,comment_id FROM github_outbox WHERE request_id=?',(a['request_id'],)).fetchall()
  if not row or row[0]!='COMPLETED' or not row[1] or row[2]!=a['turn_id'] or active or pending or not out or any(r[0]!='CLOSED' or not r[1] for r in out):
   raise ValueError('current task/result publication not terminal and idle; no shutdown')
 finally:db.close()
def idle(h):
 if h.get('turn_active') is not False or h.get('active_async_request') is not None or h.get('maintenance_active') or h.get('approval_pending') or h.get('human_review_required') or h.get('relay_ready') is not True:
  raise ValueError('bridge not unambiguously idle; no shutdown')
def independent(life):
 current=life.process(os.getpid())
 for _ in range(24):
  if Path(current['image']).name.lower()=='codex.exe':
   raise ValueError('launch from owner desktop after the task, never from the bridge/Codex process tree')
  if not current['parent']:return
  try:current=life.process(current['parent'])
  except RuntimeError:return
 raise ValueError('independent owner process ancestry not proven')
def activation_plan():
 return migration.read_sealed(AREA/'activation.json')
def verify_tools(a):
 for name,want in a['tools'].items():
  if migration.sha(Path(name))!=want:raise ValueError('reviewed installer/lifecycle changed')
 if migration.sha(AREA/'plan.json')!=a['migration_plan_sha256']:raise ValueError('prepared migration plan changed')


@contextlib.contextmanager
def instance_lock():
 import msvcrt
 f=(RUNTIME/'instance.lock').open('a+b');f.seek(0)
 try:
  msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
  try:yield
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
 finally:f.close()


def mark_arm(path,value):
 # Exclusive durable invocation audit: concurrent/restarted owner commands never
 # repeat an uncertain HTTP arm, even if the reply or process is lost.
 with path.open('xb') as f:
  f.write(migration.canonical(migration.sealed(value)).encode());f.flush();os.fsync(f.fileno())


@contextlib.contextmanager
def exclusive_stopped(life,a):
 """Managed if_idle rejects races; no force, process termination or new tray."""
 verify_tools(a);task_finished(a);independent(life)
 health=http();old=life.process(health['bridge_pid']);tray=life.process(a['tray']['pid'])
 if tray!=a['tray'] or old['parent']!=tray['pid']:raise ValueError('original tray ownership changed')
 for _ in range(3):idle(http());task_finished(a);time.sleep(1)
 # Recheck exact PID/start before sending the existing reviewed managed command.
 if life.process(old['pid'])!=old:raise ValueError('bridge identity changed before shutdown')
 args=[str(PIPE),'probe',str(tray['pid']),str(old['pid']),str(tray['ticks']),str(old['ticks']),'-']
 p=subprocess.run(args,capture_output=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if p.returncode:raise ValueError('managed pipe probe failed; no shutdown')
 channel=json.loads(p.stdout)['pipe_sha256'];idle(http());task_finished(a)
 args[1]='shutdown-if-idle';args[-1]=channel
 p=subprocess.run(args,capture_output=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if p.returncode:raise ValueError('managed idle shutdown unconfirmed; no file install')
 deadline=time.monotonic()+30
 while not life.process_exited(old['pid'],old['ticks']):
  if time.monotonic()>deadline:raise ValueError('owned process did not exit; no force, no install')
  time.sleep(.1)
 # This is the SAME lock the managed bridge takes before opening any state.
 # If a tray restart wins the race, lock acquisition fails and no file is touched.
 with instance_lock():yield


def prepare():
 life=lifecycle();h=http();active=h.get('active_async_request') or {}
 if h.get('bridge_pid')!=464 or h.get('turn_active') is not True or not active.get('request_id') or not active.get('codex_turn_id'):
  raise ValueError('expected current bridge-owned turn identity missing')
 exact_unattempted()
 manifest=json.loads((HERE/'source-manifest.json').read_text())
 plan=migration.prepare(BRIDGE,STAGE,manifest,AREA)
 tray_record=json.loads((RUNTIME/'tray.json').read_text());tray=life.process(tray_record['pid']);old=life.process(464)
 if tray_record['bridge_pid']!=464 or old['parent']!=tray['pid']:raise ValueError('managed tray ownership not proven')
 tools=[Path(__file__).resolve(),HERE/'seal_migration.py',LIFECYCLE,PIPE,HERE/'source-manifest.json']
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':old,'tray':tray,
    'migration_plan_sha256':migration.sha(AREA/'plan.json'),'tools':{str(p):migration.sha(p) for p in tools}}
 migration.save(AREA/'activation.json',migration.sealed(a))
 print('Prepared only. No shutdown, deployment, grant or Send. Run Finish Exact One.cmd from the desktop AFTER this result is published.')


def finish(rollback=False):
 life=lifecycle();a=activation_plan();verify_tools(a);independent(life);task_finished(a)
 if (AREA/'arm-invocation.json').exists():
  raise ValueError('one owner arm invocation already recorded; no retry/rollback. Inspect attempt-result.json or exact-one status, never resend')
 journal=migration.read_sealed(AREA/'journal.json') if (AREA/'journal.json').exists() else None
 if rollback:
  try:http()
  except OSError:
   # A crash during a multi-file install may prevent imports/startup. The SAME
   # bridge lock proves no active queue owner exists; no process is terminated.
   with instance_lock():migration.rollback(BRIDGE,AREA,migration.read_sealed(AREA/'plan.json'),True)
   print('Offline source/config rollback verified; queue/history untouched. Existing tray Restart Bridge while idle.');return
 if rollback or not journal or journal['phase']!='COMPLETE':
  with exclusive_stopped(life,a):
   if rollback:
    migration.rollback(BRIDGE,AREA,migration.read_sealed(AREA/'plan.json'),True)
   else:migration.install(BRIDGE,STAGE,AREA,True)
 if rollback:
  print('Source/config rollback complete; queue/history untouched. Existing tray may restart. No grant or Send.');return
 plan=migration.read_sealed(AREA/'plan.json');migration.unchanged(BRIDGE,plan)
 print('Source/seal installed. Waiting for existing tray to restart the coherent bundle; no new tray/token.')
 deadline=time.monotonic()+120
 while True:
  try:
   h=http();cap=http('/local/inbox/capabilities')
   if h['bridge_pid']==a['old']['pid'] or life.process(h['bridge_pid'])['parent']!=a['tray']['pid'] or cap['pid']!=h['bridge_pid'] or cap.get('exact_one_build')!=BUILD:raise ValueError()
   idle(h)
   status=http('/local/inbox/admin/exact-one',admin=True)
   if status['binding']!={k:plan['new_binding'][k] for k in ('schema','build','conversation_id','generation','epoch','delivery_policy','identity')} or status['loaded_source_identity']!=migration.digest(plan['new_binding']['components']):raise ValueError()
   break
  except (OSError,ValueError,KeyError):
   if time.monotonic()>deadline:raise ValueError('coherent bridge not live; no grant. Use existing tray Restart Bridge while idle, then rerun this command')
   time.sleep(2)
 exact_unattempted()
 # Only no-send diagnostic state is written; stale receipts cannot satisfy this nonce.
 probe={'probe_id':migration.uuid.uuid4().hex,'binding_identity':plan['new_binding']['identity']}
 migration.save(RUNTIME/'inbox_binding_probe.json',probe)
 print('If needed: Firefox about:debugging#/runtime/this-firefox > Reload EXISTING Jarvis Inbox V1, then refresh NEW ChatGPT tab. No manual Send.')
 print('Waiting up to 180 seconds for fresh exact-one native/background/content readiness; grant remains absent.')
 deadline=time.monotonic()+180
 last_probe=time.monotonic()
 while True:
  try:
   r=json.loads((RUNTIME/'inbox_binding_readiness.json').read_text())
   if r['probe_id']!=probe['probe_id'] or r['binding_identity']!=probe['binding_identity'] or not 0<=time.time()*1000-r['observed_ms']<=60000 or r.get('ready') is not True or r['content'].get('one_build')!=BUILD:raise ValueError()
   # The actual server independently validates all uniqueness/URL/composer flags.
   break
  except (OSError,ValueError,KeyError):
   if time.monotonic()>deadline:raise ValueError('no fresh coherent readiness; nothing armed. Complete the single Reload/refresh step and rerun command')
   if time.monotonic()-last_probe>=5:
    probe={'probe_id':migration.uuid.uuid4().hex,'binding_identity':plan['new_binding']['identity']}
    migration.save(RUNTIME/'inbox_binding_probe.json',probe);last_probe=time.monotonic()
   time.sleep(1)
 migration.unchanged(BRIDGE,plan);exact_unattempted();idle(http())
 status=http('/local/inbox/admin/exact-one',admin=True)
 if status['grant'] is not None:raise ValueError('grant exists; never rearm')
 # Exactly ONE HTTP arm invocation. Uncertain reply is never retried.
 mark_arm(AREA/'arm-invocation.json',{'at':time.time(),'delivery_id':TARGET,'queue_fingerprint':status['queue_fingerprint'],'migration_plan_sha256':migration.digest(plan)})
 result=http('/local/inbox/admin/exact-one',{'delivery_id':TARGET,'text_sha256':TEXT,
   'binding_identity':probe['binding_identity'],'queue_fingerprint':status['queue_fingerprint'],'expires_in':120},admin=True)
 print('Exact existing item armed once. Monitoring only; no retries or second authorization.')
 deadline=time.monotonic()+160
 while True:
  q=json.loads((RUNTIME/'inbox_queue.json').read_text(encoding='utf-8-sig'));e=q['entries'][TARGET]
  grant=q.get('exact_one') or {}
  if e['state'] in ('DELIVERED','NEEDS_REVIEW','FAILED_PERMANENT') or grant.get('state') in ('EXPIRED','REVOKED') or time.monotonic()>deadline:
   unchanged_history=migration.history_digest(q)==plan['history_sha256']
   unchanged_hold=migration.sha(RUNTIME/'inbox_readiness_request.json')==plan['protected']['inbox_readiness_request.json']
   summary={'delivery_id':TARGET,'state':e['state'],'attempt_count':e['attempt_count'],
     'grant_state':grant.get('state'),'backend_delivery_verified':e['state']=='DELIVERED',
     'history_unchanged':unchanged_history,'historical_hold_unchanged':unchanged_hold,
     'senior_nonce_receipt_confirmation':'NOT_OBSERVED_BY_THIS_LAUNCHER'}
   migration.save(AREA/'attempt-result.json',summary);print(json.dumps(summary));return
  time.sleep(1)


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','finish','rollback']);a=p.parse_args()
 try:
  if a.action=='prepare':prepare()
  else:
   import msvcrt
   with (AREA/'owner.lock').open('a+b') as lock:
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    try:finish(a.action=='rollback')
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
 except Exception as error:
  # Fixed local errors are safe; network/provider exception text is not.
  message=str(error) if type(error) is ValueError else type(error).__name__+'; stopped fail-closed, do not resend or retry an arm'
  print('STOP: '+message);sys.exit(1)
