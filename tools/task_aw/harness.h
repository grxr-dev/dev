#pragma once
#include "bridge.h"
#include <stdexcept>
#include <utility>

namespace task_aw {
inline void require(bool valid, const std::string& why) {
    if (!valid) throw std::runtime_error(why);
}
inline void exact(const Snapshot& actual, const Snapshot& expected) {
    require(actual.values == expected.values, "numeric snapshot mismatch/missing/extra");
    require(actual.bytes == expected.bytes, "byte snapshot mismatch/missing/extra");
}
struct Contract {
    Snapshot entry;
    std::vector<Event> ordered;
    bool source_reviewed=false;
    bool passive_timing_certified=false;
    bool provenance_certified=false;
};
inline void preflight(const Snapshot& actual, const Contract& contract,
                      size_t ledger_size) {
    require(contract.source_reviewed && contract.passive_timing_certified &&
            contract.provenance_certified, "unsealed source/timing/provenance contract");
    require(!contract.ordered.empty() && ledger_size==0, "missing plan or nonempty ledger");
    const char* needed[] = {"pc","cycle9","ordinal9","cycle7","ordinal7",
        "active_cpu","system_timestamp","slice_cap","slice_cap_source",
        "fast_limit","deferred","round_active","owner_thread","divcnt",
        "div_deadline","divider_event_identity","irq9_ready","irq7_ready",
        "arm7_ready","device_ready","stop_ready","code_cached",
        "literal_numd","mmio_numd","snapshot_ordinal","schema"};
    for (const auto* key : needed)
        require(actual.values.count(key)!=0 && contract.entry.values.count(key)!=0,
                std::string("missing required field: ")+key);
    const char* blobs[] = {"cpu","ram","dtcm","save","opcodes","cp15",
                           "timing","scheduler","runtime","io","devices"};
    for (const auto* key : blobs)
        require(actual.bytes.count(key)!=0 && !actual.bytes.at(key).empty() &&
                contract.entry.bytes.count(key)!=0,
                std::string("missing required bytes: ")+key);
    exact(actual,contract.entry);
    auto get = [&](const char* key) { return actual.values.at(key); };
    const uint32_t registers[] = {0x1000,0x04000280,0x04000290,1,
        0x020ea1bc,0,0xda,0x020e9a00,0x1000,0x1000,0x020fd00c,0,0x48c,
        0x027e3654,0x02001a20,0x02001980};
    for (unsigned index=0;index<16;++index) {
        const auto key="r"+std::to_string(index);
        require(actual.values.count(key) && actual.values.at(key)==registers[index],
                "wrong/missing AU register: "+key);
    }
    require(actual.values.count("cpsr") && get("cpsr")==0x1f,"wrong AU flags/mode");
    require(get("schema")==1 && get("pc")==0x02001980 && get("active_cpu")==0,
            "wrong entry/schema/CPU");
    require(get("cycle9")==3416875721ULL && get("ordinal9")==281098008 &&
            get("snapshot_ordinal")==get("ordinal9"), "wrong/stale AU clock/ordinal");
    require(get("ordinal7")==96026779 && get("cycle7")==1708437825,
            "wrong AU ARM7 slot observation");
    require(get("slice_cap")==0 || get("slice_cap")>3416875785ULL,
            "unsafe entry cap");
    require(get("slice_cap_source")!=0 && get("owner_thread")==1 &&
            get("round_active")==1, "unknown cap source or capture context");
    for (auto key : {"irq9_ready","irq7_ready","arm7_ready","device_ready",
                     "stop_ready","deferred"})
        require(get(key)==0,std::string("unsafe readiness/debt: ")+key);
    require(get("code_cached")==1 && get("literal_numd")==3 && get("mmio_numd")==8,
            "uncertified timing class");
    require(get("div_deadline")==UINT64_MAX ||
            get("div_deadline")>(get("cycle9")>>1),"due inherited divider");
    require(get("divider_event_identity")==get("div_deadline"),"wrong scalar divider event identity");
    require(((get("divcnt")&0x8000)!=0)==(get("div_deadline")!=UINT64_MAX),
            "inconsistent busy/deadline model");
}
class Ledger {
    const Contract& contract;
    std::vector<Event> accepted;
    bool failed=false;
    bool armed=false;
public:
    explicit Ledger(const Contract& plan):contract(plan) {}
    void arm(const Snapshot& snapshot) {
        try {
            require(!failed && !armed,"rearm/failed harness");
            preflight(snapshot,contract,accepted.size());
            armed=true;
        } catch (...) { failed=true; throw; }
    }
    void observe(const Event& actual) {
        try {
            require(armed && !failed && accepted.size()<contract.ordered.size(),"ledger unarmed/exhausted/failed");
            require(actual.kind!=Kind::irq && actual.kind!=Kind::scheduler &&
                    actual.kind!=Kind::device && actual.kind!=Kind::arm7,
                    "forbidden IRQ/scheduler/device/ARM7 before side effect");
            const auto& expected=contract.ordered[accepted.size()];
            require(actual.kind==expected.kind && actual.pc==expected.pc &&
                    actual.address==expected.address && actual.width==expected.width &&
                    actual.value==expected.value && actual.write==expected.write,
                    "ordered event mismatch");
            exact(actual.state,expected.state);
            accepted.push_back(actual);
        } catch (...) { failed=true; throw; }
    }
    void terminal(const Snapshot& final, const Snapshot& expected) {
        try {
            require(armed && !failed && accepted.size()==contract.ordered.size(),"incomplete/failed terminal ledger");
            exact(final,expected);
        } catch (...) { failed=true; throw; }
    }
    size_t size() const { return accepted.size(); }
};
}
