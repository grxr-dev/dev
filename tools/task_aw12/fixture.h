#pragma once
#include <fstream>
#include <iostream>
#include <cstring>
#include <set>
#include "aw12/controller.h"
#include "vendor/melonds/FIFO.h"

namespace rail {
using task_aw2::Snapshot;
using task_aw2::require;
inline Snapshot baseline,initial;
inline std::string mode;
inline unsigned dispatches=0,services=0;
inline constexpr int NDS_ARM9=0,NDS_ARM7=1,CPSR_T_BIT=32,CPSR_I_BIT=128;
inline constexpr int NDS_EMU_EXEC_ARM9=0,NDS_EMU_EXEC_ARM7=1,NDS_DISPATCH_CLASS_RESUME=0;
struct NdsEmuScope { explicit NdsEmuScope(int) {} };
struct Cpu { uint32_t R[16]{}; uint32_t cpsr=31; uint32_t banked_sentinel[32]{}; };
inline Cpu g_cpu,g_preserved_unwind_state;
inline bool g_preserved_unwind_state_valid=false;
inline uint64_t g_runtime_cycles=0,g_cycle_cap=0,g_nds_fast_limit=0,g_insn_count[2]{};
inline uint64_t g_nds_force_tier3_misses=0,g_nds_fast_limit_publishes=0;
inline bool g_nds_terminal=false,g_nds_insn_stop=false,g_nds_force_tier3=true,g_cpu_fast_poll=true,g_cycle_fast_limit_enabled=true;
inline uint32_t g_nds_unwinding=0,g_yield_poll_hint=1,g_deferred_cycles=0,g_runtime_break_pc=0,g_crs_depth=0,g_crs[32]{};
inline int g_nds_active=0;
inline const char* g_nds_halt_reason=nullptr;
inline void* g_static_guard=nullptr;
inline void* g_tail_dispatch=nullptr;
struct Context { uint64_t dispatch_epoch=0; };
inline Context g_ctx[2];
inline bool event_break=false;
inline bool nds_event_break_hit() { return event_break; }
inline bool active_static_code_changed() { return baseline.get("hidden.static_changed"); }
inline void* lookup_static(const Context&,uint32_t pc,bool,void*,void*) {
    return baseline.get(task_aw2::address_key("hidden.bank.",pc)) ? reinterpret_cast<void*>(uintptr_t(1)) : nullptr;
}
struct Slot { uint64_t cycles=0; uint32_t deferred_cycles=0; bool halted=false,started=true; const char* reason=nullptr; };
inline Slot g_slot[2];
inline int g_cur=0;
inline std::thread::id g_owner_thread;
inline bool g_round_active=true;
inline uint64_t g_sys_timestamp=0,g_aw3_round_epoch=0,g_aw3_planned_target=0,g_aw3_next_event=0;
struct NdsSpuSaveState { uint64_t mix_count=0; };
inline bool spu_savestate_export(NdsSpuSaveState* state) { state->mix_count=baseline.get("service.spu_mixes"); return true; }
inline uint64_t nds_wifi_next_event_time() { return baseline.get("wifi.deadline"); }
struct Entry { uint32_t Param=0; uint8_t Command=0; };
struct Gpu {
    bool GeometryEnabled=true;
    uint32_t FlushRequest=0,GXStat=0,NumPushPopCommands=0,NumTestCommands=0,ExecParamCount=0,VertexSlotsFree=0;
    int32_t CycleCount=0,VertexPipeline=0,NormalPipeline=0,PolygonPipeline=0,VertexSlotCounter=0;
    uint64_t Timestamp=1708437825;
    melonDS::FIFO<Entry,4> CmdPIPE;
    melonDS::FIFO<Entry,256> CmdFIFO;
    melonDS::FIFO<Entry,64> CmdStallQueue;
};
inline struct Console { struct Geometry { Gpu GPU3D; } GPU; uint64_t ARM9Timestamp=3416875650ULL; unsigned ARM9ClockShift=1; } g_nds;
inline int32_t nds_gpu3d_cycles_to_run() { return g_nds.GPU.GPU3D.CycleCount>0 ? g_nds.GPU.GPU3D.CycleCount : 0; }
inline void switch_to(int) {}
inline bool nds_dma_cpu_stalled(int cpu) {
    for (unsigned index=cpu*4;index<cpu*4+4;++index)
        if (baseline.get("dma."+std::to_string(index)+".active")) return true;
    return false;
}
inline void forbidden_service() { ++services; std::fputs("SERVICE_SENTINEL",stderr); std::_Exit(91); }
inline void nds_dma_run(int,uint64_t) { forbidden_service(); }
inline bool nds_cpu_halted(int cpu) { return baseline.get(cpu ? "halt7" : "halt9"); }
inline bool nds_halt_wake_pending(int cpu) {
    const auto prefix=cpu ? "irq7." : "irq9.";
    return (baseline.get(std::string(prefix)+"ie")&baseline.get(std::string(prefix)+"if"))!=0;
}
inline void nds_slice_begin(uint64_t cap) { g_cycle_cap=cap; }
inline bool nds_slice_over() { return g_cycle_cap && g_runtime_cycles>=g_cycle_cap; }
inline void nds_cpu_wake(int) { forbidden_service(); }
inline bool nds_irq_pending(int cpu) { return nds_halt_wake_pending(cpu); }
inline void runtime_irq(uint32_t) { forbidden_service(); }
inline void nds_dispatch_tag(int) {}
inline struct Stats { uint64_t resume_dispatch=0; } g_nds_dispatch_stats[2];
inline uint64_t nds_dma_entry_cycle(int) { return 0; }
inline uint64_t nds_halt_entry_cycle(int cpu) { return baseline.get("service.halt_epoch."+std::to_string(cpu)); }
inline void runtime_deferred_cycles_set(uint32_t value) { g_deferred_cycles=value; }
inline uint32_t runtime_deferred_cycles() { return g_deferred_cycles; }
inline void sync_out(const Cpu& state) { g_cpu=state; }
inline void runtime_dispatch(uint32_t);
inline void nds_tick_timers(int,uint64_t) { forbidden_service(); }
inline void nds_gpu3d_run(uint64_t) { forbidden_service(); }
#include "runtime_unwind.inc"
#include "run_slice.inc"
}

namespace task_aw3 {
using namespace rail;
using rail::g_insn_count;
using rail::g_nds_insn_stop;
using rail::nds_event_break_hit;
#include "runtime_getter.inc"
#include "scheduler_getter.inc"
inline void immutable_group(Snapshot& out) {
    static const std::set<std::string> keys={
#include "immutable_keys.inc"
    };
    for (const auto& name:keys) {
        require(!out.fields.count(name),"fixture immutable/mutable owner overlap");
        out.fields[name]=rail::baseline.fields.at(name);
    }
    out.hashes=rail::baseline.hashes;
}
inline void bus_snapshot(Snapshot& out) { immutable_group(out); }
inline void io_snapshot(Snapshot&) {}
inline void cp15_snapshot(Snapshot&) {}
}

namespace task_aw12 {
using namespace rail;
#include "gpu_facade.inc"
#include "saved_facade.inc"
}

#include "aw7/integration.h"

namespace rail {
inline task_aw2::Snapshot core_source() {
    auto actual=task_aw3::passive();
    if (mode=="omit-core") actual.fields.erase("cp15.control");
    return actual;
}
inline task_aw2::Snapshot gpu_source() {
    auto actual=task_aw12::runtime_gpu_observation();
    if (mode=="omit-gpu") actual.fields.erase("gpu.geometry");
    if (mode=="gpu-width") actual.fields.at("gpu.cycles").width=8;
    if (mode=="duplicate-fence") task_aw12::pre_device_fence();
    if (mode=="gpu-torn") ++g_nds.GPU.GPU3D.Timestamp;
    return actual;
}
inline void fault_after_offer() {
    if (mode=="duplicate-offer") task_aw12::offer(core_source());
    if (mode=="stale-after") ++task_aw3::epoch;
    if (mode=="frame-serial") ++task_aw12::frame->serial;
    if (mode=="forbidden-fetch") task_aw12::guard_guest();
    if (mode=="reorder") task_aw12::slice_saved(0);
    if (mode=="early-fence") task_aw12::pre_device_fence();
    if (mode=="irq") baseline.fields.at("irq9.if").value|=baseline.get("irq9.ie");
    if (mode=="arm7") ++g_slot[1].deferred_cycles;
    if (mode=="scheduler") g_aw3_next_event=g_sys_timestamp;
    if (mode=="device") baseline.fields.at("card.deadline").value=g_sys_timestamp;
    if (mode=="timer") baseline.fields.at("timer.0.counter").value^=1;
    if (mode=="hint") g_yield_poll_hint^=1;
    if (mode=="bank") baseline.fields.at(task_aw2::address_key("hidden.bank.",0x020019b4)).value^=1;
    if (mode=="journal") ++task_aw3::history.back().serial;
    if (mode=="thread") { std::thread other([] { task_aw12::tier3_exit(); }); other.join(); }
    if (mode=="cost-drift") ++g_runtime_cycles;
    if (mode=="duplicate-exit") task_aw12::tier3_exit();
    if (mode=="unexpected-service") task_aw::emit(task_aw::Kind::device);
    if (mode=="unexpected-arm7") task_aw::emit(task_aw::Kind::arm7);
    if (mode=="unexpected-irq") task_aw::emit(task_aw::Kind::irq);
}
inline void interpreted_return() {
    Cpu ic=g_cpu;
    for (;;) {
        if (mode=="skip-exit") break;
#include "tier3_exit.inc"
        break;
    }
    if (mode=="saved-corrupt") g_preserved_unwind_state.R[4]^=1;
}
struct DisabledRedispatch {};
inline void runtime_dispatch(uint32_t) {
    task_aw12::Frame aw12_frame(g_static_guard!=nullptr,g_tail_dispatch!=nullptr);
    if (++dispatches>1) {
        if (mode=="disabled") throw DisabledRedispatch{};
        forbidden_service();
    }
    g_runtime_cycles=baseline.get("cycle9");
    if (mode=="disabled") return;
    if (mode=="cap-short") --g_cycle_cap;
    if (mode=="cap-long") ++g_cycle_cap;
    task_aw::Event retired{task_aw::Kind::retired,0x020019b0};
    if (mode=="nested") { task_aw12::Frame nested(false,true); task_aw7::receive(retired); }
    else task_aw7::receive(retired);
    fault_after_offer();
    interpreted_return();
}
inline void scheduler_boundary() {
    if (mode=="missing-fence") { task_aw::emit(task_aw::Kind::device); forbidden_service(); }
#include "fence.inc"
    forbidden_service();
}
inline void begin(const Snapshot& terminal) {
    baseline=terminal; g_owner_thread=std::this_thread::get_id();
    g_sys_timestamp=terminal.get("system_timestamp"); g_cur=terminal.get("current_slot");
    g_round_active=terminal.get("round_active"); g_nds_active=terminal.get("active_cpu");
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=terminal.get("r"+std::to_string(index));
    g_cpu.cpsr=terminal.get("cpsr");
    for (unsigned index=0;index<32;++index) g_cpu.banked_sentinel[index]=index*7919+17;
    g_runtime_cycles=terminal.get("cycle9"); g_cycle_cap=terminal.get("slice_cap"); g_nds_fast_limit=terminal.get("fast_limit");
    g_insn_count[0]=terminal.get("ordinal9"); g_insn_count[1]=terminal.get("ordinal7");
    g_yield_poll_hint=terminal.get("hidden.yield"); g_deferred_cycles=terminal.get("deferred9");
    g_nds_force_tier3=terminal.get("force_tier3"); g_cpu_fast_poll=terminal.get("hidden.cpu_poll");
    g_cycle_fast_limit_enabled=terminal.get("hidden.fast_enabled"); g_nds_force_tier3_misses=terminal.get("hidden.force_misses");
    g_nds_fast_limit_publishes=terminal.get("hidden.fast_publishes"); g_runtime_break_pc=terminal.get("hidden.break_pc");
    g_ctx[0].dispatch_epoch=terminal.get("hidden.dispatch_epoch");
    g_crs_depth=terminal.get("return_depth");
    for (unsigned index=0;index<g_crs_depth;++index) g_crs[index]=terminal.get("return."+std::to_string(index));
    g_aw3_round_epoch=terminal.get("scheduler.round_epoch"); g_aw3_planned_target=terminal.get("scheduler.planned_target");
    g_aw3_next_event=terminal.get("scheduler.next_event");
    for (unsigned cpu=0;cpu<2;++cpu) {
        g_slot[cpu].cycles=terminal.get(cpu ? "cycle7" : "slot9.cycle");
        g_slot[cpu].deferred_cycles=terminal.get(cpu ? "deferred7" : "slot9.deferred");
        g_slot[cpu].started=terminal.get("scheduler.started."+std::to_string(cpu));
        g_slot[cpu].halted=terminal.get("scheduler.halted."+std::to_string(cpu));
    }
    task_aw3::armed=true; task_aw3::owner=std::this_thread::get_id();
    task_aw3::epoch=terminal.get("capture.epoch"); task_aw3::serial=terminal.get("capture.serial");
    task_aw3::rom_epoch=terminal.get("capture.rom_epoch");
    for (unsigned index=0;index<terminal.get("cap.count");++index) {
        const auto prefix="cap."+std::to_string(index)+".";
        task_aw3::history.push_back({task_aw3::epoch,terminal.get(prefix+"serial"),terminal.get(prefix+"cycle"),
            terminal.get(prefix+"observed_before"),terminal.get(prefix+"after"),terminal.get(prefix+"deadline"),
            uint32_t(terminal.get(prefix+"cpu")),uint32_t(terminal.get(prefix+"kind"))});
    }
    require(task_aw3::passive()==terminal,"actual mutable getters reproduce all 411 terminal fields");
}
}
