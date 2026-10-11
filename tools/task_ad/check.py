"""Focused AD/AC boundary and unchanged publication-policy checks; no gameplay."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/task-ad-tests';build.mkdir(parents=True,exist_ok=True)
local=ROOT/'local/task-ad';local.mkdir(parents=True,exist_ok=True)
compiler=ROOT/'local/toolchain/w64devkit/bin/g++.exe';results={}
for name,source in [('pop_return_guard','tools/task_ad/guard_test.cpp'),('predecessor_guard','tools/task_ac/guard_test.cpp'),('publication_policy','tools/task_y/policy_test.cpp')]:
 binary=build/(name+'.exe')
 subprocess.run([str(compiler),'-O2','-std=c++17','-Wall','-Wextra','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/source),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 reply=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
 results[name]={'pass':True,'output':reply.stdout.strip()}
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 previous=subprocess.check_output(['git','show','ab430d71d42f7122199f3a35e9922a166972c113:tools/brainage_custom/'+name],cwd=ROOT)
 assert previous.decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']={'pass':True}
text=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert text.index('brainage_task_ad::control(ic)')<text.index('const bool covered = nds_has_bank')<text.index('++g_stats.instructions')<text.index('r = Interpreter::step')
results['pre_dispatch_hook']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: AD/AC guards, frozen publication policy, unchanged production sources and pre-dispatch hook')
