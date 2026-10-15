"""Install only the guarded capture wrapper. Does not arm or launch anything."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'local/ndsrecomp/runner/src'


def patch_file(path, text):
    old = path.read_text(encoding='utf-8-sig') if path.exists() else None
    if old == text:
        return
    patch = '*** Begin Patch\n'
    if old is None:
        patch += f'*** Add File: {path.as_posix()}\n' + ''.join('+' + line + '\n' for line in text.splitlines())
    else:
        lines = list(difflib.unified_diff(old.splitlines(), text.splitlines(), n=3))[2:]
        patch += f'*** Update File: {path.as_posix()}\n' + ''.join(('@@' if line.startswith('@@') else line) + '\n' for line in lines)
    patch += '*** End Patch\n'
    binary = Path.home() / 'AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'
    subprocess.run([str(binary), '--codex-run-as-apply-patch', patch], check=True)


def main():
    if not (SOURCE / 'aw5/capture.h').exists():
        subprocess.run(['python', str(ROOT / 'tools/task_aw3/install.py')], check=True)
    patch_file(SOURCE / 'aw4/reconcile.h', (ROOT / 'tools/task_aw4/reconcile.h').read_text())
    patch_file(SOURCE / 'aw5/capture.h', (ROOT / 'tools/task_aw5/capture.h').read_text())
    header = SOURCE / 'brainage_task_au.h'
    text = header.read_text(encoding='utf-8-sig')
    if '#include "aw5/capture.h"' not in text:
        patch_file(header, '#include "aw5/capture.h"\n' + text)
    setup = SOURCE / 'task_au_setup.inc'
    text = setup.read_text(encoding='utf-8-sig')
    old = '        if (task_aw3::armed) task_aw3::handoff();'
    new = '        if (task_aw3::armed) {\n            if (task_aw5::selected()) task_aw5::handoff();\n            task_aw3::handoff();\n        }'
    if new not in text:
        assert text.count(old) == 1
        patch_file(setup, text.replace(old, new))
    output = ROOT / 'local/task-aw5'
    output.mkdir(exist_ok=True)
    (output / 'installation.json').write_text(json.dumps({
        'capture_only': True, 'AX_activation': False,
        'sources': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                    for name in ['aw4/reconcile.h', 'aw5/capture.h', 'brainage_task_au.h', 'task_au_setup.inc']}
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
