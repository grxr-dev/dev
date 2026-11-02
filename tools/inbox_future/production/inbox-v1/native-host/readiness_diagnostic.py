"""No-send readiness bound to the same persistent recipient as native delivery."""
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from inbox_binding import BUILD, load, atomic, public
from inbox_one import BUILD as ONE_BUILD
from inbox_future import BUILD as FUTURE_BUILD

BOOLS={'reachable','bound','composer_present','composer_empty','generation_active','busy','ready'}
REASONS={'ready','unique_bound_tab_required','delivery_or_ack_active','content_unreachable_or_timeout','tab_query_failed','page_unbound','composer_missing_or_unsupported','delivery_active','draft_present','generation_active','readiness_inspection_failed'}
PROOF_BUILD='inbox-composer-user-proof-20261102-01'

def targets(value):
 if not isinstance(value,list) or len(value)>2:raise ValueError('bounded targets required')
 for target in value:
  if not isinstance(target,dict) or set(target)!={'delivery_id','user_turn_uuid','text_sha256'} or not re.fullmatch('[A-Za-z0-9:_.-]{1,200}',target['delivery_id']) or not re.fullmatch('[0-9a-f-]{36}',target['user_turn_uuid']) or not re.fullmatch('[0-9a-f]{64}',target['text_sha256']):raise ValueError('invalid diagnostic target')
 return value

def diagnostics(value,expected):
 if not isinstance(value,list) or len(value)!=len(expected):raise ValueError('diagnostic count mismatch')
 for item,target in zip(value,expected):
  keys={'delivery_id','uuid','expected_sha256','observed_sha256','exact','bound','node_count','model_status','structure','rendered_sha256','rendered_length','raw_model_length'}
  if not isinstance(item,dict) or set(item)!=keys or item['delivery_id']!=target['delivery_id'] or item['uuid']!=target['user_turn_uuid'] or item['expected_sha256']!=target['text_sha256']:raise ValueError('diagnostic identity mismatch')
  observed=item['observed_sha256']
  if observed is not None and not re.fullmatch('[0-9a-f]{64}',observed):raise ValueError('invalid hash')
  if item['rendered_sha256'] is not None and not re.fullmatch('[0-9a-f]{64}',item['rendered_sha256']):raise ValueError('invalid rendered hash')
  for k in ('rendered_length','raw_model_length'):
   if item[k] is not None and (type(item[k]) is not int or not 0<=item[k]<=1000000):raise ValueError('invalid diagnostic length')
  if type(item['exact']) is not bool or type(item['bound']) is not bool or item['exact']!=(observed==target['text_sha256']) or type(item['node_count']) is not int or not 0<=item['node_count']<=1000 or item['model_status'] not in ('raw_user_model','model_unavailable','conflicting_or_unsupported_model'):raise ValueError('invalid diagnostic proof')
  if not isinstance(item['structure'],list) or len(item['structure'])>32:raise ValueError('invalid structure bound')
  for node in item['structure']:
   if not isinstance(node,dict) or set(node) not in ({'type','length','depth'},{'type','depth','bubble','markdown','interactive'}) or not re.fullmatch('[a-z0-9-]{1,24}',node['type']) or type(node['depth']) is not int or not 0<=node['depth']<=3:raise ValueError('invalid node structure')
   if node['type']=='text':
    if type(node.get('length')) is not int or not 0<=node['length']<=1000000:raise ValueError('invalid text length')
   elif any(type(node.get(k)) is not bool for k in ('bubble','markdown','interactive')):raise ValueError('invalid element metadata')
 return value


class ReadinessDiagnostic:
 def __init__(self,directory):
  self.directory=Path(directory)
  self.request=self.directory/'inbox_binding_probe.json'
  self.result=self.directory/'inbox_binding_readiness.json'
  self.waiting=None
  self.completed=None
  self.targets=[]
 def poll(self):
  binding=load(self.directory)
  if not self.request.exists():return {'cmd':'idle','readiness_hold':True,'binding_identity':binding['identity']}
  try:
   if self.request.stat().st_size>2048:raise ValueError()
   request=json.loads(self.request.read_text())
   if set(request) not in ({'probe_id','binding_identity'},{'probe_id','binding_identity','diagnostic_targets'}) or not re.fullmatch('[0-9a-f]{32}',request['probe_id']) or request['binding_identity']!=binding['identity']:raise ValueError()
   pair=(request['probe_id'],binding['identity'])
   if pair in (self.waiting,self.completed):return {'cmd':'idle','readiness_hold':True,'binding_identity':binding['identity']}
   self.waiting=pair
   self.targets=targets(request.get('diagnostic_targets',[]))
   return {'cmd':'readiness_probe','probe_id':pair[0],'binding_identity':pair[1],'diagnostic_targets':self.targets}
  except (OSError,ValueError,KeyError,TypeError):return {'cmd':'idle','readiness_hold':True,'readiness_error':'invalid_or_stale_binding_probe'}
 def accept(self,msg):
  try:
   binding=load(self.directory)
   if self.waiting!=(msg.get('probe_id'),binding['identity']) or msg.get('binding_identity')!=binding['identity']:raise ValueError()
   if set(msg)-{'cmd','probe_id','build','binding_identity','match_count','matches','truncated','ready','reason','content','one_build','future_build','diagnostics'}:raise ValueError()
   if msg.get('one_build')!=ONE_BUILD or msg.get('future_build')!=FUTURE_BUILD:raise ValueError()
   if msg.get('build')!=BUILD or msg.get('reason') not in REASONS:raise ValueError()
   count=msg['match_count'];matches=msg['matches']
   if type(count) is not int or not 0<=count<=100000 or not isinstance(matches,list) or len(matches)!=min(count,128):raise ValueError()
   if type(msg['truncated']) is not bool or msg['truncated']!=(count>128) or type(msg['ready']) is not bool:raise ValueError()
   ids=set()
   for tab in matches:
    if not isinstance(tab,dict) or set(tab)-{'id','windowId','url','active','hidden','discarded','pinned','incognito'}:raise ValueError()
    if type(tab.get('id')) is not int or type(tab.get('windowId')) is not int or tab['id'] in ids:raise ValueError()
    ids.add(tab['id']);url=urlsplit(tab['url'])
    if url.scheme!='https' or url.netloc!='chatgpt.com' or url.query or url.fragment or not re.fullmatch(r'(?:/g/g-p-[a-z0-9-]+)?/c/'+binding['conversation_id']+r'/?',url.path,re.I):raise ValueError()
    if any(type(value) is not bool for key,value in tab.items() if key not in {'id','windowId','url'}):raise ValueError()
   content=msg.get('content')
   if content is not None:
    if count!=1 or set(content)!=BOOLS|{'reason','binding_identity','one_build','future_build','future_lane_seal','proof_build'} or content.get('proof_build')!=PROOF_BUILD or content.get('one_build')!=ONE_BUILD or content.get('future_build')!=FUTURE_BUILD or content['binding_identity']!=binding['identity'] or content['reason'] not in REASONS or any(type(content[key]) is not bool for key in BOOLS):raise ValueError()
   diagnostics(msg.get('diagnostics',[]),self.targets if content else [])
   ready=bool(count==1 and content and all(content[key] for key in ['reachable','bound','composer_present','composer_empty','ready']) and not content['generation_active'] and not content['busy'])
   if ready and any(matches[0].get(key) is not False for key in ('hidden','discarded','incognito')):raise ValueError()
   from inbox_future import config as future_config
   lane=future_config(self.directory)
   if content and content.get('future_lane_seal')!=(lane['seal'] if lane else None):raise ValueError()
   if msg['ready']!=ready or (ready and msg['reason']!='ready'):raise ValueError()
   value=dict(msg,native_pid=os.getpid(),observed_ms=int(time.time()*1000));value.pop('cmd')
   if len(json.dumps(value))>65536:raise ValueError()
   atomic(self.result,value);self.completed=self.waiting;self.waiting=None
   return {'cmd':'readiness_recorded','probe_id':self.completed[0],'binding_identity':binding['identity']}
  except Exception:return {'cmd':'error','error':'invalid/stale binding readiness; no delivery attempted'}
