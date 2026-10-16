import copy,json,sys,tempfile,threading,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from inbox_queue import *
from inbox_wire import sha256_text
from inbox_recovery import RecoveryAdmin,TARGET
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.now=1000
  self.patch=patch('inbox_recovery.TEXT_SHA256',sha256_text('fixture only'));self.patch.start()
  self.q=InboxQueue(self.root/'queue.json',clock=lambda:self.now);self.q.enqueue(TARGET,'fixture only')
  for i in range(3):
   self.now+=200;e=self.q.claim_next();self.q.ack(TARGET,FAILED_RETRYABLE,'exactly one already-open bound tab required',claim_token=e['claim_token'],pre_send=True)
  self.old=self.q.get(TARGET);self.admin=RecoveryAdmin(self.q);self.probe='1'*32;self.ready();self.fp=self.q.fingerprint()
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def ready(self,**updates):
  r=dict(probe_id=self.probe,build='inbox-readiness-20261015-01',observed_ms=self.now*1000,native_pid=123,match_count=1,truncated=False,ready=True,reason='ready',matches=[dict(id=755,windowId=5761,url='https://chatgpt.com/c/6acab580-d218-83ea-9598-0ff64dc33aa7',hidden=False,discarded=False,incognito=False)],content=dict(reachable=True,bound=True,composer_present=True,composer_empty=True,ready=True,busy=False,generation_active=False))
  r.update(updates);(self.root/'inbox_readiness_result.json').write_text(json.dumps(r));(self.root/'inbox_readiness_request.json').write_text(json.dumps({'probe_id':self.probe}))
 def arm(self,**updates):
  body=dict(delivery_id=TARGET,expected_fingerprint=self.fp);body.update(updates);return self.admin.recover(body)
 def claim(self):self.arm();return self.q.claim_next()
 def test_success_exactly_one_extra_normal_verified_delivery(self):
  r=self.arm();self.assertEqual(r['max_total_attempts'],4);self.assertEqual(self.q.get(TARGET)['attempt_count'],3)
  e=self.q.claim_next();self.assertEqual(e['attempt_count'],4);self.assertEqual(e['delivery_id'],TARGET)
  self.q.ack(TARGET,DELIVERED,claim_token=e['claim_token'],observed_sha256=e['text_sha256'],send_count=1,new_user_turns=1,composer_empty=True)
  self.assertEqual(self.q.get(TARGET)['state'],DELIVERED);self.assertIsNone(self.q.claim_next());self.assertEqual(self.q._recovery['status'],'FINISHED')
 def test_wrong_id(self):
  with self.assertRaises(Conflict):self.arm(delivery_id='different')
  self.assertIsNone(self.q._recovery)
 def test_wrong_payload_identity(self):
  with patch('inbox_recovery.TEXT_SHA256','0'*64):
   with self.assertRaises(Conflict):self.arm()
 def test_nonterminal_rejected(self):
  e=copy.deepcopy(self.q._entries);e[TARGET]['state']=QUEUED;self.q._commit(e);self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.arm()
 def test_ambiguous_terminal_cannot_be_rearmed(self):
  e=copy.deepcopy(self.q._entries);e[TARGET]['state']=NEEDS_REVIEW;self.q._commit(e);self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.arm()
 def test_duplicate_recovery_even_after_new_fingerprint(self):
  self.arm();self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.arm()
 def test_stale_state(self):
  self.q.enqueue('other','test')
  with self.assertRaises(Conflict):self.arm()
 def test_other_work_blocks_even_with_current_fingerprint(self):
  self.q.enqueue('other','test');self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.arm()
 def test_concurrent_calls_one_authorization(self):
  def run(_):
   try:self.arm();return True
   except Conflict:return False
  with ThreadPoolExecutor(max_workers=8) as pool:self.assertEqual(sum(pool.map(run,range(8))),1)
  self.assertEqual(sum(e['event']=='authorized' for e in self.q._recovery['events']),1)
 def test_extra_pre_send_failure_exhausts_without_retry(self):
  e=self.claim();self.q.ack(TARGET,FAILED_RETRYABLE,'draft appeared',claim_token=e['claim_token'],pre_send=True)
  self.assertEqual(self.q.get(TARGET)['attempt_count'],4);self.assertEqual(self.q.get(TARGET)['state'],FAILED_PERMANENT);self.now+=100000
  self.assertIsNone(self.q.claim_next())
  with self.assertRaises(Conflict):self.arm()
 def test_extra_ambiguous_failure_never_retries(self):
  e=self.claim();self.q.ack(TARGET,NEEDS_REVIEW,'unknown Send',claim_token=e['claim_token']);self.now+=100000;self.assertIsNone(self.q.claim_next())
 def test_full_history_preserved_restart_and_idempotent_ack(self):
  e=self.claim();self.q.ack(TARGET,FAILED_PERMANENT,'pre-send no candidate',claim_token=e['claim_token'],pre_send=True)
  prior=copy.deepcopy(self.q._recovery);self.q.ack(TARGET,FAILED_PERMANENT,'pre-send no candidate',claim_token=e['claim_token'],pre_send=True)
  self.assertEqual(self.q._recovery,prior);q=InboxQueue(self.q.path,clock=lambda:self.now)
  self.assertEqual(q._recovery['entry_before'],self.old);self.assertEqual(q.get(TARGET)['text'],self.old['text']);self.assertEqual(q.get(TARGET)['created_at'],self.old['created_at']);self.assertEqual(q.get(TARGET)['attempt_count'],4)
  self.assertEqual([e['event'] for e in q._recovery['events']],['authorized','armed','claimed','outcome'])
 def test_restart_before_claim_cancels_without_execution(self):
  self.arm();q=InboxQueue(self.q.path,clock=lambda:self.now);self.assertEqual(q.get(TARGET)['state'],FAILED_PERMANENT);self.assertEqual(q._recovery['status'],'CANCELLED');self.assertIsNone(q.claim_next())
 def test_restart_after_claim_requires_review(self):
  self.claim();q=InboxQueue(self.q.path,clock=lambda:self.now);self.assertEqual(q.get(TARGET)['state'],NEEDS_REVIEW);self.assertIsNone(q.claim_next())
 def test_stale_readiness_at_authorization(self):
  self.now+=61
  with self.assertRaises(Conflict):self.arm()
  self.assertEqual(self.q.get(TARGET),self.old)
 def test_invalid_bound_tab_readiness(self):
  for update in [dict(match_count=2),dict(match_count=True),dict(native_pid=None),dict(ready=False),dict(observed_ms=(self.now+20)*1000)]:
   self.ready(**update)
   with self.assertRaises(Conflict):self.arm()
 def test_readiness_rechecked_at_claim(self):
  self.arm();self.now+=61
  with self.assertRaises(Conflict):self.q.claim_next()
  self.assertEqual(self.q.get(TARGET)['attempt_count'],3)
 def test_queue_change_after_authorization_blocks_claim(self):
  self.arm();self.q.enqueue('other','new')
  with self.assertRaises(Conflict):self.q.claim_next()
  self.assertEqual(self.q.get(TARGET)['attempt_count'],3)
 def test_missing_validator_blocks_claim(self):
  self.arm();self.q._recovery_check=None
  with self.assertRaises(Conflict):self.q.claim_next()
 def test_persistence_failure_does_not_publish_authorization(self):
  with patch.object(self.q,'_commit',side_effect=OSError('disk')):
   with self.assertRaises(OSError):self.arm()
  self.assertEqual(self.q.get(TARGET),self.old);self.assertIsNone(self.q._recovery);self.assertTrue((self.root/'inbox_readiness_request.json').exists())
 def test_release_failure_preserves_before_history_and_cancels(self):
  with patch.object(self.admin,'release_hold',side_effect=OSError('hold')):
   with self.assertRaises(OSError):self.arm()
  self.assertEqual(self.q.get(TARGET),self.old);self.assertEqual(self.q._recovery['entry_before'],self.old);self.assertEqual(self.q._recovery['status'],'CANCELLED');self.assertIsNone(self.q.claim_next())
 def test_second_commit_failure_never_leaves_claimable_prepared(self):
  original=self.q._commit;n=0
  def commit(*a,**k):
   nonlocal n;n+=1
   if n==2:raise OSError('second commit')
   return original(*a,**k)
  with patch.object(self.q,'_commit',side_effect=commit):
   with self.assertRaises(OSError):self.arm()
  self.assertIsNone(self.q.claim_next());self.assertEqual(self.q._recovery['entry_before'],self.old)
 def test_prior_trace_evidence_captured_before_authorization(self):
  record={'delivery_id':TARGET,'event':'native_outcome','state':FAILED_RETRYABLE,'ts_ms':123}
  path=self.root/'inbox_verifier_trace.jsonl';raw=json.dumps(record)+'\n';path.write_text(raw)
  self.arm();saved=self.q._recovery['prior_evidence'];self.assertEqual(saved['records'][0]['record'],record)
  path.write_text('later unrelated rotation')
  self.assertEqual(self.q._recovery['prior_evidence'],saved)
 def test_corrupt_armed_state_rejected_without_startup_mutation(self):
  self.arm();raw=json.loads(self.q.path.read_text());raw['entries'][TARGET]['state']=DELIVERED
  self.q.path.write_text(json.dumps(raw));before=self.q.path.read_bytes()
  with self.assertRaises(ValueError):InboxQueue(self.q.path,clock=lambda:self.now)
  self.assertEqual(self.q.path.read_bytes(),before)
 def test_unused_queue_schema_and_budget_unchanged(self):
  self.assertEqual(set(json.loads(self.q.path.read_text())),{'version','entries'});self.assertEqual(self.q.get(TARGET)['attempt_count'],3);self.assertIsNone(self.q.claim_next())
class HttpRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.fixture=RecoveryTests();self.fixture.setUp();self.q=self.fixture.q
  from inbox_api import InboxApi
  from inbox_local import LocalInboxServer
  self.server=LocalInboxServer(0,InboxApi(self.q));self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.fixture.tearDown()
 def call(self,path='/local/inbox/admin/recovery-once',body=None,admin=True,origin=None):
  from http.client import HTTPConnection
  headers={'X-Jarvis-Local':'1'}
  if admin:headers['X-Jarvis-Admin']=self.server.recovery.token
  if origin:headers['Origin']=origin
  raw=None
  if body is not None:raw=json.dumps(body);headers['Content-Type']='application/json'
  c=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5);c.request('GET' if body is None else 'POST',path,body=raw,headers=headers);r=c.getresponse();raw=r.read();status=r.status;c.close();return status,json.loads(raw) if raw else None
 def test_admin_required_even_for_status(self):self.assertEqual(self.call(admin=False)[0],403)
 def test_origin_rejected_with_valid_admin_token(self):self.assertEqual(self.call(origin='https://chatgpt.com')[0],403)
 def test_fixed_target_and_extra_fields_rejected(self):
  body={'delivery_id':'wrong','expected_fingerprint':self.q.fingerprint()};self.assertEqual(self.call(body=body)[0],409)
  body['delivery_id']=TARGET;body['arbitrary_action']='send';self.assertEqual(self.call(body=body)[0],400)
 def test_status_authorize_normal_claim_ack_flow(self):
  status,r=self.call();self.assertEqual(status,200);self.assertTrue(r['ready'])
  body={'delivery_id':TARGET,'expected_fingerprint':r['queue_fingerprint']}
  self.assertEqual(self.call(body=body)[0],200);self.assertEqual(self.call(body=body)[0],409)
  status,d=self.call(path='/local/inbox/next',admin=False);self.assertEqual(status,200);self.assertEqual(d['attempt_count'],4)
  ack=dict(delivery_id=TARGET,claim_token=d['claim_token'],state=DELIVERED,observed_sha256=d['text_sha256'],send_count=1,new_user_turns=1,composer_empty=True)
  self.assertEqual(self.call(path='/local/inbox/ack',body=ack,admin=False)[1]['state'],DELIVERED)
  self.assertEqual(self.call(path='/local/inbox/next',admin=False)[0],204)
 def test_stale_readiness_returns_conflict_without_rearm(self):
  self.fixture.now+=61;body={'delivery_id':TARGET,'expected_fingerprint':self.q.fingerprint()};self.assertEqual(self.call(body=body)[0],409);self.assertEqual(self.q.get(TARGET),self.fixture.old)
 def test_unknown_routes_still_rejected(self):self.assertEqual(self.call(path='/local/inbox/arbitrary')[0],404)
if __name__=='__main__':unittest.main()
