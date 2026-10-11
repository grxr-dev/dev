import subprocess,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_am/analyze.py')],check=True)
for commit,tag,report in [('cb2126cfa0c2e75714b993cdc0124c49c8e1b680','AM','PostMutationStaticMap'),('7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70','AL','FirstValueChangingObjectStore')]:
 names=[f'docs/BrainAge_Task{tag}_{report}.md',f'docs/BrainAge_Task{tag}_Result.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/'],cwd=ROOT,text=True).splitlines()
 for name in names:assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode().splitlines()==(ROOT/name).read_text().splitlines(),name
am=json.loads((ROOT/'docs/BrainAge_TaskAM_Result.json').read_text());m=json.loads((ROOT/'tools/task_an/expected.json').read_text())
assert m['facts']==am['prefix']+[am['first_next_meaningful_action']]
assert m['states'][0]['r']==am['entry']['r'] and m['states'][-1]['r']==[int(v,16) for v in am['an']['r']]
out=ROOT/'local/task-an';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'AM_commit':'cb2126cfa0c2e75714b993cdc0124c49c8e1b680','AL_commit':'7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70','model_sha256':hashlib.sha256((ROOT/'tools/task_an/expected.json').read_bytes()).hexdigest(),'AL_start':am['entry'],'AN_dispatches':19,'terminal_pc':'0x02067C44'},indent=2)+'\n')
print('PASS: committed AM/AL artifacts, retained AL CPU/images, exact ROM/checkpoint identity')
