"""Unaffected existing regressions; never bind the production 18741 test port.

Legacy unbound-native ACK fixtures are incompatible with the new mandatory HOLD.
Their replacement is test_binding.py, which forbids all transport HTTP/ACK paths.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

bridge=Path(__file__).resolve().parents[3]/'bridge'
sys.path[:0]=[str(bridge),str(bridge/'inbox-v1/tests')]


def module(name):
 spec=importlib.util.spec_from_file_location(name,bridge/'inbox-v1/tests'/(name+'.py'))
 result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


hardening=module('test_hardening');trace=module('test_trace')
retention=module('test_incident_retention')
suite=unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(hardening.QueueTests))
for name in ('test_corrupt_journal_blocks','test_native_wire_roundtrip_maximum','test_no_general_command','test_partial_malformed_frame'):
 suite.addTest(hardening.NativeTests(name))
for name in ('test_metadata_persisted_no_payload','test_rotation_bounds'):
 suite.addTest(trace.TraceTests(name))
for name in unittest.defaultTestLoader.getTestCaseNames(retention.IncidentTests):
 if name not in ('test_persistence_failure_outcome_unchanged','test_restart_unknown_outcome_retained'):
  suite.addTest(retention.IncidentTests(name))
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
