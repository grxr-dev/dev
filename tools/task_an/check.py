import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
b=ROOT/'build/task-an-tests';b.mkdir(exist_ok=True)
results={}
for name,src in [('AN_guard','tools/task_an/guard_test.cpp'),('AL_guard','tools/task_al/guard_test.cpp'),('policy','tools/task_y/policy_test.cpp')]:
 binary=b/(name+'.exe');subprocess.run([str(ROOT/'local/toolchain/w64devkit/bin/g++.exe'),'-std=c++17','-O2','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/src),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 results[name]=subprocess.check_output([str(binary)],text=True).strip()
t=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert t.index('brainage_task_an::control(ic)')<t.index('brainage_task_al::control(ic)')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
for bits in (8,16,32):
 line=next(l for l in t.splitlines() if l.strip().startswith('void write'+str(bits)) and 'override' in l)
 assert line.count('bus_write_u'+str(bits)+'(a, v)')==1
 assert line.index('brainage_task_an::memory_before')<line.index('bus_write_u'+str(bits))<line.index('brainage_task_an::memory_after')
results['hook_order_and_single_bus_call']='PASS'
import re
m=json.loads((ROOT/'tools/task_an/expected.json').read_text());g=(ROOT/'tools/task_an/guard.h').read_text()
block=g.split('an_r[20][16]={',1)[1].split('};',1)[0]
assert [[int(x,16) for x in re.findall(r'0x([0-9a-f]+)u',row)] for row in block.splitlines() if '{' in row]==[s['r'] for s in m['states']]
block=g.split('an_flags[20][4]={',1)[1].split('};',1)[0]
assert [[int(x) for x in row.split(',')] for row in re.findall(r'\{([^{}]+)\}',block)]==[s['nzcv'] for s in m['states']]
block=g.split('an_opcodes[]={',1)[1].split('};',1)[0]
assert [int(x,16) for x in re.findall(r'0x([0-9a-f]+)u',block)]==[int(f['opcode'],16) for f in m['facts']]
results['compiled_full_states_match_frozen_AM_model']='PASS'
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 assert subprocess.check_output(['git','show','cb2126cfa0c2e75714b993cdc0124c49c8e1b680:tools/brainage_custom/'+name],cwd=ROOT).decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']='PASS'
assert t.index('brainage_task_an::control(ic)')<t.index('const bool covered = nds_has_bank')
assert 'AN forbids every write before underlying bus' in (ROOT/'tools/task_an/diagnostic.h').read_text()
results['AN_pre_dispatch_and_before_bus_firewall']='PASS'
(ROOT/'local/task-an/focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
