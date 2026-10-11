"""Read-only fixed POP decode and original stack provenance; no guest execution."""
import hashlib,json,struct
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
rom=(ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds').read_bytes()
sha=hashlib.sha1(rom).hexdigest();assert sha=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',rom,0x20)
def word(pc):return struct.unpack_from('<I',rom,o+pc-base)[0]
r=json.loads((ROOT/'docs/BrainAge_TaskAC_Result.json').read_text());pre=r['safe_stop'];pc=0x02025744;opcode=word(pc)
assert pre['pc']==pc and pre['opcode']==opcode==0x08bd8030
m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM);dec=next(m.disasm(struct.pack('<I',opcode),pc))
assert dec.mnemonic=='popeq' and dec.op_str=='{r4, r5, pc}'
assert '02025744 08BD8030 popeq {r4, r5, pc}' in (ROOT/'local/task-z/static-001/02025698.txt').read_text()
assert pre['z']==1 and pre['r'][13]==0x027e3b08 and pre['r'][14]==0
assert ((opcode>>20)&31)==11 and ((opcode>>16)&15)==13 and opcode&65535==0x8030
local=ROOT/'local/task-ac/session-001';dtcm=(local/'decision-after-dtcm.bin').read_bytes();ram=(local/'decision-after-mainram.bin').read_bytes()
assert hashlib.sha256(dtcm).hexdigest()==r['hashes']['immediate_dtcm_after']
assert hashlib.sha256(ram).hexdigest()==r['hashes']['immediate_mainram_after']
steps=[json.loads(x) for x in (local/'audit.jsonl').read_text().splitlines() if json.loads(x)['event']=='decision_step']
helper=next(s for s in steps if s['pc']==0x02025698)
assert word(0x02025698)==0xe92d4030 and word(0x0202582c)==0xebffff99
assert helper['r'][13]==0x027e3b14 and [helper['r'][i] for i in (4,5,14)]==[1,0x020e9a00,0x02025830]
reads=[{'address':pre['r'][13]+4*i,'value':struct.unpack_from('<I',dtcm,pre['r'][13]+4*i-0x027e0000)[0],'register':reg} for i,reg in enumerate((4,5,15))]
assert [s['value'] for s in reads]==[helper['r'][i] for i in (4,5,14)]
assert word(0x02025830)==0xe8bd8010
proof={'rom_sha1':sha,'pc':hex(pc),'opcode':f'0x{opcode:08X}','decoded':dec.mnemonic+' '+dec.op_str,'alias':'LDMEQIA sp!,{r4,r5,pc}','condition':'EQ / Z == 1','register_list':[4,5,15],'sp_before':pre['r'][13],'stack_reads':reads,'sp_after':pre['r'][13]+12,'expected_successor':'0x02025830','successor_opcode':'0xE8BD8010','lr_before':0,'lr_expected':0,'memory_write':False,'flags_updated':False,'s_bit':0,'provenance':{'push_pc':'0x02025698','push_opcode':'0xE92D4030','original_call_pc':'0x0202582C','original_call_opcode':'0xEBFFFF99','saved_registers':[4,5,14],'helper_entry_sp':helper['r'][13]},'safe':True}
out=ROOT/'local/task-ad/preflight.json';out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():assert json.loads(out.read_text())==proof
else:out.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
