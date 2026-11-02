"""No linker/ROM calls: malformed authored ELF and in-memory policy mutations only."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]/'tools/matching_phase0')]
from partial_link_audit import inspect,attributes,validate_inputs,validate_output,external_targets,CLUSTER_NAMES
from partial_link import INPUT_ROOT,LINK_FLAGS,inputs


def projection(models,manifest):
    """Logical expected-state fixture only. Never writes or fabricates a linked .o."""
    result=copy.deepcopy(models[0]);result.update(functions={},bodies={},layouts={},calls=[],exidx=[])
    result['inventory']['undefined_symbols']=sorted(external_targets(manifest))
    position=0
    for index,(model,row) in enumerate(zip(models,manifest['symbols'])):
        name=row['symbol'];function=copy.deepcopy(model['functions'][name]);function['value']=position
        result['functions'][name]=function;result['bodies'][name]=model['bodies'][name];result['layouts'][name]=copy.deepcopy(model['layouts'][name])
        for record in model['calls']:
            call=dict(record,section_offset=position+record['offset'],target_defined=record['target'] in {entry['symbol'] for entry in manifest['symbols']})
            result['calls'].append(call)
        result['exidx'].append(dict(model['exidx'][0],offset=8*index,raw_addend=position))
        position+=function['size']
    for section in result['inventory']['sections']:
        if section['name']=='.text':section['size']=position
        if section['name']=='.ARM.exidx':section['size']=8*len(models)
    return result


class PartialLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((HERE/'batch.json').read_text())
        cls.raw=[(INPUT_ROOT/row['symbol']/'leaf.o').read_bytes() for row in cls.manifest['symbols']]
        cls.models=[inspect(data) for data in cls.raw]
        cls.undefined=external_targets(cls.manifest)

    def test_actual_independent_compiler_objects_pass_preflight(self):
        result=validate_inputs(self.models,self.manifest)
        self.assertEqual(result[5],'arm946e-s');self.assertEqual(result[6],4)
        self.assertEqual([len(model['functions']) for model in self.models],[1]*len(self.models))

    def test_duplicate_object_symbol_rejected(self):
        models=copy.deepcopy(self.models);models[1]=models[0]
        with self.assertRaises(ValueError):validate_inputs(models,self.manifest)

    def test_unity_object_not_substituted_for_independent_inputs(self):
        models=copy.deepcopy(self.models);models[0]['functions'].update(models[1]['functions'])
        with self.assertRaisesRegex(ValueError,'independently'):validate_inputs(models,self.manifest)

    def test_unexpected_or_missing_input_undefined_rejected(self):
        for names in [['unapproved_runtime'],[]]:
            models=copy.deepcopy(self.models);models[1]['inventory']['undefined_symbols']=names
            with self.subTest(names=names),self.assertRaises(ValueError):validate_inputs(models,self.manifest)

    def test_call_coverage_changes_rejected(self):
        models=copy.deepcopy(self.models);models[2]['calls'].pop()
        with self.assertRaises(ValueError):validate_inputs(models,self.manifest)

    def test_literal_values_cannot_be_reassigned(self):
        models=copy.deepcopy(self.models);name=self.manifest['symbols'][1]['symbol']
        body=bytearray(models[1]['bodies'][name]);body[-1]^=1;models[1]['bodies'][name]=bytes(body)
        with self.assertRaisesRegex(ValueError,'literal'):validate_inputs(models,self.manifest)

    def test_cpu_attribute_drift_rejected(self):
        models=copy.deepcopy(self.models);models[1]['attributes'][6]=5
        with self.assertRaises(ValueError):validate_inputs(models,self.manifest)

    def test_wrong_elf_type_machine_flags_program_headers(self):
        for offset,format,value in [(16,'H',2),(18,'H',62),(36,'I',0x05000400),(44,'H',1)]:
            data=bytearray(self.raw[0]);struct.pack_into('<'+format,data,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):inspect(data)

    def test_weak_function_rejected(self):
        data=bytearray(self.raw[0]);parsed=self.models[0]['inventory']
        table=next(section for section in parsed['sections'] if section['type']==2)
        for offset in range(table['offset'],table['offset']+table['size'],16):
            if data[offset+12]&15==2:data[offset+12]=0x22;break
        with self.assertRaisesRegex(ValueError,'weak'):inspect(data)

    def test_thumb_entry_rejected(self):
        data=bytearray(self.raw[0]);parsed=self.models[0]['inventory']
        table=next(section for section in parsed['sections'] if section['type']==2)
        for offset in range(table['offset'],table['offset']+table['size'],16):
            if data[offset+12]&15==2:struct.pack_into('<I',data,offset+4,1);break
        with self.assertRaises(ValueError):inspect(data)

    def test_comdat_group_flag_rejected(self):
        data=bytearray(self.raw[0]);header=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
        flags=struct.unpack_from('<I',data,header[6]+40+8)[0]
        struct.pack_into('<I',data,header[6]+40+8,flags|0x200)
        with self.assertRaisesRegex(ValueError,'COMDAT'):inspect(data)

    def test_nonzero_section_address_rejected(self):
        data=bytearray(self.raw[0]);header=struct.unpack_from('<16sHHIIIIIHHHHHH',data)
        struct.pack_into('<I',data,header[6]+40+12,0x020660f4)
        with self.assertRaises(ValueError):inspect(data)

    def test_unexpected_named_static_object_rejected(self):
        data=bytearray(self.raw[0]);parsed=self.models[0]['inventory']
        table=next(section for section in parsed['sections'] if section['type']==2)
        for offset in range(table['offset'],table['offset']+table['size'],16):
            if data[offset+12]&15==2:data[offset+12]=0x11;break
        with self.assertRaises(ValueError):inspect(data)

    def test_malformed_attributes_and_wrong_cpu_rejected(self):
        section=next(section for section in self.models[0]['inventory']['sections'] if section['name']=='.ARM.attributes')
        data=self.raw[0][section['offset']:section['offset']+section['size']]
        for bad in [data[:-1],data.replace(b'arm946e-s',b'arm926e-s'),data.replace(b'\x06\x04',b'\x06\x05')]:
            with self.assertRaises(ValueError):attributes(bad)

    def test_wrong_call_opcode_or_addend_rejected(self):
        model=self.models[1];section=next(section for section in model['inventory']['sections'] if section['name']=='.text')
        where=section['offset']+model['calls'][0]['offset']
        for word in (0xeafffffe,0xeb000000):
            data=bytearray(self.raw[1]);struct.pack_into('<I',data,where,word)
            with self.subTest(word=word),self.assertRaises(ValueError):inspect(data)

    def test_unsupported_relocation_rejected(self):
        model=self.models[1];section=next(section for section in model['inventory']['sections'] if section['name']=='.rel.text')
        data=bytearray(self.raw[1]);info=struct.unpack_from('<I',data,section['offset']+4)[0]
        struct.pack_into('<I',data,section['offset']+4,(info&~255)|2)
        with self.assertRaisesRegex(ValueError,'unsupported'):inspect(data)

    def test_model_expected_projection_is_self_consistent(self):
        result=validate_output(self.models,projection(self.models,self.manifest),self.manifest)
        self.assertEqual(result['status'],'PASS_AUTHORED_PARTIAL_LINK_ONLY')
        self.assertEqual(len(result['functions']),len(self.models))
        self.assertFalse(result['original_object_comparison'])

    def test_output_undefined_add_remove_or_resolve_rejected(self):
        for names in [sorted(self.undefined|{'unexpected_runtime'}),sorted(self.undefined-{'func_02019024'}),[]]:
            model=projection(self.models,self.manifest);model['inventory']['undefined_symbols']=names
            with self.subTest(names=names),self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_output_missing_function_rejected(self):
        model=projection(self.models,self.manifest);model['functions'].pop('func_020665cc')
        with self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_output_offset_size_or_layout_drift_rejected(self):
        for field,value in [('value',48),('size',120)]:
            model=projection(self.models,self.manifest);model['functions']['func_0206655c'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)
        model=projection(self.models,self.manifest);model['layouts']['func_0206655c'][0]['size']-=4
        with self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_output_call_target_kind_addend_or_binding_drift(self):
        for field,value in [('target','func_0200abbc'),('kind',2),('normalized_entry_addend',4),('target_defined',True)]:
            model=projection(self.models,self.manifest);model['calls'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_output_missing_extra_or_reordered_exidx(self):
        for action in ('missing','extra','reordered','gap'):
            model=projection(self.models,self.manifest)
            if action=='missing':model['exidx'].pop()
            elif action=='extra':model['exidx'].append(copy.deepcopy(model['exidx'][-1]))
            elif action=='reordered':model['exidx'][0]['owner'],model['exidx'][1]['owner']=model['exidx'][1]['owner'],model['exidx'][0]['owner']
            else:model['exidx'][-1]['offset']+=8
            with self.subTest(action=action),self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_nonrelocation_code_or_pool_mutation_rejected(self):
        for name,offset in [('func_020660f4',0),('func_020660fc',32)]:
            model=projection(self.models,self.manifest);body=bytearray(model['bodies'][name]);body[offset]^=1;model['bodies'][name]=bytes(body)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'bytes changed'):validate_output(self.models,model,self.manifest)

    def test_output_cpu_and_abi_attributes_preserved(self):
        model=projection(self.models,self.manifest);model['attributes'][28]=1
        with self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_aggregate_section_extent_rejected(self):
        model=projection(self.models,self.manifest)
        next(section for section in model['inventory']['sections'] if section['name']=='.text')['size']+=4
        with self.assertRaises(ValueError):validate_output(self.models,model,self.manifest)

    def test_link_flags_retain_all_content_and_reject_duplicates(self):
        self.assertIn('-r',LINK_FLAGS);self.assertIn('--no-gc-sections',LINK_FLAGS)
        self.assertIn('--icf=none',LINK_FLAGS);self.assertIn('--no-merge-exidx-entries',LINK_FLAGS)
        self.assertIn('--no-allow-multiple-definition',LINK_FLAGS)
        self.assertNotIn('--allow-multiple-definition',LINK_FLAGS)

    def test_original_byte_verdicts_are_not_rebased_into_matches(self):
        paths=[INPUT_ROOT/row['symbol']/'leaf.o' for row in self.manifest['symbols']]
        self.assertEqual(len({path.resolve() for path in paths}),len(self.models))
        records=[json.loads((INPUT_ROOT/name/'status.json').read_text()) for name in CLUSTER_NAMES]
        self.assertEqual(sum(row['exact_status']=='MATCH' for row in records),1)
        self.assertEqual(sum(row['exact_status']=='MISMATCH' for row in records),5)


if __name__=='__main__':unittest.main(verbosity=2)
