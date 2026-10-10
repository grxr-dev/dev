"""Task X API and offline policy tests; W check includes focused historical P/Q/V."""
import argparse,json,subprocess
from pathlib import Path
from consumer import test
from corpus import load
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--code-snapshot',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parents[2]
c=load();test();w=json.loads((r/'tools/task_w/corpus.json').read_text())['samples']
for id,label in [('7-w-anchor',7),('9-w-anchor',9),('4-control',4),('5-control',5)]:assert next(s['strokes'] for s in c['samples'] if s['id']==id)==w[label]['strokes']
assert all(0<len(s['strokes'])<=8 and sum(map(len,s['strokes']))<=512 for s in c['samples'])
core=r/'local/ndsrecomp/external/arm-recomp-core/common';out=r/'build/task-x-tests';out.mkdir(exist_ok=True,parents=True)
cmd=[r/'local/toolchain/w64devkit/bin/g++.exe','-O2','-std=c++17','-Wall','-Wextra','-I',r/'tools/brainage_custom','-I',core,r/'tools/task_x/service_test.cpp']+[core/n for n in ('interpreter.cpp','arm_decode.cpp','thumb_decode.cpp','arm_ir.cpp')]+['-o',out/'service_test.exe','-static-libgcc','-static-libstdc++']
subprocess.run(list(map(str,cmd)),cwd=r,check=True)
subprocess.run([str(out/'service_test.exe'),str(a.rom.resolve()),str(a.code_snapshot.resolve())],cwd=r,check=True)
assert json.loads((r/'local/task-w/focused-tests.json').read_text())['pass']
(r/'local/task-x/focused-tests.json').write_text(json.dumps({'pass':True,'consumer_model':True,'exact_anchors':True,'bounded_groups_and_accessor_known_4':True,'historical_W_V_P_Q':'local/task-w/focused-tests.json'},indent=2)+'\n')
