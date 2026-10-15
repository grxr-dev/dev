#pragma once
#include "aw4/reconcile.h"

namespace task_aw6 {
using task_aw2::Snapshot;
using task_aw2::Observation;
using task_aw2::require;
using task_aw::Kind;
constexpr unsigned instruction_count=11;
constexpr size_t observation_count=69;
constexpr uint32_t stop_pc=0x020019b4;
constexpr const char* entry_identity="0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c";

inline uint64_t rtc_due(uint64_t system) {
    return (task_aw2::multiply(task_aw2::add(system,1),32768)-1)/33513982;
}
inline uint64_t timer_deadline(const Snapshot& state,unsigned index) {
    const auto prefix=task_aw2::numbered("timer.",index)+".";
    const auto control=state.get(prefix+"control");
    require(!(control&~uint64_t{0xc7}),"unknown timer control bits");
    if (!(control&128)) return UINT64_MAX;
    require(!(control&4),"cascade timer outside captured profile");
    constexpr uint64_t divisors[4]={1,64,256,1024};
    const auto divisor=divisors[control&3];
    const auto accumulated=state.get(prefix+"accum");
    require(accumulated<divisor,"unclassified timer prescaler phase");
    const auto distance=task_aw2::multiply(65536-state.get(prefix+"counter"),divisor);
    require(distance>accumulated,"timer overflow already eligible");
    return task_aw2::add(state.get(prefix+"last"),distance-accumulated);
}
inline void ready_before(const Snapshot& state,uint64_t final_cycle) {
    require(state.get("active_cpu")==0 && state.get("current_slot")==0 && state.get("owner_thread")==1 &&
        state.get("round_active")==1 && state.get("force_tier3")==1,"Tier-3 ARM9 ownership");
    require(state.get("hidden.yield")<=1,"unclassified yield hint");
    require(state.get("deferred7")==2 && state.get("arm7_started")==1 && state.get("arm7_terminal")==0,
        "parked ARM7 profile changed");
    require(state.get("halt7")==1 && !(state.get("irq7.ie")&state.get("irq7.if")),"parked ARM7 halt/wakeup changed");
    for (const auto* name:{"deferred9","slot9.deferred","terminal","insn_stop","event_break","unwinding",
        "halt9","gpu_stall","card_end","save_dirty","synth_config","hidden.break_pc",
        "hidden.static_changed","service.gpu_debt","service.powered_off","service.firmware_dirty"})
        require(state.get(name)==0,"eligible/unknown service: "+std::string(name));
    const auto system=state.get("system_timestamp");
    require(state.get("cycle7")==system && state.get("cycle7")<=(state.get("cycle9")>>1),"parked ARM7 clock");
    require(state.get("service.rtc_due")==task_aw2::multiply(system,32768)/33513982,
        "protected legacy RTC projection changed");
    require(state.get("service.rtc_processed")==rtc_due(system),"actual RTC service phase mismatch");
    require(state.get("service.display_last")==system && state.get("service.spu_mixes")==system/1024,
        "periodic phase mismatch");
    const auto final_system=final_cycle>>1;
    require(system<=final_system && task_aw2::periodic_next(system)>final_system &&
        state.get("scheduler.next_event")>final_system,"periodic/scheduled work before stop");
    require(state.get("slice_cap")>final_cycle && state.get("fast_limit")==state.get("slice_cap") &&
        state.get("hidden.fast_enabled")==1 && state.get("hidden.cpu_poll")==1,"cap/fast-limit boundary");
    for (unsigned cpu=0;cpu<2;++cpu) {
        const auto irq=task_aw2::numbered("irq",cpu ? 7 : 9)+".";
        const auto pending=(state.get(irq+"ime")&1) ? state.get(irq+"ie")&state.get(irq+"if") : 0;
        require(!pending && state.get(irq+"cached")==0 && state.get(cpu ? "service.irq_cache7" : "service.irq_cache9")==0,
            "IRQ acceptance/wakeup eligible");
        require(state.get(task_aw2::numbered("scheduler.started.",cpu))==1 &&
            state.get(task_aw2::numbered("scheduler.halted.",cpu))==0,"scheduler slot lifecycle");
    }
    for (unsigned index=0;index<8;++index) {
        const auto dma=task_aw2::numbered("dma.",index)+".";
        require(state.get(dma+"active")==0 && state.get(dma+"running")==0 && state.get(dma+"in_progress")==0,
            "DMA eligible");
        require(state.get(task_aw2::numbered("timer.",index)+".last")==system,"timer timestamp mismatch");
        require(timer_deadline(state,index)>final_system,"timer overflow before stop");
    }
    for (const auto* name:{"card.deadline","spi.deadline","auxspi.deadline","sqrt.deadline","wifi.deadline","div.deadline"})
        require(state.get(name)>final_system,"device deadline before stop");
    require(bool(state.get("div.control")&0x8000)==(state.get("div.deadline")!=UINT64_MAX),"divider busy/deadline");
}
inline void entry(const Snapshot& state) {
    task_aw4::full_schema(state);
    task_aw2::manifest_matches(state);
    task_aw4::journal_valid(state);
    ready_before(state,task_aw2::add(state.get("cycle9"),56));
    require(task_aw2::digest(state)==entry_identity,"not the immutable AW5 captured profile");
    require(state.get("slice_cap")==state.get("slot9.target") &&
        state.get("scheduler.planned_target")==state.get("slice_cap") &&
        state.get("slot9.cycle")==state.get("cap.0.base"),"slice source binding");
    const auto selected=std::min({task_aw2::periodic_next(state.get("system_timestamp")),state.get("card.deadline"),
        state.get("spi.deadline"),state.get("auxspi.deadline"),state.get("sqrt.deadline"),state.get("wifi.deadline"),state.get("div.deadline")});
    require(state.get("scheduler.next_event")==selected,"round-selected event binding");
    require(state.get(task_aw2::numbered("return.",unsigned(state.get("return_depth")-1)))==state.get("r14"),"return stack/LR");
    for (unsigned index=0;index<12;++index)
        require(task_aw2::cost(state,index)==std::array<unsigned,12>{8,1,8,1,3,8,8,8,4,4,3,8}[index],"captured cost class");
}
inline void guard_next(const Snapshot& state,unsigned index) {
    require(index<instruction_count && state.get("r15")==task_aw2::pcs[index],"forbidden successor/PC");
    const auto after=task_aw2::add(state.get("cycle9"),task_aw2::cost(state,index));
    ready_before(state,after);
    if (index==0 || index==2 || index==5 || index==6 || index==7) {
        const auto deadline=task_aw2::add(state.get("cycle9")>>1,34);
        require(task_aw2::twice(deadline)>=state.get("slice_cap"),"unmodeled shortening");
        require(std::min(state.get("slice_cap"),task_aw2::twice(deadline))>after && deadline>(after>>1),
            "precommit MMIO cannot fit existing cap/deadline");
    }
}
inline std::vector<Observation> expected(const Snapshot& initial) {
    entry(initial);
    auto state=initial;
    std::vector<Observation> result;
    for (unsigned index=0;index<instruction_count;++index) {
        const auto pc=task_aw2::pcs[index];
        guard_next(state,index);
        task_aw2::append(result,Kind::instruction,pc,state);
        const auto ordinal=task_aw2::add(state.get("ordinal9"),1);
        for (const auto* name:{"ordinal9","snapshot_ordinal","capture.end_ordinal"}) state.put(name,8,ordinal);
        state.put("hidden.code_pc9",4,pc);
        task_aw2::append(result,Kind::access_before,pc,state,pc,4);
        task_aw2::append(result,Kind::access_after,pc,state,pc,4,uint32_t(initial.get(task_aw2::address_key("code.",pc))));
        uint32_t address=0,width=4,value=0; bool write=false;
        switch (index) {
            case 0: address=0x04000280; width=2; value=1; write=true; break;
            case 2: address=0x04000290; write=true; break;
            case 4: address=0x020019ac; value=0x04000298; break;
            case 5: address=0x04000294; value=4096; write=true; break;
            case 6: address=0x04000298; value=4096; write=true; break;
            case 7: address=0x0400029c; write=true; break;
            case 10: address=0x020019e4; value=0x04000280; break;
            default: break;
        }
        if (address) {
            state.put("hidden.data_addr9",4,address);
            task_aw2::append(result,Kind::access_before,pc,state,address,width,write ? value : 0,write);
            if (write) {
                state.put("div.control",2,0x8001);
                if (index!=0) state.put(index==2 ? "div.nlo" : index==5 ? "div.nhi" : index==6 ? "div.dlo" : "div.dhi",4,value);
                const auto deadline=task_aw2::add(state.get("cycle9")>>1,34);
                state.put("div.deadline",8,deadline);
                task_aw4::append_cap(state,deadline);
                require(state.get(task_aw2::numbered("cap.",unsigned(state.get("cap.count")-1))+".after")==state.get("slice_cap"),"cap unexpectedly changed");
            }
            task_aw2::append(result,Kind::access_after,pc,state,address,width,value,write);
        }
        if (index==1) state.put("r12",4,0);
        if (index==3) state.put("r3",4,4096);
        if (index==4) state.put("r1",4,0x04000298);
        if (index==9) state.put("r14",4,0x02001a24);
        if (index==10) state.put("r1",4,0x04000280);
        state.put("r15",4,index+1<instruction_count ? task_aw2::pcs[index+1] : stop_pc);
        const auto cost=task_aw2::cost(state,index);
        state.put("cycle9",8,task_aw2::add(state.get("cycle9"),cost));
        state.put("capture.end_cycle",8,state.get("cycle9"));
        task_aw2::append(result,Kind::cycle_commit,pc,state,0,0,cost);
        if (index==8) {
            const auto depth=unsigned(state.get("return_depth"));
            require(depth>1,"return underflow");
            state.fields.erase(task_aw2::numbered("return.",depth-1)); state.put("return_depth",4,depth-1);
        }
        if (index==9) {
            const auto depth=unsigned(state.get("return_depth"));
            state.put(task_aw2::numbered("return.",depth),4,0x02001a24); state.put("return_depth",4,depth+1);
        }
        task_aw2::append(result,Kind::retired,pc,state);
        require(state.get("cycle9")<state.get("fast_limit"),"unexpected post-retire poll");
    }
    require(result.size()==observation_count,"reduced transcript count");
    return result;
}
struct Ledger {
    std::shared_ptr<const std::vector<Observation>> plan;
    Snapshot seal;
    std::string previous,failure;
    size_t cursor=0;
    unsigned instructions=0;
    explicit Ledger(const Snapshot& observed):plan(std::make_shared<const std::vector<Observation>>(expected(observed))),seal(task_aw4::invariant(observed)),previous(task_aw2::digest(observed)) {}
    bool accept(const Observation& actual,const std::string& predecessor) noexcept {
        if (!failure.empty()) return false;
        try {
            require(predecessor==previous && cursor<plan->size(),"chain/order/extra event");
            task_aw4::full_schema(actual.state);
            require(task_aw4::invariant(actual.state)==seal,"immutable/latent observation changed");
            require(task_aw2::same(actual,(*plan)[cursor]),"full protected event/transition mismatch");
            task_aw4::journal_valid(actual.state);
            ready_before(actual.state,actual.state.get("cycle9"));
            if (actual.kind==Kind::instruction) { guard_next(actual.state,instructions); ++instructions; }
            previous=task_aw4::chain(previous,cursor,actual); ++cursor;
            return true;
        } catch (const std::exception& error) { failure=error.what(); }
        catch (...) { failure="unknown reduced ledger failure"; }
        return false;
    }
    bool complete() const { return failure.empty() && cursor==observation_count && instructions==instruction_count; }
};
}
