"""Emit only immediate constructor/setup/activation evidence for the Task T blocker."""
import argparse,hashlib,struct
from pathlib import Path
import capstone
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
r=a.rom.read_bytes();assert hashlib.sha1(r).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',r,0x20);b=r[o:o+n];a.out.mkdir(parents=True,exist_ok=False)
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);m.skipdata=True
for lo,hi in [(0x27a28,0x27ad8),(0x531c8,0x53368),(0x5228c,0x52424)]:
 (a.out/f'{base+lo:08X}.txt').write_text('\n'.join(f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in m.disasm(b[lo:hi],base+lo))+'\n')
