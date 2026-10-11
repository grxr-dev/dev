"""Read-only AF/AE identity check; freeze exactly the authorized AG prefix."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
import capstone
ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
af_path=ROOT/'docs/BrainAge_TaskAF_Result.json';ae_path=ROOT/'docs/BrainAge_TaskAE_Result.json'
for path,commit in ((af_path,'63ff0c59f995fe9e2df57248ef261d1f4c8c6819'),(ae_path,'6a43d5bfa4c85773b0f986b9d73944ab5e01700e')):
 assert subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT).decode().splitlines()==path.read_text().splitlines()
af=json.loads(af_path.read_text());ae=json.loads(ae_path.read_text());assert af['ae_safe_stop']==ae['safe_stop']
for path,digest in af['input_sha256'].items():assert sha((ROOT.parent/path).read_bytes())==digest
assert subprocess.check_output(['git','-C',str(ROOT/'local/ndsrecomp'),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
rom=(ROOT.parent/'Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds').read_bytes();assert hashlib.sha1(rom).hexdigest()==af['rom_sha1']=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
o,_,base,n=struct.unpack_from('<4I',rom,0x20);m=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
ram=(ROOT/'local/task-ae/session-001/decision-after-mainram.bin').read_bytes();dtcm=(ROOT/'local/task-ae/session-001/decision-after-dtcm.bin').read_bytes()
assert sha(ram)==ae['hashes']['immediate_mainram_after'] and sha(dtcm)==ae['hashes']['immediate_dtcm_after']
source=(ROOT/'tools/task_ag/guard.h').read_text();body=re.search(r'outer_r\[9\]\[16\]=\{(.*?)\n\};',source,re.S)[1]
regs=[[int(x.rstrip('u'),16) for x in line.strip('{}').split(',')] for line in body.strip().split(',\n')]
assert len(regs)==9 and regs[0]==ae['safe_stop']['r'] and regs[-1]==af['ag']['predicted_stop_r']
states=[]
for index,fact in enumerate(af['instruction_facts'][:9]):
 pc=int(fact['pc'],16);opcode=int(fact['opcode'],16)
 assert regs[index][15]==pc and struct.unpack_from('<I',rom,o+pc-base)[0]==opcode and struct.unpack_from('<I',ram,pc-0x02000000)[0]==opcode
 dec=next(m.disasm(struct.pack('<I',opcode),pc));assert dec.mnemonic+' '+dec.op_str==fact['decoded']
 states.append({'pc':pc,'opcode':opcode,'decoded':fact['decoded'],'r':regs[index],'nzcv':[1,0,0,0],'dispatch':index<8})
assert states[-1]['pc']==0x0202624c and states[-1]['opcode']==0xe5840034
assert af['phase_dispatch']['target']=='0x02026234' and 0x02026228+8+(1<<2)==0x02026234
for f in af['fields']:
 value=int.from_bytes(ram[int(f['address'],16)-0x02000000:int(f['address'],16)-0x02000000+f['width']],'little');assert value==f['value']
expected=bytearray(dtcm)
for f in af['first_memory_write']['words']:
 a=int(f['address'],16)-0x027e0000;assert struct.unpack_from('<I',dtcm,a)[0]==f['before'];struct.pack_into('<I',expected,a,f['predicted_after'])
proof={'safe':True,'rom_sha1':af['rom_sha1'],'framework_baseline':af['framework_baseline'],'ae_start':ae['safe_stop'],'states':states,'fields':af['fields'],'stack_words':af['first_memory_write']['words'],'expected_dtcm_after_sha256':sha(expected),'mainram_sha256':sha(ram),'dtcm_sha256':sha(dtcm),'checkpoint_sha256':ae['checkpoint_sha256'],'save_sha256':ae['save']['after_sha256'],'ae_json_sha256':sha(ae_path.read_bytes()),'af_json_sha256':sha(af_path.read_bytes()),'new_dispatches':8,'stop_before_pc':'0x0202624C','first_object_store_dispatched':False}
out=ROOT/'local/task-ag/preflight.json';out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():assert json.loads(out.read_text())==proof
else:out.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'safe':True,'start':'0x02026B90','stop':'0x0202624C','new_dispatches':8,'predicted_changed_dtcm_bytes':sum(a!=b for a,b in zip(dtcm,expected))}))
