"""Checked, reversible private diagnostic overlay. Never install or activate a runner."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('AW12 hook anchor missing/ambiguous: ' + before[:90])
    return text.replace(before, after, 1)


def patch_sources(original):
    result = dict(original)
    edits = {}
    def change(name, before, after):
        result[name] = once(result[name], before, after)
        edits.setdefault(name, []).append((before, after))
    for name in ['tier3.cpp', 'runtime_arm.cpp', 'scheduler.cpp', 'gpu3d.cpp', 'aw7/integration.h']:
        change(name, result[name].splitlines()[0] + '\n', '#include "aw12/controller.h"\n' + result[name].splitlines()[0] + '\n')
    change('aw7/integration.h',
           '            task_aw3::audit_text("terminal","AW7 reduced owner complete;',
           '            if (task_aw12::offer(state)) return;\n            task_aw3::audit_text("terminal","AW7 reduced owner complete;')
    change('tier3.cpp', '        task_aw::emit(task_aw::Kind::instruction, ic.R[15]);',
           '        task_aw12::guard_guest();\n        task_aw::emit(task_aw::Kind::instruction, ic.R[15]);')
    retired = '        if (task_aw::enabled()) { sync_out(ic); task_aw::emit(task_aw::Kind::retired,pc); }'
    change('tier3.cpp', retired, retired + '\n        if (task_aw12::tier3_exit()) { sync_out(ic); nds_preserve_unwind_state(); task_aw12::preserved(); break; }')
    change('runtime_arm.cpp', 'void runtime_dispatch_impl(uint32_t target_pc, NdsLinkSlot* linked) {',
           'void runtime_dispatch_impl(uint32_t target_pc, NdsLinkSlot* linked) {\n    task_aw12::Frame aw12_frame(g_static_guard!=nullptr,g_tail_dispatch!=nullptr);')
    change('scheduler.cpp', '        nds_restore_unwind_state();',
           '        nds_restore_unwind_state();\n        if (task_aw12::slice_exit(cpu)) break;')
    change('scheduler.cpp', '    g_slot[cpu].deferred_cycles = runtime_deferred_cycles();\n}',
           '    g_slot[cpu].deferred_cycles = runtime_deferred_cycles();\n    task_aw12::slice_saved(cpu);\n}')
    change('scheduler.cpp', '    task_aw::emit(task_aw::Kind::device);\n    nds_tick_timers(0, g_slot[0].cycles);',
           '    task_aw12::pre_device_fence();\n    task_aw::emit(task_aw::Kind::device);\n    nds_tick_timers(0, g_slot[0].cycles);')
    result['gpu3d.cpp'] += '\nnamespace task_aw12 {\nSnapshot runtime_gpu_observation() {\n    return gpu_project(g_nds.GPU.GPU3D,g_nds.ARM9Timestamp,g_nds.ARM9ClockShift);\n}\n}\n'
    result['runtime_arm.cpp'] += '\nnamespace task_aw12 {\nbool runtime_saved_unwind() { return g_preserved_unwind_state_valid; }\n}\n'
    for name, values in edits.items():
        reverse = result[name]
        if name in ['gpu3d.cpp', 'runtime_arm.cpp']:
            reverse = reverse[:reverse.rindex('\nnamespace task_aw12 {')]
        for before, after in reversed(values):
            reverse = once(reverse, after, before)
        if reverse != original[name]:
            raise ValueError('AW12 non-hook source drift: ' + name)
    return result


def write_overlay(destination, source):
    names = ['tier3.cpp', 'runtime_arm.cpp', 'scheduler.cpp', 'gpu3d.cpp', 'aw7/integration.h', 'brainage_task_au.h']
    original = {name: (source / name).read_text(encoding='utf-8-sig') for name in names}
    result = patch_sources(original)
    for name, text in result.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    support = destination / 'aw12'
    support.mkdir()
    for name in ['gpu.h', 'controller.h']:
        (support / name).write_bytes((Path(__file__).parent / name).read_bytes())
    return original, result, {name: hashlib.sha256(text.encode()).hexdigest() for name, text in result.items()}
