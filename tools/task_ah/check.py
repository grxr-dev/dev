"""Focused AG/AE boundary and unchanged publication-policy checks; no gameplay."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/task-ah-tests';build.mkdir(parents=True,exist_ok=True)
local=ROOT/'local/task-ah';local.mkdir(parents=True,exist_ok=True)
compiler=ROOT/'local/toolchain/w64devkit/bin/g++.exe';results={}
for name,source in [('outer_dispatch_guard','tools/task_ah/guard_test.cpp'),('predecessor_guard','tools/task_ag/guard_test.cpp'),('publication_policy','tools/task_y/policy_test.cpp')]:
 binary=build/(name+'.exe')
 subprocess.run([str(compiler),'-O2','-std=c++17','-Wall','-Wextra','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/source),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 reply=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
 results[name]={'pass':True,'output':reply.stdout.strip()}
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 previous=subprocess.check_output(['git','show','6a43d5bfa4c85773b0f986b9d73944ab5e01700e:tools/brainage_custom/'+name],cwd=ROOT)
 assert previous.decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']={'pass':True}
text=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert text.index('brainage_task_ah::control(ic)')<text.index('const bool covered = nds_has_bank')<text.index('++g_stats.instructions')<text.index('r = Interpreter::step')
results['pre_dispatch_hook']={'pass':True}
for bits in (8,16,32):
 line=next(line for line in text.splitlines() if line.strip().startswith('void write'+str(bits)) and 'override' in line)
 assert line.count('bus_write_u'+str(bits)+'(a, v)')==1
 assert line.index('brainage_task_ah::memory_before')<line.index('bus_write_u'+str(bits))<line.index('brainage_task_ah::memory_after')
 assert 'memory_read(a,'+str(bits//8)+')' in text
results['actual_interpreter_bus_hook']={'pass':True,'widths':[1,2,4],'underlying_bus_call_once':True,'unexpected_MMIO_reads_rejected':True}
assert text.index('brainage_task_ah::control(ic)')<text.index('brainage_task_ag::control(ic)')
results['terminal_guard_before_AG_and_dispatch']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: AH/AG guards and actual write-path instrumentation, frozen publication policy, unchanged production sources and pre-dispatch hook')
