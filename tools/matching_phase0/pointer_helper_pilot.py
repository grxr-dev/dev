"""Fixed shared-buffer helper pilot; no generic guest-call or formatter emulator.

Raw original code/windows stay local. The formatter body remains opaque; its
result register is varied to check that the helper returns its own fixed alias.
"""
import json
import re
import struct
from diagnostic import ROOT, HERE, run, sha
from nul_count_pilot import evidence, decode

CFG=HERE/'pointer_helper_config.json'
OUT=ROOT/'local/matching_phase0/pointer-helper-pilot'
ADDRESS=0x020660fc
SHARED=0x020dcbb4


def terminator_offset(return_count,limit):
    """9058's unsigned normal-return decision for a nonnull destination.

    Arithmetic only; does NOT assert the selected offset is valid storage.
    """
    n=return_count&0xffffffff;cap=limit&0xffffffff
    return n if n<cap else cap-1 if cap else None


def split_pool(body):
    if len(body)%4 or len(body)<8 or struct.unpack_from('<I',body,len(body)-4)[0]!=SHARED:
        raise ValueError('unexpected helper literal')
    rows=decode(body[:-4],ADDRESS);refs=[]
    for pc,op,args in rows:
        m=re.fullmatch(r'r\d+, \[pc(?:, #(0x[0-9a-f]+|\d+))?\]',args)
        if op=='ldr' and m:
            if pc+8+int(m[1] or '0',0)!=ADDRESS+len(body)-4:raise ValueError('unexpected literal target')
            refs.append(pc)
    if not refs:raise ValueError('missing pool reference')
    return rows,{'address':ADDRESS+len(body)-4,'value':SHARED,'references':refs}


def helper_trace(rows,pool,format_pointer=0x5000,incoming_r1=0xffffffff,call_result=0):
    """Small decoded-operation check conditional on an ABI-preserving call.

    No input/output string memory is accessed. No claim that a null/invalid
    format would return normally; test pointers are abstract valid objects.
    """
    if format_pointer<=0:raise ValueError('valid abstract format pointer required')
    regs={f'r{i}':0xabc00000+i for i in range(13)}
    regs.update(r0=format_pointer,r1=incoming_r1&0xffffffff,sp=0x8000,lr=0x9000)
    saved={k:v for k,v in regs.items() if k not in ('r0','r1','r2','r3','lr')}
    stack={};writes=[];calls=[]
    for pc,op,args in rows:
        if op=='push' or (op=='stmdb' and args.startswith('sp!, ')):
            text=args if op=='push' else args[5:]
            names=text[1:-1].split(', ');regs['sp']-=4*len(names)
            for i,name in enumerate(names):
                at=regs['sp']+4*i;stack[at]=regs[name];writes.append((at,regs[name]))
        elif op=='pop' or (op=='ldm' and args.startswith('sp!, ')):
            text=args if op=='pop' else args[5:]
            names=text[1:-1].split(', ');target=None
            for i,name in enumerate(names):
                value=stack[regs['sp']+4*i]
                if name=='pc':target=value
                else:regs[name]=value
            regs['sp']+=4*len(names)
            if target!=0x9000 or any(regs[k]!=v for k,v in saved.items()):raise ValueError('return/preserved registers')
            if len(calls)!=1:raise ValueError('expected one call')
            return {'return':regs['r0'],'call':calls[0],'stack_writes':writes,'sp':regs['sp']}
        elif op in ('sub','add'):
            dest,left,imm=args.split(', ')
            if dest!='sp' or left!='sp':raise ValueError('unexpected arithmetic')
            regs['sp']+=int(imm[1:],0)*(-1 if op=='sub' else 1)
        elif op=='mov':
            dest,source=args.split(', ')
            regs[dest]=int(source[1:],0) if source.startswith('#') else regs[source]
        elif op=='ldr':
            m=re.fullmatch(r'(r\d+), \[pc, #(0x[0-9a-f]+|\d+)\]',args)
            if not m or pc+8+int(m[2],0)!=pool['address']:raise ValueError('unexpected load')
            regs[m[1]]=pool['value']
        elif op=='bl' and args=='#0x2019024':
            calls.append([regs['r0'],regs['r1'],regs['r2']])
            for i in range(4):regs[f'r{i}']=0xd00d0000+i
            regs['r0']=call_result&0xffffffff;regs['lr']=pc+4
        else:raise ValueError('unexpected helper instruction '+op+' '+args)
    raise ValueError('missing return')


def analyze():
    evidence()
    cfg=json.loads(CFG.read_text(encoding='utf-8'));raw=(ROOT/cfg['extracted_arm9']).read_bytes()
    body=raw[0x660fc:0x66124]
    assert sha(body)==cfg['reference_sha256']
    rows,pool=split_pool(body)
    metadata=ROOT/cfg['metadata']
    counts={}
    for file in sorted(metadata.rglob('symbols.txt')):
        counts[str(file.relative_to(metadata))]=sum(' kind:function(' in line for line in file.read_text(encoding='utf-8').splitlines())
    assert sorted(counts.values())==[0,11,2977]
    symbols=(metadata/'arm9/symbols.txt').read_text(encoding='utf-8')
    assert 'func_02066124 kind:function(arm,size=0x94) addr:0x02066124' in symbols
    assert 'data_020dcbb4 kind:bss addr:0x020dcbb4' in symbols
    assert 'data_020dcbf4 kind:bss addr:0x020dcbf4' in symbols
    site=decode(raw[0x85be0:0x85bf8],0x02085be0)
    assert site[2][1:]==('bl','#0x20660fc')
    assert struct.unpack_from('<I',raw,0x86004)[0]==0x020d1e94
    start=0xd1e94;end=raw.index(0,start,start+64);fmt=raw[start:end]
    assert len(fmt)==29 and fmt.count(b'%')==1 and fmt[23:25]==b'%c'
    wrappers={'02019024-02019058':decode(raw[0x19024:0x19058],0x02019024),
              '02019058-020190bc':decode(raw[0x19058:0x190bc],0x02019058)}
    return {'original':rows,'pool':pool,'callsite':site,'wrappers':wrappers,
            'format':{'pointer':'0x020d1e94','bytes_before_nul':len(fmt),'sha256_with_nul':sha(fmt+b'\0'),
                      'single_conversion':'%c','conversion_offset':23,'first_argument':0x65,
                      'conditional_printf_output_length':len(fmt)-1,
                      'output_length_is_executed_engine_proof':False},
            'adjacent_symbol_distance':0x40,'distance_is_proven_object_capacity':False,
            'inferred_function_records':counts}


def verify_result(before):
    r=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    if r['compile']['exit_code']:raise ValueError('compiler failed')
    original,op=split_pool(bytes.fromhex(r['reference_hex']))
    compiled,cp=split_pool(bytes.fromhex(r['compiled_hex']))
    cases=[]
    for fmt in (0x5000,0x5001):
        for r1 in (0,0xffffffff,0x1234):
            for result in (0,1,0xffffffff,0xdeadbeef):
                a=helper_trace(original,op,fmt,r1,result);b=helper_trace(compiled,cp,fmt,r1,result)
                assert a['return']==b['return']==SHARED
                assert a['call']==b['call']==[SHARED,fmt,0x65]
                assert len(a['stack_writes'])==1 and len(b['stack_writes'])==2
                cases.append({'format_pointer':fmt,'incoming_r1':r1,'opaque_result':result,'original':a,'compiled':b})
    assert analyze()==before
    (OUT/'behavior.json').write_text(json.dumps({'analysis':before,'cases':cases,'count':len(cases),
          'scope':'fixed returned alias and meaningful call arguments under normal ABI-return assumption; no formatter memory-effect proof'},indent=2)+'\n',encoding='utf-8')
    print(f'HELPER PASS: {len(cases)} conditional call scenarios; fixed shared alias; no output-capacity guarantee; Gate0 OPEN')
    return 0


def main():
    before=analyze();run(HERE/'pointer_helper.c',OUT,CFG)
    return verify_result(before)


if __name__=='__main__':raise SystemExit(main())
