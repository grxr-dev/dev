"""Static CFG proofs and virtual-byte differential tests; no live pointers/guest calls."""
import copy
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from batch import ROOT,read_json,verify_hashes
from command4_contract import load,analyze,handler_proof,selector_proof,reaches,record_requirements,TARGET,TABLE
from pair_contract import cfg
from context_models import trace,queue_case,verify,CONTEXT,INPUT,PAIR
from nul_count_pilot import decode


class Command4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.protected,cls.programs,cls.records,cls.baselines=load()
        cls.audit=analyze(cls.programs)
        cls.queue=read_json(ROOT/'local/matching_phase1/runs/utility-batch/func_0200af44/result.json')

    def test_all_original_inputs_and_three_baselines_bound(self):
        verify_hashes(self.protected)
        self.assertEqual([row['symbols'] for row in self.baselines],[6,8,10])
        self.assertEqual(len(self.records),7)

    def test_dispatcher_full_code_cfg_and_four_exits(self):
        graph=self.audit['dispatcher_cfg']
        self.assertEqual((len(graph['nodes']),len(graph['edges'])),(96,114))
        self.assertEqual(graph['returns'],['0x200a4c4','0x200a580','0x200a5b4','0x200a5e0'])

    def test_handler_all_six_exits_and_all_code_nodes(self):
        graph=self.audit['handler']['cfg']
        self.assertEqual((len(graph['nodes']),len(graph['edges'])),(129,170))
        self.assertEqual(len(graph['returns']),6)

    def test_table_slot4_not_notification9(self):
        selector=self.audit['selector']
        self.assertEqual(selector['slot'],hex(TABLE+16));self.assertEqual(selector['target'],hex(TARGET))
        self.assertEqual(selector['custom_enable_mask'],16)
        self.assertIn('UNOBSERVED',selector['custom_target_identity'])
        self.assertIn('NOT',selector['notification9'])

    def test_each_pair_store_dominates_default_zero_exit(self):
        graph=cfg(self.programs[TARGET])
        self.assertTrue(reaches(graph,TARGET,0x02009974))
        for pc in (0x02009968,0x0200996c):self.assertFalse(reaches(graph,TARGET,0x02009974,{pc}))

    def test_store_removal_or_wrong_destination_rejected(self):
        for pc,operation in [(0x02009968,('mov','r2, r2')),(0x0200996c,('str','r1, [r3, #8]'))]:
            rows=[(at,*operation) if at==pc else (at,op,args) for at,op,args in self.programs[TARGET]]
            with self.subTest(pc=pc),self.assertRaises(ValueError):handler_proof(rows)

    def test_forged_early_zero_return_rejected(self):
        for pc,op in ((0x02009850,'moveq'),(0x020098b8,'movgt'),(0x020098e0,'movne'),(0x0200999c,'moveq')):
            rows=[(at,op,'r0, #0') if at==pc else (at,mn,args) for at,mn,args in self.programs[TARGET]]
            with self.subTest(pc=pc),self.assertRaises(ValueError):handler_proof(rows)

    def test_saved_mode_or_extra_pair_write_rejected(self):
        for pc,op,args in [(0x020097d0,'str','r1, [sp]'),(0x020097d8,'str','r1, [r3]')]:
            rows=[(at,op,args) if at==pc else (at,mn,operand) for at,mn,operand in self.programs[TARGET]]
            with self.subTest(pc=pc),self.assertRaises(ValueError):handler_proof(rows)

    def test_selector_result_switch_and_indirect_frontier_fail_closed(self):
        rows=self.programs[0x02009cfc]
        for pc in (0x02009d64,0x02009d8c,0x02009dc4):
            altered=[(at,'mov','r0, r0') if at==pc else (at,op,args) for at,op,args in rows]
            with self.subTest(pc=pc),self.assertRaises(ValueError):selector_proof(altered)
        with self.assertRaisesRegex(ValueError,'indirect'):cfg(self.programs[0x0200a464])

    def test_scratch_unknowns_are_not_silently_initialized(self):
        scratch=self.audit['scratch']
        self.assertEqual(scratch['AD94_initialized_byte_count'],46)
        self.assertEqual(scratch['still_unknown_before_opaque_work'],list(range(26,44)))
        self.assertEqual([(row['offset'],row['width']) for row in scratch['default_handler_unproved_reads']],[(32,2),(40,4)])
        reads={(row['pc'],row['offset'],row['width']) for row in scratch['direct_root_access_inventory'] if row['access']=='read'}
        self.assertTrue({('0x20097c4',60,4),('0x20097c8',56,4),('0x2009890',32,2),('0x200989c',40,4),('0x2009958',64,4)}<=reads)

    def test_pair_stores_not_confused_with_initialized_values(self):
        self.assertEqual(self.audit['handler']['mode0_write_mask_bytes'],255)
        self.assertIn('REQUIRES',self.audit['handler']['source_values_initialized'])
        self.assertIn('CONDITIONAL',self.audit['ABBC_safety'])

    def test_record_read_before_write_obligation_is_path_sensitive(self):
        self.assertEqual(record_requirements(1,'metadata_only'),list(range(12,20)))
        self.assertEqual(record_requirements(3,'terminal_pair'),[*range(8),*range(12,23)])
        self.assertEqual(record_requirements(3,'intermediate'),list(range(23)))
        initialized=set(range(8))
        self.assertEqual(set(record_requirements(3,'terminal_pair'))-initialized,set(range(12,23)))

    def test_record_name_bound_and_invalid_domain_rejected(self):
        self.assertEqual(max(record_requirements(127,'name_compare')),146)
        for length,route in [(0,'terminal_pair'),(128,'terminal_pair'),(1,'guessed')]:
            with self.subTest(length=length),self.assertRaises(ValueError):record_requirements(length,route)

    def test_custom_callback_success_and_deferred_completion_not_proved(self):
        families=self.audit['return_families']
        self.assertEqual(len(families),10)
        custom=next(row for row in families if row['family']=='custom command4 returns0')
        self.assertEqual(custom['dispatcher_normal_result'],1);self.assertIn('UNPROVEN',custom['pair_guarantee'])
        self.assertTrue(self.audit['handler']['nontermination_possible'])

    def test_stack_publication_is_distinct_from_nonretention(self):
        lifetime=self.audit['lifetime']
        self.assertFalse(lifetime['global_nonretention_proved'])
        self.assertIn('descriptor',lifetime['publication']);self.assertIn('AF8C',lifetime['removal'])
        self.assertIn('not restored',lifetime['callback_local_escape'])

    def test_queue_real_original_and_compiled_all_bounded_cases(self):
        result=verify('queue_reinsert',bytes.fromhex(self.queue['reference_hex']),bytes.fromhex(self.queue['compiled_hex']),0x0200af44)
        self.assertEqual(result['status'],'PASS_BOUNDED_MODEL');self.assertEqual(result['cases'],90)

    def test_queue_each_position_empty_and_nonempty_destinations(self):
        for source_count in range(5):
            for position in range(-1,source_count):
                for destination_count in range(5):
                    case=queue_case(source_count,position,destination_count)
                    result=trace(self.programs[0x0200af44],bytes(8),protocol='queue_reinsert',queue=case)
                    self.assertEqual(result['queue_memory'],case['expected'])
                    self.assertEqual(result['return'],CONTEXT)

    def test_queue_same_chain_reinsert_tail_preserves_links(self):
        for position in range(4):
            case=queue_case(4,position,0,True)
            result=trace(self.programs[0x0200af44],bytes(8),protocol='queue_reinsert',queue=case)
            self.assertEqual(result['queue_memory'],case['expected'])

    def test_queue_publication_and_null_termination_are_real_stores(self):
        case=queue_case(0,-1,0)
        result=trace(self.programs[0x0200af44],bytes(8),protocol='queue_reinsert',queue=case)
        self.assertIn((PAIR+4,4,CONTEXT),result['writes'])
        self.assertIn((CONTEXT,4,PAIR),result['writes']);self.assertIn((CONTEXT+4,4,0),result['writes'])

    def test_queue_bad_storage_and_null_head_rejected_without_host_dereference(self):
        for head in (0,PAIR+1):
            case=queue_case(0,-1,0);case['head']=head
            with self.subTest(head=head),self.assertRaisesRegex(ValueError,'virtual read'):
                trace(self.programs[0x0200af44],bytes(8),protocol='queue_reinsert',queue=case)

    def test_queue_cycle_is_bounded_not_assumed_safe(self):
        case=queue_case(0,-1,0)
        for index in range(4):case['memory'][PAIR+4+index]=(PAIR>>(8*index))&255
        with self.assertRaisesRegex(ValueError,'budget'):trace(self.programs[0x0200af44],bytes(8),protocol='queue_reinsert',queue=case)

    def test_new_c_byte_mismatch_remains_mismatch(self):
        self.assertEqual(self.queue['reference_size'],72)
        self.assertFalse(self.queue['comparison']['equal'])
        self.assertEqual(self.queue['original_toolchain_matched_c'],0)

    def test_queue_coverage_and_duplicate_symbol_policy(self):
        from batch import validate_manifest
        manifest=copy.deepcopy(self.manifest);manifest['symbols'][-1]=manifest['symbols'][0]
        with self.assertRaises(ValueError):validate_manifest(manifest)
        row=self.manifest['symbols'][-1]
        self.assertEqual(row['symbol'],'func_0200af44');self.assertEqual(row['original_relocations'],[])
        caller=next(row for row in self.records if row['address']=='0x200af44')
        self.assertIn('from:0x0200a4e0 kind:arm_call to:0x0200af44 module:main',caller['original_direct_callers'])


if __name__=='__main__':unittest.main()
