#include <fstream>
#include <iostream>
#include "fixture.h"
#include "controller.h"
#include "synthetic_manifest.h"
#include "runtime_arm.h"
#include "state.h"

namespace {
using namespace task_aw4;
std::string root,mode;
unsigned assertions=0;
std::vector<Observation> observed;
unsigned source_calls=0;
Snapshot binding_source() {
    if (mode=="bind-torn" && ++source_calls==2) fixture::mutate("cpu");
    return task_aw3::passive();
}
void check(bool condition,const std::string& reason) { ++assertions; require(condition,reason); }
template<class Action> void rejects(Action action,const std::string& reason) {
    bool rejected=false; try { action(); } catch (const std::exception&) { rejected=true; }
    check(rejected,reason);
}
void marker(const std::string& name) { std::ofstream(root+"/"+name)<<"REACHED"; }
void persistence() { marker("persistence"); }
struct Shutdown { ~Shutdown() { marker("shutdown"); } };
void tail() {
    for (const auto* name:{"scheduler","device","IRQ","ARM7","guest","old-halt"}) marker(name);
}
void collect(const task_aw::Event& event) {
    observed.push_back({event.kind,event.pc,event.address,event.width,event.value,event.write,task_aw3::passive()});
}
void setup(FILE* output) {
    task_aw3::arm(output);
    const std::string identity="AW4 ROM-free fixture identity; not Brain Age";
    task_aw3::rom_identity=gba::sha1(reinterpret_cast<const uint8_t*>(identity.data()),identity.size()).hex();
    task_aw3::rom_epoch=1;
    fixture::bus_begin(); fixture::io_begin(); fixture::scheduler_begin(); fixture::spu_begin(); fixture::runtime_begin();
    if (mode=="success-banks" || mode=="unit-banks") fixture::runtime_banks();
}
void mutation() {
    if (mode=="ordinal") fixture::mutate("ordinal");
    if (mode=="journal") task_aw3::history.pop_back();
    if (mode=="journal-extra") {
        const auto& last=task_aw3::history.back();
        task_aw3::reschedule(0,g_runtime_cycles,last.after,last.deadline);
    }
    if (mode=="source") task_aw3::history.back().source=2;
    if (mode=="epoch") ++task_aw3::history.back().epoch;
    if (mode=="serial") ++task_aw3::history.back().serial;
    if (mode=="old-cap") ++task_aw3::history.back().before;
    if (mode=="new-cap") ++task_aw3::history.back().after;
    if (mode=="deadline") ++task_aw3::history.back().deadline;
    if (mode=="import") task_aw3::invalidate();
    if (mode=="latch") fixture::bus_mutate("latch");
    if (mode=="yield") fixture::mutate("latch");
    if (mode=="irq") fixture::io_mutate("irq");
    if (mode=="arm7") fixture::scheduler_mutate("arm7");
    if (mode=="device") fixture::io_mutate("device");
    if (mode=="scheduler") fixture::scheduler_mutate("event");
    if (mode=="image") fixture::bus_mutate("image");
    if (mode=="save") fixture::io_mutate("save");
    if (mode=="cpu") fixture::mutate("cpu");
    if (mode=="divider") fixture::io_mutate("divider");
    if (mode=="debt") fixture::mutate("debt");
    if (mode=="cap") fixture::mutate("cap");
}
void stream() {
    static constexpr uint32_t addresses[12]={0x04000280,0,0x04000290,0,0x020019ac,0x04000294,
        0x04000298,0x0400029c,0,0,0x020019e4,0x04000280};
    const auto authority=task_aw2::au_manifest();
    for (unsigned index=0;index<12;++index) {
        const auto pc=task_aw2::pcs[index];
        if (index==1) mutation();
        task_aw::emit(Kind::instruction,pc);
        if (mode=="extra" && index==1) task_aw::emit(Kind::instruction,pc);
        fixture::runtime_fetch();
        const auto code_cost=runtime_code_cycles(pc);
        task_aw::emit(Kind::access_before,pc,pc,4);
        task_aw::emit(Kind::access_after,pc,pc,4,uint32_t(authority.get(task_aw2::address_key("code.",pc))));
        const auto address=addresses[index];
        uint32_t data_cost=0;
        if (address) {
            const bool write=index==0 || index==2 || index==5 || index==6 || index==7;
            const uint32_t width=index==0 || index==11 ? 2 : 4;
            uint32_t value=index==0 ? 1 : index==5 || index==6 ? 4096 : index==4 ? 0x04000298 :
                index==10 ? 0x04000280 : index==11 ? 0x8001 : 0;
            data_cost=runtime_mem_cycles(address,width,0);
            task_aw::emit(Kind::access_before,pc,address,width,mode=="wrong-mmio" && index==2 ? 99 : write ? value : 0,write);
            if (write) fixture::io_model_write(index);
            task_aw::emit(Kind::access_after,pc,address,width,value,write);
        }
        const auto committed=index==8 ? arm9_refill_cycles(0x02001a20) : index==9 ? arm9_refill_cycles(0x020019b0) :
            arm9_cycle_combine(code_cost,data_cost,0,data_cost ? 1 : 0);
        fixture::runtime_commit(index,committed);
        if (mode=="cost" && index==3) fixture::mutate("cost");
        task_aw::emit(Kind::cycle_commit,pc,0,0,committed);
        fixture::runtime_retire(index);
        if (mode=="missing" && index==11) return;
        task_aw::emit(Kind::retired,pc);
        if (index==11 && mode!="unit" && mode!="unit-banks") tail();
        fixture::runtime_poll();
    }
}
void unit(const Snapshot& entry) {
    const auto authority=synthetic_authority();
    task_aw4::entry(entry,authority);
    check(task_aw3::passive()==entry,"real passive provider repeat is nonmutating");
    check(task_aw2::decode(task_aw2::canonical(entry))==entry,"full canonical roundtrip");
    rejects([&] { task_aw4::entry(entry,task_aw2::au_manifest()); },"synthetic identities never admitted as actual AU");
    Ledger origin(entry,authority);
    for (const auto& field:entry.fields) {
        auto changed=entry; changed.fields.erase(field.first);
        rejects([&] { task_aw4::entry(changed,authority); },"every required full-entry scalar omission rejects");
        changed=entry; changed.fields.at(field.first)={uint8_t(field.second.width==8 ? 4 : 8),0};
        rejects([&] { task_aw4::entry(changed,authority); },"every required full-entry scalar width mismatch rejects");
    }
    for (const auto& field:authority.fields) {
        auto changed=entry; changed.fields.at(field.first).value^=1;
        rejects([&] { task_aw4::entry(changed,authority); },"every manifest scalar mutation rejects");
    }
    for (const auto& identity:authority.hashes) {
        auto changed=entry; changed.hashes.at(identity.first)[0]^=1;
        rejects([&] { task_aw4::entry(changed,authority); },"every manifest identity mutation rejects");
    }
    task_aw::observer=collect; stream(); task_aw::observer=nullptr;
    auto ledger=origin;
    check(observed.size()==77,"actual provider delivers exactly 77 observations");
    for (const auto& event:observed) check(ledger.accept(event,ledger.previous),ledger.failure);
    check(ledger.complete(),"actual provider completes reconciled ledger");
    check(observed.back().state.get("cap.count")==6,"five reschedules including retained-cap replacements");
    check(observed.back().state.get("ordinal9")==entry.get("ordinal9")+12,"exact ordinal increments");
    check(observed.back().state.get("hidden.fast_publishes")==entry.get("hidden.fast_publishes")+1,"post-retire fast-limit republished exactly once");
    check(observed.back().state.get("hidden.force_misses")==entry.get("hidden.force_misses")+(mode=="unit-banks" ? 12 : 0),"exact passive bank classification predicts forced misses");
    check(observed.back().state.hashes==entry.hashes,"actual ROM-free images/save remain unchanged");
    for (size_t index=0;index<observed.size();++index) {
        auto prefix=origin;
        for (size_t cursor=0;cursor<index;++cursor) require(prefix.accept(observed[cursor],prefix.previous),"prefix");
        auto duplicate=prefix;
        if (index) check(!duplicate.accept(observed[index-1],duplicate.previous),"reordered/duplicate event rejects");
        auto missing=prefix;
        if (index+1<observed.size()) check(!missing.accept(observed[index+1],missing.previous),"missing/extra event rejects");
        auto changed=observed[index]; changed.pc^=4;
        check(!prefix.accept(changed,prefix.previous),"wrong event PC rejects");
        check(!prefix.accept(observed[index],prefix.previous),"sticky failure cannot recover");
    }
    for (const size_t index:{size_t{0},size_t{4},size_t{18},size_t{76}}) {
        auto prefix=origin;
        for (size_t cursor=0;cursor<index;++cursor) require(prefix.accept(observed[cursor],prefix.previous),"prefix");
        const auto& event=observed[index];
        for (const auto& field:event.state.fields) {
            auto changed=event; changed.state.fields.at(field.first).value^=1;
            auto guard=prefix;
            check(!guard.accept(changed,guard.previous),"every immutable/evolving/constant scalar mutation rejects: "+field.first);
            changed=event; changed.state.fields.erase(field.first); guard=prefix;
            check(!guard.accept(changed,guard.previous),"every protected scalar omission rejects");
        }
        for (const auto& identity:event.state.hashes) {
            auto changed=event; changed.state.hashes.at(identity.first)[0]^=1; auto guard=prefix;
            check(!guard.accept(changed,guard.previous),"every identity mutation rejects");
        }
    }
    auto bad_chain=origin;
    check(!bad_chain.accept(observed[0],std::string(64,'0')),"chained identity tamper fails semantically before accept");
    auto incomplete=origin; check(!incomplete.finish(),"empty stream cannot finish");
    check(!ledger.accept(observed.back(),ledger.previous),"extra terminal observation rejected");
    auto skipped=observed[1]; skipped.state.put("ordinal9",8,skipped.state.get("ordinal9")+1);
    auto ordinal=origin; require(ordinal.accept(observed[0],ordinal.previous),"first entry");
    check(!ordinal.accept(skipped,ordinal.previous),"unexplained ordinal increment");
    for (const auto changed_ordinal:{entry.get("ordinal9"),entry.get("ordinal9")-1,entry.get("ordinal9")+2,entry.get("ordinal9")+8}) {
        auto changed=observed[1];
        for (const auto* key:{"ordinal9","snapshot_ordinal","capture.end_ordinal"}) changed.state.put(key,8,changed_ordinal);
        auto guard=origin; require(guard.accept(observed[0],guard.previous),"first entry");
        check(!guard.accept(changed,guard.previous),"duplicate/rewound/skipped/unexplained coherent ordinal");
    }
    auto hazard=observed[0].state; hazard.put("slice_cap",8,hazard.get("cycle9")+1);
    rejects([&] { task_aw2::prospective(hazard,0); },"prospective retained-cap hazard");
    hazard=observed[0].state; hazard.put("deferred9",4,1);
    rejects([&] { task_aw2::prospective(hazard,0); },"prospective debt hazard");
    hazard=observed[0].state; hazard.put("timing.generation",4,0);
    rejects([&] { task_aw2::prospective(hazard,0); },"prospective unknown timing");
    hazard=observed[0].state; hazard.put("scheduler.next_event",8,hazard.get("system_timestamp"));
    auto forbidden=observed[0]; forbidden.state=hazard; auto guarded=origin;
    check(!guarded.accept(forbidden,guarded.previous),"earlier scheduler event fails full protection");
    for (const auto forbidden_kind:{Kind::irq,Kind::scheduler,Kind::device,Kind::arm7}) {
        auto forbidden_event=observed[0]; forbidden_event.kind=forbidden_kind; auto denied=origin;
        check(!denied.accept(forbidden_event,denied.previous),"zero tolerated service");
    }
    const auto final=observed.back().state;
    std::ofstream fields(root+"/fields.json");
    fields<<"{\"entry_scalars\":"<<entry.fields.size()<<",\"final_scalars\":"<<final.fields.size()<<",\"hashes\":"<<entry.hashes.size()<<",\"invariant_scalars\":"<<invariant(entry).fields.size()<<"}\n";
    task_aw3::armed=false; std::fclose(task_aw3::output);
    std::cout<<"AW4 assertions: "<<assertions<<"\n";
}
}
int main(int argc,char** argv) {
    try {
        require(argc==3,"mode/evidence directory required"); mode=argv[1]; root=argv[2];
        auto* output=task_aw3::exclusive_audit((root+"/audit.jsonl").c_str()); require(output,"fresh writable audit required");
        require(!task_aw3::exclusive_audit((root+"/audit.jsonl").c_str()),"existing audit cannot be overwritten");
        setup(output); const auto initial=task_aw3::passive();
        if (mode=="unit" || mode=="unit-banks") { unit(initial); return 0; }
        static Shutdown shutdown; std::atexit(persistence);
        if (mode=="disabled") {
            task_aw3::armed=false;
            const auto serial=task_aw3::serial;
            nds_reschedule_slice((g_runtime_cycles>>1)+34);
            require(task_aw3::serial==serial && !task_aw::observer,"disabled journal/observer remains inactive");
            marker("disabled-normal-return"); std::fclose(output); std::_Exit(0);
        }
        Controller controller;
        const auto authority=synthetic_authority();
        bool guards=false;
        if (mode=="guard") {
            task_aw3::guarded_handoff([] { throw std::runtime_error("preserved AU guard failure"); });
        }
        auto guarded=[&] {
            require(initial.get("r15")==0x02001980 && initial.get("ordinal9")==281098008 &&
                    initial.get("cycle9")==task_aw2::entry_cycle,"synthetic preserved entry guards");
            guards=true;
        };
        guarded(); require(guards,"guards dominate observer ownership");
        if (mode=="preflight-rom") task_aw3::rom_identity[0]^=1;
        if (mode=="preflight-code") fixture::bus_mutate("code");
        if (mode=="preflight-cpu") fixture::mutate("cpu");
        if (mode=="preflight-ram") fixture::bus_mutate("image");
        if (mode=="preflight-dtcm") fixture::bus_mutate("dtcm");
        if (mode=="preflight-save") fixture::io_mutate("save");
        if (mode=="preflight-debt") fixture::mutate("debt");
        if (mode=="preflight-cap") fixture::mutate("cap");
        controller.test_only_start(output,binding_source,authority);
        stream(); controller.end();
        tail(); return 90;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
