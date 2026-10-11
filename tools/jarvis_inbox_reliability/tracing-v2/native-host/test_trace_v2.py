"""Windows v2 schema tests against the installed production native host.
The committed handoff omitted its documented Python test file.
"""
import importlib.util,json,tempfile,unittest
from pathlib import Path
production=Path(__file__).resolve().parents[5]/'bridge/inbox-v1/native-host/jarvis_inbox_host.py'
spec=importlib.util.spec_from_file_location('trace_v2_native',production)
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
class TraceV2Tests(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.path=Path(tmp.name)/'inbox_verifier_trace.jsonl'
  self.event={'build':'inbox-v1-trace2-20261011-01','event':'sample','delivery_id':'test:'+('a'*64),'ts_ms':1,'conv_id':'6acab580-d218-83ea-9598-0ff64dc33aa7','conv_changed':False,'is_branch':None,'candidates':[{'uuid':'8e8126f2-eb9b-41a7-8b02-746dfc18f07d','in_baseline':False,'canonical_match':False,'hash_match':None,'source':'bubble','expected_sha256':'a'*64,'observed_sha256':'b'*64,'expected_len':100,'observed_len':99,'raw_len':99,'mismatch_index':20,'mismatch_window':'diff@20: U+0061!=U+0062','normalization':'none'}]}
 def write(self):native.trace_event(self.path,self.event)
 def test_all_new_fields_roundtrip(self):
  self.write();r=json.loads(self.path.read_text());self.assertEqual(r['candidates'],self.event['candidates']);self.assertEqual(r['conv_id'],self.event['conv_id'])
 def test_invalid_conversation_rejected(self):
  self.event['conv_id']='https://example.com/private';self.write();self.assertFalse(self.path.exists())
 def test_changed_requires_bool_or_null(self):
  self.event['conv_changed']='yes';self.write();self.assertFalse(self.path.exists())
 def test_branch_requires_bool_or_null(self):
  self.event['is_branch']=1;self.write();self.assertFalse(self.path.exists())
 def test_unknown_branch_is_null(self):
  self.event['conv_id']=None;self.write();self.assertIsNone(json.loads(self.path.read_text())['is_branch'])
 def test_window_bounds(self):
  self.event['candidates'][0]['mismatch_window']='x'*60;self.write();self.assertEqual(len(json.loads(self.path.read_text())['candidates'][0]['mismatch_window']),60)
  self.event['candidates'][0]['mismatch_window']='x'*81;self.write();self.assertEqual(len(self.path.read_text().splitlines()),1)
 def test_full_payload_field_rejected(self):
  self.event['candidates'][0]['text']='PRIVATE PAYLOAD';self.write();self.assertFalse(self.path.exists())
 def test_v1_compatibility_and_failure_observational(self):
  native.trace_event(self.path,{'event':'sample','bound':True});self.assertTrue(json.loads(self.path.read_text())['bound'])
  transport=native.Transport('http://127.0.0.1:18741',self.path.parent/'journal.json',lambda *a:(204,None));transport.trace_path=self.path.parent
  self.assertEqual(transport.handle({'cmd':'verifier_trace','event':self.event}),{'cmd':'trace_recorded'});self.assertIsNone(transport.pending);self.assertFalse(transport.path.exists())
if __name__=='__main__':unittest.main()
