#pragma once
#include <stdexcept>

namespace slice_rail {
constexpr uint32_t CPSR_I_BIT=128, CPSR_T_BIT=32;
constexpr int NDS_EMU_EXEC_ARM9=0,NDS_EMU_EXEC_ARM7=1,NDS_DISPATCH_CLASS_RESUME=0;
struct NdsEmuScope { explicit NdsEmuScope(int) {} };
struct Slot { bool halted=false; uint64_t cycles=0; uint32_t deferred_cycles=0; const char* reason=nullptr; };
struct Cpu { uint32_t R[16]{}; uint32_t cpsr=31; };
inline Slot g_slot[2];
inline Cpu g_cpu;
inline uint64_t g_runtime_cycles=0,cycle_cap=0;
inline bool g_nds_terminal=false,event_break=false,insn_stop=false,unwinding=false;
inline const char* g_nds_halt_reason=nullptr;
inline unsigned dispatches=0,irq_calls=0,dma_calls=0,slice_begins=0;
inline unsigned mode=0;
inline const task_aw2::Snapshot* profile=nullptr;
inline struct Stats { unsigned resume_dispatch=0; } g_nds_dispatch_stats[2];
struct Redispatch {};
inline void switch_to(int) {}
inline bool nds_dma_cpu_stalled(int cpu) { return profile->get("dma."+std::to_string(cpu*4)+".active"); }
inline void nds_dma_run(int,uint64_t) { ++dma_calls; throw std::runtime_error("unexpected DMA"); }
inline bool nds_cpu_halted(int cpu) { return profile->get(cpu ? "halt7" : "halt9"); }
inline bool nds_halt_wake_pending(int cpu) {
    const auto prefix=cpu ? "irq7." : "irq9.";
    return (profile->get(std::string(prefix)+"ie")&profile->get(std::string(prefix)+"if"))!=0;
}
inline void nds_slice_begin(uint64_t cap) { ++slice_begins; cycle_cap=cap; }
inline void nds_cpu_wake(int) { throw std::runtime_error("unexpected wake"); }
inline bool nds_irq_pending(int cpu) {
    const auto prefix=cpu ? "irq7." : "irq9.";
    return (profile->get(std::string(prefix)+"ime")&1) && nds_halt_wake_pending(cpu);
}
inline void runtime_irq(uint32_t) { ++irq_calls; throw std::runtime_error("unexpected IRQ"); }
inline void nds_clear_unwinding() { unwinding=false; }
inline void nds_dispatch_tag(int) {}
inline void runtime_dispatch(uint32_t) {
    ++dispatches;
    if (dispatches>1) throw Redispatch{};
    g_runtime_cycles=profile->get("cycle9")+(mode==2 ? 1 : 0);
    if (mode==1) unwinding=true;
    if (mode==3) insn_stop=true;
    if (mode==4) event_break=true;
}
inline void nds_restore_unwind_state() { unwinding=false; }
inline uint64_t nds_dma_entry_cycle(int) { return 0; }
inline uint64_t nds_halt_entry_cycle(int cpu) { return profile->get("service.halt_epoch."+std::to_string(cpu)); }
inline bool nds_event_break_hit() { return event_break; }
inline bool nds_slice_over() { return cycle_cap && g_runtime_cycles>=cycle_cap; }
inline void runtime_deferred_cycles_set(uint32_t value) { g_slot[0].deferred_cycles=value; }
inline uint32_t runtime_deferred_cycles() { return g_slot[0].deferred_cycles; }
#include "run_slice.inc"
inline bool probe(const task_aw2::Snapshot& state,unsigned selected) {
    profile=&state; mode=selected; dispatches=irq_calls=dma_calls=slice_begins=0;
    g_slot[0]={false,state.get("slot9.cycle"),uint32_t(state.get("slot9.deferred")),nullptr};
    g_slot[1]={false,state.get("cycle7"),uint32_t(state.get("deferred7")),nullptr};
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=uint32_t(state.get("r"+std::to_string(index)));
    g_cpu.cpsr=uint32_t(state.get("cpsr"));
    g_nds_terminal=event_break=insn_stop=unwinding=false;
    try { run_slice(0,uint32_t(state.get("slice_cap")-state.get("slot9.cycle"))); }
    catch (const Redispatch&) { return true; }
    return false;
}
}

namespace timer_rail {
constexpr int NDS_EMU_TIMERS_ARM9=0,NDS_EMU_TIMERS_ARM7=1;
struct NdsEmuScope { explicit NdsEmuScope(int) {} };
struct Timer { uint16_t ctrl=0,counter=0,reload=0; uint64_t accum=0; };
inline Timer g_timer[2][4];
inline unsigned long long g_timer_last[2]{};
inline const uint32_t kPrescaler[4]={1,64,256,1024};
inline struct Counts { uint64_t timer_ovf=0; } g_counts;
inline unsigned irq_calls=0,break_calls=0;
inline void nds_raise_irq(int,uint32_t) { ++irq_calls; }
inline void brk_check() { ++break_calls; }
#include "timers.inc"
inline void begin(const task_aw2::Snapshot& state) {
    irq_calls=break_calls=0; g_counts.timer_ovf=0;
    for (unsigned index=0;index<8;++index) {
        const auto prefix="timer."+std::to_string(index)+".";
        auto& timer=g_timer[index/4][index%4];
        timer.ctrl=uint16_t(state.get(prefix+"control")); timer.counter=uint16_t(state.get(prefix+"counter"));
        timer.reload=uint16_t(state.get(prefix+"reload")); timer.accum=state.get(prefix+"accum");
        g_timer_last[index/4]=state.get(prefix+"last");
    }
}
}

namespace gpu_rail {
using s32=int32_t;
struct Console { uint64_t ARM9Timestamp=3416875777ULL; unsigned ARM9ClockShift=1; };
struct GPU3D {
    Console NDS;
    bool GeometryEnabled=false;
    uint32_t FlushRequest=0;
    s32 CycleCount=0;
    uint64_t Timestamp=1708437825;
    uint32_t GXStat=0;
    unsigned NumPushPopCommands=0,NumTestCommands=0,commands=0,finishes=0;
    struct Pipe { bool empty=true; bool IsEmpty() const { return empty; } } CmdPIPE;
    s32 CyclesToRunFor() const noexcept;
    void Run() noexcept;
    void ExecuteCommand() noexcept { ++commands; CmdPIPE.empty=true; CycleCount=0; }
    void FinishWork(s32) noexcept { ++finishes; CycleCount=0; }
};
#include "gpu.inc"
}
