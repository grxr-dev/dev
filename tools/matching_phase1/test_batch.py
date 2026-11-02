"""ROM-free manifest, status, protection and ELF-boundary regressions."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import contextlib
import io
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from batch import read_json,validate_manifest,statuses,summarize,verify_hashes,objdiff_scores
from object_inventory import inventory
from elf_function import function,compare
from test_diagnostic import elf
from install_objdiff import release_asset,TAG,COMMIT,ASSET,SHA256,SIZE,URL
import batch


class BatchTests(unittest.TestCase):
    def setUp(self):self.manifest=read_json(HERE/'batch.json')

    def test_six_existing_hypotheses_exactly_once(self):
        validate_manifest(self.manifest)
        self.assertEqual({row['symbol'] for row in self.manifest['symbols']},{'func_020660f4','func_020660fc','func_0206655c','func_020665cc','func_02067f74','func_02068008','func_0200aee8','func_0200abbc','func_0200ac04','func_0200acd0','func_0200af44'})

    def test_duplicate_symbol_rejected(self):
        self.manifest['symbols'][1]=copy.deepcopy(self.manifest['symbols'][0])
        with self.assertRaises(ValueError):validate_manifest(self.manifest)

    def test_omitted_pilot_rejected(self):
        self.manifest['symbols'].pop(0)
        with self.assertRaises(ValueError):validate_manifest(self.manifest)

    def test_wrong_reference_address_size_hash_rejected(self):
        for key,value in [('address','0x020660f8'),('reference_size',12),('reference_sha256','0'*64),('mode','THUMB')]:
            candidate=copy.deepcopy(self.manifest);candidate['symbols'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(candidate)

    def test_literal_pool_must_not_be_counted_as_instructions(self):
        self.manifest['symbols'][1]['code_bytes']=40
        with self.assertRaises(ValueError):validate_manifest(self.manifest)

    def test_relocation_support_is_explicit_not_a_general_linker(self):
        self.manifest['symbols'][1]['direct_call_targets']={}
        with self.assertRaises(ValueError):validate_manifest(self.manifest)
        with self.assertRaises(ValueError):function(elf(relocation=True),'pilot')

    def test_literal_value_and_call_pc_policy_cannot_drift(self):
        for key,value in [('literal_words',{}),('original_relocations',[])]:
            candidate=copy.deepcopy(self.manifest);candidate['symbols'][1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(candidate)

    def test_compiler_profile_immutable(self):
        for key,value in [('compiler_sha256','0'*64),('flags',['-O0']),('zig_version','unknown')]:
            candidate=copy.deepcopy(self.manifest);candidate['compiler'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(candidate)

    def test_canonical_source_cannot_escape_cluster(self):
        self.manifest['symbols'][0]['source']='tools/matching_phase0/leaf_pilot.c'
        with self.assertRaises(ValueError):validate_manifest(self.manifest)

    def test_behavior_pass_does_not_imply_exact_pass(self):
        result=statuses({'compile':{'exit_code':0},'comparison':{'equal':False}},{'status':'PASS_BOUNDED_MODEL'})
        self.assertEqual(result['compile_status'],'PASS')
        self.assertEqual(result['semantic_status'],'PASS_BOUNDED_MODEL')
        self.assertEqual(result['exact_status'],'MISMATCH')
        self.assertFalse(result['genuine_original_match'])

    def test_trivial_exact_pass_is_not_original_compiler_qualification(self):
        result=statuses({'compile':{'exit_code':0},'comparison':{'equal':True}},{'status':'PASS_BOUNDED_MODEL'})
        self.assertEqual(result['exact_status'],'MATCH');self.assertFalse(result['genuine_original_match'])

    def test_compile_failure_cannot_be_exact_pass_from_stale_comparison(self):
        result=statuses({'compile':{'exit_code':1},'comparison':{'equal':True}},None)
        self.assertEqual(result['compile_status'],'FAIL');self.assertEqual(result['exact_status'],'NOT_CHECKED')

    def test_summary_counts_errors_separately(self):
        rows=[statuses({'compile':{'exit_code':0},'comparison':{'equal':False}},{'status':'PASS_BOUNDED_MODEL'}),statuses({'compile':{'exit_code':1}},None)]
        result=summarize(rows)
        self.assertEqual(result['exact_matches'],0);self.assertEqual(result['exact_mismatches'],1);self.assertEqual(result['errors'],1)

    def test_all_twelve_input_cells_detect_mutation_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            expected={}
            for name in ['rom','arm9',*['metadata'+str(index) for index in range(10)]]:
                path=Path(directory)/name;path.write_bytes(name.encode());expected[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
            verify_hashes(expected)
            for path in expected:
                original=Path(path).read_bytes();Path(path).write_bytes(original+b'changed')
                with self.subTest(path=path),self.assertRaises(ValueError):verify_hashes(expected)
                Path(path).write_bytes(original)
            verify_hashes(expected)

    def test_duplicate_json_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'manifest.json';path.write_text('{"schema":1,"schema":2}')
            with self.assertRaises(ValueError):read_json(path)

    def test_inventory_uses_symbol_and_section_bounds(self):
        result=inventory(elf())
        self.assertEqual(result['functions'][0]['value'],4)
        self.assertEqual(result['functions'][0]['size'],8)
        with self.assertRaises(ValueError):inventory(elf(size=100))
        with self.assertRaises(ValueError):inventory(elf(value=5))

    def test_raw_binary_is_not_a_relocatable_original_object(self):
        with self.assertRaises((ValueError,struct.error)):inventory(bytes(64))
        with self.assertRaises(ValueError):inventory(elf(machine=62))

    def test_extra_missing_bytes_are_exact_mismatches(self):
        self.assertFalse(compare(b'ab',b'ab\x00')['equal'])
        self.assertFalse(compare(b'ab',b'a')['equal'])

    def test_legacy_sources_are_thin_includes_not_duplicate_bodies(self):
        root=HERE.parents[1]
        for row in self.manifest['symbols']:
            if 'legacy_config' not in row:continue
            config=Path(row['legacy_config']).name
            names={'diagnostic_config.json':'leaf_pilot.c','byte_exchange_config.json':'byte_exchange.c'}
            source=names.get(config,config.replace('_config.json','.c'))
            text=(root/'tools/matching_phase0'/source).read_text()
            self.assertEqual(text.strip(),'#include "../../'+row['source']+'"')

    def test_objdiff_control_score_is_never_a_game_match(self):
        report={'left':{'symbols':[{'name':'authored','kind':'SYMBOL_FUNCTION','match_percent':100}]}}
        self.assertEqual(objdiff_scores(report,{'authored'},True),{'authored':100})
        with self.assertRaises(ValueError):objdiff_scores(report,{'authored'},False)
        report['left']['symbols'][0]['match_percent']=20
        self.assertEqual(objdiff_scores(report,{'authored'},False),{'authored':20})
        with self.assertRaises(ValueError):objdiff_scores(report,{'authored'},True)

    def test_objdiff_missing_or_duplicate_functions_rejected(self):
        row={'name':'authored','kind':'SYMBOL_FUNCTION','match_percent':100}
        for records in [[],[row,row]]:
            with self.assertRaises(ValueError):objdiff_scores({'left':{'symbols':records}},{'authored'},True)

    def test_official_objdiff_release_contract(self):
        release={'tag_name':TAG,'draft':False,'assets':[{'name':ASSET,'size':SIZE,'digest':'sha256:'+SHA256,'browser_download_url':URL}]}
        tag={'object':{'sha':COMMIT,'type':'commit','url':'https://api.github.com/repos/encounter/objdiff/git/commits/'+COMMIT}}
        self.assertEqual(release_asset(release,tag)['name'],ASSET)

    def test_objdiff_wrong_digest_or_download_origin_rejected(self):
        tag={'object':{'sha':COMMIT,'type':'commit','url':'https://api.github.com/repos/encounter/objdiff/git/commits/'+COMMIT}}
        for key,value in [('digest','sha256:'+'0'*64),('browser_download_url','https://example.com/tool.exe'),('size',1)]:
            asset={'name':ASSET,'size':SIZE,'digest':'sha256:'+SHA256,'browser_download_url':URL};asset[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):release_asset({'tag_name':TAG,'draft':False,'assets':[asset]},tag)

    def test_duplicate_actual_elf_definitions_fail_closed(self):
        original=bytearray(elf());header=list(struct.unpack_from('<16sHHIIIIIHHHHHH',original));shoff=header[6]
        sections=[list(struct.unpack_from('<10I',original,shoff+40*index)) for index in range(header[12])]
        table=sections[2];cut=table[4]+table[5];duplicate=original[table[4]+16:cut]
        changed=original[:cut]+duplicate+original[cut:]
        for section in sections:
            if section[4]>=cut:section[4]+=16
        sections[2][5]+=16;header[6]+=16
        struct.pack_into('<16sHHIIIIIHHHHHH',changed,0,*header)
        for index,section in enumerate(sections):struct.pack_into('<10I',changed,header[6]+40*index,*section)
        with self.assertRaisesRegex(ValueError,'duplicate'):inventory(changed)

    def test_preflight_failure_replaces_stale_local_success(self):
        parent=batch.ROOT/'local/matching_phase1/runs';parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            report=Path(directory)/'batch_status.json';report.write_text('{"classification":"OLD_SUCCESS"}')
            with patch.object(batch,'run',side_effect=ValueError('synthetic metadata mismatch')),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(batch.cli(['--output',directory]),2)
            observed=read_json(report)
            self.assertEqual(observed['classification'],'BATCH_ERROR');self.assertEqual(observed['symbols'],[])
            self.assertIn('synthetic metadata mismatch',observed['error'])

    def test_cli_distinguishes_completed_mismatch_from_execution_error(self):
        for result in (0,1,2):
            with self.subTest(result=result),patch.object(batch,'run',return_value=result):
                self.assertEqual(batch.cli(['--require-exact']),result)


if __name__=='__main__':unittest.main(verbosity=2)
