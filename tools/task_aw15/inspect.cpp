#include <fstream>
#include <iostream>
#include "aw6/prefix.h"
#include "source_path.h"

unsigned assertions=0;
void check(bool condition,const std::string& reason) {
    ++assertions;
    if (!condition) throw std::runtime_error(reason);
}
namespace periodic_rail {
constexpr int NDS_EMU_SPU=0,NDS_EMU_RTC=1,NDS_EMU_SYSEV=2,NDS_EMU_WIFI=3;
struct NdsEmuScope { explicit NdsEmuScope(int) {} };
inline uint64_t g_mix_count=1668396,g_rtc_processed_ticks=1670410,g_rtc_clock_count=0;
inline uint8_t g_rtc_irq_flag=0;
inline unsigned mixes=0,rtc_actions=0,event_actions=0;
inline void mix() { ++mixes; }
inline void rtc_count_second() { ++rtc_actions; }
inline void rtc_process_irq(int) { ++rtc_actions; }
#include "spu.inc"
#include "rtc.inc"
inline uint64_t g_auxspi_deadline=UINT64_MAX,g_spi_deadline=UINT64_MAX,g_card_deadline=UINT64_MAX;
inline uint64_t g_div_deadline=1708437913,g_sqrt_deadline=UINT64_MAX;
inline uint32_t g_auxspicnt=49152,g_spicnt=33281,g_romctrl=557934167;
inline bool g_card_end_event=false;
inline int g_card_irq_cpu=0,g_card_command=0,g_card_mode=0,g_card_data_mode=0,g_card_transfer_pos=0;
constexpr int NDS_CARD_TRACE_COMPLETE=0,NDS_CARD_TRACE_DATA_READY=1;
template<class... Arguments> void card_trace_push(Arguments...) { ++event_actions; }
inline uint32_t card_response_word(int) { ++event_actions; return 0; }
inline void nds_raise_irq(int,uint32_t) { ++event_actions; }
inline void nds_dma_trigger(int,unsigned) { ++event_actions; }
inline void finish_div() { ++event_actions; }
inline void finish_sqrt() { ++event_actions; }
#include "events.inc"
struct EventSource {
    uint64_t CurrentSystemTimestamp=1708437825,deadline=UINT64_MAX;
    bool pending=false;
    unsigned callbacks=0;
    bool HasPendingEvent() const { return pending; }
    uint64_t PendingEventTime() const { return deadline; }
    void RunPendingEvent() { ++callbacks; pending=false; }
};
struct Bridge { EventSource nds; bool wifi=true; };
inline Bridge* g_bridge=nullptr;
#include "wifi.inc"
}
namespace overlay_rail {
inline struct Live { bool enabled=false; } g_live;
inline unsigned polls=0;
inline void live_overlay_poll_now() { ++polls; }
#include "overlay.inc"
}
namespace cap_rail {
inline unsigned g_nds_active=0,g_yield_poll_hint=1;
inline uint64_t g_runtime_cycles=3416875777,g_cycle_cap=3416875778,g_nds_fast_limit=3416875778;
inline bool g_nds_terminal=false;
#include "slice_begin.inc"
}
void persistence() { std::fputs("PERSISTENCE_SENTINEL",stderr); }
struct Shutdown { ~Shutdown() { std::fputs("SHUTDOWN_SENTINEL",stderr); } };

int main(int argc,char** argv) {
    try {
        check(argc==2 || argc==4,"canonical metadata input only");
        std::ifstream input(argv[1]); std::string hex; input>>hex;
        std::vector<uint8_t> bytes;
        for (size_t index=0;index<hex.size();index+=2)
            bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
        const auto state=task_aw2::decode(bytes);
        check(task_aw2::digest(state)=="3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84","full fence identity");
        check(!task_aw::enabled(),"default observer null");
        check(slice_rail::probe(state,0) && slice_rail::dispatches==2,"disabled original slice still redispatches under unexpired cap");
        timer_rail::begin(state);
        timer_rail::nds_tick_timers(0,state.get("cycle9"));
        timer_rail::nds_tick_timers(1,state.get("cycle9")>>1);
        check(timer_rail::g_timer[0][0].counter==14558 && timer_rail::g_timer[0][0].accum==62,"ARM9 timer");
        check(timer_rail::g_timer[1][0].counter==50776 && timer_rail::g_timer[1][0].accum==43,"ARM7 timer0");
        check(timer_rail::g_timer[1][1].counter==64195 && timer_rail::g_timer[1][1].accum==39,"ARM7 timer1");
        check(!timer_rail::irq_calls && !timer_rail::break_calls,"no overflow IRQ");
        auto changed=state; changed.put("timer.0.counter",2,65535);
        timer_rail::begin(changed); timer_rail::nds_tick_timers(0,state.get("cycle9"));
        check(timer_rail::irq_calls==1,"timer readiness negative reaches actual overflow branch");
        slice_rail::profile=&state;
        slice_rail::g_slot[1]={false,state.get("cycle7"),2,nullptr};
        slice_rail::dispatches=slice_rail::irq_calls=slice_rail::dma_calls=0;
        slice_rail::run_slice(1,63);
        check(slice_rail::g_slot[1].cycles==1708437888 && slice_rail::g_slot[1].deferred_cycles==2,"HALT catchup/debt");
        check(!slice_rail::dispatches && !slice_rail::irq_calls && !slice_rail::dma_calls,"HALT catchup zero guest");
        changed=state; changed.put("irq7.if",4,state.get("irq7.ie")); slice_rail::profile=&changed;
        bool rejected=false;
        try { slice_rail::run_slice(1,63); } catch (const std::exception&) { rejected=true; }
        check(rejected && !slice_rail::dispatches,"ARM7 readiness hits fail-closed wake sentinel before IRQ/dispatch");
        gpu_rail::GPU3D gpu;
        gpu.GeometryEnabled=true; gpu.GXStat=0x80000000; gpu.NDS.ARM9Timestamp=state.get("cycle9");
        gpu.Run();
        check(gpu.Timestamp==1708437888 && !gpu.commands && !gpu.finishes && gpu.CycleCount==0,"actual GPU early-out timestamp");
        gpu.CmdPIPE.empty=false; gpu.Run();
        check(gpu.commands==1,"alternate GPU eligibility distinguished");
        using namespace periodic_rail;
        periodic_rail::nds_tick_spu(1708437888); periodic_rail::nds_tick_rtc(1708437888); periodic_rail::nds_run_system_events(1708437888);
        check(!mixes && !rtc_actions && !event_actions,"SPU RTC system events have no due callbacks");
        --g_mix_count; nds_tick_spu(1708437888); check(mixes==1,"SPU negative");
        --g_rtc_processed_ticks; periodic_rail::nds_tick_rtc(1708437888); check(rtc_actions==1,"RTC negative");
        g_div_deadline=1708437888; periodic_rail::nds_run_system_events(1708437888); check(event_actions==1,"divider due negative");
        check(nds_wifi_next_event_time()==UINT64_MAX,"null bridge max projection");
        nds_wifi_run_events(1708437888);
        Bridge bridge; g_bridge=&bridge;
        check(nds_wifi_next_event_time()==UINT64_MAX,"present idle bridge same projection");
        nds_wifi_run_events(1708437888);
        check(bridge.nds.CurrentSystemTimestamp==1708437888 && !bridge.nds.callbacks,"idle Wi-Fi bridge timestamp-only branch");
        bridge.nds.pending=true; bridge.nds.deadline=1708437888; nds_wifi_run_events(1708437888);
        check(bridge.nds.callbacks==1,"Wi-Fi due negative");
        overlay_rail::live_overlay_poll(); check(overlay_rail::polls==0,"overlay disabled early-out");
        overlay_rail::g_live.enabled=true; overlay_rail::live_overlay_poll();
        check(overlay_rail::polls==1,"same core/GPU can reach unprojected overlay body");
        task_aw3::armed=true; task_aw3::owner=std::this_thread::get_id();
        task_aw3::epoch=state.get("capture.epoch"); task_aw3::serial=state.get("capture.serial");
        task_aw3::rom_epoch=state.get("capture.rom_epoch");
        for (unsigned index=0;index<state.get("cap.count");++index) {
            const auto prefix="cap."+std::to_string(index)+".";
            task_aw3::history.push_back({task_aw3::epoch,state.get(prefix+"serial"),state.get(prefix+"cycle"),
                state.get(prefix+"observed_before"),state.get(prefix+"after"),state.get(prefix+"deadline"),
                uint32_t(state.get(prefix+"cpu")),uint32_t(state.get(prefix+"kind"))});
        }
        task_aw2::Snapshot before; task_aw3::export_history(before);
        check(before.get("cap.count")==6 && before.get("capture.serial")==506,"actual journal from fence metadata");
        cap_rail::nds_slice_begin(3416875826);
        task_aw2::Snapshot after; task_aw3::export_history(after);
        check(after.get("capture.epoch")==497 && after.get("capture.serial")==507 && after.get("cap.count")==1,"actual conditional cap reset");
        check(after.get("cap.0.observed_before")==3416875778 && after.get("cap.0.after")==3416875826 &&
            after.get("cap.0.quantum")==49 && after.get("cap.0.kind")==0,"actual conditional cap provenance");
        check(cap_rail::g_cycle_cap==3416875826 && cap_rail::g_nds_fast_limit==0 && cap_rail::g_yield_poll_hint==1,"actual conditional poll invalidation");
        task_aw3::armed=false;
        if (argc==4) {
            Shutdown shutdown; std::atexit(persistence);
            FILE* output=task_aw3::exclusive_audit(argv[3]); check(output,"exclusive audit");
            task_aw2::audit_snapshot(output,state);
            const bool success=std::string(argv[2])=="model_stop";
            std::fprintf(output,"{\"event\":\"%s\",\"model_only\":true,\"guest\":0,\"MMIO\":0}\n",
                success ? "pre_overlay_model_stop" : "binding_failure");
            if (!success) {
                changed=state; changed.put("capture.epoch",8,state.get("capture.epoch")+1);
                check(task_aw2::digest(changed)!=task_aw2::digest(state),"stale entry rejected");
            }
            task_aw::dispose(output,success ? 73 : 79);
            std::fputs("SCHEDULER_DEVICE_IRQ_ARM7_SENTINEL",stderr);
        }
        check(!task_aw::enabled(),"runtime diagnostics remain disabled");
        std::cout<<"{\"assertions\":"<<assertions<<",\"guest\":0,\"MMIO\":0,\"model_only\":true}\n";
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
