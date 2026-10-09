"""Install a read-only, opt-in Tier-3 observer on the pinned local runtime."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2]
fw=root/'local/ndsrecomp'
assert subprocess.check_output(['git','-C',str(fw),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
p=fw/'runner/src/tier3.cpp';s=p.read_text()
if '#include "brainage_task_r_trace.h"' not in s:
 s=s.replace('#include "brainage_task_c_trace.h"','#include "brainage_task_c_trace.h"\n#include "brainage_task_r_trace.h"')
 anchor='if (condition_passed) task_i_snapshot(pc, thumb, in.raw, ic.R);'
 assert anchor in s
 s=s.replace(anchor,anchor+'\n            if (condition_passed) task_r::snapshot(pc, thumb, ic.R);')
 p.write_text(s)
(fw/'runner/src/brainage_task_r_trace.h').write_bytes((root/'tools/task_r/request_trace.h').read_bytes())
print('Task R observer installed; force-tier3 required for authoritative capture')
