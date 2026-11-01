"""Only critical migration cases. Reuse #96's 88 staged contract results."""
import ast
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import seal_migration as m

HERE=Path(__file__).resolve().parent;LIVE=HERE.parents[2]/'bridge'


class MigrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.bridge=self.root/'bridge';self.stage=self.root/'stage';self.area=self.root/'audit'
  self.bridge.mkdir();(self.bridge/'.runtime').mkdir();shutil.copytree(HERE/'production',self.stage)
  self.manifest=json.loads((HERE/'source-manifest.json').read_text())
  self.old=json.loads((LIVE/'.runtime/inbox_binding.json').read_text())
  for name in set(self.old['components'])|set(self.manifest['source_files_sha256']):
   if (LIVE/name).exists():
    p=self.bridge/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(LIVE/name,p)
  (self.bridge/'.runtime/inbox_binding.json').write_bytes((LIVE/'.runtime/inbox_binding.json').read_bytes())
  text=next(ast.literal_eval(n.value) for n in ast.parse((HERE/'test_exact_one.py').read_text(encoding='utf-8-sig')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEXT' for t in n.targets))
  q={'version':2,'entries':{m.TARGET:{'state':'QUEUED','attempt_count':0,'text':text,'text_sha256':m.TEXT_SHA},'history':{'state':'NEEDS_REVIEW','opaque':'unchanged'}}}
  for name,value in [('inbox_queue.json',q),('inbox_native_recovery.json',None),('inbox_readiness_request.json',{'probe_id':'a'*32})]:m.save(self.bridge/'.runtime'/name,value)
  self.before=m.state_hashes(self.bridge)
 def prepare(self):return m.prepare(self.bridge,self.stage,self.manifest,self.area)
 def test_positive_same_recipient_epoch_hold_history_and_idempotence(self):
  p=self.prepare();m.install(self.bridge,self.stage,self.area,True)
  new=m.checked_binding(self.bridge)
  for key in self.old:
   if key not in ('components','identity'):self.assertEqual(new[key],self.old[key])
  self.assertEqual(new['identity'],p['new_binding']['identity']);self.assertEqual(m.state_hashes(self.bridge),self.before)
  self.assertEqual(m.install(self.bridge,self.stage,self.area,True),p)
 def test_no_exclusive_idle_ownership_rejects_before_write(self):
  self.prepare()
  with self.assertRaises(ValueError):m.install(self.bridge,self.stage,self.area,False)
  self.assertEqual(m.checked_binding(self.bridge),self.old)
 def test_changed_stage_rejects_before_write(self):
  self.prepare();(self.stage/'inbox_one.py').write_text('tampered')
  with self.assertRaises(ValueError):m.install(self.bridge,self.stage,self.area,True)
  self.assertEqual(m.checked_binding(self.bridge),self.old)
 def test_mid_install_failure_rolls_back_all_source_and_seal(self):
  p=self.prepare()
  with self.assertRaises(OSError):m.install(self.bridge,self.stage,self.area,True,fail_after=5)
  self.assertEqual(m.checked_binding(self.bridge),self.old);self.assertEqual(m.state_hashes(self.bridge),self.before)
  self.assertEqual(m.read_sealed(self.area/'journal.json')['phase'],'ROLLED_BACK')
  self.assertFalse((self.bridge/'inbox_one.py').exists())
 def test_post_seal_rollback_retains_queue_and_old_exact_bytes(self):
  p=self.prepare();m.install(self.bridge,self.stage,self.area,True);m.rollback(self.bridge,self.area,p,True)
  self.assertEqual(m.checked_binding(self.bridge),self.old);self.assertEqual(m.state_hashes(self.bridge),self.before)
 def test_changed_queue_or_grant_blocks_install_and_rollback(self):
  p=self.prepare();m.install(self.bridge,self.stage,self.area,True)
  q=json.loads((self.bridge/'.runtime/inbox_queue.json').read_text());q['exact_one']={'state':'ARMED'};m.save(self.bridge/'.runtime/inbox_queue.json',q)
  with self.assertRaises(ValueError):m.rollback(self.bridge,self.area,p,True)
  with self.assertRaises(ValueError):m.install(self.bridge,self.stage,self.area,True)
 def test_journal_plan_or_backup_tamper_fails_closed(self):
  self.prepare();p=self.area/'plan.json';value=json.loads(p.read_text());value['old_identity']='0'*64;m.save(p,value)
  with self.assertRaises(ValueError):m.install(self.bridge,self.stage,self.area,True)
  self.assertEqual(m.checked_binding(self.bridge),self.old)
 def test_stale_deployed_source_rejects_without_overwrite(self):
  self.prepare();p=self.bridge/'inbox_api.py';p.write_bytes(p.read_bytes()+b'\n# owner edit\n');before=p.read_bytes()
  with self.assertRaises(ValueError):m.install(self.bridge,self.stage,self.area,True)
  self.assertEqual(p.read_bytes(),before)


if __name__=='__main__':unittest.main(verbosity=2)
