"""Read-only AF evidence checks. Never launches a guest or writes input artifacts.

Without --export, only prints a summary. Export is restricted to the AF result.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import capstone

ROOT = Path(__file__).resolve().parents[2]
SHA1 = 'b8a105bacc3234dede8d4465df0869f2b922a0e2'
# Individual decoded instruction facts, not an executable ROM/code image.
FACTS = [
    (0x02026B90, 0xEBFFFDA0, 'BL 0x02026218'),
    (0x02026218, 0xE92D4010, 'PUSH {r4,lr}'),
    (0x0202621C, 0xE1A04000, 'MOV r4,r0'),
    (0x02026220, 0xE1D401F0, 'LDRSH r0,[r4,#0x10]'),
    (0x02026224, 0xE3500005, 'CMP r0,#5'),
    (0x02026228, 0x908FF100, 'ADDLS pc,pc,r0,LSL #2'),
    (0x02026234, 0xEA000003, 'B 0x02026248'),
    (0x02026248, 0xE3A000DA, 'MOV r0,#0xDA'),
    (0x0202624C, 0xE5840034, 'STR r0,[r4,#0x34]'),
    (0x02026250, 0xE1A00004, 'MOV r0,r4'),
    (0x02026254, 0xEBFFFF47, 'BL 0x02025F78'),
    (0x02025F78, 0xE92D41F0, 'PUSH {r4-r8,lr}'),
    (0x02025F7C, 0xE24DD008, 'SUB sp,sp,#8'),
    (0x02025F80, 0xE1A07000, 'MOV r7,r0'),
    (0x02025F84, 0xE5971040, 'LDR r1,[r7,#0x40]'),
    (0x02025F88, 0xE597001C, 'LDR r0,[r7,#0x1C]'),
    (0x02025F8C, 0xE2415001, 'SUB r5,r1,#1'),
    (0x02025F90, 0xE3500000, 'CMP r0,#0'),
    (0x02025F94, 0xE5976034, 'LDR r6,[r7,#0x34]'),
    (0x02025F98, 0x0A00000C, 'BEQ 0x02025FD0'),
    (0x02025FD0, 0xE5971040, 'LDR r1,[r7,#0x40]'),
    (0x02025FD4, 0xE597003C, 'LDR r0,[r7,#0x3C]'),
    (0x02025FD8, 0xE1510000, 'CMP r1,r0'),
    (0x02025FDC, 0xAA000019, 'BGE 0x02026048'),
    (0x02025FE0, 0xE0871101, 'ADD r1,r7,r1,LSL #2'),
    (0x02025FE4, 0xE5910054, 'LDR r0,[r1,#0x54]'),
    (0x02025FE8, 0xE3500009, 'CMP r0,#9'),
    (0x02025FEC, 0xCA000002, 'BGT 0x02025FFC'),
    (0x02025FFC, 0xE3A01000, 'MOV r1,#0'),
    (0x02026000, 0xE1A02001, 'MOV r2,r1'),
    (0x02026004, 0xE2870E57, 'ADD r0,r7,#0x570'),
    (0x02026008, 0xE3A0301F, 'MOV r3,#0x1F'),
    (0x0202600C, 0xEB0106F0, 'BL 0x02067BD4'),
    (0x02067BD4, 0xE92D4010, 'PUSH {r4,lr}'),
    (0x02067BD8, 0xE1A04000, 'MOV r4,r0'),
    (0x02067BDC, 0xE5842254, 'STR r2,[r4,#0x254]'),
    (0x02026B94, 0xE28DD00C, 'ADD sp,sp,#0xC'),
    (0x02026B98, 0xE8BD83F0, 'POP {r4-r9,pc}'),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def branch_target(pc, opcode):
    imm = opcode & 0xffffff
    if imm & 0x800000:
        imm -= 0x1000000
    return (pc + 8 + (imm << 2)) & 0xffffffff

def analyze():
    ae_path = ROOT / 'docs/BrainAge_TaskAE_Result.json'
    ae = json.loads(ae_path.read_text())
    rom_path = ROOT.parent / 'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds'
    session = ROOT / 'local/task-ae/session-001'
    inputs = [ae_path, rom_path, session / 'decision-after-mainram.bin',
              session / 'decision-after-dtcm.bin', session / 'decision-after.sav',
              ROOT / 'local/task-g/session-001/11-answer-01-63/checkpoint.state',
              ROOT / 'local/task-g/session-001/11-answer-01-63/after.sav']
    initial = {str(p.relative_to(ROOT.parent)): sha(p.read_bytes()) for p in inputs}
    rom = rom_path.read_bytes()
    assert hashlib.sha1(rom).hexdigest() == SHA1
    offset, _, base, length = struct.unpack_from('<4I', rom, 0x20)
    ram = inputs[2].read_bytes()
    dtcm = inputs[3].read_bytes()
    assert len(ram) == 0x400000 and len(dtcm) == 0x4000
    assert sha(ram) == ae['hashes']['immediate_mainram_after']
    assert sha(dtcm) == ae['hashes']['immediate_dtcm_after']
    assert sha(inputs[4].read_bytes()) == ae['save']['after_sha256']
    assert sha(inputs[5].read_bytes()) == ae['checkpoint_sha256']
    assert inputs[4].read_bytes() == inputs[6].read_bytes()
    stop = ae['safe_stop']
    expected = [0x020E9A00,1,4,0,3,0,0x72,0,0x020E9A00,0,0,0,0,0x027E3B34,0,0x02026B90]
    assert stop['r'] == expected and stop['pc'] == expected[15]
    assert [stop[k] for k in ('n','z','c','v','t','mode','i','f')] == [1,0,0,0,0,31,0,0]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = []
    for pc, opcode, description in FACTS:
        assert base <= pc < base + length
        word = struct.unpack_from('<I', rom, offset + pc - base)[0]
        assert word == opcode, hex(pc)
        assert struct.unpack_from('<I', ram, pc - 0x02000000)[0] == word
        insn = next(decoder.disasm(struct.pack('<I', word), pc))
        decoded.append(dict(pc=f'0x{pc:08X}', opcode=f'0x{word:08X}',
                            decoded=insn.mnemonic+' '+insn.op_str,
                            role='proposed AG prefix' if len(decoded)<8 else 'not proposed for AG'))
    assert branch_target(0x02026B90, 0xEBFFFDA0) == 0x02026218
    assert branch_target(0x02026234, 0xEA000003) == 0x02026248
    assert branch_target(0x02026254, 0xEBFFFF47) == 0x02025F78
    fields = []
    for off, fmt, name, expected_value in [(0x10,'h','phase',1),(0x20,'I','result_delay',1),
            (0x34,'I','unknown phase-one-assigned word',218),(0x44,'I','correct_count',1),
            (0x1C,'I','unknown zero-tested word',0),(0x3C,'I','unknown comparison bound',20),(0x40,'I','unknown index word',1),(0x58,'I','indexed +0x54 element',11),(0x4C,'I','expected',4),(0x504,'I','result_flag',1),(0x51C,'I','later_outcome',255)]:
        value = struct.unpack_from('<'+fmt, ram, 0xE9A00+off)[0]
        assert value == expected_value
        fields.append(dict(offset=f'0x{off:X}',address=f'0x{0x020E9A00+off:08X}',
                           width=struct.calcsize(fmt),name=name,value=value))
    phase = fields[0]['value']
    # CMP 1,5 -> N=1,Z=0,C=0,V=0. LS is C==0 or Z==1.
    assert phase == 1 and phase <= 5
    assert 0x02026228 + 8 + (phase << 2) == 0x02026234
    assert branch_target(0x02025F98,0x0A00000C)==0x02025FD0
    assert branch_target(0x02025FDC,0xAA000019)==0x02026048
    assert branch_target(0x02025FEC,0xCA000002)==0x02025FFC
    assert branch_target(0x0202600C,0xEB0106F0)==0x02067BD4
    nested_before=struct.unpack_from('<I',ram,0xE9A00+0x7C4)[0]
    stack = []
    for address, value, source in [(0x027E3B2C,3,'r4'),(0x027E3B30,0x02026B94,'lr')]:
        stack.append(dict(address=f'0x{address:08X}',width=4,source=source,
                          before=struct.unpack_from('<I',dtcm,address-0x027E0000)[0],
                          predicted_after=value))
    predicted = list(expected)
    predicted[0]=0xDA;predicted[4]=0x020E9A00;predicted[13]=0x027E3B2C
    predicted[14]=0x02026B94;predicted[15]=0x0202624C
    assert initial == {str(p.relative_to(ROOT.parent)):sha(p.read_bytes()) for p in inputs}
    return dict(task='AF - read-only phase dispatch map',classification='FULL PASS',
        authoritative_ae_commit='6a43d5bfa4c85773b0f986b9d73944ab5e01700e',
        repository_head_at_start='5a37a257d09344df7c992fb8ba9dee9abd6630c1',
        branch='codex/brainage',rom_sha1=SHA1,
        framework_baseline='3a57236bb23d25dcb4caad7d58d733311062ff5e',
        evidence_tier='Static exact-ROM + hashed forced Tier-3 AE evidence; no AF dynamic execution or compiled parity',
        ae_safe_stop=stop,callee_entry_r=[*expected[:14],0x02026B94,0x02026218],
        object=dict(address='0x020E9A00',role='previously audited exercise object',audited_size='0xC34'),
        fields=fields,instruction_facts=decoded,
        phase_dispatch=dict(pc='0x02026228',predicate='unsigned LS after CMP sign-extended halfword,5',
                    input=1,nzcv=[1,0,0,0],taken=True,target='0x02026234',
                    slot_branch_target='0x02026248'),
        first_memory_write=dict(pc='0x02026218',opcode='0xE92D4010',classification='stack scratch',
                                sp_before='0x027E3B34',sp_after='0x027E3B2C',words=stack),
        first_object_store=dict(pc='0x0202624C',opcode='0xE5840034',base='r4=0x020E9A00',
                                offset='0x34',address='0x020E9A34',width=4,source='r0',value=218,
                                before=218,predicted_after=218,changed_bytes=0,
                                classification='unknown semantic role; idempotent exercise-object word assignment',
                                mapped_result_count_phase_fields_affected=False),
        next_call=dict(pc='0x02026254',target='0x02025F78',arguments=[0x020E9A00,1,4,0],
                       effects='Exact prefix reaches nested BL at 0x0202600C; first nested object store proven at 0x02067BDC; remainder unbounded and dispatch forbidden'),
        inner_call_prefix=dict(
            entry_arguments=[0x020E9A00,1,4,0],
            branches=[dict(pc='0x02025F98',predicate='+0x1C == 0',value=0,taken=True,target='0x02025FD0'),
                      dict(pc='0x02025FDC',predicate='signed +0x40 >= +0x3C',values=[1,20],taken=False,target='0x02026048'),
                      dict(pc='0x02025FEC',predicate='signed indexed +0x54 value > 9',value=11,taken=True,target='0x02025FFC')],
            nested_call=dict(pc='0x0202600C',target='0x02067BD4',arguments=[0x020E9F70,0,0,31]),
            first_nested_object_store=dict(pc='0x02067BDC',opcode='0xE5842254',base='r4=0x020E9F70',
                                           offset='0x254',exercise_offset='0x7C4',address='0x020EA1C4',
                                           width=4,source='r2=0',before=nested_before,predicted_after=0,
                                           classification='unknown subobject state; semantic role not proven'),
            scope='Static prefix only; no full effect/safety claim for either inner routine'),
        ag=dict(start_pc='0x02026B90',stop_pc='0x0202624C',stop_before_first_object_store=True,
                dispatch_count=8,predicted_stop_r=predicted,predicted_nzcv=[1,0,0,0],
                may_dispatch_outer_call='Yes, only with separately authorized exact-prefix pre-dispatch guard',
                first_object_store_recommendation='Mechanically safe/idempotent in exact state, but omit from smallest AG experiment',
                alternative_if_explicitly_authorized=dict(stop_pc='0x02026250',dispatch_count=9,
                                                          effect='Exactly one additional idempotent object store'),
                forbid=['0x0202624C dispatch in preferred experiment','0x02026254 inner call',
                        'return/continuation','score/count/phase/progression/history/save changes',
                        'unexpected guest instructions or MMIO','general guest-call framework']),
        safety=dict(guest_instructions_executed_in_AF=0,pending_call_executed=False,
                    guest_or_save_mutations=0,logical_save_requests_in_AF=0,flash_commits_in_AF=0,
                    ag_started=False,input_hashes_unchanged=True),
        input_sha256=initial,
        limitations=['Exact AE state only; no AF runtime/scheduler validation',
                     '+0x34 meaning unproven; no score/history semantic names assigned',
                     'Only first object-store prefixes of inner routines bounded; full bodies not authorized'],
        contradictions=[])

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--export',action='store_true')
    args=parser.parse_args()
    result=analyze()
    if args.export:
        (ROOT/'docs/BrainAge_TaskAF_Result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'classification':result['classification'],'static_checks':'PASS',
                      'guest_dispatches':0,'ag_stop':result['ag']['stop_pc']}))
