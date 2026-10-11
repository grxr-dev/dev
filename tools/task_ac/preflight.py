"""Independently decode one fixed instruction from the selected exact ROM; no guest execution."""
import argparse,hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds');a=p.parse_args()
rom=a.rom.read_bytes();assert hashlib.sha1(rom).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',rom,0x20);pc=0x02025740;opcode=struct.unpack_from('<I',rom,o+pc-base)[0]
r=json.loads((ROOT/'docs/BrainAge_TaskAB_Result.json').read_text());pre=r['safe_stop'];assert pre['pc']==pc and pre['opcode']==opcode
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);decoded=next(m.disasm(struct.pack('<I',opcode),pc))
assert decoded.mnemonic=='addeq' and decoded.op_str=='sp, sp, #4'
assert '02025740 028DD004 addeq sp, sp, #4' in (ROOT/'local/task-z/static-001/02025698.txt').read_text()
rn=(opcode>>16)&15;rd=(opcode>>12)&15;imm=opcode&255;rotate=((opcode>>8)&15)*2
assert opcode==0x028dd004 and rn==rd==13 and imm==4 and rotate==0
assert pre['z']==1 and pre['r'][13]==0x027e3b04 and pre['r'][14]==0
ram=(ROOT/'local/task-ab/session-001/decision-after-mainram.bin').read_bytes()
assert hashlib.sha256(ram).hexdigest()==r['hashes']['immediate_mainram_after']
assert struct.unpack_from('<I',rom,o+pc+4-base)[0]==0x08bd8030
proof={'rom_sha1':hashlib.sha1(rom).hexdigest(),'pc':hex(pc),'opcode':f'0x{opcode:08X}','decoded':decoded.mnemonic+' '+decoded.op_str,'condition':'EQ / Z == 1','source_register':rn,'destination_register':rd,'source_value':pre['r'][rn],'immediate':imm,'rotate':rotate,'expected_value':pre['r'][rn]+imm,'flags_updated':False,'memory_write':False,'effective_memory_address':None,'branch_or_call':False,'branch_call_target':None,'lr_before':pre['r'][14],'lr_expected':pre['r'][14],'expected_successor':'0x02025744','successor_opcode':'0x08BD8030','static_evidence':'Retained local/task-z/static-001/02025698.txt agrees with independent exact-ROM Capstone decode','safe':True}
out=ROOT/'local/task-ac/preflight.json';out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():assert json.loads(out.read_text())==proof,'frozen decode contradicts current evidence'
else:out.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
