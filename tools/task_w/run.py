"""One frozen-corpus SDL session per digit, then repeat 0 and preserve legacy V proof."""
import argparse,json,subprocess
from pathlib import Path
from corpus import load,EXPECTED
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parents[2];out=a.out.resolve();assert out.is_relative_to(r/'local/task-w');out.mkdir(exist_ok=False,parents=True)
freeze=load();(out/'freeze.json').write_text(json.dumps({'sha256':EXPECTED,'corpus':freeze},indent=2)+'\n')
for label in range(10):
    cmd=['python',str(r/'tools/task_w/drive.py'),'--out',str(out/f'digit-{label}'),'--sample',str(label)]
    if label in (0,4,7):cmd+=['--visual']
    if label==4:cmd+=['--handoff-visual']
    print(f'BEGIN FROZEN DIGIT {label}',flush=True);subprocess.run(cmd,cwd=r,check=True)
subprocess.run(['python',str(r/'tools/task_w/drive.py'),'--out',str(out/'repeat-0'),'--sample','0'],cwd=r,check=True)
subprocess.run(['python',str(r/'tools/task_w/drive.py'),'--out',str(out/'legacy-v-4'),'--sample','4','--legacy-v'],cwd=r,check=True)
print('Task W corpus/repeat/legacy sessions completed; run analyzer for classification',flush=True)
