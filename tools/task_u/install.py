from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2];fw=root/'local/ndsrecomp';assert subprocess.check_output(['git','-C',str(fw),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
p=fw/'runner/src/main.cpp';s=p.read_text()
if '#include "brainage_task_u.h"' not in s:s=s.replace('#include "brainage_native_probe.h"','#include "brainage_native_probe.h"\n#include "brainage_task_u.h"')
if 'task_u::install();' not in s:s=s.replace('brainage_task_j::initialize(rom_sha1.c_str());','brainage_task_j::initialize(rom_sha1.c_str());\n    task_u::install();')
p.write_text(s);(fw/'runner/src/brainage_task_u.h').write_bytes((root/'tools/task_u/isolated_session.h').read_bytes());(fw/'runner/src/task_s_adapter.h').write_bytes((root/'tools/task_s/adapter.h').read_bytes())

p=fw/'runner/src/tier3.cpp';s=p.read_text()
if '#include "brainage_task_u.h"' not in s:s=s.replace('#include "brainage_native_probe.h"','#include "brainage_native_probe.h"\n#include "brainage_task_u.h"')
if 'task_u::stop_rules(ic.R[15])' not in s:s=s.replace('    while (true) {\n        const int task_s_action', '    while (true) {\n        if (task_u::stop_rules(ic.R[15])) { sync_out(ic); nds_preserve_unwind_state(); break; }\n        const int task_s_action')
p.write_text(s)
