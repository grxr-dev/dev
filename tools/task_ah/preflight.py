import hashlib,json,subprocess,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_ag/preflight.py')],check=True)
commit='e2bc0765d9d70f8d3e8b12dbc7fbf5c42ac3b5a5'
for name in ['docs/BrainAge_TaskAG_DynamicDispatchBoundary.md','docs/BrainAge_TaskAG_Result.json']+[str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'tools/task_ag').iterdir() if p.is_file()]:
 assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode().splitlines()==(ROOT/name).read_text().splitlines()
ag=json.loads((ROOT/'docs/BrainAge_TaskAG_Result.json').read_text())
for name,key in [('mainram','AG_mainram'),('dtcm','AG_dtcm')]:
 data=(ROOT/'local/task-ag/session-001'/('decision-after-'+name+'.bin')).read_bytes()
 assert hashlib.sha256(data).hexdigest()==ag['hashes'][key]
ram=(ROOT/'local/task-ag/session-001/decision-after-mainram.bin').read_bytes()
assert struct.unpack_from('<I',ram,0x2624c)[0]==0xe5840034 and struct.unpack_from('<I',ram,0x26250)[0]==0xe1a00004
assert ag['ag_stop']['r']==[218,1,4,0,0x020e9a00,0,114,0,0x020e9a00,0,0,0,0,0x027e3b2c,0x02026b94,0x0202624c]
assert ag['accounting']['arm9_ordinal_after']==281097897
out=ROOT/'local/task-ah';out.mkdir(exist_ok=True)
proof={'safe':True,'ag_commit':commit,'ag_result_sha256':hashlib.sha256((ROOT/'docs/BrainAge_TaskAG_Result.json').read_bytes()).hexdigest(),'ag_stop':ag['ag_stop'],'ag_hashes':ag['hashes'],'ag_accounting':ag['accounting'],'store_pc':0x0202624c,'terminal_pc':0x02026250,'ah_dispatch_count':1}
(out/'preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
print('PASS: authoritative AG source/state/evidence and sole STR/terminal opcode validated')
