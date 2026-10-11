"""Read-only static certificate; no guest executor, replay, build or image writes.
--export writes only the Task AM JSON. Instruction facts are analysis, not ROM data.
"""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
AL='7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70'
AK='dd29b71e182611fb73016aa1a13367e70c9cd290'
AJ='a1d2c76baedc0ae841086eeccaf9aa5daebe8d16'
BASE='3a57236bb23d25dcb4caad7d58d733311062ff5e'
def git(*args,cwd=ROOT): return subprocess.check_output(['git',*args],cwd=cwd)
def sha(b): return hashlib.sha256(b).hexdigest()
def hx(n): return f'0x{n:08X}'
def word(b,o): return struct.unpack_from('<I',b,o)[0]
# Explicit symbolic proof facts, not an interpreter or instruction dispatch loop.
PREFIX=[
(0x02067BE0,0xE3510000,'CMP 0,0 -> NZCV=0110'),
(0x02067BE4,0xE3A00000,'r0=0; flags unchanged'),
(0x02067BE8,0x0A000004,'EQ true Z=1 -> 02067C00; skips alternate r1 cases'),
(0x02067C00,0xE3520000,'CMP 0,0 -> NZCV=0110'),
(0x02067C04,0xBA00000D,'LT false N=V=0; target 02067C40 not taken -> 02067C08'),
(0x02067C08,0xE3520008,'CMP 0,8 -> NZCV=1000'),
(0x02067C0C,0xAA00000B,'GE false N=1 V=0; target 02067C40 not taken -> 02067C10'),
(0x02067C10,0xE3A00001,'r0=1'),
(0x02067C14,0xE1A00210,'r0=1 << r2(0) = 1; no flags'),
(0x02067C18,0xE59410C0,'object read [020EA030] (+630)=1 -> r1'),
(0x02067C1C,0xE0110000,'r0=1 & 1=1; NZ=00; zero-shift carry preserved C=0, V=0'),
(0x02067C20,0x0A000006,'EQ false Z=0; target 02067C40 not taken -> 02067C24'),
(0x02067C24,0xE0841102,'r1=020E9F70+(0 << 2)=020E9F70'),
(0x02067C28,0xE5910080,'object read [020E9FF0] (+5F0)=44 hex -> r0'),
(0x02067C2C,0xE1530000,'CMP 1F,44 -> NZCV=1000; signed 31 < 68'),
(0x02067C30,0xB5911060,'LT true; object read [020E9FD0] (+5D0)=02131D24 -> r1'),
(0x02067C34,0xB3A00054,'LT true; r0=54 hex'),
(0x02067C38,0xB0201093,'LT true; r0=1F*54+02131D24=02132750; no flags'),
(0x02067C3C,0xBA000000,'LT true N=1 V=0 -> 02067C44; skips MOV r0,0'),
]

def analyze():
 assert git('branch','--show-current').decode().strip()=='codex/brainage'
 assert git('rev-parse','HEAD',cwd=ROOT/'local/ndsrecomp').decode().strip()==BASE
 paths=[]
 for commit,tag,report in [(AL,'al','FirstValueChangingObjectStore'),(AK,'ak','DynamicInnerHelperBoundary'),(AJ,'aj','InnerHelperStaticMap')]:
  git('merge-base','--is-ancestor',commit,'HEAD')
  names=[f'docs/BrainAge_Task{tag.upper()}_{report}.md',f'docs/BrainAge_Task{tag.upper()}_Result.json']+git('ls-tree','-r','--name-only',commit,f'tools/task_{tag}/').decode().splitlines()
  for name in names:
   p=ROOT/name
   assert git('show',commit+':'+name).decode().splitlines()==p.read_text().splitlines(),name
   paths.append(p)
 al=json.loads((ROOT/'docs/BrainAge_TaskAL_Result.json').read_text())
 ak=json.loads((ROOT/'docs/BrainAge_TaskAK_Result.json').read_text())
 session=ROOT/al['authoritative_path']
 rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
 paths += [rompath]+[p for p in session.iterdir() if p.is_file()]
 before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 rom=rompath.read_bytes(); ram=(session/'decision-after-mainram.bin').read_bytes(); dt=(session/'decision-after-dtcm.bin').read_bytes()
 assert hashlib.sha1(rom).hexdigest()==al['rom_sha1']=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
 assert len(ram)==0x400000 and len(dt)==0x4000
 assert sha(ram)==al['memory']['mainram_after_sha256']
 assert sha(dt)==al['memory']['dtcm_after_sha256']==ak['memory']['dtcm_after_sha256']
 assert sha((session/'decision-after.sav').read_bytes())==al['save']['after_sha256']
 entry=[0x020E9F70,0,0,31,0x020E9F70,0,218,0x020E9A00,0x020E9A00,0,0,0,0,0x027E3B04,0x02026010,0x02067BE0]
 assert al['al_stop']['r']==entry and al['al_stop']['insn9']==281097925
 assert [al['al_stop'][k] for k in ['n','z','c','v','t','mode','i','f']]==[0,0,1,0,0,31,0,0]
 audit=[json.loads(l) for l in (session/'audit.jsonl').read_text().splitlines()]
 assert [x for x in audit if x['event']=='decision_step'][-1]==al['al_stop']
 assert [x for x in audit if x['event']=='decision_stopped']==[dict(event='decision_stopped',al_instructions=1,al_writes=1,successor_dispatched=False)]
 for f in al['memory']['mapped_fields']:
  o=int(f['address'],16)-0x02000000
  assert int.from_bytes(ram[o:o+f['width']],'little')==f['after']
 assert [word(ram,a-0x02000000) for a in [0x020EA030,0x020E9FF0,0x020E9FD0,0x020EA1C0]]==[1,68,0x02131D24,0x02133A18]
 assert 31*84+0x02131D24==0x02132750
 assert [word(dt,o) for o in [0x3b04,0x3b08]]==[0x020E9A00,0x02026010]
 off,_,base,size=struct.unpack_from('<4I',rom,0x20)
 decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
 def fact(pc,expected=None,effect=''):
  assert base<=pc<base+size
  op=word(rom,off+pc-base); assert op==word(ram,pc-0x02000000)
  if expected is not None: assert op==expected
  ins=next(decoder.disasm(struct.pack('<I',op),pc))
  return dict(pc=hx(pc),opcode=hx(op),decoded=ins.mnemonic+' '+ins.op_str,effect=effect)
 facts=[fact(pc,op,effect) for pc,op,effect in PREFIX]
 # Branch-immediate / path completeness checked independently from disassembly.
 for idx,(pc,op,_) in enumerate(PREFIX):
  dest=(PREFIX+[ (0x02067C44,0,'') ])[idx+1][0]
  if pc in [0x02067BE8,0x02067C3C]:
   imm=op&0xffffff; imm=imm-0x1000000 if imm&0x800000 else imm
   assert dest==pc+8+4*imm
  else: assert dest==pc+4
 assert len(facts)==19
 final=entry.copy(); final[0]=0x02132750;final[1]=0x02131D24;final[15]=0x02067C44
 first=dict(**fact(0x02067C44,0xE5840250),address='0x020EA1C0',exercise_offset='0x7C0',subobject_offset='0x250',width=4,source='r0',before='0x02133A18',after='0x02132750',changed_bytes=2,semantics='unknown pointer-valued field',executed=False)
 # Optional bounded static lookahead only; none of this is in AN.
 tailpcs=list(range(0x02067C44,0x02067C5C,4))+list(range(0x020672B0,0x020672DC,4))+[0x02067C58]+list(range(0x02067D10,0x02067D64,4))+[0x02026010]+list(range(0x02026028,0x02026048,4))
 tail=[fact(pc) for pc in tailpcs]
 assert word(rom,off+0x02067D64-base)==word(ram,0x67d64)==0xffff
 # Every direct store on selected tail through return; source values proven in report.
 spec=[(0x02067C44,0x250,4,0x02132750,'r0'),(0x02067C50,0x24c,4,0x020E9F70,'r4'),(0x02067D10,0x278,4,0,'r0'),(0x02067D18,0x258,4,0,'r2'),(0x02067D1C,0x25c,4,0,'r2'),(0x02067D24,0x260,4,0x1000,'r0'),(0x02067D28,0x264,4,0x1000,'r0'),(0x02067D30,0x288,2,0,'r2'),(0x02067D34,0x26c,4,0,'r2'),(0x02067D3C,0x270,4,0,'r2'),(0x02067D40,0x28a,2,0xffff,'r1'),(0x02067D44,0x27c,4,0,'r2'),(0x02067D4C,0x280,4,0xffffffff,'r0'),(0x02067D50,0x268,4,0,'r2'),(0x02067D58,0x274,4,0,'r0'),(0x02067D5C,0x284,4,0,'r2')]
 writes=[]
 for pc,o,w,v,reg in spec:
  a=0x020E9F70+o; old=int.from_bytes(ram[a-0x02000000:a-0x02000000+w],'little')
  writes.append(dict(**fact(pc),address=hx(a),exercise_offset=hex(o+0x570),width=w,source=reg,before=hx(old),after=hx(v),value_changing=old!=v,semantics='unproven; offset only'))
 assert word(ram,0xe9f70+0xa0)==0
 assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 return dict(task='AM',classification='FULL PASS',authoritative_al_commit=AL,authoritative_ak_commit=AK,authoritative_aj_commit=AJ,initial_head=git('rev-parse','HEAD').decode().strip(),rom_sha1=al['rom_sha1'],framework_baseline=BASE,entry=al['al_stop'],prefix=facts,first_next_meaningful_action=first,lookahead_instruction_facts=tail,all_helper_tail_stores=writes,an=dict(start_pc=hx(entry[15]),stop_pc=hx(final[15]),stop_before='STR r0,[r4,#0x250], before fetch/dispatch',instruction_count=19,pc_sequence=[f['pc'] for f in facts],r=[hx(v) for v in final],nzcv=[1,0,0,0],t=0,mode=31,i=0,f=0,predicted_arm9_ordinal=281097944,ram_writes=0,dtcm_writes=0,ram_changed_bytes=0,dtcm_changed_bytes=0,mainram_sha256=sha(ram),dtcm_sha256=sha(dt),mapped_fields=[dict(f,before=f['after']) for f in al['memory']['mapped_fields']],save_sha256=al['save']['after_sha256'],save_changed_bytes=0,logical_save_requests=0,flash_commits=0,mmio_accesses=0,calls=0,returns=0),safety=dict(guest_dispatches=0,guest_mutation=False,an_started=False,input_hashes_unchanged=True),input_sha256=before,evidence_tier='Static exact-ROM analysis anchored in retained forced Tier-3 AL interpreter evidence; no compiled parity',contradictions=[],limitations=['Predictions conditional on exact AL context and future fail-closed gates','Lookahead stores/return/caller are static only and excluded from AN','Unknown fields retain mechanical offset descriptions','No cycle or scheduler prediction'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');args=p.parse_args();r=analyze()
 if args.export:(ROOT/'docs/BrainAge_TaskAM_Result.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(dict(classification=r['classification'],prefix_count=19,stop=r['an']['stop_pc'],guest_dispatches=0)))
