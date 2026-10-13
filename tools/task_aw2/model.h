#pragma once
#include <algorithm>
#include <array>
#include "au_manifest.h"
#include "../task_aw/bridge.h"

namespace task_aw2 {
constexpr uint64_t entry_cycle=3416875721ULL;
constexpr uint32_t terminal_pc=0x020019b8;
constexpr std::array<uint32_t,12> pcs={0x02001980,0x02001984,0x02001988,0x0200198c,
    0x02001990,0x02001994,0x02001998,0x0200199c,0x020019a0,0x02001a20,0x020019b0,0x020019b4};
inline std::string numbered(const std::string& prefix, unsigned index) {
    return prefix+std::to_string(index);
}
inline std::string address_key(const std::string& prefix, uint32_t address) {
    char text[9];
    std::snprintf(text,sizeof(text),"%08x",address);
    return prefix+text;
}
inline uint64_t multiply(uint64_t value, uint64_t scale) {
    require(scale==0 || value<=UINT64_MAX/scale, "periodic multiply overflow");
    return value*scale;
}
inline uint64_t rtc_next(uint64_t timestamp) {
    auto ordinal=add(multiply(timestamp,32768)/33513982,1);
    auto deadline=multiply(ordinal,33513982)/32768;
    if (deadline<=timestamp) deadline=multiply(add(ordinal,1),33513982)/32768;
    require(deadline>timestamp, "RTC phase");
    return deadline;
}
inline uint64_t periodic_next(uint64_t timestamp) {
    const auto base=multiply(timestamp/2130,2130);
    const auto lcd=add(base,timestamp-base<1584 ? 1584 : 2130);
    const auto spu=multiply(add(timestamp/1024,1),1024);
    return std::min({lcd,spu,rtc_next(timestamp)});
}
inline bool cacheable(const Snapshot& snapshot, uint32_t address, bool code) {
    const auto control=snapshot.get("cp15.control");
    if (!(control & (code ? 4096 : 4))) return false;
    if (!(control & 1)) return true;
    for (int index=7;index>=0;--index) {
        const uint32_t region=uint32_t(snapshot.get(numbered("cp15.region.",unsigned(index))));
        if (!(region&1)) continue;
        const auto size=uint64_t{1}<<(((region>>1)&31)+1);
        const auto base=uint64_t(region&0xfffff000u)&~(size-1);
        if (address>=base && address<add(base,size))
            return ((snapshot.get(code ? "cp15.icache" : "cp15.dcache")>>index)&1)!=0;
    }
    return false;
}
inline bool tcm_overlap(const Snapshot& snapshot, uint32_t address) {
    for (const auto* prefix:{"itcm", "dtcm_map"}) {
        if (!snapshot.get(std::string(prefix)+".enabled")) continue;
        const auto base=snapshot.get(std::string(prefix)+".base");
        const auto size=snapshot.get(std::string(prefix)+".size");
        require(size>0 && !(size&(size-1)) && !(base&(size-1)), "invalid copied TCM mapping");
        if (address>=base && address<add(base,size)) return true;
    }
    return false;
}
inline uint32_t code_cost(const Snapshot& snapshot, uint32_t pc) {
    require(snapshot.get("timing.valid")==1 && snapshot.get("timing.class")==1,
            "unknown/not cached code latch");
    require(snapshot.get("cp15.generation")==snapshot.get("timing.generation") &&
            snapshot.get("cp15.generation")==snapshot.get("timing.publication"), "stale timing generation");
    require(cacheable(snapshot,pc,true) && !tcm_overlap(snapshot,pc), "code mapping mismatch");
    return ((pc+8)&31) ? 1 : 3;
}
inline uint32_t data_cost(const Snapshot& snapshot, uint32_t address) {
    require(!tcm_overlap(snapshot,address), "unexpected TCM data mapping");
    if (cacheable(snapshot,address,false)) return 3;
    require(address>=0x04000000 && address<0x05000000, "uncertified data region");
    return 8;
}
inline uint32_t cost(const Snapshot& snapshot, unsigned index) {
    require(index<pcs.size(), "instruction beyond candidate");
    const auto num_code=code_cost(snapshot,pcs[index]);
    if (index==8 || index==9) {
        const auto target=index==8 ? 0x02001a20u : 0x020019b0u;
        require(cacheable(snapshot,target,true) && !tcm_overlap(snapshot,target), "uncertified branch refill");
        return 3+(((target+4)&31) ? 1 : 3);
    }
    uint32_t num_data=0;
    if (index==4 || index==10)
        num_data=data_cost(snapshot,index==4 ? 0x020019ac : 0x020019e4);
    else if (index==0 || index==2 || index==5 || index==6 || index==7 || index==11)
        num_data=data_cost(snapshot,0x04000280);
    if (!num_data) return num_code;
    return std::max(std::max(num_code,num_data),num_code+num_data>6 ? num_code+num_data-6 : 0);
}
inline uint64_t cap_from_history(const Snapshot& snapshot) {
    const auto count=snapshot.get("cap.count");
    require(count>=1 && count<=64, "missing/unbounded cap history");
    uint64_t cap=0, previous_cycle=0;
    for (unsigned index=0;index<count;++index) {
        const auto prefix=numbered("cap.",index)+".";
        const auto kind=snapshot.get(prefix+"kind");
        const auto cycle=snapshot.get(prefix+"cycle");
        require(cycle>=previous_cycle && cycle<=snapshot.get("cycle9"), "stale cap history clock");
        require(snapshot.get(prefix+"before")==cap, "broken cap provenance chain");
        if (!index) {
            require(kind==0 && snapshot.get(prefix+"cpu")==0, "unknown cap origin");
            require(snapshot.get(prefix+"base")==cycle, "slice base/cycle mismatch");
            cap=add(cycle,snapshot.get(prefix+"quantum"));
            require(cap && !(cap&1), "slice cap conversion");
        } else {
            require(kind==1 && snapshot.get(prefix+"cpu")==0, "untracked setter/CPU switch");
            const auto shortened=twice(snapshot.get(prefix+"deadline"));
            cap=cap ? std::min(cap,shortened) : shortened;
        }
        require(snapshot.get(prefix+"after")==cap, "cap replacement/retention mismatch");
        previous_cycle=cycle;
    }
    require(snapshot.get("slice_cap")==cap, "entry cap provenance mismatch");
    require(cap>snapshot.get("cycle9"), "stale entry cap");
    return cap;
}
inline std::map<std::string,uint8_t> layout(const Snapshot& snapshot) {
    std::map<std::string,uint8_t> result;
    for (const auto& item:au_manifest().fields) result[item.first]=item.second.width;
    for (const auto* key:{"active_cpu","owner_thread","round_active","current_slot","force_tier3",
                         "event_break","insn_stop","terminal","unwinding","halt9","halt7",
                         "arm7_started","arm7_terminal","gpu_stall","card_end","save_dirty",
                         "synth_config","timing.valid","itcm.enabled","dtcm_map.enabled"}) result[key]=1;
    for (const auto* key:{"deferred9","deferred7","irq9.ime","irq9.ie","irq9.if","irq9.cached",
                         "irq7.ime","irq7.ie","irq7.if","irq7.cached","cp15.control","cp15.dcache",
                         "cp15.icache","cp15.generation","timing.generation","timing.publication",
                         "timing.class","itcm.base","dtcm_map.base","div.nlo","div.nhi",
                         "div.dlo","div.dhi","div.qlo","div.qhi","div.rlo","div.rhi","return_depth",
                         "cap.count","slot9.deferred"}) result[key]=4;
    for (const auto* key:{"fast_limit","system_timestamp","itcm.size","dtcm_map.size","div.deadline",
                         "card.deadline","spi.deadline","auxspi.deadline","sqrt.deadline","wifi.deadline",
                         "slice_cap","slot9.cycle","slot9.target","snapshot_ordinal"}) result[key]=8;
    result["div.control"]=2;
    for (unsigned cpu=0;cpu<2;++cpu)
        for (unsigned index=0;index<4;++index) {
            result[numbered("dma.",cpu*4+index)+".active"]=1;
            result[numbered("timer.",cpu*4+index)+".control"]=2;
            result[numbered("timer.",cpu*4+index)+".last"]=8;
        }
    for (unsigned index=0;index<8;++index) result[numbered("cp15.region.",index)]=4;
    const auto depth=snapshot.get("return_depth");
    require(depth>=1 && depth<=32, "return stack bounds");
    for (unsigned index=0;index<depth;++index) result[numbered("return.",index)]=4;
    const auto count=snapshot.get("cap.count");
    require(count>=1 && count<=64, "cap record bounds");
    for (unsigned index=0;index<count;++index) {
        const auto prefix=numbered("cap.",index)+".";
        result[prefix+"kind"]=1;
        result[prefix+"cpu"]=1;
        for (const auto* key:{"cycle","before","after","base","quantum","deadline"}) result[prefix+key]=8;
    }
    return result;
}
inline void manifest_matches(const Snapshot& snapshot
#if defined(AW4_ROMFREE_CERTIFICATION)
    , const Snapshot& expected=au_manifest()
#endif
) {
#if !defined(AW4_ROMFREE_CERTIFICATION)
    const auto expected=au_manifest();
#endif
    for (const auto& item:expected.fields) {
        const auto found=snapshot.fields.find(item.first);
        require(found!=snapshot.fields.end() && found->second==item.second, "AU manifest scalar: "+item.first);
    }
    require(snapshot.hashes==expected.hashes, "AU ROM/RAM/DTCM/save/framework hashes");
}
inline void readiness(const Snapshot& snapshot, uint64_t final_cycle) {
    require(snapshot.get("active_cpu")==0 && snapshot.get("current_slot")==0 &&
            snapshot.get("owner_thread")==1 && snapshot.get("round_active")==1 &&
            snapshot.get("force_tier3")==1, "owner/round/backend");
    for (const auto* key:{"deferred9","deferred7","slot9.deferred","event_break","insn_stop","terminal",
                         "unwinding","halt9","halt7","gpu_stall","card_end","save_dirty","synth_config"})
        require(snapshot.get(key)==0, "ready/stale state: "+std::string(key));
    for (unsigned cpu=0;cpu<2;++cpu) {
        const auto prefix=numbered("irq",cpu==0 ? 9 : 7)+".";
        const auto pending=(snapshot.get(prefix+"ime")&1) &&
                           (snapshot.get(prefix+"ie")&snapshot.get(prefix+"if"));
        require(snapshot.get(prefix+"cached")==uint64_t(pending), "IRQ cache inconsistent");
        require(!pending, "IRQ acceptance/wakeup ready");
    }
    require(snapshot.get("arm7_started")==1 && snapshot.get("arm7_terminal")==0,
            "ARM7 lifecycle state unclassified");
    require(snapshot.get("cycle7")<=(snapshot.get("cycle9")>>1), "ARM7 ahead/unclassified catch-up relation");
    const auto system=snapshot.get("system_timestamp");
    require(system<=(snapshot.get("cycle9")>>1) && (snapshot.get("slot9.target")>>1)>system,
            "scheduler timeline mismatch");
    require(snapshot.get("slice_cap")<=snapshot.get("slot9.target") &&
            snapshot.get("fast_limit")<=snapshot.get("slice_cap"), "stale cap/fast limit");
    const auto final_system=final_cycle>>1;
    require(periodic_next(system)>final_system, "periodic service ready before terminal");
    for (const auto* prefix:{"card", "spi", "auxspi", "sqrt", "wifi"})
        require(snapshot.get(std::string(prefix)+".deadline")>final_system, "peripheral deadline ready");
    for (unsigned index=0;index<8;++index) {
        require(snapshot.get(numbered("dma.",index)+".active")==0, "DMA bus owner ready");
        require(snapshot.get(numbered("timer.",index)+".control")==0, "timer readiness not certified");
    }
    const auto deadline=snapshot.get("div.deadline");
    require(deadline==UINT64_MAX || deadline>final_system, "divider event ready");
    require(bool(snapshot.get("div.control")&0x8000)==(deadline!=UINT64_MAX), "divider busy/deadline disagreement");
}
inline void preflight(const Snapshot& snapshot
#if defined(AW4_ROMFREE_CERTIFICATION)
    , const Snapshot& authority=au_manifest()
#endif
) {
    canonical(snapshot);
#if defined(AW4_ROMFREE_CERTIFICATION)
    manifest_matches(snapshot,authority);
#else
    manifest_matches(snapshot);
#endif
    const auto expected=layout(snapshot);
    require(expected.size()==snapshot.fields.size(), "unknown/missing snapshot fields");
    for (const auto& item:expected) {
        const auto found=snapshot.fields.find(item.first);
        require(found!=snapshot.fields.end() && found->second.width==item.second, "snapshot field width/layout");
    }
    require(snapshot.get("snapshot_ordinal")==snapshot.get("ordinal9"), "stale snapshot ordinal");
    require(snapshot.get(numbered("return.",unsigned(snapshot.get("return_depth")-1)))==snapshot.get("r14"),
            "entry return-stack/LR mismatch");
    const auto cap=cap_from_history(snapshot);
    require(snapshot.get("slot9.target")==snapshot.get("cap.0.after") &&
            snapshot.get("slot9.cycle")==snapshot.get("cap.0.base"), "scheduler/cap origin mismatch");
    uint64_t final_cycle=snapshot.get("cycle9");
    for (unsigned index=0;index<pcs.size();++index) final_cycle=add(final_cycle,cost(snapshot,index));
    require(final_cycle==add(entry_cycle,64), "candidate cost classification differs from AV");
    require(cap>final_cycle, "retained slice cap would return to scheduler");
    readiness(snapshot,final_cycle);
}
inline void prospective(const Snapshot& snapshot, unsigned index) {
    require(snapshot.get("r15")==pcs.at(index), "prospective PC");
    const auto final_cycle=add(snapshot.get("cycle9"),cost(snapshot,index));
    auto cap=snapshot.get("slice_cap");
    const bool divider_write=index==0 || index==2 || index==5 || index==6 || index==7;
    if (divider_write) {
        const auto deadline=add(snapshot.get("cycle9")>>1,34);
        cap=cap ? std::min(cap,twice(deadline)) : twice(deadline);
    }
    require(cap>final_cycle, "prospective cost crosses retained cap");
    require(snapshot.get("deferred9")==0, "prospective deferred cost");
    readiness(snapshot,final_cycle);
    if (index==11) require(snapshot.get("div.control")==0x8001 &&
                           snapshot.get("div.deadline")>(final_cycle>>1), "uncertified final status read");
}
struct Observation {
    task_aw::Kind kind{};
    uint32_t pc=0,address=0,width=0,value=0;
    bool write=false;
    Snapshot state;
};
inline bool same(const Observation& actual, const Observation& expected) {
    return actual.kind==expected.kind && actual.pc==expected.pc && actual.address==expected.address &&
           actual.width==expected.width && actual.value==expected.value && actual.write==expected.write &&
           actual.state==expected.state;
}
inline void append(std::vector<Observation>& plan, task_aw::Kind kind, uint32_t pc,
                   const Snapshot& snapshot, uint32_t address=0, uint32_t width=0,
                   uint32_t value=0, bool write=false) {
    plan.push_back({kind,pc,address,width,value,write,snapshot});
}
inline std::vector<Observation> transcript(const Snapshot& entry) {
    preflight(entry);
    auto state=entry;
    std::vector<Observation> plan;
    for (unsigned index=0;index<pcs.size();++index) {
        const auto pc=pcs[index];
        prospective(state,index);
        append(plan,task_aw::Kind::instruction,pc,state);
        state.put("ordinal9",8,add(state.get("ordinal9"),1));
        const auto opcode=uint32_t(entry.get(address_key("code.",pc)));
        append(plan,task_aw::Kind::access_before,pc,state,pc,4);
        append(plan,task_aw::Kind::access_after,pc,state,pc,4,opcode);
        uint32_t address=0,width=4,value=0;
        bool write=false;
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
            append(plan,task_aw::Kind::access_before,pc,state,address,width,write ? value : 0,write);
            if (write) {
                state.put("div.control",2,0x8001);
                if (index!=0) state.put(index==2 ? "div.nlo" : index==5 ? "div.nhi" :
                                        index==6 ? "div.dlo" : "div.dhi",4,value);
                const auto deadline=add(state.get("cycle9")>>1,34);
                state.put("div.deadline",8,deadline);
                const auto cap=std::min(state.get("slice_cap"),twice(deadline));
                if (cap!=state.get("slice_cap")) {
                    state.put("slice_cap",8,cap);
                    append(plan,task_aw::Kind::cap_change,pc,state);
                    state.put("fast_limit",8,0);
                }
            }
            append(plan,task_aw::Kind::access_after,pc,state,address,width,value,write);
        }
        if (index==1) state.put("r12",4,0);
        if (index==3) state.put("r3",4,4096);
        if (index==4) state.put("r1",4,0x04000298);
        if (index==9) state.put("r14",4,0x02001a24);
        if (index==10) state.put("r1",4,0x04000280);
        if (index==11) state.put("r0",4,0x8001);
        state.put("r15",4,index+1<pcs.size() ? pcs[index+1] : terminal_pc);
        const auto cycles=cost(state,index);
        state.put("cycle9",8,add(state.get("cycle9"),cycles));
        append(plan,task_aw::Kind::cycle_commit,pc,state,0,0,cycles);
        if (index==8) {
            const auto depth=unsigned(state.get("return_depth"));
            require(depth>1, "unclassified enclosing return path");
            state.fields.erase(numbered("return.",depth-1));
            state.put("return_depth",4,depth-1);
        }
        if (index==9) {
            const auto depth=unsigned(state.get("return_depth"));
            state.put(numbered("return.",depth),4,0x02001a24);
            state.put("return_depth",4,depth+1);
        }
        append(plan,task_aw::Kind::retired,pc,state);
    }
    require(state.get("r15")==terminal_pc && state.get("cycle9")==entry_cycle+64,
            "modeled terminal mismatch");
    return plan;
}
}
