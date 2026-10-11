import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('retention_native',Path(__file__).resolve().parents[1]/'native-host/jarvis_inbox_host.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
import incident_retention as inc
class IncidentTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'inbox_verifier_trace.jsonl';self.did='held:'+('a'*64)
 def emit(self,event='sample',**kwargs):
  native.trace_event(self.path,dict(event=event,delivery_id=self.did,ts_ms=1,**kwargs))
 def final(self):return self.path.parent/'inbox_verifier_incidents'/(inc.key(self.did)+'.jsonl')
 def test_complete_v2_incident_and_ack(self):
  self.emit('baseline',build='inbox-v1-trace2-20261011-01',baseline_ids=['21a73100-224f-4068-b3a5-d2e10d1e3a53'])
  self.emit('send',deadline_ms=123)
  self.emit(candidates=[{'uuid':'21a73100-224f-4068-b3a5-d2e10d1e3a54','source':'bubble','in_baseline':False,'expected_sha256':'a'*64,'observed_sha256':'b'*64,'expected_len':20,'observed_len':21,'raw_len':22,'mismatch_index':3,'mismatch_window':'\\n','normalization':True}],conv_id='6acab580-d218-83ea-9598-0ff64dc33aa7',conv_changed=False,is_branch=None,bound=True)
  self.emit('terminal',state='NEEDS_REVIEW',reason='deadline')
  self.emit('native_outcome',state='NEEDS_REVIEW');self.emit('ack_committed',state='NEEDS_REVIEW')
  rows=[json.loads(l) for l in self.final().read_text().splitlines()]
  self.assertEqual([r['event'] for r in rows],['baseline','send','sample','terminal','native_outcome','ack_committed'])
  self.assertEqual(rows[2]['candidates'][0]['mismatch_index'],3)
  self.assertTrue(all(r['request_id']=='held' for r in rows))
 def test_real_rotation_stress_preserves_incident(self):
  self.emit('baseline');self.emit('terminal',state='NEEDS_REVIEW');original=self.final().read_bytes()
  for i in range(6000):native.trace_event(self.path,{'event':'sample','delivery_id':'later','sample':i,'reason':'x'*250})
  self.assertEqual(self.final().read_bytes(),original)
  self.assertEqual(len(list(self.path.parent.glob('inbox_verifier_trace.jsonl*'))),4)
  self.assertNotIn(self.did,''.join(p.read_text() for p in self.path.parent.glob('inbox_verifier_trace.jsonl*')))
 def test_success_has_no_retained_bundle(self):
  self.emit();self.emit('native_outcome',state='DELIVERED');self.emit('ack_committed',state='DELIVERED')
  self.assertFalse(self.final().exists());self.assertEqual(list(self.final().parent.joinpath('active').glob('*')),[])
 def test_privacy(self):
  self.emit(text='FULL SECRET PAYLOAD');self.emit(candidates=[{'text':'FULL SECRET PAYLOAD'}]);self.emit('terminal',state='NEEDS_REVIEW')
  self.assertNotIn('FULL SECRET PAYLOAD',self.final().read_text())
 def test_persistence_failure_outcome_unchanged(self):
  t=native.Transport('http://127.0.0.1:18741',self.path.parent/'journal.json',lambda *a:(200,{'ok':True,'state':'NEEDS_REVIEW'}))
  t.pending={'delivery':{'delivery_id':self.did,'claim_token':'secret'},'outcome':None}
  with patch.object(native,'retain',side_effect=OSError('disk unavailable')):
   self.assertEqual(t.handle({'cmd':'result','delivery_id':self.did,'state':'NEEDS_REVIEW','error':'timeout'})['state'],'NEEDS_REVIEW')
  self.assertIsNone(t.pending)
 def test_age_cleanup(self):
  root=self.final().parent;root.mkdir();p=root/'old.jsonl';p.write_text('{}');import os;os.utime(p,(0,0))
  inc.cleanup(root,inc.MAX_AGE+1);self.assertFalse(p.exists())
 def test_count_and_byte_cleanup_preserves_young(self):
  root=self.final().parent;root.mkdir();import os
  for i in range(3):
   p=root/(str(i)+'.jsonl');p.write_bytes(b'x'*20);os.utime(p,(i,i))
  with patch.object(inc,'MAX_INCIDENTS',2),patch.object(inc,'MAX_TOTAL_BYTES',40):
   self.assertTrue(inc.cleanup(root,inc.MIN_AGE+10));self.assertEqual(len(list(root.glob('*.jsonl'))),2)
   self.assertFalse(inc.cleanup(root,inc.MIN_AGE+10,reserve=50))
  p=root/'young.jsonl';p.write_bytes(b'x'*20);os.utime(p,(100000,100000))
  with patch.object(inc,'MAX_INCIDENTS',0):
   self.assertFalse(inc.cleanup(root,100001));self.assertTrue(p.exists())
 def test_incident_overflow_explicit(self):
  with patch.object(inc,'MAX_INCIDENT_BYTES',70000):
   for i in range(80):self.emit(reason='x'*250)
   self.emit('terminal',state='NEEDS_REVIEW')
   self.assertLessEqual(self.final().stat().st_size,70000);self.assertIn('incident_truncated',self.final().read_text())
 def test_partial_stage_recovers_without_corrupting_other_incident(self):
  self.emit('baseline');stage=self.final().parent/'active'/(inc.key(self.did)+'.jsonl')
  with stage.open('ab') as f:f.write(b'{partial')
  self.emit('terminal',state='NEEDS_REVIEW')
  rows=[json.loads(l) for l in self.final().read_text().splitlines()];self.assertEqual(len(rows),2)
 def test_atomic_update_failure_preserves_final(self):
  self.emit('terminal',state='NEEDS_REVIEW');before=self.final().read_bytes()
  with patch.object(inc.os,'replace',side_effect=OSError('failed replace')):self.emit('ack_committed',state='NEEDS_REVIEW')
  self.assertEqual(self.final().read_bytes(),before);self.assertEqual(list(self.final().parent.glob('*.tmp')),[])
 def test_path_identity_safe(self):
  self.did='../escape:abc';self.emit('terminal',state='NEEDS_REVIEW');self.assertTrue(self.final().exists());self.assertEqual(len(self.final().stem),64)
 def test_restart_unknown_outcome_retained(self):
  journal=self.path.parent/'journal.json';d={'cmd':'delivery','delivery_id':'a','text':'text','text_sha256':native.sha256_text('text'),'claim_token':'token','attempt_count':1}
  native.journal_write(journal,{'delivery':d,'outcome':None});native.Transport('http://127.0.0.1:18741',journal)
  self.assertTrue((self.final().parent/(inc.key('a')+'.jsonl')).exists())
if __name__=='__main__':unittest.main()
