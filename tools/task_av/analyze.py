"""AV file-only certificate. No guest evaluator, runtime import, or replay.
Only --export writes, and only the ROM-free AV result JSON.
"""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path
import capstone
ROOT = Path(__file__).resolve().parents[2]
AU = 'f17f95ae2b2a15f7fced6f04d82d2593350d37a4'
AT = '6478bd11b386799a3f4e03f923c39227e982c51d'
BASE = '3a57236bb23d25dcb4caad7d58d733311062ff5e'
ROM_SHA1 = 'b8a105bacc3234dede8d4465df0869f2b922a0e2'
ENTRY = [0x1000,0x4000280,0x4000290,1,0x20ea1bc,0,0xda,0x20e9a00,
         0x1000,0x1000,0x20fd00c,0,0x48c,0x27e3654,0x2001a20,0x2001980]
# Explicit reviewed facts, NOT an opcode evaluator. Deltas are proof annotations.
PATH = [
 (0x2001980,0xe1c130b0,'STRH r3,[r1]',{},8),
 (0x2001984,0xe3a0c000,'MOV r12,#0',{12:0},1),
 (0x2001988,0xe582c000,'STR r12,[r2]',{},8),
 (0x200198c,0xe3a03a01,'MOV r3,#0x1000',{3:0x1000},1),
 (0x2001990,0xe59f1014,'LDR r1,[pc,#0x14]',{1:0x4000298},3),
 (0x2001994,0xe5823004,'STR r3,[r2,#4]',{},8),
 (0x2001998,0xe5810000,'STR r0,[r1]',{},8),
 (0x200199c,0xe581c004,'STR r12,[r1,#4]',{},8),
 (0x20019a0,0xe12fff1e,'BX lr',{},4),
 (0x2001a20,0xebffffe2,'BL 0x020019B0',{14:0x2001a24},4),
 (0x20019b0,0xe59f102c,'LDR r1,[pc,#0x2c]',{1:0x4000280},3),
 (0x20019b4,0xe1d100b0,'LDRH r0,[r1]',{0:0x8001},8),
]
LOOKAHEAD = {0x20019b8:0xe2100902,0x20019bc:0x1afffffc,
             0x20019c0:0xe59f1020,0x20019c4:0xe3a00702,
             0x20019c8:0xe5912000,0x20019cc:0xe5911004}
LITERALS={0x20019a4:0x4000280,0x20019a8:0x4000290,0x20019ac:0x4000298,
          0x20019e4:0x4000280,0x20019e8:0x40002a0}
MMIO=[(0x2001980,0x4000280,2,'write',1),(0x2001988,0x4000290,4,'write',0),
      (0x2001994,0x4000294,4,'write',0x1000),(0x2001998,0x4000298,4,'write',0x1000),
      (0x200199c,0x400029c,4,'write',0),(0x20019b4,0x4000280,2,'read',0x8001)]
C0=3416875721
SRC=['runner/src/io.cpp','runner/src/bus.cpp','runner/src/tier3.cpp',
     'runner/src/runtime_arm.cpp','runner/src/scheduler.cpp','runner/src/frontend.cpp',
     'runner/src/main.cpp','recompiler/armv4t/runtime_arm.h',
     'external/arm-recomp-core/common/interpreter.cpp']
def hx(n):return f'0x{n:08X}'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def word(b,o):return struct.unpack_from('<I',b,o)[0]
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*args],cwd=cwd)
def body(t,s):
 start=t.index(s);return t[start:t.index('\n}',start)+2]
def ordered(t,*tokens):
 positions=[t.index(x) for x in tokens];assert positions==sorted(positions),tokens

def analyze():
 fw=ROOT/'local/ndsrecomp'; inputs=[]
 assert git('branch','--show-current').decode().strip()=='codex/brainage'
 assert git('rev-parse','HEAD',cwd=fw).decode().strip()==BASE
 for commit,tag,title in [(AU,'AU','DynamicPreMMIOBoundary'),(AT,'AT','NestedMMIOStaticMap')]:
  git('merge-base','--is-ancestor',commit,'HEAD')
  names=[f'docs/BrainAge_Task{tag}_{title}.md',f'docs/BrainAge_Task{tag}_Result.json']
  names+=git('ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/').decode().splitlines()
  for name in names:
   p=ROOT/name
   assert git('show',commit+':'+name).decode('utf-8-sig').splitlines()==p.read_text(encoding='utf-8-sig').splitlines(),name
   inputs.append(p)
 au=load(ROOT/'docs/BrainAge_TaskAU_Result.json'); at=load(ROOT/'docs/BrainAge_TaskAT_Result.json')
 session=ROOT/au['authoritative_path']
 rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
 inputs += [rompath]+sorted(p for p in session.iterdir() if p.is_file())+[fw/n for n in SRC]
 before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in inputs}
 rom=rompath.read_bytes(); assert hashlib.sha1(rom).hexdigest()==ROM_SHA1
 ram=(session/'decision-after-mainram.bin').read_bytes(); dt=(session/'decision-after-dtcm.bin').read_bytes()
 assert len(ram)==0x400000 and len(dt)==0x4000
 assert sha(ram)==au['memory']['mainram_after_sha256']
 assert sha(dt)==au['memory']['dtcm_after_sha256']
 assert word(dt,0x3658)==0x2067568
 assert au['au_stop']['r']==ENTRY and au['au_stop']['opcode']==PATH[0][1]
 assert au['au_stop']['insn9']==281098008
 assert [au['au_stop'][k] for k in ['n','z','c','v','t','mode','i','f']]==[0,0,0,0,0,31,0,0]
 rows=[json.loads(l) for l in (session/'audit.jsonl').read_text().splitlines()]
 assert not any(x['event']=='failure' for x in rows)
 assert [x for x in rows if x['event']=='au_step']==au['instruction_observations']
 assert [x for x in rows if x['event']=='au_read_event']==au['bus_reads']
 assert [x for x in rows if x['event']=='au_step'][-1]==au['au_stop']
 stop=next(x for x in rows if x['event']=='decision_stop_sample')
 assert (stop['cycle9'],stop['cycle7'],stop['insn9'],stop['insn7'])==(C0,1708437825,281098008,96026779)
 ended=next(x for x in rows if x['event']=='decision_stopped')
 assert not ended['successor_fetched'] and not ended['successor_dispatched']
 assert (ended['au_reads'],ended['au_writes'],ended['au_instructions'])==(9,1,7)
 for name in ['decision-after.sav','final.sav','session.sav','initial.sav']:
  assert sha((session/name).read_bytes())==au['save']['after_sha256']
 for name in ['requests.jsonl','flash.jsonl']:assert not (session/name).read_bytes()
 for f in au['memory']['mapped_fields']:
  off=int(f['address'],16)-0x2000000
  assert int.from_bytes(ram[off:off+f['width']],'little')==f['before']==f['after']
 assert len(au['memory']['mapped_fields'])==35
 ro,_,ra,rs=struct.unpack_from('<4I',rom,0x20)
 decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
 facts=[]
 words={**{p:o for p,o,_,_,_ in PATH},**LOOKAHEAD}
 for p,o in sorted(words.items()):
  assert ra<=p<ra+rs and word(rom,ro+p-ra)==word(ram,p-0x2000000)==o
  ins=list(decoder.disasm(struct.pack('<I',o),p));assert len(ins)==1
  facts.append(dict(pc=hx(p),opcode=hx(o),decode=ins[0].mnemonic+' '+ins[0].op_str))
 for p,v in LITERALS.items():assert word(rom,ro+p-ra)==word(ram,p-0x2000000)==v
 source={n:(fw/n).read_text(encoding='utf-8-sig') for n in SRC}
 io=source['runner/src/io.cpp']; tier=source['runner/src/tier3.cpp']; sched=source['runner/src/scheduler.cpp']; rt=source['runner/src/runtime_arm.cpp']
 signatures=['uint64_t active_system_timestamp()', 'void start_div()', 'void finish_div()',
             'uint32_t math_reg_read32(', 'bool math_addr(', 'void math_reg_write(',
             'uint64_t nds_next_system_event_time()', 'void nds_run_system_events(']
 baseio=git('show',BASE+':runner/src/io.cpp',cwd=fw).decode()
 for sig in signatures:assert body(io,sig)==body(baseio,sig),sig
 assert body(io,'void math_reg_write(').count('start_div();')==5
 assert 'g_div_deadline = active_system_timestamp() +' in body(io,'void start_div()')
 assert '((g_divcnt & 0x3u) == 0u ? 18u : 34u)' in io
 assert 'g_div_deadline = UINT64_MAX;\n        finish_div();' in io
 assert 'cpu == 0 && math_addr(addr)' in io
 ordered(tier,'brainage_task_au::control(ic)','const bool covered = nds_has_bank','++g_stats.instructions','r = Interpreter::step','g_runtime_cycles += cyc + runtime_deferred_cycles_take();','if (poll_after && !ic.cpsr.i && nds_irq_pending','if (poll_after && nds_slice_over())')
 ordered(sched,'run_slice(0,','nds_tick_timers(0,','nds_gpu3d_run(','const uint64_t rendezvous =','run_slice(1, quantum)','nds_tick_display(rendezvous)','nds_run_system_events(rendezvous)')
 halt=body(rt,'extern "C" void nds_halt(')
 assert 'g_nds_terminal = true' in halt and 'scheduler_terminal_halt_all' not in halt
 assert 'cpu_deadline < g_cycle_cap' in body(rt,'extern "C" void nds_reschedule_slice(')
 assert 'g_slot[cpu].cycles = g_runtime_cycles;' in sched
 assert 'bus.access_cycles(effective_addr, access_w, false)' in source[SRC[-1]]
 r=ENTRY.copy();elapsed=0;trace=[];ledger=[]
 for j,(p,o,decode,changes,cost) in enumerate(PATH):
  assert r[15]==p
  before_r=r.copy();c=C0+elapsed
  numc=3 if (p+8)%32==0 else 1
  if p in (0x20019a0,0x2001a20): expected_cost=4
  else:
   numd=8 if p in [m[0] for m in MMIO] else (3 if p in (0x2001990,0x20019b0) else 0)
   expected_cost=max(numc,numd,numc+numd-6) if numd else numc
  assert cost==expected_cost,(hx(p),cost,expected_cost)
  if p in (0x2001990,0x20019b0):
   assert changes=={1:LITERALS[p+8+(o&0xfff)]}
  if p==0x2001a20:
   imm=o&0xffffff
   assert p+8+4*(imm-0x1000000 if imm&0x800000 else imm)==0x20019b0
   assert changes=={14:p+4}
  for m in MMIO:
   if m[0]==p:
    rn=(o>>16)&15;rd=(o>>12)&15
    offset=0 if m[2]==2 else o&0xfff
    assert r[rn]+offset==m[1]
    if m[3]=='write':assert m[4]==r[rd] and not changes
    else:assert m[2]==2 and m[4]==0x8001 and changes=={rd:m[4]}
    ledger.append(dict(pc=hx(p),address=hx(m[1]),width=m[2],direction=m[3],value=hx(m[4]),
                       pre_instruction_cycle9=c,system_deadline=(c//2+34) if m[3]=='write' else None))
  for reg,v in changes.items():r[reg]=v
  r[15]=PATH[j+1][0] if j+1<len(PATH) else 0x20019b8
  elapsed+=cost
  trace.append(dict(pc=hx(p),opcode=hx(o),decode=decode,r_before=list(map(hx,before_r)),r_after=list(map(hx,r)),
                    nzcv=[0,0,0,0],conditional_cost=cost,cycle9_before=c,cycle9_after=C0+elapsed))
 assert elapsed==64 and r==[0x8001,0x4000280,0x4000290,0x1000,0x20ea1bc,0,0xda,0x20e9a00,0x1000,0x1000,0x20fd00c,0,0,0x27e3654,0x2001a24,0x20019b8]
 assert [x['system_deadline'] for x in ledger[:5]]==[1708437894,1708437899,1708437905,1708437909,1708437913]
 assert C0+64 < 2*ledger[0]['system_deadline']==C0+67
 assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in inputs}
 return dict(task='AV',classification='PARTIAL',reason='Current runtime source and ARM path identified; AU omitted live scheduler cap, timing and peripheral entry snapshots, and its terminal halt does not suppress scheduler tail. Conditional AW candidate is specified but eligibility is unproven.',
  authoritative_AU_commit=AU,authoritative_AT_commit=AT,framework_baseline=BASE,rom_sha1=ROM_SHA1,
  evidence_tier='Committed forced Tier-3 exact-context original ARM evidence plus file-only ROM/source inspection; no new execution or compiled parity',
  au_stop=au['au_stop'],au_stop_counters=stop,entry_images=dict(mainram=sha(ram),dtcm=sha(dt),save=au['save']['after_sha256']),mapped_fields=au['memory']['mapped_fields'],
  code_facts=facts,literals={hx(p):hx(v) for p,v in LITERALS.items()},
  source_functions_baseline_identical=signatures,input_sha256=before,
  AW=dict(status='CONDITIONAL DESIGN ONLY; not ready to execute',start_pc=hx(PATH[0][0]),stop_pc=hx(r[15]),stop='before fetch/accounting/dispatch of ANDS, after exactly one status read',instruction_count=12,
          pc_sequence=[hx(x[0]) for x in PATH],conditional_trace=trace,mmio_ledger=ledger,
          required_timing='cached code at all mapped PCs/branch targets; literal data numD=3; MMIO numD=8; deferred cycles=0; preexisting cap is zero or strictly greater than C0+64; no pending IRQ/halt/DMA/event break; no scheduler service/ARM7 dispatch; stop cannot return into scheduler tail',
          final_registers=list(map(hx,r)),nzcv=[0,0,0,0],conditional_cycle9=C0+64,insn9=281098020,
          final_divcnt=hx(0x8001),final_numer=[0,4096],final_denom=[4096,0],quotient_remainder='unchanged from REQUIRED entry snapshot, values not recorded by AU',final_deadline=1708437913,
          retained_cap='min(nonzero entry cap,3416875788); zero entry cap becomes 3416875788',
          mainram_changed_bytes=0,dtcm_changed_bytes=0,save_changed_bytes=0,logical_save_requests=0,flash_commits=0,
          forbidden_next=dict(pc='0x020019B8',opcode='0xE2100902',effect='ANDS at conditional +67 cycles reaches retained first-write cap, permitting scheduler return before next PC guard')),
  polling=dict(program_local_bound=None,mode1_delay_system_cycles=34,deadline_arm9_distance='67 for odd pre-write cycle; 68 for even; cycle cost is committed after write',guaranteed_poll_iteration_bound=None,
               conditional_completion_quotient=[0,1],conditional_completion_remainder=[0,0],single_read='8001 only under stated no-event guards',single_iteration='Not approved; ANDS reaches retained slice cap under candidate timing'),
  safety=dict(guest_dispatches=0,runtime_mmio_accesses=0,guest_image_writes=0,event_service_calls=0,AW_started=False,input_hashes_unchanged=True),
  limitations=['Astra Medium fresh-thread setting could not be selected; current thread used',
              'No exact AU divider operands/result/remainder/deadline or live cap captured',
              'Conditional timing prerequisites not established as facts of AU',
              'No runtime instrumentation installed; fail-closed AW gates remain to be implemented/reviewed',
              'No hardware timing parity, compiled parity, gameplay attribution or whole-call termination claim'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');args=p.parse_args()
 result=analyze()
 if args.export:(ROOT/'docs/BrainAge_TaskAV_Result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print('PASS AV file-only provenance, AU evidence, ROM words/literals, source order and conditional arithmetic; classification '+result['classification'])
