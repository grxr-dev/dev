"""One parent reconstruction and a fixed-depth pointer-forwarding investigation.

Uses pinned local ROM/metadata and the existing compiler/relocation comparator.
Opaque external effects are explicit test scenarios, never claimed real I/O.
"""
import json
import re
import struct
from diagnostic import ROOT, HERE, run, sha
from nul_count_pilot import evidence, decode

CFG=HERE/'input_parent_config.json'
OUT=ROOT/'local/matching_phase0/input-parent-pilot'
ADDRESS=0x0206655c
CONTEXT=0x020dcbf4
MASK=0xffffffff


def split_pool(code):
    """This one function's pinned, final 4-byte context literal is not code."""
    if len(code)%4 or struct.unpack_from('<I',code,len(code)-4)[0]!=CONTEXT:
        raise ValueError('expected final context literal')
    rows=decode(code[:-4],ADDRESS)
    refs=[]
    for pc,op,args in rows:
        m=re.fullmatch(r'r\d+, \[pc(?:, #(0x[0-9a-f]+|\d+))?\]',args)
        if op=='ldr' and m:
            target=pc+8+int(m[1] or '0',0)
            if target!=ADDRESS+len(code)-4:raise ValueError('unexpected literal reference')
            refs.append(pc)
    if not refs:raise ValueError('unused/unproven pool')
    return rows,{'address':hex(ADDRESS+len(code)-4),'value':hex(CONTEXT),'references':[hex(pc) for pc in refs]}


def parent_trace(rows, pool, *, predicate, start, end, header, prepare_result=1,
                 read_result=32, initialize_header=True):
    """Bounded decoded-operation model; calls use declared scenario effects.

    start/end are the context values produced by the opaque preparation stub.
    header is the word written by the opaque 32-byte-call stub. No real guest,
    filesystem or host C pointer access occurs. Input is a safe modeled pointer.
    """
    if predicate not in (0,1):raise ValueError('known predicate returns 0 or 1')
    regs={f'r{i}':0xabc00000+i for i in range(13)}
    regs.update(r0=0x5000,sp=0x8000,lr=0x9000)
    saved={k:v for k,v in regs.items() if k not in ('r0','r1','r2','r3','lr')}
    memory={int(pool['address'],16):CONTEXT}
    stack={};calls=[];loads=[];writes=[];path=[]
    pc=rows[0][0];program={a:(op,args) for a,op,args in rows};z=False;frame=None
    def reg(s):return 'r11' if s=='fp' else s
    def value(s):return int(s[1:],0)&MASK if s.startswith('#') else regs[reg(s)]
    for _ in range(40):
        if pc not in program:raise ValueError('escaped parent code')
        op,args=program[pc];path.append(pc);next_pc=pc+4
        if op=='push':
            names=[reg(s) for s in args[1:-1].split(', ')]
            regs['sp']-=4*len(names)
            for i,name in enumerate(names):
                at=regs['sp']+4*i;stack[at]=regs[name];writes.append({'pc':pc,'address':at,'value':regs[name]})
        elif op=='pop':
            names=[reg(s) for s in args[1:-1].split(', ')];target=None
            for i,name in enumerate(names):
                v=stack[regs['sp']+4*i]
                if name=='pc':target=v
                else:regs[name]=v
            regs['sp']+=4*len(names)
            if target!=0x9000 or any(regs[k]!=v for k,v in saved.items()):raise ValueError('return/preserved state')
            return {'return':regs['r0'],'calls':calls,'loads':loads,'stack_writes':writes,'path':path,'frame':frame}
        elif op in ('add','sub','lsr'):
            dest,left,right=args.split(', ');a,b=value(left),value(right)
            regs[reg(dest)]=((a+b) if op=='add' else (a-b) if op=='sub' else a>>b)&MASK
            if dest=='sp' and op=='sub':frame=regs['sp']
        elif op=='mov':
            dest,source=args.split(', ');regs[reg(dest)]=value(source)
        elif op=='ldr':
            m=re.fullmatch(r'(r\d+), \[(pc|sp|r\d+)(?:, #(0x[0-9a-f]+|\d+))?\]',args)
            if not m:raise ValueError('unsupported word load')
            dest,base,offset=m.groups();at=(pc+8 if base=='pc' else regs[base])+int(offset or '0',0)
            source=stack if base=='sp' else memory
            if at not in source:raise ValueError('uninitialized/outside modeled word read')
            regs[dest]=source[at];loads.append({'pc':pc,'address':at,'value':source[at]})
        elif op=='cmp':
            left,right=args.split(', ');z=value(left)==value(right)
        elif op=='beq':
            if z:next_pc=value(args)
        elif op=='b':next_pc=value(args)
        elif op=='bl':
            target=value(args);a=[regs[f'r{i}'] for i in range(3)]
            count={0x0200aee8:1,0x0200abbc:2,0x020665cc:1,0x0200aa5c:3,0x0200ab7c:1}.get(target)
            if count is None:raise ValueError('unapproved call')
            relevant=a[:count]
            if target==0x020665cc:
                if a[0]!=0x5000:raise ValueError('wrong input pointer')
                result=predicate
                # Deliberately mutate context after its snapshot: neither body
                # may recompute the false result from these later values.
                memory[CONTEXT+0x20]=0xdead;memory[CONTEXT+0x24]=0xbeef
            else:
                if a[0]!=CONTEXT:raise ValueError('wrong context')
                result=0
                if target==0x0200abbc:
                    if a[1]!=0x5000:raise ValueError('wrong preparation input')
                    memory[CONTEXT+0x20]=start&MASK;memory[CONTEXT+0x24]=end&MASK
                    result=prepare_result
                elif target==0x0200aa5c:
                    if a[1]!=frame or a[2]!=32:raise ValueError('wrong stack-buffer call ABI')
                    if initialize_header:stack[frame]=header&MASK
                    relevant=[CONTEXT, 'frame+0', 32];result=read_result
            calls.append({'target':hex(target),'args':relevant})
            for i in range(4):regs[f'r{i}']=0xd00d0000+i
            regs['r0']=result&MASK;regs['lr']=next_pc
        else:raise ValueError('unsupported parent operation '+op)
        pc=next_pc
    raise ValueError('parent instruction budget')


def analyze():
    evidence()
    cfg=json.loads(CFG.read_text(encoding='utf-8'));raw=(ROOT/cfg['extracted_arm9']).read_bytes()
    body=raw[0x6655c:0x665cc]
    assert sha(body)==cfg['reference_sha256']
    original,pool=split_pool(body)
    metadata=ROOT/cfg['metadata'];xrefs=[]
    for file in metadata.rglob('relocs.txt'):
        for line in file.read_text(encoding='utf-8').splitlines():
            if 'to:0x0206655c ' in line:xrefs.append(line)
    sites=(0x020431c4,0x02058c9c,0x0206af6c,0x0206afd8,0x0206b1ac,0x0207b898,0x02083670,0x02085c68)
    assert sorted(xrefs)==[f'from:0x{pc:08x} kind:arm_call to:0x0206655c module:main' for pc in sites]
    windows={}
    # Fixed endpoint windows only; stop at the opaque return-producing call.
    for start,end in ((0x02083660,0x02083674),(0x02085ba8,0x02085bf8),(0x0200aee8,0x0200af10)):
        windows[f'{start:08x}-{end:08x}']=decode(raw[start-0x02000000:end-0x02000000],start)
    pointer_argument=struct.unpack_from('<I',raw,0x86004)[0]
    assert pointer_argument==0x020d1e94
    return {'original':original,'pool':pool,'direct_xrefs':xrefs,'windows':windows,
            'producer_call':'0x02085be8 -> 0x020660fc','producer_arg0':hex(pointer_argument),
            'producer_arg1':'0xffffffff','path':['0x02085bec: r1=returned pointer','0x02085bf4: call 02083660',
            '0x02083664: r6=r1','0x0208366c: r0=r6','0x02083670: call 0206655c'],
            'string_base_extent_termination':'not established; opaque returned pointer',
            'different_allocation':'return of 020508f0(0x14) at 02085bd4/BD8 is r0 object argument to 02083660, not string r1; allocator contract not proved here'}


def verify_result(before):
    result=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    if result['compile']['exit_code']:raise ValueError('compiler failed')
    original,op=split_pool(bytes.fromhex(result['reference_hex']))
    compiled,cp=split_pool(bytes.fromhex(result['compiled_hex']))
    cases=[]
    for predicate in (0,1):
        for start,end in ((0,0),(4,40),(0x100,0x80),(0xfffffff0,0x10)):
            for header in (0,0xffffffff,0x12345678):
                kwargs=dict(predicate=predicate,start=start,end=end,header=header,prepare_result=0,read_result=0)
                a=parent_trace(original,op,**kwargs);b=parent_trace(compiled,cp,**kwargs)
                expected=(header>>8) if predicate else (end-start)&MASK
                assert a['return']==b['return']==expected
                assert a['calls']==b['calls']
                assert len(a['calls'])==(5 if predicate else 4)
                cases.append({'scenario':kwargs,'original':a,'compiled':b})
    assert analyze()==before
    details={'analysis':before,'finite_scenarios':len(cases),'scenarios':cases,
             'original_code_bytes':len(original)*4,'compiled_code_bytes':len(compiled)*4,
             'original_pool':op,'compiled_pool':cp,'effects_scope':'conditional opaque-call scenarios only; no full callee equivalence claim'}
    (OUT/'behavior.json').write_text(json.dumps(details,indent=2)+'\n',encoding='utf-8')
    print(f'PARENT CONTROL/ABI PASS: {len(cases)} declared scenarios; dynamic string bounds UNPROVEN; Gate0 OPEN')
    return 0


def main():
    before=analyze()
    run(HERE/'input_parent.c',OUT,CFG)
    return verify_result(before)


if __name__=='__main__':raise SystemExit(main())
