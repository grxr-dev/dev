import copy,hashlib,json,sqlite3,sys,tempfile,threading,unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from inbox_queue import InboxQueue,Conflict,FAILED_PERMANENT,QUEUED,DELIVERING
from inbox_supersession import *
TEXT="""[JARVIS CONTINUITY WATCHDOG]

Brain Age continuity check: the latest task has completed and no successor task exists yet. Please review the GitHub result and continue from the latest safe boundary.

- task: brainage-task-aw10-20261015-01
- issue: #70 ([CODEX RELAY] brainage-task-aw10-20261015-01)
- result: PARTIAL
- commit: c699e3a21207abaa72b8130bf54c0f189c846412
- completed: 2026-10-15T19:22:38Z"""
class FakeGH:
 def __init__(self):self.issues={};self.actor='grxr-dev';self.private_ok=True
 def private(self):
  if not self.private_ok:raise BusError('not private')
 def call(self,path):
  if path=='user':return {'login':self.actor}
  return copy.deepcopy(self.issues[int(path.rsplit('/',1)[1])])
class SupersessionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.base=datetime(2026,10,15,tzinfo=timezone.utc);self.now=(self.base+timedelta(hours=1.5)).timestamp()
  self.q=InboxQueue(self.root/'queue.json',clock=lambda:self.now);self.q.enqueue(WATCHDOG,TEXT);self.old=self.q.get(WATCHDOG);self.client=FakeGH()
  db=sqlite3.connect(self.root/'completions.sqlite3');db.executescript('CREATE TABLE requests(request_id TEXT PRIMARY KEY,state TEXT,source TEXT,source_ref TEXT,github_issue_number INTEGER,result_available INTEGER,terminal_reason TEXT,result_sha256 TEXT,prompt_sha256 TEXT);CREATE TABLE completions(request_id TEXT,sequence INTEGER,status TEXT,completed_at TEXT,result BLOB,result_bytes INTEGER,failure TEXT,unavailable_reason TEXT);')
  prior=None
  for i,(n,issue,commit) in enumerate(TASKS):
   req='brainage-task-aw'+str(n)+'-20261015-01';created=self.base+timedelta(hours=i*2);completed=created+timedelta(hours=1);closed=completed+timedelta(seconds=5)
   iso=lambda t:t.isoformat().replace('+00:00','Z')
   message='[CHATGPT \u2192 CODEX]\nFixture '+(prior or 'root')
   body='---\ncodex_relay_version: 1\nrequest_id: '+req+'\nthread_key: main\nroute_id: sol-high\n---\n'+message
   self.client.issues[issue]={'number':issue,'state':'closed','user':{'login':'grxr-dev'},'title':'[CODEX RELAY] '+req,'body':body,'created_at':iso(created),'closed_at':iso(closed)}
   response='Fixture commit '+commit;sha=hashlib.sha256(response.encode()).hexdigest();raw=json.dumps({'request_id':req,'ok':True,'status':'completed','response':response,'response_sha256':sha}).encode()
   db.execute('insert into requests values(?,?,?,?,?,?,?,?,?)',(req,'COMPLETED','github',REPO+'#'+str(issue),issue,1,'completed',sha,hashlib.sha256(message.encode()).hexdigest()));db.execute('insert into completions values(?,?,?,?,?,?,?,?)',(req,i+1,'completed',iso(completed),raw,len(raw),None,None));prior=commit
  db.commit();db.close();self.policy=SupersessionPolicy(self.root,self.client);self.admin=SupersessionAdmin(self.q,self.policy);self.fp=self.q.fingerprint();self.proof=self.policy.verify();self.psha=proof_sha(self.proof)
 def tearDown(self):self.tmp.cleanup()
 def cancel(self,**updates):
  body={'delivery_id':WATCHDOG,'expected_fingerprint':self.fp,'expected_proof_sha256':self.psha};body.update(updates);return self.admin.cancel(body)
 def change_db(self,sql,args=()):
  db=sqlite3.connect(self.root/'completions.sqlite3')
  try:db.execute(sql,args);db.commit()
  finally:db.close()
 def test_success_never_delivers_or_attempts(self):
  r=self.cancel();e=self.q.get(WATCHDOG);self.assertEqual(r['disposition'],'SUPERSEDED');self.assertFalse(r['delivered']);self.assertEqual(e['state'],FAILED_PERMANENT);self.assertEqual(e['attempt_count'],0);self.assertIsNone(e['delivered_at']);self.assertIsNone(e['last_attempt_at']);self.assertIsNone(e['claim_token']);self.assertIsNone(self.q.claim_next())
 def test_history_survives_restart(self):
  self.cancel();q=InboxQueue(self.q.path);self.assertEqual(q._supersession['entry_before'],self.old);self.assertEqual(q.get(WATCHDOG)['text'],TEXT);self.assertEqual(q.get(WATCHDOG)['outcome']['state'],'SUPERSEDED');self.assertEqual(q._supersession['proof_sha256'],self.psha)
 def test_wrong_id(self):
  with self.assertRaises(Conflict):self.cancel(delivery_id='another')
 def test_wrong_content_hash(self):
  with patch('inbox_supersession.HASH','0'*64):
   with self.assertRaises(Conflict):self.cancel()
 def test_attempted_or_nonqueued_rejected(self):
  e=self.q.claim_next();self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.cancel()
  self.assertEqual(self.q.get(WATCHDOG),e)
 def test_stale_queue(self):
  self.q.enqueue('other','leave alone')
  with self.assertRaises(Conflict):self.cancel()
 def test_unrelated_entry_preserved_and_not_claimed(self):
  self.q.enqueue('other','leave alone');before=self.q.get('other');self.fp=self.q.fingerprint();self.cancel();self.assertEqual(self.q.get('other'),before)
 def test_duplicate_rejected(self):
  self.cancel();self.fp=self.q.fingerprint()
  with self.assertRaises(Conflict):self.cancel()
 def test_concurrent_one_atomic_disposition(self):
  def run(_):
   try:self.cancel();return True
   except Conflict:return False
  with ThreadPoolExecutor(max_workers=8) as pool:self.assertEqual(sum(pool.map(run,range(8))),1)
 def test_wrong_expected_proof(self):
  with self.assertRaises(Conflict):self.cancel(expected_proof_sha256='0'*64)
 def test_incomplete_successor(self):
  self.change_db("update requests set state='RUNNING' where github_issue_number=78")
  with self.assertRaises(Conflict):self.cancel()
  self.assertEqual(self.q.get(WATCHDOG),self.old)
 def test_missing_successor_result(self):
  self.change_db("delete from completions where sequence=4")
  with self.assertRaises(Conflict):self.cancel()
 def test_corrupt_result_hash(self):
  self.change_db("update requests set result_sha256=? where github_issue_number=76",('0'*64,))
  with self.assertRaises(Conflict):self.cancel()
 def test_wrong_local_provenance(self):
  self.change_db("update requests set source_ref='elsewhere' where github_issue_number=74")
  with self.assertRaises(Conflict):self.cancel()
 def test_wrong_remote_author(self):
  self.client.issues[74]['user']['login']='other'
  with self.assertRaises(Conflict):self.cancel()
 def test_open_remote_successor(self):
  self.client.issues[78]['state']='open'
  with self.assertRaises(Conflict):self.cancel()
 def test_wrong_remote_actor_private_or_dependency(self):
  self.client.actor='other'
  with self.assertRaises(Conflict):self.cancel()
  self.client.actor='grxr-dev';self.client.private_ok=False
  with self.assertRaises(Conflict):self.cancel()
  self.client.private_ok=True;self.client.issues[76]['body']=self.client.issues[76]['body'].replace(TASKS[1][2],'missing')
  with self.assertRaises(Conflict):self.cancel()
 def test_wrong_timestamp_order(self):
  self.client.issues[74]['created_at']=self.client.issues[70]['created_at']
  with self.assertRaises(Conflict):self.cancel()
 def test_disk_failure_preserves_queue_and_history(self):
  before=self.q.path.read_bytes()
  with patch.object(self.q,'_commit',side_effect=OSError('disk')):
   with self.assertRaises(OSError):self.cancel()
  self.assertEqual(self.q.get(WATCHDOG),self.old);self.assertEqual(self.q.path.read_bytes(),before);self.assertIsNone(self.q._supersession)
 def test_corrupt_disposition_rejected_without_rewrite(self):
  self.cancel();raw=json.loads(self.q.path.read_text());raw['entries'][WATCHDOG]['attempt_count']=1;self.q.path.write_text(json.dumps(raw));before=self.q.path.read_bytes()
  with self.assertRaises(ValueError):InboxQueue(self.q.path)
  self.assertEqual(self.q.path.read_bytes(),before)
 def test_normal_schema_unchanged_until_used(self):self.assertEqual(set(json.loads(self.q.path.read_text())),{'version','entries'})
class HttpSupersessionTests(unittest.TestCase):
 def setUp(self):
  self.f=SupersessionTests();self.f.setUp()
  from inbox_api import InboxApi
  from inbox_local import LocalInboxServer
  self.server=LocalInboxServer(0,InboxApi(self.f.q));self.server.supersession=SupersessionAdmin(self.f.q,self.f.policy);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.f.tearDown()
 def call(self,body=None,auth=True,origin=None):
  from http.client import HTTPConnection
  h={'X-Jarvis-Local':'1'}
  if auth:h['X-Jarvis-Admin']=self.server.recovery.token
  if origin:h['Origin']=origin
  raw=None
  if body is not None:raw=json.dumps(body);h['Content-Type']='application/json'
  c=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5);c.request('GET' if body is None else 'POST','/local/inbox/admin/supersede-watchdog',raw,h);r=c.getresponse();data=r.read();status=r.status;c.close();return status,json.loads(data)
 def test_admin_required(self):self.assertEqual(self.call(auth=False)[0],403)
 def test_browser_origin_denied(self):self.assertEqual(self.call(origin='https://chatgpt.com')[0],403)
 def test_reviewed_proof_atomic_cancel_once(self):
  status,r=self.call();self.assertEqual(status,200);self.assertTrue(r['evidence_verified']);body={'delivery_id':WATCHDOG,'expected_fingerprint':r['queue_fingerprint'],'expected_proof_sha256':r['proof_sha256']}
  self.assertEqual(self.call(body)[1]['disposition'],'SUPERSEDED');self.assertEqual(self.call(body)[0],409);self.assertEqual(self.f.q.get(WATCHDOG)['attempt_count'],0)
 def test_wrong_id_and_schema_denied(self):
  body={'delivery_id':'other','expected_fingerprint':self.f.fp,'expected_proof_sha256':self.f.psha};self.assertEqual(self.call(body)[0],409);body['arbitrary_action']='send';self.assertEqual(self.call(body)[0],400)
 def test_proof_failure_never_changes_queue(self):
  self.f.client.issues[78]['state']='open';body={'delivery_id':WATCHDOG,'expected_fingerprint':self.f.fp,'expected_proof_sha256':self.f.psha};self.assertEqual(self.call(body)[0],409);self.assertEqual(self.f.q.get(WATCHDOG),self.f.old)
if __name__=='__main__':unittest.main()
