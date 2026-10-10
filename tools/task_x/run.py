"""Authoritative frozen Task X SDL batch, labels remain offline metadata."""
import argparse,json,subprocess
from pathlib import Path
from corpus import load,EXPECTED
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parents[2];out=a.out.resolve();assert out.is_relative_to(r/'local/task-x');out.mkdir(exist_ok=False,parents=True)
c=load();(out/'freeze.json').write_text(json.dumps({'sha256':EXPECTED,'corpus':c},indent=2)+'\n')
for i,s in enumerate(c['samples']):
 print('BEGIN '+s['id'],flush=True)
 subprocess.run(['python',str(r/'tools/task_x/drive.py'),'--out',str(out/s['id']),'--sample',str(i)],cwd=r,check=True)
subprocess.run(['python',str(r/'tools/task_x/drive.py'),'--out',str(out/'legacy-v-4'),'--sample','9','--legacy-v'],cwd=r,check=True)
