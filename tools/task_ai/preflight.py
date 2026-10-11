import hashlib,json,subprocess,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_ah/preflight.py')],check=True)
commit='2b846d5ddeb751c59f02caa1aacd227d016a9b24'
for name in ['docs/BrainAge_TaskAH_IdempotentObjectStore.md','docs/BrainAge_TaskAH_Result.json']+[p.relative_to(ROOT).as_posix() for p in (ROOT/'tools/task_ah').iterdir() if p.is_file()]:
 assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode().splitlines()==(ROOT/name).read_text().splitlines()
ah=json.loads((ROOT/'docs/BrainAge_TaskAH_Result.json').read_text())
for name in ('mainram','dtcm'):
 data=(ROOT/'local/task-ah/session-001'/('decision-after-'+name+'.bin')).read_bytes()
 assert hashlib.sha256(data).hexdigest()==ah['memory'][name+'_after_sha256']
ram=(ROOT/'local/task-ah/session-001/decision-after-mainram.bin').read_bytes()
assert struct.unpack_from('<I',ram,0x26250)[0]==0xe1a00004 and struct.unpack_from('<I',ram,0x26254)[0]==0xebffff47
assert ah['ah_stop']['r']==[218,1,4,0,0x020e9a00,0,114,0,0x020e9a00,0,0,0,0,0x027e3b2c,0x02026b94,0x02026250]
assert hashlib.sha256((ROOT/'local/task-ah/session-001/decision-after.sav').read_bytes()).hexdigest()==ah['save']['after_sha256']
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='codex/brainage'
proof={'safe':True,'ah_commit':commit,'ah_result_sha256':hashlib.sha256((ROOT/'docs/BrainAge_TaskAH_Result.json').read_bytes()).hexdigest(),'ah_stop':ah['ah_stop'],'ah_memory':ah['memory'],'ah_accounting':ah['accounting'],'AI_dispatch_count':1,'terminal_pc':'0x02026254'}
out=ROOT/'local/task-ai';out.mkdir(exist_ok=True);(out/'preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
print('PASS: immutable AH evidence; exact CPU/RAM/DTCM/save and MOV/terminal BL verified')
