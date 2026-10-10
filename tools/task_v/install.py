"""Install Task V into the already provisioned pinned P/Q/U runner. No generated code edits."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[2];fw=r/'local/ndsrecomp';dst=fw/'runner/src'
assert subprocess.check_output(['git','-C',str(fw),'rev-parse','HEAD'],text=True).strip()=='3a57236bb23d25dcb4caad7d58d733311062ff5e'
assert 'NDS_NATIVE_HOLD_FRONTEND_SERVICE' in (dst/'frontend.h').read_text()
for p in (r/'tools/brainage_custom').glob('bc_*.h'):(dst/p.name).write_bytes(p.read_bytes())
p=dst/'main.cpp';s=p.read_text();old='brainage_task_j::initialize(rom_sha1.c_str());';new='brainage_task_j::initialize(rom_sha1.c_str(), rom.data(), rom.size());'
assert s.count(old)+s.count(new)==1
p.write_text(s.replace(old,new))
print('Task V installed; active verified ROM view supplied at existing title init')
