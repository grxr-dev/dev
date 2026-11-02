"""Focused no-production-write checks for the single receipt owner action."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import postturn_receipt134 as p


class OwnerTests(unittest.TestCase):
 def test_exact_current_turn_must_be_terminal_and_bridge_idle(self):
  with patch.object(p.r.managed,'task_finished',side_effect=ValueError('active')):
   self.assertFalse(p.owner.terminal_idle({}, {'turn_active':False}))
  with patch.object(p.r.managed,'task_finished',return_value=None):
   self.assertFalse(p.owner.terminal_idle({}, {'turn_active':True}))
   self.assertTrue(p.owner.terminal_idle({}, {'turn_active':False,'active_async_request':None,'relay_ready':True}))

 def test_no_sender_or_cursor_writer_in_owner(self):
  source=Path(p.__file__).read_text()
  self.assertNotIn('send_permit(',source)
  self.assertNotIn('post_inbox(',source)
  self.assertNotIn('rearm(',source)
  self.assertIn('with r.managed.exclusive_stopped(life,a):',source)
  self.assertIn('receipt.reconcile(',source)

 def test_github_cli_is_windowless_and_utf8(self):
  result=type('Result',(),{'returncode':0,'stdout':'{"id":1}'})()
  with patch.object(p.subprocess,'run',return_value=result) as run:
   self.assertEqual(p.gh(['read-only']),{'id':1})
   self.assertEqual(run.call_args.kwargs['encoding'],'utf-8')
   self.assertEqual(run.call_args.kwargs['creationflags'],getattr(p.subprocess,'CREATE_NO_WINDOW',0))

 def test_first_new_review_stops_monitor_without_another_receipt(self):
  with tempfile.TemporaryDirectory() as directory:
   runtime=Path(directory)
   e={'delivery_id':'fixture135','state':'NEEDS_REVIEW','attempt_count':1,'last_error':'exact mismatch','outcome':{'_future':{'source':{'sequence':135}}}}
   path=runtime/'inbox_future_queue.json';path.write_text(json.dumps({'entries':{'fixture135':e}}));before=path.read_bytes()
   with patch.object(p.r,'RUNTIME',runtime),patch.object(p,'record',return_value={}) as record,patch.object(p,'post') as post:
    p.monitor();self.assertEqual(record.call_args.args[0],'STOPPED_ON_NEW_REVIEW');self.assertEqual(post.call_count,1)
   self.assertEqual(path.read_bytes(),before)

 def test_delivered135_is_observed_not_mutated(self):
  with tempfile.TemporaryDirectory() as directory:
   runtime=Path(directory);e={'state':'DELIVERED','attempt_count':1,'outcome':{'_future':{'source':{'sequence':135}}}}
   path=runtime/'inbox_future_queue.json';path.write_text(json.dumps({'entries':{'fixture135':e}}));before=path.read_bytes()
   with patch.object(p.r,'RUNTIME',runtime),patch.object(p,'record',return_value={}) as record,patch.object(p,'post'):
    p.monitor();self.assertEqual(record.call_args.args[0],'SEQ135_AUTOMATIC_DELIVERED')
   self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':unittest.main()
