"""Install the fixed opt-in AB hook before AA; generated ROM-derived C is untouched."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'local/ndsrecomp';s=f/'runner/src'
assert subprocess.check_output(['git','-C',str(f),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
for src,dst in [('diagnostic.h','brainage_task_ab.h'),('task_ab_decision.inc','task_ab_decision.inc'),('guard.h','task_ab_guard.h')]:
 (s/dst).write_text((ROOT/'tools/task_ab'/src).read_text(encoding='utf-8-sig'))
p=s/'tier3.cpp';t=p.read_text();anchor='#include "brainage_task_aa.h"';replacement=anchor+'\n#include "brainage_task_ab.h"'
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
anchor='        if (brainage_task_aa::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }'
replacement='        if (brainage_task_ab::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n'+anchor
if replacement not in t:
 assert t.count(anchor)==1;t=t.replace(anchor,replacement)
assert t.index('brainage_task_ab::control(ic)')<t.index('++g_stats.instructions')<t.index('r = Interpreter::step')
p.write_text(t)
for name in ('main.cpp','frontend.cpp'):
 p=s/name;t=p.read_text();anchor='std::getenv("NDS_TASK_AA_OUT")'
 if 'std::getenv("NDS_TASK_AB_OUT")' not in t:
  assert anchor in t;t=t.replace(anchor,'('+anchor+' || std::getenv("NDS_TASK_AB_OUT"))')
 p.write_text(t)
print('Task AB pre-dispatch hook installed; earlier diagnostics and generated code unchanged')
