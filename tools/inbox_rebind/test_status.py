"""No browser/process/queue writes: launcher status evidence separation."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

BRIDGE=Path(__file__).resolve().parents[3]/'bridge'
sys.path.insert(0,str(BRIDGE))
spec=importlib.util.spec_from_file_location('middleman_status',BRIDGE/'inbox-v1/middleman_status.py')
status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)


class StatusTests(unittest.TestCase):
 def snapshot(self, receipt=None, ready=False):
  return {'binding':{'identity':'a'*64,'delivery_policy':'HOLD'},'url':'https://chatgpt.com/c/example',
          'readiness':receipt,'no_send_ready':ready}
 def run_status(self,state,query=lambda:'old'):
  with patch.object(status.inbox_binding,'status',return_value=state):return status.summarize(Path('unused'),query)
 def test_disk_only_never_proves_browser_loaded(self):
  result=self.run_status(self.snapshot());self.assertEqual(result['browser_native'],'NOT VERIFIED');self.assertEqual(result['loaded_binding'],'MISSING_OR_NOT_VERIFIED')
 def test_fresh_exact_receipt_and_runtime_build_independent(self):
  result=self.run_status(self.snapshot({'binding_identity':'a'*64,'reason':'ready'},True),lambda:status.EXPECTED_VALIDATOR)
  self.assertEqual(result['browser_native'],'READY');self.assertEqual(result['validator'],'LIVE');self.assertFalse(result['delivery_authorized'])
 def test_old_runtime_build_requires_activation(self):
  self.assertEqual(self.run_status(self.snapshot())['validator'],'NEEDS_POST_TURN_ACTIVATION')
 def test_status_connection_failure_never_grants_ready(self):
  def fail():raise OSError('private transport detail')
  result=self.run_status(self.snapshot(),fail);self.assertIsNone(result['validator_build']);self.assertNotIn('private',str(result));self.assertFalse(result['delivery_authorized'])
 def test_failed_content_receipt_is_not_ready(self):
  result=self.run_status(self.snapshot({'binding_identity':'a'*64,'reason':'content_unreachable_or_timeout'}))
  self.assertEqual(result['browser_native'],'NOT VERIFIED');self.assertEqual(result['readiness_reason'],'content_unreachable_or_timeout')


if __name__=='__main__':unittest.main(verbosity=2)
