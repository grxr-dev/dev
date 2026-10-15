#pragma once
#include "prefix.h"

namespace aw6_source {
inline task_aw2::Snapshot working;
inline constexpr unsigned NDS_ARM9=0;
inline unsigned g_nds_active=0;
inline uint64_t g_runtime_cycles=0,g_cycle_cap=0,g_nds_fast_limit=0;
inline uint16_t g_divcnt=0,g_sqrtcnt=0;
inline uint64_t g_div_deadline=0;
inline uint32_t g_div_numer[2]{},g_div_denom[2]{};
inline uint32_t g_sqrt_val[2]{};
inline uint32_t g_yield_poll_hint=0,g_deferred_cycles=0;
inline bool g_nds_terminal=false;
inline bool g_cycle_fast_limit_enabled=true,g_cpu_fast_poll=true,g_nds_insn_stop=false;
inline uint32_t g_runtime_break_pc=0,g_nds_irq_pending_cache[2]{};
inline uint64_t g_nds_fast_limit_publishes=0;
inline uint32_t g_ie[2]{},g_if[2]{},g_ime[2]{};
inline const uint32_t kPrescaler[4]={1,64,256,1024};
inline struct Timer { uint16_t ctrl=0,counter=0; uint64_t accum=0; } g_timer[2][4];
inline uint64_t g_timer_last[2]{};
inline struct { uint32_t R[16]{}; } g_cpu;
inline void start_sqrt() { std::abort(); }
inline bool active_static_code_changed() { return working.get("hidden.static_changed"); }
inline bool nds_event_break_hit() { return working.get("event_break"); }
inline bool nds_cpu_halted(unsigned) { return working.get("halt9"); }
inline bool nds_dma_cpu_stalled(unsigned) { return working.get("dma.0.active") || working.get("dma.1.active") || working.get("dma.2.active") || working.get("dma.3.active"); }
enum class Arm9CodeTiming { Itcm,Cached,MainRam,Other };
inline Arm9CodeTiming arm9_latch_code_timing(uint32_t address) {
    task_aw2::code_cost(working,address);
    return Arm9CodeTiming::Cached;
}
#include "source_model.inc"

inline void begin(const task_aw2::Snapshot& initial) {
    working=initial;
    g_nds_active=0;
    g_runtime_cycles=initial.get("cap.0.cycle");
    g_cycle_cap=initial.get("cap.0.observed_before");
    task_aw3::armed=true; task_aw3::bound=false; task_aw3::owner=std::this_thread::get_id();
    task_aw3::epoch=initial.get("capture.epoch")-1; task_aw3::serial=initial.get("capture.serial")-1;
    task_aw3::rom_epoch=initial.get("capture.rom_epoch"); task_aw3::history.clear(); task_aw3::sticky.clear();
    task_aw3::rom_identity=initial.hashes.at("rom");
    nds_slice_begin(initial.get("slice_cap"));
    g_runtime_cycles=initial.get("cycle9");
    g_nds_fast_limit=initial.get("fast_limit");
    g_deferred_cycles=initial.get("deferred9");
    g_nds_fast_limit_publishes=initial.get("hidden.fast_publishes");
    g_divcnt=initial.get("div.control"); g_div_deadline=initial.get("div.deadline");
    g_div_numer[0]=initial.get("div.nlo"); g_div_numer[1]=initial.get("div.nhi");
    g_div_denom[0]=initial.get("div.dlo"); g_div_denom[1]=initial.get("div.dhi");
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=initial.get("r"+std::to_string(index));
    for (unsigned cpu=0;cpu<2;++cpu) {
        const auto irq=task_aw2::numbered("irq",cpu ? 7 : 9)+".";
        g_ie[cpu]=initial.get(irq+"ie"); g_if[cpu]=initial.get(irq+"if"); g_ime[cpu]=initial.get(irq+"ime");
        for (unsigned index=0;index<4;++index) {
            const auto prefix=task_aw2::numbered("timer.",cpu*4+index)+".";
            g_timer[cpu][index].ctrl=initial.get(prefix+"control");
            g_timer[cpu][index].counter=initial.get(prefix+"counter");
            g_timer[cpu][index].accum=initial.get(prefix+"accum");
            g_timer_last[cpu]=initial.get(prefix+"last");
        }
    }
    task_aw2::require(g_yield_poll_hint==initial.get("hidden.yield"),"real slice begin preserves captured hint");
}
inline task_aw2::Snapshot sample() {
    auto result=working;
    task_aw3::export_history(result);
    result.put("cycle9",8,g_runtime_cycles); result.put("capture.end_cycle",8,g_runtime_cycles);
    result.put("slice_cap",8,g_cycle_cap); result.put("fast_limit",8,g_nds_fast_limit);
    result.put("hidden.yield",4,g_yield_poll_hint); result.put("deferred9",4,g_deferred_cycles);
    result.put("hidden.fast_publishes",8,g_nds_fast_limit_publishes);
    result.put("div.control",2,g_divcnt); result.put("div.deadline",8,g_div_deadline);
    result.put("div.nlo",4,g_div_numer[0]); result.put("div.nhi",4,g_div_numer[1]);
    result.put("div.dlo",4,g_div_denom[0]); result.put("div.dhi",4,g_div_denom[1]);
    for (unsigned index=0;index<16;++index) result.put("r"+std::to_string(index),4,g_cpu.R[index]);
    return result;
}
}
