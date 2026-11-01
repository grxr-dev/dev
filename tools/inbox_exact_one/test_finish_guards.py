"""Only launcher critical guards; no production HTTP, shutdown or Send."""
import concurrent.futures
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import finish_once as f


class FinishGuards(unittest.TestCase):
 def test_active_or_uncertain_bridge_never_passes_idle(self):
  for h in ({},{'turn_active':True},{'turn_active':False,'active_async_request':{'id':'another'}},{'turn_active':False,'maintenance_active':True}):
   with self.subTest(h=h),self.assertRaises(ValueError):f.idle(h)
  f.idle({'turn_active':False,'active_async_request':None,'relay_ready':True})
 def test_concurrent_or_repeated_arm_invocation_is_exclusive(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'arm.json'
   def attempt(_):
    try:f.mark_arm(path,{'delivery_id':f.TARGET});return True
    except FileExistsError:return False
   with concurrent.futures.ThreadPoolExecutor(4) as pool:self.assertEqual(sum(pool.map(attempt,range(8))),1)
   self.assertEqual(f.migration.read_sealed(path)['delivery_id'],f.TARGET)
 def test_codex_ancestry_rejects_before_any_shutdown(self):
  life=type('Life',(),{'process':staticmethod(lambda _: {'pid':1,'parent':0,'image':'C:/tools/codex.exe'})})()
  with self.assertRaises(ValueError):f.independent(life)


if __name__=='__main__':unittest.main(verbosity=2)
