import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
b=ROOT/'build/task-al-tests';b.mkdir(exist_ok=True)
results={}
for name,src in [('AL_guard','tools/task_al/guard_test.cpp'),('AK_guard','tools/task_ak/guard_test.cpp'),('policy','tools/task_y/policy_test.cpp')]:
 binary=b/(name+'.exe');subprocess.run([str(ROOT/'local/toolchain/w64devkit/bin/g++.exe'),'-std=c++17','-O2','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/src),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 results[name]=subprocess.check_output([str(binary)],text=True).strip()
t=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert t.index('brainage_task_al::control(ic)')<t.index('brainage_task_ak::control(ic)')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
for bits in (8,16,32):
 line=next(l for l in t.splitlines() if l.strip().startswith('void write'+str(bits)) and 'override' in l)
 assert line.count('bus_write_u'+str(bits)+'(a, v)')==1
 assert line.index('brainage_task_al::memory_before')<line.index('bus_write_u'+str(bits))<line.index('brainage_task_al::memory_after')
results['hook_order_and_single_bus_call']='PASS'
(ROOT/'local/task-al/focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
