"""One owner-invoked post-turn install; PREPARED is not live authorization."""
import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];BRIDGE=ROOT/'bridge';RUNTIME=BRIDGE/'.runtime'
sys.path.insert(0,str(HERE.parent/'inbox_exact_one'))
import seal_migration as m
import finish_once as managed
AREA=RUNTIME/'inbox-future-deploy';STAGE=HERE/'production'
BUILD='inbox-future-only-20261101-01'


def cutoffs(c):
 return (c.execute("SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name='completions'),0)").fetchone()[0],c.execute('SELECT COALESCE(MAX(rowid),0) FROM requests').fetchone()[0])
def policy(runtime,binding,state='PREPARED',connection=None):
 if connection is None:
  c=sqlite3.connect((runtime/'completions.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)
  try:completion,request=cutoffs(c)
  finally:c.close()
 else:completion,request=cutoffs(connection)
 v={'schema':'inbox-future-only/1','build':BUILD,'state':state,'lane_id':uuid.uuid4().hex,
    'binding':{k:binding[k] for k in ('schema','build','conversation_id','generation','epoch','delivery_policy','identity')},
    'completion_cutoff':completion,'request_cutoff':request,'legacy_queue_sha256':m.sha(runtime/'inbox_queue.json'),'legacy_hold_sha256':m.sha(runtime/'inbox_readiness_request.json')}
 return m.sealed(v)
def evidence():
 h=managed.http();b=m.checked_binding(BRIDGE);q=json.loads((RUNTIME/'inbox_queue.json').read_text(encoding='utf-8-sig'))
 if b['identity']!='89d9cfb3df159b1c5e332d0be127fa37bdacad8f072d5dcf5bab4e740967921d' or b['delivery_policy']!='HOLD' or q.get('exact_one',{}).get('state')!='FINISHED' or q['entries'][managed.TARGET]['state']!='DELIVERED' or q['entries'][managed.TARGET]['attempt_count']!=1:
  raise ValueError('exact deployed predecessor/finished95/HOLD required')
 if json.loads((RUNTIME/'inbox_native_recovery.json').read_text()) is not None or any(e['state']=='DELIVERING' for e in q['entries'].values()):raise ValueError('outstanding delivery; stop')
 return h,b
def prepare():
 if (AREA/'plan.json').exists():raise ValueError('existing plan retained; inspect, never overwrite')
 h,old=evidence();active=h.get('active_async_request') or {}
 if h.get('turn_active') is not True or not active.get('codex_turn_id'):raise ValueError('current turn identity required for post-turn gate')
 manifest=json.loads((HERE/'source-manifest.json').read_text());m.check_stage(STAGE,manifest);new=copy.deepcopy(old)
 new['components']={n:manifest['source_files_sha256'][n] for n in manifest['required_binding_components']};new['identity']=m.digest({k:v for k,v in new.items() if k!='identity'})
 if new['identity']!=manifest['derived_identity']:raise ValueError('reviewed derived seal mismatch')
 AREA.mkdir(parents=True)
 originals=manifest['expected_original_sources']
 for n,want in originals.items():
  actual=m.sha(BRIDGE/n) if (BRIDGE/n).exists() else None
  if actual!=want:raise ValueError('original source changed')
  if want is not None:m.atomic(AREA/'backup'/n,(BRIDGE/n).read_bytes())
 raw=(RUNTIME/'inbox_binding.json').read_bytes();m.atomic(AREA/'backup/binding.json',raw)
 plan={'schema':'inbox-source-migration/1','authorization':'current #98 disabled install only; senior6560156429; live activation requires separate owner authority',
       'old_binding_sha256':m.sha(RUNTIME/'inbox_binding.json'),'old_identity':old['identity'],'new_binding':new,'new_sources':manifest['source_files_sha256'],
       'original_sources':originals,'protected':m.state_hashes(BRIDGE)}
 m.save(AREA/'plan.json',m.sealed(plan))
 life=managed.lifecycle();oldproc=life.process(h['bridge_pid']);tray=life.process(json.loads((RUNTIME/'tray.json').read_text())['pid'])
 if oldproc['parent']!=tray['pid']:raise ValueError('managed tray ownership required')
 tools=[Path(__file__).resolve(),HERE/'source-manifest.json',Path(managed.__file__),Path(m.__file__),managed.LIFECYCLE,managed.PIPE]
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':oldproc,'tray':tray,'migration_plan_sha256':m.sha(AREA/'plan.json'),'tools':{str(p):m.sha(p) for p in tools}}
 m.save(AREA/'activation.json',m.sealed(a));print('Prepared inert post-turn source migration. No restart, mode activation or Send.')
def publish(status):
 note='PREPARED is DISABLED; keep VM activation absent. Separate senior live authorization remains required.' if status['state']=='PREPARED' else 'Windows ACTIVE owner-authorized checkpoint; Jarvis must require matching separately senior-authorized VM activation record. No synthetic requested automatically.'
 body='[CODEX -> CHATGPT / JARVIS] Windows FUTURE_ONLY owner readback (no synthetic requested):\n'+json.dumps(status,indent=2)+'\n'+note+' All legacy state remains held.'
 p=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/45/comments','--method','POST','--input','-'],input=json.dumps({'body':body}),text=True,capture_output=True)
 if p.returncode==0:print('Readback posted directly to #45: '+str(json.loads(p.stdout)['id']))
 else:print('Readback #45 post unavailable; local status retained, no activation.')
def finish(rollback=False):
 managed.AREA=AREA;a=m.read_sealed(AREA/'activation.json');managed.verify_tools(a);life=managed.lifecycle();managed.independent(life);managed.task_finished(a)
 p=m.read_sealed(AREA/'plan.json');j=m.read_sealed(AREA/'journal.json') if (AREA/'journal.json').exists() else None
 cfg=RUNTIME/'inbox_future.json'
 if rollback:
  if (RUNTIME/'inbox_future_queue.json').exists() or (cfg.exists() and json.loads(cfg.read_text()).get('state')!='PREPARED'):raise ValueError('ever-active/used future lane: no source rollback')
  if cfg.exists() and (not (AREA/'prepared-policy.json').exists() or json.loads(cfg.read_text())!=json.loads((AREA/'prepared-policy.json').read_text())):raise ValueError('prepared policy changed independently; preserve it')
  with managed.exclusive_stopped(life,a):
   if cfg.exists():cfg.unlink()
   m.rollback(BRIDGE,AREA,p,True)
  print('Source/config restored; no queue/history rollback.');return
 if not j or j['phase']!='COMPLETE':
  if cfg.exists():raise ValueError('unexpected existing future policy; no overwrite')
  with managed.exclusive_stopped(life,a):
   try:
    m.install(BRIDGE,STAGE,AREA,True)
    prepared=policy(RUNTIME,p['new_binding']);m.save(AREA/'prepared-policy.json',prepared);m.save(cfg,prepared)
   except Exception:
    if cfg.exists():cfg.unlink()
    m.rollback(BRIDGE,AREA,p,True);raise
 m.unchanged(BRIDGE,p)
 if json.loads(cfg.read_text())['state']!='PREPARED':raise ValueError('lane is already active; no reinstall, use status only')
 print('Installed PREPARED/DISABLED. Existing tray restarts; no Send/grant can occur.')
 print('If prompted by absence: Reload existing Firefox Inbox extension, then refresh NEW tab. Waiting for no-send readback only.')
 deadline=time.monotonic()+180;status=None
 while time.monotonic()<deadline:
  try:
   h=managed.http();status=None
   r=json.loads((RUNTIME/'inbox_binding_readiness.json').read_text());v=json.loads(cfg.read_text())
   if h['bridge_pid']==a['old']['pid'] or h.get('relay_ready') is not True or h.get('bridge_healthy') is not True or life.process(h['bridge_pid'])['parent']!=a['tray']['pid'] or r['binding_identity']!=p['new_binding']['identity'] or not 0<=time.time()*1000-r['observed_ms']<=60000 or not r['ready'] or r['content'].get('future_build')!=BUILD or r['content'].get('future_lane_seal')!=v['seal']:raise ValueError()
   m.unchanged(BRIDGE,p)
   status={'state':'PREPARED','build':BUILD,'binding':v['binding'],'lane_id':v['lane_id'],'seal':v['seal'],'completion_cutoff':v['completion_cutoff'],'request_cutoff':v['request_cutoff'],'bridge_pid':h['bridge_pid'],'fresh_unique_target_no_send_ready':True,'legacy_hashes_unchanged':True,'synthetic_sent':False}
   break
  except (OSError,ValueError,KeyError):time.sleep(2)
 if not status:raise ValueError('installed but no fresh loaded readiness; keep DISABLED. Reload existing add-on+refresh NEW tab; existing tray Restart Bridge only if idle and needed')
 m.save(AREA/'readback.json',status);publish(status);print(json.dumps(status))
def activate_policy(runtime,expected_seal,comment,readiness):
 # Called only by explicit local owner command AFTER a separate positive senior
 # authorization. No remote flag/endpoint can enable this lane.
 if type(comment) is not int or comment<=0:raise ValueError('explicit authorization reference required')
 sys.path.insert(0,str(BRIDGE));from inbox_future import config
 v=config(runtime)
 if v['state']!='PREPARED' or v['seal']!=expected_seal or (runtime/'inbox_future_queue.json').exists():raise ValueError('only unused prepared lane may activate once')
 r=readiness()
 if not r or not 0<=time.time()*1000-r['observed_ms']<=60000 or not r['ready'] or r['binding_identity']!=v['binding']['identity'] or r['content'].get('future_build')!=BUILD or r['content'].get('future_lane_seal')!=v['seal']:raise ValueError('fresh exact prepared browser/native readiness required')
 c=sqlite3.connect(runtime/'completions.sqlite3',timeout=3)
 try:
  c.execute('BEGIN IMMEDIATE')  # producers cannot create a pre-activation row between snapshot and publication
  if config(runtime)!=v:raise ValueError('prepared state changed')
  new=policy(runtime,v['binding'],'ACTIVE',c)
  audit={'authorization_comment':comment,'at':time.time(),'previous_seal':v['seal'],'active_policy':new}
  m.save(runtime/'inbox_future_activation.json',m.sealed(audit));m.save(runtime/'inbox_future.json',new);c.commit();return new
 except Exception:c.rollback();raise
 finally:c.close()


def verify_live_authorization(comment,prepared):
 if type(comment) is not int or comment<=0:raise ValueError('separate positive authorization comment required')
 r=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/comments/'+str(comment)],capture_output=True,text=True,timeout=15)
 if r.returncode:raise ValueError('authorization read unavailable; no activation')
 record=json.loads(r.stdout)
 if record.get('user',{}).get('login')!='grxr-dev' or not record.get('issue_url','').endswith('/issues/45'):raise ValueError('owner control-channel authorization required')
 try:body=json.loads(record['body'])
 except (ValueError,KeyError):raise ValueError('exact explicit activation envelope required; a general/disabled comment cannot activate') from None
 expected={'action':'ACTIVATE_FUTURE_ONLY','prepared_seal':prepared['seal'],'binding_identity':prepared['binding']['identity'],'conversation_id':prepared['binding']['conversation_id'],'historical_policy':'HOLD'}
 if body!=expected:raise ValueError('authorization scope/checkpoint mismatch; no activation')


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','finish','rollback','activate']);p.add_argument('--expected-seal');p.add_argument('--authorization-comment',type=int);args=p.parse_args()
 try:
  if args.action=='prepare':prepare()
  else:
   import msvcrt
   with (AREA/'owner.lock').open('a+b') as f:
    f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
    try:
     if args.action=='activate':
      managed.independent(managed.lifecycle());managed.idle(managed.http())
      prepared=json.loads((RUNTIME/'inbox_future.json').read_text());verify_live_authorization(args.authorization_comment,prepared)
      value=activate_policy(RUNTIME,args.expected_seal,args.authorization_comment,lambda:managed.http('/local/inbox/admin/recovery-once',admin=True)['readiness'])
      print(json.dumps(value));publish({'state':'ACTIVE_OWNER_AUTHORIZED','policy':value,'synthetic_sent':False})
     else:finish(args.action=='rollback')
    finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
 except Exception as e:
  print('STOP: '+(str(e) if type(e) is ValueError else type(e).__name__+'; fail-closed, no automatic retry'));sys.exit(1)
