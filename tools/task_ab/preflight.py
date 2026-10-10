"""Read-only exact-ROM decode plus committed AA pre-state; no guest execution."""
import argparse,hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds');a=p.parse_args()
rom=a.rom.read_bytes();assert hashlib.sha1(rom).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',rom,0x20);pc=0x0202573c;opcode=struct.unpack_from('<I',rom,o+pc-base)[0]
r=json.loads((ROOT/'docs/BrainAge_TaskAA_Result.json').read_text());pre=r['safe_stop'];assert pre['pc']==pc and pre['opcode']==opcode
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);decoded=next(m.disasm(struct.pack('<I',opcode),pc))
assert decoded.mnemonic=='streq' and decoded.op_str=='r1, [r0, #0x504]'
assert '0202573C 05801504 streq r1, [r0, #0x504]' in (ROOT/'local/task-z/static-001/02025698.txt').read_text()
assert opcode==0x05801504 and (opcode>>25)&7==2
rn=(opcode>>16)&15;rd=(opcode>>12)&15;offset=opcode&4095;address=pre['r'][rn]+offset
assert pre['z']==1 and pre['r'][rd]==1 and address==0x020e9f04
ram=(ROOT/'local/task-aa/session-001/decision-after-mainram.bin').read_bytes()
assert hashlib.sha256(ram).hexdigest()==r['decision_memory_hashes']['mainram_after']
before=struct.unpack_from('<I',ram,address-0x02000000)[0];assert before==0
proof={'rom_sha1':hashlib.sha1(rom).hexdigest(),'pc':hex(pc),'opcode':f'0x{opcode:08X}','decoded':decoded.mnemonic+' '+decoded.op_str,'condition':'EQ / Z == 1','base_register':rn,'base_value':pre['r'][rn],'source_register':rd,'source_value':pre['r'][rd],'immediate_offset':offset,'effective_address':hex(address),'write_bytes':4,'addressing':'immediate positive pre-index, no writeback, word store','before':before,'expected_after':1,'expected_successor':'0x02025740','successor_opcode':'0x028DD004','static_evidence':'Retained local/task-z/static-001/02025698.txt agrees with independent exact-ROM Capstone decode','safe':True}
assert struct.unpack_from('<I',rom,o+pc+4-base)[0]==0x028dd004
out=ROOT/'local/task-ab/preflight.json';out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():assert json.loads(out.read_text())==proof,'existing frozen decode contradicts current evidence'
else:out.write_text(json.dumps(proof,indent=2)+'\n')
print('PASS: independent word-store decode, AA live target/value, no writeback and fixed successor; no guest execution')
