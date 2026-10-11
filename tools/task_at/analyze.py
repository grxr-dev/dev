"""Fixed Task AT proof annotations, not an ARM evaluator.
Reads ROM/evidence/source bytes; never imports or invokes guest/runtime code.
--export writes only the ROM-free JSON report. Run with python -B.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
import capstone

ROOT = Path(__file__).resolve().parents[2]
AS = '72c93f2eb0a561ff4b047d171e904477d8553e7b'
AR = '7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad'
BASE = '3a57236bb23d25dcb4caad7d58d733311062ff5e'
ROM_SHA1 = 'b8a105bacc3234dede8d4465df0869f2b922a0e2'
ENTRY = [0x1000,0x2132750,0,1,0x20ea1bc,0,0xda,0x20e9a00,
         0x1000,0x1000,0x20fd00c,0,0x48c,0x27e365c,0x2026048,0x2067564]
FINAL = [0x1000,0x4000280,0x4000290,1,0x20ea1bc,0,0xda,0x20e9a00,
         0x1000,0x1000,0x20fd00c,0,0x48c,0x27e3654,0x2001a20,0x2001980]
# Reviewed fixed changes. No opcode dispatch loop or bus implementation.
PREFIX = [
 (0x2067564,0xebfe692a,{14:0x2067568},'BL creates LR; enters wrapper'),
 (0x2001a14,0xe92d4000,{13:0x27e3658},'DTCM [027E3658] := LR=02067568'),
 (0x2001a18,0xe24dd004,{13:0x27e3654},'allocate 4 bytes; no initialization'),
 (0x2001a1c,0xebffffd4,{14:0x2001a20},'BL enters divider setup leaf'),
 (0x2001974,0xe59f1028,{1:0x4000280},'r1 := main-RAM literal [020019A4]'),
 (0x2001978,0xe3a03001,{3:1},'r3 := 1 (idempotent register assignment)'),
 (0x200197c,0xe59f2024,{2:0x4000290},'r2 := main-RAM literal [020019A8]'),
]
WORDS = {
 0x2001980:0xe1c130b0,0x2001984:0xe3a0c000,0x2001988:0xe582c000,
 0x200198c:0xe3a03a01,0x2001990:0xe59f1014,0x2001994:0xe5823004,
 0x2001998:0xe5810000,0x200199c:0xe581c004,0x20019a0:0xe12fff1e,
 0x2001a20:0xebffffe2,0x20019b0:0xe59f102c,0x20019b4:0xe1d100b0,
 0x20019b8:0xe2100902,0x20019bc:0x1afffffc,0x20019c0:0xe59f1020,
 0x20019c4:0xe3a00702,0x20019c8:0xe5912000,0x20019cc:0xe5911004,
 0x20019d0:0xe0920000,0x20019d4:0xe2a11000,0x20019d8:0xe1a00a20,
 0x20019dc:0xe1800601,0x20019e0:0xe12fff1e,0x2001a24:0xe28dd004,
 0x2001a28:0xe8bd8000,
}
LITERALS = {0x20019a4:0x4000280,0x20019a8:0x4000290,0x20019ac:0x4000298,
            0x20019e4:0x4000280,0x20019e8:0x40002a0}
MMIO = [
 (0x2001980,0x4000280,2,'write',1,'r3 := 1 at 02001978','DIVCNT'),
 (0x2001988,0x4000290,4,'write',0,'r12 := 0 at 02001984','DIV_NUMER low'),
 (0x2001994,0x4000294,4,'write',0x1000,'r3 := 1000 at 0200198C','DIV_NUMER high'),
 (0x2001998,0x4000298,4,'write',0x1000,'r0 preserved from AS','DIV_DENOM low'),
 (0x200199c,0x400029c,4,'write',0,'r12 remains 0','DIV_DENOM high'),
 (0x20019b4,0x4000280,2,'read',None,'r1 := literal [020019E4]; r0 receives status','DIVCNT'),
 (0x20019c8,0x40002a0,4,'read',None,'r1 := literal [020019E8]; r2 receives quotient low','DIV_RESULT low'),
 (0x20019cc,0x40002a4,4,'read',None,'old r1 + 4; r1 receives quotient high','DIV_RESULT high'),
]
def hx(v): return f'0x{v:08X}'
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def word(b,o): return struct.unpack_from('<I',b,o)[0]
def git(*args,cwd=ROOT): return subprocess.check_output(['git',*args],cwd=cwd)
def target(pc,op):
    imm=op&0xffffff
    return pc+8+4*(imm-0x1000000 if imm&0x800000 else imm)
def function(text,signature):
    start=text.index(signature)
    end=text.index('\n}',start)+2
    return text[start:end]

def analyze():
    assert git('branch','--show-current').decode().strip()=='codex/brainage'
    framework=ROOT/'local/ndsrecomp'
    assert git('rev-parse','HEAD',cwd=framework).decode().strip()==BASE
    paths=[]
    for commit,tag,title in [(AS,'AS','Dynamic6753CEntryBoundary'),(AR,'AR','Pending6753CStaticMap')]:
        git('merge-base','--is-ancestor',commit,'HEAD')
        names=[f'docs/BrainAge_Task{tag}_{title}.md',f'docs/BrainAge_Task{tag}_Result.json']
        names+=git('ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/').decode().splitlines()
        for name in names:
            p=ROOT/name
            assert git('show',commit+':'+name).decode('utf-8-sig').splitlines()==p.read_text(encoding='utf-8-sig').splitlines(),name
            paths.append(p)
    a=load(ROOT/'docs/BrainAge_TaskAS_Result.json')
    ar=load(ROOT/'docs/BrainAge_TaskAR_Result.json')
    assert load(ROOT/'tools/task_as/expected.json')==ar
    session=ROOT/a['authoritative_path']
    rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
    source_names=['io.cpp','bus.cpp','tier3.cpp','runtime_arm.cpp','scheduler.cpp']
    paths += [rompath]+sorted(p for p in session.iterdir() if p.is_file())
    paths += [framework/'runner/src'/n for n in source_names]
    before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
    rom=rompath.read_bytes()
    ram=(session/'decision-after-mainram.bin').read_bytes()
    dt=(session/'decision-after-dtcm.bin').read_bytes()
    save=(session/'decision-after.sav').read_bytes()
    assert hashlib.sha1(rom).hexdigest()==ROM_SHA1==a['rom_sha1']
    assert len(ram)==0x400000 and len(dt)==0x4000
    hashes=dict(mainram=sha(ram),dtcm=sha(dt),save=sha(save))
    assert hashes==dict(mainram=a['memory']['mainram_after_sha256'],dtcm=a['memory']['dtcm_after_sha256'],save=a['save']['after_sha256'])
    assert hashes==dict(mainram='84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340',
                       dtcm='48b89027a274b3268219cdc6a8cd1f7fe15bf442a78b3931d79c4e6ae3ea36e4',
                       save='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb')
    audit=[json.loads(l) for l in (session/'audit.jsonl').read_text().splitlines()]
    steps=[v for v in audit if v['event']=='as_step']
    reads=[v for v in audit if v['event']=='as_read_event']
    writes=[v for v in audit if v['event']=='as_write_event']
    assert steps==a['instruction_observations'] and len(steps)==12
    assert steps[-1]==a['as_stop'] and steps[-1]['r']==ENTRY
    assert [steps[-1][k] for k in ['pc','opcode','n','z','c','v','t','mode','i','f','insn9']]==[ENTRY[15],0xebfe692a,0,0,0,0,0,31,0,0,281098001]
    assert reads==a['bus_reads'] and len(reads)==16
    assert writes==[w['actual_event'] for w in a['architectural_stores']] and len(writes)==10
    assert [v for v in audit if v['event']=='decision_stopped']==[dict(event='decision_stopped',as_instructions=11,as_writes=10,as_reads=16,successor_fetched=False,successor_dispatched=False)]
    assert not any(v['pc']==ENTRY[15] for v in reads)
    for i,s in enumerate(steps):
        regs=ar['instructions'][i]['r_before'] if i<11 else ar['AS']['r']
        assert s['r']==[int(x,16) for x in regs]
        assert [s[k] for k in ['n','z','c','v','t','mode','i','f','insn9']]==[0,0,0,0,0,31,0,0,281097990+i]
    expected_reads=[]
    for i,f in enumerate(ar['instructions']):
        expected_reads.append(dict(event='as_read_event',index=i,pc=int(f['pc'],16),address=int(f['pc'],16),width=4,value=int(f['opcode'],16)))
        for rd in f.get('data_reads',[]):
            expected_reads.append(dict(event='as_read_event',index=i,pc=int(rd['pc'],16),address=int(rd['address'],16),width=4,value=int(rd['value'],16)))
    assert reads==expected_reads
    db=(session/'as-before-dtcm.bin').read_bytes()
    assert sha(db)==ar['entry_hashes']['dtcm']
    assert ram==(session/'as-before-mainram.bin').read_bytes()
    actual_diff=[dict(address=hx(0x27e0000+i),before=b,after=e) for i,(b,e) in enumerate(zip(db,dt)) if b!=e]
    assert actual_diff==a['memory']['dtcm_byte_changes']==ar['AS']['dtcm_byte_diffs']
    for w,q in zip(writes,ar['stores']):
        addr=int(q['address'],16)
        assert (w['pc'],w['address'],w['width'],w['before'],w['after'])==(int(q['pc'],16),addr,4,int(q['before'],16),int(q['after'],16))
        assert word(db,addr-0x27e0000)==w['before'] and word(dt,addr-0x27e0000)==w['after']
    assert len(a['memory']['mapped_fields'])==35
    for f in a['memory']['mapped_fields']:
        off=int(f['address'],16)-0x2000000
        assert int.from_bytes(ram[off:off+f['width']],'little')==f['before']==f['after']
    for name in ['as-before.sav','initial.sav','session.sav','final.sav']:
        assert (session/name).read_bytes()==save
    assert all((session/n).stat().st_size==0 for n in ['requests.jsonl','flash.jsonl'])
    assert a['state_effects']['MMIO_accesses']==0 and not any(v.get('save_dirty',False) for v in audit)
    assert load(session/'session.json')['pass']
    off,_,base,size=struct.unpack_from('<4I',rom,32)
    dec=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
    def fact(pc,op):
        assert base<=pc<base+size and pc%4==0
        assert word(rom,off+pc-base)==word(ram,pc-0x2000000)==op,(hx(pc),hx(op))
        ins=next(dec.disasm(struct.pack('<I',op),pc))
        return dict(pc=hx(pc),opcode=hx(op),decode=ins.mnemonic+' '+ins.op_str,
                    fetch_space='main RAM; ROM-backed ARM9 code',predicate='NE' if op>>28==1 else 'AL')
    facts=[fact(pc,op) for pc,op in WORDS.items()]
    for addr,value in LITERALS.items():
        assert word(rom,off+addr-base)==word(ram,addr-0x2000000)==value
    assert target(0x2001a20,WORDS[0x2001a20])==0x20019b0
    assert target(0x20019bc,WORDS[0x20019bc])==0x20019b4
    regs=ENTRY.copy()
    prefix=[]
    for i,(pc,op,changes,effect) in enumerate(PREFIX):
        assert regs[15]==pc and op>>28==14
        f=fact(pc,op)
        f.update(index=i,r_before=list(map(hx,regs)),nzcv_before=[0]*4,effect=effect)
        nextpc=PREFIX[i+1][0] if i<6 else 0x2001980
        if i in (0,3):
            assert op>>24==0xeb and target(pc,op)==nextpc and changes=={14:pc+4}
        else:
            assert nextpc==pc+4
        if i==1:
            assert op==0xe92d4000 and changes=={13:regs[13]-4}
        elif i==2:
            assert changes=={13:regs[13]-4}
        elif i in (4,6):
            dest=(op>>12)&15
            addr=pc+8+(op&0xfff)
            assert changes=={dest:LITERALS[addr]}
            f['data_read']=dict(address=hx(addr),width=4,value=hx(LITERALS[addr]),space='main RAM literal')
        elif i==5:
            assert changes=={3:1}
        for k,v in changes.items(): regs[k]=v
        regs[15]=nextpc
        f.update(r_after=list(map(hx,regs)),nzcv_after=[0]*4)
        prefix.append(f)
    assert regs==FINAL
    old=word(dt,0x3658)
    assert old==0x2067ae0
    new=0x2067568
    diffs=[dict(address=hx(0x27e3658+i),before=b,after=e)
           for i,(b,e) in enumerate(zip(old.to_bytes(4,'little'),new.to_bytes(4,'little'))) if b!=e]
    predicted_dt=dt[:0x3658]+new.to_bytes(4,'little')+dt[0x365c:]
    # Static operands for all five excluded writes and all three read sites.
    mmio=[]
    for pc,addr,width,kind,value,derivation,identity in MMIO:
        op=WORDS[pc]
        mmio.append(dict(pc=hx(pc),opcode=hx(op),address=hx(addr),width=width,
                         direction=kind,value=None if value is None else hx(value),
                         derivation=derivation,identity=identity,space='MMIO',
                         allowed_in_AU=False))
    assert [(q[0],q[1],q[2],q[3],q[4]) for q in MMIO]==[
      (0x2001980,0x4000280,2,'write',1),(0x2001988,0x4000290,4,'write',0),
      (0x2001994,0x4000294,4,'write',0x1000),(0x2001998,0x4000298,4,'write',0x1000),
      (0x200199c,0x400029c,4,'write',0),(0x20019b4,0x4000280,2,'read',None),
      (0x20019c8,0x40002a0,4,'read',None),(0x20019cc,0x40002a4,4,'read',None)]
    # Prove register identities/side effects from local source without calling it.
    io=(framework/'runner/src/io.cpp').read_text(encoding='utf-8')
    pinned=git('show',BASE+':runner/src/io.cpp',cwd=framework).decode()
    signatures=['uint64_t active_system_timestamp()', 'void start_div()', 'void finish_div()',
                'uint32_t math_reg_read32(', 'bool math_addr(', 'void math_reg_write(',
                'uint64_t nds_next_system_event_time()', 'void nds_run_system_events(',
                'uint32_t nds_io_read(', 'void nds_io_write(']
    verified=[]
    for sig in signatures:
        local=function(io,sig)
        assert local==function(pinned,sig),sig
        verified.append(dict(signature=sig,line=io[:io.index(sig)].count('\n')+1,
                             sha256=sha(local.encode()),matches_pinned_baseline=True))
    assert '((g_divcnt & 0x3u) == 0u ? 18u : 34u)' in function(io,'void start_div()')
    assert 'finish_div();' in function(io,'void nds_run_system_events(')
    assert 'finish_div' not in function(io,'uint32_t math_reg_read32(')
    assert 'g_divcnt &= ~0xC000u;' in function(io,'void finish_div()')
    assert (0x1000<<32)//0x1000==0x100000000
    assert ((0x100000000+0x80000)>>20)==0x1000
    conditional_final=[0x1000,1,0,0x1000,*ENTRY[4:12],0,ENTRY[13],0x2001a24,0x2067568]
    assert len(conditional_final)==16
    assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
    return dict(
      task='AT',classification='FULL PASS',authoritative_AS_commit=AS,authoritative_AR_commit=AR,
      branch='codex/brainage',rom_sha1=ROM_SHA1,framework_baseline=BASE,
      evidence_tier='Exact-ROM static proof anchored in committed forced Tier-3 AS original-ARM evidence; no compiled parity',
      entry=a['as_stop'],entry_hashes=hashes,AS_revalidation=dict(observations=12,reads=16,writes=10,mapped_fields=35,terminal_not_fetched=True),
      call=dict(pc=hx(ENTRY[15]),opcode='0xEBFE692A',target='0x02001A14',r0_r3=list(map(hx,ENTRY[:4])),sp=hx(ENTRY[13]),lr_before=hx(ENTRY[14]),lr_created='0x02067568',frame_bytes=8,saved_lr_address='0x027E3658'),
      prefix=prefix,excluded_instructions=facts,literals={hx(k):hx(v) for k,v in LITERALS.items()},
      mmio=mmio,poll=dict(pc='0x020019B4',mask='0x00008000',ands_pc='0x020019B8',branch_pc='0x020019BC',repeat_if='Z=0, sampled DIVCNT bit15 set',exit_if='Z=1, bit15 clear',max_iterations=None,read_has_completion_side_effect=False),
      divider=dict(mode=1,numerator='0x0000100000000000',denominator='0x00001000',
                   final_quotient='0x0000000100000000',final_remainder=0,
                   completion='nds_run_system_events(timestamp) when g_div_deadline <= timestamp',
                   restart_delay_system_ticks=34,arm9_cycle_equivalent=68,
                   each_control_or_operand_write_restarts=True,requires_dma_irq_fifo_arm7=False,
                   initially_stale_operands_and_result_unobserved=True,
                   no_unconditional_poll_bound=True,source_functions=verified),
      conditional_return=dict(assumptions='All five stores complete; no intervening divider writer; timed final division completes; status/result reads coherent; saved LR intact',
                              r=list(map(hx,conditional_final)),nzcv=[0,0,0,0],sp='0x027E365C',
                              wrapper_return_pc='0x02067568',observed=False,mainram_writes=0,
                              dtcm_writes=1,mmio_write_count=5,mmio_read_count='k+2, k>=1'),
      AU=dict(start_pc='0x02067564',stop_pc='0x02001980',stop_before='fetch/accounting/dispatch of STRH r3,[r1]; first MMIO access',
              instruction_count=7,pc_sequence=[f['pc'] for f in prefix],r=list(map(hx,FINAL)),nzcv=[0]*4,t=0,mode=31,i=0,f=0,
              predicted_arm9_ordinal=281098008,cycle_prediction=None,
              data_reads=[f['data_read']|dict(pc=f['pc']) for f in prefix if 'data_read' in f],
              instruction_fetches=7,data_read_words=2,
              stores=[dict(pc='0x02001A14',opcode='0xE92D4000',address='0x027E3658',width=4,source='LR',before=hx(old),after=hx(new),space='DTCM stack',value_changing=True)],
              dtcm_byte_diffs=diffs,dtcm_after_sha256=sha(predicted_dt),dtcm_changed_bytes=len(diffs),
              mainram_changed_bytes=0,save_changed_bytes=0,mmio_accesses=0,logical_save_requests=0,flash_commits=0,
              mapped_fields=a['memory']['mapped_fields'],
              forbidden_next=dict(pc='0x02001980',opcode='0xE1C130B0',address='0x04000280',width=2,value=1,effect='starts/restarts timed division; sets BUSY and reschedules slice')),
      safety=dict(guest_dispatches=0,runtime_mmio_accesses=0,guest_image_writes=0,AU_started=False,input_hashes_unchanged=True),
      input_sha256=before,limitations=[
       'Astra Medium fresh-thread selection unavailable; current thread used, no claim of requested model execution',
       'No runtime guards implemented or AU started',
       'No exact AS divider peripheral state or first-write intermediate result certified',
       'No loop-count, cycle/scheduler or hardware timing parity claim',
       'Conditional return is static, not observed; whole enclosing 0206753C callee excluded'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    result=analyze()
    if args.export:
        (ROOT/'docs/BrainAge_TaskAT_Result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(classification=result['classification'],AU_count=7,AU_stop=result['AU']['stop_pc'],guest_dispatches=0)))
