"""AR fixed static proof annotations. No guest dispatch or guest-image mutation.
--export writes only the two ROM-free AR reports. Default is read-only.
"""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
AQ='06b1432abaac62be3e4649afe58a70b2d5bb793d'
AP='f36f1ac432a5946f1b451e2d437176447163df3f'
AO='3e2ecf215823ad1e5b95a4af830d4ee6026152e0'
BASE='3a57236bb23d25dcb4caad7d58d733311062ff5e'
ENTRY=[0x20e9f70,0x60000,0,1,0x20e9a00,0,0xda,0x20e9a00,0x20e9a00,0,0,0,0,0x27e3b0c,0x2067c58,0x2026044]
# Explicit proof annotations, not a generic opcode evaluator or ARM interpreter.
FACTS=[
(0x2026044,0xeb01053c,{14:0x2026048},'BL creates LR=02026048; target=0206753C'),
(0x206753c,0xe92d4ff0,{13:0x27e3ae8},'Save r4-r11,LR in ascending DTCM words; SP -= 24 hex'),
(0x2067540,0xe59fc5a4,{12:0x48c},'r12=[02067AEC]=48C'),
(0x2067544,0xe04dd00c,{13:0x27e365c},'SP -= r12(48C); allocation writes no memory'),
(0x2067548,0xe2804f93,{4:0x20ea1bc},'r4=r0+24C=exercise+7BC'),
(0x206754c,0xe5949014,{9:0x1000},'r9=[exercise+7D0]=1000'),
(0x2067550,0xe5941004,{1:0x2132750},'r1=[exercise+7C0]=02132750'),
(0x2067554,0xe58d000c,{},'Save r0 at SP+C=027E3668 (idempotent)'),
(0x2067558,0xe1a00009,{0:0x1000},'r0=r9=1000'),
(0x206755c,0xe591a02c,{10:0x20fd00c},'r10=[02132750+2C]=020FD00C; unnamed pointee field'),
(0x2067560,0xe5948018,{8:0x1000},'r8=[exercise+7D4]=1000')]
READS={0x2067540:(0x2067aec,0x48c,12,'main RAM ROM literal'),0x206754c:(0x20ea1d0,0x1000,9,'main RAM exercise+7D0'),0x2067550:(0x20ea1c0,0x2132750,1,'main RAM exercise+7C0'),0x206755c:(0x213277c,0x20fd00c,10,'main RAM pointee+2C; offset-only'),0x2067560:(0x20ea1d4,0x1000,8,'main RAM exercise+7D4')}
STOP=0x2067564
FINAL=[0x1000,0x2132750,0,1,0x20ea1bc,0,0xda,0x20e9a00,0x1000,0x1000,0x20fd00c,0,0x48c,0x27e365c,0x2026048,STOP]
def hx(x):return f'0x{x:08X}'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a,cwd=ROOT):return subprocess.check_output(['git',*a],cwd=cwd)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def word(b,o):return struct.unpack_from('<I',b,o)[0]

def analyze():
 assert git('branch','--show-current').decode().strip()=='codex/brainage'
 assert git('rev-parse','HEAD',cwd=ROOT/'local/ndsrecomp').decode().strip()==BASE
 paths=[]
 for commit,tag,title in [(AQ,'AQ','DynamicHelperTailBoundary'),(AP,'AP','PostAOStaticMap'),(AO,'AO','SecondValueChangingObjectStore')]:
  git('merge-base','--is-ancestor',commit,'HEAD')
  names=[f'docs/BrainAge_Task{tag}_{title}.md',f'docs/BrainAge_Task{tag}_Result.json']+git('ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/').decode().splitlines()
  for name in names:
   p=ROOT/name;assert git('show',commit+':'+name).decode('utf-8-sig').splitlines()==p.read_text(encoding='utf-8-sig').splitlines(),name;paths.append(p)
 aq=load(ROOT/'docs/BrainAge_TaskAQ_Result.json');ap=load(ROOT/'docs/BrainAge_TaskAP_Result.json')
 session=ROOT/aq['authoritative_path'];rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
 paths += [rompath]+sorted(p for p in session.iterdir() if p.is_file())
 before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 rom=rompath.read_bytes();ram=(session/'decision-after-mainram.bin').read_bytes();dt=(session/'decision-after-dtcm.bin').read_bytes();save=(session/'decision-after.sav').read_bytes()
 assert hashlib.sha1(rom).hexdigest()==aq['rom_sha1']=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
 assert len(ram)==0x400000 and len(dt)==0x4000
 assert sha(ram)==aq['memory']['mainram_after_sha256']=='84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340'
 assert sha(dt)==aq['memory']['dtcm_after_sha256']=='1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716'
 assert sha(save)==aq['save']['after_sha256']=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
 audit=[json.loads(l) for l in (session/'audit.jsonl').read_text().splitlines()]
 steps=[v for v in audit if v['event']=='aq_step'];assert steps==aq['instruction_observations'] and len(steps)==46
 assert steps[-1]==aq['aq_stop'] and steps[-1]['r']==ENTRY and steps[-1]['pc']==ENTRY[15] and steps[-1]['opcode']==0xeb01053c
 assert [steps[-1][k] for k in ['n','z','c','v','t','mode','i','f','insn9']]==[0,0,0,0,0,31,0,0,281097990]
 assert [v for v in audit if v['event']=='decision_stopped']==[dict(event='decision_stopped',aq_instructions=45,aq_writes=18,aq_reads=51,successor_fetched=False,successor_dispatched=False)]
 assert [v for v in audit if v['event']=='aq_read_event']==aq['bus_reads']
 assert len(aq['bus_reads'])==51 and all(v['pc']!=ENTRY[15] for v in aq['bus_reads'])
 assert [v for v in audit if v['event']=='aq_write_event']==[v['actual_event'] for v in aq['architectural_stores']]
 assert aq['executed_pcs']==ap['aq']['pc_sequence'] and aq['forbidden_next']['target_entered'] is False
 for i,s in enumerate(steps):
  e=ap['instructions'][i] if i<45 else dict(r_before=ap['aq']['r'],nzcv_before=ap['aq']['nzcv'],pc=ap['aq']['stop_pc'],opcode=ap['forbidden_next']['opcode'])
  assert s['r']==[int(v,16) for v in e['r_before']] and s['pc']==int(e['pc'],16) and s['opcode']==int(e['opcode'],16)
  assert [s[k] for k in ['n','z','c','v']]==e['nzcv_before'] and s['insn9']==281097945+i
 assert (session/'aq-before-dtcm.bin').read_bytes()==dt and (session/'aq-before.sav').read_bytes()==save
 assert not (session/'requests.jsonl').stat().st_size and not (session/'flash.jsonl').stat().st_size
 for f in aq['memory']['mapped_fields']:
  a=int(f['address'],16)-0x2000000;assert int.from_bytes(ram[a:a+f['width']],'little')==f['after']
 off,_,base,size=struct.unpack_from('<4I',rom,32);decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
 def fact(pc,op=None):
  assert base<=pc<base+size
  actual=word(rom,off+pc-base);assert actual==word(ram,pc-0x2000000)
  if op is not None:assert actual==op,(hx(pc),hx(actual),hx(op))
  d=next(decoder.disasm(struct.pack('<I',actual),pc));return dict(pc=hx(pc),opcode=hx(actual),decode=d.mnemonic+' '+d.op_str)
 def original(a):
  if 0x27e0000<=a<=0x27e3ffc:return word(dt,a-0x27e0000)
  assert 0x2000000<=a<=0x23ffffc
  return word(ram,a-0x2000000)
 regs=ENTRY.copy();facts=[];writes=[];reads=[]
 for idx,(pc,op,changes,effect) in enumerate(FACTS):
  assert regs[15]==pc and op>>28==14
  f=fact(pc,op);f.update(index=idx,r_before=list(map(hx,regs)),nzcv_before=[0]*4,predicate='AL; unconditional',effect=effect,memory_class='main RAM instruction fetch only')
  nxt=FACTS[idx+1][0] if idx+1<len(FACTS) else STOP
  if idx==0:
   imm=op&0xffffff;imm=imm-0x1000000 if imm&0x800000 else imm
   assert pc+8+4*imm==nxt and changes=={14:pc+4}
  else:assert nxt==pc+4
  planned=[]
  if pc==0x206753c:
   saved=[i for i in range(16) if op&(1<<i)];assert saved==list(range(4,12))+[14]
   start=regs[13]-4*len(saved);assert changes=={13:start}
   planned=[(start+4*j,r) for j,r in enumerate(saved)]
  elif pc==0x2067554:
   assert not changes;planned=[(regs[(op>>16)&15]+(op&0xfff),(op>>12)&15)]
  elif pc==0x2067544:assert changes=={13:regs[13]-regs[12]}
  elif pc==0x2067548:assert changes=={4:regs[0]+0x24c}
  elif pc==0x2067558:assert changes=={0:regs[9]}
  if pc in READS:
   addr,value,dest,kind=READS[pc];rn=(op>>16)&15
   assert addr==(pc+8 if rn==15 else regs[rn])+(op&0xfff)
   assert dest==((op>>12)&15) and original(addr)==value and changes=={dest:value}
   if rn==15:assert word(rom,off+addr-base)==value
   rd=dict(pc=hx(pc),address=hx(addr),width=4,value=hx(value),memory_class=kind);reads.append(rd);f['data_reads']=[rd];f['memory_class']=kind
  for addr,src in planned:
   assert 0x27e0000<=addr<=0x27e3ffc
   old=original(addr);value=regs[src]
   w=dict(pc=hx(pc),opcode=hx(op),address=hx(addr),width=4,source='LR' if src==14 else 'r'+str(src),before=hx(old),after=hx(value),value_changing=old!=value,memory_class='DTCM stack',field='callee saved register' if pc==0x206753c else 'local saved object pointer; SP+0xC',exercise_field=None)
   writes.append(w);f.setdefault('stores',[]).append(w);f['memory_class']='DTCM stack writes'
  for k,v in changes.items():regs[k]=v
  regs[15]=nxt;f.update(r_after=list(map(hx,regs)),nzcv_after=[0]*4,next_pc=hx(nxt));facts.append(f)
 assert len(facts)==11 and len(reads)==5 and len(writes)==10 and sum(w['value_changing'] for w in writes)==8
 assert regs==FINAL
 diffs=[]
 for w in writes:
  for j,(b,a) in enumerate(zip(int(w['before'],16).to_bytes(4,'little'),int(w['after'],16).to_bytes(4,'little'))):
   if b!=a:diffs.append(dict(address=hx(int(w['address'],16)+j),before=b,after=a))
 diffs.sort(key=lambda d:d['address'])
 forbidden=dict(**fact(STOP,0xebfe692a),target='0x02001A14',r0_r3=list(map(hx,regs[:4])),sp=hx(regs[13]),lr_before=hx(regs[14]),lr_created='0x02067568',bounded_read_only=False,reason='Unconditionally calls MMIO-writing 02001974, then MMIO polling 020019B0. Stop before this BL, not within its prologue.')
 lookahead=[fact(pc) for lo,hi in [(0x2001a14,0x2001a2c),(0x2001974,0x20019a4),(0x20019b0,0x20019e4)] for pc in range(lo,hi,4)]
 literals={hx(a):hx(original(a)) for a in [0x20019a4,0x20019a8,0x20019ac,0x20019e4,0x20019e8]}
 assert list(literals.values())==list(map(hx,[0x4000280,0x4000290,0x4000298,0x4000280,0x40002a0]))
 for a,v in literals.items():assert word(rom,off+int(a,16)-base)==int(v,16)
 assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
 excluded_calls=[
  dict(forbidden,included_in_AS=False),
  dict(pc='0x02001A1C',opcode='0xEBFFFFD4',target='0x02001974',r0_r3=['0x00001000','0x02132750','0x00000000','0x00000001'],sp='0x027E3654',lr_before='0x02067568',lr_created='0x02001A20',included_in_AS=False,bounded_read_only=False,reason='Straight-line leaf has five unconditional MMIO writes'),
  dict(pc='0x02001A20',opcode='0xEBFFFFE2',target='0x020019B0',r0_r3=['0x00001000','0x04000298','0x04000290','0x00001000'],sp='0x027E3654',lr_before='0x02001A20',lr_created='0x02001A24',included_in_AS=False,bounded_read_only=False,reason='Conditional on excluded MMIO leaf completing; MMIO busy-bit polling has no static iteration bound')]
 excluded_mmio=[dict(pc=hx(pc),opcode=fact(pc)['opcode'],address=hx(a),width=w,source=src,value=hx(v),before=None,idempotent=None,memory_class='MMIO',included_in_AS=False) for pc,a,w,src,v in [(0x2001980,0x4000280,2,'r3',1),(0x2001988,0x4000290,4,'r12',0),(0x2001994,0x4000294,4,'r3',0x1000),(0x2001998,0x4000298,4,'r0',0x1000),(0x200199c,0x400029c,4,'r12',0)]]
 return dict(task='AR',classification='FULL PASS',excluded_calls=excluded_calls,excluded_mmio_writes=excluded_mmio,authoritative_AQ_commit=AQ,authoritative_AP_commit=AP,authoritative_AO_commit=AO,rom_sha1=aq['rom_sha1'],framework_baseline=BASE,entry=aq['aq_stop'],entry_hashes=dict(mainram=sha(ram),dtcm=sha(dt),save=sha(save)),instructions=facts,data_reads=reads,stores=writes,first_meaningful_action=writes[0],call=dict(pc='0x02026044',opcode='0xEB01053C',target='0x0206753C',r0_r3=list(map(hx,ENTRY[:4])),sp=hx(ENTRY[13]),lr_before=hx(ENTRY[14]),lr_created='0x02026048',whole_callee_bounded=False,frame_saved_bytes=36,local_allocation_bytes=1164,frame_sp='0x027E365C',teardown_reached=False),returns=[],forbidden_next=forbidden,excluded_lookahead=lookahead,excluded_literals=literals,AS=dict(start_pc=hx(ENTRY[15]),stop_pc=hx(STOP),stop_before='fetch/accounting/dispatch of BL 02001A14',instruction_count=11,pc_sequence=[f['pc'] for f in facts],r=list(map(hx,regs)),nzcv=[0]*4,t=0,mode=31,i=0,f=0,predicted_arm9_ordinal=281098001,architectural_word_writes=10,value_changing_writes=8,idempotent_writes=2,mainram_changed_bytes=0,dtcm_changed_bytes=len(diffs),dtcm_byte_diffs=diffs,save_changed_bytes=0,logical_save_requests=0,flash_commits=0,mmio_accesses=0,instruction_fetches=11,data_read_words=5,mapped_fields=[dict(f,before=f['after']) for f in aq['memory']['mapped_fields']]),safety=dict(guest_dispatches=0,guest_image_writes=0,AS_started=False,input_hashes_unchanged=True),input_sha256=before,evidence_tier='Exact-ROM static proof anchored in committed forced Tier-3 exact-context original ARM interpreter AQ evidence; no compiled parity',limitations=['No whole-callee termination proof: first nested operation reaches MMIO and polling','No object/gameplay transition before boundary; meaningful architectural effect is saved-frame DTCM mutation','AS recommendation only; no runtime guard implemented or experiment started','No scheduler/cycle prediction','Requested Astra Medium fresh thread could not be selected in this existing thread'])

def report(r):
 a=r['AS'];lines=['# Task AR - pending 0206753C static map','',
 '**FULL PASS for the safe-boundary map.** Recommend 11 instructions from AQ, stopping at `02067564 / EBFE692A / BL 02001A14` before fetch/accounting/dispatch. The whole 0206753C callee is **not** certified bounded or read-only: its first nested operation reaches MMIO writes and polling. AR performed no guest execution; AS was not started.','',
 'AQ/AP/AO commits: `'+AQ+'`, `'+AP+'`, `'+AO+'`. ROM SHA-1 `'+r['rom_sha1']+'`; ndsrecomp baseline `'+BASE+'`. Committed reports/helpers match. Retained AQ CPU observations, full images, terminal non-dispatch event, access ledgers and mapped fields were checked. Code/literals match ROM and retained RAM. Inputs were hashed before/after.','',
 'AQ entry r0-r12=`020E9F70,00060000,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B0C`, LR=`02067C58`, PC=`02026044`, NZCV=0000; T/mode/I/F=0/31/0/0, ordinal 281097990. Entry hashes: '+json.dumps(r['entry_hashes'])+'.','',
 'Unless specified as counts, addresses, offsets and register values below are hexadecimal. BL creates LR 02026048. The callee pushes r4-r11,LR (36 bytes), SP becomes 027E3AE8, then allocates 48C bytes to SP 027E365C. It saves the object pointer at SP+C. No teardown/return occurs in the permitted prefix. Following a return requires crossing excluded MMIO. All included predicates are AL, all instructions preserve NZCV, all fetches are main RAM; unlisted registers are unchanged. JSON contains full before/after states.','',
 '| PC / opcode | Decode | Effect | Data access |','|---|---|---|---|']
 for f in r['instructions']:lines.append(f"| {f['pc']} / {f['opcode']} | {f['decode']} | {f['effect']} | {f['memory_class']} |")
 lines += ['', 'The first meaningful architectural effect is PUSH 0206753C: its first word changes 027E3AE8 from 020EA644 to 020E9A00. This is saved-frame storage, not a gameplay claim. Continue through deterministic prologue/argument loads; stop at the first call with external effects. No unknown effect precedes this bounded value-changing store, so the safe-boundary map is FULL PASS. Whole-callee completion is not established.','', '| Store PC / opcode | DTCM address | Width / source | Before -> after | Class |','|---|---|---|---|---|']
 for w in r['stores']:lines.append(f"| {w['pc']} / {w['opcode']} | {w['address']} | 4 / {w['source']} | {w['before']} -> {w['after']} | {'value-changing' if w['value_changing'] else 'idempotent'} |")
 lines += ['', 'All ten writes are DTCM stack words: eight value-changing, two idempotent. None has an exercise-field name. Frame allocation does not initialize other local bytes. No main-RAM/object/global/save/Flash/MMIO write occurs in the prefix.','', '| Read PC | Address | Word | Class |','|---|---|---|---|']
 for d in r['data_reads']:lines.append(f"| {d['pc']} | {d['address']} | {d['value']} | {d['memory_class']} |")
 lines += ['', '## Excluded calls and returns','',
 'At 02067564, r0-r3=`1000,02132750,0,1`, SP=`027E365C`, LR=`02026048`; BL would create LR=`02067568`. The call is not read-only: original code proves unconditional MMIO access. Stop before it, not at an arbitrary point within its prologue.','',
 'Static lookahead only: 02001A14 would push LR at 027E3658; 02001A18 subtracts 4 to SP 027E3654. At 02001A1C, BL 02001974 would have the same r0-r3, incoming LR 02067568, created LR 02001A20. That leaf loads literal pointers and issues STRH 02001980 to 04000280 (width 2,r3=1); STR 02001988 to 04000290 (width 4,r12=0); STR 02001994 to 04000294 (width 4,r3=1000); STR 02001998 to 04000298 (width 4,r0=1000); STR 0200199C to 0400029C (width 4,r12=0). These are MMIO. Before-values/device effects are unproven; none is in the AS allowance.','',
 'Excluded BX LR 020019A0 would return 02001A20 without changing SP. Register arithmetic leaves r0-r3=`1000,04000298,04000290,1000`, r12=0, LR 02001A20. BL 020019B0 at 02001A20 would create LR 02001A24, SP 027E3654. This leaf reads a halfword at 04000280, ANDS bit 8000, then BNE 020019BC loops to 020019B4 when Z=0. Predicate depends on unobserved MMIO; iteration count and final state are not certified. Later reads 040002A0/A4 are also MMIO. Wrapper ADD SP,#4 and POP PC 02001A24/28 would undo its 8-byte frame and return 02067568 only if polling completes. They are excluded, as is all 0206753C teardown/caller continuation. JSON records each lookahead opcode/decode and checked pointer literal.','',
 '## Exact AS recommendation','',
 'Sequence: `'+ ' -> '.join(v[2:] for v in a['pc_sequence'])+'`; halt at 02067564 before its BL. Exactly 11 instruction fetches, five data-read words, ten DTCM word writes; ordinal 281098001 predicted. No cycle/scheduler prediction.','',
 'Final r0-r12=`1000,02132750,0,1,020EA1BC,0,DA,020E9A00,1000,1000,020FD00C,0,48C`; SP=`027E365C`, LR=`02026048`, PC=`02067564`, NZCV=0000; T/mode/I/F=0/31/0/0. Main RAM/save have zero byte differences. DTCM has exactly '+str(a['dtcm_changed_bytes'])+' changed bytes:','', '| DTCM byte | Before | After |','|---|---|---|']
 for d in a['dtcm_byte_diffs']:lines.append(f"| {d['address']} | {d['before']:02X} | {d['after']:02X} |")
 lines += ['', 'Every AQ mapped field remains unchanged: phase/delay/correct-count/result flag 1/1/1/1; +7BC=020E9F70,+7C0=02132750,+7C4=0,+7C8=80000,+7CC=60000,+7F4=1; +7D0/+7D4=1000. No semantic name is assigned to pointee+2C. Save SHA remains '+r['entry_hashes']['save']+'; logical requests=0, Flash commits=0, MMIO accesses=0.','',
 'AS guard contract (recommendation only): reconstruct AQ independently, verify all CPU flags/mode/masks, full RAM/DTCM/save hashes, ordinal, code/literals/data. Permit only eleven ordered PC/opcode/full-state transitions and five reads. Deny extra fetch/read/write before the bus. Audit all nine PUSH words in ascending order and the local pointer store, exact source/before/readback, including idempotent stores. Validate SP and complete memory at each observation. Deny MMIO, save requests, extra guest/scheduler dispatch, divergence and budget overrun. Halt before terminal fetch/accounting/dispatch, compare complete images/registers. Forbidden next instruction is 02067564, not just MMIO store 02001980. No runtime guard installed.','',
 'Read-only reproduction: `python -B tools/task_ar/check.py`. Export only these reports: `python -B tools/task_ar/analyze.py --export`. Checks cover provenance, fixed operand/address/frame arithmetic, reproducibility and negative opcode/source/address/SP/entry tests. No interpreter, replay, runtime build, checkpoint/save mutation, ROM patch, generated-C edit or scheduler refactor. Unrelated jarvis-inbox-v1.zip preserved.','',
 'Evidence: exact-ROM static proof anchored in forced Tier-3 exact-context original ARM interpreter AQ evidence; no compiled parity. Predictions require frozen context and future guards. Requested Astra Medium fresh thread could not be selected in this existing thread. Stopped after AR; AS not started.','']
 return '\n'.join(lines)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');args=p.parse_args();r=analyze()
 if args.export:
  (ROOT/'docs/BrainAge_TaskAR_Result.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  (ROOT/'docs/BrainAge_TaskAR_Pending6753CStaticMap.md').write_text(report(r),encoding='utf-8')
 print(json.dumps(dict(classification=r['classification'],instructions=11,writes=10,dtcm_bytes=r['AS']['dtcm_changed_bytes'],stop=r['AS']['stop_pc'],guest_dispatches=0)))
