"""Critical migration/loaded-policy gates only; no scheduler or production writes."""
import copy
import json
import unittest
import deploy_composer135 as p

class DeploymentTests(unittest.TestCase):
 def test_self_comment_cannot_be_vm_ack(self):
  v={'action':'COMPOSER_POLICY_GATE_ALIGNED'}
  self.assertEqual(p.objects({'user':{'login':'grxr-dev'},'body':'[CODEX → JARVIS]\n'+json.dumps(v)}),[])
  self.assertEqual(p.objects({'user':{'login':'grxr-dev'},'body':'[JARVIS → CODEX]\n'+json.dumps(v)}),[v])

 def test_failed_policy_install_restores_source_policy_but_never_queue(self):
  events=[];queue={'state':'NEEDS_REVIEW','attempt_count':1};before=copy.deepcopy(queue)
  def fail():events.append('policy_failed');raise OSError('injected')
  with self.assertRaises(OSError):p.r.transaction(lambda:events.append('source'),fail,lambda:None,lambda:events.append('restore_policy'),lambda:events.append('restore_source'))
  self.assertEqual(events,['source','policy_failed','restore_policy','restore_source']);self.assertEqual(queue,before)

 def test_old_loaded_build_cannot_claim_under_new_policy(self):
  plan={'new_binding':{'identity':'new','conversation_id':p.receipt.DEST},'new_policy':{'seal':'new-seal'}}
  c={k:True for k in ('reachable','bound','composer_present','composer_empty','ready')}
  c.update(busy=False,generation_active=False,proof_build=p.BUILD,future_lane_seal='new-seal',binding_identity='new')
  value={'probe_id':'fresh','ready':True,'match_count':1,'binding_identity':'new','observed_ms':1000,'content':c,'matches':[{'url':'https://chatgpt.com/c/'+p.receipt.DEST,'hidden':False,'discarded':False,'incognito':False}]}
  self.assertTrue(p.r.checked_readiness(value,plan,'fresh',1100))
  c['proof_build']='inbox-raw-user-proof-20261101-01'
  with self.assertRaises(ValueError):p.r.checked_readiness(value,plan,'fresh',1100)

 def test_receipt_is_not_an_online_queue_edit(self):
  with self.assertRaisesRegex(ValueError,'exclusive stopped-bridge'):
   p.receipt.reconcile(None,p.receipt.TARGET,p.receipt.FINGERPRINT,{}, {},{},b'',{},exclusive=False)

if __name__=='__main__':unittest.main()
