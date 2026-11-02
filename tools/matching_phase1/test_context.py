"""New callee checks use bounded local comparison artifacts; never execute ARM or host C."""
import copy
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from batch import ROOT,read_json,comparison_config,validate_manifest
from context_models import trace,initialized,verify,CONTEXT,WRITTEN
from nul_count_pilot import decode
from partial_link_audit import external_targets,inspect
from partial_link import baseline_check,BASELINE_OUTPUT,BASELINE_SHA256


class ContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read_json(HERE/'batch.json')
        cls.results={name:read_json(ROOT/'local/matching_phase1/runs/utility-batch'/name/'result.json')
                     for name in ('func_0200aee8','func_0200abbc')}

    def rows(self,name,compiled=False):
        result=self.results[name]
        return decode(bytes.fromhex(result['compiled_hex' if compiled else 'reference_hex']),int(result['address'],16))

    def test_initializer_512_safe_memory_cases(self):
        result=self.results['func_0200aee8']
        checked=verify('context_init',bytes.fromhex(result['reference_hex']),bytes.fromhex(result['compiled_hex']),0x0200aee8)
        self.assertEqual(checked['cases'],512);self.assertFalse(checked['independent_cpu_emulator'])

    def test_initializer_preserves_gaps_and_two_byte_store_extent(self):
        initial=bytes([0xa5]*32)
        for compiled in (False,True):
            result=trace(self.rows('func_0200aee8',compiled),initial)
            self.assertEqual(result['context'],initialized(initial))
            self.assertEqual(result['context'][20:24],initial[20:24])
            self.assertEqual(result['context'][26:],initial[26:])
            self.assertEqual({(at-CONTEXT,width) for at,width,_ in result['writes']},set(WRITTEN.items()))

    def test_original_initializer_rereads_zero_compiler_may_elide(self):
        before=trace(self.rows('func_0200aee8'),bytes(range(32)))
        after=trace(self.rows('func_0200aee8',True),bytes(range(32)))
        self.assertEqual(before['reads'],[(CONTEXT,4)]);self.assertEqual(after['reads'],[])
        self.assertEqual(before['context'],after['context'])

    def test_invalid_short_or_unaligned_context_rejected(self):
        for initial,alignment in [(bytes(24),0),(bytes(32),1)]:
            with self.subTest(alignment=alignment),self.assertRaises(ValueError):
                trace(self.rows('func_0200aee8'),initial,alignment=alignment)

    def test_unknown_operation_is_not_silently_modeled(self):
        rows=self.rows('func_0200aee8');rows[0]=(rows[0][0],'svc','#0')
        with self.assertRaisesRegex(ValueError,'unsupported'):trace(rows,bytes(32))

    def test_wrong_initializer_constant_detected(self):
        rows=self.rows('func_0200aee8');rows[3]=(rows[3][0],'mov','r1, #0xf')
        self.assertNotEqual(trace(rows,bytes(32))['context'],initialized(bytes(32)))

    def test_wrapper_320_declared_opaque_call_scenarios(self):
        result=self.results['func_0200abbc']
        checked=verify('context_prepare',bytes.fromhex(result['reference_hex']),bytes.fromhex(result['compiled_hex']),0x0200abbc)
        self.assertEqual(checked['cases'],320);self.assertFalse(checked['formatter_or_external_effects_proved'])

    def test_zero_first_result_never_reads_uninitialized_pair(self):
        for compiled in (False,True):
            result=trace(self.rows('func_0200abbc',compiled),bytes(32),first=0,initialize_pair=False)
            self.assertEqual(result['return'],0);self.assertEqual(len(result['calls']),1)

    def test_nonzero_first_requires_both_pair_words(self):
        for compiled in (False,True):
            with self.assertRaisesRegex(ValueError,'uninitialized'):
                trace(self.rows('func_0200abbc',compiled),bytes(32),first=1,initialize_pair=False)

    def test_pair_values_not_addresses_are_forwarded(self):
        for compiled in (False,True):
            result=trace(self.rows('func_0200abbc',compiled),bytes(32),first=0xffffffff,second=0x80000000,pair=(0xdeadbeef,0x76543210))
            self.assertEqual(result['calls'][1],(0x0200ac04,CONTEXT,0xdeadbeef,0x76543210))
            self.assertEqual(result['return'],1);self.assertEqual(result['stack_bytes'],16)

    def test_second_zero_result_returns_zero(self):
        result=trace(self.rows('func_0200abbc'),bytes(32),first=1,second=0,pair=(1,2))
        self.assertEqual(len(result['calls']),2);self.assertEqual(result['return'],0)

    def test_wrong_opaque_call_rejected(self):
        rows=self.rows('func_0200abbc');rows[4]=(rows[4][0],'bl','#0x200ad94')
        with self.assertRaisesRegex(ValueError,'unknown opaque'):trace(rows,bytes(32))

    def test_wrong_pair_output_pointer_rejected(self):
        rows=self.rows('func_0200abbc');rows[3]=(rows[3][0],'mov','r0, r4')
        with self.assertRaisesRegex(ValueError,'ABI'):trace(rows,bytes(32))

    def test_return_and_saved_register_checks_reject_drift(self):
        rows=self.rows('func_0200aee8');rows[-1]=(rows[-1][0],'bx','r0')
        with self.assertRaisesRegex(ValueError,'return'):trace(rows,bytes(32))
        rows=self.rows('func_0200aee8');rows[0]=(rows[0][0],'mov','r4, #0')
        with self.assertRaisesRegex(ValueError,'callee-saved'):trace(rows,bytes(32))

    def test_minimal_comparison_configs_inherit_pinned_profile(self):
        for row in self.manifest['symbols'][-2:]:
            config=comparison_config(row,self.manifest)
            self.assertEqual(config['compiler_sha256'],self.manifest['compiler']['compiler_sha256'])
            self.assertEqual(config['metadata_sha256'],self.manifest['inputs']['metadata_sha256'])
            self.assertNotIn('legacy_config',row)

    def test_config_ambiguity_or_escape_rejected(self):
        for update in ({'legacy_config':'tools/matching_phase0/diagnostic_config.json'},{'comparison_config':'tools/matching_phase0/diagnostic_config.json'}):
            row=dict(self.manifest['symbols'][-1],**update)
            with self.assertRaises(ValueError):comparison_config(row,self.manifest)

    def test_new_reference_hash_size_and_calls_cannot_drift(self):
        for key,value in [('reference_sha256','0'*64),('reference_size',76),('direct_call_targets',{})]:
            manifest=copy.deepcopy(self.manifest);manifest['symbols'][-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(manifest)

    def test_two_former_imports_defined_two_new_nested_imports(self):
        names={row['symbol'] for row in self.manifest['symbols']};undefined=external_targets(self.manifest)
        self.assertTrue({'func_0200aee8','func_0200abbc'}<=names)
        self.assertEqual(undefined,{'func_02019024','func_0200aa5c','func_0200ab7c','func_0200acd0','func_0200ac04'})

    def test_real_baseline_and_old_six_bodies_unchanged(self):
        models=[inspect((ROOT/'local/matching_phase1/runs/utility-batch'/row['symbol']/'leaf.o').read_bytes()) for row in self.manifest['symbols']]
        self.assertEqual(baseline_check(models)['output_sha256'],BASELINE_SHA256)
        models[0]['bodies']['func_020660f4']=b'changed!'
        with self.assertRaisesRegex(ValueError,'old six'):baseline_check(models)

    def test_new_diagnostics_are_mismatches_not_matches(self):
        for result in self.results.values():
            self.assertFalse(result['comparison']['equal'])
            self.assertEqual(result['original_toolchain_matched_c'],0)
            self.assertEqual(result['elf']['section'],'.text')
            self.assertEqual(result['elf']['elf_flags'],'0x5000200')


if __name__=='__main__':unittest.main(verbosity=2)
