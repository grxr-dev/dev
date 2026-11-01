"""Single foreground owner finish; never schedule or run from an active Codex turn."""
import argparse
import copy
import datetime
import json
from pathlib import Path
import subprocess
import re
import sys
import time
import uuid
from urllib.parse import quote, urlsplit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];BRIDGE=ROOT/'bridge';RUNTIME=BRIDGE/'.runtime'
AREA=RUNTIME/'inbox-verifier-repair';STAGE=HERE.parent/'inbox_future/production'
sys.path.insert(0,str(HERE.parent/'inbox_exact_one'))
import seal_migration as m
import finish_once as managed
from receipt133 import receipt, KERNEL
PROOF_BUILD='inbox-raw-user-proof-20261101-01'
PROTECTED=('inbox_queue.json','inbox_native_recovery.json','inbox_readiness_request.json')


def lane_public(v):
 return {k:v[k] for k in ('schema','build','state','lane_id','binding','completion_cutoff','request_cutoff','seal')}


def derive(old_binding,old_policy,components):
 if m.digest({k:v for k,v in old_binding.items() if k!='identity'})!=old_binding['identity'] or m.digest({k:v for k,v in old_policy.items() if k!='seal'})!=old_policy['seal']:
  raise ValueError('old source/policy seal mismatch')
 old_public={k:old_binding[k] for k in ('schema','build','conversation_id','generation','epoch','delivery_policy','identity')}
 receipt.scope(old_public,lane_public(old_policy))
 if set(components)!=set(old_binding['components']):raise ValueError('no component/permission expansion allowed')
 new=copy.deepcopy(old_binding);new['components']=components
 new['identity']=m.digest({k:v for k,v in new.items() if k!='identity'})
 policy=copy.deepcopy(old_policy);policy['binding']={k:new[k] for k in old_public}
 policy['seal']=m.digest({k:v for k,v in policy.items() if k!='seal'})
 if {k:v for k,v in new.items() if k not in ('components','identity')}!={k:v for k,v in old_binding.items() if k not in ('components','identity')} or {k:v for k,v in policy.items() if k not in ('binding','seal')}!={k:v for k,v in old_policy.items() if k not in ('binding','seal')}:
  raise ValueError('immutable recipient/lane/cutoffs/HOLD changed')
 return new,policy


def transaction(install,write_policy,validate,restore_policy,restore_sources):
 try:install();write_policy();validate()
 except Exception:
  restore_policy();restore_sources();raise


def github_record(comment):
 p=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/comments/'+str(comment)],capture_output=True,text=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if p.returncode:raise ValueError('GitHub authority unavailable; no mutation')
 return json.loads(p.stdout)


def post(body):
 p=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/45/comments','--method','POST','--input','-'],input=json.dumps({'body':body}),capture_output=True,text=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if p.returncode:raise ValueError('control-channel status could not be posted; stop before receipt')
 value=json.loads(p.stdout);print('Posted #45 '+str(value['id']));return value['id']


def incident():
 return RUNTIME/'inbox_verifier_incidents'/(receipt.sha(receipt.TARGET.encode())+'.jsonl')


def protected(plan):
 if m.state_hashes(BRIDGE)!=plan['protected']:raise ValueError('historical/native/HOLD state changed')


def queue_preflight(plan=None):
 raw=(RUNTIME/'inbox_future_queue.json').read_bytes();value=json.loads(raw)
 if set(value)!={'version','entries'} or any(e['state']=='DELIVERING' for e in value['entries'].values()) or json.loads((RUNTIME/'inbox_native_recovery.json').read_text(encoding='utf-8')) is not None:
  raise ValueError('active/uncertain native delivery or unexpected queue schema')
 sys.path.insert(0,str(BRIDGE));from inbox_queue import InboxQueue
 q=InboxQueue(RUNTIME/'inbox_future_queue.json')
 if q.fingerprint()!=receipt.FINGERPRINT or (plan and m.sha(q.path)!=plan['future_queue_sha256']):raise ValueError('pinned future queue changed/reconciled; no replay')
 return q


def prepare():
 if (AREA/'plan.json').exists():raise ValueError('existing prepared plan; never overwrite')
 old=m.checked_binding(BRIDGE);cfg=json.loads((RUNTIME/'inbox_future.json').read_text(encoding='utf-8'))
 q=queue_preflight();authority=github_record(receipt.COMMENT);receipt.authority(authority);receipt.trace_proof(incident().read_bytes())
 components={name:m.sha(STAGE/name) for name in old['components']}
 new,policy=derive(old,cfg,components)
 # Capture actual trusted ledger source without publishing/claiming a delivery.
 from inbox_future import source
 trusted=source(RUNTIME,cfg,receipt.TARGET,q._entries[receipt.TARGET]['text'])
 if q._entries[receipt.TARGET]['outcome']['_future']['source']!=trusted:raise ValueError('trusted source mismatch')
 h=managed.http();active=h.get('active_async_request') or {}
 if h.get('turn_active') is not True or not active.get('codex_turn_id'):raise ValueError('current owned turn required for inert preparation')
 life=managed.lifecycle();oldproc=life.process(h['bridge_pid']);tray=life.process(json.loads((RUNTIME/'tray.json').read_text())['pid'])
 if oldproc['parent']!=tray['pid']:raise ValueError('existing managed tray required')
 AREA.mkdir(parents=True,exist_ok=True)
 for n,want in old['components'].items():
  if m.sha(BRIDGE/n)!=want:raise ValueError('original component changed')
  m.atomic(AREA/'backup'/n,(BRIDGE/n).read_bytes())
 m.atomic(AREA/'backup/binding.json',(RUNTIME/'inbox_binding.json').read_bytes())
 m.atomic(AREA/'backup/future.json',(RUNTIME/'inbox_future.json').read_bytes())
 m.atomic(AREA/'retained-133.jsonl',incident().read_bytes())
 plan={'schema':'inbox-source-migration/1','authorization':'owner root-fix task; receipt #45/6561830626; no Send133',
       'old_binding_sha256':m.sha(RUNTIME/'inbox_binding.json'),'old_identity':old['identity'],
       'new_binding':new,'new_sources':components,'original_sources':old['components'],'protected':m.state_hashes(BRIDGE),
       'old_policy':cfg,'new_policy':policy,'future_queue_sha256':m.sha(q.path),'trusted_source':trusted,
       'old_binding_public':{k:old[k] for k in cfg['binding']},'old_lane':lane_public(cfg)}
 m.save(AREA/'plan.json',m.sealed(plan))
 tools=[Path(__file__),HERE/'receipt133.py',KERNEL,Path(managed.__file__),Path(m.__file__),managed.LIFECYCLE,managed.PIPE]
 pinned={str(p.resolve()):m.sha(p) for p in tools};pinned.update({str((STAGE/n).resolve()):v for n,v in components.items()})
 a={'request_id':active['request_id'],'turn_id':active['codex_turn_id'],'old':oldproc,'tray':tray,'tools':pinned,'migration_plan_sha256':m.sha(AREA/'plan.json')}
 m.save(AREA/'activation.json',m.sealed(a))
 print(json.dumps({'prepared_only':True,'old_identity':old['identity'],'new_identity':new['identity'],'old_seal':cfg['seal'],'new_seal':policy['seal'],'lane_id':policy['lane_id'],'cutoffs':[policy['completion_cutoff'],policy['request_cutoff']],'no_source_queue_cursor_or_send_changes':True}))


def validate_installed(plan):
 if m.checked_binding(BRIDGE)!=plan['new_binding'] or json.loads((RUNTIME/'inbox_future.json').read_text(encoding='utf-8'))!=plan['new_policy']:raise ValueError('coherent installed source/binding/policy required')
 protected(plan);queue_preflight(plan)


def checked_readiness(value,plan,probe,now_ms):
 """Loaded current content readiness; never require a historical DOM node."""
 c=value.get('content',{})
 if value.get('probe_id')!=probe:return False
 if not value.get('ready') or value.get('match_count')!=1 or c.get('proof_build')!=PROOF_BUILD or c.get('future_lane_seal')!=plan['new_policy']['seal'] or value.get('binding_identity')!=plan['new_binding']['identity'] or c.get('binding_identity')!=plan['new_binding']['identity']:
  raise ValueError('fresh loaded content/readiness failed; no receipt/Send')
 if any(c.get(k) is not True for k in ('reachable','bound','composer_present','composer_empty','ready')) or any(c.get(k) is not False for k in ('busy','generation_active')):
  raise ValueError('content not unambiguously ready')
 matches=value.get('matches',[])
 if len(matches)!=1 or any(matches[0].get(k) is not False for k in ('hidden','discarded','incognito')):raise ValueError('one actual ready bound tab required')
 url=urlsplit(matches[0].get('url',''))
 if url.scheme!='https' or url.netloc!='chatgpt.com' or url.query or url.fragment or not re.fullmatch(r'(?:/g/g-p-[a-z0-9-]+)?/c/'+plan['new_binding']['conversation_id']+r'/?',url.path,re.I):raise ValueError('wrong readiness conversation')
 if not 0<=now_ms-value.get('observed_ms',0)<=60000:raise ValueError('stale no-send readiness')
 return True


def wait_probe(plan):
 probe=uuid.uuid4().hex
 started_ms=time.time()*1000
 m.save(RUNTIME/'inbox_binding_probe.json',{'probe_id':probe,'binding_identity':plan['new_binding']['identity']})
 print('Fresh no-send current-content probe; no historical message lookup, scrolling or reload.')
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  try:
   value=json.loads((RUNTIME/'inbox_binding_readiness.json').read_text(encoding='utf-8'))
   # Native periodic freshness may replace an empty owner probe. Accept its
   # authenticated current nonce only if generated after this request, with the
   # same binding and no targeted/historical lookup. Never accept an old result.
   expected_probe=probe
   request=json.loads((RUNTIME/'inbox_binding_probe.json').read_text(encoding='utf-8'))
   if request.get('binding_identity')==plan['new_binding']['identity'] and not request.get('diagnostic_targets') and value.get('observed_ms',0)>=started_ms:expected_probe=request.get('probe_id')
   if value.get('observed_ms',0)>=started_ms and checked_readiness(value,plan,expected_probe,time.time()*1000):
    # Do not overwrite the original diagnostic proving node_count=0. A missing
    # historical node is not an extraction failure on a current node.
    m.save(AREA/'current-content-readiness.json',value)
    return value
  except (OSError,json.JSONDecodeError):pass
  time.sleep(1)
 raise ValueError('new loaded native/background/content proof not received; no receipt/Send; keep VM stopped')


def wait_vm_ack(plan,after):
 expected={'action':'VM_MODEL_GATE_ALIGNED','in_reply_to':after,'lane_id':plan['new_policy']['lane_id'],
           'seal':plan['new_policy']['seal'],'binding_identity':plan['new_binding']['identity'],
           'completion_cutoff':129,'request_cutoff':129,'future_cursor':132,'historical_state_unchanged':True}
 deadline=time.monotonic()+180
 # ACK may arrive while the Codex turn is still active. Start at the request,
 # not one minute before worker startup, or a valid early ACK would be missed.
 since=quote(github_record(after)['created_at'])
 while time.monotonic()<deadline:
  p=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/45/comments?per_page=100&since='+since,'--paginate','--jq',f'.[] | select(.id>{after})'],capture_output=True,text=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  # jq emits separate JSON objects. Decode incrementally without interpreting prose.
  if p.returncode==0:
   decoder=json.JSONDecoder();data=p.stdout.lstrip()
   while data:
    record,end=decoder.raw_decode(data);data=data[end:].lstrip()
    if record.get('user',{}).get('login')!='grxr-dev':continue
    if alignment_ack(record,expected):return record['id']
  time.sleep(10)
 raise ValueError('exact Jarvis VM gate alignment ACK absent; receipt remains held; no Send')


def alignment_ack(record,expected):
 """Accept a typed ACK, including a fenced reply; never a generic auto-ACK."""
 if record.get('user',{}).get('login')!='grxr-dev':return False
 text=record.get('body','');decoder=json.JSONDecoder()
 for match in re.finditer(r'\{',text):
  try:value,_=decoder.raw_decode(text[match.start():])
  except ValueError:continue
  if isinstance(value,dict) and all(value.get(k)==v and type(value.get(k)) is type(v) for k,v in expected.items()):return True
 return False


def wait_delivery_proof(plan,after):
 """Read-only after receipt. No POST, claim, ACK, cursor write or Send trigger."""
 since=quote((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(minutes=1)).isoformat())
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  try:
   q=json.loads((RUNTIME/'inbox_future_queue.json').read_text(encoding='utf-8'))
   blocked=[e for e in q['entries'].values() if e['state']=='NEEDS_REVIEW' and (e.get('outcome') or {}).get('_future',{}).get('source',{}).get('sequence',0)>133]
   if blocked:
    e=min(blocked,key=lambda e:e['outcome']['_future']['source']['sequence'])
    incident=RUNTIME/'inbox_verifier_incidents'/(receipt.sha(e['delivery_id'].encode())+'.jsonl')
    captured=None
    if incident.exists():
     destination=AREA/('next-blocked-'+incident.name);m.atomic(destination,incident.read_bytes());captured=str(destination)
    value={'status':'STOPPED_ON_NEW_NEEDS_REVIEW','delivery_id':e['delivery_id'],'sequence':e['outcome']['_future']['source']['sequence'],
           'attempt_count':e['attempt_count'],'error':e['last_error'],'incident':captured,'no_additional_reconciliation':True}
    m.save(AREA/'live-validation.json',m.sealed(value))
    try:post('[CODEX → JARVIS / CHATGPT] STOPPED: first new automatic delivery is ambiguous. Preserve strict oldest-first and no resend. No further receipt/reconciliation. Targeted incident retained.\n'+json.dumps(value))
    except (ValueError,OSError,subprocess.TimeoutExpired):pass
    return
   auto={e['outcome']['_future']['source']['sequence']:e for e in q['entries'].values()
         if e['state']=='DELIVERED' and e['attempt_count']==1 and isinstance(e.get('outcome'),dict)
         and 'operator_receipt' not in e['outcome'] and e['outcome'].get('observed_sha256')==e['text_sha256']
         and e['outcome'].get('send_intent') is True and e['outcome'].get('send_count')==1
         and e['outcome'].get('new_user_turns')==1 and e['outcome'].get('user_turn_uuid')}
   p=subprocess.run(['gh','api','repos/grxr-dev/codex-relay/issues/45/comments?per_page=100&since='+since,'--paginate','--jq',f'.[] | select(.id>{after})'],capture_output=True,text=True,timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   if p.returncode==0 and 134 in auto and 135 in auto:
    decoder=json.JSONDecoder();data=p.stdout.lstrip()
    while data:
     record,end=decoder.raw_decode(data);data=data[end:].lstrip()
     if record.get('user',{}).get('login')!='grxr-dev':continue
     try:v=json.loads(record['body'])
     except (ValueError,KeyError):continue
     if v.get('action')!='VM_MODEL_DELIVERY_PROOF' or v.get('in_reply_to')!=after or v.get('seal')!=plan['new_policy']['seal'] or v.get('lane_id')!=plan['new_policy']['lane_id'] or type(v.get('future_cursor')) is not int or v['future_cursor']<=135 or v.get('historical_state_unchanged') is not True:continue
     # Independently correlate one new automatic result with raw-model trace
     # evidence, one Send event and the committed stable user UUID.
     for seq,e in sorted(auto.items()):
      if seq<=133:continue
      rows=[]
      for path in RUNTIME.glob('inbox_verifier_trace.jsonl*'):
       if not path.is_file():continue
       for line in path.read_text(encoding='utf-8').splitlines():
        try:x=json.loads(line)
        except ValueError:continue
        if x.get('delivery_id')==e['delivery_id']:rows.append(x)
      uuid_value=e['outcome'].get('user_turn_uuid')
      samples=[c for x in rows if x.get('event')=='sample' and x.get('bound') is True for c in x.get('candidates',[]) if c.get('uuid')==uuid_value and c.get('source')=='raw-user-model' and c.get('in_baseline') is False and c.get('hash_match') is True and c.get('observed_sha256')==e['text_sha256']]
      if len(samples)>=2 and sum(x.get('event')=='send' for x in rows)==1:
       protected(plan)
       result={'status':'LIVE_AUTOMATIC_DELIVERY_PROVEN','future_cursor':v['future_cursor'],'vm_comment':record['id'],
               'seq134':auto[134]['delivery_id'],'seq135':auto[135]['delivery_id'],
               'automatic_model_delivery':e['delivery_id'],'user_turn_uuid':uuid_value,'send_events':1,
               'historical_files_unchanged':True}
       m.save(AREA/'live-validation.json',m.sealed(result));post('[CODEX → CHATGPT / JARVIS] Live automatic model delivery proof (not operator receipt):\n'+json.dumps(result));return
  except (OSError,KeyError,ValueError):pass
  time.sleep(10)
 m.save(AREA/'live-validation.json',m.sealed({'status':'PENDING_READ_ONLY_PROOF','not_claimed_resolved':True}))
 print('Receipt committed; automatic delivery/cursor proof not yet complete. No resend or additional task started.')


def finish():
 managed.AREA=AREA;a=m.read_sealed(AREA/'activation.json');managed.verify_tools(a)
 life=managed.lifecycle();managed.independent(life);managed.task_finished(a)
 plan=m.read_sealed(AREA/'plan.json');authority=github_record(receipt.COMMENT);receipt.authority(authority)
 raw=(AREA/'retained-133.jsonl').read_bytes();receipt.trace_proof(raw)
 if (AREA/'result.json').exists():raise ValueError('receipt already committed; never repeat')
 protected(plan);queue_preflight(plan)
 with managed.exclusive_stopped(life,a):
  protected(plan);queue_preflight(plan)
  current=json.loads((RUNTIME/'inbox_future.json').read_text(encoding='utf-8'))
  if current==plan['old_policy']:
   transaction(lambda:m.install(BRIDGE,STAGE,AREA,True),
               lambda:m.save(RUNTIME/'inbox_future.json',plan['new_policy']),
               lambda:validate_installed(plan),
               lambda:m.atomic(RUNTIME/'inbox_future.json',(AREA/'backup/future.json').read_bytes()),
               lambda:m.rollback(BRIDGE,AREA,plan,True))
  else:validate_installed(plan)
  print('Coherent source/new seal installed under exclusive stopped ownership; queue133 still held. Existing tray restart follows maintenance exit.')
  proof=wait_probe(plan)
  request={'action':'VM_MODEL_GATE_ALIGNED','lane_id':plan['new_policy']['lane_id'],'seal':plan['new_policy']['seal'],
           'binding_identity':plan['new_binding']['identity'],'completion_cutoff':129,'request_cutoff':129,'future_cursor':132,'historical_state_unchanged':True}
  comment=post('[CODEX → JARVIS] Owner maintenance: source/new binding/lane seal coherently installed, native/background/content build '+PROOF_BUILD+' loaded and current-content no-send readiness verified. Historical seq133 is operator-attested; no historical DOM lookup or raw-model claim. Bridge is held stopped under the original instance lock. Queue/cursor/history unchanged. Please now align ONLY your VM activation identity/seal (same lane/cutoffs), retain cursor132, and reply to this comment with ONLY this JSON plus in_reply_to set to THIS comment ID:\n'+json.dumps(request)+'\nThe bridge restarts after your ACK and the one seq133 operator receipt. Existing worker may then progress naturally. No repost/rearm133.')
  ack=wait_vm_ack(plan,comment)
  proof=wait_probe(plan)  # freshness after coordination; no composer mutation
  validate_installed(plan)
  sys.path.insert(0,str(BRIDGE));from inbox_future import source
  q=queue_preflight(plan);trusted=source(RUNTIME,plan['new_policy'],receipt.TARGET,q._entries[receipt.TARGET]['text'])
  if trusted!=plan['trusted_source']:raise ValueError('trusted source changed')
  m.atomic(AREA/'future-queue.before.json',q.path.read_bytes())
  result=receipt.reconcile(q,receipt.TARGET,receipt.FINGERPRINT,plan['old_binding_public'],plan['old_lane'],trusted,raw,authority,exclusive=True)
  protected(plan)
  result.update(new_binding_identity=plan['new_binding']['identity'],new_lane_seal=plan['new_policy']['seal'],
                loaded_proof_build=PROOF_BUILD,vm_alignment_comment=ack,raw_model_no_send_proof=False,current_content_readiness=True,
                historical_files_unchanged=True,cursor_modified=False)
  m.save(AREA/'result.json',m.sealed(result))
 print(json.dumps(result));after=post('[CODEX → JARVIS] Pinned seq133 operator receipt committed; original failed outcome/attempt/grant retained. No resend or cursor mutation. Existing managed tray now owns restart. Please let normal worker progress and provide cursor>135, each134/135 once, one wholly new automatically verified raw-user-model result, and unchanged historical hashes. Reply with ONLY JSON: action=VM_MODEL_DELIVERY_PROOF, in_reply_to=THIS comment ID, lane_id, seal, future_cursor, historical_state_unchanged=true.\n'+json.dumps(result))
 wait_delivery_proof(plan,after)


def rollback():
 managed.AREA=AREA;a=m.read_sealed(AREA/'activation.json');managed.verify_tools(a)
 life=managed.lifecycle();managed.independent(life);managed.task_finished(a)
 plan=m.read_sealed(AREA/'plan.json');protected(plan);queue_preflight(plan)
 if (AREA/'result.json').exists():raise ValueError('receipt committed: no source or queue rollback')
 def restore():
  protected(plan);queue_preflight(plan)
  current=json.loads((RUNTIME/'inbox_future.json').read_text(encoding='utf-8'))
  if current not in (plan['old_policy'],plan['new_policy']):raise ValueError('independent policy edit; no rollback')
  m.atomic(RUNTIME/'inbox_future.json',(AREA/'backup/future.json').read_bytes());m.rollback(BRIDGE,AREA,plan,True)
 try:managed.http()
 except OSError:
  # No force kill: acquiring the real instance lock is mandatory even if an
  # interrupted bundle prevents the managed bridge from starting.
  with managed.instance_lock():restore()
 else:
  with managed.exclusive_stopped(life,a):restore()
 post('[CODEX → JARVIS] Owner rolled back only the source/binding/lane source seal before any seq133 receipt. Queue/cursor/history untouched;133 remains held. Align VM gate back to original identity/seal if it was changed. No delivery release. Browser may require Reload to match restored disk source.')
 print('Rolled back source/policy only. No queue rollback or Send. Keep133 held.')


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','finish','rollback']);args=parser.parse_args()
 try:
  if args.action=='prepare':prepare()
  else:
   import msvcrt
   with (AREA/'owner.lock').open('a+b') as f:
    f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
    try:
     if args.action=='rollback':rollback()
     else:finish()
    finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
 except Exception as e:
  print('STOP: '+(str(e) if type(e) is ValueError else type(e).__name__+'; no blind retry, preserve audit.'));sys.exit(1)
