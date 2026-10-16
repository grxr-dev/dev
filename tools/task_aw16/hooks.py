"""Reversible, ignored diagnostic overlay only. No installation or runner build."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def patch(original):
    prior = module('aw16_aw12_hooks', ROOT / 'tools/task_aw12/hooks.py')
    result = prior.patch_sources(original)
    for name in ['live_overlay.cpp', 'wifi_net.cpp']:
        result[name] = original[name]
    result['aw12/controller.h'] = (ROOT / 'tools/task_aw12/controller.h').read_text()
    changes = []
    def change(name, before, after, count=1):
        if result[name].count(before) != count:
            raise ValueError('AW16 ambiguous/missing anchor: ' + name + ': ' + before[:90])
        result[name] = result[name].replace(before, after)
        changes.append((name, before, after, count))
    change('aw12/controller.h', '#include "gpu.h"', '#include "gpu.h"\n#include "aw16/forward.h"')
    change('aw12/controller.h', 'disposed,failed };', 'disposed,failed,transferred };')
    change('aw12/controller.h', 'class Controller {', 'class Controller {\n    friend class task_aw16::Controller;')
    before = '        stop(true,"AW12 pre-device capture complete; no service/new slice/guest re-entry");'
    change('aw12/controller.h', before,
           '#if defined(AW16_DIAGNOSTIC_TAIL)\n'
           '        if (task_aw16::receive_fence(output,state,gpu,ticket,bound_frame,cursor,previous)) return;\n'
           '#endif\n' + before)
    for name in ['scheduler.cpp', 'gpu3d.cpp', 'runtime_arm.cpp', 'tier3.cpp', 'live_overlay.cpp', 'wifi_net.cpp']:
        change(name, result[name].splitlines()[0] + '\n', '#include "aw16/controller.h"\n' + result[name].splitlines()[0] + '\n')
    change('scheduler.cpp', 'void run_slice(int cpu, uint32_t quantum) {',
           'void run_slice(int cpu, uint32_t quantum) {\n    task_aw16::slice_gate(cpu,quantum);')
    change('scheduler.cpp', '    nds_slice_begin(cap);', '    nds_slice_begin(cap);\n    task_aw16::slice_begun(cpu,quantum);')
    change('scheduler.cpp', '~RoundActivityGuard() { g_round_active = false; }',
           '~RoundActivityGuard() { g_round_active = false; task_aw16::mark("round_left"); }')
    change('scheduler.cpp', '    RoundActivityGuard round_activity;',
           '    RoundActivityGuard round_activity;\n    task_aw16::mark("round_entered");')
    anchor = '    if (task_aw3::armed) { ++g_aw3_round_epoch; g_aw3_planned_target=arm9_target; g_aw3_next_event=ev; }'
    change('scheduler.cpp', anchor, anchor + '\n    task_aw16::mark("target_selected");')
    for before, label, count in [
        ('    nds_tick_timers(0, g_slot[0].cycles);', 'timers9_done', 1),
        ('    nds_gpu3d_run(g_slot[0].cycles);', 'gpu_done', 1),
        ('        run_slice(1, quantum);', 'arm7_done', 1),
        ('        nds_tick_timers(1, g_slot[1].cycles);', 'timers7_done', 1),
        ('        nds_tick_display(rendezvous);', 'display_done', 2),
        ('        nds_tick_spu(rendezvous);', 'spu_done', 2),
        ('        nds_wifi_run_events(rendezvous);', 'wifi_done', 2),
        ('        nds_tick_rtc(rendezvous);', 'rtc_done', 2),
        ('        nds_run_system_events(rendezvous);', 'system_done', 2)]:
        indent = before[:len(before)-len(before.lstrip())]
        change('scheduler.cpp', before, before + '\n' + indent + 'task_aw16::mark("' + label + '");', count)
    anchor = '        g_sys_timestamp = rendezvous;\n        return;\n    }'
    change('scheduler.cpp', anchor, anchor + '\n    task_aw16::mark("power_checked");')
    change('scheduler.cpp', '    g_sys_timestamp = rendezvous;\n    live_overlay_poll();',
           '    g_sys_timestamp = rendezvous;\n    task_aw16::mark("time_published");\n    live_overlay_poll();\n    task_aw16::mark("overlay_done");')
    for name, provider in [('live_overlay.cpp', 'overlay.inc'), ('wifi_net.cpp', 'wifi.inc'),
                           ('gpu3d.cpp', 'trace.inc'), ('scheduler.cpp', 'scheduler.inc')]:
        addition = '\n' + (HERE / provider).read_text()
        change(name, result[name], result[name] + addition)
    reversed_result = dict(result)
    for name, before, after, count in reversed(changes):
        if reversed_result[name].count(after) != count:
            raise ValueError('AW16 inverse anchor: ' + name)
        reversed_result[name] = reversed_result[name].replace(after, before)
    prior_result = prior.patch_sources(original)
    for name in ['live_overlay.cpp', 'wifi_net.cpp']:
        prior_result[name] = original[name]
    prior_result['aw12/controller.h'] = (ROOT / 'tools/task_aw12/controller.h').read_text()
    if reversed_result != prior_result:
        raise ValueError('AW16 non-hook semantic drift')
    return result


def write_overlay(output, source):
    names = ['tier3.cpp', 'runtime_arm.cpp', 'scheduler.cpp', 'gpu3d.cpp', 'aw7/integration.h',
             'brainage_task_au.h', 'live_overlay.cpp', 'wifi_net.cpp']
    original = {name: (source / name).read_text(encoding='utf-8-sig') for name in names}
    result = patch(original)
    for name, text in result.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    for folder, names in [('aw12', ['gpu.h']), ('aw16', ['forward.h', 'auxiliary.h', 'plan.h', 'controller.h'])]:
        (output / folder).mkdir(exist_ok=True)
        for name in names:
            (output / folder / name).write_bytes((ROOT / 'tools' / ('task_' + folder) / name).read_bytes())
    return original, result
