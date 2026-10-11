"""Read-only exact-ROM caller-slice identification, frozen before original execution."""
import hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
rom=(ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds').read_bytes()
sha=hashlib.sha1(rom).hexdigest();assert sha=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',rom,0x20)
def word(pc):return struct.unpack_from('<I',rom,o+pc-base)[0]
ad=json.loads((ROOT/'docs/BrainAge_TaskAD_Result.json').read_text());pre=ad['safe_stop'];assert pre['pc']==0x02025830
ram=(ROOT/'local/task-ad/session-001/decision-after-mainram.bin').read_bytes();dtcm=(ROOT/'local/task-ad/session-001/decision-after-dtcm.bin').read_bytes()
assert hashlib.sha256(ram).hexdigest()==ad['hashes']['immediate_mainram_after']
assert hashlib.sha256(dtcm).hexdigest()==ad['hashes']['immediate_dtcm_after']
def stack(a):return struct.unpack_from('<I',dtcm,a-0x027e0000)[0]
assert [stack(a) for a in (0x027e3b14,0x027e3b18,0x027e3b24,0x027e3b28,0x027e3b2c,0x027e3b30)]==[1,0x020266b8,3,0,114,0x02026988]
assert struct.unpack_from('<h',ram,0xe9a10)[0]==1
pcs=[0x02025830,0x020266b8,0x020266fc,0x02026700,0x02026704,0x02026988,0x0202698c,0x02026990,0x02026b8c,0x02026b90]
ops=[0xe8bd8010,0xea00000f,0xe3a00001,0xe28dd008,0xe8bd8070,0xe1d801f0,0xe3500002,0x1a00007d,0xe1a00008,0xebfffda0]
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
states=[];regs=list(pre['r']);flags=[pre[k] for k in ('n','z','c','v')]
for i,(pc,op) in enumerate(zip(pcs,ops)):
 assert regs[15]==pc and word(pc)==op
 dec=next(m.disasm(struct.pack('<I',op),pc));states.append({'pc':pc,'opcode':op,'decoded':dec.mnemonic+' '+dec.op_str,'r':list(regs),'nzcv':list(flags),'dispatch':i<9})
 if i==0:regs[4]=stack(regs[13]);regs[15]=stack(regs[13]+4);regs[13]+=8
 elif i==1:regs[15]=0x020266fc
 elif i==2:regs[0]=1;regs[15]+=4
 elif i==3:regs[13]+=8;regs[15]+=4
 elif i==4:
  for j,reg in enumerate((4,5,6,15)):regs[reg]=stack(regs[13]+4*j)
  regs[13]+=16
 elif i==5:regs[0]=struct.unpack_from('<h',ram,regs[8]+0x10-0x02000000)[0]&0xffffffff;regs[15]+=4
 elif i==6:assert regs[0]==1;flags=[1,0,0,0];regs[15]+=4
 elif i==7:assert flags[1]==0;regs[15]=0x02026b8c
 elif i==8:regs[0]=regs[8];regs[15]+=4
assert word(0x02026218)==0xe92d4010 and word(0x0202624c)==0xe5840034
proof={'rom_sha1':sha,'start':'0x02025830','stop':'0x02026B90','stop_opcode':'0xEBFFFDA0','call_target':'0x02026218','expected_lr_if_call_executed':'0x02026B94','call_executed':False,'safe':True,'new_dispatches':9,'states':states,'stack_reads':[{'address':a,'value':stack(a)} for a in (0x027e3b14,0x027e3b18,0x027e3b24,0x027e3b28,0x027e3b2c,0x027e3b30)],'phase_read':{'address':'0x020E9A10','signed_halfword':1},'boundary_reason':'First new semantic routine after correctness/publication returns and phase-one branch. Callee phase-dispatch can write +0x34; stop before BL, no callee body.'}
out=ROOT/'local/task-ae/preflight.json';out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():assert json.loads(out.read_text())==proof
else:out.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'start':proof['start'],'stop':proof['stop'],'call_target':proof['call_target'],'new_dispatches':9,'safe':True}))
