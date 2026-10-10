"""Identity-gated bounded static evidence; raw disassembly stays ignored/local."""
import argparse,hashlib,json,struct
from pathlib import Path
import capstone
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
r=a.rom.read_bytes();assert hashlib.sha1(r).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',r,0x20);b=r[o:o+n];assert base==0x02000000
out=a.out.resolve();assert out.is_relative_to(R/'local/task-x');out.mkdir(parents=True,exist_ok=False)
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);m.skipdata=True
ranges=[(0x25698,0x25834),(0x26510,0x26710),(0x26c08,0x26ca0),(0x51a30,0x51c58),(0x5204c,0x520f8),(0x5213c,0x521a0),(0x52260,0x52424),(0x52424,0x52a78),(0x52f14,0x52fc4),(0xa3acc,0xa3e9c),(0xa3f2c,0xa4034),(0xa41a0,0xa437c),(0xa4718,0xa4780),(0xa49b8,0xa4c00),(0xa5b70,0xa5ce4),(0xa5fe8,0xa606c),(0xb387c,0xb3938)]
evidence=[]
for lo,hi in ranges:
 data=b[lo:hi];name=f'{base+lo:08X}.txt'
 (out/name).write_text('\n'.join(f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in m.disasm(data,base+lo))+'\n')
 evidence.append({'start':hex(base+lo),'end_exclusive':hex(base+hi),'sha256':hashlib.sha256(data).hexdigest()})
(out/'ranges.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS: exact ROM; bounded static ranges saved locally; no code bytes exported')
