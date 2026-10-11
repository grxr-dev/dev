#include "harness.h"
#include <functional>
#include <iostream>

using namespace task_aw;
unsigned assertions=0;
void check(bool value) { ++assertions; require(value,"test assertion"); }
void rejects(const std::function<void()>& action) {
    bool rejected=false;
    try { action(); } catch (const std::runtime_error&) { rejected=true; }
    check(rejected);
}
Contract fixture() {
    Contract plan;
    plan.source_reviewed=plan.passive_timing_certified=plan.provenance_certified=true;
    plan.entry.values={{"schema",1},{"pc",0x02001980},{"cycle9",3416875721ULL},
        {"ordinal9",281098008},{"snapshot_ordinal",281098008},
        {"cycle7",1708437825},{"ordinal7",96026779},{"active_cpu",0},
        {"system_timestamp",1708437800},{"slice_cap",3416875900ULL},
        {"slice_cap_source",1},{"fast_limit",0},{"deferred",0},{"round_active",1},
        {"owner_thread",1},{"divcnt",0},{"div_deadline",UINT64_MAX},
        {"divider_event_identity",UINT64_MAX},{"irq9_ready",0},{"irq7_ready",0},
        {"arm7_ready",0},{"device_ready",0},{"stop_ready",0},{"code_cached",1},
        {"literal_numd",3},{"mmio_numd",8}};
    const uint32_t registers[] = {0x1000,0x04000280,0x04000290,1,
        0x020ea1bc,0,0xda,0x020e9a00,0x1000,0x1000,0x020fd00c,0,0x48c,
        0x027e3654,0x02001a20,0x02001980};
    for (unsigned index=0;index<16;++index)
        plan.entry.values["r"+std::to_string(index)]=registers[index];
    plan.entry.values["cpsr"]=0x1f;
    for (auto key : {"cpu","ram","dtcm","save","opcodes","cp15","timing",
                     "scheduler","runtime","io","devices"})
        plan.entry.bytes[key]={1,2,3,4};
    plan.ordered={{Kind::instruction,0x02001980,0,0,0,false,plan.entry},
                  {Kind::access_before,0x02001980,0x04000280,2,1,true,plan.entry},
                  {Kind::cap_change,0x02001980,0,0,0,false,plan.entry},
                  {Kind::access_after,0x02001980,0x04000280,2,1,true,plan.entry},
                  {Kind::cycle_commit,0x02001980,0,0,8,false,plan.entry},
                  {Kind::retired,0x02001980,0,0,0,false,plan.entry}};
    return plan;
}
void marker(const std::string& name) {
    auto* output=std::fopen(name.c_str(),"wb");
    if (output) { std::fputs("reached",output); std::fclose(output); }
}
struct ShutdownSentinel {
    std::string path;
    ~ShutdownSentinel() { marker(path); }
};
void child(const std::string& root, bool failure) {
    static ShutdownSentinel shutdown{root+"/destructor"};
    audit=std::fopen((root+"/terminal.jsonl").c_str(),"wb");
    require(audit!=nullptr,"audit file");
    observer=failure ? +[](const Event&) { throw std::runtime_error("synthetic IRQ tripwire"); }
                     : +[](const Event&) {
                           auto plan=fixture();
                           Ledger ledger(plan);
                           ledger.arm(plan.entry);
                           for (const auto& event : plan.ordered) ledger.observe(event);
                           ledger.terminal(plan.entry,plan.entry);
                           require(record_snapshot(audit,plan.entry,ledger.size()),"terminal audit");
                           std::fputs("{\"event\":\"terminal\",\"pc\":33561016,\"tail\":false}\n",audit);
                           dispose(audit,73);
                       };
    emit(failure?Kind::irq:Kind::retired,0x020019b4);
    marker(root+"/scheduler-tail");
    marker(root+"/device-service");
    marker(root+"/arm7-catchup");
    marker(root+"/shutdown-save");
}
int main(int argc,char** argv) {
    if (argc==3) { child(argv[2],std::string(argv[1])=="failure"); return 99; }
    auto plan=fixture();
    const auto before=plan.entry;
    preflight(plan.entry,plan,0);
    exact(before,plan.entry);
    auto pending=plan;
    pending.entry.values["divcnt"]=0x8001;
    pending.entry.values["div_deadline"]=1708437999;
    pending.entry.values["divider_event_identity"]=1708437999;
    preflight(pending.entry,pending,0);
    pending.entry.values["divider_event_identity"]+=1;
    rejects([&] { preflight(pending.entry,pending,0); });
    pending.entry.values["divider_event_identity"]-=1;
    pending.entry.values["divcnt"]=1;
    rejects([&] { preflight(pending.entry,pending,0); });
    for (const auto& field : plan.entry.values) {
        auto changed=plan.entry; changed.values[field.first]^=1;
        rejects([&] { preflight(changed,plan,0); });
        changed=plan.entry; changed.values.erase(field.first);
        rejects([&] { preflight(changed,plan,0); });
    }
    for (const auto& field : plan.entry.bytes) {
        auto changed=plan.entry; changed.bytes[field.first][0]^=1;
        rejects([&] { preflight(changed,plan,0); });
        changed=plan.entry; changed.bytes.erase(field.first);
        rejects([&] { preflight(changed,plan,0); });
    }
    for (auto key : {"slice_cap","div_deadline","irq9_ready","irq7_ready",
                     "arm7_ready","device_ready","stop_ready","deferred",
                     "code_cached","literal_numd","mmio_numd","owner_thread"}) {
        auto changed=plan;
        changed.entry.values[key]=std::string(key)=="slice_cap"?3416875785ULL:
            std::string(key)=="div_deadline"?1708437800:9;
        rejects([&] { preflight(changed.entry,changed,0); });
    }
    for (unsigned seal=0;seal<3;++seal) {
        auto changed=plan;
        if (seal==0) changed.source_reviewed=false;
        if (seal==1) changed.passive_timing_certified=false;
        if (seal==2) changed.provenance_certified=false;
        rejects([&] { preflight(changed.entry,changed,0); });
    }
    rejects([&] { preflight(plan.entry,plan,1); });
    auto extra=plan.entry; extra.values["unknown"]=0;
    rejects([&] { preflight(extra,plan,0); });
    auto empty=plan; empty.ordered.clear();
    rejects([&] { preflight(empty.entry,empty,0); });
    Ledger incomplete(plan); incomplete.arm(plan.entry);
    rejects([&] { incomplete.terminal(plan.entry,plan.entry); });
    rejects([&] { incomplete.observe(plan.ordered.front()); });
    Ledger good(plan); good.arm(plan.entry);
    for (const auto& event : plan.ordered) good.observe(event);
    good.terminal(plan.entry,plan.entry);
    rejects([&] { good.observe(plan.ordered.front()); });
    for (auto kind : {Kind::irq,Kind::scheduler,Kind::device,Kind::arm7}) {
        Ledger bad(plan); bad.arm(plan.entry);
        rejects([&] { bad.observe(Event{kind,0,0,0,0,false,{}}); });
        rejects([&] { bad.observe(plan.ordered.front()); });
        rejects([&] { bad.terminal(plan.entry,plan.entry); });
    }
    Ledger reordered(plan); reordered.arm(plan.entry);
    rejects([&] { reordered.observe(plan.ordered[1]); });
    Ledger unarmed(plan);
    rejects([&] { unarmed.observe(plan.ordered.front()); });
    rejects([&] { unarmed.arm(plan.entry); });
    observer=nullptr;
    unsigned normal_tail=0;
    emit(Kind::retired); ++normal_tail;
    emit(Kind::device); ++normal_tail;
    emit(Kind::arm7); ++normal_tail;
    check(normal_tail==3 && !enabled());
    std::cout << "ROM-free preflight/ledger/disabled tests: " << assertions << " assertions\n";
}
