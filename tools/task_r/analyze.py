"""Audit one original answer's touch, stroke descriptors, worker results and acceptance."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.out
trace=[json.loads(x) for x in (root/'recognition.jsonl').read_text().splitlines()];result=json.loads((root/'result.json').read_text())
assert len(trace)<12000 and [e['seq'] for e in trace]==list(range(1,len(trace)+1))
def rows(pc):return [e for e in trace if e['pc']==pc]
def one(pc):
 es=rows(pc);assert len(es)==1,(hex(pc),len(es));return es[0]
def mem(e,addr,n):
 for m in e['mem']:
  b=bytes.fromhex(m['hex']);off=addr-m['addr']
  if 0<=off<=len(b)-n:return b[off:off+n]
 raise AssertionError((e['seq'],hex(addr),n))
def word(e,addr):return struct.unpack('<I',mem(e,addr,4))[0]
def half(e,addr):return struct.unpack('<H',mem(e,addr,2))[0]
def event(e,kind,**kw):return dict(kind=kind,seq=e['seq'],cycle9=e['cycle9'],pc=f"0x{e['pc']:08X}",**kw)
first=rows(0x02052424)[0];manager=first['manager'];slot=word(first,manager+4);exercise=first['exercise']
assert word(first,manager)==1
assert [word(first,slot+x) for x in [0xc,0x10,0x14,0x18]]==[54,6,247,183]
assert word(first,slot+0x214)==word(first,slot+0x218)==0
points_addr=word(first,slot+0x208);descriptors=word(first,slot+0x20c);context=word(first,slot+0x1c)
points=[];timeline=[dict(kind='exercise_ready',cycle9=result['initial']['counts']['cyc9'],exercise=hex(exercise),expected=4,previous_correct_answers=1)]
timeline += result['touch_events']
writes=rows(0x02052534);afterwrites=rows(0x02052558);assert len(writes)==len(afterwrites)==14
for i,(before,after) in enumerate(zip(writes,afterwrites)):
 assert before['r'][7]==i and before['r'][5]==points_addr and before['r'][3]==i*4
 x,y,down,validity=struct.unpack('<4H',mem(before,0x020da4e4,8));assert down==1
 source=[e for e in result['touch_events'] if e['cycle9']<=before['cycle9']][-1]
 assert source['kind'] in ['down','motion'] and source['xy']==[x,y]
 point=[y,255-x];assert before['r'][1:3]==point
 assert list(struct.unpack('<hh',mem(after,points_addr+i*4,4)))==point
 assert word(before,slot+0x214)==i and word(after,slot+0x214)==i+1
 points.append(point);timeline.append(event(before,'point_stored',index=i,source_xy=[x,y],stored_xy=point,buffer=hex(points_addr)))
finals=rows(0x020525e4);calls=rows(0x02051af4);returns=rows(0x02051af8);published=rows(0x02052038);consumed=rows(0x02052938)
assert list(map(len,[finals,calls,returns,published,consumed]))==[2]*5
strokes=[];invocations=[]
for i,(fin,call,ret,pub,consume) in enumerate(zip(finals,calls,returns,published,consumed)):
 total=[9,14][i];count=[9,5][i];start=[0,9][i];candidate=[2,4][i]
 assert half(fin,0x020da4e8)==0 and mem(fin,manager+0x234,1)==b'\x01'
 assert word(fin,slot+0x214)==total and word(fin,slot+0x218)==i
 assert word(fin,descriptors+8*i)==count and word(fin,descriptors+8*i+4)==points_addr+4*start
 assert call['r'][:4]==[context,descriptors+8*i,i,slot+0xe4]
 args=struct.unpack('<5I',mem(call,call['r'][13],20));assert args[0]==args[3]==16 and args[2]==slot+0x104
 assert ret['r'][0]==0 and ret['r'][14]==0x02051af8
 assert half(ret,slot+0xe4)==0 and half(ret,slot+0x104)==ord(str(candidate)) and half(ret,slot+0x106)==0
 assert [word(ret,args[1]),word(ret,args[4])]==[0,1]
 assert word(consume,slot+0x320)==candidate
 assert fin['seq']<call['seq']<ret['seq']<pub['seq']<consume['seq']
 stroke=points[start:total];assert list(struct.iter_unpack('<hh',mem(call,points_addr+start*4,count*4)))==list(map(tuple,stroke))
 strokes.append(stroke)
 invocations.append(dict(index=i,callsite=hex(call['pc']),target='0x020A41A0',return_site='0x02051AF8',context=hex(context),descriptor=hex(call['r'][1]),stroke_identifier=i,point_count=count,register_args=[hex(v) for v in call['r'][:4]],stack_args=[hex(v) for v in args],return_value=ret['r'][0],group_counts=[0,1],candidate_code=ord(str(candidate)),candidate=candidate,metric=word(pub,slot+0x144),membership_count=word(pub,slot+0x184)))
 timeline += [event(fin,'stroke_finalized',stroke=i,point_count=count,total_points=total,descriptor=hex(descriptors+8*i)),event(call,'recognition_call',stroke=i,target='0x020A41A0',descriptor=hex(call['r'][1])),event(ret,'recognition_return',stroke=i,return_value=0,candidate_code=ord(str(candidate)),group_counts=[0,1]),event(pub,'worker_result_published',stroke=i),event(consume,'candidate_to_number',value=candidate)]
submit=one(0x020266b4);check=one(0x02025728);correct=one(0x02025740);accepted=one(0x020265f8)
assert submit['r'][:3]==[exercise,0,4]
assert check['r'][1]==check['r'][5]==4 and check['r'][3]==0
assert word(correct,exercise+0x514)==4 and word(correct,exercise+0x4c)==4 and word(correct,exercise+0x504)==1
assert accepted['r'][0]==2 and word(accepted,exercise+0x44)==2
assert consumed[1]['seq']<submit['seq']<check['seq']<correct['seq']<accepted['seq']
finalbytes=bytes.fromhex(result['exercise_after']['hex']);assert struct.unpack_from('<H',finalbytes,0x10)[0]==2 and struct.unpack_from('<I',finalbytes,0x44)[0]==2
assert result['accepted_path_observed'] and result['canonical_source_unchanged']
save=(root/'initial.sav').read_bytes();assert (root/'after.sav').read_bytes()==(root/'disposable.sav').read_bytes()==save
assert (root/'requests.jsonl').read_bytes()==(root/'flash.jsonl').read_bytes()==b''
assert len(save)==262144 and hashlib.sha256(save).hexdigest()==result['save_sha256_before']==result['save_sha256_after']
for e,kind in [(submit,'candidate_submitted'),(check,'correctness_compare'),(correct,'correct_flag_set'),(accepted,'answer_accepted')]:timeline.append(event(e,kind,value=4,exercise=hex(exercise)))
timeline.sort(key=lambda e:(e['cycle9'],e.get('seq',0)))
audit=dict(validated=True,snapshots=len(trace),manager=hex(manager),slot=hex(slot),exercise=hex(exercise),points_buffer=hex(points_addr),descriptor_array=hex(descriptors),recognizer_context=hex(context),stroke_point_counts=[9,5],total_points=14,strokes=strokes,invocations=invocations,logical_save_requests=0,flash_commits=0,changed_bytes=0,save_sha256=result['save_sha256_after'],trace_sha256=hashlib.sha256((root/'recognition.jsonl').read_bytes()).hexdigest())
(root/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');(root/'timeline.json').write_text(json.dumps(timeline,indent=2)+'\n')
# Exact small input dumps remain local, not versioned.
last=calls[-1];(root/'finalized-points.hex').write_text(mem(last,points_addr,56).hex()+'\n');(root/'finalized-descriptors.hex').write_text(mem(last,descriptors,16).hex()+'\n')
print(json.dumps(audit,indent=2))
