"""Install dormant task-scoped ownership hooks. No runner launch or activation."""
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
    subprocess.run([str(Path.home() / 'AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'),
                    '--codex-run-as-apply-patch', patch + '*** End Patch\n'], check=True)


def main():
    output = ROOT / 'local/task-aw7'
    output.mkdir(exist_ok=True)
    protected = ['brainage_task_au.h', 'task_au_setup.inc', 'tier3.cpp']
    before = {name: (SOURCE / name).read_text(encoding='utf-8-sig') for name in protected}
    assert '#include "aw5/capture.h"' in before['brainage_task_au.h']
    for name in ['prefix.h']:
        patch_file(SOURCE / 'aw6' / name, (ROOT / 'tools/task_aw6' / name).read_text())
    patch_file(SOURCE / 'aw7/integration.h', (ROOT / 'tools/task_aw7/integration.h').read_text())
    text = before['brainage_task_au.h']
    if '#include "aw7/integration.h"' not in text:
        text = '#include "aw7/integration.h"\n' + text
    patch_file(SOURCE / 'brainage_task_au.h', text)
    text = before['task_au_setup.inc']
    early = '    if (task_aw7::owns()) { task_aw7::check_dispatch(); return 0; }\n'
    if early not in text:
        text = text.replace('template<class CPU> inline int au_control(CPU& cpu){\n', 'template<class CPU> inline int au_control(CPU& cpu){\n' + early)
    handoff = '        if (task_aw7::waiting()) { task_aw7::handoff(); return 0; }\n'
    if handoff not in text:
        anchor = '        if (task_aw3::armed) {'
        assert text.count(anchor) == 1
        text = text.replace(anchor, handoff + anchor)
    patch_file(SOURCE / 'task_au_setup.inc', text)
    text = before['tier3.cpp']
    original = 'if (task_aw3::armed && ic.R[15]==0x02001980)'
    replacement = 'if (task_aw3::armed && !task_aw7::owns() && ic.R[15]==0x02001980)'
    if replacement not in text:
        assert text.count(original) == 1
        text = text.replace(original, replacement)
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if 'override {' not in line or 'task_aw7::owns()' in line:
            continue
        for width, kind in [(8, 'read'), (16, 'read'), (32, 'read'), (8, 'write'), (16, 'write'), (32, 'write')]:
            if not line.strip().startswith(('uint8_t', 'uint16_t', 'uint32_t', 'void')) or kind + str(width) not in line.split('override')[0]:
                continue
            size = width // 8
            callback = f'bus_read_u{width}(a)' if kind == 'read' else f'(bus_write_u{width}(a, v), uint32_t(v))'
            route = f' if (task_aw7::owns()) '
            route += ('return ' if kind == 'read' else '{ ')
            route += f'task_aw7::runtime_access(g_cpu.R[15],a,{size},' + ('0,false' if kind == 'read' else 'v,true') + f',[&] {{ return {callback}; }});'
            if kind == 'write':
                route += ' return; }'
            lines[index] = line.replace('override {', 'override {' + route, 1)
    patch_file(SOURCE / 'tier3.cpp', '\n'.join(lines) + '\n')
    record = output / 'installation.json'
    if not record.exists():
        record.write_text(json.dumps({'before': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in before.items()},
                                     'after': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in protected},
                                     'dynamic_execution_ready': False, 'activation_installed': False}, indent=2) + '\n')


if __name__ == '__main__':
    main()
