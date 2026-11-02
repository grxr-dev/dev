"""Pinned command-4 CFG/dataflow audit; no guest, live BSS, or opaque-call execution."""
import argparse
import json
import re
import struct
from batch import ROOT,HERE,read_json,validate_manifest,verify_inputs,verify_hashes,sha
from context_evidence import call_target
from nul_count_pilot import decode
from pair_contract import cfg,public_cfg,preserve_baselines

REFERENCES={
    0x0200a464:(384,384,'c785fabba0294602866b9e8bfbbcb8333a4932e508dfd2011ee741edc67f8e4a'),
    0x020097b8:(516,516,'a2f3ad69d47db158aa1b5f090884e5260fb52b2b50b379438bb76be7769cf64c'),
    0x02009cfc:(396,392,'c34f8a2e6235fee97a585ea4774fb378669872c90ee83ae1986c875a1b5359f4'),
    0x0200a5e4:(68,68,'e740e1007ee39523fabd979ec7eb9194117de383a10174e597d5f0bb742c9187'),
    0x02009e88:(64,64,'64f2269fb1d0088d03d1eef7b260828778bf91c887f11d208d4a5efd95fdaeba'),
    0x0200af44:(72,72,'a0ede9b82518e5a14a72ab0bfb533021242e7e332512366c243f72a8e6ffa8b6'),
    0x0200af8c:(44,44,'adb1f92372b3ac3ca04ba7c21689b28162b9b45210eb1ac2ec760a7b13a232aa')
}
TABLE=0x020c606c
TARGET=0x020097b8


def require(rows,expected):
    actual={pc:(op,args) for pc,op,args in rows}
    for pc,operation in expected.items():
        if actual.get(pc)!=operation:raise ValueError('contract instruction changed at '+hex(pc))


def load():
    manifest=read_json(HERE/'batch.json');validate_manifest(manifest);protected,image=verify_inputs(manifest)
    metadata=ROOT/manifest['inputs']['metadata_root'];symbols=(metadata/'arm9/symbols.txt').read_text().splitlines()
    relocs=(metadata/'arm9/relocs.txt').read_text().splitlines();programs={};records=[]
    for address,(size,code,digest) in REFERENCES.items():
        body=image[address-0x02000000:address-0x02000000+size]
        if sha(body)!=digest or symbols.count(f'func_{address:08x} kind:function(arm,size=0x{size:x}) addr:0x{address:08x}')!=1:
            raise ValueError('command4 boundary/hash changed')
        rows=decode(body[:code],address);programs[address]=rows
        outgoing=[line for line in relocs if address<=int(line.split('from:')[1].split()[0],16)<address+size]
        decoded_calls=[(pc,int(args[1:],0)) for pc,op,args in rows if op=='bl']
        expected_calls=[(int(line.split('from:')[1].split()[0],16),int(line.split('to:')[1].split()[0],16)) for line in outgoing if 'kind:arm_call ' in line]
        if expected_calls!=decoded_calls or any(call_target(image,pc)!=target for pc,target in decoded_calls):raise ValueError('call relocation mismatch')
        loads=[line for line in outgoing if 'kind:load ' in line]
        if len(outgoing)!=len(expected_calls)+len(loads) or loads!=([f'from:0x02009e84 kind:load to:0x{TABLE:08x} module:main'] if address==0x02009cfc else []):raise ValueError('pool/data relocation mismatch')
        if any(op=='ldr' and '[pc,' in args for _,op,args in rows) != (address==0x02009cfc):raise ValueError('unexpected literal access')
        records.append({'address':hex(address),'reference_size':size,'code_bytes':code,'literal_bytes':size-code,
                        'sha256':digest,'mode':'ARM_LE','section':'.text','original_relocations':outgoing})
        if address==0x0200af44:
            incoming=[line for line in relocs if f' to:0x{address:08x} ' in line]
            for line in incoming:
                pc=int(line.split('from:')[1].split()[0],16)
                if 'kind:arm_call ' not in line or call_target(image,pc)!=address:raise ValueError('queue caller relocation changed')
            records[-1]['original_direct_callers']=incoming
    if struct.unpack_from('<I',image,0x9e84)[0]!=TABLE or struct.unpack_from('<I',image,TABLE-0x02000000+16)[0]!=TARGET:
        raise ValueError('command4 table identity changed')
    if f'from:0x{TABLE+16:08x} kind:load to:0x{TARGET:08x} module:main' not in relocs or f'data_{TABLE:08x} kind:data(any) addr:0x{TABLE:08x}' not in symbols:
        raise ValueError('table slot relocation/ownership changed')
    for address,rows in programs.items():
        expected_indirect={0x0200a540,0x02009d58,0x02009dc8} if address in (0x0200a464,0x02009cfc) else set()
        if {pc for pc,op,_ in rows if op=='blx'}!={pc for pc in expected_indirect if address<=pc<address+REFERENCES[address][1]}:
            raise ValueError('indirect-call frontier changed')
    baseline_protected,baselines=preserve_baselines(manifest);protected.update(baseline_protected)
    verify_hashes(protected)
    return manifest,protected,programs,records,baselines


def reaches(graph,start,target,removed=()):
    visited=set();pending=[start]
    while pending:
        node=pending.pop()
        if node in removed or node in visited:continue
        if node==target:return True
        visited.add(node);pending.extend(to for source,to,_ in graph['edges'] if source==node and to!='RETURN')
    return False


def handler_proof(rows):
    graph=cfg(rows)
    require(rows,{
        0x020097c4:('ldr','r2, [sl, #0x3c]'),0x020097d0:('str','r2, [sp]'),
        0x02009850:('moveq','r0, #1'),0x020098b8:('movgt','r0, #1'),
        0x020098e0:('movne','r0, #1'),0x02009950:('movne','r0, #1'),
        0x02009924:('add','r3, sl, #0x2c'),0x0200992c:('stm','r3, {r0, r1, r2}'),
        0x02009958:('ldr','r3, [sl, #0x40]'),0x0200995c:('ldr','r2, [sp, #8]'),
        0x02009960:('ldr','r1, [sp, #0xc]'),0x02009968:('str','r2, [r3]'),
        0x0200996c:('str','r1, [r3, #4]'),0x02009970:('mov','r0, #0'),
        0x02009994:('ldr','r0, [sp]'),0x02009998:('cmp','r0, #0'),
        0x0200999c:('moveq','r0, #1'),0x020099a0:('addne','r0, sl, #0x1c'),
        0x020099a4:('ldrne','r3, [sl, #0x40]'),0x020099a8:('ldmne','r0, {r0, r1, r2}'),
        0x020099ac:('stmne','r3, {r0, r1, r2}'),0x020099b0:('movne','r0, #0')})
    if graph['returns']!=[0x02009854,0x020098bc,0x020098e4,0x02009954,0x02009974,0x020099b8]:raise ValueError('handler exit coverage changed')
    if graph['calls']!=[(0x020097d4,0x02009cfc),(0x020098a4,0x02009c1c),(0x020098d4,0x02009cfc),(0x0200990c,0x02009bc0),(0x0200993c,0x02009cfc)]:raise ValueError('handler opaque frontier changed')
    for store in (0x02009968,0x0200996c):
        if not reaches(graph,TARGET,0x02009974) or reaches(graph,TARGET,0x02009974,{store}):raise ValueError('pair store does not dominate zero exit')
    mode_stores=[pc for pc,op,args in rows if op.startswith('str') and args.endswith('[sp]')]
    if mode_stores!=[0x020097d0]:raise ValueError('saved mode overwritten')
    pair_stores=[pc for pc,op,args in rows if op.startswith(('str','stm')) and ('[r3' in args or args.startswith('r3,'))]
    if pair_stores!=[0x0200992c,0x02009968,0x0200996c,0x020099ac]:raise ValueError('r3-store inventory changed')
    return {'cfg':public_cfg(graph),'mode0_zero_exit':hex(0x02009974),'mode0_write_mask_bytes':255,
            'dominating_pair_store_pcs':[hex(0x02009968),hex(0x0200996c)],
            'source_values_initialized':'REQUIRES_COMMAND3_STACK_OUTPUT_CONTRACT',
            'saved_mode_invariance':'local stack word stored once; excludes opaque out-of-bounds corruption',
            'other_mode0_returns':1,'mode_nonzero_terminal_copy_bytes':12,
            'nontermination_possible':True,'proof_kind':'CFG dominance plus pinned exit/mode dataflow, NOT opaque-call verification'}


def selector_proof(rows):
    require(rows,{
        0x02009d40:('ldr','r0, [r7, #0x4c]'),0x02009d44:('ands','r0, r0, r5'),
        0x02009d4c:('ldr','r2, [r7, #0x48]'),0x02009d58:('blx','r2'),
        0x02009d64:('addls','pc, pc, r6, lsl #2'),0x02009d90:('str','r6, [r4, #0x14]'),
        0x02009da4:('str','r0, [r7, #0x4c]'),0x02009da8:('mov','r6, #7'),
        0x02009db4:('cmp','r6, #7'),0x02009dbc:('ldr','r1, [pc, #0xc0]'),
        0x02009dc4:('ldr','r1, [r1, r8, lsl #2]'),0x02009dc8:('blx','r1'),
        0x02009e58:('strne','r6, [r4, #0x14]')})
    destinations=[int(args[1:],0) for pc,op,args in rows if 0x02009d6c<=pc<=0x02009d8c and op=='b']
    if destinations!=[0x02009d90,0x02009d90,0x02009db4,0x02009db4,0x02009d90,0x02009db4,0x02009db4,0x02009db4,0x02009d98]:raise ValueError('callback status jump table changed')
    return {'command':4,'custom_enable_mask':16,'custom_target_source':'descriptor+0x48; gated by descriptor+0x4c bit 0x10',
            'custom_target_identity':'UNOBSERVED_RUNTIME_DESCRIPTOR_NOT_STATICALLY_PROVED',
            'fallback_table':hex(TABLE),'slot':hex(TABLE+16),'target':hex(TARGET),
            'fallback_if':'custom disabled, custom returns 7, or custom returns 8 (also clears enable bit)',
            'custom_status6':'waits under synchronous flag, then reads context+0x14; opaque completion obligation',
            'custom_status0':'can make context status zero WITHOUT any proved pair write',
            'notification9':'separate optional descriptor callback at A540; NOT the command4 table operation'}


def record_requirements(component_length,route):
    if not 1<=component_length<=127 or route not in ('metadata_only','name_compare','terminal_pair','intermediate'):
        raise ValueError('record contract domain')
    required=set(range(12,20))
    if route!='metadata_only':required.update(range(20,20+component_length))
    if route=='terminal_pair':required.update(range(8))
    elif route=='intermediate':required.update(range(12))
    return sorted(required)


def scratch_accesses(programs):
    aliases={0x0200a464:'r7',TARGET:'sl',0x02009cfc:'r4',0x0200a5e4:'r4',
             0x02009e88:'r6',0x0200af44:'r0',0x0200af8c:'r0'}
    accesses=[]
    for address,base in aliases.items():
        for pc,op,args in programs[address]:
            if not op.startswith(('ldr','str')):continue
            match=re.fullmatch(r'(?:r\d+|sb|sl|fp|ip), \['+base+r'(?:, #(0x[0-9a-f]+|\d+))?\]',args)
            if match:
                accesses.append({'pc':hex(pc),'function':hex(address),'offset':int(match[1],0) if match[1] else 0,
                    'width':1 if op.startswith(('ldrb','strb')) else 2 if op.startswith(('ldrh','strh')) else 4,
                    'access':'read' if op.startswith('ldr') else 'write','predicate':op[4:] if op.startswith(('ldrh','strh','ldrb','strb')) else op[3:]})
    return accesses


def return_families():
    return [
        {'family':'descriptor bit 0x80 set','dispatcher_return':'0','pair_guarantee':'NONE'},
        {'family':'scratch sync bit 4 cleared by opaque work','dispatcher_return':'1 at A580 or A5B4','pair_guarantee':'UNPROVEN; not the stable command4 route'},
        {'family':'descriptor busy/active','dispatcher_return':'wait loop or completion helper boolean','pair_guarantee':'requires progress, no premature completion and correct worker result'},
        {'family':'default handler mode0 empty/exhausted component','operation_return':1,'dispatcher_normal_result':0,'pair_guarantee':'NONE'},
        {'family':'default handler zero-length/over127 component or command3 nonzero','operation_return':1,'dispatcher_normal_result':0,'pair_guarantee':'NONE'},
        {'family':'default handler mode0 terminal match','operation_return':0,'dispatcher_normal_result':1,'pair_write_mask':255,'initialized_values':'CONDITIONAL on command3 record initialization'},
        {'family':'default handler dot/dotdot/intermediate directory','operation_return':'continue parsing or loop','pair_guarantee':'no immediate pair success; command2/9C1C effects opaque'},
        {'family':'custom command4 returns0','dispatcher_normal_result':1,'pair_guarantee':'UNPROVEN; callback may not write'},
        {'family':'custom status6 deferred completion','dispatcher_normal_result':'depends on later context status','pair_guarantee':'UNPROVEN_ASYNC_LIFETIME'},
        {'family':'custom other nonfallback nonzero','dispatcher_normal_result':0,'pair_guarantee':'NONE; partial opaque writes possible'}
    ]


def analyze(programs):
    dispatcher=programs[0x0200a464];completion=programs[0x0200a5e4]
    graph=cfg(dispatcher,indirect_calls={0x0200a540})
    require(dispatcher,{
        0x0200a480:('str','r0, [r7, #0x14]'),0x0200a488:('lsl','r5, r2, r1'),
        0x0200a4c8:('ands','r0, r5, #0x1fc'),0x0200a4d4:('orrne','r0, r0, #4'),
        0x0200a4d8:('strne','r0, [r7, #0xc]'),0x0200a4dc:('mov','r0, r7'),
        0x0200a4d0:('add','r1, r6, #0x14'),0x0200a4e0:('bl','#0x200af44'),
        0x0200a534:('ldr','r2, [r6, #0x48]'),0x0200a53c:('mov','r1, #9'),
        0x0200a540:('blx','r2'),0x0200a5d4:('mov','r0, r7'),0x0200a5d8:('bl','#0x200a5e4')})
    require(completion,{
        0x0200a5ec:('ldr','r1, [r4, #0x10]'),0x0200a5f0:('bl','#0x2009cfc'),
        0x0200a5fc:('bl','#0x2009e88'),0x0200a604:('bl','#0x200a6bc'),
        0x0200a614:('ldr','r0, [r4, #0x14]'),0x0200a618:('cmp','r0, #0'),
        0x0200a61c:('moveq','r0, #1'),0x0200a620:('movne','r0, #0')})
    require(programs[0x02009e88],{0x02009ea0:('bl','#0x200af8c'),0x02009eb4:('str','r5, [r6, #0x14]')})
    scratch_known=set(range(20))|{24,25}|set(range(44,68))
    dispatcher_added=set(range(20,24))
    return {'dispatcher_cfg':public_cfg(graph),'handler':handler_proof(programs[TARGET]),
        'selector':selector_proof(programs[0x02009cfc]),'return_families':return_families(),
        'conditional_contract_assumptions':[
            'Valid aligned disjoint scratch, descriptor, local record and eight-byte pair; readable input; normal ARM ABI',
            'Mode cached as zero; scratch+0x40 still denotes the original pair when the default stores execute',
            'Opaque helpers respect object bounds, stack lifetime and completed status; none of these effects is independently proved here',
            'Default route requires descriptor custom gate absent or callback fallback; actual gate/target not observed',
            'Command2 initializes fields before dotdot reads; successful command3 initializes every path-required record/name byte',
            'No concurrent mutation, invalid aliasing or signed length wrap; no termination guarantee inferred from CFG'],
        'scratch':{'AD94_initialized_byte_count':len(scratch_known),'dispatcher_initializes_half_open_range':[20,24],
                   'direct_root_access_inventory':scratch_accesses(programs),
                   'inventory_scope':'stable root aliases only; indirect record/pair/descriptor accesses and published interior pointers are described separately',
                   'known_before_opaque_work':sorted(scratch_known|dispatcher_added),
                   'still_unknown_before_opaque_work':sorted(set(range(68))-scratch_known-dispatcher_added),
                   'default_handler_unproved_reads':[{'pc':'0x02009890','offset':32,'width':2,'condition':'dotdot after opaque command2'},
                        {'pc':'0x0200989c','offset':40,'width':4,'condition':'dotdot and halfword+0x20 nonzero'}],
                   'command2':'return status ignored at 97D4 and 993C; cannot infer initialization from a success check',
                   'command3_local_record':'stack+8..0x1b and name stack+0x1c, up to 127 bytes; reads +0x14,+0x18 before pair words',
                   'command3_record_relative_reads':{route:record_requirements(3,route) for route in ('metadata_only','name_compare','terminal_pair','intermediate')},
                   'name_compare_read_bound':'requires opaque 9BC0 to respect count and not retain pointers; not proved',
                   'wait_primitive':'context+0x18 passed; only first halfword initialized by AEE8; opaque read width unproved'},
        'lifetime':{'publication':'AF44 stores scratch pointer in descriptor+0x14 list or its final node next field',
                    'removal':'9E88 calls AF8C unlink and clears both link words, then signals opaque 5598',
                    'callback_local_escape':'97B8 stores own stack+8 in context+0x2c before command3; field not restored on final match',
                    'synchronous_condition':'opaque command2/3, comparator9BC0, parent9C1C, callbacks and wait/signal helpers must not retain invalidated stack pointers',
                    'global_nonretention_proved':False},
        'ABBC_safety':'CONDITIONAL_DEFAULT_PATH_ONLY; actual descriptor callback/enable state and nested initialization/lifetime contracts remain unproved',
        'next_step':'Audit only command3 default table slot and its record/name-buffer write coverage, with descriptor command3 override gate; no general subsystem sweep'}


def run(publish=False):
    manifest,protected,programs,records,baselines=load()
    try:
        report={'schema':'brainage-command4-contract/1','classification':'GROUNDED_PARTIAL_CONTRACT_WITH_QUEUE_C',
            'references':records,'audit':analyze(programs),'immutable_baselines':baselines,
            'new_C':['func_0200af44'],'new_C_is_dispatcher_or_handler':False,
            'new_C_reason':'directly called queue primitive, verified unlink/append; no speculative callback bodies',
            'opaque_commands_not_recursed':[2,3],'guest_execution':False,'runtime_descriptor_observed':False,
            'protected_input_count':12,'protected_inputs_unchanged':True,'genuine_original_matches':0,'gate0':'OPEN'}
        status=read_json(ROOT/'docs/matching_phase1/batch_status.json')
        report['batch_summary']=status['summary'];report['regressions']=status['regressions']
        if status['summary']['errors'] or not status['regressions']['pass']:raise ValueError('current batch/regressions must pass')
        report['link']=read_json(ROOT/manifest['partial_link']['status'])['output']
        verify_hashes(protected)
        path=ROOT/'local/matching_phase1/runs/command4_contract_status.json'
        path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        if publish:(ROOT/'docs/matching_phase1/command4_contract_status.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PASS command4 pinned CFG/conditional pair-store audit; ABBC obligation remains conditional; inputs/baselines unchanged')
    finally:verify_hashes(protected)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args();run(args.publish)
