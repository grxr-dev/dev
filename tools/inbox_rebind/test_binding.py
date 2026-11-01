"""Recipient-only tests: every transport HTTP/Send/ACK path is forbidden."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
BRIDGE=ROOT/'bridge'
sys.path[:0]=[str(BRIDGE),str(BRIDGE/'inbox-v1/native-host')]
import inbox_binding as binding
from readiness_diagnostic import ReadinessDiagnostic
spec=importlib.util.spec_from_file_location('rebind_host',BRIDGE/'inbox-v1/native-host/jarvis_inbox_host.py')
host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
NEW='6ae5615a-0720-83ea-a43b-82386ce031e5'
NONCE='1'*32


class BindingTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for name,value in [('inbox_readiness_request.json',{'probe_id':'a'*32}),('inbox_native_recovery.json',None),('inbox_queue.json',{'historical':'never mutate'})]:
   (self.root/name).write_text(json.dumps(value))
  self.before={path.name:path.read_bytes() for path in self.root.iterdir()}
 def tearDown(self):self.temp.cleanup()
 def bind(self):return binding.change(self.root,NEW,binding.LEGACY,'LEGACY_UNCONFIGURED')[0]
 def unchanged(self):
  for name,expected in self.before.items():self.assertEqual((self.root/name).read_bytes(),expected)
 def test_explicit_bootstrap_and_no_history_mutation(self):
  value=self.bind();self.assertEqual(value['conversation_id'],NEW);self.assertEqual(value['delivery_policy'],'HOLD');self.unchanged()
 def test_idempotent_same_command_no_write(self):
  value=self.bind();before=binding.path_for(self.root).read_bytes()
  same,changed=binding.change(self.root,NEW,binding.LEGACY,'LEGACY_UNCONFIGURED')
  self.assertFalse(changed);self.assertEqual(same,value);self.assertEqual(binding.path_for(self.root).read_bytes(),before)
 def test_stale_expected_id_or_hash_rejects(self):
  self.bind()
  for expected_id,identity in [(NEW,'0'*64),(binding.LEGACY,'1'*64)]:
   with self.subTest(identity=identity),self.assertRaises(ValueError):binding.change(self.root,binding.LEGACY,expected_id,identity)
 def test_invalid_targets_fail_closed(self):
  for target in ['https://evil.example/c/'+NEW,'https://chatgpt.com/c/'+NEW+'?x=1',NEW+'/',NEW+'#x','active',NEW.upper()]:
   with self.subTest(target=target),self.assertRaises(ValueError):binding.change(self.root,target,binding.LEGACY,'LEGACY_UNCONFIGURED')
  self.assertFalse(binding.path_for(self.root).exists());self.unchanged()
 def test_missing_hold_or_pending_journal_blocks(self):
  (self.root/'inbox_readiness_request.json').unlink()
  with self.assertRaises(ValueError):self.bind()
  (self.root/'inbox_readiness_request.json').write_text('{}')
  (self.root/'inbox_native_recovery.json').write_text('{"pending":true}')
  with self.assertRaises(ValueError):self.bind()
 def test_atomic_failure_preserves_previous_binding(self):
  first=self.bind();before=binding.path_for(self.root).read_bytes()
  with patch('inbox_binding.os.replace',side_effect=OSError('failure')):
   with self.assertRaises(OSError):binding.change(self.root,binding.LEGACY,NEW,first['identity'],True)
  self.assertEqual(binding.path_for(self.root).read_bytes(),before)
 def test_rollback_new_epoch_monotonic_and_hold(self):
  first=self.bind();rolled,changed=binding.change(self.root,binding.LEGACY,NEW,first['identity'],True)
  self.assertTrue(changed);self.assertEqual(rolled['generation'],2);self.assertNotEqual(first['epoch'],rolled['epoch']);self.assertEqual(rolled['delivery_policy'],'HOLD');self.unchanged()
 def test_rollback_wrong_target_rejected(self):
  first=self.bind()
  with self.assertRaises(ValueError):binding.change(self.root,'11111111-1111-1111-1111-111111111111',NEW,first['identity'],True)
 def test_corrupt_duplicate_or_partial_binding_rejected(self):
  for text in ['{','{"schema":1,"schema":1}', '{}']:
   binding.path_for(self.root).write_text(text)
   with self.subTest(text=text),self.assertRaises(ValueError):binding.load(self.root)
 def test_new_process_persistent_readback(self):
  value=self.bind()
  code='import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from inbox_binding import load;print(load(Path(sys.argv[2]))["identity"])'
  result=subprocess.run([sys.executable,'-X','utf8','-c',code,str(BRIDGE),str(self.root)],capture_output=True,text=True,check=True)
  self.assertEqual(result.stdout.strip(),value['identity']);self.unchanged()
 def test_native_old_client_and_wrong_epoch_cannot_claim(self):
  value=self.bind();transport=host.Transport('http://127.0.0.1:18741',self.root/'inbox_native_recovery.json',lambda *args:self.fail('HTTP forbidden'))
  self.assertEqual(transport.handle({'cmd':'poll'})['cmd'],'binding_config')
  self.assertEqual(transport.handle({'cmd':'binding'})['binding'],binding.public(value))
  for message in [{'cmd':'poll','binding_identity':'0'*64},{'cmd':'result','delivery_id':'historical'},{'cmd':'poll','binding_identity':value['identity']}]:
   self.assertTrue(transport.handle(message)['readiness_hold'])
  transport.disconnect();self.unchanged()
 def test_native_pending_recovery_never_acks(self):
  self.bind();transport=host.Transport('http://127.0.0.1:18741',self.root/'inbox_native_recovery.json',lambda *args:self.fail('ACK forbidden'))
  transport.pending={'delivery':{},'outcome':None}
  self.assertTrue(transport.recover_ack()['readiness_hold']);transport.disconnect();self.unchanged()
 def result(self,value):
  return {'cmd':'readiness_result','probe_id':NONCE,'binding_identity':value['identity'],'build':binding.BUILD,'match_count':1,
   'matches':[{'id':1,'windowId':2,'url':'https://chatgpt.com/c/'+NEW,'hidden':False,'discarded':False,'incognito':False}],
   'truncated':False,'ready':True,'reason':'ready','content':{'binding_identity':value['identity'],'reason':'ready',
    'reachable':True,'bound':True,'composer_present':True,'composer_empty':True,'generation_active':False,'busy':False,'ready':True}}
 def probe(self):
  value=self.bind();binding.atomic(self.root/'inbox_binding_probe.json',{'probe_id':NONCE,'binding_identity':value['identity']})
  diagnostic=ReadinessDiagnostic(self.root);self.assertEqual(diagnostic.poll()['cmd'],'readiness_probe');return value,diagnostic
 def test_native_readiness_valid_exact_target_without_http(self):
  value,diagnostic=self.probe();self.assertEqual(diagnostic.accept(self.result(value))['cmd'],'readiness_recorded');self.assertTrue(binding.status(self.root)['no_send_ready']);self.unchanged()
 def test_old_target_stale_epoch_and_content_mismatch_reject(self):
  value,diagnostic=self.probe()
  for kind in ['old_target','epoch','content','build','hidden']:
   result=self.result(value)
   if kind=='old_target':result['matches'][0]['url']='https://chatgpt.com/c/'+binding.LEGACY
   if kind=='epoch':result['binding_identity']='0'*64
   if kind=='content':result['content']['binding_identity']='0'*64
   if kind=='build':result['build']='old'
   if kind=='hidden':result['matches'][0]['hidden']=True
   with self.subTest(kind=kind):self.assertEqual(diagnostic.accept(result)['cmd'],'error')
  self.assertFalse(diagnostic.result.exists())
 def test_probe_removed_still_holds_all_claims(self):
  value,diagnostic=self.probe();diagnostic.request.unlink()
  transport=host.Transport('http://127.0.0.1:18741',self.root/'inbox_native_recovery.json',lambda *args:self.fail('claim forbidden'))
  self.assertTrue(transport.handle({'cmd':'poll','binding_identity':value['identity']})['readiness_hold'])
 def test_recovery_validator_same_identity_and_content(self):
  value,diagnostic=self.probe();self.assertEqual(diagnostic.accept(self.result(value))['cmd'],'readiness_recorded')
  from inbox_recovery import RecoveryAdmin
  queue=type('ReadOnlyQueue',(),{'path':self.root/'inbox_queue.json','clock':staticmethod(__import__('time').time)})()
  admin=RecoveryAdmin(queue);proof=admin.check_readiness();self.assertEqual(proof['binding_identity'],value['identity'])
  r=json.loads(diagnostic.result.read_text());r['content']['binding_identity']='0'*64;diagnostic.result.write_text(json.dumps(r))
  with self.assertRaises(ValueError):admin.check_readiness()
 def test_recovery_release_never_lifts_production_hold(self):
  self.bind();from inbox_recovery import RecoveryAdmin
  queue=type('ReadOnlyQueue',(),{'path':self.root/'inbox_queue.json'})();admin=RecoveryAdmin(queue)
  with self.assertRaises(ValueError):admin.release_hold({})
  self.unchanged()
 def test_config_changes_mid_probe_reject(self):
  value,diagnostic=self.probe();binding.change(self.root,binding.LEGACY,NEW,value['identity'],True)
  self.assertEqual(diagnostic.accept(self.result(value))['cmd'],'error')


if __name__=='__main__':unittest.main(verbosity=2)
