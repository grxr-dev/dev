"""Audit private-bus lifecycle, fixed glyph and bounded original continuation."""
import argparse,json,hashlib,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--export',type=Path);a=p.parse_args();root=a.out
h=lambda b:hashlib.sha256(b).hexdigest();word=lambda b,o:struct.unpack_from('<I',b,o)[0]
e=[json.loads(s) for s in (root/'calls.jsonl').read_text().splitlines()]
assert [(x['operation'],x['stroke']) for x in e]==[(0,0),(1,0),(2,0),(1,1),(2,1),(3,0)]
assert all(x['return']==0 and x['instructions']<10000000 for x in e)
assert [e[i]['candidate'] for i in [1,3]]==[50,52]
assert [e[i]['metric'] for i in [2,4]]==[500,249]
assert all([e[i]['count0'],e[i]['count1']]==[0,1] for i in [1,3])
ctx=0x02200000
init=(root/f'0-0-after-{ctx}.bin').read_bytes();assert len(init)==0xa350
assert [word(init,x) for x in [0x94bc,0x94c0,0x94d0,0x94dc]]==[16,1,0x02220000,ctx+0x94e0]
end=(root/f'3-0-after-{ctx}.bin').read_bytes();assert end[:0x94e0]==bytes(0x94e0)
points=[(110,65),(91,99),(65,134),(98,134),(130,134),(114,82),(114,123),(114,180)]
for i in range(2):
 tag=f'1-{i}-before';assert (root/f'{tag}-{0x0220b000}.bin').read_bytes()[:32]==b''.join(struct.pack('<HH',*x) for x in points)
 assert (root/f'{tag}-{0x0220f000}.bin').read_bytes()[:16]==struct.pack('<4I',5,0x0220b000,3,0x0220b014)
assert (root/f'1-0-after-{ctx}.bin').read_bytes()==(root/f'2-0-before-{ctx}.bin').read_bytes()
assert (root/f'2-0-after-{ctx}.bin').read_bytes()==(root/f'1-1-before-{ctx}.bin').read_bytes()
before=(root/'before-mainram.bin').read_bytes();after=(root/'after-mainram.bin').read_bytes();assert len(before)==0x400000 and before==after
success=json.loads((root/'success.json').read_text());assert success['policy']=='A' and success['live_cpu_equal'] and success['owned_session_destroyed']
continuation=json.loads((root/'continuation.json').read_text());assert continuation==dict(pc=0x020610b4,current=0x41,requested=0x41,selected=0x11)
entries=[json.loads(s) for s in (root/'entries.jsonl').read_text().splitlines()];assert len(entries)==1 and entries[0]['kind']=='lifecycle' and entries[0]['backend']=='compiled' and not entries[0]['forced_tier3']
result=json.loads((root/'result.json').read_text());assert result['finished'] and result['canonical_source_unchanged']
save=(root/'initial.sav').read_bytes();assert save==(root/'after.sav').read_bytes()==(root/'disposable.sav').read_bytes();assert h(save)==result['save_sha256_before']==result['save_sha256_after']
assert (root/'flash.jsonl').read_bytes()==(root/'requests.jsonl').read_bytes()==b''
regions={ctx:0xa350,0x0220b000:0x4000,0x0220f000:0x100,0x0220f100:0x100,0x0220f200:16,0x0220f300:8,0x02210000:0x8000}
mutations=[]
for call in e:
 tag=f"{call['operation']}-{call['stroke']}"
 changes=[]
 for addr,n in regions.items():
  b=(root/f'{tag}-before-{addr}.bin').read_bytes();c=(root/f'{tag}-after-{addr}.bin').read_bytes();assert len(b)==len(c)==n
  changes.append(dict(address=hex(addr),size=n,before_sha256=h(b),after_sha256=h(c),changed_bytes=sum(x!=y for x,y in zip(b,c))))
 mutations.append(dict(operation=call['operation'],stroke=call['stroke'],regions=changes))
audit=dict(classification='FULL PASS for isolated private-bus session; no live title heap session claimed',calls=e,execution=success,continuation=continuation,private_guest_address_regions={hex(k):v for k,v in regions.items()},live_mainram_sha256=h(before),database_sha256=h((root/'database.bin').read_bytes()),save_sha256=h(save),logical_save_requests=0,flash_commits=0,changed_save_bytes=0,context_prefix_zeroed_by_original_teardown=True,region_mutations=mutations)
(root/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
if a.export:a.export.write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ['classification','calls','execution','continuation','save_sha256']},indent=2))
