"""File-only source/authority continuity review. Does not open ROM/save/checkpoint images."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'local/ndsrecomp/runner/src'
HERE = Path(__file__).resolve().parent


def main():
    assert subprocess.check_output(['git', '-C', str(SOURCE.parents[1]), 'rev-parse', 'HEAD'],
                                   text=True).strip() == '3a57236bb23d25dcb4caad7d58d733311062ff5e'
    aw = json.loads((ROOT/'docs/BrainAge_TaskAW_Result.json').read_text())
    hashes = {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()
              for name in ['tier3.cpp', 'runtime_arm.cpp', 'scheduler.cpp', 'bus.cpp', 'io.cpp', 'cp15.cpp']}
    for name, expected in aw['source_sha256'].items():
        assert hashes[name] == expected, f'AW source continuity: {name}'
    installation = json.loads((ROOT/'local/task-aw/installation.json').read_text())
    assert all(hashes[name] == expected for name, expected in installation['after'].items())
    tier3 = (SOURCE/'tier3.cpp').read_text(encoding='utf-8-sig')
    runtime = (SOURCE/'runtime_arm.cpp').read_text(encoding='utf-8-sig')
    scheduler = (SOURCE/'scheduler.cpp').read_text(encoding='utf-8-sig')
    io = (SOURCE/'io.cpp').read_text(encoding='utf-8-sig')
    assert tier3.index('Kind::instruction') < tier3.index('brainage_task_au::control(ic)') < tier3.index('const uint32_t code_correction')
    assert tier3.index('Kind::retired') < tier3.index('// Deliver a pending IRQ')
    assert runtime.index('g_cycle_cap = cpu_deadline;') < runtime.index('Kind::cap_change') < runtime.index('g_nds_fast_limit = 0u;', runtime.index('Kind::cap_change'))
    assert scheduler.index('task_aw::emit(task_aw::Kind::device);') < scheduler.index('nds_tick_timers(0, g_slot[0].cycles);') < scheduler.index('const uint64_t rendezvous')
    assert 'g_slot[1].cycles < rendezvous' in scheduler
    assert 'g_div_deadline = active_system_timestamp() +' in io and 'nds_reschedule_slice(g_div_deadline);' in io
    au_control = (ROOT/'tools/task_au/setup.inc').read_text()
    assert 'AU forbidden STRH not dispatched' in au_control and 'done=true;finish(0);return 2;' in au_control
    au_finish = (ROOT/'tools/task_au/diagnostic.h').read_text()
    assert 'nds_halt(code==0?' in au_finish
    controller = (HERE/'controller.h').read_text()
    assert 'task_aw::dispose' in controller and 'nds_halt(' not in controller
    assert 'std::getenv' not in controller and 'brainage_task_au' not in controller
    observed = (HERE/'observed_timing.h').read_text()
    assert all(term not in observed for term in ['reinterpret_cast', 'memcpy', 'runtime_code_cycles(', 'runtime_mem_cycles(', 'cp15_savestate_import('])
    result = {
        'source_hashes': hashes, 'AW_runtime_sources_unchanged': True,
        'AU_stop_and_denial_guards_unchanged': True,
        'observer_before_AU_guard_and_fetch': True, 'retired_before_IRQ': True,
        'actual_cap_observer_before_remaining_reschedule_body': True,
        'scheduler_tail_and_ARM7_catchup_still_exist': True,
        'no_AX_runtime_installation_or_activation': True,
        'canonical_timing_capture_uses_typed_fields_only': True,
        'AX_certificate_issued': False,
    }
    output = ROOT/'local/task-aw2/retry-20261013/source-review.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
