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

BOOLS={'reachable','bound','composer_present','composer_empty','generation_active','busy','ready'}
REASONS={'ready','unique_bound_tab_required','delivery_or_ack_active','content_unreachable_or_timeout','tab_query_failed','page_unbound','composer_missing_or_unsupported','delivery_active','draft_present','generation_active','readiness_inspection_failed'}


class ReadinessDiagnostic:
 def __init__(self,directory):
  self.directory=Path(directory)
  self.request=self.directory/'inbox_binding_probe.json'
  self.result=self.directory/'inbox_binding_readiness.json'
  self.waiting=None
  self.completed=None
 def poll(self):
  binding=load(self.directory)
  if not self.request.exists():return {'cmd':'idle','readiness_hold':True,'binding_identity':binding['identity']}
  try:
   if self.request.stat().st_size>256:raise ValueError()
   request=json.loads(self.request.read_text())
   if set(request)!={'probe_id','binding_identity'} or not re.fullmatch('[0-9a-f]{32}',request['probe_id']) or request['binding_identity']!=binding['identity']:raise ValueError()
   pair=(request['probe_id'],binding['identity'])
   if pair in (self.waiting,self.completed):return {'cmd':'idle','readiness_hold':True,'binding_identity':binding['identity']}
   self.waiting=pair
   return {'cmd':'readiness_probe','probe_id':pair[0],'binding_identity':pair[1]}
  except (OSError,ValueError,KeyError,TypeError):return {'cmd':'idle','readiness_hold':True,'readiness_error':'invalid_or_stale_binding_probe'}
 def accept(self,msg):
  try:
   binding=load(self.directory)
   if self.waiting!=(msg.get('probe_id'),binding['identity']) or msg.get('binding_identity')!=binding['identity']:raise ValueError()
   if set(msg)-{'cmd','probe_id','build','binding_identity','match_count','matches','truncated','ready','reason','content'}:raise ValueError()
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
    if count!=1 or set(content)!=BOOLS|{'reason','binding_identity'} or content['binding_identity']!=binding['identity'] or content['reason'] not in REASONS or any(type(content[key]) is not bool for key in BOOLS):raise ValueError()
   ready=bool(count==1 and content and all(content[key] for key in ['reachable','bound','composer_present','composer_empty','ready']) and not content['generation_active'] and not content['busy'])
   if ready and any(matches[0].get(key) is not False for key in ('hidden','discarded','incognito')):raise ValueError()
   if msg['ready']!=ready or (ready and msg['reason']!='ready'):raise ValueError()
   value=dict(msg,native_pid=os.getpid(),observed_ms=int(time.time()*1000));value.pop('cmd')
   if len(json.dumps(value))>65536:raise ValueError()
   atomic(self.result,value);self.completed=self.waiting;self.waiting=None
   return {'cmd':'readiness_recorded','probe_id':self.completed[0],'binding_identity':binding['identity']}
  except Exception:return {'cmd':'error','error':'invalid/stale binding readiness; no delivery attempted'}
