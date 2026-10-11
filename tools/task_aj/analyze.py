"""AJ static proof certificate. Reads immutable evidence; never invokes guest code.
Only --export writes, restricted to the two AJ reports. No emulation/replay.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path
import capstone

ROOT = Path(__file__).resolve().parents[2]
AI = '5e086cb667a87d41eda1aec016e6418a57f64356'
AH = '2b846d5ddeb751c59f02caa1aacd227d016a9b24'
AF = '63ff0c59f995fe9e2df57248ef261d1f4c8c6819'
BASELINE = '3a57236bb23d25dcb4caad7d58d733311062ff5e'
SHA1 = 'b8a105bacc3234dede8d4465df0869f2b922a0e2'
def hx(v): return f'0x{v:08X}'
def sha(b): return hashlib.sha256(b).hexdigest()
def word(b, offset): return struct.unpack_from('<I', b, offset)[0]
def git(*args, cwd=ROOT): return subprocess.check_output(['git', *args], cwd=cwd)
def target(pc, op):
    n = op & 0xffffff
    return (pc + 8 + ((n - 0x1000000 if n & 0x800000 else n) << 2)) & 0xffffffff

# Exact-path proof obligations: explicit instruction facts and arithmetic effects.
# This is a static certificate, not an instruction executor or guest runner.
ROWS = [
(0x02026254,0xEBFFFF47,'call','LR=02026258; SP unchanged; target 02025F78'),
(0x02025F78,0xE92D41F0,'stack write','PUSH r4-r8,LR; SP 027E3B2C -> 027E3B14; six words'),
(0x02025F7C,0xE24DD008,'register','SP 027E3B14 -> 027E3B0C; reserve 8 bytes, no write'),
(0x02025F80,0xE1A07000,'register','r7=r0=020E9A00'),
(0x02025F84,0xE5971040,'object read','[020E9A40]=1 -> r1'),
(0x02025F88,0xE597001C,'object read','[020E9A1C]=0 -> r0'),
(0x02025F8C,0xE2415001,'register','r5=1-1=0; flags unchanged'),
(0x02025F90,0xE3500000,'flags','CMP 0,0 -> NZCV 0/1/1/0'),
(0x02025F94,0xE5976034,'object read','[020E9A34]=DA -> r6; flags unchanged'),
(0x02025F98,0x0A00000C,'branch','EQ true (Z=1); taken 02025FD0'),
(0x02025FD0,0xE5971040,'object read','[020E9A40]=1 -> r1'),
(0x02025FD4,0xE597003C,'object read','[020E9A3C]=20 decimal -> r0'),
(0x02025FD8,0xE1510000,'flags','CMP 1,20 -> NZCV 1/0/0/0'),
(0x02025FDC,0xAA000019,'branch','GE false (N!=V); not taken 02026048; next 02025FE0'),
(0x02025FE0,0xE0871101,'register','r1=020E9A00+(1<<2)=020E9A04'),
(0x02025FE4,0xE5910054,'object read','[020E9A04+54]=[020E9A58]=11 decimal -> r0'),
(0x02025FE8,0xE3500009,'flags','CMP 11,9 -> NZCV 0/0/1/0'),
(0x02025FEC,0xCA000002,'branch','GT true (Z=0,N=V); taken 02025FFC'),
(0x02025FFC,0xE3A01000,'register','r1=0'),
(0x02026000,0xE1A02001,'register','r2=r1=0'),
(0x02026004,0xE2870E57,'register','r0=020E9A00+570=020E9F70'),
(0x02026008,0xE3A0301F,'register','r3=1F'),
(0x0202600C,0xEB0106F0,'call','target 02067BD4; LR=02026010; SP=027E3B0C'),
(0x02067BD4,0xE92D4010,'stack write','PUSH r4,LR; SP 027E3B0C -> 027E3B04; two words'),
(0x02067BD8,0xE1A04000,'register','r4=r0=020E9F70'),
(0x02067BDC,0xE5842254,'FORBIDDEN object write','STR r2=0 to [r4+254]=020EA1C4; before=1; STOP BEFORE DISPATCH'),
]

def analyze():
    assert git('branch','--show-current').decode().strip() == 'codex/brainage'
    assert git('rev-parse','HEAD',cwd=ROOT/'local/ndsrecomp').decode().strip() == BASELINE
    tracked=[]
    for commit,tag,report in [(AI,'ai','InnerCallBoundary'),(AH,'ah','IdempotentObjectStore'),(AF,'af','PhaseDispatchMap')]:
        names=[f'docs/BrainAge_Task{tag.upper()}_{report}.md',f'docs/BrainAge_Task{tag.upper()}_Result.json']
        names += git('ls-tree','-r','--name-only',commit,f'tools/task_{tag}/').decode().splitlines()
        for name in names:
            p=ROOT/name
            assert git('show',commit+':'+name).decode().splitlines()==p.read_text().splitlines(),name
            tracked.append(p)
    ai=json.loads((ROOT/'docs/BrainAge_TaskAI_Result.json').read_text())
    af=json.loads((ROOT/'docs/BrainAge_TaskAF_Result.json').read_text())
    session=ROOT/'local/task-ai/session-001'
    rompath=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
    paths=tracked+[rompath]+[p for p in session.iterdir() if p.is_file()]
    paths += [ROOT/'local/task-g/session-001/11-answer-01-63'/n for n in ['checkpoint.state','after.sav']]
    before={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
    rom=rompath.read_bytes(); ram=(session/'decision-after-mainram.bin').read_bytes(); dtcm=(session/'decision-after-dtcm.bin').read_bytes()
    assert hashlib.sha1(rom).hexdigest()==SHA1
    assert len(ram)==0x400000 and len(dtcm)==0x4000
    assert sha(ram)==ai['memory']['mainram_after_sha256'] and sha(dtcm)==ai['memory']['dtcm_after_sha256']
    assert sha((session/'decision-after.sav').read_bytes())==ai['save']['after_sha256']
    assert sha(paths[-2].read_bytes())==ai['source_checkpoint_sha256']
    assert sha(paths[-1].read_bytes())==ai['save']['after_sha256']
    start=[0x020E9A00,1,4,0,0x020E9A00,0,0x72,0,0x020E9A00,0,0,0,0,0x027E3B2C,0x02026B94,0x02026254]
    assert ai['ai_stop']['r']==start
    assert [ai['ai_stop'][k] for k in ['n','z','c','v','t','mode','i','f']]==[1,0,0,0,0,31,0,0]
    audit=[json.loads(s) for s in (session/'audit.jsonl').read_text().splitlines()]
    assert [r for r in audit if r['event']=='decision_step'][-1]==ai['ai_stop']
    fields=ai['memory']['mapped_fields']
    for f in fields:
        off=int(f['address'],16)-0x02000000
        assert int.from_bytes(ram[off:off+f['width']],'little')==f['before']==f['after']
    assert [word(ram,0xE9A00+o) for o in [0x40,0x1c,0x34,0x3c,0x58,0x7c4]]==[1,0,218,20,11,1]
    offset,_,base,length=struct.unpack_from('<4I',rom,0x20)
    decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
    facts=[]
    for pc,op,cls,effect in ROWS+[(0x02026258,0xE5940004,'caller','LDR r0,[r4,#4] after hypothetical return'),(0x0202625C,0xE3500000,'caller','CMP r0,#0; returned r0 overwritten')]:
        assert base<=pc<base+length
        assert word(rom,offset+pc-base)==word(ram,pc-0x02000000)==op,hx(pc)
        insn=next(decoder.disasm(struct.pack('<I',op),pc))
        facts.append(dict(pc=hx(pc),opcode=hx(op),decoded=insn.mnemonic+' '+insn.op_str,classification=cls,effect=effect))
    for pc,op,dest in [(0x02026254,0xEBFFFF47,0x02025F78),(0x02025F98,0x0A00000C,0x02025FD0),(0x02025FDC,0xAA000019,0x02026048),(0x02025FEC,0xCA000002,0x02025FFC),(0x0202600C,0xEB0106F0,0x02067BD4)]:
        assert target(pc,op)==dest
    # Static control-flow completeness: every successor is accounted for.
    taken = {0x02026254,0x02025F98,0x02025FEC,0x0202600C}
    assert len(ROWS)-1 == 25
    for row, successor in zip(ROWS, ROWS[1:]):
        pc, op = row[:2]
        assert successor[0] == (target(pc,op) if pc in taken else pc+4)
    def cmp_flags(a,b):
        d=(a-b)&0xffffffff
        return [d>>31,int(d==0),int(a>=b),int(bool((a^b)&(a^d)&0x80000000))]
    zero=word(ram,0xE9A1C); index=word(ram,0xE9A40)
    bound=word(ram,0xE9A3C); element=word(ram,0xE9A54+4*index)
    assert cmp_flags(zero,0)==[0,1,1,0]
    assert cmp_flags(index,bound)==[1,0,0,0]
    assert cmp_flags(element,9)==[0,0,1,0]
    assert zero==0 and not index>=bound and element>9
    assert word(dtcm,0x3B0C)==0x020E9A00 and word(dtcm,0x3B10)==0x02025830
    assert 0x020E9A00+(1<<2)+0x54==0x020E9A58
    assert 0x020E9A00+0x570+0x254==0x020EA1C4
    assert 0x027E3B2C-6*4-8-2*4==0x027E3B04
    writes=[]
    for pc,address,values,sources in [(0x02025F78,0x027E3B14,[start[i] for i in range(4,9)]+[0x02026258],['r4','r5','r6','r7','r8','lr']), (0x02067BD4,0x027E3B04,[start[4],0x02026010],['r4','lr'])]:
        for i,(value,source) in enumerate(zip(values,sources)):
            a=address+4*i; old=word(dtcm,a-0x027E0000)
            writes.append(dict(pc=hx(pc),address=hx(a),end_inclusive=hx(a+3),width=4,source=source,before=hx(old),after=hx(value),changed_bytes=sum(x!=y for x,y in zip(struct.pack('<I',old),struct.pack('<I',value)))))
    # A derived byte projection for diff/hash arithmetic only; never written as a dump.
    projection=bytearray(dtcm)
    for w in writes: struct.pack_into('<I',projection,int(w['address'],16)-0x027E0000,int(w['after'],16))
    changes=[dict(address=hx(0x027E0000+i),before=a,after=b) for i,(a,b) in enumerate(zip(dtcm,projection)) if a!=b]
    final=[0x020E9F70,0,0,0x1F,0x020E9F70,0,0xDA,0x020E9A00,0x020E9A00,0,0,0,0,0x027E3B04,0x02026010,0x02067BDC]
    nested=af['inner_call_prefix']
    assert nested['nested_call']['arguments']==final[:4]
    assert nested['first_nested_object_store']['address']=='0x020EA1C4'
    assert nested['first_nested_object_store']['before']==1 and nested['first_nested_object_store']['predicted_after']==0
    afwords={f['pc']:f['opcode'] for f in af['instruction_facts']}
    assert all(afwords[f['pc']]==f['opcode'] for f in facts[:26])
    assert before=={str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in paths}
    return dict(task='AJ - read-only exact inner-helper map',classification='FULL PASS',authoritative_ai_commit=AI,authoritative_ah_commit=AH,authoritative_af_commit=AF,branch='codex/brainage',rom_sha1=SHA1,framework_baseline=BASELINE,evidence_tier='Static ROM and retained hashed AI forced Tier-3 evidence; no AJ dynamic execution or compiled parity',entry=dict(r=[hx(x) for x in start],nzcv=[1,0,0,0],t=0,mode=31,i=0,f=0,opcode='0xEBFFFF47',target='0x02025F78',new_lr='0x02026258',argument_use='r0 object pointer consumed; incoming r1-r3 overwritten before read on this exact prefix; r12=0 incidental; no incoming stack arguments read'),instruction_facts=facts,stack_writes=writes,first_object_mutation=dict(pc='0x02067BDC',opcode='0xE5842254',address='0x020EA1C4',exercise_offset='0x7C4',width=4,source='r2',before=1,after=0,classification='unknown subobject field',executed=False),af_claim_verified=True,first_divergence=None,nested_call=dict(pc='0x0202600C',opcode='0xEB0106F0',target='0x02067BD4',arguments=[hx(v) for v in final[:4]],sp='0x027E3B0C',lr_before='0x02026258',lr_after='0x02026010',bounded_prefix_instructions=2),ak=dict(start_pc='0x02026254',stop_pc='0x02067BDC',stop_before='store dispatch',dispatch_count=25,terminal_observation_index=25,predicted_arm9_ordinal=ai['ai_stop']['insn9']+25,r=[hx(v) for v in final],nzcv=[0,0,1,0],t=0,mode=31,i=0,f=0,stack_word_writes=8,stack_written_bytes=32,dtcm_changed_bytes=len(changes),dtcm_byte_changes=changes,predicted_dtcm_sha256=sha(projection),mainram_changed_bytes=0,mainram_sha256=sha(ram),mapped_fields=fields,save_changed_bytes=0,logical_save_requests=0,flash_commits=0,object_global_writes=0,mmio_accesses=0,local_unwritten_range=['0x027E3B0C','0x027E3B13']),safety=dict(guest_dispatches=0,pending_BL_executed=False,ak_started=False,guest_state_writes=0,input_hashes_unchanged=True),input_sha256=before,limitations=['Exact AI context only; no full callee return or continuation proof','No runtime guards, scheduling or cycle prediction tested in AJ','Unknown fields retain offset-based descriptions'])

def report(r):
    text=f'''# Task AJ - exact inner-helper static map

**FULL PASS.** Static analysis only; zero guest instructions dispatched. AF's first-change claim is verified with no divergence. Recommend a separately authorized AK prefix of **25 instructions**, starting **0x02026254** and stopping **before 0x02067BDC**. AK has not begun.

[Result JSON](BrainAge_TaskAJ_Result.json) and [read-only verifier](../tools/task_aj/analyze.py).

## Provenance and ABI

Authoritative AI `{AI}`, AH `{AH}`, AF `{AF}`; branch `codex/brainage`. Initial HEAD was AI. ROM SHA-1 `{SHA1}`; ndsrecomp baseline `{BASELINE}`. Committed reports/helpers match those commits. ROM instruction words also match retained AI main RAM. AI CPU is cross-checked against its retained audit log; complete RAM/DTCM/save and source checkpoint hashes match. All inspected input hashes are unchanged after analysis. Unrelated `jarvis-inbox-v1.zip` is preserved.

AI pre-call r0-r12 (hex): `020E9A00, 1, 4, 0, 020E9A00, 0, 72, 0, 020E9A00, 0, 0, 0, 0`. SP=`027E3B2C`, LR=`02026B94`, PC=`02026254`; NZCV=`1/0/0/0`, T=0, System mode=31, I=F=0.

`02026254 / EBFFFF47 / BL 02025F78` creates LR=`02026258`, changes PC to `02025F78`, and leaves SP, flags and r0-r12 unchanged. r0 is the exercise pointer consumed by MOV r7,r0. Incoming r1/r2/r3 are incidental on this exact prefix: each is overwritten before use. No stack argument is read. This is a machine-level ABI observation, not a recovered source signature or whole-function liveness claim. r12=0 is untouched. Saved LR=02026B94 remains in the existing caller frame at 027E3B30; BL itself performs no stack write.

Immediately after a hypothetical return: `02026258 / E5940004 / LDR r0,[r4,#4]`, then `0202625C / E3500000 / CMP r0,#0`. Thus returned r0 is overwritten before comparison; the caller expects preserved r4. The remainder and actual return are outside this proof.

## Exact path

Every listed instruction is AL except the three named conditional branches. Unlisted registers and flags are unchanged; PC advances by four except at taken branches/calls. LR changes only at the two BLs; SP changes only at the two PUSHes and SUB. All object loads are aligned 32-bit ordinary main-RAM reads. No unknown access or MMIO occurs.

| Index | PC / opcode | Decode | Class and exact effect |
|---|---|---|---|
'''
    for i,f in enumerate(r['instruction_facts'][:26]): text+=f"| {i} | {f['pc']} / {f['opcode']} | {f['decoded']} | {f['classification']}: {f['effect']} |\n"
    text+='''
+40=1 selects index 1 and r5=0; +1C=0 takes BEQ, skipping the nonzero arm entirely. +34=DA is loaded into r6. Signed 1<20 from +40/+3C rejects BGE. The indexed load is +54+4*1=+58=11; signed 11>9 takes BGT. All three predicates and branch immediates were checked independently of AF. No earlier nested call or object/global store lies on this selected path.

## Write and call firewall

The first PUSH writes six words at 027E3B14..027E3B2B. SUB reserves 027E3B0C..027E3B13 without writing it; its retained words remain 020E9A00 and 02025830. The nested PUSH writes two words at 027E3B04..027E3B0B. All lie below AI SP, in released ordinary DTCM stack storage, newly allocated as saved-register frames/local scratch. Existing active caller storage at/above 027E3B2C is untouched. No red-zone or incoming stack data is read by this prefix.

| Write PC | DTCM word address | Source | AI before | Predicted after | Changed bytes |
|---|---|---|---|---|---|
'''
    for w in r['stack_writes']: text+=f"| {w['pc']} | {w['address']} | {w['source']} | {w['before']} | {w['after']} | {w['changed_bytes']} |\n"
    text+=f'''
These are 8 architectural word writes / 32 written bytes, with **{r['ak']['dtcm_changed_bytes']} changed bytes**, not 32 changed bytes. The JSON records every differing byte and predicted DTCM SHA-256 `{r['ak']['predicted_dtcm_sha256']}`. All eight saved words change value; no object/global write, even idempotent, precedes the stop. AH's earlier +34 store is outside the AK-only extension.

At `0202600C / EB0106F0`, the first nested BL targets `02067BD4`, with r0-r3=`020E9F70 / 0 / 0 / 1F`; SP=`027E3B0C`, incoming LR=`02026258`, outgoing LR=`02026010`. Its bounded prefix is exactly `02067BD4 / E92D4010 PUSH {{r4,lr}}` and `02067BD8 / E1A04000 MOV r4,r0`. Saved r4 is still `020E9A00` at the PUSH. Both calls are statically bounded to this stop; neither full body is claimed safe.

First object/global mutation: **02067BDC / E5842254 / STR r2,[r4,#0x254]**, AL, word, positive immediate, no writeback. r4=`020E9F70`; effective address=`020EA1C4`=exercise+7C4; source r2=0; retained before=1, predicted after=0 (one byte differs). Its semantic role remains unknown. AF's path, arguments, prefix opcodes, address and 1->0 claim are all verified. This store was decoded but never dispatched.

## Fail-closed AK recommendation

Start at the exact AI pre-dispatch stop **02026254**. Permit exactly the ordered 25-instruction prefix at indices 0..24 above, including both BLs and the condition-failed BGE as a dispatched instruction. Observation 25 is terminal-only at **02067BDC**, before fetch/dispatch, bank handoff or instruction increment. Expected ARM9 ordinal is **{r['ak']['predicted_arm9_ordinal']}** (+25); no cycle estimate is made.

Expected terminal r0-r12 (hex): `020E9F70, 0, 0, 1F, 020E9F70, 0, DA, 020E9A00, 020E9A00, 0, 0, 0, 0`. SP=`027E3B04`, LR=`02026010`, PC=`02067BDC`; NZCV=`0/0/1/0`; T=0, System mode=31, I=F=0. No full return is allowed.

Require exact AI CPU, complete RAM/DTCM/save hashes, ROM identity, instruction words, ordinal and all mapped field values before arming. Check the ordered PC/opcode/register/flag path; reject wrong/repeated/skipped entries before dispatch. Permit only the eight listed DTCM word stores with exact PC/address/width/value/order. Permit only instruction fetches and listed object reads; reject unknown/MMIO reads and any additional write. Stop before the STR regardless of operand equality; forbid all later instructions, full helper returns, gameplay continuation and save/Flash requests. Audit actual write events separately from byte diffs. These are requirements for future AK implementation, not guards implemented or dynamically tested by AJ.

Expected full main-RAM/object diff: **zero bytes**, hash `{r['ak']['mainram_sha256']}`. Expected save diff zero; logical requests/Flash commits zero. Only the listed DTCM bytes may differ. All mapped fields remain unchanged: +10=1, +1C=0, +20=1, +34=DA hex, +38=0, +3C=20, +40=1, +44=1, +4C=4, +58=11, +504=1, +50C=255, +514=4, +51C=255, +7C4=1 (other values decimal). This does not assign semantics to unknown fields. Specifically +7C4 remains 1 because its store is forbidden.

## Validation and limits

`python tools/task_aj/analyze.py --export` verifies and exports only these two ROM-free reports; omit `--export` for read-only checking. It uses explicit static instruction facts and arithmetic obligations, Capstone decoding, immutable retained images and an in-memory stack-byte projection for diff arithmetic. It never invokes an emulator, interpreter, replay, build, guest scheduler or pending call, and never writes a guest image. Each source input is hashed before/after. Individual opcode facts are analytical evidence, not a ROM/code-image artifact.

Evidence tier: static exact-ROM analysis anchored in retained forced Tier-3 original-interpreter AI evidence. No new dynamic evidence, compiled parity, full-routine safety, scheduler or cycle claim. Prediction is conditional on the exact AI state and a future fail-closed runtime gate. Initial sandbox process setup failed; approved escalated file-access commands succeeded. No authoritative input or runtime source was changed.

**Stopped after AJ. Pending BL not executed; AK not started.**
'''
    return text

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');args=p.parse_args()
    result=analyze()
    if args.export:
        (ROOT/'docs/BrainAge_TaskAJ_Result.json').write_text(json.dumps(result,indent=2)+'\n')
        (ROOT/'docs/BrainAge_TaskAJ_InnerHelperStaticMap.md').write_text(report(result))
    print(json.dumps(dict(classification=result['classification'],guest_dispatches=0,ak_dispatch_count=25,dtcm_changed_bytes=result['ak']['dtcm_changed_bytes'],ak_stop='0x02067BDC')))
