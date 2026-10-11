import json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_aj/analyze.py')],check=True)
commit='a1d2c76baedc0ae841086eeccaf9aa5daebe8d16'
for name in ['docs/BrainAge_TaskAJ_InnerHelperStaticMap.md','docs/BrainAge_TaskAJ_Result.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_aj/'],cwd=ROOT,text=True).splitlines():
 assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode().splitlines()==(ROOT/name).read_text().splitlines(),name
m=json.loads((ROOT/'tools/task_ak/expected.json').read_text());aj=json.loads((ROOT/'docs/BrainAge_TaskAJ_Result.json').read_text());ai=json.loads((ROOT/'docs/BrainAge_TaskAI_Result.json').read_text())
assert m['facts']==aj['instruction_facts'][:26] and m['writes']==aj['stack_writes']
assert m['states'][0]['r']==ai['ai_stop']['r'] and m['states'][-1]['r']==[int(x,16) for x in aj['ak']['r']]
out=ROOT/'local/task-ak';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'aj_commit':commit,'ai_stop':ai['ai_stop'],'AJ_dispatch_count':25,'terminal_pc':'0x02067BDC','model_sha256':hashlib.sha256((ROOT/'tools/task_ak/expected.json').read_bytes()).hexdigest()},indent=2)+'\n')
print('PASS: immutable AJ/AI evidence and complete ROM/checkpoint identity')
