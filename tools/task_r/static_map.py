"""Emit only Task R boundary disassembly to an ignored local directory."""
import argparse,hashlib,struct
from pathlib import Path
import capstone
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rom=a.rom.read_bytes();assert hashlib.sha1(rom).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,entry,base,n=struct.unpack_from('<4I',rom,0x20);b=rom[o:o+n]
assert base==0x02000000
a.out.mkdir(parents=True,exist_ok=False)
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);md.skipdata=True
ranges=[(0x25698,0x25834),(0x26510,0x26710),(0x26be4,0x26ca0),(0x51a30,0x51c58),(0x52030,0x520f8),(0x5213c,0x521cc),(0x52260,0x52424),(0x52424,0x52850),(0x52904,0x52a78),(0x52f14,0x52fb8),(0x531c8,0x53368),(0xa3970,0xa39ec),(0xa3f2c,0xa4034),(0xa41a0,0xa437c),(0xa447c,0xa455c),(0xa4718,0xa4780),(0xb387c,0xb3938)]
for lo,hi in ranges:
 (a.out/f'{base+lo:08X}.txt').write_text('\n'.join(f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in md.disasm(b[lo:hi],base+lo))+'\n')
needle=b'/data/Decuma/_databas_le.bin';at=b.index(needle);addr=base+at
refs=[hex(base+i) for i in range(0,len(b)-3,4) if struct.unpack_from('<I',b,i)[0]==addr]
(a.out/'identity.txt').write_text(f'ARM9 Decuma resource path: ROM {o+at:#x}, guest {addr:#x}, pointer xrefs {refs}\n')
