"""Focused AA/Z boundary and unchanged publication-policy checks; no gameplay."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/task-ac-tests';build.mkdir(parents=True,exist_ok=True)
local=ROOT/'local/task-ac';local.mkdir(parents=True,exist_ok=True)
compiler=ROOT/'local/toolchain/w64devkit/bin/g++.exe';results={}
for name,source in [('stack_adjust_guard','tools/task_ac/guard_test.cpp'),('predecessor_guard','tools/task_ab/guard_test.cpp'),('publication_policy','tools/task_y/policy_test.cpp')]:
 binary=build/(name+'.exe')
 subprocess.run([str(compiler),'-O2','-std=c++17','-Wall','-Wextra','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/source),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 reply=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
 results[name]={'pass':True,'output':reply.stdout.strip()}
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 previous=subprocess.check_output(['git','show','9b3396619e0b853ea8445929428beee6919aa15d:tools/brainage_custom/'+name],cwd=ROOT)
 assert previous.decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']={'pass':True}
text=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert text.index('brainage_task_ac::control(ic)')<text.index('++g_stats.instructions')<text.index('r = Interpreter::step')
results['pre_dispatch_hook']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: AC/AB guards, frozen publication policy, unchanged production sources and pre-dispatch hook')
