"""Focused AA/Z boundary and unchanged publication-policy checks; no gameplay."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/task-aa-tests';build.mkdir(parents=True,exist_ok=True)
local=ROOT/'local/task-aa';local.mkdir(parents=True,exist_ok=True)
compiler=ROOT/'local/toolchain/w64devkit/bin/g++.exe';results={}
for name,source in [('first_store_guard','tools/task_aa/guard_test.cpp'),('predecessor_guard','tools/task_z/guard_test.cpp'),('publication_policy','tools/task_y/policy_test.cpp')]:
 binary=build/(name+'.exe')
 subprocess.run([str(compiler),'-O2','-std=c++17','-Wall','-Wextra','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/source),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 reply=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
 results[name]={'pass':True,'output':reply.stdout.strip()}
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 previous=subprocess.check_output(['git','show','343a3daf41f05ab5ff14ea05124da2045cafe6cb:tools/brainage_custom/'+name],cwd=ROOT)
 assert previous.decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']={'pass':True}
text=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert text.index('brainage_task_aa::control(ic)')<text.index('++g_stats.instructions')<text.index('r = Interpreter::step')
results['pre_dispatch_hook']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: AA/Z guards, frozen publication policy, unchanged production sources and pre-dispatch hook')
