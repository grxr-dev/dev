"""Install only the opt-in fixed Task Z diagnostic; retain Task Y unchanged."""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'local/ndsrecomp';s=f/'runner/src'
assert subprocess.check_output(['git','-C',str(f),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
for original,target in [('diagnostic.h','brainage_task_z.h'),('task_z_decision.inc','task_z_decision.inc'),('guard.h','task_z_guard.h')]:
 (s/target).write_text((ROOT/'tools/task_z'/original).read_text(encoding='utf-8-sig'))
p=s/'tier3.cpp';t=p.read_text();anchor='#include "brainage_task_y.h"';replacement=anchor+'\n#include "brainage_task_z.h"'
if replacement not in t:assert t.count(anchor)==1;t=t.replace(anchor,replacement)
anchor='        if (brainage_task_y::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }'
replacement='        if (brainage_task_z::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n'+anchor
if replacement not in t:assert t.count(anchor)==1;t=t.replace(anchor,replacement)
p.write_text(t)
for name in ('main.cpp','frontend.cpp'):
 p=s/name;t=p.read_text();t=t.replace('std::getenv("NDS_TASK_Y_OUT")','(std::getenv("NDS_TASK_Y_OUT") || std::getenv("NDS_TASK_Z_OUT"))') if 'std::getenv("NDS_TASK_Z_OUT")' not in t else t;p.write_text(t)
print('Task Z opt-in hook installed; Task Y hook and generated code unchanged')
