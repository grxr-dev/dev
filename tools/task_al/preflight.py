import subprocess,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_ak/preflight.py')],check=True)
commit='dd29b71e182611fb73016aa1a13367e70c9cd290'
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='codex/brainage'
for name in ['docs/BrainAge_TaskAK_DynamicInnerHelperBoundary.md','docs/BrainAge_TaskAK_Result.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_ak/'],cwd=ROOT,text=True).splitlines():
 assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode().splitlines()==(ROOT/name).read_text().splitlines(),name
ak=json.loads((ROOT/'docs/BrainAge_TaskAK_Result.json').read_text())
assert ak['classification']=='FULL PASS' and ak['ak_stop']['insn9']==281097924
for name,key in [('mainram','mainram_after_sha256'),('dtcm','dtcm_after_sha256')]:
 assert hashlib.sha256((ROOT/ak['authoritative_path']/('decision-after-'+name+'.bin')).read_bytes()).hexdigest()==ak['memory'][key]
assert hashlib.sha256((ROOT/ak['authoritative_path']/'decision-after.sav').read_bytes()).hexdigest()==ak['save']['after_sha256']
out=ROOT/'local/task-al';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'ak_commit':commit,'ak_stop':ak['ak_stop']},indent=2)+'\n')
print('PASS authoritative AK sources, retained images and predecessor provenance')
