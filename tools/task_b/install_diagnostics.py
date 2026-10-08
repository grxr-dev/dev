"""Install the Task B observer on the pinned framework with Task A already applied."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2];framework=root/"local/ndsrecomp"
assert subprocess.check_output(["git","-C",str(framework),"rev-parse","HEAD"],text=True).strip()=="3a57236bb23d25dcb4caad7d58d733311062ff5e"
src=framework/"runner/src";p=src/"tier3.cpp";s=p.read_text()
assert 'TaskAInstructionScope task_a_instruction_scope(pc, thumb);' in s
if '#include "brainage_request_trace.h"' not in s:s=s.replace('#include "brainage_flash_trace.h"','#include "brainage_flash_trace.h"\n#include "brainage_request_trace.h"')
if 'task_b_snapshot(pc, thumb, ic.R, pack_cpsr(ic));' not in s:s=s.replace('TaskAInstructionScope task_a_instruction_scope(pc, thumb);','task_b_snapshot(pc, thumb, ic.R, pack_cpsr(ic));\n            TaskAInstructionScope task_a_instruction_scope(pc, thumb);')
p.write_text(s)
(src/"brainage_request_trace.h").write_bytes((root/"tools/task_b/brainage_request_trace.h").read_bytes())
s=(root/"tools/task_a/brainage_flash_trace.h").read_text().replace('#include "state.h"','#include "state.h"\n#include "brainage_request_trace.h"')
s=s.replace('FILE* output = task_a_flash_trace_file();','if (task_b_armed && offset == 0x18f && last) task_b_done = true;\n    FILE* output = task_a_flash_trace_file();')
(src/"brainage_flash_trace.h").write_text(s)
print("Task B observer installed; use the route helper with --force-tier3 and NDS_TASK_B_TRACE")
