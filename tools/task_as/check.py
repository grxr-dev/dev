import subprocess,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
b=ROOT/'build/task-as-tests';b.mkdir(exist_ok=True)
results={}
old=(ROOT/'tools/task_as/slice_guard.h').read_bytes();subprocess.run(['python',str(ROOT/'tools/task_as/generate_guard.py')],check=True);assert old==(ROOT/'tools/task_as/slice_guard.h').read_bytes()
for name,src in [('AS_guard','tools/task_as/guard_test.cpp'),('AO_guard','tools/task_ao/guard_test.cpp'),('policy','tools/task_y/policy_test.cpp')]:
 binary=b/(name+'.exe');subprocess.run([str(ROOT/'local/toolchain/w64devkit/bin/g++.exe'),'-std=c++17','-O2','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/src),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True);results[name]=subprocess.check_output([str(binary)],text=True).strip()
t=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert t.index('brainage_task_as::control(ic)')<t.index('brainage_task_aq::control(ic)')<t.index('const bool covered = nds_has_bank')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
for bits in (8,16,32):
 line=next(l for l in t.splitlines() if l.strip().startswith('void write'+str(bits)) and 'override' in l)
 assert line.count('bus_write_u'+str(bits)+'(a, v)')==1
 assert line.index('brainage_task_as::memory_before')<line.index('bus_write_u'+str(bits))<line.index('brainage_task_as::memory_after')
 line=next(l for l in t.splitlines() if ('read'+str(bits)+' ' in l or 'read'+str(bits)+'(' in l) and 'override' in l)
 assert line.index('brainage_task_as::memory_read')<line.index('return bus_read');assert line.count('return bus_read')==1
results['hook_order_single_underlying_bus_call']='PASS'
for name in ['bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h']:
 p='tools/brainage_custom/'+name;assert subprocess.check_output(['git','show','7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad:'+p],cwd=ROOT).decode('utf-8-sig').splitlines()==(ROOT/p).read_text(encoding='utf-8-sig').splitlines()
assert (ROOT/'tools/task_as/slice_guard.h').read_text().replace('as_aq_replay_fixed','aq_fixed')==(ROOT/'tools/task_aq/slice_guard.h').read_text()
results['prior_AQ_table_exact']='PASS'
results['production_sources_unchanged']='PASS';results['certificate_tables_reproducible']='PASS'
(ROOT/'local/task-as/focused-tests.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
