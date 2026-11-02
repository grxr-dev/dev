"""One suffix caller and four immediate input-forwarding paths, not a sweep.

Reuses the prior bounded counter checker and compiler/ELF comparator. Detailed
original bytes, instruction windows, modeled reads/writes stay in local/.
"""
import itertools
import json
import re
import struct
from diagnostic import ROOT, HERE, run, sha
from nul_count_pilot import evidence, decode, trace as counter_trace

CFG = HERE/'suffix_caller_config.json'
OUT = ROOT/'local/matching_phase0/suffix-caller-pilot'
MASK = 0xffffffff


def valid_object(data):
    if not isinstance(data,bytes) or 0 not in data:
        raise ValueError('out of contract: readable terminated object required')
    n = data.index(0)
    if n < 3:
        raise ValueError('out of contract: n>=3; no short-input ARM/C execution')
    return n


def predicate_trace(rows, counter, data, alignment=0):
    """Small decoded-operation model; not an independent CPU emulator.

    No host pointer dereference; all modeled byte reads bounds-check first.
    The only nested call allowed is the already characterized byte counter.
    """
    valid_object(data)
    base=0x1000+alignment
    if alignment not in range(4) or base+len(data)>MASK:raise ValueError('address domain')
    regs={f'r{i}':0xabc00000+i for i in range(13)}
    regs.update(r0=base,sp=0x8000,lr=0x9000)
    preserved={k:v for k,v in regs.items() if k not in ('r0','r1','r2','r3','lr')}
    program={pc:(op,args) for pc,op,args in rows}
    pc=rows[0][0];z=False
    stack={};reads=[];writes=[];path=[];calls=[]
    def value(token):return int(token[1:],0)&MASK if token.startswith('#') else regs[token]
    for _ in range(32):
        if pc not in program:raise ValueError('escaped caller')
        op,args=program[pc];path.append(pc);next_pc=pc+4
        if op=='bne':
            if not z:next_pc=value(args)
            pc=next_pc;continue
        if op.endswith('eq'):
            if not z:pc=next_pc;continue
            op=op[:-2]
        if op=='push' and args=='{r4, lr}':
            regs['sp']-=8
            for i,name in enumerate(('r4','lr')):
                at=regs['sp']+4*i;stack[at]=regs[name]
                writes.append({'pc':pc,'address':at,'width':4,'value':regs[name]})
        elif op=='pop' and args=='{r4, pc}':
            regs['r4']=stack[regs['sp']];target=stack[regs['sp']+4];regs['sp']+=8
            if target!=0x9000 or any(regs[k]!=v for k,v in preserved.items()):raise ValueError('bad return/preserved state')
            return {'return':regs['r0'],'registers':regs,'reads':reads,'stack_writes':writes,'calls':calls,'path':path,'return_pc':target}
        elif op=='bl' and value(args)==0x02067f74:
            if regs['r0']!=base:raise ValueError('changed counter argument')
            nested=counter_trace(counter,data,base)
            regs['lr']=next_pc
            calls.append({'pc':pc,'target':value(args),'arg0':base,'lr':next_pc})
            for name in ('r0','r1','r2'):regs[name]=nested['registers'][name]
            z=bool(nested['nzcv'][1]);reads.extend(nested['reads'])
        elif op in ('ldrb','ldrsb'):
            m=re.fullmatch(r'(r\d+), \[(r\d+), (r\d+|#-?\d+|#-?0x[0-9a-f]+)\]',args)
            if not m:raise ValueError('unsupported suffix address')
            dest,ptr,index=m.groups();at=(regs[ptr]+value(index))&MASK;offset=at-base
            if not 0<=offset<len(data):raise ValueError('out-of-object suffix read')
            byte=data[offset];reads.append({'pc':pc,'offset':offset,'width':1,'byte':byte})
            regs[dest]=(byte-256 if op=='ldrsb' and byte>=128 else byte)&MASK
        elif op=='cmp':
            left,right=args.split(', ');z=value(left)==value(right)
        elif op in ('add','sub','lsr'):
            dest,left,right=args.split(', ');a,b=value(left),value(right)
            regs[dest]=((a+b) if op=='add' else (a-b) if op=='sub' else (a>>b))&MASK
        elif op=='clz':
            dest,source=args.split(', ');regs[dest]=32-value(source).bit_length()
        elif op=='mov':
            dest,source=args.split(', ');regs[dest]=value(source)
        else:raise ValueError('unsupported caller operation: '+op+' '+args)
        pc=next_pc
    raise ValueError('caller instruction budget')


def verify_case(original, compiled, counter, data, alignment=0):
    n=valid_object(data)
    expected=int(data[n-3:n]==b'cmp')
    suffix=[n-3]
    if data[n-3]==0x63:
        suffix.append(n-2)
        if data[n-2]==0x6d:suffix.append(n-1)
    results=[predicate_trace(rows,counter,data,alignment) for rows in (original,compiled)]
    for result in results:
        assert result['return']==expected
        assert [r['offset'] for r in result['reads']]==list(range(n+1))+suffix
        assert len(result['calls'])==1 and len(result['stack_writes'])==2
    return results


def cases():
    for i,word in enumerate(itertools.product((1,0x63,0x6d,0x70,0x80,0xff),repeat=3)):
        yield bytes(word)+b'\0',i%4
    for position in range(3):
        for byte in range(256):
            suffix=bytearray(b'cmp');suffix[position]=byte
            yield b'XYZ'+suffix+b'\0unread',position
    for length in (0,1,7,31,255):
        for alignment in range(4):
            for suffix in (b'cmp',b'cmx',b'xmp',b'Cmp'):
                yield b'Q'*length+suffix+b'\0',alignment


def analyze():
    verified=evidence()  # prior counter, ROM prefix and ten metadata identities
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    raw=(ROOT/cfg['extracted_arm9']).read_bytes()
    assert sha(raw[0x665cc:0x66614])==cfg['reference_sha256']
    metadata=ROOT/cfg['metadata'];xrefs=[]
    for file in sorted(metadata.rglob('relocs.txt')):
        for line in file.read_text(encoding='utf-8').splitlines():
            if 'to:0x020665cc ' in line:xrefs.append({'module':file.parent.name,'entry':line})
    expected=(0x020661e4,0x020662dc,0x02066408,0x02066590)
    assert xrefs==[{'module':'arm9','entry':f'from:0x{pc:08x} kind:arm_call to:0x020665cc module:main'} for pc in expected]
    windows={}
    def window(start,end):
        rows=decode(raw[start-0x02000000:end-0x02000000],start)
        assert len(rows)*4==end-start
        windows[f'{start:08x}-{end:08x}']=rows
        return rows
    # Only entry-to-call slices, one local preparation helper, two preparation
    # API entry bodies, and ONE representative literal producer upstream.
    for start,end,hold in ((0x020661b8,0x020661e8,'r8'),(0x020662ac,0x020662e0,'r7'),
                           (0x020663e0,0x0206640c,'r6'),(0x0206655c,0x02066594,'r4')):
        rows=window(start,end)
        assert any(op=='mov' and args==hold+', r0' for _,op,args in rows)
        setup=next(row for row in rows if row[0]==end-8) if hold!='r4' else next(row for row in rows if row[0]==0x02066580)
        assert setup[1:] == ('mov','r0, '+hold)
    for start,end in ((0x020664f8,0x0206655c),(0x0200aee8,0x0200af10),
                      (0x0200abbc,0x0200ac04),(0x020275bc,0x020275d8)):
        window(start,end)
    # Literal input to parent 020661B8: no full private/resource string logging.
    pool=0x020278f8;pointer=struct.unpack_from('<I',raw,pool-0x02000000)[0]
    assert pointer==0x020c8c14
    at=pointer-0x02000000;end=raw.index(0,at,at+128);literal=raw[at:end]
    assert len(literal)==36 and literal[-3:]==b'cmp'
    return {'direct_xrefs':xrefs,'windows':windows,'counter_evidence':verified,
            'literal_producer':{'load_pc':'0x020275bc','pool':hex(pool),'pointer':hex(pointer),
                                'call_pc':'0x020275d4','callee':'0x020661b8','nul_offset':len(literal),
                                'suffix_hex':literal[-3:].hex(),'sha256_without_nul':sha(literal)},
            'global_minimum_length_proven':False}


def verify_result(before):
    result=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    if result['compile']['exit_code']:raise ValueError('compilation failed')
    original=decode(bytes.fromhex(result['reference_hex']),0x020665cc)
    compiled=decode(bytes.fromhex(result['compiled_hex']),0x020665cc)
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    raw=(ROOT/cfg['extracted_arm9']).read_bytes()
    counter=decode(raw[0x67f74:0x67f9c],0x02067f74)
    count=0
    for data,alignment in cases():verify_case(original,compiled,counter,data,alignment);count+=1
    assert analyze()==before
    details={'analysis':before,'finite_cases':count,'comparison_exit':int(not result['comparison']['equal']),
             'match_example':verify_case(original,compiled,counter,b'XYZcmp\0'),
             'last_byte_mismatch':verify_case(original,compiled,counter,b'XYZcmx\0'),
             'first_byte_mismatch':verify_case(original,compiled,counter,b'XYZCmp\0')}
    (OUT/'behavior.json').write_text(json.dumps(details,indent=2)+'\n',encoding='utf-8')
    print(f'BEHAVIOR PASS: {count} safe cases, exact ordered byte reads and returns; minimum-length provenance UNPROVEN; Gate0 OPEN')
    return 0


def main():
    before=analyze()
    run(HERE/'suffix_caller.c',OUT,CFG)
    return verify_result(before)


if __name__=='__main__':raise SystemExit(main())
