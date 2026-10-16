#pragma once
#include "auxiliary.h"

namespace task_aw16 {
inline constexpr const char* fence_identity="3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84";
inline constexpr const char* gpu_identity="708de6de2568d09123820267c9daaa7abd49321e90e275923ac93d96513ad5d4";
struct Step {
    std::string label;
    Snapshot core,gpu,extra;
    bool observed=false;
    task_aw::Kind kind=task_aw::Kind::device;
};
inline void timer_step(Snapshot& core,unsigned cpu,uint64_t timestamp) {
    const auto base="timer."+std::to_string(cpu*4)+".";
    const auto last=core.get(base+"last");
    require(timestamp>=last,"AW16 timer time rewind");
    for (unsigned index=cpu*4;index<cpu*4+4;++index) {
        const auto prefix="timer."+std::to_string(index)+".";
        require(core.get(prefix+"last")==last,"AW16 shared timer latch");
        core.put(prefix+"last",8,timestamp);
        const auto control=core.get(prefix+"control");
        if (!(control&128)) continue;
        uint64_t ticks=0;
        if (!(control&4)) {
            const uint64_t scale[]={1,64,256,1024};
            const auto total=task_aw2::add(core.get(prefix+"accum"),timestamp-last);
            ticks=total/scale[control&3]; core.put(prefix+"accum",8,total%scale[control&3]);
        }
        const auto count=task_aw2::add(core.get(prefix+"counter"),ticks);
        require(count<65536,"AW16 timer overflow forbidden"); core.put(prefix+"counter",2,count);
    }
}
inline std::vector<Step> tail_plan(const Snapshot& entry,const Snapshot& geometry,const Snapshot& auxiliary) {
    task_aw4::full_schema(entry); task_aw4::journal_valid(entry);
    require(task_aw2::digest(entry)==fence_identity && task_aw2::digest(geometry)==gpu_identity,"AW16 exact AW14 fence");
    task_aw12::gpu_admit(geometry,entry); aux_admit(auxiliary,entry);
    auto core=entry,gpu=geometry,extra=auxiliary;
    std::vector<Step> plan;
    auto point=[&](const char* label) { plan.push_back({label,core,gpu,extra}); };
    auto observe=[&](const char* label,task_aw::Kind kind) {
        plan.push_back({label,core,gpu,extra,true,kind});
    };
    const auto rendezvous=core.get("cycle9")>>1;
    require(rendezvous==1708437888 && core.get("slice_cap")==3416875778,"AW16 retained cap relation");
    point("successor_admitted");
    observe("scheduler_device",task_aw::Kind::device);
    observe("timer9_entry",task_aw::Kind::device);
    timer_step(core,0,rendezvous); point("timers9_done");
    gpu.put("gpu.arm9_timestamp",8,core.get("cycle9")); gpu.put("gpu.timestamp",8,rendezvous);
    extra.put("trace.count",8,task_aw2::add(extra.get("trace.count"),1));
    extra.put("trace.last.count",8,extra.get("trace.count"));
    extra.put("trace.last.cycle",8,core.get("cycle9"));
    extra.put("trace.last.before",4,geometry.get("gpu.stat")); extra.put("trace.last.after",4,geometry.get("gpu.stat"));
    extra.put("trace.last.debt_before",4,geometry.get("gpu.cycles")); extra.put("trace.last.debt_after",4,geometry.get("gpu.cycles"));
    point("gpu_done"); point("slice7_gate"); observe("arm7_entry",task_aw::Kind::arm7);
    core.put("cycle7",8,rendezvous); point("arm7_done");
    observe("timer7_entry",task_aw::Kind::device);
    timer_step(core,1,rendezvous); point("timers7_done"); point("power_checked");
    const auto prior=core.get("service.display_last");
    require(prior/2130==rendezvous/2130 && (prior-1584)/2130==(rendezvous-1584)/2130,"AW16 display edge");
    core.put("service.display_last",8,rendezvous); point("display_done");
    require(core.get("service.spu_mixes")>=rendezvous/1024,"AW16 SPU mix readiness"); point("spu_done");
    if (extra.get("wifi.bridge") && extra.get("wifi.device")) extra.put("wifi.timestamp",8,rendezvous);
    point("wifi_done"); observe("rtc_entry",task_aw::Kind::device);
    require(core.get("service.rtc_processed")>=((rendezvous+1)*32768-1)/33513982,"AW16 RTC readiness"); point("rtc_done");
    observe("system_entry",task_aw::Kind::device);
    for (const auto* device:{"auxspi","spi","card","div","sqrt"})
        require(core.get(std::string(device)+".deadline")>rendezvous,"AW16 system event readiness");
    point("system_done"); core.put("system_timestamp",8,rendezvous);
    core.put("service.rtc_due",8,rendezvous*32768/33513982); point("time_published"); point("overlay_done");
    core.put("round_active",1,0); point("round_left");
    observe("next_scheduler",task_aw::Kind::scheduler);
    core.put("round_active",1,1); point("round_entered");
    const auto event=std::min({task_aw2::periodic_next(rendezvous),core.get("div.deadline"),core.get("wifi.deadline"),
        core.get("auxspi.deadline"),core.get("spi.deadline"),core.get("card.deadline"),core.get("sqrt.deadline")});
    auto target=rendezvous+64;
    if (event<target+8) target=event;
    target=task_aw2::twice(target);
    require(target==3416875826 && target-core.get("slot9.cycle")==49,"AW16 next target/quantum");
    core.put("scheduler.round_epoch",8,task_aw2::add(core.get("scheduler.round_epoch"),1));
    core.put("scheduler.planned_target",8,target); core.put("scheduler.next_event",8,event);
    point("target_selected"); point("slice9_gate");
    const auto serial=task_aw2::add(core.get("capture.serial"),1);
    for (auto item=core.fields.begin();item!=core.fields.end();) {
        if (item->first.rfind("cap.",0)==0) item=core.fields.erase(item); else ++item;
    }
    core.put("capture.epoch",8,task_aw2::add(core.get("capture.epoch"),1)); core.put("capture.serial",8,serial);
    core.put("cap.count",4,1); core.put("cap.0.kind",1,0); core.put("cap.0.cpu",1,0);
    core.put("cap.0.cycle",8,core.get("cycle9")); core.put("cap.0.base",8,core.get("cycle9"));
    core.put("cap.0.before",8,0); core.put("cap.0.observed_before",8,core.get("slice_cap"));
    core.put("cap.0.after",8,target); core.put("cap.0.quantum",8,49); core.put("cap.0.deadline",8,0); core.put("cap.0.serial",8,serial);
    core.put("slot9.target",8,target); core.put("slice_cap",8,target); core.put("terminal",1,0);
    core.put("fast_limit",8,0); core.put("hidden.yield",4,1);
    require(task_aw2::digest(core)=="68b88b2de2264fb8fc456422de7aa026a8ac00685268f8cd8ea5650d3b01f773","AW15 final protected projection");
    point("slice_begun_stop"); return plan;
}
}
