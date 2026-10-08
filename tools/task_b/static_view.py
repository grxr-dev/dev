"""Local-only targeted disassembly and marker xrefs; requires Capstone."""
import argparse, hashlib, struct
from pathlib import Path
import capstone
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--rom",type=Path,required=True)
p.add_argument("--cpu",type=int,choices=[7,9],required=True)
p.add_argument("--start",type=lambda x:int(x,0),required=True)
p.add_argument("--end",type=lambda x:int(x,0),required=True)
a=p.parse_args(); rom=a.rom.read_bytes()
assert hashlib.sha1(rom).hexdigest()=="b8a105bacc3234dede8d4465df0869f2b922a0e2"
u=lambda b,o:struct.unpack_from("<I",b,o)[0]
o=0x20 if a.cpu==9 else 0x30
fileoff,base,size=u(rom,o),u(rom,o+8),u(rom,o+12)
b=rom[fileoff:fileoff+size]
segments=[(base,fileoff,size)]
if a.cpu==7:
 params=u(b,0x114)-base
 src=u(b,params+8)-base
 for t in range(u(b,params)-base,u(b,params+4)-base,12):
  dst,n,z=u(b,t),u(b,t+4),u(b,t+8)
  segments.append((dst,fileoff+src,n));src+=n
print("segments",[(hex(v),hex(f),hex(n)) for v,f,n in segments])
for marker in [b"CLEAR-RAM-CHECK"]:
 pos=0
 while (pos:=rom.find(marker,pos))>=0:
  print("marker ROM",hex(pos))
  for v,f,n in segments:
   if f<=pos<f+n:
    addr=v+pos-f
    print("guest",hex(addr),"pointer words",[hex(base+i) for i in range(0,len(b)-3,4) if u(b,i)==addr])
  pos+=1
for v,f,n in reversed(segments):
 if v<=a.start<a.end<=v+n:
  md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);md.skipdata=True
  for i in md.disasm(rom[f+a.start-v:f+a.end-v],a.start):
   print(f"{i.address:08X} {i.bytes.hex():8} {i.mnemonic:8} {i.op_str}")
  break
else:raise SystemExit("range outside mapped segments")
