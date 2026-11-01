"""Only the #110 changed gates. No scheduler, production write or browser Send."""
import copy
import unittest
from unittest.mock import patch
import finish_repair as r
import postturn_receipt as p


class GateTests(unittest.TestCase):
 def fixture(self):
  plan={'new_binding':{'identity':'new','conversation_id':r.receipt.DEST},'new_policy':{'seal':'seal'}}
  content={k:True for k in ('reachable','bound','composer_present','composer_empty','ready')}
  content.update(busy=False,generation_active=False,proof_build=r.PROOF_BUILD,future_lane_seal='seal',binding_identity='new')
  value={'probe_id':'probe','ready':True,'match_count':1,'binding_identity':'new','observed_ms':1000,'content':content,
         'matches':[{'hidden':False,'discarded':False,'incognito':False,'url':'https://chatgpt.com/c/'+r.receipt.DEST}],
         'diagnostics':[{'model_status':'model_unavailable','node_count':0,'exact':False}]}
  return plan,value

 def test_virtualized_historical_message_is_not_a_readiness_gate(self):
  plan,value=self.fixture();self.assertTrue(r.checked_readiness(value,plan,'probe',1100))
  value['diagnostics']=[];self.assertTrue(r.checked_readiness(value,plan,'probe',1100))

 def test_zero_or_multiple_tabs_refused(self):
  for count in (0,2):
   plan,value=self.fixture();value['match_count']=count
   with self.assertRaises(ValueError):r.checked_readiness(value,plan,'probe',1100)

 def test_wrong_conversation_or_loaded_build_or_identity_refused(self):
  plan,value=self.fixture()
  for key in ('proof_build','binding_identity','future_lane_seal'):
   bad=copy.deepcopy(value);bad['content'][key]='stale'
   with self.assertRaises(ValueError):r.checked_readiness(bad,plan,'probe',1100)
  value['matches'][0]['url']='https://chatgpt.com/c/other'
  with self.assertRaises(ValueError):r.checked_readiness(value,plan,'probe',1100)

 def test_draft_generation_hidden_or_stale_readiness_refused(self):
  plan,value=self.fixture()
  for key,val in (('composer_empty',False),('busy',True),('generation_active',True)):
   bad=copy.deepcopy(value);bad['content'][key]=val
   with self.assertRaises(ValueError):r.checked_readiness(bad,plan,'probe',1100)
  bad=copy.deepcopy(value);bad['matches'][0]['hidden']=True
  with self.assertRaises(ValueError):r.checked_readiness(bad,plan,'probe',1100)
  with self.assertRaises(ValueError):r.checked_readiness(value,plan,'probe',61001)

 def test_wrong_probe_does_not_satisfy_current_request(self):
  plan,value=self.fixture();self.assertFalse(r.checked_readiness(value,plan,'other',1100))

 def test_current_task_not_terminal_can_never_activate(self):
  with patch.object(r.managed,'task_finished',side_effect=ValueError('active turn')):
   self.assertFalse(p.terminal_idle({}, {'turn_active':False}))

 def test_terminal_task_still_requires_unambiguously_idle_bridge(self):
  with patch.object(r.managed,'task_finished',return_value=None):
   self.assertFalse(p.terminal_idle({}, {'turn_active':True,'relay_ready':True}))
   self.assertTrue(p.terminal_idle({}, {'turn_active':False,'active_async_request':None,'relay_ready':True}))

 def test_typed_alignment_ack_survives_reply_format_but_not_generic_ack(self):
  import json
  expected={'action':'VM_MODEL_GATE_ALIGNED','in_reply_to':123,'future_cursor':132,'historical_state_unchanged':True}
  record={'user':{'login':'grxr-dev'},'body':'[JARVIS → CODEX]\n```json\n'+json.dumps(expected)+'\n```'}
  self.assertTrue(r.alignment_ack(record,expected))
  record['body']='[JARVIS-ACK] received123';self.assertFalse(r.alignment_ack(record,expected))
  record['body']=json.dumps(dict(expected,future_cursor=133));self.assertFalse(r.alignment_ack(record,expected))


if __name__=='__main__':unittest.main()
