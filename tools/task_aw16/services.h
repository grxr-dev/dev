#pragma once
using s32=int32_t;
constexpr int NDS_EMU_TIMERS_ARM9=2,NDS_EMU_TIMERS_ARM7=3,NDS_EMU_SPU=4,NDS_EMU_RTC=5,NDS_EMU_SYSEV=6;
constexpr int NDS_EMU_WIFI=7,NDS_EMU_GEOM=8,NDS_EMU_DISPLAY=9,NDS_EMU_NEXTEV=10;
struct NdsEmuScopeIf { NdsEmuScopeIf(int,bool) {} };
struct NdsEmuRound {};
using ProfileClock=std::chrono::steady_clock;
inline bool g_sample_active=false;
inline uint64_t g_profile_rounds=0;
inline struct Profile {
    uint64_t next_event_ns=0,arm9_ns=0,arm7_ns=0,display_ns=0,spu_ns=0,wifi_ns=0,rtc_ns=0,sysev_ns=0;
    uint64_t devices_ns=0,sampled_round_ns=0,sampled_rounds=0;
} g_profile;
inline void profile_add(uint64_t&,ProfileClock::time_point) {}
inline void nds_pc_profile_note(int,uint32_t) {}
inline void nds_emu_note_gxstall_round() { forbidden_service(); }
constexpr int kArm9ClockShift=1;
constexpr uint64_t kIterCap=64;
#include "profile_modulus.inc"
#include "round_guard.inc"
struct Timer { uint16_t ctrl=0,counter=0,reload=0; uint64_t accum=0; };
inline Timer g_timer[2][4];
inline unsigned long long g_timer_last[2]{};
inline const uint32_t kPrescaler[4]={1,64,256,1024};
inline struct Counts { uint64_t timer_ovf=0,vblank9=0,vblank7=0; } g_counts;
inline void nds_raise_irq(int,uint32_t) { forbidden_service(); }
inline void brk_check() { forbidden_service(); }
#include "timers.inc"
inline uint64_t g_display_last=0,g_rtc_processed_ticks=0,g_rtc_clock_count=0;
inline uint8_t g_rtc_irq_flag=0;
inline uint16_t g_vcount=0,g_next_vcount=0,g_dispstat[2]{};
inline bool g_next_vcount_valid=false,g_vcount_match[2]{},g_in_vblank=false;
inline void nds_gpu2d_render_scanline(int) { forbidden_service(); }
inline void nds_gpu2d_start_frame() { forbidden_service(); }
inline void nds_gpu3d_start_frame() { forbidden_service(); }
inline void nds_title_patches_start_frame() { forbidden_service(); }
inline void nds_gpu2d_vblank() { forbidden_service(); }
inline void nds_gpu3d_vblank() { forbidden_service(); }
inline void nds_gpu3d_vcount144() { forbidden_service(); }
inline void nds_gpu3d_vcount215() { forbidden_service(); }
inline void nds_gpu2d_finish_frame() { forbidden_service(); }
inline void nds_dma_trigger(int,unsigned) { forbidden_service(); }
#include "display.inc"
inline void mix() { forbidden_service(); }
inline void rtc_count_second() { forbidden_service(); }
inline void rtc_process_irq(int) { forbidden_service(); }
#include "spu.inc"
#include "rtc.inc"
inline uint64_t g_auxspi_deadline=UINT64_MAX,g_spi_deadline=UINT64_MAX,g_card_deadline=UINT64_MAX;
inline uint64_t g_div_deadline=1708437913,g_sqrt_deadline=UINT64_MAX;
inline uint32_t g_auxspicnt=0,g_spicnt=0,g_romctrl=0;
inline bool g_card_end_event=false;
inline int g_card_irq_cpu=0,g_card_command=0,g_card_mode=0,g_card_data_mode=0,g_card_transfer_pos=0;
constexpr int NDS_CARD_TRACE_COMPLETE=0,NDS_CARD_TRACE_DATA_READY=1;
template<class... Arguments> void card_trace_push(Arguments...) { forbidden_service(); }
inline uint32_t card_response_word(int) { forbidden_service(); return 0; }
inline void finish_div() { forbidden_service(); }
inline void finish_sqrt() { forbidden_service(); }
#include "events.inc"
#include "system_deadline.inc"
inline uint64_t nds_next_timer_overflow_time() { forbidden_service(); return 0; }
inline bool nds_powered_off() { return baseline.get("service.powered_off"); }
inline bool nds_gxfifo_stalled() { return baseline.get("gpu_stall"); }
inline struct Network { bool enabled=false; } g_network_config;
struct WifiClock {
    uint64_t CurrentSystemTimestamp=1708437825,deadline=0;
    bool pending=false;
    bool HasPendingEvent() const { return pending; }
    uint64_t PendingEventTime() const { return deadline; }
    void RunPendingEvent() { forbidden_service(); }
};
struct Bridge { WifiClock nds; bool wifi=true; void* worker_thread=nullptr; };
inline std::unique_ptr<Bridge> g_bridge;
#include "wifi_events.inc"
inline struct Live { bool enabled=false; uint64_t opaque_noninterfering=0; } g_live;
inline void live_overlay_poll_now() { forbidden_service(); }
#include "overlay_poll.inc"
inline void Gpu::ExecuteCommand() { forbidden_service(); }
inline void Gpu::FinishWork(int32_t) { forbidden_service(); }
#include "gpu_methods.inc"
inline uint64_t g_gx_run_trace_count=0;
constexpr uint32_t kGxRunTraceSize=65536;
struct NdsGxRunTraceEntry {
    uint64_t count=0,arm9_cycles=0;
    uint32_t gxstat_before=0,gxstat_after=0;
    int32_t cycle_count_before=0,cycle_count_after=0;
};
inline NdsGxRunTraceEntry g_gx_run_trace[kGxRunTraceSize];
#include "gpu_run.inc"
#include "trace_getters.inc"
#include "next_event.inc"
inline void services_begin(const task_aw2::Snapshot& state) {
    g_mix_count=state.get("service.spu_mixes"); g_display_last=state.get("service.display_last");
    g_rtc_processed_ticks=state.get("service.rtc_processed");
    g_div_deadline=state.get("div.deadline"); g_auxspi_deadline=state.get("auxspi.deadline");
    g_card_deadline=state.get("card.deadline"); g_spi_deadline=state.get("spi.deadline"); g_sqrt_deadline=state.get("sqrt.deadline");
    for (unsigned index=0;index<8;++index) {
        const auto prefix="timer."+std::to_string(index)+"."; auto& timer=g_timer[index/4][index%4];
        timer.ctrl=state.get(prefix+"control"); timer.counter=state.get(prefix+"counter");
        timer.reload=state.get(prefix+"reload"); timer.accum=state.get(prefix+"accum"); g_timer_last[index/4]=state.get(prefix+"last");
    }
}
inline void dynamic_io(task_aw2::Snapshot& out) {
    for (unsigned index=0;index<8;++index) {
        const auto prefix="timer."+std::to_string(index)+"."; const auto& timer=g_timer[index/4][index%4];
        out.put(prefix+"control",2,timer.ctrl); out.put(prefix+"counter",2,timer.counter);
        out.put(prefix+"reload",2,timer.reload); out.put(prefix+"accum",8,timer.accum); out.put(prefix+"last",8,g_timer_last[index/4]);
    }
    out.put("service.display_last",8,g_display_last); out.put("service.rtc_processed",8,g_rtc_processed_ticks);
    out.put("service.rtc_due",8,task_aw2::multiply(out.get("system_timestamp"),32768)/33513982);
    out.put("div.deadline",8,g_div_deadline); out.put("auxspi.deadline",8,g_auxspi_deadline);
    out.put("spi.deadline",8,g_spi_deadline); out.put("card.deadline",8,g_card_deadline); out.put("sqrt.deadline",8,g_sqrt_deadline);
}
