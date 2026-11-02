"""FUTURE_ONLY lane on the existing Inbox engine. Legacy queue is read-only.
Eligibility comes exclusively from the local production completion/request ledger.
"""
import copy
import contextlib
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from inbox_binding import load as binding_load,public,digest,COMPONENTS
from inbox_queue import InboxQueue,Conflict
from inbox_wire import validate_text,sha256_text,delivery_message

BUILD='inbox-future-only-20261101-01'
ONE_BUILD='inbox-exact-one-20261101-01'
DEST='6ae5615a-0720-83ea-a43b-82386ce031e5'
LOADED={n:hashlib.sha256((Path(__file__).resolve().parent/n).read_bytes()).hexdigest() for n in COMPONENTS}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def config(runtime):
 p=Path(runtime)/'inbox_future.json'
 if not p.exists():return None
 if p.stat().st_size>8192:raise Conflict('future checkpoint size')
 v=json.loads(p.read_text());expected=v.pop('seal',None)
 if digest(v)!=expected or set(v)!={'schema','build','state','lane_id','binding','completion_cutoff','request_cutoff','legacy_queue_sha256','legacy_hold_sha256'}:
  raise Conflict('future checkpoint invalid')
 b=binding_load(runtime)
 if v['schema']!='inbox-future-only/1' or v['build']!=BUILD or v['state'] not in ('PREPARED','ACTIVE') or v['binding']!=public(b) or b['components']!=LOADED or b['conversation_id']!=DEST or b['generation']!=1 or b['delivery_policy']!='HOLD':raise Conflict('future loaded binding/source mismatch')
 if not re.fullmatch('[0-9a-f]{32}',v['lane_id']) or any(type(v[k]) is not int or v[k]<0 for k in ('completion_cutoff','request_cutoff')):raise Conflict('future checkpoint invalid')
 if sha(Path(runtime)/'inbox_queue.json')!=v['legacy_queue_sha256'] or sha(Path(runtime)/'inbox_readiness_request.json')!=v['legacy_hold_sha256']:raise Conflict('legacy HOLD/history changed; future lane stopped')
 return dict(v,seal=expected)
def lane_public(v):return {k:v[k] for k in ('schema','build','state','lane_id','binding','completion_cutoff','request_cutoff','seal')}
@contextlib.contextmanager
def db(runtime):
 c=sqlite3.connect((Path(runtime)/'completions.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=3);c.row_factory=sqlite3.Row
 try:yield c
 finally:c.close()
def source(runtime,v,did,text=None):
 if v['state']!='ACTIVE':raise Conflict('future lane PREPARED; separate live authorization required')
 rid,sep,result_hash=did.rpartition(':')
 if not sep or not re.fullmatch('[0-9a-f]{64}',result_hash):raise Conflict('trusted completion identity required')
 with db(runtime) as c:
  r=c.execute('SELECT c.sequence,c.event_id,c.request_id,c.result,r.rowid AS request_ordinal,r.source FROM completions c JOIN requests r USING(request_id) WHERE c.request_id=?',(rid,)).fetchone()
 if not r or r['sequence']<=v['completion_cutoff'] or r['request_ordinal']<=v['request_cutoff'] or r['source'] not in ('github','http') or r['result'] is None:raise Conflict('pre-activation/unavailable result remains quarantined')
 payload=json.loads(bytes(r['result']));response=payload.get('response')
 if payload.get('request_id')!=rid or not isinstance(response,str) or sha256_text(response)!=result_hash or payload.get('response_sha256')!=result_hash:raise Conflict('stored result identity/hash mismatch')
 expected='[CODEX → CHATGPT]\n\n'+response
 if text is not None and text!=expected:raise Conflict('exact verbatim stored result required')
 return {'sequence':r['sequence'],'event_id':r['event_id'],'request_ordinal':r['request_ordinal'],'request_id':rid,'result_sha256':result_hash}
def annotate(runtime,events):
 v=config(runtime)
 if v is None:return None
 with db(runtime) as c:
  for e in events:
   r=c.execute('SELECT rowid,source FROM requests WHERE request_id=?',(e['request_id'],)).fetchone()
   e['future_eligible']=bool(v['state']=='ACTIVE' and r and e['sequence']>v['completion_cutoff'] and r['rowid']>v['request_cutoff'] and r['source'] in ('github','http'))
   if e['future_eligible']:
    e['future_request_ordinal']=r['rowid']
    stored=c.execute('SELECT result FROM completions WHERE request_id=?',(e['request_id'],)).fetchone()
    payload=json.loads(bytes(stored['result'])) if stored and stored['result'] is not None else {}
    response=payload.get('response');claimed=payload.get('response_sha256')
    e['future_result_sha256']=claimed if isinstance(response,str) and payload.get('request_id')==e['request_id'] and sha256_text(response)==claimed else None
 return lane_public(v)


def verify_envelope(v,d,current,now,allow_expired=False,runtime=None):
 runtime=Path(runtime) if runtime else Path(__file__).resolve().parent/'.runtime'
 cfg=config(runtime)
 keys={'schema','build','authorization_id','delivery_id','text_sha256','binding','created_at','expires_at','lane','source'}
 if not cfg or cfg['state']!='ACTIVE' or not isinstance(v,dict) or set(v)!=keys or v['schema']!='inbox-future-grant/1' or v['build']!=ONE_BUILD or v['lane']!=lane_public(cfg) or v['binding']!=current:raise Conflict('future authorization/binding mismatch')
 if v['delivery_id']!=d['delivery_id'] or v['text_sha256']!=d['text_sha256'] or not re.fullmatch('[0-9a-f]{32}',v['authorization_id']):raise Conflict('future exact delivery mismatch')
 s=v['source']
 if s!=source(runtime,cfg,d['delivery_id'],d.get('text')):raise Conflict('future source event mismatch')
 if type(v['created_at']) not in (int,float) or type(v['expires_at']) not in (int,float) or not 1<=v['expires_at']-v['created_at']<=300 or now<v['created_at'] or (not allow_expired and now>=v['expires_at']):raise Conflict('future grant expired')
 return v


class FutureLane:
 def __init__(self,legacy):
  self.legacy=legacy;self.runtime=legacy.path.parent;config(self.runtime)
  self.q=InboxQueue(self.runtime/'inbox_future_queue.json')
 def post(self,body):
  if not isinstance(body,dict) or set(body)!={'delivery_id','text'}:raise ValueError('only delivery_id and text accepted')
  v=config(self.runtime);did=body['delivery_id'];text=validate_text(did,body['text'])
  # Existing legacy ID returns existing evidence only; never requeues or retargets.
  if did in self.legacy._entries:
   e=self.legacy._entries[did]
   if e['text']!=text:raise Conflict('delivery_id has different canonical text')
   return copy.deepcopy(e),False
  source(self.runtime,v,did,text)
  return self.q.enqueue(did,text)
 def ready(self):
  if not self.legacy._recovery_check:raise Conflict('fresh future readiness required')
  r=self.legacy._recovery_check()
  if r['content'].get('proof_build')!='inbox-composer-user-proof-20261102-01' or r['content'].get('future_build')!=BUILD or r['content'].get('future_lane_seal')!=config(self.runtime)['seal']:raise Conflict('loaded future content/lane capability required')
 def claim(self):
  with self.q.lock:
   v=config(self.runtime)
   if v['state']!='ACTIVE':return None
   # Query the trusted sequence, not POST order. Missing earlier eligible items
   # block later ones; the legacy cursor is never consulted or advanced.
   with db(self.runtime) as c:
    oldest=c.execute('SELECT min(sequence) FROM completions').fetchone()[0]
    rows=c.execute('SELECT c.request_id,c.sequence,c.result FROM completions c JOIN requests r USING(request_id) WHERE c.sequence>? AND r.rowid>? AND r.source IN (\'github\',\'http\') ORDER BY c.sequence',(v['completion_cutoff'],v['request_cutoff'])).fetchall()
   done={e['outcome']['_future']['source']['sequence'] for e in self.q._entries.values() if e['state']=='DELIVERED'}
   frontier=max(done,default=v['completion_cutoff'])
   if oldest and oldest>frontier+1:raise Conflict('source event retention gap; review, never skip')
   for row in rows:
    if row['sequence'] in done:continue
    if row['result'] is None:raise Conflict('oldest future result unavailable; review')
    payload=json.loads(bytes(row['result']));did=row['request_id']+':'+str(payload.get('response_sha256'))
    e=self.q._entries.get(did)
    if e is None:return None
    if e['state']=='DELIVERED':continue
    if e['state']!='QUEUED' or e['attempt_count']!=0:return None
    self.ready();s=source(self.runtime,v,did,e['text']);now=self.q.clock()
    grant={'schema':'inbox-future-grant/1','build':ONE_BUILD,'authorization_id':secrets.token_hex(16),
      'delivery_id':did,'text_sha256':e['text_sha256'],'binding':v['binding'],'created_at':now,'expires_at':now+120,'lane':lane_public(v),'source':s}
    entries=copy.deepcopy(self.q._entries);e=entries[did]
    e.update(state='DELIVERING',attempt_count=1,last_attempt_at=now,claim_token=secrets.token_hex(32),outcome={'_future':grant,'send_intent':False})
    self.q._commit(entries)
    result=delivery_message(e);result['authorization']=grant;return result
   return None
 def checked(self,body,allow_expired=False):
  config(self.runtime);e=self.q._entries.get(body.get('delivery_id'));meta=e.get('outcome') if e else None
  if not e or not isinstance(meta,dict) or '_future' not in meta or e['claim_token']!=body.get('claim_token') or meta['_future']['authorization_id']!=body.get('authorization_id'):raise Conflict('future claim mismatch')
  grant=meta['_future'];verify_envelope(grant,e,config(self.runtime)['binding'],self.q.clock(),allow_expired,self.runtime)
  return e,grant
 def permit(self,body):
  with self.q.lock:
   if set(body)!={'delivery_id','authorization_id','claim_token','text_sha256','binding_identity'}:raise Conflict('invalid future permit')
   e,g=self.checked(body)
   if e['state']!='DELIVERING' or e['outcome']['send_intent'] or body['text_sha256']!=e['text_sha256'] or body['binding_identity']!=g['binding']['identity']:raise Conflict('future Send permit already used/stale')
   entries=copy.deepcopy(self.q._entries);entries[e['delivery_id']]['outcome']['send_intent']=True;self.q._commit(entries)
   return {'ok':True,'build':ONE_BUILD,'authorization_id':g['authorization_id'],'expires_at':g['expires_at']}
 def ack(self,body):
  with self.q.lock:
   allowed={'delivery_id','claim_token','authorization_id','state','error','pre_send','observed_sha256','send_count','new_user_turns','composer_empty','user_turn_uuid','verification_method','composer_sha256'}
   if set(body)-allowed:raise Conflict('invalid future ACK')
   if body.get('error') is not None and (not isinstance(body['error'],str) or len(body['error'])>2000):raise Conflict('invalid error')
   e,g=self.checked(body,True);state=body['state']
   if state=='FAILED_RETRYABLE':state='FAILED_PERMANENT'
   if state not in ('DELIVERED','FAILED_PERMANENT','NEEDS_REVIEW'):raise Conflict('invalid future outcome')
   if state=='DELIVERED' and (not e['outcome']['send_intent'] or body.get('verification_method')!='composer_hash_single_send_new_user_uuid_v1' or body.get('composer_sha256')!=e['text_sha256'] or body.get('observed_sha256') is not None or type(body.get('send_count')) is not int or body['send_count']!=1 or type(body.get('new_user_turns')) is not int or body['new_user_turns']!=1 or body.get('composer_empty') is not True or not re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',str(body.get('user_turn_uuid','')))):raise Conflict('exact composer hash/one-Send/new USER/empty-composer proof required')
   outcome=dict(body,state=state,_future=g,send_intent=e['outcome']['send_intent']);outcome.pop('claim_token')
   if e['outcome']==outcome:return e
   if e['state'] not in ('DELIVERING','NEEDS_REVIEW') or (e['state']=='NEEDS_REVIEW' and 'state' in e['outcome']):raise Conflict('refusing to rewrite terminal future outcome')
   entries=copy.deepcopy(self.q._entries);n=entries[e['delivery_id']];n.update(state=state,outcome=outcome,last_error=body.get('error'))
   if state=='DELIVERED':n.update(delivered_at=self.q.clock(),last_error=None)
   self.q._commit(entries);return n
