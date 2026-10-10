"""Install the opt-in fixed publication gate on the existing pinned SDL runner."""
import argparse,difflib,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--codex-executable',type=Path,required=True);args=parser.parse_args()
root=Path(__file__).resolve().parents[2];framework=root/'local/ndsrecomp';source=framework/'runner/src'
assert subprocess.check_output(['git','-C',str(framework),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
def patch(path,text):
    if path.exists():
        old=path.read_text()
        if old==text:return
        lines=list(difflib.unified_diff(old.splitlines(),text.splitlines(),n=3))[2:]
        body='*** Update File: '+path.relative_to(root).as_posix()+'\n'+'\n'.join('@@' if line.startswith('@@') else line for line in lines)
    else:body='*** Add File: '+path.relative_to(root).as_posix()+'\n'+'\n'.join('+'+line for line in text.splitlines())
    subprocess.run([str(args.codex_executable.resolve()),'--codex-run-as-apply-patch','*** Begin Patch\n'+body+'\n*** End Patch\n'],cwd=root,check=True)
patch(source/'bc_calculations_policy.h',(root/'tools/brainage_custom/bc_calculations_policy.h').read_text())
patch(source/'brainage_task_y.h',(root/'tools/task_y/diagnostic.h').read_text())
path=source/'tier3.cpp';text=path.read_text()
if '#include "brainage_task_y.h"' not in text:
    anchor='#include "brainage_native_probe.h"';assert text.count(anchor)==1;text=text.replace(anchor,anchor+'\n#include "brainage_task_y.h"')
if 'brainage_task_y::control(ic)' not in text:
    anchor='        sync_out(ic);\n\n        // Deadline-bounded exit polling';assert text.count(anchor)==1
    text=text.replace(anchor,'        sync_out(ic);\n        if (brainage_task_y::control(ic) == 2) { sync_out(ic); nds_preserve_unwind_state(); break; }\n\n        // Deadline-bounded exit polling')
patch(path,text)
path=source/'main.cpp';text=path.read_text()
anchor='        g_nds_force_tier3 = false;';replacement=anchor+'\n        if (std::getenv("NDS_TASK_Y_OUT")) g_nds_force_tier3 = true;'
if replacement not in text:assert text.count(anchor)==1;text=text.replace(anchor,replacement)
patch(path,text)
path=source/'frontend.cpp';text=path.read_text()
anchor='        while (running && scheduler_system_timestamp() < next_frame &&'
replacement=anchor+'\n               !(std::getenv("NDS_TASK_Y_OUT") && g_nds_terminal) &&'
if replacement not in text:assert text.count(anchor)==1;text=text.replace(anchor,replacement)
anchor='        // A real DS power-off is an application lifecycle request'
replacement='        if (std::getenv("NDS_TASK_Y_OUT") && g_nds_terminal) { running = false; break; }\n'+anchor
if replacement not in text:assert text.count(anchor)==1;text=text.replace(anchor,replacement)
patch(path,text)
print('Task Y fixed Tier-3 publication hook installed; generated code and default behavior untouched')
