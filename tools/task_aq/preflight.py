import json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_ao/preflight.py')],check=True)
subprocess.run(['python',str(ROOT/'tools/task_ap/check.py')],check=True)
for commit,names in [('f36f1ac432a5946f1b451e2d437176447163df3f',['docs/BrainAge_TaskAP_PostAOStaticMap.md','docs/BrainAge_TaskAP_Result.json']),('3e2ecf215823ad1e5b95a4af830d4ee6026152e0',['docs/BrainAge_TaskAO_SecondValueChangingObjectStore.md','docs/BrainAge_TaskAO_Result.json'])]:
 names+=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_'+('ap' if 'AP' in names[0] else 'ao')+'/'],cwd=ROOT,text=True).splitlines()
 for name in names:assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode('utf-8-sig').splitlines()==(ROOT/name).read_text(encoding='utf-8-sig').splitlines(),name
x=json.loads((ROOT/'tools/task_aq/expected.json').read_text());assert x==json.loads((ROOT/'docs/BrainAge_TaskAP_Result.json').read_text())
assert x['classification']=='FULL PASS' and x['aq']['instruction_count']==45 and len(x['stores'])==18
for name,wanted in x['entry_hashes'].items():
 file='decision-after.sav' if name=='save' else 'decision-after-'+name+'.bin'
 ao=json.loads((ROOT/'docs/BrainAge_TaskAO_Result.json').read_text());assert hashlib.sha256((ROOT/ao['authoritative_path']/file).read_bytes()).hexdigest()==wanted
out=ROOT/'local/task-aq';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'AP_commit':'f36f1ac432a5946f1b451e2d437176447163df3f','AO_commit':'3e2ecf215823ad1e5b95a4af830d4ee6026152e0','model_sha256':hashlib.sha256((ROOT/'tools/task_aq/expected.json').read_bytes()).hexdigest(),'entry':x['entry'],'hashes':x['entry_hashes']},indent=2)+'\n')
print('PASS committed AP/AO identity, static ROM certificate, retained full images and frozen model')
