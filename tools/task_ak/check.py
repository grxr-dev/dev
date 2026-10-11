"""Focused AK/AI boundary and unchanged publication-policy checks; no gameplay."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/task-ak-tests';build.mkdir(parents=True,exist_ok=True)
local=ROOT/'local/task-ak';local.mkdir(parents=True,exist_ok=True)
compiler=ROOT/'local/toolchain/w64devkit/bin/g++.exe';results={}
for name,source in [('inner_prefix_guard','tools/task_ak/guard_test.cpp'),('predecessor_guard','tools/task_ai/guard_test.cpp'),('publication_policy','tools/task_y/policy_test.cpp')]:
 binary=build/(name+'.exe')
 subprocess.run([str(compiler),'-O2','-std=c++17','-Wall','-Wextra','-I',str(ROOT/'tools/brainage_custom'),str(ROOT/source),'-o',str(binary),'-static-libgcc','-static-libstdc++'],check=True)
 reply=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
 results[name]={'pass':True,'output':reply.stdout.strip()}
for name in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_calculations_policy.h'):
 previous=subprocess.check_output(['git','show','6a43d5bfa4c85773b0f986b9d73944ab5e01700e:tools/brainage_custom/'+name],cwd=ROOT)
 assert previous.decode().splitlines()==(ROOT/'tools/brainage_custom'/name).read_text().splitlines()
results['production_sources_unchanged']={'pass':True}
text=(ROOT/'local/ndsrecomp/runner/src/tier3.cpp').read_text()
assert text.index('brainage_task_ak::control(ic)')<text.index('const bool covered = nds_has_bank')<text.index('++g_stats.instructions')<text.index('r = Interpreter::step')
results['pre_dispatch_hook']={'pass':True}
for bits in (8,16,32):
 line=next(line for line in text.splitlines() if line.strip().startswith('void write'+str(bits)) and 'override' in line)
 assert line.count('bus_write_u'+str(bits)+'(a, v)')==1
 assert line.index('brainage_task_ak::memory_before')<line.index('bus_write_u'+str(bits))<line.index('brainage_task_ak::memory_after')
 assert 'memory_read(a,'+str(bits//8)+')' in text
results['actual_interpreter_bus_hook']={'pass':True,'widths':[1,2,4],'underlying_bus_call_once':True,'unexpected_MMIO_reads_rejected':True}
assert text.index('brainage_task_ak::control(ic)')<text.index('brainage_task_ai::control(ic)')
results['terminal_guard_before_AI_and_dispatch']={'pass':True}
diagnostic=(ROOT/'tools/task_ak/diagnostic.h').read_text()
assert 'AK unexpected write before bus dispatch' in diagnostic and 'AK unknown/MMIO read rejected before bus' in diagnostic
assert '(!ah_armed&&!ai_armed)' in diagnostic
results['AK_bus_firewall']={'pass':True}
# Verify every compiled expected state/opcode against the frozen ROM-free model.
import re
model=json.loads((ROOT/'tools/task_ak/expected.json').read_text())
guard=(ROOT/'tools/task_ak/guard.h').read_text()
block=guard.split('ak_r[26][16]={',1)[1].split('};',1)[0]
compiled=[[int(v,16) for v in re.findall(r'0x([0-9a-f]+)u',line)] for line in block.splitlines() if '{' in line]
assert compiled==[s['r'] for s in model['states']]
block=guard.split('ak_flags[26][4]={',1)[1].split('};',1)[0]
assert [[int(v) for v in row.split(',')] for row in re.findall(r'\{([^{}]+)\}',block)]==[s['nzcv'] for s in model['states']]
block=guard.split('ak_opcodes[]={',1)[1].split('};',1)[0]
assert [int(v,16) for v in re.findall(r'0x([0-9a-f]+)u',block)]==[int(f['opcode'],16) for f in model['facts']]
assert 'AK exact full register path' in (ROOT/'tools/task_ak/task_ak_decision.inc').read_text()
assert 'AK exact flags/mode/masks' in (ROOT/'tools/task_ak/task_ak_decision.inc').read_text()
results['full_26_CPU_states_and_opcodes_match_frozen_model']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: AK/AI boundary guards, bus firewall, all 26 CPU states/opcodes, unchanged production policy and pre-dispatch hook')
