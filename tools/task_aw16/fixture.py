"""Derive a source-coupled scalar rail; never import a runner or a guest image."""
from hooks import ROOT, HERE, module


def create(output, patched):
    parser = module('aw16_parser', ROOT / 'tools/task_aw6/check.py')
    prior = (ROOT / 'tools/task_aw12/fixture.h').read_text()
    prefix = prior[:prior.index('inline void fault_after_offer()')]
    prefix = prefix[:prefix.index('#include "aw7/integration.h"')]
    prefix = prefix.replace('#include "aw12/controller.h"', '#include "aw16/controller.h"')
    prefix = prefix.replace('struct Slot { uint64_t cycles=0;', 'struct Slot { Cpu state; uint64_t cycles=0;')
    prefix = '#include <chrono>\n' + prefix
    prefix = prefix.replace('inline bool spu_savestate_export(NdsSpuSaveState* state) { state->mix_count=baseline.get("service.spu_mixes"); return true; }',
                            'inline uint64_t g_mix_count=0;\ninline bool spu_savestate_export(NdsSpuSaveState* state) { state->mix_count=g_mix_count; return true; }')
    prefix = prefix.replace('inline uint64_t nds_wifi_next_event_time() { return baseline.get("wifi.deadline"); }','inline uint64_t nds_wifi_next_event_time();')
    prefix = prefix.replace('struct Gpu {', 'struct Gpu {\n    struct Clock { uint64_t& ARM9Timestamp; unsigned& ARM9ClockShift; } NDS;\n    Gpu(uint64_t& time,unsigned& shift):NDS{time,shift} {}\n    int32_t CyclesToRunFor() const noexcept;\n    void Run() noexcept;\n    void ExecuteCommand();\n    void FinishWork(int32_t);')
    before = 'inline struct Console { struct Geometry { Gpu GPU3D; } GPU; uint64_t ARM9Timestamp=3416875650ULL; unsigned ARM9ClockShift=1; } g_nds;'
    after = ('inline struct Console { uint64_t ARM9Timestamp=3416875650ULL; unsigned ARM9ClockShift=1; '
             'struct Geometry { Gpu GPU3D; Geometry(uint64_t& time,unsigned& shift):GPU3D(time,shift) {} } GPU; '
             'Console():GPU(ARM9Timestamp,ARM9ClockShift) {} } g_nds;')
    if before not in prefix:
        raise ValueError('AW12 fixture clock anchor')
    prefix = prefix.replace(before, after)
    before = 'inline void forbidden_service() { ++services; std::fputs("SERVICE_SENTINEL",stderr); std::_Exit(91); }'
    prefix = prefix.replace(before,'inline void forbidden_service() { ++services; if (task_aw16::current) task_aw16::current->fail("unexpected service sentinel"); task_aw3::fail("unexpected service without successor"); }')
    prefix = prefix.replace('inline void nds_slice_begin(uint64_t cap) { g_cycle_cap=cap; }',
        '#include "slice_runtime.inc"\ninline void nds_slice_begin(uint64_t cap) { if (task_aw16::current && task_aw16::current->active()) original_slice_begin(cap); else g_cycle_cap=cap; }')
    prefix = prefix.replace('inline void nds_tick_timers(int,uint64_t) { forbidden_service(); }\ninline void nds_gpu3d_run(uint64_t) { forbidden_service(); }', '#include "services.h"')
    prefix = prefix.replace('inline void io_snapshot(Snapshot&) {}','inline void io_snapshot(Snapshot& out) { rail::dynamic_io(out); }')
    begin = parser.function(prior, 'inline void begin(const Snapshot& terminal)')
    begin = begin.replace('    require(task_aw3::passive()==terminal,', '    services_begin(terminal);\n    require(task_aw3::passive()==terminal,')
    (output / 'fixture.h').write_text(prefix + '\nnamespace rail {\n' + begin + '\n}\n')
    fragments = [('timers.inc','io.cpp','void nds_tick_timers('),('display.inc','io.cpp','void nds_tick_display('),
        ('spu.inc','spu.cpp','void nds_tick_spu('),('rtc.inc','io.cpp','void nds_tick_rtc('),
        ('events.inc','io.cpp','void nds_run_system_events('),('system_deadline.inc','io.cpp','uint64_t nds_next_system_event_time()'),
        ('wifi_events.inc','wifi_net.cpp','uint64_t nds_wifi_next_event_time()'),('wifi_events.inc','wifi_net.cpp','void nds_wifi_run_events('),
        ('overlay_poll.inc','live_overlay.cpp','void live_overlay_poll()'),('gpu_run.inc','gpu3d.cpp','void nds_gpu3d_run('),
        ('trace_getters.inc','gpu3d.cpp','uint64_t nds_gpu3d_run_trace_count()'),('trace_getters.inc','gpu3d.cpp','bool nds_gpu3d_run_trace_get('),
        ('profile_modulus.inc','scheduler.cpp','uint64_t profile_modulus()'),('next_event.inc','scheduler.cpp','uint64_t next_scheduled_event_time()'),
        ('run_slice.inc','scheduler.cpp','void run_slice(int cpu, uint32_t quantum)'),('next_round.inc','scheduler.cpp','void scheduler_run_round()')]
    contents = {}
    source = ROOT / 'local/ndsrecomp/runner/src'
    for target, name, signature in fragments:
        text = patched[name] if name in patched else (source / name).read_text(encoding='utf-8-sig')
        contents.setdefault(target, []).append(parser.function(text, signature))
    for name, parts in contents.items():
        (output / name).write_text('\n'.join(parts) + '\n')
    runtime = patched['runtime_arm.cpp']
    (output / 'runtime_unwind.inc').write_text('\n'.join(parser.function(runtime, signature) for signature in [
        'extern "C" void nds_clear_unwinding(void)', 'void nds_preserve_unwind_state()', 'void nds_restore_unwind_state()']) + '\n')
    request = parser.function(runtime,'void request_yield_poll()')
    begin_slice = parser.function(runtime,'extern "C" void nds_slice_begin(').replace('extern "C" void nds_slice_begin(', 'inline void original_slice_begin(')
    (output / 'slice_runtime.inc').write_text(request + '\n' + begin_slice + '\n')
    scheduler = patched['scheduler.cpp']
    guard = scheduler[scheduler.index('struct RoundActivityGuard {'):scheduler.index('\nvoid save_current()')]
    (output / 'round_guard.inc').write_text(guard + '\n')
    start = scheduler.index('    task_aw12::pre_device_fence();')
    tail = scheduler[start:scheduler.index('\nvoid scheduler_terminal_halt_all')]
    (output / 'tail.inc').write_text('inline void tail_from_fence() {\n    const bool sample=false;\n    auto phase_start=ProfileClock::time_point{};\n    auto round_start=phase_start;\n' + tail)
    geometry = (source.parent / 'vendor/melonds/GPU3D.cpp').read_text()
    (output / 'gpu_methods.inc').write_text('\n'.join(parser.function(geometry, signature).replace('s32 GPU3D::','int32_t Gpu::').replace('void GPU3D::','void Gpu::')
        for signature in ['s32 GPU3D::CyclesToRunFor()', 'void GPU3D::Run()']) + '\n')
    for name in ['runtime','scheduler']:
        text = (ROOT / f'tools/task_aw3/{name}.inc').read_text()
        (output / f'{name}_getter.inc').write_text(parser.function(text,f'void {name}_snapshot(') + '\n')
    for name, source_name, signature in [('gpu_facade.inc','gpu3d.cpp','Snapshot runtime_gpu_observation()'),
                                         ('saved_facade.inc','runtime_arm.cpp','bool runtime_saved_unwind()')]:
        (output / name).write_text(parser.function(patched[source_name], signature) + '\n')
    for name in ['overlay','wifi','trace','scheduler']:
        text = (HERE / (name + '.inc')).read_text()
        body = parser.function(text,'void ' + ('trace_aux' if name=='trace' else name + '_aux') + '(')
        (output / (name + '_provider.inc')).write_text(body + '\n')
    return fragments
