#include <filesystem>
#include <fstream>
#include <iostream>
#include <functional>
#include "controller.h"
#include "fixture.h"

using namespace task_aw2;
namespace {
size_t assertions=0;
void check(bool condition, const std::string& reason) {
    ++assertions;
    require(condition,reason);
}
void rejects(const std::function<void()>& action, const std::string& reason) {
    bool rejected=false;
    try { action(); } catch (const std::exception&) { rejected=true; }
    check(rejected,reason);
}
void mutate_reject(const Snapshot& original, const std::string& key, uint64_t value) {
    auto mutated=original;
    mutated.put(key,mutated.fields.at(key).width,value);
    rejects([&] { preflight(mutated); },"preflight mutation: "+key);
}
void unit() {
    const auto original=synthetic::entry();
    const auto fingerprint=digest(original);
    preflight(original);
    check(digest(original)==fingerprint,"passive preflight does not mutate copied state");
    check(decode(canonical(original))==original,"canonical round trip");
    check(digest(decode(canonical(original)))==fingerprint,"round trip hash");
    const uint8_t abc[]={'a','b','c'};
    check(brainage_custom::resource_detail::sha256(abc,3)==
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA256 known vector");
    Snapshot endian;
    endian.put("test",4,0x12345678);
    const auto bytes=canonical(endian);
    check(bytes[17]==0x78 && bytes[18]==0x56 && bytes[19]==0x34 && bytes[20]==0x12,"little-endian fixed width");
    for (const auto& item:original.fields) {
        auto mutated=original;
        mutated.fields.at(item.first).value^=1;
        check(digest(mutated)!=fingerprint,"protected logical field affects canonical identity: "+item.first);
        mutated=original;
        mutated.fields.erase(item.first);
        rejects([&] { preflight(mutated); },"missing field fails: "+item.first);
        mutated=original;
        mutated.fields.at(item.first).width=item.second.width==8 ? 4 : 8;
        rejects([&] { preflight(mutated); },"field width fails: "+item.first);
    }
    for (const auto& item:au_manifest().fields) {
        auto mutated=original;
        mutated.fields.at(item.first).value^=1;
        rejects([&] { preflight(mutated); },"immutable AU manifest scalar: "+item.first);
    }
    for (const auto& item:original.hashes) {
        auto mutated=original;
        auto& hash=mutated.hashes.at(item.first);
        hash[0]=hash[0]=='0' ? '1' : '0';
        check(digest(mutated)!=fingerprint,"hash identity protects: "+item.first);
        rejects([&] { preflight(mutated); },"immutable AU manifest digest: "+item.first);
        mutated=original;
        mutated.hashes.erase(item.first);
        rejects([&] { preflight(mutated); },"missing manifest digest: "+item.first);
    }
    auto malformed=canonical(original);
    malformed[4]=2;
    rejects([&] { decode(malformed); },"unknown schema rejected");
    malformed=canonical(original);
    malformed.pop_back();
    rejects([&] { decode(malformed); },"truncated canonical bytes");
    malformed=canonical(original);
    malformed.push_back(0);
    rejects([&] { decode(malformed); },"extra canonical bytes");
    malformed=canonical(original);
    malformed[6]=255; malformed[7]=255;
    rejects([&] { decode(malformed); },"oversized canonical field count");
    auto unknown=original;
    unknown.put("caller_says_safe",1,1);
    rejects([&] { preflight(unknown); },"caller attestation/unknown field rejected");
    for (const auto* key:{"event_break","insn_stop","terminal","unwinding","halt9","halt7","gpu_stall",
                         "card_end","save_dirty","synth_config","deferred9","deferred7","slot9.deferred"})
        mutate_reject(original,key,1);
    for (const auto* key:{"owner_thread","round_active","force_tier3","arm7_started","timing.valid"})
        mutate_reject(original,key,0);
    mutate_reject(original,"active_cpu",1);
    mutate_reject(original,"current_slot",1);
    mutate_reject(original,"arm7_terminal",1);
    mutate_reject(original,"timing.class",2);
    mutate_reject(original,"timing.generation",10);
    mutate_reject(original,"timing.publication",10);
    mutate_reject(original,"cp15.control",0);
    mutate_reject(original,"cp15.dcache",0);
    mutate_reject(original,"cp15.icache",0);
    mutate_reject(original,"cp15.region.0",0);
    mutate_reject(original,"cp15.region.7",0x0200002b);
    mutate_reject(original,"cp15.region.1",0x0200002b);
    mutate_reject(original,"cp15.dcache",3);
    mutate_reject(original,"itcm.enabled",1);
    auto tcm=original;
    tcm.put("itcm.enabled",1,1);
    tcm.put("itcm.base",4,0x02000000);
    tcm.put("itcm.size",8,0x4000);
    rejects([&] { preflight(tcm); },"ITCM overlaps candidate");
    mutate_reject(original,"dtcm_map.base",0x02000000);
    mutate_reject(original,"cap.0.kind",2);
    mutate_reject(original,"cap.0.cpu",1);
    mutate_reject(original,"cap.0.before",1);
    mutate_reject(original,"cap.0.cycle",entry_cycle+1);
    mutate_reject(original,"cap.0.after",entry_cycle+64);
    mutate_reject(original,"slice_cap",entry_cycle+64);
    mutate_reject(original,"fast_limit",UINT64_MAX);
    mutate_reject(original,"snapshot_ordinal",0);
    mutate_reject(original,"return.1",0x02000000);
    mutate_reject(original,"slot9.cycle",entry_cycle);
    mutate_reject(original,"slot9.target",entry_cycle);
    mutate_reject(original,"div.deadline",(entry_cycle>>1)+1);
    mutate_reject(original,"div.control",0x8000);
    for (const auto* prefix:{"card","spi","auxspi","sqrt","wifi"})
        mutate_reject(original,std::string(prefix)+".deadline",entry_cycle>>1);
    for (unsigned index=0;index<8;++index) {
        mutate_reject(original,numbered("dma.",index)+".active",1);
        mutate_reject(original,numbered("timer.",index)+".control",0x80);
    }
    for (const auto* prefix:{"irq9.", "irq7."}) {
        auto irq=original;
        irq.put(std::string(prefix)+"ime",4,1);
        irq.put(std::string(prefix)+"ie",4,8);
        irq.put(std::string(prefix)+"if",4,8);
        irq.put(std::string(prefix)+"cached",4,1);
        rejects([&] { preflight(irq); },"IRQ pending/eligible");
        mutate_reject(original,std::string(prefix)+"cached",1);
    }
    mutate_reject(original,"cycle7",entry_cycle>>1);
    rejects([&] { add(UINT64_MAX,1); },"cycle wrap rejected");
    rejects([&] { twice(UINT64_MAX); },"system-to-CPU wrap rejected");
    rejects([&] { periodic_next(UINT64_MAX); },"periodic arithmetic overflow rejected");
    auto retained=original;
    retained.put("cap.count",4,2);
    for (const auto& item:layout(retained))
        if (!retained.fields.count(item.first)) retained.put(item.first,item.second,0);
    retained.put("cap.1.kind",1,1);
    retained.put("cap.1.cycle",8,entry_cycle-1);
    retained.put("cap.1.before",8,original.get("slice_cap"));
    retained.put("cap.1.deadline",8,(entry_cycle+65)/2);
    retained.put("cap.1.after",8,entry_cycle+65);
    retained.put("slice_cap",8,entry_cycle+65);
    retained.put("fast_limit",8,0);
    preflight(retained);
    check(cap_from_history(retained)==entry_cycle+65,"earlier shortened cap derived, not reset by later deadline");
    retained.put("cap.1.deadline",8,(entry_cycle+63)/2);
    retained.put("cap.1.after",8,entry_cycle+63);
    retained.put("slice_cap",8,entry_cycle+63);
    rejects([&] { preflight(retained); },"retained shortened cap aborts before dispatch");
    auto overflow=original;
    overflow.put("cap.0.quantum",8,UINT64_MAX);
    rejects([&] { preflight(overflow); },"cap addition overflow");
    const auto plan=transcript(original);
    check(plan.size()==77,"complete fetch/data/model/cycle transcript length");
    constexpr std::array<uint32_t,12> costs={8,1,8,1,3,8,8,8,4,4,3,8};
    uint64_t cumulative=0;
    unsigned instruction=0,fetches=0,literals=0,writes=0,status_reads=0,cap_changes=0;
    Ledger ledger(original);
    for (const auto& event:plan) {
        check(ledger.accept(event),"exact synthetic transcript accepted");
        if (event.kind==task_aw::Kind::cycle_commit) {
            cumulative+=costs[instruction++];
            check(event.value==costs[instruction-1] && event.state.get("cycle9")==entry_cycle+cumulative,
                  "per-instruction source-derived cost/cycle");
        }
        if (event.kind==task_aw::Kind::access_after) {
            if (event.address==event.pc) ++fetches;
            else if (event.address<0x04000000) ++literals;
            else if (event.write) {
                ++writes;
                check(event.state.get("div.deadline")==((event.state.get("cycle9")>>1)+34),
                      "MMIO model happens before cycle commit");
                check(event.state.get("div.qlo")==original.get("div.qlo") &&
                      event.state.get("div.rhi")==original.get("div.rhi"),"inherited divider result not invented");
            } else { ++status_reads; check(event.value==0x8001,"one certified conditional busy status"); }
        }
        if (event.kind==task_aw::Kind::cap_change) ++cap_changes;
    }
    check(fetches==12 && literals==2 && writes==5 && status_reads==1 && cap_changes==1,"exact access counts");
    check(ledger.complete() && ledger.finish(),"exact terminal");
    const auto& final=plan.back().state;
    check(final.get("r15")==terminal_pc && final.get("r0")==0x8001 && final.get("r14")==0x02001a24,
          "conditional final CPU registers");
    check(final.get("div.deadline")==1708437913 && final.get("slice_cap")==3416875788ULL,
          "deadline replacements retain first shorter cap");
    check(final.get("cycle7")==original.get("cycle7") && final.get("ordinal7")==original.get("ordinal7"),
          "ARM7 lag is retained, not normalized");
    check(final.hashes==original.hashes && final.get("logical_saves")==0 && final.get("flash_commits")==0,
          "synthetic protected hashes and save counts invariant");
    check(!ledger.accept(plan.back()) && !ledger.failure.empty(),"extra terminal event sticky failure");
    for (size_t index=0;index<plan.size();++index) {
        Ledger wrong(original);
        for (size_t earlier=0;earlier<index;++earlier) require(wrong.accept(plan[earlier]),"prefix");
        auto event=plan[index];
        event.value^=1;
        check(!wrong.accept(event),"wrong access/opcode/cost value rejected");
        check(!wrong.accept(plan[index]),"sticky failure cannot recover");
        Ledger missing(original);
        for (size_t earlier=0;earlier<index;++earlier) require(missing.accept(plan[earlier]),"prefix");
        check(index+1<plan.size() ? !missing.accept(plan[index+1]) : !missing.finish(),"missing ordered event rejected");
    }
    for (auto forbidden:{task_aw::Kind::irq,task_aw::Kind::arm7,task_aw::Kind::scheduler,task_aw::Kind::device}) {
        Ledger wrong(original);
        auto event=plan.front(); event.kind=forbidden;
        check(!wrong.accept(event),"unexpected service rejected");
    }
    for (const auto* field:{"cycle9","div.deadline","slice_cap","r0","ordinal9"}) {
        Ledger wrong(original);
        auto event=plan.front(); event.state.fields.at(field).value^=1;
        check(!wrong.accept(event),"unexpected event snapshot state");
    }
    for (size_t index=0;index<plan.size();++index) {
        Ledger duplicate(original);
        for (size_t earlier=0;earlier<=index;++earlier) require(duplicate.accept(plan[earlier]),"prefix");
        check(!duplicate.accept(plan[index]),"duplicate event rejected");
        if (plan[index].kind!=task_aw::Kind::cycle_commit &&
            !(plan[index].kind==task_aw::Kind::access_after && plan[index].write)) continue;
        Ledger wrong_state(original);
        for (size_t earlier=0;earlier<index;++earlier) require(wrong_state.accept(plan[earlier]),"prefix");
        auto event=plan[index];
        const auto field=event.kind==task_aw::Kind::cycle_commit ? "cycle9" : "div.deadline";
        event.state.fields.at(field).value^=1;
        check(!wrong_state.accept(event),"committed cost clock/post-MMIO deadline mismatch");
    }
    for (unsigned mode=0;mode<4;++mode) {
        Ledger wrong(original);
        auto event=plan[3];
        require(wrong.accept(plan[0]) && wrong.accept(plan[1]) && wrong.accept(plan[2]),"prefix");
        if (mode==0) event.address^=4;
        if (mode==1) event.width=4;
        if (mode==2) event.write=false;
        if (mode==3) event.state.put("cycle9",8,entry_cycle+8);
        check(!wrong.accept(event),"MMIO address/width/direction/precommit ordering");
    }
    rejects([&] { reject_legacy_copy(task_aw::Snapshot{}); },"raw AW object copies cannot arm canonical controller");
    check(task_aw::observer==nullptr && task_aw::audit==nullptr,"disabled observer initial state");
    task_aw::emit(task_aw::Kind::device);
    task_aw::emit(task_aw::Kind::irq);
    check(task_aw::observer==nullptr && digest(original)==fingerprint,"disabled path performs no capture/disposal");
    std::cout<<"AW2 ROM-free synthetic assertions: "<<assertions<<"\n";
    std::cout<<"entry_sha256="<<fingerprint<<"\nmanifest_sha256="<<digest(au_manifest())<<"\n";
}
Snapshot supplied;
Snapshot passive_fixture() { return supplied; }
Snapshot legacy_fixture() { return reject_legacy_copy(task_aw::Snapshot{}); }
std::filesystem::path child_root;
void sentinel(const std::string& name) { std::ofstream(child_root/name)<<"REACHED\n"; }
struct ShutdownSentinel { ~ShutdownSentinel() { sentinel("destructor"); } };
void shutdown_sentinel() { sentinel("atexit"); }
void child(const std::string& mode, const std::filesystem::path& root) {
    child_root=root;
    static ShutdownSentinel shutdown;
    std::atexit(shutdown_sentinel);
    auto* output=std::fopen((root/"audit.jsonl").string().c_str(),"wb");
    require(output!=nullptr,"child audit open");
    supplied=synthetic::entry();
    auto plan=transcript(supplied);
    if (mode=="preflight") supplied.put("slice_cap",8,entry_cycle+64);
    Controller controller;
    controller.start(output,mode=="legacy" ? legacy_fixture : passive_fixture);
    for (size_t index=0;index<plan.size();++index) {
        if (mode=="missing" && index==plan.size()-1) break;
        auto event=plan[index];
        if (mode=="wrong-mmio" && event.write && event.kind==task_aw::Kind::access_before) event.address^=4;
        if (mode=="irq" && index==10) event.kind=task_aw::Kind::irq;
        if (mode=="cost" && event.kind==task_aw::Kind::cycle_commit) event.value^=1;
        if (mode=="state" && index==20) event.state.put("deferred9",4,1);
        supplied=event.state;
        task_aw::emit(event.kind,event.pc,event.address,event.width,event.value,event.write);
    }
    controller.end_stream();
    sentinel("scheduler-tail");
    sentinel("device-service");
    sentinel("irq-acceptance");
    sentinel("arm7-catchup");
    sentinel("shutdown-save");
}
}
int main(int argc, char** argv) {
    try {
        if (argc==3) { child(argv[1],argv[2]); return 90; }
        unit();
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<error.what()<<"\n";
        return 1;
    }
}
