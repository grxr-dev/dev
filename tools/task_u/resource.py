"""Read the one identity-gated ROM resource without altering it."""
import hashlib,struct
def extract_database(rom):
 assert hashlib.sha1(rom).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
 fo,fn,fa,fs=struct.unpack_from('<4I',rom,0x40);f=rom[fo:fo+fn];found=[]
 def walk(d,p):
  off,file_id,_=struct.unpack_from('<IHH',f,(d&4095)*8)
  while f[off]:
   n=f[off];off+=1;name=f[off:off+(n&127)].decode();off+=n&127
   if n&128:
    sub=struct.unpack_from('<H',f,off)[0];off+=2;walk(sub,p+'/'+name)
   else:
    if p+'/'+name=='/data/Decuma/_databas_le.bin':
     lo,hi=struct.unpack_from('<II',rom,fa+file_id*8);assert file_id==55 and lo==0x796e00 and hi-lo==113956;found.append(rom[lo:hi])
    file_id+=1
 walk(0xf000,'');assert len(found)==1;return found[0]
