"""Protocol and immutable-link regressions; no guest/host-C execution or test linking."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from batch import ROOT,read_json
from context_models import trace,verify,CONTEXT,WRITTEN
from nul_count_pilot import decode
from partial_link_audit import inspect,external_targets
import partial_link


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read_json(HERE/'batch.json')
        cls.results={name:read_json(ROOT/'local/matching_phase1/runs/utility-batch'/name/'result.json') for name in ('func_0200ac04','func_0200acd0')}

    def rows(self,name,compiled=False):
        result=self.results[name]
        return decode(bytes.fromhex(result['compiled_hex' if compiled else 'reference_hex']),int(result['address'],16))

    def test_accept_1536_explicit_dispatch_scenarios(self):
        result=self.results['func_0200ac04']
        checked=verify('context_accept',bytes.fromhex(result['reference_hex']),bytes.fromhex(result['compiled_hex']),0x0200ac04)
        self.assertEqual(checked['cases'],1536);self.assertFalse(checked['formatter_or_external_effects_proved'])

    def test_zero_first_needs_no_context_storage_or_dispatch(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200ac04',compiled),b'',protocol='context_accept',first=0)
            self.assertEqual(checked['return'],0);self.assertEqual(checked['calls'],[])
            self.assertTrue(all(at<0x8000 and at>=0x7fe0 for at,_,_ in checked['writes']))

    def test_dispatch_arguments_and_pre_call_context_are_exact(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200ac04',compiled),bytes(64),protocol='context_accept',first=0x1234,second=0x5678)
            self.assertEqual(checked['calls'],[(0x0200a464,CONTEXT,6,0x5678,0x1234)])
            state=checked['call_states'][0]['before']
            self.assertEqual([int.from_bytes(state[offset:offset+4],'little') for offset in (8,44,48)],[0x1234,0x1234,0x5678])

    def test_failed_dispatch_does_not_rollback_pre_or_opaque_writes(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200ac04',compiled),bytes(64),protocol='context_accept',first=7,second=8,dispatch_words={12:0xabcdef20,20:99})
            self.assertEqual(checked['return'],0)
            self.assertEqual(int.from_bytes(checked['context'][12:16],'little'),0xabcdef20)
            self.assertEqual(int.from_bytes(checked['context'][20:24],'little'),99)
            self.assertEqual(int.from_bytes(checked['context'][44:48],'little'),7)

    def test_success_updates_post_dispatch_flags_not_entry_flags(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200ac04',compiled),bytes(64),protocol='context_accept',first=1,dispatch_result=1,dispatch_words={12:0xffffffff})
            self.assertEqual(checked['return'],1)
            self.assertEqual(int.from_bytes(checked['context'][12:16],'little'),0xffffffdf)

    def test_original_and_generated_nzcv_observations(self):
        for result in (0,1,0x80000000,0xffffffff):
            expected=(result>>31,int(result==0),1,0)
            for compiled in (False,True):
                checked=trace(self.rows('func_0200ac04',compiled),bytes(64),protocol='context_accept',first=1,dispatch_result=result)
                self.assertEqual(checked['nzcv'],expected)

    def test_nonzero_first_rejects_short_or_unaligned_context(self):
        for initial,alignment in ((bytes(48),0),(bytes(64),1)):
            with self.subTest(alignment=alignment),self.assertRaises(ValueError):
                trace(self.rows('func_0200ac04'),initial,protocol='context_accept',first=1,alignment=alignment)

    def test_wrong_dispatch_command_rejected(self):
        rows=self.rows('func_0200ac04')
        rows=[(pc,op,'r1, #7' if op=='mov' and args=='r1, #6' else args) for pc,op,args in rows]
        with self.assertRaisesRegex(ValueError,'dispatcher ABI'):trace(rows,bytes(64),protocol='context_accept',first=1)

    def test_opaque_effect_outside_declared_region_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            trace(self.rows('func_0200ac04'),bytes(64),protocol='context_accept',first=1,dispatch_words={64:1})

    def test_forward_48_explicit_scenarios(self):
        result=self.results['func_0200acd0']
        checked=verify('pair_forward',bytes.fromhex(result['reference_hex']),bytes.fromhex(result['compiled_hex']),0x0200acd0)
        self.assertEqual(checked['cases'],48)

    def test_scratch_is_only_partially_initialized(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200acd0',compiled),bytes(32),protocol='pair_forward')
            initialized_bytes=dict(checked['call_states'][0]['scratch'])
            self.assertEqual(len(initialized_bytes),22)
            self.assertEqual(set(initialized_bytes),{offset+index for offset,width in WRITTEN.items() for index in range(width)})
            self.assertNotIn(20,initialized_bytes);self.assertNotIn(26,initialized_bytes);self.assertNotIn(67,initialized_bytes)

    def test_uninitialized_scratch_word_and_halfword_tail_rejected(self):
        for offset in (20,24,28,64):
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'uninitialized'):
                trace(self.rows('func_0200acd0'),bytes(32),protocol='pair_forward',forward_read_offsets=(offset,))

    def test_initialized_scratch_words_can_be_read(self):
        checked=trace(self.rows('func_0200acd0'),bytes(32),protocol='pair_forward',forward_read_offsets=(0,4,8,12,16))
        self.assertEqual(checked['return'],0)

    def test_wrong_forward_mode_rejected(self):
        rows=[(pc,op,'r3, #1' if op=='mov' and args=='r3, #0' else args) for pc,op,args in self.rows('func_0200acd0')]
        with self.assertRaisesRegex(ValueError,'producer ABI'):trace(rows,bytes(32),protocol='pair_forward')

    def test_forwarder_does_not_prove_successful_pair_initialization(self):
        checked=trace(self.rows('func_0200acd0'),bytes(32),protocol='pair_forward',forward_result=1)
        self.assertEqual(checked['return'],1);self.assertEqual(checked['output_pair_bytes'],[None]*8)

    def test_failed_forwarder_retains_opaque_output_mutation(self):
        for compiled in (False,True):
            checked=trace(self.rows('func_0200acd0',compiled),bytes(32),protocol='pair_forward',forward_result=0,forward_pair=(0x1234,0x5678))
            self.assertEqual(checked['return'],0)
            self.assertEqual(checked['output_pair_bytes'],list(bytes.fromhex('3412000078560000')))

    def test_stack_reservations_are_recorded_not_claimed_identical(self):
        for name,kind,expected in [('func_0200ac04','context_accept',[24,16]),('func_0200acd0','pair_forward',[80,88])]:
            self.assertEqual([trace(self.rows(name,compiled),bytes(64),protocol=kind)['stack_bytes'] for compiled in (False,True)],expected)

    def test_old_eight_raw_bodies_and_object_identities_are_protected(self):
        models=[inspect((partial_link.INPUT_ROOT/row['symbol']/'leaf.o').read_bytes()) for row in self.manifest['symbols']]
        self.assertTrue(partial_link.baseline_check(models)['old_eight_raw_bodies_identical'])
        models[6]['bodies']['func_0200aee8']=b'changed'
        with self.assertRaisesRegex(ValueError,'old six/eight'):partial_link.baseline_check(models)

    def test_each_baseline_report_or_object_identity_mismatch_rejects(self):
        for index in (0,1):
            for field in ('report_sha256_lf','output_sha256'):
                manifest=copy.deepcopy(self.manifest);manifest['partial_link']['baselines'][index][field]='0'*64
                with self.subTest(index=index,field=field),self.assertRaises(ValueError):partial_link.baseline_records(manifest)

    def test_both_baseline_directories_are_unwritable_link_targets(self):
        for _,_,path in partial_link.baseline_records(self.manifest):
            with patch.object(partial_link,'command') as command,self.assertRaisesRegex(ValueError,'dedicated output'):
                partial_link.run(output=path.parent)
            command.assert_not_called()

    def test_baseline_report_cannot_be_publication_target(self):
        manifest=copy.deepcopy(self.manifest);manifest['partial_link']['status']=manifest['partial_link']['baselines'][1]['report']
        with patch.object(partial_link,'read_json',return_value=manifest),patch.object(partial_link,'command') as command:
            with self.assertRaisesRegex(ValueError,'overwrite'):partial_link.run(publish=True)
            command.assert_not_called()

    def test_manifest_call_whitelist_is_enforced_before_link(self):
        data=(partial_link.INPUT_ROOT/'func_0200ac04/leaf.o').read_bytes()
        with self.assertRaisesRegex(ValueError,'external'):inspect(data,allowed_calls=set())
        self.assertEqual(len(inspect(data,allowed_calls=partial_link.call_names(self.manifest))['calls']),1)

    def test_ten_function_graph_resolves_pair_calls_but_keeps_dispatch_opaque(self):
        self.assertEqual(len(self.manifest['symbols']),10)
        self.assertEqual(external_targets(self.manifest),{'func_02019024','func_0200aa5c','func_0200ab7c','func_0200a464','func_0200ad94'})

    def test_new_symbol_sizes_and_exact_verdicts_are_not_behavior_passes(self):
        for name,reference,generated in [('func_0200ac04',124,76),('func_0200acd0',64,64)]:
            result=self.results[name]
            self.assertEqual(result['reference_size'],reference);self.assertEqual(result['elf']['symbol_size'],generated)
            self.assertFalse(result['comparison']['equal']);self.assertEqual(result['original_toolchain_matched_c'],0)

    def test_unknown_protocol_operation_fails_closed(self):
        rows=self.rows('func_0200ac04');rows[0]=(rows[0][0],'svc','#0')
        with self.assertRaisesRegex(ValueError,'unsupported'):trace(rows,bytes(64),protocol='context_accept')


if __name__=='__main__':unittest.main(verbosity=2)
