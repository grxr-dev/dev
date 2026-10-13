#pragma once
#include <set>
#include "aw3/bridge.h"

namespace task_aw4 {
using task_aw2::Snapshot;
using task_aw2::Observation;
using task_aw2::require;
using task_aw::Kind;
inline bool evolves(const std::string& name) {
    static const std::set<std::string> names={"r0","r1","r3","r12","r14","r15",
        "cycle9","ordinal9","snapshot_ordinal","capture.end_cycle","capture.end_ordinal",
        "capture.serial","cap.count","slice_cap","fast_limit","return_depth",
        "hidden.code_pc9","hidden.data_addr9","hidden.fast_publishes","hidden.force_misses",
        "div.control","div.deadline","div.nlo","div.nhi","div.dlo","div.dhi"};
    return names.count(name) || name.rfind("cap.",0)==0 || name.rfind("return.",0)==0;
}
inline Snapshot invariant(const Snapshot& full) {
    auto result=full;
    for (auto iterator=result.fields.begin();iterator!=result.fields.end();) {
        if (evolves(iterator->first)) iterator=result.fields.erase(iterator);
        else ++iterator;
    }
    return result;
}
inline std::string difference(const Snapshot& actual,const Snapshot& expected) {
    for (const auto& item:expected.fields) {
        const auto found=actual.fields.find(item.first);
        if (found==actual.fields.end() || !(found->second==item.second)) return item.first;
    }
    for (const auto& item:actual.fields) if (!expected.fields.count(item.first)) return "extra: "+item.first;
    for (const auto& item:expected.hashes) {
        const auto found=actual.hashes.find(item.first);
        if (found==actual.hashes.end() || found->second!=item.second) return "hash: "+item.first;
    }
    if (actual.hashes!=expected.hashes) return "extra hash";
    return {};
}
inline void append_cap(Snapshot& state,uint64_t deadline) {
    const auto count=unsigned(state.get("cap.count"));
    require(count<64,"journal bound before reschedule");
    const auto prefix=task_aw2::numbered("cap.",count)+".";
    const auto before=state.get("slice_cap");
    const auto after=before ? std::min(before,task_aw2::twice(deadline)) : task_aw2::twice(deadline);
    const auto serial=task_aw2::add(state.get("capture.serial"),1);
    state.put(prefix+"kind",1,1); state.put(prefix+"cpu",1,0);
    state.put(prefix+"cycle",8,state.get("cycle9")); state.put(prefix+"before",8,before);
    state.put(prefix+"observed_before",8,before); state.put(prefix+"after",8,after);
    state.put(prefix+"base",8,0); state.put(prefix+"quantum",8,0);
    state.put(prefix+"deadline",8,deadline); state.put(prefix+"serial",8,serial);
    state.put("cap.count",4,count+1); state.put("capture.serial",8,serial);
}
inline void journal_valid(const Snapshot& state) {
    const auto count=unsigned(state.get("cap.count"));
    require(count>=1 && count<=64 && state.get("capture.epoch"),"journal epoch/bounds");
    for (unsigned index=0;index<count;++index) {
        const auto prefix=task_aw2::numbered("cap.",index)+".";
        const auto sequence=state.get(prefix+"serial");
        require(sequence,"zero journal serial");
        if (index) {
            const auto previous=task_aw2::numbered("cap.",index-1)+".";
            require(sequence==task_aw2::add(state.get(previous+"serial"),1),"journal serial gap");
            require(state.get(prefix+"observed_before")==state.get(previous+"after"),"journal actual predecessor");
        }
    }
    require(state.get("capture.serial")==state.get(task_aw2::numbered("cap.",count-1)+".serial"),"journal terminal serial");
    task_aw2::cap_from_history(state);
}
inline std::map<std::string,uint8_t> full_layout(const Snapshot& state) {
    auto layout=task_aw2::layout(state);
    for (const auto* key:{"capture.epoch","capture.serial","capture.rom_epoch","capture.end_cycle","capture.end_ordinal",
        "hidden.force_misses","hidden.fast_publishes","hidden.dispatch_epoch","scheduler.round_epoch",
        "scheduler.planned_target","scheduler.next_event","service.spu_mixes","service.display_last",
        "service.rtc_processed","service.rtc_due"}) layout[key]=8;
    for (const auto* key:{"hidden.code_pc9","hidden.code_pc7","hidden.data_addr9","hidden.data_addr7",
        "hidden.cache_page","hidden.cache_generation","hidden.cache_class","hidden.region_class",
        "hidden.yield","hidden.break_pc","service.gpu_debt","service.irq_cache9","service.irq_cache7",
        "service.card_control"}) layout[key]=4;
    for (const auto* key:{"hidden.region_valid","hidden.class_ready","hidden.cpu_poll","hidden.fast_enabled",
        "hidden.static_changed","service.powered_off","service.firmware_dirty"}) layout[key]=1;
    for (const auto* key:{"service.spi_control","service.auxspi_control"}) layout[key]=2;
    for (const auto pc:task_aw2::pcs) layout[task_aw2::address_key("hidden.bank.",pc)]=1;
    for (const auto pc:task_aw2::pcs) layout[task_aw2::address_key("hidden.code_bit.",pc)]=1;
    for (const uint32_t address:{0x020019acu,0x020019e4u,0x04000280u,0x04000290u,0x04000294u,0x04000298u,0x0400029cu})
        layout[task_aw2::address_key("hidden.data_bit.",address)]=1;
    for (unsigned index=0;index<state.get("cap.count");++index) {
        const auto prefix=task_aw2::numbered("cap.",index)+".";
        layout[prefix+"serial"]=8; layout[prefix+"observed_before"]=8;
    }
    for (unsigned cpu=0;cpu<2;++cpu) {
        layout[task_aw2::numbered("scheduler.started.",cpu)]=1;
        layout[task_aw2::numbered("scheduler.halted.",cpu)]=1;
        layout[task_aw2::numbered("service.halt_epoch.",cpu)]=8;
        layout[task_aw2::numbered("service.dma_entry.",cpu)]=8;
    }
    for (unsigned index=0;index<8;++index) {
        layout[task_aw2::numbered("hidden.permission.",index)]=4;
        const auto dma=task_aw2::numbered("dma.",index)+".";
        for (const auto* key:{"running","in_progress","mode"}) layout[dma+key]=1;
        for (const auto* key:{"count","remaining","src","dst"}) layout[dma+key]=4;
        layout[dma+"burst"]=2;
        const auto timer=task_aw2::numbered("timer.",index)+".";
        layout[timer+"counter"]=2; layout[timer+"reload"]=2; layout[timer+"accum"]=8;
    }
    return layout;
}
inline void full_schema(const Snapshot& state) {
    const auto layout=full_layout(state);
    require(state.fields.size()==layout.size(),"missing/extra full provider field");
    for (const auto& item:layout) {
        const auto found=state.fields.find(item.first);
        require(found!=state.fields.end() && found->second.width==item.second,"full provider field/width: "+item.first);
    }
    require(state.hashes.size()==5,"missing/extra provider identity");
    for (const auto* name:{"rom","framework_commit","mainram","dtcm","save"})
        require(state.hashes.count(name),"missing provider identity");
    task_aw2::canonical(state);
}
inline void entry(const Snapshot& observed,const Snapshot& authority) {
    full_schema(observed);
#if defined(AW4_ROMFREE_CERTIFICATION)
    task_aw3::entry_preflight(observed,authority);
#else
    require(authority==task_aw2::au_manifest(),"production authority cannot be overridden");
    task_aw3::entry_preflight(observed);
#endif
    journal_valid(observed);
    require(observed.get("hidden.break_pc")==0 && observed.get("hidden.static_changed")==0,
            "unclassified frontend/static-code yield");
    require(observed.get("hidden.fast_enabled")<=1,"fast selector not binary");
    for (const auto pc:task_aw2::pcs)
        require(observed.get(task_aw2::address_key("hidden.bank.",pc))<=1,"bank classification not binary");
    require(observed.get("slice_cap")>task_aw2::twice(task_aw2::add(observed.get("cycle9")>>1,34)),
        "77-event admission requires first setup write to shorten cap");
    const auto expected_limit=observed.get("hidden.fast_enabled") && observed.get("hidden.cpu_poll") ? observed.get("slice_cap") : 0;
    require(observed.get("fast_limit")==expected_limit,"unclassified entry fast limit");
}
inline std::vector<Observation> expected(const Snapshot& initial,const Snapshot& authority) {
    entry(initial,authority);
    auto state=initial;
    std::vector<Observation> result;
    for (unsigned index=0;index<task_aw2::pcs.size();++index) {
        const auto pc=task_aw2::pcs[index];
        task_aw2::prospective(state,index);
        task_aw2::append(result,Kind::instruction,pc,state);
        state.put("hidden.force_misses",8,task_aw2::add(state.get("hidden.force_misses"),
            state.get(task_aw2::address_key("hidden.bank.",pc))));
        const auto ordinal=task_aw2::add(state.get("ordinal9"),1);
        for (const auto* name:{"ordinal9","snapshot_ordinal","capture.end_ordinal"}) state.put(name,8,ordinal);
        state.put("hidden.code_pc9",4,pc);
        const auto opcode=uint32_t(initial.get(task_aw2::address_key("code.",pc)));
        task_aw2::append(result,Kind::access_before,pc,state,pc,4);
        task_aw2::append(result,Kind::access_after,pc,state,pc,4,opcode);
        uint32_t address=0,width=4,value=0; bool write=false;
        switch (index) {
            case 0: address=0x04000280; width=2; value=1; write=true; break;
            case 2: address=0x04000290; write=true; break;
            case 4: address=0x020019ac; value=0x04000298; break;
            case 5: address=0x04000294; value=4096; write=true; break;
            case 6: address=0x04000298; value=4096; write=true; break;
            case 7: address=0x0400029c; write=true; break;
            case 10: address=0x020019e4; value=0x04000280; break;
            case 11: address=0x04000280; width=2; value=0x8001; break;
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
                append_cap(state,deadline);
                const auto cap=state.get(task_aw2::numbered("cap.",unsigned(state.get("cap.count")-1))+".after");
                if (cap!=state.get("slice_cap")) {
                    state.put("slice_cap",8,cap);
                    task_aw2::append(result,Kind::cap_change,pc,state);
                    state.put("fast_limit",8,0);
                }
            }
            task_aw2::append(result,Kind::access_after,pc,state,address,width,value,write);
        }
        if (index==1) state.put("r12",4,0);
        if (index==3) state.put("r3",4,4096);
        if (index==4) state.put("r1",4,0x04000298);
        if (index==9) state.put("r14",4,0x02001a24);
        if (index==10) state.put("r1",4,0x04000280);
        if (index==11) state.put("r0",4,0x8001);
        state.put("r15",4,index+1<task_aw2::pcs.size() ? task_aw2::pcs[index+1] : task_aw2::terminal_pc);
        const auto cost=task_aw2::cost(state,index);
        const auto cycle=task_aw2::add(state.get("cycle9"),cost);
        state.put("cycle9",8,cycle); state.put("capture.end_cycle",8,cycle);
        task_aw2::append(result,Kind::cycle_commit,pc,state,0,0,cost);
        if (index==8) {
            const auto depth=unsigned(state.get("return_depth"));
            require(depth>1,"return-stack underflow");
            state.fields.erase(task_aw2::numbered("return.",depth-1)); state.put("return_depth",4,depth-1);
        }
        if (index==9) {
            const auto depth=unsigned(state.get("return_depth"));
            state.put(task_aw2::numbered("return.",depth),4,0x02001a24); state.put("return_depth",4,depth+1);
        }
        task_aw2::append(result,Kind::retired,pc,state);
        if (cycle>=state.get("fast_limit")) {
            const bool enabled=state.get("hidden.fast_enabled") && state.get("hidden.cpu_poll");
            state.put("fast_limit",8,enabled ? state.get("slice_cap") : 0);
            if (enabled) state.put("hidden.fast_publishes",8,task_aw2::add(state.get("hidden.fast_publishes"),1));
        }
    }
    require(result.size()==77,"reconciled transcript size");
    return result;
}
inline std::string chain(const std::string& previous,size_t index,const Observation& event) {
    auto bytes=task_aw2::canonical(event.state);
    bytes.insert(bytes.begin(),previous.begin(),previous.end());
    task_aw2::little(bytes,index,8); task_aw2::little(bytes,unsigned(event.kind),4);
    for (auto value:{event.pc,event.address,event.width,event.value}) task_aw2::little(bytes,value,4);
    task_aw2::little(bytes,event.write,1);
    return brainage_custom::resource_detail::sha256(bytes.data(),bytes.size());
}
struct Ledger {
    std::vector<Observation> plan;
    Snapshot seal;
    std::string seal_digest,previous,failure;
    size_t cursor=0;
    unsigned instructions=0;
    Ledger(const Snapshot& observed,const Snapshot& authority):plan(expected(observed,authority)),seal(invariant(observed)),
        seal_digest(task_aw2::digest(seal)),previous(task_aw2::digest(observed)) {}
    bool accept(const Observation& actual,const std::string& claimed_previous) noexcept {
        if (!failure.empty()) return false;
        try {
            require(claimed_previous==previous,"chained observation tamper/replay");
            require(cursor<plan.size(),"extra observation after terminal");
            full_schema(actual.state);
            require(invariant(actual.state)==seal && task_aw2::digest(invariant(actual.state))==seal_digest,"immutable entry seal mutation");
            const auto& target=plan[cursor];
            require(actual.kind==target.kind && actual.pc==target.pc && actual.address==target.address &&
                actual.width==target.width && actual.value==target.value && actual.write==target.write,"event order/metadata");
            require(actual.state==target.state,"protected transition mismatch: "+difference(actual.state,target.state));
            journal_valid(actual.state);
            require(actual.state.get("snapshot_ordinal")==actual.state.get("ordinal9") &&
                actual.state.get("capture.end_ordinal")==actual.state.get("ordinal9") &&
                actual.state.get("capture.end_cycle")==actual.state.get("cycle9"),"torn observation");
            if (actual.kind==Kind::instruction) { task_aw2::prospective(actual.state,instructions); ++instructions; }
            previous=chain(previous,cursor,actual); ++cursor;
            return true;
        } catch (const std::exception& error) { failure=error.what(); }
        catch (...) { failure="unknown transition failure"; }
        return false;
    }
    bool complete() const { return failure.empty() && cursor==77 && instructions==12; }
    bool finish() { if (complete()) return true; if (failure.empty()) failure="incomplete transcript"; return false; }
};
}
