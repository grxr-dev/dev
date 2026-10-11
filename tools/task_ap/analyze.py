"""AP static proof certificate. No emulator, interpreter, replay, or guest-image writes.
The explicit annotations are proof obligations, not an ARM execution engine.
Default is read-only; --export writes only AP's ROM-free JSON and Markdown.
"""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path
import capstone
ROOT = Path(__file__).resolve().parents[2]
AO='3e2ecf215823ad1e5b95a4af830d4ee6026152e0'
AN='0f3d697861a8d52f569ec051915258e02915d878'
AM='cb2126cfa0c2e75714b993cdc0124c49c8e1b680'
BASE='3a57236bb23d25dcb4caad7d58d733311062ff5e'
def git(*a,cwd=ROOT):return subprocess.check_output(['git',*a],cwd=cwd)
def sha(b):return hashlib.sha256(b).hexdigest()
def hx(n):return f'0x{n:08X}'
def word(b,o):return struct.unpack_from('<I',b,o)[0]
# PC, opcode, mechanical effect. AL unless explicitly conditional below.
FACTS=[
(0x02067C48,0xE1A00004,'r0=r4=020E9F70'),
(0x02067C4C,0xE1A01002,'r1=r2=0'),
(0x02067C50,0xE584424C,'store r4=020E9F70 at exercise+7BC'),
(0x02067C54,0xEBFFFD95,'call 020672B0; LR=02067C58; SP unchanged'),
(0x020672B0,0xE3510000,'CMP 0,0: NZCV=0110'),
(0x020672B4,0xBA000008,'LT false (N=V=0); fall through; target 020672DC excluded'),
(0x020672B8,0xE3510008,'CMP 0,8: NZCV=1000'),
(0x020672BC,0xAA000006,'GE false (N=1,V=0); fall through; target 020672DC excluded'),
(0x020672C0,0xE3A02001,'r2=1'),
(0x020672C4,0xE1A02112,'r2=1 << r1(0)=1; flags unchanged'),
(0x020672C8,0xE59030C0,'r3=[020EA030]=1 (exercise+630)'),
(0x020672CC,0xE0132002,'r2=1 & 1=1; NZCV=0000; unshifted carry preserved'),
(0x020672D0,0x10800101,'NE true (Z=0); r0=020E9F70+(0<<2)=020E9F70'),
(0x020672D4,0x159000A0,'NE true; r0=[020EA010]=0 (exercise+610)'),
(0x020672D8,0x112FFF1E,'NE true; BX LR -> 02067C58, T=0; SP unchanged'),
(0x02067C58,0xEA00002C,'branch AL -> 02067D10; skip alternate cases'),
(0x02067D10,0xE5840278,'store r0=0 at exercise+7E8'),
(0x02067D14,0xE3A02000,'r2=0'),
(0x02067D18,0xE5842258,'store r2=0 at exercise+7C8'),
(0x02067D1C,0xE584225C,'store r2=0 at exercise+7CC'),
(0x02067D20,0xE3A00A01,'r0=1000'),
(0x02067D24,0xE5840260,'store r0=1000 at exercise+7D0'),
(0x02067D28,0xE5840264,'store r0=1000 at exercise+7D4'),
(0x02067D2C,0xE2840C02,'r0=r4+200=020EA170'),
(0x02067D30,0xE1C028B8,'store low halfword r2=0 at exercise+7F8'),
(0x02067D34,0xE584226C,'store r2=0 at exercise+7DC'),
(0x02067D38,0xE59F1024,'r1=[PC+8+24]=[02067D64]=FFFF'),
(0x02067D3C,0xE5842270,'store r2=0 at exercise+7E0'),
(0x02067D40,0xE1C018BA,'store low halfword r1=FFFF at exercise+7FA'),
(0x02067D44,0xE584227C,'store r2=0 at exercise+7EC'),
(0x02067D48,0xE3E00000,'r0=FFFFFFFF'),
(0x02067D4C,0xE5840280,'store r0=FFFFFFFF at exercise+7F0'),
(0x02067D50,0xE5842268,'store r2=0 at exercise+7D8'),
(0x02067D54,0xE5940278,'r0=[020EA1E8]=0, same word stored at D10'),
(0x02067D58,0xE5840274,'store r0=0 at exercise+7E4'),
(0x02067D5C,0xE5842284,'store r2=0 at exercise+7F4'),
(0x02067D60,0xE8BD8010,'POP: r4=[027E3B04]=020E9A00; PC=[027E3B08]=02026010; SP=027E3B0C; LR stays 02067C58'),
(0x02026010,0xEA000004,'branch AL -> 02026028; skip alternate nested call'),
(0x02026028,0xE3A00001,'r0=1'),
(0x0202602C,0xE58707F4,'store r0=1 at exercise+7F4'),
(0x02026030,0xE3A00702,'r0=80000'),
(0x02026034,0xE58707C8,'store r0=80000 at exercise+7C8; immediate before is zero'),
(0x02026038,0xE3A01806,'r1=60000'),
(0x0202603C,0xE2870E57,'r0=r7+570=020E9F70'),
(0x02026040,0xE58717CC,'store r1=60000 at exercise+7CC; immediate before is zero'),
]
# Explicit sources and offsets independently checked against instruction encoding.
STORES=[(0x2067c50,0x7bc,4,4,0x20e9f70),(0x2067d10,0x7e8,4,0,0),(0x2067d18,0x7c8,4,2,0),(0x2067d1c,0x7cc,4,2,0),(0x2067d24,0x7d0,4,0,0x1000),(0x2067d28,0x7d4,4,0,0x1000),(0x2067d30,0x7f8,2,2,0),(0x2067d34,0x7dc,4,2,0),(0x2067d3c,0x7e0,4,2,0),(0x2067d40,0x7fa,2,1,0xffff),(0x2067d44,0x7ec,4,2,0),(0x2067d4c,0x7f0,4,0,0xffffffff),(0x2067d50,0x7d8,4,2,0),(0x2067d58,0x7e4,4,0,0),(0x2067d5c,0x7f4,4,2,0),(0x202602c,0x7f4,4,0,1),(0x2026034,0x7c8,4,0,0x80000),(0x2026040,0x7cc,4,1,0x60000)]
# Explicit proof annotations: register changes and flags after each relevant instruction.
CHANGES={0x2067c48:{0:0x20e9f70},0x2067c4c:{1:0},0x2067c54:{14:0x2067c58},0x20672c0:{2:1},0x20672c8:{3:1},0x20672d4:{0:0},0x2067d14:{2:0},0x2067d20:{0:0x1000},0x2067d2c:{0:0x20ea170},0x2067d38:{1:0xffff},0x2067d48:{0:0xffffffff},0x2067d54:{0:0},0x2067d60:{4:0x20e9a00,13:0x27e3b0c},0x2026028:{0:1},0x2026030:{0:0x80000},0x2026038:{1:0x60000},0x202603c:{0:0x20e9f70}}
FLAG_CHANGES={0x20672b0:[0,1,1,0],0x20672b8:[1,0,0,0],0x20672cc:[0,0,0,0]}
READS={0x20672c8:[(0x20ea030,4,1,'main RAM object +630')],0x20672d4:[(0x20ea010,4,0,'main RAM object +610; newly mapped offset')],0x2067d38:[(0x2067d64,4,0xffff,'ROM literal in main RAM')],0x2067d54:[(0x20ea1e8,4,0,'main RAM object +7E8; D10 dependency')],0x2067d60:[(0x27e3b04,4,0x20e9a00,'DTCM stack'),(0x27e3b08,4,0x2026010,'DTCM stack')]}

def entry_regs(an):return an['an_stop']['r']

def analyze():
 assert git('branch','--show-current').decode().strip()=='codex/brainage'
 assert git('rev-parse','HEAD',cwd=ROOT/'local/ndsrecomp').decode().strip()==BASE
 paths=[]
 for commit,tag,title in [(AO,'AO','SecondValueChangingObjectStore'),(AN,'AN','DynamicPostMutationPrefix'),(AM,'AM','PostMutationStaticMap')]:
  git('merge-base','--is-ancestor',commit,'HEAD')
  names=[f'docs/BrainAge_Task{tag}_{title}.md',f'docs/BrainAge_Task{tag}_Result.json']+git('ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/').decode().splitlines()
  for name in names:
   p=ROOT/name;assert git('show',commit+':'+name).decode().splitlines()==p.read_text().splitlines(),name;paths.append(p)
 ao=json.loads((ROOT/'docs/BrainAge_TaskAO_Result.json').read_text());an=json.loads((ROOT/'docs/BrainAge_TaskAN_Result.json').read_text())
 session=ROOT/ao['authoritative_path'];rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
 paths += [rompath]+[p for p in session.iterdir() if p.is_file()]
 before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 rom=rompath.read_bytes();ram=(session/'decision-after-mainram.bin').read_bytes();dt=(session/'decision-after-dtcm.bin').read_bytes();save=(session/'decision-after.sav').read_bytes()
 assert hashlib.sha1(rom).hexdigest()==ao['rom_sha1']=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
 assert len(ram)==0x400000 and len(dt)==0x4000
 assert sha(ram)==ao['memory']['mainram_after_sha256'] and sha(dt)==ao['memory']['dtcm_after_sha256'] and sha(save)==ao['save']['after_sha256']
 audit=[json.loads(l) for l in (session/'audit.jsonl').read_text().splitlines()]
 steps=[x for x in audit if x['event']=='decision_step'];assert len(steps)==112 and steps[-1]==ao['ao_stop'] and steps[-2]==an['an_stop']
 assert [x for x in audit if x['event']=='decision_stopped']==[dict(event='decision_stopped',ao_instructions=1,ao_writes=1,successor_dispatched=False)]
 assert [x for x in audit if x['event']=='ao_write_event']==[ao['store_event']]
 assert ao['terminal_dispatched'] is False and ao['executed_pcs']==['0x02067C44']
 assert all(ao['ao_start'][k]==ao['ao_stop'][k]==an['an_stop'][k] for k in ['n','z','c','v','t','mode','i','f'])
 assert ao['ao_start']['r'][:15]==entry_regs(an)[:15]==ao['ao_stop']['r'][:15]
 before_ram=(session/'ao-before-mainram.bin').read_bytes()
 assert sha(before_ram)==an['memory']['mainram_after_sha256']
 assert [(i,x,y) for i,(x,y) in enumerate(zip(before_ram,ram)) if x!=y]==[(0xea1c0,0x18,0x50),(0xea1c1,0x3a,0x27)]
 assert (session/'ao-before-dtcm.bin').read_bytes()==dt and (session/'ao-before.sav').read_bytes()==save
 entry=[0x2132750,0x2131d24,0,31,0x20e9f70,0,218,0x20e9a00,0x20e9a00,0,0,0,0,0x27e3b04,0x2026010,0x2067c48]
 assert ao['ao_stop']['r']==entry and ao['ao_stop']['insn9']==281097945
 assert [ao['ao_stop'][k] for k in ['n','z','c','v','t','mode','i','f']]==[1,0,0,0,0,31,0,0]
 for f in ao['memory']['mapped_fields']:
  a=int(f['address'],16)-0x2000000;assert int.from_bytes(ram[a:a+f['width']],'little')==f['after']
 assert (session/'requests.jsonl').stat().st_size==(session/'flash.jsonl').stat().st_size==0
 off,_,base,size=struct.unpack_from('<4I',rom,32);decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
 def fact(pc,op=None):
  assert base<=pc<base+size
  actual=word(rom,off+pc-base);assert actual==word(ram,pc-0x2000000)
  if op is not None:assert actual==op,(hx(pc),hx(actual),hx(op))
  d=next(decoder.disasm(struct.pack('<I',actual),pc));return dict(pc=hx(pc),opcode=hx(actual),decode=d.mnemonic+' '+d.op_str)
 def original(a,w):return int.from_bytes((dt if 0x27e0000<=a<0x27e4000 else ram)[a-(0x27e0000 if 0x27e0000<=a<0x27e4000 else 0x2000000):a-(0x27e0000 if 0x27e0000<=a<0x27e4000 else 0x2000000)+w],'little')
 assert word(rom,off+0x2067d64-base)==word(ram,0x67d64)==0xffff
 # Fold explicit proof annotations into a certificate, never dispatch ROM instructions.
 regs=entry.copy();flags=[1,0,0,0];known={};writes=[];facts=[];read_facts=[]
 for idx,(pc,op,effect) in enumerate(FACTS):
  f=fact(pc,op);f.update(index=idx,effect=effect,r_before=[hx(v) for v in regs],nzcv_before=flags.copy(),predicate='AL' if op>>28==14 else ('LT false' if pc==0x20672b4 else 'GE false' if pc==0x20672bc else 'NE true'),memory_class='instruction fetch only (main RAM code)')
  if pc==0x20672b4:assert flags[0]==flags[3]
  if pc==0x20672bc:assert flags[0]!=flags[3]
  if op>>28==1:assert flags[1]==0
  if pc in [0x20672b0,0x20672b8]:assert regs[1]==0
  if pc==0x20672c4:assert regs[2]==1 and regs[1]==0
  if pc==0x20672cc:assert regs[2]==regs[3]==1 and flags[2:]==[0,0]
  if pc==0x20672d0:assert regs[0]+(regs[1]<<2)==0x20e9f70
  nxt=FACTS[idx+1][0] if idx+1<len(FACTS) else 0x2026044
  if pc in [0x2067c54,0x2067c58,0x2026010]:
   imm=op&0xffffff;imm=imm-0x1000000 if imm&0x800000 else imm;assert pc+8+4*imm==nxt
  elif pc==0x20672d8:assert nxt==regs[14] and nxt&3==0
  elif pc==0x2067d60:assert nxt==original(regs[13]+4,4) and original(regs[13],4)==0x20e9a00
  else:assert nxt==pc+4
  for a,w,v,kind in READS.get(pc,[]):
   assert known.get((a,w),original(a,w))==v
   if pc!=0x2067d60:
    rn=(op>>16)&15;assert (pc+8 if rn==15 else regs[rn])+(op&0xfff)==a
    assert CHANGES[pc][(op>>12)&15]==v
   rr=dict(pc=hx(pc),address=hx(a),width=w,value=hx(v),memory_class=kind);read_facts.append(rr);f.setdefault('data_reads',[]).append(rr);f['memory_class']=kind
  for spc,offset,width,src,value in STORES:
   if spc!=pc:continue
   assert regs[src] & ((1<<(8*width))-1)==value
   rn=(op>>16)&15;imm=op&0xfff if width==4 else ((op>>4)&0xf0)|(op&15)
   assert (op>>12)&15==src and regs[rn]+imm==0x20e9a00+offset
   assert any(int(f['address'],16)==0x20e9a00+offset and f['width']==width for f in ao['memory']['mapped_fields'])
   a=0x20e9a00+offset;old=known.get((a,width),original(a,width));known[(a,width)]=value
   wf=dict(**fact(pc),address=hx(a),exercise_offset=hex(offset),width=width,source='r'+str(src),value=hx(value),before=hx(old),after=hx(value),value_changing=old!=value,already_mapped_in_AO=True,semantics='offset only; unproven')
   writes.append(wf);f['store']=wf;f['memory_class']='main RAM object store'
  for k,v in CHANGES.get(pc,{}).items():regs[k]=v
  flags=FLAG_CHANGES.get(pc,flags).copy();regs[15]=nxt
  f.update(r_after=[hx(v) for v in regs],nzcv_after=flags.copy(),next_pc=hx(nxt));facts.append(f)
 assert len(facts)==45 and len(writes)==18 and sum(w['value_changing'] for w in writes)==6
 assert regs==[0x20e9f70,0x60000,0,1,0x20e9a00,0,218,0x20e9a00,0x20e9a00,0,0,0,0,0x27e3b0c,0x2067c58,0x2026044]
 diffs=[]
 for (a,w),v in sorted(known.items()):
  for i,(old,new) in enumerate(zip(original(a,w).to_bytes(w,'little'),v.to_bytes(w,'little'))):
   if old!=new:diffs.append(dict(address=hx(a+i),before=old,after=new))
 assert diffs==[dict(address=hx(a),before=b,after=c) for a,b,c in [(0x20ea1bc,0x34,0x70),(0x20ea1bd,0xa0,0x9f),(0x20ea1c9,0xd0,0),(0x20ea1ca,2,8),(0x20ea1f4,0,1)]]
 fields=[]
 for f in ao['memory']['mapped_fields']:
  a=int(f['address'],16);fields.append(dict(f,before=f['after'],after=known.get((a,f['width']),f['after'])))
 fields.append(dict(offset='0x610',address='0x020EA010',width=4,before=original(0x20ea010,4),after=0))
 forbidden=dict(**fact(0x2026044,0xeb01053c),target='0x0206753C',r0_r3=[hx(x) for x in regs[:4]],sp=hx(regs[13]),lr_before=hx(regs[14]),lr_if_dispatched='0x02026048',bounded_read_only=False,reason='Not a cheap accessor: nine-register PUSH, 0x48C local allocation, pointer dereference and nested calls. Excluded before call dispatch; no callee-wide effect/return claim.')
 lookahead=[fact(p) for p in range(0x206753c,0x2067568,4)]+[fact(p) for p in range(0x2001a14,0x2001a2c,4)]
 assert word(rom,off+0x2067aec-base)==word(ram,0x67aec)==0x48c
 assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 return dict(task='AP',classification='FULL PASS',authoritative_ao_commit=AO,authoritative_an_commit=AN,authoritative_am_commit=AM,rom_sha1=ao['rom_sha1'],framework_baseline=BASE,entry=ao['ao_stop'],entry_hashes=dict(mainram=sha(ram),dtcm=sha(dt),save=sha(save)),provenance='Committed reports/helpers match named commits; retained AO CPU, terminal non-dispatch, full images, mapped fields and ROM words checked read-only.',resolved_evidence_discrepancy='AO flags_before/flags_after summary arrays are stale 0010; ao_start/ao_stop named NZCV and retained audit are 1000. AP uses named fields, consistent with AN and STR preserving flags; predecessor artifacts unchanged.',instructions=facts,data_reads=read_facts,stores=writes,calls=[dict(pc='0x02067C54',target='0x020672B0',r0_r3=['0x020E9F70','0x00000000','0x00000000','0x0000001F'],sp='0x027E3B04',lr_before='0x02026010',lr_after='0x02067C58',bounded_read_only=True,callee_instruction_count=11,returns_at='0x020672D8',return_to='0x02067C58')],returns=[dict(pc='0x020672D8',target='0x02067C58',kind='BXNE LR',sp='unchanged'),dict(pc='0x02067D60',target='0x02026010',kind='POP {r4,pc}',sp_before='0x027E3B04',sp_after='0x027E3B0C',lr='0x02067C58')],first_next_meaningful_action=writes[0],forbidden_next=forbidden,excluded_callee_rationale_facts=lookahead,aq=dict(start_pc='0x02067C48',stop_pc='0x02026044',stop_before='fetch/dispatch of BL 0206753C; after caller store 02026040',instruction_count=45,pc_sequence=[f['pc'] for f in facts],r=[hx(v) for v in regs],nzcv=flags,t=0,mode=31,i=0,f=0,predicted_arm9_ordinal=281097990,architectural_writes=18,value_changing_write_events=6,idempotent_write_events=12,mainram_changed_bytes=5,byte_diffs=diffs,dtcm_writes=0,dtcm_changed_bytes=0,mapped_fields=fields,save_changed_bytes=0,logical_save_requests=0,flash_commits=0,mmio_accesses=0,instruction_fetches=45,data_read_words=6),safety=dict(guest_dispatches=0,guest_image_writes=0,aq_started=False,input_hashes_unchanged=True),input_sha256=before,evidence_tier='Exact-ROM static analysis anchored in forced Tier-3 exact-context original ARM interpreter AO evidence; no compiled parity',limitations=['Conditional on frozen AO state and future fail-closed guards','No general gameplay or field semantics claim','No cycle or scheduler accounting prediction','No effect/return guarantee for excluded call 0206753C'])

def report(r):
 a=r['aq'];lines=['# Task AP - post-AO static map','', '**FULL PASS.** Recommend one AQ experiment from `0x02067C48` through **45 instructions**, stopping **before fetch/dispatch of `0x02026044 / EB01053C / BL 0x0206753C`**. AP performed static reads only; AQ was not started.','', 'AO/AN/AM commits: `'+AO+'`, `'+AN+'`, `'+AM+'`. ROM SHA-1 `'+r['rom_sha1']+'`; ndsrecomp baseline `'+BASE+'`. All required reports/helpers match these commits (line-ending normalized). AO retained CPU/audit, terminal non-dispatch record, full RAM/DTCM/save and every mapped field were revalidated. Every mapped instruction and literal matches verified ROM and retained RAM.','', 'Entry r0-r12: `02132750,02131D24,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067C48`, NZCV=`1000`, T=0, mode=31, I=F=0, ARM9 ordinal=281097945.','', 'Entry SHA-256: '+json.dumps(r['entry_hashes'])+'.','', '**Evidence correction:** '+r['resolved_evidence_discrepancy'], '', 'The next meaningful action is `02067C50`: exercise+7BC changes `020EA034 -> 020E9F70`. The larger prefix is safe to propose because every source/address is deterministic, the accessor is bounded, and the nested helper returns cleanly. Continue across the return and three understood caller stores. The next call is a separate substantial operation; stop before it. Reaching it after fully bounding these effects does not trigger the PARTIAL criterion (an unknown call before the next bounded effect).', '', 'All numbers below are hexadecimal except counts. Each instruction fetch is ordinary main-RAM code. Unlisted registers, SP/LR and flags remain unchanged. Sequential successor is PC+4 unless stated. The JSON records complete before/after registers, NZCV, predicate and exact successor for every instruction.','', '| PC / opcode | Decode | Predicate / effect | Data access class |','|---|---|---|---|']
 for f in r['instructions']:lines.append(f"| {f['pc']} / {f['opcode']} | {f['decode']} | {f['predicate']}; {f['effect']} | {f['memory_class']} |")
 lines += ['', 'All 18 direct stores are already mapped AO fields. Six store events change values; twelve are idempotent. No stack/global/unknown/MMIO store occurs. Store order matters: +7C8 and +7CC are zeroed before the caller sets them; +7CC ends equal to AO despite two value-changing events. Offset names carry no semantic claim.','', '| PC / opcode | Address / exercise offset | Width / source | Immediate before -> after | Class |','|---|---|---|---|---|']
 for w in r['stores']:lines.append(f"| {w['pc']} / {w['opcode']} | {w['address']} / {w['exercise_offset']} | {w['width']} / {w['source']} | {w['before']} -> {w['after']} | {'value-changing' if w['value_changing'] else 'idempotent'} |")
 lines += ['', '`02067C54 -> 020672B0` is the only included call: r0-r3=`020E9F70,0,0,1F`, SP=`027E3B04`, LR=`02026010 -> 02067C58`. Its 11-instruction path has two object reads (+630=1, newly mapped +610=0), no stores, no nested calls and no stack adjustment. LT/GE fail; NE instructions execute. BXNE at `020672D8` returns to `02067C58`, r0-r3=`0,0,1,1`, NZCV=0000.','', 'The second return, POP at `02067D60`, reads DTCM `027E3B04=020E9A00` and `027E3B08=02026010`; SP becomes `027E3B0C`, r4 becomes exercise base, LR stays `02067C58`. This returns the nested helper only. The outer helper has not returned. No DTCM byte changes.','', 'Forbidden call `02026044 -> 0206753C`: r0-r3=`020E9F70,60000,0,1`, SP=`027E3B0C`, incoming LR=`02067C58`; dispatch would set LR=`02026048`. It is not certified read-only/bounded. Static inspection shows a nine-register PUSH, literal `02067AEC=48C` stack allocation, pointer dereference and a nested BL at `02067564 -> 02001A14`; that helper itself calls `02001974` and `020019B0`. The PUSH would start writing DTCM at `027E3AE8` (SP-24 hex), and later SP would become `027E365C`. No callee execution, whole-callee effect claim, or continuation past this call is authorized by the proposed AQ.','', 'AQ terminal r0-r12: `020E9F70,60000,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B0C`, LR=`02067C58`, PC=`02026044`, NZCV=`0000`, T=0, mode=31, I=F=0. ARM9 ordinal predicted `281097990` (+45). No cycle or scheduler prediction.','', 'Expected architectural writes: 18 ordinary object writes (16 words, 2 halfwords); final main-RAM diff exactly five bytes:','', '| Address | AO byte | AQ predicted byte |','|---|---|---|']
 for d in a['byte_diffs']:lines.append(f"| {d['address']} | {d['before']:02X} | {d['after']:02X} |")
 lines += ['', 'Only final mapped fields +7BC (`020EA034 -> 020E9F70`), +7C8 (`2D000 -> 80000`), and +7F4 (`0 -> 1`) change. All other AO fields remain equal at the boundary, including +7C0=`02132750`, +7C4=0 and +7CC=`60000`. JSON enumerates all values. Newly mapped +610 remains zero. DTCM/save byte diffs=0; save requests=0; Flash commits=0; MMIO=0. No general gameplay-completion interpretation is established.','', '**Future AQ guard contract (recommendation, not an implemented runtime):** reconstruct exact AO evidence; check ROM identity, all CPU flags/mode/masks, full RAM/DTCM/save hashes, ordinal, instruction words, and stack words before arming. Permit only the 45 ordered PC/opcode/full-state transitions in JSON, 45 instruction fetches and six data-read words listed there. The D10-dependent read must see the written zero. Permit exactly the 18 ordered store events with exact PC, address, width, source, immediate-before and readback values, including idempotent stores. Deny unexpected/repeated reads or writes before the bus, MMIO, save requests, path divergence, extra call, scheduler handoff or any instruction beyond the budget. Terminal control must run before fetch/accounting/dispatch of `02026044`; validate full CPU and complete memory diffs there, then halt/unwind. Do not merely gate final bytes: transient zeroing of +7CC must be audited.','', 'Validation: static certificate and focused negative checks (wrong opcode, divergent branch, wrong store address/source, wrong stack restoration) pass; report/JSON regeneration is deterministic. Run `python -B tools/task_ap/check.py` for these checks. Reproduce with `python tools/task_ap/analyze.py`; add `--export` to regenerate only the AP Markdown/JSON. Capstone decodes verified ROM words; explicit static arithmetic/proof annotations derive the certificate. There is no ARM interpreter, guest instruction dispatch, replay, build, checkpoint write, ROM patch or generated-C edit. All required predecessor sources and retained AO files are hashed before/after. Only ROM-free AP artifacts are written. Unrelated `jarvis-inbox-v1.zip` remains untouched.','', 'Evidence: exact-ROM static analysis anchored in **forced Tier-3 exact-context original ARM interpreter** AO observations; **no compiled parity**. Predictions require frozen context and future guards. Stopped after AP; AQ not executed.','']
 return '\n'.join(lines)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');args=p.parse_args();result=analyze()
 if args.export:
  (ROOT/'docs/BrainAge_TaskAP_Result.json').write_text(json.dumps(result,indent=2)+'\n')
  (ROOT/'docs/BrainAge_TaskAP_PostAOStaticMap.md').write_text(report(result))
 print(json.dumps(dict(classification=result['classification'],instructions=result['aq']['instruction_count'],writes=18,changed_bytes=5,stop=result['aq']['stop_pc'],guest_dispatches=0)))
