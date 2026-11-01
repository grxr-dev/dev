"""Owner-invoked, journaled source-only upgrade. Never edits a queue or a grant.

The caller MUST own the existing bridge instance byte lock after managed idle
shutdown. Source files are replaced atomically, binding last. A partial bundle
fails the existing source seal. Recovery restores only source/config, never state.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

OLD_ID='376671cc6cefba6f6e5f95284f13b7a96deb912518a3a0032ae97845bd3493c3'
DEST='6ae5615a-0720-83ea-a43b-82386ce031e5'
EPOCH='b2108916e5fb44098859a58e0252a2ad'
PROTECTED=('inbox_queue.json','inbox_native_recovery.json','inbox_readiness_request.json')
TARGET='middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878'
TEXT_SHA='1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651'


def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'))
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if tmp.exists():tmp.unlink()
def save(path,value):atomic(path,canonical(value).encode())
def sealed(value):return dict(value,seal=digest(value))
def read_sealed(path):
 value=json.loads(Path(path).read_text());seal=value.pop('seal')
 if digest(value)!=seal:raise ValueError('migration audit seal mismatch')
 return value
def state_hashes(bridge):return {n:sha(bridge/'.runtime'/n) for n in PROTECTED}
def history_digest(q):return digest({'entries':{k:v for k,v in q['entries'].items() if k!=TARGET},'recovery_once':q.get('recovery_once'),'superseded_watchdog':q.get('superseded_watchdog')})
def checked_binding(bridge):
 code='import sys,json;sys.path.insert(0,sys.argv[1]);from inbox_binding import load;print(json.dumps(load(sys.argv[1]+"/.runtime")))'
 p=subprocess.run([sys.executable,'-B','-c',code,str(bridge)],capture_output=True,timeout=10)
 if p.returncode:raise ValueError('coherent source/config verification failed')
 return json.loads(p.stdout)
def paths(manifest):
 names=manifest['source_files_sha256']
 for name in names:
  if not isinstance(name,str) or name.startswith('/') or '\\' in name or ':' in name or '..' in name.split('/'):
   raise ValueError('unsafe source path')
 return names
def check_stage(stage,manifest):
 for name,want in paths(manifest).items():
  if sha(stage/name)!=want:raise ValueError('staged source differs from reviewed manifest')


def prepare(bridge,stage,manifest,area):
 if (area/'plan.json').exists():raise ValueError('plan already exists; inspect existing audit, never overwrite')
 check_stage(stage,manifest)
 old=checked_binding(bridge)
 if (old['identity'],old['conversation_id'],old['generation'],old['epoch'],old['delivery_policy'])!=(OLD_ID,DEST,1,EPOCH,'HOLD'):
  raise ValueError('wrong initial sealed recipient')
 protected=state_hashes(bridge)
 queue=json.loads((bridge/'.runtime/inbox_queue.json').read_text(encoding='utf-8-sig'))
 e=queue['entries'].get(TARGET)
 if not e or e['state']!='QUEUED' or e['attempt_count']!=0 or e['text_sha256']!=TEXT_SHA or hashlib.sha256(e['text'].encode()).hexdigest()!=TEXT_SHA:
  raise ValueError('exact existing test identity/state mismatch')
 if queue.get('exact_one') is not None or any(e['state']=='DELIVERING' for e in queue['entries'].values()):raise ValueError('grant/delivery already exists')
 if json.loads((bridge/'.runtime/inbox_native_recovery.json').read_text()) is not None:raise ValueError('native outcome outstanding')
 components=manifest['required_binding_components']
 if set(components)-set(paths(manifest)) or len(set(components))!=len(components):raise ValueError('component coverage incomplete')
 # Derive the new seal from the reviewed exact source bytes. Every other binding
 # field, including protected_history, recipient, generation and epoch is immutable.
 new=copy.deepcopy(old);new['components']={n:manifest['source_files_sha256'][n] for n in components}
 new['identity']=digest({k:v for k,v in new.items() if k!='identity'})
 expected=manifest['hypothetical_source_reseal_identity_not_applied']
 if new['identity']!=expected:raise ValueError('reviewed new source identity mismatch')
 area.mkdir(parents=True,exist_ok=True)
 originals={}
 for name in paths(manifest):
  file=bridge/name;originals[name]=sha(file) if file.exists() else None
  if originals[name]!=manifest['expected_original_sources'][name]:raise ValueError('original deployed source differs from issue96 inventory')
  if file.exists():atomic(area/'backup'/name,file.read_bytes())
 old_raw=(bridge/'.runtime/inbox_binding.json').read_bytes();atomic(area/'backup/binding.json',old_raw)
 plan={'schema':'inbox-source-migration/1','authorization':'owner issue96 continuation; source only, exact-one remains separately gated',
       'created_at':time.time(),'old_binding_sha256':hashlib.sha256(old_raw).hexdigest(),
       'old_identity':old['identity'],'new_binding':new,'new_sources':manifest['source_files_sha256'],
       'original_sources':originals,'protected':protected,'history_sha256':history_digest(queue)}
 save(area/'plan.json',sealed(plan));return plan


def unchanged(bridge,plan):
 if state_hashes(bridge)!=plan['protected']:raise ValueError('queue/journal/hold changed; do not rollback or retry')
def event(area,plan,phase):
 journal={'plan_sha256':digest(plan),'phase':phase,'at':time.time()}
 save(area/'journal.json',sealed(journal))
def verify_backups(area,plan):
 if sha(area/'backup/binding.json')!=plan['old_binding_sha256']:raise ValueError('binding backup corrupted')
 for name,want in plan['original_sources'].items():
  if want is not None and sha(area/'backup'/name)!=want:raise ValueError('source backup corrupted')
def rollback(bridge,area,plan,exclusive):
 if not exclusive:raise ValueError('exclusive stopped-bridge ownership required')
 unchanged(bridge,plan);verify_backups(area,plan)
 # Only known old/new bytes may be restored. Never overwrite unrelated owner edits.
 for name,old in plan['original_sources'].items():
  p=bridge/name;current=sha(p) if p.exists() else None
  if current not in (old,plan['new_sources'][name]):raise ValueError('unexpected source edit; preserve for review')
 binding=bridge/'.runtime/inbox_binding.json'
 if sha(binding) not in (plan['old_binding_sha256'],hashlib.sha256(canonical(plan['new_binding']).encode()).hexdigest()):raise ValueError('binding changed independently')
 event(area,plan,'ROLLING_BACK')
 for name,old in plan['original_sources'].items():
  if old is None:
   if (bridge/name).exists():(bridge/name).unlink()
  else:atomic(bridge/name,(area/'backup'/name).read_bytes())
 atomic(binding,(area/'backup/binding.json').read_bytes())
 if checked_binding(bridge)['identity']!=plan['old_identity']:raise ValueError('restored seal failed')
 unchanged(bridge,plan);event(area,plan,'ROLLED_BACK')


def install(bridge,stage,area,exclusive,fail_after=None):
 if not exclusive:raise ValueError('exclusive stopped-bridge ownership required')
 plan=read_sealed(area/'plan.json');unchanged(bridge,plan);verify_backups(area,plan)
 for name,want in plan['new_sources'].items():
  if sha(stage/name)!=want:raise ValueError('staged source tampered after prepare')
 if (area/'journal.json').exists():
  j=read_sealed(area/'journal.json')
  if j['plan_sha256']!=digest(plan):raise ValueError('journal belongs to different migration')
  if j['phase']=='COMPLETE':
   if checked_binding(bridge)!=plan['new_binding']:raise ValueError('installed source changed')
   return plan  # Source idempotence, never repeats a grant.
  raise ValueError('interrupted/rolled-back migration; explicit rollback/review required')
 if checked_binding(bridge)['identity']!=plan['old_identity']:raise ValueError('initial binding changed')
 for name,want in plan['original_sources'].items():
  p=bridge/name
  if (sha(p) if p.exists() else None)!=want:raise ValueError('deployed source changed since prepare')
 event(area,plan,'PREPARED')
 try:
  event(area,plan,'APPLYING')
  for index,name in enumerate(plan['new_sources'],1):
   atomic(bridge/name,(stage/name).read_bytes())
   if index==fail_after:raise OSError('injected interruption')
  unchanged(bridge,plan)
  # Commit point. Until this replacement, existing hash checks fail closed.
  atomic(bridge/'.runtime/inbox_binding.json',canonical(plan['new_binding']).encode())
  if checked_binding(bridge)!=plan['new_binding']:raise ValueError('new source seal failed')
  unchanged(bridge,plan);event(area,plan,'COMPLETE');return plan
 except Exception:
  rollback(bridge,area,plan,exclusive=True)
  raise
