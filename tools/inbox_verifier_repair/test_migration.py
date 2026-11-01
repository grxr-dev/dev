"""Critical source-seal continuity and privacy boundaries; no production writes."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
import json
import sys
from unittest.mock import patch
import finish_repair as f


class MigrationTests(unittest.TestCase):
 def fixture(self):
  b={'schema':'middleman-inbox-binding/1','build':'inbox-binding-20261101-01',
     'conversation_id':f.receipt.DEST,'generation':1,'epoch':f.receipt.EPOCH,'delivery_policy':'HOLD',
     'components':{'a.py':'a'*64},'protected_history':{'history':'b'*64},'previous':[],'updated_at':1}
  b['identity']=f.m.digest(b)
  public={k:b[k] for k in ('schema','build','conversation_id','generation','epoch','delivery_policy','identity')}
  p={'schema':'inbox-future-only/1','build':'inbox-future-only-20261101-01','state':'ACTIVE',
     'lane_id':f.receipt.LANE,'binding':public,'completion_cutoff':129,'request_cutoff':129,
     'legacy_queue_sha256':'c'*64,'legacy_hold_sha256':'d'*64}
  p['seal']=f.m.digest(p)
  return b,p

 def test_derives_new_seals_without_recipient_lane_cutoff_or_history_change(self):
  b,p=self.fixture();before=copy.deepcopy((b,p))
  with patch.multiple(f.receipt,IDENTITY=b['identity'],SEAL=p['seal']):
   new,cfg=f.derive(b,p,{'a.py':'e'*64})
  self.assertNotEqual(b['identity'],new['identity']);self.assertNotEqual(p['seal'],cfg['seal'])
  self.assertEqual({k:v for k,v in p.items() if k not in ('seal','binding')},{k:v for k,v in cfg.items() if k not in ('seal','binding')})
  self.assertEqual(new['protected_history'],b['protected_history']);self.assertEqual((b,p),before)

 def test_stale_seal_or_identity_refused(self):
  b,p=self.fixture()
  for which in ('binding','policy'):
   bad_b,bad_p=copy.deepcopy(b),copy.deepcopy(p)
   if which=='binding':bad_b['identity']='0'*64
   else:bad_p['seal']='0'*64
   with self.assertRaises(ValueError):f.derive(bad_b,bad_p,{'a.py':'e'*64})

 def test_component_expansion_refused(self):
  b,p=self.fixture()
  with patch.multiple(f.receipt,IDENTITY=b['identity'],SEAL=p['seal']):
   with self.assertRaises(ValueError):f.derive(b,p,{'a.py':'e'*64,'new-permission.py':'f'*64})

 def test_failed_policy_install_rolls_back_policy_and_sources_not_queue(self):
  events=[];queue={'state':'NEEDS_REVIEW','attempt_count':1};before=copy.deepcopy(queue)
  def fail():events.append('policy_write_failed');raise OSError('injected interruption')
  with self.assertRaises(OSError):f.transaction(lambda:events.append('source_install'),fail,lambda:None,lambda:events.append('policy_restore'),lambda:events.append('source_restore'))
  self.assertEqual(events,['source_install','policy_write_failed','policy_restore','source_restore'])
  self.assertEqual(queue,before)


class DiagnosticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  path=f.STAGE/'inbox-v1/native-host/readiness_diagnostic.py'
  spec=importlib.util.spec_from_file_location('new_readiness_validator',path);cls.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.mod)

 def fixture(self):
  t={'delivery_id':f.receipt.TARGET,'user_turn_uuid':f.receipt.UUID,'text_sha256':f.receipt.TEXT_SHA}
  v={'delivery_id':t['delivery_id'],'uuid':t['user_turn_uuid'],'expected_sha256':t['text_sha256'],
     'observed_sha256':t['text_sha256'],'exact':True,'bound':True,'node_count':1,'model_status':'raw_user_model',
     'rendered_sha256':None,'rendered_length':None,'raw_model_length':1287,
     'structure':[{'type':'div','depth':0,'bubble':True,'markdown':False,'interactive':False}]}
  return t,v

 def test_exact_bounded_diagnostic_accepted(self):
  t,v=self.fixture();self.assertEqual(self.mod.diagnostics([v],[t]),[v])

 def test_different_uuid_or_hash_refused(self):
  t,v=self.fixture()
  for key in ('uuid','observed_sha256'):
   bad=dict(v);bad[key]='0'*64
   with self.assertRaises(ValueError):self.mod.diagnostics([bad],[t])

 def test_payload_or_arbitrary_node_attributes_refused(self):
  t,v=self.fixture();v['payload']='must not persist'
  with self.assertRaises(ValueError):self.mod.diagnostics([v],[t])
  del v['payload'];v['structure'][0]['innerText']='must not persist'
  with self.assertRaises(ValueError):self.mod.diagnostics([v],[t])


class NativeProbeTests(unittest.TestCase):
 def run_probe(self,completed):
  path=f.STAGE/'inbox-v1/native-host/jarvis_inbox_host.py'
  sys.path.append(str(f.BRIDGE/'inbox-v1/native-host'))
  spec=importlib.util.spec_from_file_location('staged_transport_probe_test',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  import inbox_binding
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);probe={'probe_id':'a'*32,'binding_identity':'test','diagnostic_targets':[{'delivery_id':'known'}]}
   (root/'inbox_binding_probe.json').write_text(json.dumps(probe),encoding='utf-8')
   if completed:(root/'inbox_binding_readiness.json').write_text(json.dumps({'probe_id':probe['probe_id']}),encoding='utf-8')
   transport=mod.Transport('http://127.0.0.1:18741',root/'native.json')
   with patch.object(mod,'load_binding',return_value={'identity':'test','delivery_policy':'HOLD'}),patch.object(mod,'future_config',return_value={'seal':'new'}),patch.object(inbox_binding,'status',return_value={'no_send_ready':False}),patch.object(transport.readiness,'poll',return_value={'cmd':'readiness_probe'}):
    transport.handle({'cmd':'poll','binding_identity':'test'})
   return probe,json.loads((root/'inbox_binding_probe.json').read_text(encoding='utf-8'))

 def test_pending_owner_probe_is_not_overwritten(self):
  before,after=self.run_probe(False);self.assertEqual(before,after)

 def test_completed_owner_probe_does_not_block_routine_freshness(self):
  before,after=self.run_probe(True);self.assertNotEqual(before['probe_id'],after['probe_id']);self.assertNotIn('diagnostic_targets',after)


if __name__=='__main__':unittest.main()
