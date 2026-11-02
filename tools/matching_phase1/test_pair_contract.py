"""AD94 finite CFG/conditional-contract tests; all memory accesses remain virtual."""
import copy
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from batch import ROOT,read_json
from context_models import trace,initialized,CONTEXT,INPUT,PAIR
from nul_count_pilot import decode
from pair_contract import load_reference,cfg,scenarios,explore,preserve_baselines,stack_geometry


class PairContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,_,cls.rows,cls.graph,cls.helper=load_reference()

    def sample(self,data=b'\0',lookup='enabled',mode=0,mask=0,result=1,**extra):
        return trace(self.rows,initialized(bytes(68)),protocol='pair_producer',dispatch_result=result,
                     producer=dict(input=data,lookup=lookup,mode=mode,pair_mask=mask,**extra))

    def test_cfg_code_pool_and_three_direct_exits(self):
        self.assertEqual(len(self.graph['nodes']),84);self.assertEqual(len(self.graph['edges']),107)
        self.assertNotIn(0x0200aee4,self.graph['nodes'])
        self.assertEqual(self.graph['returns'],[0x0200ae34,0x0200ae54,0x0200aee0])
        self.assertEqual(len(self.helper['nodes']),18);self.assertEqual(len(self.helper['calls']),3)

    def test_all_original_calls_are_bound_not_indirect_guesses(self):
        self.assertEqual(self.graph['calls'],[(0x0200ae24,0x0200a8d8),(0x0200aed8,0x0200a464)])
        self.assertEqual(self.helper['returns'],[0x0200a91c])

    def test_cfg_rejects_escape_into_pool_or_unknown_indirect_control(self):
        rows=copy.deepcopy(self.rows);rows[8]=(rows[8][0],'beq','#0x0200aee4')
        with self.assertRaisesRegex(ValueError,'escapes'):cfg(rows)
        rows=copy.deepcopy(self.rows);rows[-1]=(rows[-1][0],'bx','r6')
        with self.assertRaisesRegex(ValueError,'indirect'):cfg(rows)

    def test_cfg_rejects_missing_or_duplicate_instruction(self):
        for rows in (self.rows[:-1],self.rows+[self.rows[-1]],self.rows[:10]+self.rows[11:]):
            with self.assertRaises(ValueError):cfg(rows)

    def test_every_original_edge_and_predicate_outcome_is_covered(self):
        result=explore(self.rows,self.graph)
        self.assertEqual(result['family_count'],33);self.assertEqual(result['scenario_count'],792)
        self.assertEqual(result['node_coverage'],84);self.assertEqual(result['edge_coverage'],107)
        self.assertEqual(result['direct_pair_write_mask'],0)
        self.assertGreater(result['mode0_nonzero_incomplete_pair_countermodels'],0)

    def test_missing_cfg_edge_rejects_trace_not_silently_ignored(self):
        graph=copy.deepcopy(self.graph);graph['edges'].pop()
        with self.assertRaisesRegex(ValueError,'outside CFG'):explore(self.rows,graph)

    def test_each_return_site_and_frame_is_observed(self):
        self.assertEqual([self.sample(b':\0',lookup=lookup)['path'][-1] for lookup in ('null','disabled','enabled')],
                         [0x0200ae34,0x0200ae54,0x0200aee0])
        self.assertEqual(self.sample()['stack_bytes'],40)

    def test_storing_pair_pointer_is_not_initializing_pair(self):
        result=self.sample();state=result['call_states'][0]['scratch']
        self.assertEqual(int.from_bytes(bytes(state[64:68]),'little'),PAIR)
        self.assertEqual(state[60:64],[0,0,0,0]);self.assertEqual(result['pair_writes'],[])
        self.assertEqual(result['output_pair_bytes'],[None]*8);self.assertEqual(result['return'],1)

    def test_nonzero_return_all_four_opaque_write_masks(self):
        for mask in range(4):
            result=self.sample(mask=mask)
            self.assertEqual(result['return'],1)
            for index in range(2):
                self.assertEqual(all(value is not None for value in result['output_pair_bytes'][4*index:4*index+4]),bool(mask&(1<<index)))
            self.assertTrue(all(event['origin']=='opaque_dispatch' for event in result['pair_writes']))

    def test_failed_dispatch_can_leave_one_word_written(self):
        result=self.sample(mask=1,result=0)
        self.assertEqual(result['return'],0)
        self.assertTrue(all(value is not None for value in result['output_pair_bytes'][:4]))
        self.assertEqual(result['output_pair_bytes'][4:],[None]*4)

    def test_raw_result_preserved_then_actual_ACD0_normalizes(self):
        result=self.sample(result=0x80000000)
        self.assertEqual(result['return'],0x80000000);self.assertIsNone(result['nzcv'])
        record=read_json(ROOT/'local/matching_phase1/runs/utility-batch/func_0200acd0/result.json')
        rows=decode(bytes.fromhex(record['reference_hex']),0x0200acd0)
        normalized=trace(rows,bytes(32),protocol='pair_forward',forward_result=result['return'])
        self.assertEqual(normalized['return'],1)

    def test_ABBC_reads_pair_only_when_normalized_return_nonzero(self):
        record=read_json(ROOT/'local/matching_phase1/runs/utility-batch/func_0200abbc/result.json')
        rows=decode(bytes.fromhex(record['reference_hex']),0x0200abbc)
        self.assertEqual(trace(rows,bytes(32),first=0,initialize_pair=False)['return'],0)
        with self.assertRaisesRegex(ValueError,'uninitialized'):trace(rows,bytes(32),first=1,initialize_pair=False)

    def test_nonzero_mode_does_not_publish_caller_pair(self):
        result=self.sample(mode=0x12345678,mask=3)
        state=result['call_states'][0]['scratch']
        self.assertEqual(state[60:64],[1,0,0,0]);self.assertEqual(state[64:68],[0x78,0x56,0x34,0x12])
        self.assertEqual(result['output_pair_bytes'],[None]*8)

    def test_leading_separator_and_relative_global_copy_differ(self):
        words=(0x7000,0x11223344,0xaabbccdd)
        leading=self.sample(b'/',global_words=words)['call_states'][0]['scratch']
        relative=self.sample(b'\0',global_words=words)['call_states'][0]['scratch']
        self.assertEqual(leading[48:56],[0]*8)
        self.assertEqual(relative[48:56],[0x44,0x33,0x22,0x11,0xdd,0xcc,0xbb,0xaa])

    def test_four_byte_scan_never_reads_fifth_ordinary_byte(self):
        for data in (b'abcd',b'abcd:'):
            result=self.sample(data)
            self.assertEqual(len(result['calls']),1)
            self.assertEqual(max(address for address,width in result['reads'] if INPUT<=address<INPUT+16),INPUT+3)
            self.assertEqual(int.from_bytes(bytes(result['context'][56:60]),'little'),INPUT)

    def test_colon_at_three_reads_fifth_byte_after_lookup(self):
        result=self.sample(b'abc:\0')
        self.assertEqual(result['calls'][0],(0x0200a8d8,INPUT,3))
        self.assertIn((INPUT+4,1),result['reads'])

    def test_prefix_failure_does_not_read_post_colon_or_publish_pair(self):
        result=self.sample(b':',lookup='null',mask=3)
        self.assertEqual(result['return'],0);self.assertEqual(len(result['calls']),1)
        self.assertEqual(result['context'][64:68],[None]*4);self.assertEqual(result['pair_writes'],[])

    def test_null_empty_storage_and_short_unterminated_inputs_are_not_safe(self):
        for data,extra in ((b'',{}),(b'a',{}),(b':',{}),(b'\0',{'input_address':0})):
            with self.subTest(data=data),self.assertRaisesRegex(ValueError,'uninitialized'):
                self.sample(data,**extra)

    def test_empty_terminated_string_is_distinct_from_null_pointer(self):
        result=self.sample(b'\0');self.assertEqual(result['return'],1)
        self.assertEqual(len(result['calls']),1)

    def test_leading_and_post_colon_separator_advance_only_once(self):
        for data,offset in ((b'/',1),(b'\\',1),(b'a:/',3),(b'a:\\',3),(b'a:\0',2),(b'a:x',2)):
            result=self.sample(data)
            self.assertEqual(int.from_bytes(bytes(result['context'][56:60]),'little'),INPUT+offset)

    def test_partial_scratch_remains_protected_across_dispatch(self):
        result=self.sample();known={index for index,value in enumerate(result['context']) if value is not None}
        self.assertEqual(len(known),46);self.assertFalse({20,26,43}&known)
        for offset in (20,24,28,40):
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'uninitialized'):
                self.sample(dispatch_reads=(offset,))
        self.assertEqual(self.sample(dispatch_reads=(0,16,44,64))['return'],1)

    def test_pair_alias_null_and_unaligned_preconditions_are_explicit(self):
        for address in (0,CONTEXT+44,INPUT,0x7fe0,0x020d4b6c,PAIR+1):
            with self.subTest(address=address),self.assertRaises(ValueError):self.sample(pair_address=address)
        with self.assertRaisesRegex(ValueError,'input alias'):self.sample(input_address=CONTEXT)

    def test_changed_loop_cannot_run_unbounded(self):
        rows=[(pc,'mov','r4, r4') if pc==0x0200ae8c else (pc,op,args) for pc,op,args in self.rows]
        with self.assertRaisesRegex(ValueError,'budget'):
            trace(rows,initialized(bytes(68)),protocol='pair_producer',producer={'input':b'abcd'})

    def test_six_eight_ten_baselines_remain_byte_identical_without_link(self):
        _,audits=preserve_baselines(self.manifest)
        self.assertEqual([row['symbols'] for row in audits],[6,8,10]);self.assertFalse(any(row['relinked'] for row in audits))
        self.assertEqual(len(self.manifest['symbols'][:10]),10)
        self.assertEqual(self.manifest['symbols'][9]['symbol'],'func_0200acd0')
        self.assertFalse((ROOT/'src/arm9/utility_hypotheses/func_0200ad94.c').exists())

    def test_nested_stack_lifetime_ranges_are_disjoint_not_heap_allocations(self):
        result=stack_geometry(self.manifest)
        self.assertEqual(result['relative_to_ABBC_entry'],{'pair':[-16,-8],'ACD0_scratch':[-96,-28],'AD94_locals':[-136,-120]})
        self.assertEqual(result['pointer_non_retention'],'UNPROVEN_EXTERNAL_OBLIGATION')


if __name__=='__main__':unittest.main(verbosity=2)
