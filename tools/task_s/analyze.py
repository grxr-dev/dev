"""Validate isolated adapter bytes, ABI, memory manifest and recognition results."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.out
h=lambda b:hashlib.sha256(b).hexdigest()
events=[json.loads(x) for x in (root/'calls.jsonl').read_text().splitlines()];result=json.loads((root/'result.json').read_text());v=result['variant'];obj=events[0]
assert obj['kind']=='resolved' and events[-1]['kind']=='stopped' and result['finished']
base=[[(190,110),(156,91),(121,65),(121,98),(121,130)],[(173,114),(132,114),(75,114)]]
repeat=[[2,2,1,2,2],[1,2,2]]
source=[[p for p,n in zip(s,rs) for _ in range(n)] for s,rs in zip(base,repeat)] if v=='A' else base
stored=[[(y,255-x) for x,y in s] for s in source];flat=b''.join(struct.pack('<HH',*p) for s in stored for p in s)
desc=b''.join(struct.pack('<II',len(s),obj['points']+4*sum(map(len,stored[:i]))) for i,s in enumerate(stored))
assert (root/'write-1-adapter.bin').read_bytes()==flat and (root/'write-2-adapter.bin').read_bytes()==desc
if v=='A':
 reference=Path(__file__).resolve().parents[2]/'local/task-r/answer-002'
 assert flat==bytes.fromhex((reference/'finalized-points.hex').read_text())
 assert desc==bytes.fromhex((reference/'finalized-descriptors.hex').read_text())
entries=[e for e in events if e['kind']=='entry'];returns=[e for e in events if e['kind']=='return'];assert len(entries)==len(returns)==4
calls=[]
for entry,ret in zip(entries,returns):
 i=entry['stroke'];phase=entry['phase'];tag=f'call-{i}-{phase}'
 assert entry['r'][15]==[0x020a41a0,0x020a3fb8][phase] and entry['r'][14]==ret['r'][15]==0x02051af8
 assert ret['r'][0]==0 and ret['r'][13]==entry['r'][13] and ret['r'][4:12]==entry['r'][4:12]
 assert entry['r'][:4]==([obj['context'],obj['descriptors']+8*i,i,obj['slot']+0xe4] if phase==0 else [obj['context'],1,0,obj['slot']+0x144])
 assert entry['stack']==[16,obj['counts'],obj['slot']+0x104,16,obj['counts']+4]
 assert (root/(tag+'-before-points.bin')).read_bytes()[:len(flat)]==flat
 assert (root/(tag+'-before-descriptors.bin')).read_bytes()[:16]==desc
 after=(root/(tag+'-after-slot.bin')).read_bytes();assert struct.unpack_from('<H',after,0x104)[0]==ret['candidate']
 assert struct.unpack_from('<2I',(root/(tag+'-after-counts.bin')).read_bytes())==tuple(ret['counts'])
 assert (root/(tag+'-after-stack.bin')).read_bytes()[:256]==bytes([0xa5])*256
 if phase==0: calls.append(dict(stroke=i,point_count=len(source[i]),return_value=ret['r'][0],candidate_code=ret['candidate'],candidate=chr(ret['candidate']),group_counts=ret['counts'],registers=entry['r'][:4],stack=entry['stack'],target=entry['r'][15],return_gate=ret['r'][15]))
 else: calls[-1]['metric']=ret['metric']
 if v=='A':assert ret['candidate']==[50,52][i] and ret['counts']==[0,1] and (phase==0 or ret['metric']==[500,249][i])
manifest=[]
for e in events:
 if e['kind']=='write':
  before=(root/f"write-{e['id']}-before.bin").read_bytes();after=(root/f"write-{e['id']}-adapter.bin").read_bytes();assert len(before)==len(after)==e['length']
  manifest.append(dict(e,before_sha256=h(before),adapter_sha256=h(after),lifetime='discarded with disposable process'))
assert (root/'exercise-before.bin').read_bytes()==(root/'exercise-after.bin').read_bytes()
assert (root/'manager-before.bin').read_bytes()==(root/'manager-after.bin').read_bytes()
initial=(root/'initial-mainram.bin').read_bytes();final=(root/'call-1-1-after-mainram.bin').read_bytes()
# Startup module parameters set BSS to [020D2BA0,020E6FC0); ROM tail is relocated.
assert initial[:0xd2ba0]==final[:0xd2ba0], 'loaded title code changed'
regions=[('title_bss',0x020d2ba0,0x14420),('context',obj['context'],0xa350),('slot',obj['slot'],0x370),('points',obj['points'],0x4000),('descriptors',obj['descriptors'],0x100),('stack',obj['arena'],0x4000),('counts',obj['counts'],0x100)]
diffs={name:0 for name,_,_ in regions};other=[]
for i,(a,b) in enumerate(zip(initial,final)):
 if a==b:continue
 address=i+0x02000000
 for name,start,n in regions:
  if start<=address<start+n:diffs[name]+=1;break
 else:other.append(address)
def ranges(xs):
 out=[]
 for x in xs:
  if out and out[-1][0]+out[-1][1]==x:out[-1][1]+=1
  else:out.append([x,1])
 return out
save=(root/'initial.sav').read_bytes();assert len(save)==262144
assert save==(root/'after.sav').read_bytes()==(root/'disposable.sav').read_bytes()
assert (root/'flash.jsonl').read_bytes()==(root/'requests.jsonl').read_bytes()==b''
assert result['canonical_source_unchanged'] and h(save)==result['save_sha256_before']==result['save_sha256_after']
audit=dict(validated=True,variant=v,objects=obj,source=source,stored=stored,calls=calls,write_manifest=manifest,net_changed_bytes_by_region=diffs,other_mainram_changes=ranges(other),exercise_unchanged=True,manager_unchanged=True,loaded_code_unchanged=True,min_sp=min(e['min_sp'] for e in entries+returns),save_sha256=h(save),logical_save_requests=0,flash_commits=0,changed_save_bytes=0,trace_sha256=h((root/'calls.jsonl').read_bytes()))
(root/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ['validated','variant','calls','net_changed_bytes_by_region','other_mainram_changes','min_sp','save_sha256']},indent=2))
