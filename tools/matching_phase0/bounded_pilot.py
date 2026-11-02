"""One bounded static-analysis/C pilot, reusing diagnostic.py and its ELF checks.

Only the 21 known call windows and the selected seven-instruction helper are
decoded here. Full bytes/disassembly stay ignored locally. The bit-origin check
is a static proof for this straight-line bit transform, NOT an ARM executor.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import capstone
from diagnostic import run,ROOT,HERE

CFG=HERE/'byte_exchange_config.json'
SOURCE=HERE/'byte_exchange.c'
OUT=ROOT/'local/matching_phase0/byte-exchange-pilot'

# Human classification of the exact bounded uses, not recovered symbol names.
NOTES={
 0x020258D8:('forwarded','Result remains r0 at the call to 0x0206810C; r1=0, r2=3. Callee argument meaning unqualified.'),
 0x02025AB0:('index','Copy to r4, then load [sp+r4*4].'),
 0x02042B24:('arithmetic','Shift left 11; form (result<<11)+0x800.'),
 0x0205AEC4:('predicate','MOVS into r6; zero immediately causes conditional return.'),
 0x0205B018:('saved','Store to [sp+0x1C]; ultimate use beyond this window not established.'),
 0x0205EB6C:('predicate','Compare with 4; equality branches to 0x0205EB88.'),
 0x0205EB8C:('predicate','Compare with 4; inequality branches to 0x0205EED0.'),
 0x020601F0:('index','Save to fp; at 0x02060264 used in [lr+fp*4].'),
 0x02061618:('predicate','Signed compare with 1; choose r2=2 for <=1, else 0.'),
 0x020617BC:('predicate','Signed compare with 1; branch for >1.'),
 0x02063A74:('predicate','Compare with 4; choose r2=0 for equality, else 2.'),
 0x02069A40:('arithmetic','Form r3=r7+(result<<2).'),
 0x0206B724:('arithmetic','Copy to r2, then shift left 12 before a later call.'),
 0x0206B790:('arithmetic','Shift result left 12 into r2 before call to 0x020661B8.'),
 0x0206CF1C:('arithmetic','r0 survives two bounded initialization loops; shift left 1 at 0x0206CFAC.'),
 0x0206DC7C:('saved','Copy to r4 before r0 overwritten; ultimate path-specific use unresolved.'),
 0x020708EC:('arithmetic','Save to r5; multiply using r5 at 0x020709C0.'),
 0x020731C8:('arithmetic','Shift left 11; form (result<<11)+0x800.'),
 0x020735E8:('predicate','Compare with 2; equality branches to 0x02073604.'),
 0x020735F8:('predicate','Compare with 4; inequality branches to 0x02073660.'),
 0x02074380:('saved','Copy to r5 before another call; ultimate path-specific use unresolved.'),
}


def bit_origins(instructions):
    """Propagate constants/input-bit origins through ONLY this leaf's op subset.

    Cannot call, access memory, follow branches, or execute machine state. An OR
    or AND requiring a more general Boolean expression is rejected, not guessed.
    The result accounts for all 2**32 input words, excluding timing/ABI scratch.
    """
    registers={'r0':['x'+str(i) for i in range(32)]}
    def value(token):
        if token.startswith('#'):
            n=int(token[1:],0)&0xffffffff;return [(n>>i)&1 for i in range(32)]
        if token not in registers:raise ValueError('read before defined input/scratch register')
        return registers[token][:]
    def shift(bits,kind,n):
        if not 0<=n<32:raise ValueError('unsupported shift')
        if kind=='lsl':return [0]*n+bits[:32-n]
        if kind=='lsr':return bits[n:]+[0]*n
        if kind=='asr':return bits[n:]+[bits[31]]*n
        raise ValueError('unsupported shift')
    def combine(a,b,op):
        if a==b:return a
        if op=='and':
            if a==0 or b==0:return 0
            if a==1:return b
            if b==1:return a
        else:
            if a==1 or b==1:return 1
            if a==0:return b
            if b==0:return a
        raise ValueError('unsupported mixed Boolean origins')
    returned=False
    for position,ins in enumerate(instructions):
        op=ins['mnemonic'];args=[x.strip() for x in ins['operands'].split(',')]
        if op=='bx' and args==['lr'] and position==len(instructions)-1:
            returned=True;continue
        if not args or args[0] not in ('r0','r1','r2'):raise ValueError('unexpected state effect')
        if op=='mov' and len(args)==2:result=value(args[1])
        elif op in ('lsl','lsr','asr') and len(args)==3:result=shift(value(args[1]),op,int(args[2][1:],0))
        elif op in ('and','orr') and len(args) in (3,4):
            left=value(args[1]);right=value(args[2])
            if len(args)==4:
                kind,amount=args[3].split();right=shift(right,kind,int(amount[1:],0))
            result=[combine(a,b,op) for a,b in zip(left,right)]
        else:raise ValueError('outside the static bit-transform subset')
        registers[args[0]]=result
    if not returned:raise ValueError('missing final return')
    return registers['r0']


def analyze():
    cfg=json.loads(CFG.read_text(encoding='utf-8'));rom=(ROOT.parent/cfg['rom_name']).read_bytes()
    if hashlib.sha1(rom).hexdigest()!=cfg['rom_sha1'] or hashlib.sha256(rom).hexdigest()!=cfg['rom_sha256']:raise ValueError('ROM identity')
    data=(ROOT/cfg['extracted_arm9']).read_bytes();maps=ROOT/cfg['metadata']/'arm9'
    offset,entry,base,size=struct.unpack_from('<4I',rom,0x20)
    if base!=0x02000000 or len(data)>size or data!=rom[offset:offset+len(data)]:raise ValueError('extracted main is not the exact ROM prefix')
    functions=[]
    for line in (maps/'symbols.txt').read_text(encoding='utf-8').splitlines():
        m=re.fullmatch(r'(\S+) kind:function\(arm,size=0x([0-9a-f]+)\) addr:0x([0-9a-f]+)',line)
        if m:functions.append((int(m[3],16),int(m[2],16),m[1]))
    relocs=(maps/'relocs.txt').read_text(encoding='utf-8').splitlines()
    sites=[int(re.search(r'from:0x([0-9a-f]+)',line)[1],16) for line in relocs if 'kind:arm_call to:0x020660f4 ' in line]
    if set(sites)!=set(NOTES) or len(sites)!=21:raise ValueError('21-call census changed')
    decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);decoder.detail=True
    def decode(start,end):return list(decoder.disasm(data[start-0x02000000:end-0x02000000],start))
    rows=[];local=[]
    for site in sites:
        caller=[(a,s,n) for a,s,n in functions if a<=site<a+s]
        if len(caller)!=1:raise ValueError('ambiguous caller boundary')
        before=decode(max(caller[0][0],site-32),site)
        writes=[i for i in before if 'r0' in [i.reg_name(x) for x in i.regs_access()[1]]]
        if not writes or writes[-1].mnemonic!='mvn' or writes[-1].op_str!='r0, #0':raise ValueError('sentinel argument evidence changed')
        setup=writes[-1]
        call=decode(site,site+4)
        if len(call)!=1 or call[0].mnemonic!='bl' or call[0].op_str!='#0x20660f4':raise ValueError('call opcode/target')
        after=decode(site+4,min(site+192,caller[0][0]+caller[0][1]))
        consumer=None
        for ins in after:
            reads,writes=ins.regs_access()
            if 'r0' in [ins.reg_name(x) for x in reads]:consumer=ins;break
            if 'r0' in [ins.reg_name(x) for x in writes]:raise ValueError('unexpected overwrite-before-use')
            if ins.mnemonic in ('bl','blx'):consumer=ins;break
        if consumer is None:raise ValueError('consumer outside bounded window')
        category,note=NOTES[site]
        rows.append({'call':f'0x{site:08X}','caller':caller[0][2],'caller_start':f'0x{caller[0][0]:08X}',
                     'argument_setup':f'0x{setup.address:08X}','arg0':'0xFFFFFFFF',
                     'first_use':f'0x{consumer.address:08X}','category':category,'interpretation':note})
        local.append({'call':hex(site),'window':[{'pc':hex(i.address),'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str} for i in [*before,*call,*after]]})
        if site==0x020708EC:
            extra=decode(0x020709C0,0x020709C4)
            if len(extra)!=1 or extra[0].mnemonic!='mul' or extra[0].op_str!='r4, r5, r0':raise ValueError('saved-result secondary-use evidence')
            local[-1]['secondary_use']={'pc':hex(extra[0].address),'bytes':extra[0].bytes.hex(),'op':extra[0].mnemonic+' '+extra[0].op_str}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'call-windows.json').write_text(json.dumps(local,indent=2)+'\n',encoding='utf-8')
    (OUT/'call-sites.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    return rows


def main():
    rows=analyze()
    code=run(SOURCE,OUT,CFG)  # Exact mismatch is an observation, not task failure.
    result=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    expected=['x'+str(i) for i in [*range(8,16),*range(8)]]+[0]*16
    original=bit_origins(result['original_disassembly']);compiled=bit_origins(result['disassembly'])
    if original!=expected or compiled!=expected:raise ValueError('r0 behavioral proof differs')
    proof={'status':'PASS_R0_BIT_MAPPING_ALL_2_POW_32_INPUTS','r0_bit_origins':expected,
           'scope':'r0 result; no timing, original source/prototype or exact scratch-register claim',
           'call_sites':rows,'exact_byte_compare_exit':code,'exact_byte_match':result['comparison']['equal']}
    (OUT/'behavior.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print('PASS static r0 bit mapping for both original and compiled code; exact-byte match='+str(result['comparison']['equal']))
    return 0


if __name__=='__main__':raise SystemExit(main())
