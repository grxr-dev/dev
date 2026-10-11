"""Install fixed AU hooks before AO/accounting/fetch; generated C is untouched."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'local/ndsrecomp';s=f/'runner/src'
assert subprocess.check_output(['git','-C',str(f),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
for src,dst in [('diagnostic.h','brainage_task_au.h'),('task_au_decision.inc','task_au_decision.inc'),('guard.h','task_au_guard.h'),('slice_guard.h','task_au_slice_guard.h'),('slice.inc','task_au_slice.inc'),('entry_guard.h','task_au_entry_guard.h'),('entry.inc','task_au_entry.inc'),('setup_guard.h','task_au_setup_guard.h'),('setup.inc','task_au_setup.inc')]:
 (s/dst).write_text((ROOT/'tools/task_au'/src).read_text(encoding='utf-8-sig'))
p=s/'tier3.cpp';t=p.read_text();anchor='#include "brainage_task_as.h"';replacement=anchor+'\n#include "brainage_task_au.h"'
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
anchor='        if (brainage_task_as::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }'
replacement='        if (brainage_task_au::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n'+anchor
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
assert t.index('brainage_task_au::control(ic)')<t.index('const bool covered = nds_has_bank')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
for bits,typ in [(8,'uint8_t '),(16,'uint16_t'),(32,'uint32_t')]:
 # Match exact existing adapter spelling, keeping the underlying bus call once.
 old=next(line.strip() for line in t.splitlines() if line.strip().startswith('void write'+str(bits)) and 'override' in line)
 new=old.replace('bus_write_u'+str(bits)+'(a, v);','brainage_task_au::memory_before(a,'+str(bits//8)+',v); bus_write_u'+str(bits)+'(a, v); brainage_task_au::memory_after(a,'+str(bits//8)+',v);')
 if 'brainage_task_au::memory_before' not in old:t=t.replace(old,new)
for bits in (8,16,32):
 old=next(line.strip() for line in t.splitlines() if ('read'+str(bits)+' ' in line or 'read'+str(bits)+'(' in line) and 'override' in line)
 if 'brainage_task_au::memory_read' not in old:t=t.replace(old,old.replace('return bus_read','brainage_task_au::memory_read(a,'+str(bits//8)+'); return bus_read'))
p.write_text(t)
for name in ('main.cpp','frontend.cpp'):
 p=s/name;t=p.read_text();anchor='std::getenv("NDS_TASK_AE_OUT")'
 if 'std::getenv("NDS_TASK_AU_OUT")' not in t:
  assert anchor in t;t=t.replace(anchor,'('+anchor+' || std::getenv("NDS_TASK_AU_OUT"))')
 p.write_text(t)
print('Task AU pre-dispatch hook installed; earlier diagnostics and generated code unchanged')
