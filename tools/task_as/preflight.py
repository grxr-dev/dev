import json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(ROOT/'tools/task_aq/preflight.py')],check=True)
subprocess.run(['python',str(ROOT/'tools/task_ar/check.py')],check=True)
for commit,tag,title in [('7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad','AR','Pending6753CStaticMap'),('06b1432abaac62be3e4649afe58a70b2d5bb793d','AQ','DynamicHelperTailBoundary')]:
 names=['docs/BrainAge_Task'+tag+'_'+title+'.md','docs/BrainAge_Task'+tag+'_Result.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'tools/task_'+tag.lower()+'/'],cwd=ROOT,text=True).splitlines()
 for name in names:assert subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT).decode('utf-8-sig').splitlines()==(ROOT/name).read_text(encoding='utf-8-sig').splitlines(),name
x=json.loads((ROOT/'tools/task_as/expected.json').read_text());assert x==json.loads((ROOT/'docs/BrainAge_TaskAR_Result.json').read_text())
assert x['classification']=='FULL PASS' and x['AS']['instruction_count']==11 and len(x['stores'])==10
q=json.loads((ROOT/'docs/BrainAge_TaskAQ_Result.json').read_text())
for name,wanted in x['entry_hashes'].items():
 file='decision-after.sav' if name=='save' else 'decision-after-'+name+'.bin'
 assert hashlib.sha256((ROOT/q['authoritative_path']/file).read_bytes()).hexdigest()==wanted
out=ROOT/'local/task-as';out.mkdir(exist_ok=True)
(out/'preflight.json').write_text(json.dumps({'safe':True,'AR_commit':'7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad','AQ_commit':'06b1432abaac62be3e4649afe58a70b2d5bb793d','model_sha256':hashlib.sha256((ROOT/'tools/task_as/expected.json').read_bytes()).hexdigest(),'entry':x['entry'],'hashes':x['entry_hashes']},indent=2)+'\n')
print('PASS committed AR/AQ, exact-ROM certificate, retained full images and frozen model')
