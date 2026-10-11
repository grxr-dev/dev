"""Install the fixed opt-in AN hook before AN; generated ROM-derived C is untouched."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'local/ndsrecomp';s=f/'runner/src'
assert subprocess.check_output(['git','-C',str(f),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
for src,dst in [('diagnostic.h','brainage_task_ao.h'),('task_ao_decision.inc','task_ao_decision.inc'),('guard.h','task_ao_guard.h')]:
 (s/dst).write_text((ROOT/'tools/task_ao'/src).read_text(encoding='utf-8-sig'))
p=s/'tier3.cpp';t=p.read_text();anchor='#include "brainage_task_an.h"';replacement=anchor+'\n#include "brainage_task_ao.h"'
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
anchor='        if (brainage_task_an::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }'
replacement='        if (brainage_task_ao::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n'+anchor
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
assert t.index('brainage_task_ao::control(ic)')<t.index('const bool covered = nds_has_bank')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
for bits,typ in [(8,'uint8_t '),(16,'uint16_t'),(32,'uint32_t')]:
 # Match exact existing adapter spelling, keeping the underlying bus call once.
 old=next(line.strip() for line in t.splitlines() if line.strip().startswith('void write'+str(bits)) and 'override' in line)
 new=old.replace('bus_write_u'+str(bits)+'(a, v);','brainage_task_ao::memory_before(a,'+str(bits//8)+',v); bus_write_u'+str(bits)+'(a, v); brainage_task_ao::memory_after(a,'+str(bits//8)+',v);')
 if 'brainage_task_ao::memory_before' not in old:t=t.replace(old,new)
for bits in (8,16,32):
 old=next(line.strip() for line in t.splitlines() if ('read'+str(bits)+' ' in line or 'read'+str(bits)+'(' in line) and 'override' in line)
 if 'brainage_task_ao::memory_read' not in old:t=t.replace(old,old.replace('return bus_read','brainage_task_ao::memory_read(a,'+str(bits//8)+'); return bus_read'))
p.write_text(t)
for name in ('main.cpp','frontend.cpp'):
 p=s/name;t=p.read_text();anchor='std::getenv("NDS_TASK_AE_OUT")'
 if 'std::getenv("NDS_TASK_AO_OUT")' not in t:
  assert anchor in t;t=t.replace(anchor,'('+anchor+' || std::getenv("NDS_TASK_AO_OUT"))')
 p.write_text(t)
print('Task AO pre-dispatch hook installed; earlier diagnostics and generated code unchanged')
