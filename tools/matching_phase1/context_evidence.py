"""Fixed two-callee reference audit; public output contains hashes/scalars, never code bytes."""
import argparse
import json
import re
import struct
from batch import ROOT,HERE,read_json,validate_manifest,verify_inputs,verify_hashes,sha
from nul_count_pilot import decode

SELECTED={'func_0200aee8','func_0200abbc'}


def call_target(image,pc):
    word=struct.unpack_from('<I',image,pc-0x02000000)[0]
    if word>>24!=0xeb:raise ValueError('xref is not unconditional ARM BL')
    immediate=word&0xffffff
    return pc+8+4*(immediate-(1<<24) if immediate&(1<<23) else immediate)


def analyze(manifest,image):
    metadata=ROOT/manifest['inputs']['metadata_root']
    symbols=(metadata/'arm9/symbols.txt').read_text().splitlines()
    ranges=[]
    for line in symbols:
        match=re.fullmatch(r'(\S+) kind:function\(arm,size=0x([0-9a-f]+)\) addr:0x([0-9a-f]+)',line)
        if match:ranges.append((int(match[3],16),int(match[2],16),match[1]))
    all_relocs=[(path.relative_to(metadata).as_posix(),line) for path in sorted(metadata.rglob('relocs.txt')) for line in path.read_text().splitlines()]
    results=[]
    for row in manifest['symbols']:
        if row['symbol'] not in SELECTED:continue
        address=int(row['address'],16);size=row['reference_size'];body=image[address-0x02000000:address-0x02000000+size]
        if (address,size,row['symbol']) not in ranges or sha(body)!=row['reference_sha256']:raise ValueError('selected inferred boundary/hash changed')
        if any(start<address+size and address<start+length and name!=row['symbol'] for start,length,name in ranges):
            raise ValueError('overlapping inferred function boundary')
        operations=decode(body,address)
        if row['code_bytes']!=size or row['literal_words'] or any('pc' in args and op not in ('pop','popne') for _,op,args in operations):
            raise ValueError('unexpected pool/PC-relative data in selected function')
        outgoing=[line for module,line in all_relocs if module=='arm9/relocs.txt' and address<=int(line.split('from:')[1].split()[0],16)<address+size]
        if outgoing!=row['original_relocations']:raise ValueError('selected outgoing relocation policy differs')
        decoded_calls=[(pc,int(args[1:],0)) for pc,op,args in operations if op=='bl']
        pinned_calls=[(int(line.split('from:')[1].split()[0],16),int(line.split('to:')[1].split()[0],16)) for line in outgoing]
        if decoded_calls!=pinned_calls or any(call_target(image,pc)!=target for pc,target in pinned_calls):raise ValueError('original calls differ from metadata')
        callers=[]
        for module,line in all_relocs:
            if f'to:0x{address:08x} ' not in line:continue
            pc=int(line.split('from:')[1].split()[0],16)
            if module!='arm9/relocs.txt' or ' kind:arm_call ' not in line or call_target(image,pc)!=address:
                raise ValueError('unexpected caller module/kind/opcode')
            owners=[name for start,length,name in ranges if start<=pc<start+length]
            if len(owners)!=1:raise ValueError('caller has no unique inferred containing function')
            callers.append({'pc':hex(pc),'containing_function':owners[0]})
        results.append({'symbol':row['symbol'],'address':row['address'],'reference_size':size,'reference_sha256':sha(body),
            'inferred_section':'.text','mode':'ARM_LE','code_bytes':size,'literal_bytes':0,'original_outgoing_relocations':outgoing,
            'direct_callers':callers,'direct_caller_count':len(callers),'indirect_callers_excluded':True})
    nested=[]
    for address,size,name in ranges:
        if name not in ('func_0200acd0','func_0200ac04'):continue
        nested.append({'symbol':name,'address':hex(address),'size':size,'sha256':sha(image[address-0x02000000:address-0x02000000+size]),
                       'implementation':'OPAQUE_NOT_RECONSTRUCTED'})
    if len(results)!=2 or len(nested)!=2:raise ValueError('fixed evidence coverage')
    frontier=[]
    for address,size,code_bytes in [(0x02019024,52,52),(0x0200aee8,40,40),(0x0200abbc,72,72),(0x0200aa5c,16,12),(0x0200ab7c,64,64)]:
        name=f'func_{address:08x}'
        if (address,size,name) not in ranges:raise ValueError('original five-import boundary changed')
        body=image[address-0x02000000:address-0x02000000+size]
        relocs=[line for module,line in all_relocs if module=='arm9/relocs.txt' and address<=int(line.split('from:')[1].split()[0],16)<address+size]
        for line in relocs:
            pc=int(line.split('from:')[1].split()[0],16);target=int(line.split('to:')[1].split()[0],16)
            if 'kind:arm_call ' in line:
                if call_target(image,pc)!=target:raise ValueError('frontier BL changed')
            elif 'kind:load ' in line:
                if pc!=address+code_bytes or struct.unpack_from('<I',body,code_bytes)[0]!=target:raise ValueError('frontier literal changed')
            else:raise ValueError('unexpected frontier relocation')
        frontier.append({'symbol':name,'size':size,'code_bytes':code_bytes,'literal_bytes':size-code_bytes,'sha256':sha(body),
                         'original_relocations':relocs,'selected':name in SELECTED})
    return {'schema':'brainage-context-callee-evidence/1','selected':results,'nested_opaque_boundaries':nested,
            'original_five_import_audit':frontier,
            'prototype_and_original_compilation_units':'UNKNOWN','genuine_original_matches':0,'gate0':'OPEN'}


def run(publish=False):
    manifest=read_json(HERE/'batch.json');validate_manifest(manifest);protected,image=verify_inputs(manifest)
    try:
        report=analyze(manifest,image)
        report.update(protected_input_count=len(protected),protected_inputs_unchanged=True)
        path=ROOT/'local/matching_phase1/runs/context-evidence.json'
        path.write_text(json.dumps(report,indent=2)+'\n')
        if publish:(ROOT/'docs/matching_phase1/context_evidence.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS fixed reference audit: two functions, '+str(sum(row['direct_caller_count'] for row in report['selected']))+' verified direct callers; 12 inputs unchanged')
    finally:verify_hashes(protected)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');run(parser.parse_args().publish)
