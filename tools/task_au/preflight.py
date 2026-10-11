import json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_as/preflight.py')],check=True)
subprocess.run(['python','-B',str(ROOT/'tools/task_at/check.py')],check=True)
for commit,tag,title in [('6478bd11b386799a3f4e03f923c39227e982c51d','AT','NestedMMIOStaticMap'),('72c93f2eb0a561ff4b047d171e904477d8553e7b','AS','Dynamic6753CEntryBoundary')]:
 names=['docs/BrainAge_Task'+tag+'_'+title+'.md','docs/BrainAge_Task'+tag+'_Result.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/'],cwd=ROOT,text=True).splitlines()
 for name in names:assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode('utf-8-sig').splitlines()==(ROOT/name).read_text(encoding='utf-8-sig').splitlines(),name
x=json.loads((ROOT/'tools/task_au/expected.json').read_text());assert x==json.loads((ROOT/'docs/BrainAge_TaskAT_Result.json').read_text())
assert x['classification']=='FULL PASS' and x['AU']['instruction_count']==7 and len(x['AU']['stores'])==1
q=json.loads((ROOT/'docs/BrainAge_TaskAS_Result.json').read_text())
for name,wanted in x['entry_hashes'].items():
 file='decision-after.sav' if name=='save' else 'decision-after-'+name+'.bin'
 assert hashlib.sha256((ROOT/q['authoritative_path']/file).read_bytes()).hexdigest()==wanted
out=ROOT/'local/task-au';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'AT_commit':'6478bd11b386799a3f4e03f923c39227e982c51d','AS_commit':'72c93f2eb0a561ff4b047d171e904477d8553e7b','model_sha256':hashlib.sha256((ROOT/'tools/task_au/expected.json').read_bytes()).hexdigest(),'entry':x['entry'],'hashes':x['entry_hashes']},indent=2)+'\n')
print('PASS committed AT/AS, exact-ROM certificate, retained full images and frozen model')
