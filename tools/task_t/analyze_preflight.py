"""Read-only search for the mapped manager/slot/context shape; no guest writes."""
import argparse,json,struct,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.out
base=0x02000000
b=(root/'boundary-mainram.bin').read_bytes();assert len(b)==0x400000
ref=Path(__file__).resolve().parents[2]/'local/task-s/trial-a-001/initial-mainram.bin'
def scan(data):
 def ram(p,n=4):return base<=p<=base+len(data)-n
 def w(p):return struct.unpack_from('<I',data,p-base)[0]
 contexts=[];slots=[];managers=[]
 # Task S context has a self-relative first pointer and a second self pointer.
 for off in range(0,len(data)-0xa350,4):
  ptr=base+off
  if w(ptr)==ptr+0x84 and w(ptr+0x2c)==ptr:contexts.append(ptr)
 for off in range(0,len(data)-0x370,4):
  ptr=base+off
  if w(ptr+0x1c) not in contexts:continue
  if all(ram(w(ptr+d),n) for d,n in [(0x208,0x4000),(0x20c,0x100),(0x1fc,0x4000),(0x200,0x100)]):slots.append(ptr)
 for off in range(0,len(data)-0x238,4):
  ptr=base+off
  if 1<=w(ptr)<=8 and w(ptr+4) in slots and ram(w(ptr+8)):managers.append(ptr)
 return dict(contexts=[hex(x) for x in contexts],slots=[hex(x) for x in slots],managers=[hex(x) for x in managers])
reference=scan(ref.read_bytes());assert '0x211b994' in reference['contexts'] and '0x20faa50' in reference['slots'] and '0x20fa808' in reference['managers']
found=scan(b);regs=json.loads((root/'boundary-regs.json').read_text());w=lambda p:struct.unpack_from('<I',b,p-base)[0]
assert regs['r'][15] in [0x0204d790,0x0204d794] and regs['r'][0]==0x41 and regs['r'][14]==0x02050268
assert [w(x) for x in [0x20da464,0x20da3ec,0x20da3f0,0x20da420]]==[0x32,0x41,0x11,1]
result=json.loads((root/'result.json').read_text());assert result['finished'] and result['canonical_source_unchanged']
assert (root/'initial.sav').read_bytes()==(root/'after.sav').read_bytes()==(root/'disposable.sav').read_bytes()
assert (root/'requests.jsonl').read_bytes()==(root/'flash.jsonl').read_bytes()==b''
audit=dict(boundary_pc=hex(regs['r'][15]),scenes=[0x32,0x41,0x11],mapped_shape_matches=found,positive_control=reference,scan_limit='Known initialized shape in all canonical 4 MiB main RAM; does not prove absence of every conceivable alternative context format',mainram_sha256=hashlib.sha256(b).hexdigest(),save_sha256=result['save_sha256_after'],logical_save_requests=0,flash_commits=0,changed_save_bytes=0)
(root/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
