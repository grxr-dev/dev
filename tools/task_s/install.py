"""Install a fixed-target, opt-in Task S interpreter diagnostic; no generated C edits."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2];fw=root/'local/ndsrecomp'
assert subprocess.check_output(['git','-C',str(fw),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
src=fw/'runner/src';p=src/'tier3.cpp';s=p.read_text()
assert '#include "brainage_task_r_trace.h"' in s, 'Install the existing Task R diagnostic first'
if '#include "brainage_task_s.h"' not in s:s=s.replace('#include "brainage_task_r_trace.h"','#include "brainage_task_r_trace.h"\n#include "brainage_task_s.h"')
anchor='    while (true) {\n        uint32_t pc = ic.R[15];'
replacement='    while (true) {\n        const int task_s_action = task_s::control(ic);\n        if (task_s_action == 1) { sync_out(ic); continue; }\n        if (task_s_action == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n        uint32_t pc = ic.R[15];'
if 'task_s::control(ic)' not in s:
 assert anchor in s;s=s.replace(anchor,replacement)
p.write_text(s)
for a,b in [('adapter.h','task_s_adapter.h'),('diagnostic.h','brainage_task_s.h')]: (src/b).write_bytes((root/'tools/task_s'/a).read_bytes())
print('Task S fixed-target diagnostic installed')
