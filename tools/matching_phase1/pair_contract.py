"""Bounded AD94 CFG/contract audit reusing pinned inputs and the context trace checker.

No C reconstruction, guest dispatch, runtime BSS reads, or linker invocation.
Opaque outcomes are countermodels/assumptions, not observations of dispatcher behavior.
"""
import argparse
import itertools
import json
import re
import struct
from batch import ROOT,HERE,read_json,validate_manifest,verify_inputs,verify_hashes,sha
from context_evidence import call_target
from context_models import trace,initialized
from nul_count_pilot import decode

ADDRESS=0x0200ad94
SIZE=340
CODE_SIZE=336
SHA256='c536d8986a58164efd05d54598aa774b5ad63f2a1b8c6442df467c2ba791be80'
HELPER=(0x0200a8d8,76,'9950e1d6961160f5bdd7f0c6962186ca0997dd2322879178eaf9a73c3ce659e0')
BASELINE_TEN_LF='2a54db4e4a040e987ade5e682f2895fde85650e7dbcb2b880b416a888f9fff13'
EXPECTED_RELOCS=[
    'from:0x0200ae24 kind:arm_call to:0x0200a8d8 module:main',
    'from:0x0200aed8 kind:arm_call to:0x0200a464 module:main',
    'from:0x0200aee4 kind:load to:0x020d4b6c module:main'
]


def cfg(rows,indirect_calls=()):
    nodes={pc for pc,_,_ in rows};edges=[];calls=[];returns=[];predicates=[]
    if len(nodes)!=len(rows) or sorted(nodes)!=list(range(rows[0][0],rows[-1][0]+4,4)):raise ValueError('CFG code coverage')
    for pc,op,args in rows:
        if op=='bl':calls.append((pc,int(args[1:],0)))
        if op=='blx' and pc not in indirect_calls:raise ValueError('unknown indirect call')
        if op in ('b','beq','bne','ble','bgt','bhi','bls'):
            target=int(args[1:],0)
            edges.append((pc,target,None if op=='b' else True))
            if op!='b':edges.append((pc,pc+4,False));predicates.append(pc)
        elif (op.startswith('pop') and 'pc' in args) or op.startswith('bx'):
            if op.startswith('bx') and args!='lr':raise ValueError('unknown indirect control')
            conditional=op.endswith(('eq','ne','gt','ls'))
            edges.append((pc,'RETURN',True if conditional else None));returns.append(pc)
            if conditional:edges.append((pc,pc+4,False));predicates.append(pc)
        else:
            if op.startswith('bl') and op not in ('bl','blx','ble','bls'):raise ValueError('unknown indirect call')
            if args.startswith('pc,'):raise ValueError('unmodeled PC write')
            conditional=op.endswith(('eq','ne','gt','ls'))
            for condition in (True,False) if conditional else (None,):edges.append((pc,pc+4,condition))
            if conditional:predicates.append(pc)
        if any(target!='RETURN' and target not in nodes for source,target,_ in edges if source==pc):raise ValueError('CFG escapes code or enters literal pool')
    reachable={rows[0][0]}
    while True:
        added={target for source,target,_ in edges if source in reachable and target!='RETURN'}
        if added<=reachable:break
        reachable|=added
    if reachable!=nodes:raise ValueError('unreachable/unexplained original code')
    return {'nodes':sorted(nodes),'edges':edges,'calls':calls,'returns':returns,'predicates':predicates,
            'back_edges':[edge for edge in edges if edge[1]!='RETURN' and edge[1]<=edge[0]]}


def load_reference():
    manifest=read_json(HERE/'batch.json');validate_manifest(manifest);protected,image=verify_inputs(manifest)
    metadata=ROOT/manifest['inputs']['metadata_root'];symbols=(metadata/'arm9/symbols.txt').read_text()
    for address,size,digest in [(ADDRESS,SIZE,SHA256),HELPER]:
        if sha(image[address-0x02000000:address-0x02000000+size])!=digest:raise ValueError('audit reference hash changed')
        line=f'func_{address:08x} kind:function(arm,size=0x{size:x}) addr:0x{address:08x}'
        if symbols.splitlines().count(line)!=1:raise ValueError('audit inferred ARM boundary changed')
    if 'data_020d4b6c kind:bss addr:0x020d4b6c' not in symbols.splitlines():raise ValueError('global BSS attribution changed')
    relocation_maps={path.relative_to(metadata).as_posix():path.read_text().splitlines() for path in sorted(metadata.rglob('relocs.txt'))}
    outgoing=[line for line in relocation_maps['arm9/relocs.txt'] if ADDRESS<=int(line.split('from:')[1].split()[0],16)<ADDRESS+SIZE]
    if outgoing!=EXPECTED_RELOCS:raise ValueError('AD94 relocation policy changed')
    body=image[ADDRESS-0x02000000:ADDRESS-0x02000000+SIZE]
    if struct.unpack_from('<I',body,CODE_SIZE)[0]!=0x020d4b6c:raise ValueError('literal word changed')
    rows=decode(body[:CODE_SIZE],ADDRESS);graph=cfg(rows)
    if graph['calls']!=[(0x0200ae24,0x0200a8d8),(0x0200aed8,0x0200a464)] or graph['returns']!=[0x0200ae34,0x0200ae54,0x0200aee0]:raise ValueError('call/return coverage changed')
    for pc,target in graph['calls']:
        if call_target(image,pc)!=target:raise ValueError('original call opcode differs')
    literals=[pc+8+int(re.search(r'#(0x[0-9a-f]+|\d+)',args)[1],0) for pc,op,args in rows if op=='ldr' and '[pc,' in args]
    if literals!=[ADDRESS+CODE_SIZE]*2:raise ValueError('literal references changed')
    if struct.unpack_from('<I',body,0x0200ae3c-ADDRESS)[0]&0xf00:raise ValueError('ANDS immediate carry assumption changed')
    helper_body=image[0xa8d8:0xa924]
    if struct.unpack_from('<I',helper_body,72)[0]!=0x020d4b68:raise ValueError('helper pool ownership')
    helper_graph=cfg(decode(helper_body[:72],HELPER[0]))
    if helper_graph['calls']!=[(0x0200a8e0,0x0200a990),(0x0200a8e8,0x02006e9c),(0x0200a910,0x02006eb0)]:raise ValueError('small helper call frontier changed')
    for pc,target in helper_graph['calls']:
        if call_target(image,pc)!=target:raise ValueError('helper call opcode changed')
    verify_hashes(protected)
    return manifest,protected,rows,graph,helper_graph


def scenarios():
    yield 'leading-slash',b'/','enabled'
    yield 'leading-backslash',b'\\','enabled'
    for index in range(4):
        prefix=b'abcd'[:index]
        yield f'nul-{index}',prefix+b'\0','enabled'
        if index:
            yield f'slash-{index}',prefix+b'/','enabled'
            yield f'backslash-{index}',prefix+b'\\','enabled'
        yield f'colon-{index}-null',prefix+b':\0','null'
        yield f'colon-{index}-disabled',prefix+b':\0','disabled'
        for label,following in [('nul',b'\0'),('slash',b'/'),('backslash',b'\\')]:
            yield f'colon-{index}-{label}',prefix+b':'+following,'enabled'
    yield 'four-undelimited',b'abcd','enabled'


def explore(rows,graph):
    covered=set();condition_values=set();paths=set();families=[];cases=0;nonzero=0;mode0_nonzero=0;mode0_incomplete=0;maximum=0
    for name,data,lookup in scenarios():
        family_exits=set();family_pcs=set();family_dispatch=False
        for mode,result,mask in itertools.product((0,0x12345678),(0,1,0x80000000),range(4)):
            checked=trace(rows,initialized(bytes(68)),protocol='pair_producer',dispatch_result=result,
                          producer={'input':data,'lookup':lookup,'mode':mode,'pair_mask':mask})
            observed=set(checked['edges'])
            if not observed<=set(graph['edges']):raise ValueError('trace outside CFG')
            if any(event['origin']=='instruction' for event in checked['pair_writes']):raise ValueError('unexpected direct pair write')
            if checked['stack_bytes']!=40:raise ValueError('AD94 frame changed')
            dispatch=any(call[0]==0x0200a464 for call in checked['calls'])
            family_dispatch|=dispatch
            if checked['return']!=(result if dispatch else 0):raise ValueError('raw dispatcher result not preserved')
            if dispatch:
                expected_initialized=set(range(20))|{24,25}|set(range(44,68))
                if {index for index,byte in enumerate(checked['call_states'][0]['scratch']) if byte is not None}!=expected_initialized:
                    raise ValueError('partial scratch initialization differs')
            pair_mask=sum(1<<index for index in range(2) if all(value is not None for value in checked['output_pair_bytes'][4*index:4*index+4]))
            if pair_mask!=(mask if dispatch and mode==0 else 0):raise ValueError('conditional opaque pair writes differ')
            cases+=1;nonzero+=checked['return']!=0
            if checked['return'] and mode==0:
                mode0_nonzero+=1;mode0_incomplete+=pair_mask!=3
            covered|=observed;condition_values.update(checked['conditions']);paths.add(tuple(checked['edges']))
            family_exits.add(checked['path'][-1]);family_pcs.update(checked['path']);maximum=max(maximum,len(checked['path']))
        families.append({'name':name,'input_length':len(data),'lookup_summary':lookup,
                         'return_sites':[hex(pc) for pc in sorted(family_exits)],'executed_original_pc_count':len(family_pcs),
                         'return_rule':'RAW_COMMAND4_RESULT' if family_dispatch else 'ZERO',
                         'mode0_success_pair_obligation':'UNPROVEN_COMMAND4_SYNCHRONOUS_WRITE8' if family_dispatch else 'NOT_REACHED'})
    if covered!=set(graph['edges']) or condition_values!={(pc,condition) for pc in graph['predicates'] for condition in (False,True)}:
        raise ValueError('incomplete CFG edge/predicate coverage')
    return {'family_count':len(families),'scenario_count':cases,'distinct_control_paths':len(paths),'families':families,
            'node_coverage':len({pc for pc,_,_ in covered}),'edge_coverage':len(covered),'predicate_outcomes':len(condition_values),
            'maximum_modeled_steps':maximum,'return_nonzero_scenarios':nonzero,'mode0_nonzero_scenarios':mode0_nonzero,
            'mode0_nonzero_incomplete_pair_countermodels':mode0_incomplete,'countermodels_are_not_runtime_observations':True,
            'direct_pair_write_mask':0,'opaque_pair_masks_tested':[0,1,2,3]}


def preserve_baselines(manifest):
    protected={};audits=[]
    entries=manifest['partial_link']['baselines']
    if [entry['symbol_count'] for entry in entries]!=[6,8,10] or entries[-1]['report_sha256_lf']!=BASELINE_TEN_LF:
        raise ValueError('required immutable six/eight/ten baselines')
    for entry in entries:
        report_path=ROOT/entry['report'];report=read_json(report_path);object_path=ROOT/report['output_path']
        if sha(report_path.read_text().encode())!=entry['report_sha256_lf'] or sha(object_path.read_bytes())!=entry['output_sha256']:
            raise ValueError('immutable baseline changed')
        protected[str(report_path)]=sha(report_path.read_bytes());protected[str(object_path)]=entry['output_sha256']
        audits.append({'symbols':entry['symbol_count'],'output_sha256':entry['output_sha256'],'relinked':False})
        for row in report['inputs']:
            path=ROOT/row['object']
            if sha(path.read_bytes())!=row['object_sha256']:raise ValueError('authored baseline input object changed')
            protected[str(path)]=row['object_sha256']
    return protected,audits


def stack_geometry(manifest):
    image=(ROOT/manifest['inputs']['arm9_path']).read_bytes();frames={}
    for name,address in [('ABBC',0x0200abbc),('ACD0',0x0200acd0),('AD94',ADDRESS)]:
        rows=decode(image[address-0x02000000:address-0x02000000+8],address)
        if rows[0][1]!='push' or rows[1][1]!='sub' or not rows[1][2].startswith('sp, sp, #'):raise ValueError('frame prologue changed')
        saved=4*len(rows[0][2][1:-1].split(', '));reserved=int(rows[1][2].split('#')[1],0)
        frames[name]={'saved':saved,'reserved':reserved,'total':saved+reserved}
    pair_low=-frames['ABBC']['total'];scratch_low=pair_low-frames['ACD0']['total']
    return {'frames':frames,'relative_to_ABBC_entry':{'pair':[pair_low,pair_low+8],
             'ACD0_scratch':[scratch_low,pair_low-frames['ACD0']['saved']],
             'AD94_locals':[scratch_low-frames['AD94']['total'],scratch_low-frames['AD94']['saved']]},
            'pointer_non_retention':'UNPROVEN_EXTERNAL_OBLIGATION'}


def public_cfg(graph):
    return {'nodes':[hex(pc) for pc in graph['nodes']],
            'edges':[{'from':hex(pc),'to':target if target=='RETURN' else hex(target),'condition':condition} for pc,target,condition in graph['edges']],
            'returns':[hex(pc) for pc in graph['returns']],
            'calls':[{'pc':hex(pc),'target':hex(target)} for pc,target in graph['calls']],
            'loop_edges':[{'from':hex(pc),'to':hex(target),'condition':condition} for pc,target,condition in graph['back_edges']]}


def run(publish=False):
    manifest,original_inputs,rows,graph,helper=load_reference();baselines,audits=preserve_baselines(manifest)
    protected=dict(original_inputs,**baselines)
    try:
        coverage=explore(rows,graph)
        report={'schema':'brainage-pair-producer-contract/1','classification':'BRANCH_COMPLETE_AUDIT_EXTERNAL_SAFETY_OBLIGATION_UNRESOLVED',
            'reference':{'address':hex(ADDRESS),'size':SIZE,'code_bytes':CODE_SIZE,'pool_bytes':4,'sha256':SHA256,
                         'literal':{'address':'0x0200aee4','value':'0x020d4b6c','pointee_section':'.bss','runtime_contents':'UNOBSERVED'},
                         'original_relocations':EXPECTED_RELOCS},
            'budget':{'functions_fully_decoded':2,'full_function_bytes_including_pools':416,'existing_caller_prologue_bytes':16,
                      'AD94_step_bound':256,'large_dispatchers_decoded':0},
            'cfg':public_cfg(graph),'small_helper':{'address':hex(HELPER[0]),'size':HELPER[1],'sha256':HELPER[2],
                'code_bytes':72,'pool_bytes':4,'cfg':public_cfg(helper),'loop_termination':'UNKNOWN_LIST_CONTRACT',
                'nested_calls':'OPAQUE; no recursive inspection'},
            'coverage':coverage,'c_body_added':False,'authored_source_symbols':len(manifest['symbols']),'new_partial_link_invocations':0,
            'existing_batch_regression_report':'docs/matching_phase1/batch_status.json',
            'proof_preconditions':['ordinary stable readable input/global/lookup data','normal ABI and normal nested returns',
                                   'scratch/input/pair/owned-stack nonaliasing; scoped virtual effects only'],
            'abbc_pair_safety':'UNRESOLVED: command 4 must initialize both words synchronously on nonzero mode-0 return',
            'success_scratch_initialized_byte_offsets':sorted(set(range(20))|{24,25}|set(range(44,68))),
            'unproven':['runtime BSS descriptor validity','lookup/prefix helper termination and wider effects',
                       'command-4 pair writes and partial-scratch read-before-write policy','non-retention of scratch/output/input stack pointers'],
            'failure_contract':'direct prefix failures return zero before pair publication; dispatcher failures may leave partial pair writes; no rollback',
            'stack_lifetime':stack_geometry(manifest),
            'baselines_unchanged':audits,'protected_original_inputs':len(original_inputs),'protected_original_inputs_unchanged':True,
            'genuine_original_matches':0,'gate0':'OPEN','guest_execution':False,'opaque_summaries_are_proof':False}
        out=ROOT/'local/matching_phase1/runs/pair-producer-contract';out.mkdir(parents=True,exist_ok=True)
        (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
        if publish:(ROOT/'docs/matching_phase1/pair_producer_contract_status.json').write_text(json.dumps(report,indent=2)+'\n')
        print('AUDIT COMPLETE: '+str(coverage['node_coverage'])+' nodes, '+str(coverage['edge_coverage'])+' edges; '+str(coverage['scenario_count'])+' scenarios; pair safety UNRESOLVED; no C/link added')
    finally:verify_hashes(protected)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish-status',action='store_true');run(parser.parse_args().publish_status)
