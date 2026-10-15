#include <filesystem>
#include <fstream>
#include <iostream>
#include "controller.h"
#include "source_rail.h"

namespace {
using namespace task_aw6;
unsigned assertions=0;
std::string root;
std::vector<Observation> observed;
Controller* active=nullptr;
std::string mode;
void check(bool condition,const std::string& why) { ++assertions; require(condition,why); }
template<class Action> void rejects(Action action,const std::string& why) {
    bool rejected=false; try { action(); } catch (const std::exception&) { rejected=true; }
    check(rejected,why);
}
void marker(const std::string& name) { std::ofstream(root+"/"+name)<<"REACHED"; }
void persistence() { marker("persistence"); }
struct Shutdown { ~Shutdown() { marker("shutdown"); } };
void tail() { for (const auto* name:{"scheduler","device","IRQ","ARM7","guest","old-halt"}) marker(name); }
void event(Kind kind,uint32_t pc,uint32_t address=0,uint32_t width=0,uint32_t value=0,bool write=false) {
    if (active) active->observe(kind,pc,address,width,value,write);
    else observed.push_back({kind,pc,address,width,value,write,aw6_source::sample()});
}
void stream() {
    using namespace aw6_source;
    const uint32_t addresses[11]={0x04000280,0,0x04000290,0,0x020019ac,0x04000294,0x04000298,0x0400029c,0,0,0x020019e4};
    for (unsigned index=0;index<11;++index) {
        const auto pc=g_cpu.R[15];
        if (index==1 && mode=="mutation") working.put("deferred7",4,0);
        event(Kind::instruction,pc);
        const auto ordinal=task_aw2::add(working.get("ordinal9"),1);
        for (const auto* name:{"ordinal9","snapshot_ordinal","capture.end_ordinal"}) working.put(name,8,ordinal);
        working.put("hidden.code_pc9",4,pc);
        event(Kind::access_before,pc,pc,4);
        event(Kind::access_after,pc,pc,4,uint32_t(working.get(task_aw2::address_key("code.",pc))));
        const auto code_cost=task_aw2::code_cost(working,pc);
        uint32_t data_cost=0;
        const auto address=addresses[index];
        if (address) {
            const bool write=address>=0x04000000;
            const uint32_t width=index==0 ? 2 : 4;
            const uint32_t value=write ? index==0 ? 1 : index==5 || index==6 ? 4096 : 0 : index==4 ? 0x04000298 : 0x04000280;
            data_cost=task_aw2::data_cost(working,address);
            working.put("hidden.data_addr9",4,address);
            event(Kind::access_before,pc,address,width,write ? value : 0,write);
            if (write) math_reg_write(address,value,width);
            if (mode=="wrong-mmio" && index==2) event(Kind::access_after,pc,address,width,99,write);
            else event(Kind::access_after,pc,address,width,value,write);
        }
        if (index==1) g_cpu.R[12]=0;
        if (index==3) g_cpu.R[3]=4096;
        if (index==4) g_cpu.R[1]=0x04000298;
        if (index==9) g_cpu.R[14]=0x02001a24;
        if (index==10) g_cpu.R[1]=0x04000280;
        const auto cost=index==8 ? arm9_refill_cycles(0x02001a20) : index==9 ? arm9_refill_cycles(0x020019b0) :
            arm9_cycle_combine(code_cost,data_cost,0,data_cost ? 1 : 0);
        g_cpu.R[15]=index==8 ? 0x02001a20 : index==9 ? 0x020019b0 : pc+4;
        g_runtime_cycles+=cost+runtime_deferred_cycles_take();
        event(Kind::cycle_commit,pc,0,0,mode=="cost" && index==2 ? cost+1 : cost);
        if (index==8) {
            const auto depth=unsigned(working.get("return_depth"));
            require(working.get(task_aw2::numbered("return.",depth-1))==g_cpu.R[15],"source-side return match");
            working.fields.erase(task_aw2::numbered("return.",depth-1)); working.put("return_depth",4,depth-1);
        }
        if (index==9) {
            const auto depth=unsigned(working.get("return_depth"));
            working.put(task_aw2::numbered("return.",depth),4,pc+4); working.put("return_depth",4,depth+1);
        }
        if (!(mode=="missing" && index==10)) event(Kind::retired,pc);
        if (active && index==10 && mode!="missing") tail();
        require(g_runtime_cycles<g_nds_fast_limit,"source rail would poll before guard");
    }
}
void unit(const Snapshot& initial) {
    entry(initial);
    check(aw6_source::sample()==initial,"all 361 captured scalar cells and five identities reproduced exactly");
    check(task_aw2::decode(task_aw2::canonical(initial))==initial,"canonical roundtrip");
    aw6_source::g_nds_fast_limit=0;
    aw6_source::publish_fast_limit();
    check(aw6_source::g_nds_fast_limit==initial.get("slice_cap") && aw6_source::g_yield_poll_hint==1 &&
        aw6_source::g_nds_fast_limit_publishes==527,"actual publisher accepts hint=1 without clearing it");
    aw6_source::begin(initial);
    check(rtc_due(initial.get("system_timestamp"))==1670410,"actual RTC due vs preserved floor projection");
    check(aw6_source::source_rtc_due(initial.get("system_timestamp"))==rtc_due(initial.get("system_timestamp")),"source RTC formula agrees");
    for (uint64_t delta=0;delta<2048;++delta) {
        const auto system=initial.get("system_timestamp")+delta;
        check(rtc_due(system)==aw6_source::source_rtc_due(system),"RTC source formula phase interval");
    }
    check(timer_deadline(initial,0)==1711700418 && timer_deadline(initial,4)==1709382485 && timer_deadline(initial,5)==1708523673,"clocked timer overflow bounds");
    check(timer_deadline(initial,7)==UINT64_MAX,"IRQ-enable without timer enable is latent");
    check(aw6_source::nds_next_timer_overflow_time()==1708523673,"actual timer getter on exact copied timer scalars");
    check(!aw6_source::nds_halt_wake_pending(1),"actual parked ARM7 has no wake source");
    aw6_source::g_ime[1]=0; aw6_source::g_if[1]=aw6_source::g_ie[1];
    check(aw6_source::nds_halt_wake_pending(1),"ARM7 wake ignores IME; must guard raw IE and IF");
    aw6_source::begin(initial);
    for (const auto& field:initial.fields) {
        auto changed=initial; changed.fields.at(field.first).value^=1;
        rejects([&] { entry(changed); },"every changed entry scalar rejects: "+field.first);
        changed=initial; changed.fields.erase(field.first);
        rejects([&] { entry(changed); },"every omitted entry scalar rejects");
    }
    for (const auto& identity:initial.hashes) {
        auto changed=initial; changed.hashes.at(identity.first)[0]='0';
        rejects([&] { entry(changed); },"entry identity mutation");
    }
    for (const auto* name:{"hidden.yield","deferred7","service.rtc_processed","service.rtc_due","slice_cap","timer.0.control","timer.4.accum","timer.5.counter"}) {
        auto changed=initial; changed.fields.at(name).value^=1;
        rejects([&] { entry(changed); },"captured contradiction cannot be normalized");
    }
    auto changed=initial; changed.put("hidden.yield",4,2);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"unknown hint");
    changed=initial; changed.put("active_cpu",1,1);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"parked debt cannot belong to active core");
    changed=initial; changed.put("timer.0.counter",2,65535);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"timer ready negative");
    changed=initial; changed.put("timer.0.control",2,0xc5);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"unmodeled cascade");
    changed=initial; changed.put("service.rtc_processed",8,1670409);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"real RTC tick pending");
    changed=initial; changed.put("irq7.if",4,1); changed.put("irq7.ime",4,0);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"ARM7 wake eligibility even with IME off");
    changed=initial; changed.put("irq9.if",4,changed.get("irq9.ie"));
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"active IRQ eligible");
    changed=initial; changed.put("deferred9",4,2);
    rejects([&] { guard_next(changed,0); },"active debt cannot be treated as parked ARM7 debt");
    changed=initial; changed.put("timer.0.accum",8,64);
    rejects([&] { ready_before(changed,initial.get("cycle9")+8); },"unclassified timer phase");
    changed=initial; changed.put("div.deadline",8,initial.get("cycle9")>>1); changed.put("div.control",2,0x8001);
    rejects([&] { guard_next(changed,0); },"old divider ready before first write");
    changed=initial; changed.put("scheduler.next_event",8,initial.get("cycle9")>>1);
    rejects([&] { guard_next(changed,0); },"scheduled service already ready");
    rejects([&] { rtc_due(UINT64_MAX); },"RTC wrap rejected");
    changed=initial; changed.put("slice_cap",8,initial.get("cycle9")+8); changed.put("fast_limit",8,changed.get("slice_cap"));
    rejects([&] { guard_next(changed,0); },"first MMIO may not start with cost reaching cap");
    changed=initial; changed.put("slice_cap",8,initial.get("cycle9")+7); changed.put("fast_limit",8,changed.get("slice_cap"));
    rejects([&] { guard_next(changed,0); },"post-write deadline cannot rescue an unsafe entry cap");
    stream();
    check(observed.size()==69,"69 independent source-rail observations");
    Ledger ledger(initial);
    for (const auto& item:observed) check(ledger.accept(item,ledger.previous),ledger.failure);
    check(ledger.complete(),"reduced transcript complete");
    const auto& final=observed.back().state;
    check(final.get("r15")==stop_pc && final.get("cycle9")==3416875777,"stop before status load with one-cycle cap margin");
    check(final.get("hidden.yield")==1 && final.get("deferred7")==2 && final.get("service.rtc_processed")==1670410,"latent observations preserved");
    check(final.get("slice_cap")==3416875778 && final.get("fast_limit")==3416875778 && final.get("hidden.fast_publishes")==526,"no shortening or publisher");
    check(final.get("cap.count")==6 && final.get("capture.serial")==506 && final.get("div.deadline")==1708437913,"five genuine source journal appends");
    check(final.hashes==initial.hashes,"all image/save identities unchanged in model");
    check(task_aw2::code_cost(final,stop_pc)==1 && task_aw2::data_cost(final,0x04000280)==8 &&
        aw6_source::arm9_cycle_combine(1,8,0,1)==8,"forbidden next status cost remains eight");
    rejects([&] { guard_next(final,11); },"forbidden status-read dispatch");
    rejects([&] { ready_before(final,task_aw2::add(final.get("cycle9"),task_aw2::cost(final,11))); },"12th cost crosses captured cap");
    for (unsigned increment=1;increment<=2;++increment)
        rejects([&] { ready_before(final,task_aw2::add(final.get("cycle9"),increment)); },"cost reaches/crosses one-cycle final margin");
    for (size_t index=0;index<observed.size();++index) {
        Ledger prefix(initial);
        for (size_t prior=0;prior<index;++prior) require(prefix.accept(observed[prior],prefix.previous),"unit prefix");
        for (const auto& field:observed[index].state.fields) {
            auto candidate=observed[index]; candidate.state.fields.at(field.first).value^=1;
            auto guard=prefix;
            check(!guard.accept(candidate,guard.previous),"every full observation field checked");
            check(!guard.accept(observed[index],guard.previous),"failure sticky");
        }
        auto wrong=observed[index]; wrong.value^=1; auto guard=prefix;
        check(!guard.accept(wrong,guard.previous),"wrong metadata/value");
        guard=prefix;
        check(!guard.accept(observed[index],std::string(64,'0')),"chain tamper");
        if (index+1<observed.size()) { guard=prefix; check(!guard.accept(observed[index+1],guard.previous),"missing event"); }
        if (index) { guard=prefix; check(!guard.accept(observed[index-1],guard.previous),"duplicate/reordered event"); }
    }
    check(!ledger.accept(observed.back(),ledger.previous),"extra terminal event");
    for (const auto kind:{Kind::scheduler,Kind::device,Kind::irq,Kind::arm7,Kind::cap_change}) {
        Ledger guard(initial);
        auto forbidden=observed[0]; forbidden.kind=kind;
        check(!guard.accept(forbidden,guard.previous),"unexpected service/cap observation fails closed");
    }
    std::cout<<"AW6 assertions: "<<assertions<<"\n";
}
}
int main(int argc,char** argv) {
    try {
        require(argc==4,"mode, captured canonical hex, fresh output required");
        mode=argv[1]; root=argv[3];
        std::ifstream input(argv[2]); std::string hex; input>>hex;
        require(!hex.empty() && hex.size()%2==0,"canonical input");
        std::vector<uint8_t> bytes;
        for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
        const auto initial=task_aw2::decode(bytes);
        if (mode=="disabled") { marker("disabled-normal-return"); return 0; }
        aw6_source::begin(initial);
        if (mode=="unit") { unit(initial); task_aw3::armed=false; return 0; }
        static Shutdown shutdown; std::atexit(persistence);
        auto* output=task_aw3::exclusive_audit((root+"/audit.jsonl").c_str());
        require(output,"fresh audit");
        Controller controller;
        if (mode=="entry") aw6_source::working.put("service.rtc_processed",8,0);
        controller.start(output,aw6_source::sample);
        active=&controller;
        stream();
        controller.end();
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
