"""Read-only exact-ROM bounded map; raw disassembly remains ignored/local."""
import argparse,hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
r=a.rom.read_bytes();assert hashlib.sha1(r).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',r,0x20);code=r[o:o+n];assert base==0x02000000
out=a.out.resolve();assert out.is_relative_to(ROOT/'local/task-z');out.mkdir(parents=True,exist_ok=False)
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);evidence=[]
for lo,hi in [(0x02025698,0x0202583c),(0x02026510,0x02026710),(0x02026be4,0x02026c08)]:
 data=code[lo-base:hi-base]
 (out/f'{lo:08X}.txt').write_text('\n'.join(f'{i.address:08X} {int.from_bytes(i.bytes,"little"):08X} {i.mnemonic} {i.op_str}' for i in m.disasm(data,lo))+'\n')
 evidence.append({'start':hex(lo),'end_exclusive':hex(hi),'sha256':hashlib.sha256(data).hexdigest()})
(out/'ranges.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS: exact ROM; bounded static map; no guest execution')
