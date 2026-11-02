"""Bounded authored ELF validation; no linking, guest execution or ROM knowledge."""
from collections import Counter
import hashlib
import struct
from elf_function import region,string
from object_inventory import inventory,layout

EXPECTED_UNDEFINED={'func_02019024','func_0200aee8','func_0200abbc','func_0200aa5c','func_0200ab7c'}
CLUSTER_NAMES={'func_020660f4','func_020660fc','func_0206655c','func_020665cc','func_02067f74','func_02068008'}
ALLOWED_CALLS=EXPECTED_UNDEFINED|CLUSTER_NAMES|{'func_0200acd0','func_0200ac04','func_0200a464','func_0200ad94'}
NUMERIC_TAGS={6,7,8,9,14,17,18,20,21,23,24,25,26,27,28,30,34,38}


def digest(data):return hashlib.sha256(data).hexdigest()


def uleb(data,position,limit):
    value=0
    for shift in range(0,35,7):
        if position>=limit:raise ValueError('truncated ARM attribute')
        byte=data[position];position+=1;value|=(byte&127)<<shift
        if not byte&128:return value,position
    raise ValueError('ARM attribute ULEB overflow')


def attributes(data):
    if not data or data[0]!=65:raise ValueError('ARM attribute format')
    size=struct.unpack('<I',region(data,1,4))[0]
    if size!=len(data)-1 or region(data,5,6)!=b'aeabi\0':raise ValueError('one AEABI vendor required')
    tag,position=uleb(data,11,len(data))
    subsection=struct.unpack('<I',region(data,position,4))[0];position+=4
    if tag!=1 or 11+subsection!=len(data):raise ValueError('one file-attribute scope required')
    values={}
    while position<len(data):
        tag,position=uleb(data,position,len(data))
        if tag in values:raise ValueError('duplicate ARM attribute')
        if tag in (4,5,67):
            value=string(data,position);position+=len(value.encode('ascii'))+1
        elif tag in NUMERIC_TAGS:value,position=uleb(data,position,len(data))
        else:raise ValueError('unsupported ARM attribute tag '+str(tag))
        values[tag]=value
    if values.get(5)!='arm946e-s' or values.get(6)!=4 or values.get(8)!=1 or values.get(9)!=1 or values.get(28,0)!=0:
        raise ValueError('ARM946E-S/v5TE/base-PCS attribute mismatch')
    return values


def inspect(data,allowed_calls=None):
    allowed_calls=ALLOWED_CALLS if allowed_calls is None else allowed_calls
    parsed=inventory(data)
    header=struct.unpack('<16sHHIIIIIHHHHHH',region(data,0,52))
    if header[4]!=0 or header[10]!=0 or header[7]!=0x05000200 or header[0][7:9]!=b'\0\0':
        raise ValueError('ET_REL entry/program-header/EABI5 soft-float mismatch')
    sections=parsed['sections'];symbols=[];tables={};attributes_found=[]
    for index,section in enumerate(sections):
        alignment=section['alignment']
        if section['address'] or alignment and alignment&(alignment-1):raise ValueError('nonrelocatable section address/alignment')
        if section['type']==17 or section['flags']&0x200:raise ValueError('COMDAT/section groups are not accepted')
        if section['type']==4:raise ValueError('RELA unsupported; require explicit ARM REL addends')
        if section['flags']&2:
            if section['name'] not in ('.text','.ARM.exidx','.data','.bss'):
                raise ValueError('unexpected allocated section '+section['name'])
            if section['name'] in ('.data','.bss') and section['size']:raise ValueError('unexpected writable storage allocation')
            if alignment!=4 or section['offset']%alignment:raise ValueError('allocated section alignment changed')
        if section['name']=='.ARM.attributes':attributes_found.append(attributes(region(data,section['offset'],section['size'])))
        if section['type']!=2:continue
        names=sections[section['link']];strings=region(data,names['offset'],names['size']);rows=[]
        for offset in range(0,section['size'],16):
            name,value,size,info,other,defined=struct.unpack('<IIIBBH',region(data,section['offset']+offset,16))
            symbol={'name':string(strings,name),'value':value,'size':size,'type':info&15,'binding':info>>4,'visibility':other,'section_index':defined}
            if symbol['binding'] not in (0,1) or other or (defined>=len(sections) and not (symbol['type']==4 and defined==0xfff1)):
                raise ValueError('weak/unique/common/absolute/hidden symbol policy violation')
            if symbol['name'] and defined and symbol['binding']==1 and symbol['type']!=2:raise ValueError('unexpected non-function export/static-global definition')
            if symbol['type']==1 and defined:raise ValueError('named data/static objects are not present in this source contract')
            rows.append(symbol);symbols.append(symbol)
        tables[index]=rows
    if len(attributes_found)!=1:raise ValueError('exactly one ARM attributes section required')
    functions={symbol['name']:symbol for symbol in parsed['functions']}
    if any(symbol['binding']!=1 for symbol in parsed['functions']):raise ValueError('all functions must remain global STT_FUNC')
    calls=[];exidx=[]
    for section in sections:
        if section['type']!=9:continue
        destination=sections[section['info']];table=tables[section['link']]
        for offset in range(0,section['size'],8):
            where,info=struct.unpack('<II',region(data,section['offset']+offset,8));kind=info&255;target=table[info>>8]
            word=struct.unpack('<I',region(data,destination['offset']+where,4))[0]
            if destination['name']=='.text' and kind==28:
                owners=[symbol for symbol in functions.values() if symbol['section_index']==section['info'] and symbol['value']<=where<symbol['value']+symbol['size']]
                if len(owners)!=1 or where%4 or word>>24!=0xeb:raise ValueError('unaligned/non-BL/unowned call relocation')
                immediate=word&0xffffff;addend=(immediate-(1<<24) if immediate&(1<<23) else immediate)*4
                owner=owners[0]
                if target['section_index']==0:
                    if target['name'] not in allowed_calls or addend!=-8:raise ValueError('unexpected external/addend')
                    target_name=target['name']
                else:
                    candidates=[symbol['name'] for symbol in functions.values() if symbol['section_index']==target['section_index'] and symbol['value']==target['value']+addend+8]
                    if len(candidates)!=1:raise ValueError('defined call is not an exact function-entry reference')
                    target_name=candidates[0]
                calls.append({'owner':owner['name'],'offset':where-owner['value'],'kind':28,'target':target_name,
                    'raw_addend':addend,'normalized_entry_addend':0,'target_defined':target['section_index']!=0,'section_offset':where,'raw_target_symbol':target['name']})
            elif destination['name']=='.ARM.exidx' and kind==42:
                if where%8 or destination['link']!=target['section_index'] or word&0x80000000:raise ValueError('exidx ownership/offset')
                addend=(word&0x7fffffff)-(1<<31) if word&(1<<30) else word&0x7fffffff
                candidates=[symbol['name'] for symbol in functions.values() if symbol['section_index']==target['section_index'] and symbol['value']==target['value']+addend]
                if len(candidates)!=1 or struct.unpack('<I',region(data,destination['offset']+where+4,4))[0]!=1:
                    raise ValueError('exidx target/cantunwind mismatch')
                exidx.append({'owner':candidates[0],'offset':where,'kind':42,'raw_addend':addend,'raw_target_symbol':target['name']})
            else:raise ValueError('unsupported relocation section/kind')
    if len({(row['owner'],row['offset']) for row in calls})!=len(calls):raise ValueError('duplicate call relocation')
    if len({row['offset'] for row in exidx})!=len(exidx):raise ValueError('duplicate exidx relocation')
    bodies={}
    for name,symbol in functions.items():
        section=sections[symbol['section_index']]
        bodies[name]=region(data,section['offset']+symbol['value'],symbol['size'])
    return {'inventory':parsed,'flags':hex(header[7]),'attributes':attributes_found[0],'symbols':symbols,'functions':functions,
        'calls':calls,'exidx':exidx,'bodies':bodies,'layouts':{name:layout(data,name) for name in functions},'sha256':digest(data),'size':len(data)}


def external_targets(manifest):
    return set().union(*(set(row['direct_call_targets']) for row in manifest['symbols']))-{row['symbol'] for row in manifest['symbols']}


def validate_inputs(objects,manifest):
    expected={row['symbol']:row for row in manifest['symbols']}
    if not 6<=len(expected)<=10 or len(objects)!=len(expected):raise ValueError('exact manifest coverage of independent input objects required')
    seen=set();undefined=set();baseline_attributes=None
    for item in objects:
        if len(item['functions'])!=1:raise ValueError('input must contain one independently compiled function, not the unity cluster')
        name=next(iter(item['functions']))
        if name in seen or name not in expected:raise ValueError('duplicate/unexpected input function')
        seen.add(name)
        if set(row['target'] for row in item['calls'])!=set(expected[name]['direct_call_targets']) or len(item['calls'])!=len(expected[name]['direct_call_targets']):
            raise ValueError('input call coverage/extern mismatch')
        if len(item['exidx'])!=1 or item['exidx'][0]['owner']!=name:raise ValueError('input exidx ownership')
        if Counter(item['inventory']['undefined_symbols'])!=Counter(list(expected[name]['direct_call_targets'])):raise ValueError('unexpected input undefined symbol')
        undefined.update(item['inventory']['undefined_symbols'])
        if baseline_attributes is None:baseline_attributes=item['attributes']
        if item['attributes']!=baseline_attributes:raise ValueError('input ARM attributes differ')
        pools=[span for span in item['layouts'][name] if span['kind']=='LITERAL_DATA']
        words=[struct.unpack_from('<I',item['bodies'][name],offset)[0] for span in pools for offset in range(span['offset'],span['offset']+span['size'],4)]
        if words!=[int(value,16) for value in expected[name]['literal_words'].values()]:raise ValueError('input literal ownership/values changed')
    if seen!=set(expected) or undefined-seen!=external_targets(manifest):raise ValueError('exact manifest opaque imports must remain')
    return baseline_attributes


def validate_output(inputs,output,manifest):
    baseline_attributes=validate_inputs(inputs,manifest)
    names=[row['symbol'] for row in manifest['symbols']]
    undefined=external_targets(manifest)
    if set(output['functions'])!=set(names) or len(output['functions'])!=len(names):raise ValueError('output function coverage/uniqueness')
    if set(output['inventory']['undefined_symbols'])!=undefined or len(output['inventory']['undefined_symbols'])!=len(undefined):raise ValueError('output must retain exactly the manifest opaque undefined symbols')
    if output['attributes']!=baseline_attributes:raise ValueError('output CPU/ABI attributes changed')
    expected_calls=sorted((row['owner'],row['offset'],row['kind'],row['target'],0) for item in inputs for row in item['calls'])
    actual_calls=sorted((row['owner'],row['offset'],row['kind'],row['target'],row['normalized_entry_addend']) for row in output['calls'])
    if actual_calls!=expected_calls:raise ValueError('partial link lost/changed call relocation/addend')
    if [(row['owner'],row['offset']) for row in sorted(output['exidx'],key=lambda row:row['offset'])]!=list(zip(names,range(0,8*len(names),8))):
        raise ValueError('exidx order/completeness changed')
    results=[];position=0
    for item,name in zip(inputs,names):
        if set(item['functions'])!={name}:raise ValueError('input manifest/link order changed')
        before=item['functions'][name];after=output['functions'][name]
        if after['value']!=position or after['size']!=before['size'] or output['layouts'][name]!=item['layouts'][name]:raise ValueError('output function offset/size/code-pool ownership changed')
        before_body=item['bodies'][name];after_body=output['bodies'][name]
        if before_body!=after_body:raise ValueError('input/output raw bytes changed')
        call_offsets={row['offset'] for row in item['calls']}
        for offset in range(0,len(before_body),4):
            if offset not in call_offsets and before_body[offset:offset+4]!=after_body[offset:offset+4]:raise ValueError('nonrelocation code/literal bytes changed')
        results.append({'symbol':name,'section':'.text','section_offset':after['value'],'size':after['size'],
            'input_raw_sha256':digest(before_body),'output_raw_sha256':digest(after_body),
            'raw_symbol_bytes_identical':before_body==after_body,'layout':output['layouts'][name],
            'absolute_original_placement_claimed':False})
        position+=after['size']
    text=[section for section in output['inventory']['sections'] if section['name']=='.text']
    exidx=[section for section in output['inventory']['sections'] if section['name']=='.ARM.exidx']
    if len(text)!=1 or text[0]['size']!=position or text[0]['alignment']!=4 or len(exidx)!=1 or exidx[0]['size']!=8*len(names):
        raise ValueError('aggregate code/exidx extent/alignment changed')
    for row in output['calls']:
        if row['target_defined']!=(row['target'] in names):raise ValueError('internal/external call binding changed')
    return {'status':'PASS_AUTHORED_PARTIAL_LINK_ONLY','output_sha256':output['sha256'],'output_size':output['size'],
        'elf_flags':output['flags'],'arm_attributes':{str(key):value for key,value in output['attributes'].items()},
        'functions':results,'undefined_symbols':output['inventory']['undefined_symbols'],
        'calls':output['calls'],'exidx':output['exidx'],'sections':output['inventory']['sections'],
        'named_static_data_definitions':[],'bss_data_allocated_bytes':0,
        'symbol_resolution':{'defined_call_edges':sum(row['target_defined'] for row in output['calls']),'opaque_imports':len(undefined)},
        'comdat_weak_duplicate_policy':'rejected before link; no-allow-multiple-definition and ICF disabled',
        'original_object_comparison':False,'genuine_original_matches':0,'gate0':'OPEN'}
