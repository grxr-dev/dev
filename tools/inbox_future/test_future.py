"""Small critical tests only; real staged queue and SQLite provenance, no live send."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent;STAGE=HERE/'production';LIVE=HERE.parents[2]/'bridge'
sys.path[:0]=[str(STAGE),str(LIVE),str(STAGE/'inbox-v1/native-host')]
import inbox_binding as binding
from inbox_queue import InboxQueue,Conflict
import inbox_future as future
from inbox_api import InboxApi


class FutureTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.r=Path(self.tmp.name)
  self.legacy=InboxQueue(self.r/'inbox_queue.json');self.legacy.enqueue('old-queued','old content never send')
  (self.r/'inbox_readiness_request.json').write_text('{"probe_id":"historical-hold"}')
  value=json.loads((LIVE/'.runtime/inbox_binding.json').read_text());value['components']=future.LOADED;value['identity']=binding.digest({k:v for k,v in value.items() if k!='identity'});binding.atomic(self.r/'inbox_binding.json',value)
  self.cfg={'schema':'inbox-future-only/1','build':future.BUILD,'state':'ACTIVE','lane_id':'a'*32,'binding':binding.public(value),'completion_cutoff':10,'request_cutoff':10,'legacy_queue_sha256':future.sha(self.legacy.path),'legacy_hold_sha256':future.sha(self.r/'inbox_readiness_request.json')}
  binding.atomic(self.r/'inbox_future.json',dict(self.cfg,seal=binding.digest(self.cfg)))
  with sqlite3.connect(self.r/'completions.sqlite3') as c:
   self.addCleanup(c.close)
   c.executescript('CREATE TABLE requests(request_id TEXT PRIMARY KEY,source TEXT); CREATE TABLE completions(sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT,request_id TEXT,result BLOB);')
   for i in range(1,11):c.execute('INSERT INTO requests VALUES(?,?)',('old'+str(i),'github'))
   c.execute('INSERT INTO completions VALUES(10,?,?,NULL)',('old-event','old10'))
  self.before=self.legacy.path.read_bytes();self.legacy._recovery_check=lambda:{'content':{'future_build':future.BUILD,'future_lane_seal':future.config(self.r)['seal']}}
  self.api=InboxApi(self.legacy);self.lane=self.api.future
 def event(self,rid,seq,old_request=False):
  response='verbatim `result` '+rid;h=future.sha256_text(response)
  payload={'request_id':rid,'response':response,'response_sha256':h}
  with sqlite3.connect(self.r/'completions.sqlite3') as c:
   self.addCleanup(c.close)
   if not old_request:c.execute('INSERT INTO requests VALUES(?,?)',(rid,'github'))
   c.execute('INSERT INTO completions VALUES(?,?,?,?)',(seq,'event-unique-server-'+rid,rid,json.dumps(payload).encode()))
  return {'delivery_id':rid+':'+h,'text':'[CODEX → CHATGPT]\n\n'+response}
 def claim(self):return self.api.local_next()[1]
 def proof(self,d,state='DELIVERED'):
  return {'delivery_id':d['delivery_id'],'claim_token':d['claim_token'],'authorization_id':d['authorization']['authorization_id'],'state':state,'observed_sha256':d['text_sha256'],'send_count':1,'new_user_turns':1,'composer_empty':True,'user_turn_uuid':'12345678-1234-1234-1234-123456789abc'}
 def permit(self,d):return self.lane.permit({k:d[k] for k in ('delivery_id','claim_token','text_sha256')}|{'authorization_id':d['authorization']['authorization_id'],'binding_identity':self.cfg['binding']['identity']})
 def test_real_source_positive_exact_send_and_dedupe_legacy_unchanged(self):
  body=self.event('new',11);self.assertEqual(self.api.post_inbox(body,True)[0],201);self.assertEqual(self.api.post_inbox(body,True)[0],200)
  d=self.claim();self.permit(d);self.assertEqual(self.api.local_ack(self.proof(d))[1]['state'],'DELIVERED');self.assertEqual(self.api.local_ack(self.proof(d))[0],200);self.assertIsNone(self.claim());self.assertEqual(self.legacy.path.read_bytes(),self.before)
 def test_old_completion_and_pre_activation_request_finishing_late_blocked(self):
  for b in (self.event('old1',9,True),self.event('old2',20,True)):
   self.assertEqual(self.api.post_inbox(b,True)[0],409)
  self.assertEqual(self.legacy.path.read_bytes(),self.before)
 def test_arbitrary_flag_wrong_payload_and_unknown_source_fail(self):
  body=self.event('fresh',11)
  self.assertEqual(self.api.post_inbox(body|{'future':True},True)[0],400)
  self.assertEqual(self.api.post_inbox(body|{'text':'altered'},True)[0],409)
  self.assertEqual(self.api.post_inbox({'delivery_id':'not-a-result','text':'forged'},True)[0],409)
 def test_oldest_missing_or_ambiguous_blocks_later_then_delivered_unblocks(self):
  a=self.event('a',11);b=self.event('b',12);self.api.post_inbox(b,True);self.assertIsNone(self.claim());self.api.post_inbox(a,True)
  d=self.claim();self.assertEqual(d['delivery_id'],a['delivery_id']);self.permit(d);self.api.local_ack(self.proof(d));self.assertEqual(self.claim()['delivery_id'],b['delivery_id'])
 def test_single_permit_and_restart_ambiguity_never_resend(self):
  b=self.event('new',11);self.api.post_inbox(b,True);d=self.claim();self.permit(d)
  with self.assertRaises(Conflict):self.permit(d)
  restarted=future.FutureLane(self.legacy);self.assertEqual(restarted.q._entries[b['delivery_id']]['state'],'NEEDS_REVIEW');self.assertIsNone(restarted.claim())
 def test_wrong_binding_or_uuid_never_delivers(self):
  self.api.post_inbox(self.event('new',11),True);d=self.claim();self.permit(d);bad=self.proof(d);bad['user_turn_uuid']='fallback-turn-2';self.assertEqual(self.api.local_ack(bad)[0],409)
  grant=copy.deepcopy(d['authorization']);grant['lane']['lane_id']='b'*32
  with self.assertRaises(Conflict):future.verify_envelope(grant,d,self.cfg['binding'],self.lane.q.clock(),runtime=self.r)
 def test_readiness_and_legacy_history_change_stop_before_claim(self):
  self.api.post_inbox(self.event('new',11),True);self.legacy._recovery_check=lambda:{'content':{}}
  with self.assertRaises(Conflict):self.claim()
  self.legacy.path.write_bytes(self.before+b' ')
  with self.assertRaises(Conflict):self.claim()
 def test_authenticated_event_annotation_is_checkpoint_derived(self):
  self.event('new',11);self.event('old2',12,True)
  events=[{'sequence':11,'request_id':'new'},{'sequence':12,'request_id':'old2'}]
  policy=future.annotate(self.r,events);self.assertEqual(policy['completion_cutoff'],10);self.assertEqual([e['future_eligible'] for e in events],[True,False])
  self.assertRegex(events[0]['future_result_sha256'],'^[0-9a-f]{64}$')
 def test_prepared_is_disabled_and_owner_activation_resnapshots_both_boundaries(self):
  import finish_future as owner
  v=future.config(self.r);v.pop('seal');v['state']='PREPARED';binding.atomic(self.r/'inbox_future.json',dict(v,seal=binding.digest(v)))
  before=self.event('created-before-activation',11)
  self.assertEqual(self.api.post_inbox(before,True)[0],409);self.assertIsNone(self.claim())
  prepared=future.config(self.r)
  def receipt():return {'observed_ms':__import__('time').time()*1000,'ready':True,'binding_identity':self.cfg['binding']['identity'],'content':{'future_build':future.BUILD,'future_lane_seal':prepared['seal']}}
  active=owner.activate_policy(self.r,prepared['seal'],6560156429,receipt)
  self.assertEqual((active['state'],active['completion_cutoff'],active['request_cutoff']),('ACTIVE',11,11))
  self.assertEqual(self.api.post_inbox(before,True)[0],409)
  self.assertEqual(self.api.post_inbox(self.event('created-after-activation',12),True)[0],201)
  with self.assertRaises(ValueError):owner.activate_policy(self.r,active['seal'],6560156429,receipt)
 def test_native_automatic_readiness_claim_permit_and_ack_without_owner_arm(self):
  spec=importlib.util.spec_from_file_location('future_native',STAGE/'inbox-v1/native-host/jarvis_inbox_host.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
  self.api.post_inbox(self.event('new',11),True)
  def wire(base,path,body=None):
   if path=='/local/inbox/next':return self.api.local_next()
   if path=='/local/inbox/ack':return self.api.local_ack(body)
   if path.endswith('/send-permit'):return 200,self.lane.permit(body)
   self.fail('unexpected transport path')
  t=host.Transport('http://127.0.0.1:18741',self.r/'native_journal.json',wire);identity=self.cfg['binding']['identity']
  self.assertEqual(t.handle({'cmd':'binding'})['future_lane']['lane_id'],'a'*32)
  probe=t.handle({'cmd':'poll','binding_identity':identity});self.assertEqual(probe['cmd'],'readiness_probe')
  content={k:True for k in ['reachable','bound','composer_present','composer_empty','ready']};content.update(generation_active=False,busy=False,reason='ready',binding_identity=identity,one_build=future.ONE_BUILD,future_build=future.BUILD,future_lane_seal=future.config(self.r)['seal'])
  msg={'cmd':'readiness_result','probe_id':probe['probe_id'],'binding_identity':identity,'build':binding.BUILD,'one_build':future.ONE_BUILD,'future_build':future.BUILD,'match_count':1,'matches':[{'id':1,'windowId':1,'url':'https://chatgpt.com/c/'+future.DEST,'hidden':False,'discarded':False,'incognito':False}],'truncated':False,'ready':True,'reason':'ready','content':content}
  self.assertEqual(t.handle(msg)['cmd'],'readiness_recorded')
  d=t.handle({'cmd':'poll','binding_identity':identity});self.assertEqual(d['cmd'],'delivery')
  self.assertTrue(t.handle({'cmd':'send_permit','delivery_id':d['delivery_id'],'authorization_id':d['authorization']['authorization_id']})['ok'])
  proof=self.proof(d);proof.pop('claim_token');proof.pop('authorization_id');proof['cmd']='result'
  self.assertEqual(t.handle(proof)['state'],'DELIVERED');self.assertEqual(self.legacy.path.read_bytes(),self.before)


if __name__=='__main__':unittest.main(verbosity=2)
