"""No-network regressions for console-less background CLI calls."""
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch
import finish_repair as r


class HiddenLaunchTests(unittest.TestCase):
 def check_hidden(self,call):
  flag=getattr(r.subprocess,'CREATE_NO_WINDOW',0)
  if sys.platform=='win32':self.assertNotEqual(flag,0)
  self.assertEqual(call.call_args.kwargs.get('creationflags'),flag)

 def test_read_only_comment_lookup_is_windowless(self):
  with patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"id":1}')) as call:
   self.assertEqual(r.github_record(1),{'id':1});self.check_hidden(call)

 def test_control_comment_post_is_windowless(self):
  with patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"id":1}')) as call,contextlib.redirect_stdout(io.StringIO()):
   self.assertEqual(r.post('fixture'),1);self.check_hidden(call)

 def test_ten_second_alignment_poll_is_windowless(self):
  plan={'new_policy':{'lane_id':'lane','seal':'seal'},'new_binding':{'identity':'identity'}}
  body={'action':'VM_MODEL_GATE_ALIGNED','in_reply_to':10,'lane_id':'lane','seal':'seal','binding_identity':'identity','completion_cutoff':129,'request_cutoff':129,'future_cursor':132,'historical_state_unchanged':True}
  record={'id':11,'user':{'login':'grxr-dev'},'body':json.dumps(body)}
  with patch.object(r,'github_record',return_value={'created_at':'2026-11-01T22:00:00Z'}),patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(record))) as call:
   self.assertEqual(r.wait_vm_ack(plan,10),11);self.check_hidden(call)

 def test_ten_second_delivery_proof_poll_is_windowless(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'inbox_future_queue.json').write_text('{"entries":{}}',encoding='utf-8')
   with patch.object(r,'RUNTIME',root),patch.object(r.time,'monotonic',side_effect=[0,0,181]),patch.object(r.time,'sleep'),patch.object(r.m,'save'),patch.object(r.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='')) as call,contextlib.redirect_stdout(io.StringIO()):
    r.wait_delivery_proof({},10);self.check_hidden(call)

 def test_existing_bridge_github_service_already_uses_windowless_launch(self):
  sys.path.insert(0,str(r.BRIDGE))
  from github_bus import GHClient
  with patch('github_bus.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=b'{}')) as call:
   self.assertEqual(GHClient('grxr-dev/codex-relay').call('repos/grxr-dev/codex-relay'),{})
   self.check_hidden(call)


if __name__=='__main__':unittest.main()
