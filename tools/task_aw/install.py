"""Install inert diagnostic facilities; never arm, launch, or permit AU MMIO."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'local/ndsrecomp/runner/src'
HERE = Path(__file__).resolve().parent
BASE = '3a57236bb23d25dcb4caad7d58d733311062ff5e'


def once(text, anchor, replacement):
    if replacement in text:
        return text
    if text.count(anchor) != 1:
        raise RuntimeError(f'nonunique/missing source anchor: {anchor[:100]}')
    return text.replace(anchor, replacement)


def install():
    assert subprocess.check_output(['git', '-C', str(SOURCE.parents[1]),
                                    'rev-parse', 'HEAD'], text=True).strip() == BASE
    updated = {}
    for name in ['tier3.cpp', 'runtime_arm.cpp', 'scheduler.cpp', 'io.cpp', 'bus.cpp']:
        text = (SOURCE / name).read_text(encoding='utf-8-sig').replace('\ufeff','')
        include = '#include "task_aw_bridge.h"\n#include "savestate.h"\n'
        if '#include "task_aw_bridge.h"' not in text:
            text = include + text
        updated[name] = text
    text = updated['tier3.cpp']
    if '#include "task_aw_passive.h"' not in text:
        text = '#include "task_aw_passive.h"\n' + text
    anchor = '        if (brainage_task_au::control(ic) == 2)'
    text = once(text, anchor,
                '        task_aw::emit(task_aw::Kind::instruction, ic.R[15]);\n' + anchor)
    for bits in (8, 16, 32):
        width = bits // 8
        anchor = f'return bus_read_u{bits}(a);'
        replacement = (f'task_aw::emit(task_aw::Kind::access_before,g_cpu.R[15],a,{width}); '
                       f'const auto aw_value=bus_read_u{bits}(a); '
                       f'task_aw::emit(task_aw::Kind::access_after,g_cpu.R[15],a,{width},aw_value); '
                       'return aw_value;')
        text = once(text, anchor, replacement)
        anchor = f'bus_write_u{bits}(a, v);'
        text = once(text, anchor,
                    f'task_aw::emit(task_aw::Kind::access_before,g_cpu.R[15],a,{width},v,true); '
                    + anchor + f' task_aw::emit(task_aw::Kind::access_after,g_cpu.R[15],a,{width},v,true);')
    anchor = '        g_runtime_cycles += cyc + runtime_deferred_cycles_take();'
    text = once(text, anchor, anchor + '\n        if (task_aw::enabled()) { sync_out(ic); task_aw::emit(task_aw::Kind::cycle_commit,pc,0,0,cyc); }')
    anchor = '        // Deliver a pending IRQ to the interpreted CPU (vectors to the BIOS'
    text = once(text, anchor,
                '        if (task_aw::enabled()) { sync_out(ic); task_aw::emit(task_aw::Kind::retired,pc); }\n\n' + anchor)
    updated['tier3.cpp'] = text
    text = updated['scheduler.cpp']
    for anchor, event in [
        ('void scheduler_run_round() {', 'task_aw::emit(task_aw::Kind::scheduler);'),
        ('    nds_tick_timers(0, g_slot[0].cycles);', 'task_aw::emit(task_aw::Kind::device);'),
    ]:
        text = once(text, anchor, anchor + '\n    ' + event if anchor.endswith('{')
                    else '    ' + event + '\n' + anchor)
    anchor = 'void run_slice(int cpu, uint32_t quantum) {'
    text = once(text, anchor, anchor + '\n    if (cpu == 1) task_aw::emit(task_aw::Kind::arm7);')
    updated['scheduler.cpp'] = text
    text = updated['io.cpp']
    for anchor, event in [
        ('void nds_note_irq_accept(int cpu, uint32_t return_address) {', 'irq'),
        ('void nds_run_system_events(uint64_t timestamp) {', 'device'),
        ('void nds_tick_timers(int cpu, unsigned long long cpu_cycles) {', 'device'),
        ('void nds_tick_rtc(unsigned long long system_cycles) {', 'device'),
    ]:
        text = once(text, anchor, anchor + f'\n    task_aw::emit(task_aw::Kind::{event});')
    updated['io.cpp'] = text
    text = updated['runtime_arm.cpp']
    anchor = '        g_cycle_cap = cpu_deadline;'
    text = once(text, anchor, anchor + '\n        task_aw::emit(task_aw::Kind::cap_change,g_cpu.R[15]);')
    updated['runtime_arm.cpp'] = text
    for name, provider in [('runtime_arm.cpp', 'runtime'), ('scheduler.cpp', 'scheduler'),
                           ('bus.cpp', 'bus'), ('io.cpp', 'io')]:
        inc = f'\n#include "task_aw_{provider}.inc"\n'
        if inc not in updated[name]:
            updated[name] += inc
    local = ROOT / 'local/task-aw'
    local.mkdir(parents=True, exist_ok=True)
    before = {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in updated}
    for name, text in updated.items():
        (SOURCE/name).write_text(text,encoding='utf-8')
    for name in ('bridge.h', 'passive.h', 'runtime.inc', 'scheduler.inc', 'bus.inc', 'io.inc'):
        (SOURCE / ('task_aw_' + name)).write_text((HERE/name).read_text(encoding='utf-8'),encoding='utf-8')
    (local/'installation.json').write_text(json.dumps({'baseline': BASE, 'before': before,
        'after': {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in updated},
        'armed': False, 'guest_execution': False}, indent=2)+'\n')
    print('AW inert observers/passive copies installed. No experiment activation exists.')


if __name__ == '__main__':
    install()
