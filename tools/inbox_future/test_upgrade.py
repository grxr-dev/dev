"""Two critical owner checks: actual overlay rollback and activation scope."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import finish_future as owner

class UpgradeTests(unittest.TestCase):
 def test_current_overlay_install_and_rollback_preserve_all_history_bytes(self):
  manifest=json.loads((owner.HERE/'source-manifest.json').read_text())
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);bridge=root/'bridge';area=root/'audit';runtime=bridge/'.runtime';runtime.mkdir(parents=True)
   old=owner.m.checked_binding(owner.BRIDGE)
   for name,want in manifest['expected_original_sources'].items():
    if want is not None:
     p=bridge/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(owner.BRIDGE/name,p)
     owner.m.atomic(area/'backup'/name,p.read_bytes())
   raw=(owner.RUNTIME/'inbox_binding.json').read_bytes();owner.m.atomic(runtime/'inbox_binding.json',raw);owner.m.atomic(area/'backup/binding.json',raw)
   for name,value in [('inbox_queue.json',{'history':'never change'}),('inbox_native_recovery.json',None),('inbox_readiness_request.json',{'hold':'immutable'})]:owner.m.save(runtime/name,value)
   new=copy.deepcopy(old);new['components']={n:manifest['source_files_sha256'][n] for n in manifest['required_binding_components']};new['identity']=owner.m.digest({k:v for k,v in new.items() if k!='identity'})
   plan={'old_binding_sha256':owner.m.sha(runtime/'inbox_binding.json'),'old_identity':old['identity'],'new_binding':new,'new_sources':manifest['source_files_sha256'],'original_sources':manifest['expected_original_sources'],'protected':owner.m.state_hashes(bridge)}
   owner.m.save(area/'plan.json',owner.m.sealed(plan));owner.m.install(bridge,owner.STAGE,area,True)
   self.assertEqual(owner.m.checked_binding(bridge),new);owner.m.unchanged(bridge,plan)
   owner.m.rollback(bridge,area,plan,True);self.assertEqual(owner.m.checked_binding(bridge),old);owner.m.unchanged(bridge,plan)
 def test_disabled_or_wrong_scope_comment_cannot_authorize_live_mode(self):
  prepared={'seal':'a'*64,'binding':{'identity':'b'*64,'conversation_id':'6ae5615a-0720-83ea-a43b-82386ce031e5'}}
  record={'user':{'login':'grxr-dev'},'issue_url':'https://api.github.com/repos/grxr-dev/codex-relay/issues/45','body':'DISABLED implementation only'}
  def result():return type('Result',(),{'returncode':0,'stdout':json.dumps(record)})()
  with patch.object(owner.subprocess,'run',side_effect=lambda *a,**k:result()):
   with self.assertRaises(ValueError):owner.verify_live_authorization(6560156429,prepared)
   scope={'action':'ACTIVATE_FUTURE_ONLY','prepared_seal':prepared['seal'],'binding_identity':prepared['binding']['identity'],'conversation_id':prepared['binding']['conversation_id'],'historical_policy':'HOLD'}
   record['body']=json.dumps(scope);owner.verify_live_authorization(123,prepared)
   scope['historical_policy']='RELEASE';record['body']=json.dumps(scope)
   with self.assertRaises(ValueError):owner.verify_live_authorization(123,prepared)

if __name__=='__main__':unittest.main(verbosity=2)
