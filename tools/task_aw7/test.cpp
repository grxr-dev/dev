#include <fstream>
#include <iostream>
#include "aw7/integration.h"
#include "model_rail.h"
#include "au_guard_model.h"

namespace task_aw3 {
void scheduler_snapshot(Snapshot& out) { out=aw6_source::sample(); }
void runtime_snapshot(Snapshot&) {}
void bus_snapshot(Snapshot&) {}
void io_snapshot(Snapshot&) {}
void cp15_snapshot(Snapshot&) {}
}
namespace {
using task_aw2::require;
std::string root,mode;
void marker(const std::string& name) { std::ofstream(root+"/"+name)<<"REACHED"; }
void persistence() { marker("persistence"); }
struct Shutdown { ~Shutdown() { marker("shutdown"); } };
void tail() { for (const auto* name:{"scheduler","device","IRQ","ARM7","guest","old-halt"}) marker(name); }
void step_fault(unsigned index) {
    using namespace aw6_source;
    if (index!=1) return;
    if (mode=="hint") working.put("hidden.yield",4,0),g_yield_poll_hint=0;
    if (mode=="bank") working.put("hidden.bank.02001984",1,1);
    if (mode=="debt") working.put("deferred7",4,0);
    if (mode=="rtc") working.put("service.rtc_processed",8,0);
    if (mode=="timer") working.put("timer.0.counter",2,65535);
    if (mode=="device") working.put("spi.deadline",8,0);
    if (mode=="scheduler") working.put("scheduler.next_event",8,0);
    if (mode=="IRQ") working.put("irq9.ime",4,1),working.put("irq9.ie",4,1),working.put("irq9.if",4,1);
    if (mode=="ARM7-wake") working.put("irq7.ie",4,1),working.put("irq7.if",4,1);
    if (mode=="hidden-latch") working.put("hidden.data_addr9",4,0);
    if (mode=="divider") ++g_div_numer[0];
    if (mode=="cap") --g_cycle_cap;
    if (mode=="ordinal") working.put("ordinal9",8,working.get("ordinal9")+1);
}
void stream() {
    using namespace aw6_source;
    const uint32_t addresses[11]={0x04000280,0,0x04000290,0,0x020019ac,0x04000294,0x04000298,0x0400029c,0,0,0x020019e4};
    for (unsigned index=0;index<11;++index) {
        step_fault(index);
        const auto pc=g_cpu.R[15];
        if (index) task_aw::emit(task_aw::Kind::instruction,pc);
        if (index==1 && mode=="extra") task_aw::emit(task_aw::Kind::instruction,pc);
        auto cpu=brainage_task_au::terminal_cpu();
        for (unsigned reg=0;reg<16;++reg) cpu.R[reg]=g_cpu.R[reg];
        brainage_task_au::au_control(cpu);
        const auto ordinal=working.get("ordinal9")+1;
        for (const auto* name:{"ordinal9","snapshot_ordinal","capture.end_ordinal"}) working.put(name,8,ordinal);
        working.put("hidden.code_pc9",4,pc);
        if (mode=="forbidden-fetch" && !index)
            task_aw7::access<true>(0x020019b4,0x020019b4,4,0,false,[] { marker("forbidden-fetch"); return 0; });
        task_aw7::access<true>(pc,pc,4,0,false,[&] { return working.get(task_aw2::address_key("code.",pc)); });
        const auto code_cost=task_aw2::code_cost(working,pc);
        uint32_t data_cost=0;
        const auto address=addresses[index];
        if (address) {
            const bool write=address>=0x04000000;
            const unsigned width=index==0 ? 2 : 4;
            const uint32_t value=write ? index==0 ? 1 : index==5 || index==6 ? 4096 : 0 : index==4 ? 0x04000298 : 0x04000280;
            data_cost=task_aw2::data_cost(working,address);
            working.put("hidden.data_addr9",4,address);
            auto action=[&] {
                if (write) math_reg_write(address,value,width);
                if (!index && mode=="write-model") ++g_div_deadline;
                if (!index && mode=="journal") ++task_aw3::history.back().serial;
                if (!index && mode=="journal-source") task_aw3::history.back().source=0;
                return value;
            };
            if (!index && mode=="runtime-MMIO")
                task_aw7::runtime_access(pc,address,width,value,write,[] { marker("actual-MMIO"); return 0; });
            const auto target=mode=="address" && !index ? address+2 : address;
            const auto ordered_target=mode=="order" && !index ? uint32_t(0x04000290) : target;
            const auto size=mode=="width" && !index ? 4 : width;
            const auto payload=mode=="value" && !index ? value+1 : value;
            task_aw7::access<true>(pc,ordered_target,size,payload,write,action);
            if (mode=="duplicate-access" && !index) task_aw7::access<true>(pc,address,width,value,write,action);
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
        if (mode=="cost-"+std::to_string(index)) ++g_runtime_cycles;
        if (mode=="final-cycle" && index==10) ++g_runtime_cycles;
        task_aw::emit(task_aw::Kind::cycle_commit,pc,0,0,mode=="cost" && index==2 ? cost+1 : cost);
        if (index==8) { const auto depth=working.get("return_depth"); working.fields.erase(task_aw2::numbered("return.",unsigned(depth-1))); working.put("return_depth",4,depth-1); }
        if (index==9) { const auto depth=working.get("return_depth"); working.put(task_aw2::numbered("return.",unsigned(depth)),4,pc+4); working.put("return_depth",4,depth+1); }
        if (mode=="missing" && index==10) task_aw::emit(task_aw::Kind::instruction,g_cpu.R[15]);
        if (mode=="reorder" && index==1) task_aw::emit(task_aw::Kind::instruction,pc);
        task_aw::emit(task_aw::Kind::retired,pc);
        if (index==10) tail();
    }
}
}
int main(int argc,char** argv) {
    try {
        require(argc==4,"mode, retained canonical hex, output required");
        mode=argv[1]; root=argv[3];
        std::ifstream input(argv[2]); std::string hex; input>>hex; std::vector<uint8_t> bytes;
        for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
        const auto initial=task_aw2::decode(bytes);
        aw6_source::begin(initial);
        if (mode=="unit") {
            unsigned assertions=0;
            for (const auto& item:initial.fields) {
                auto changed=initial; changed.fields.at(item.first).value^=1;
                bool denied=false; try { task_aw6::entry(changed); } catch (...) { denied=true; }
                require(denied,"every entry scalar mismatch"); ++assertions;
            }
            for (const auto& item:initial.hashes) {
                auto changed=initial; changed.hashes.at(item.first)[0]='0';
                bool denied=false; try { task_aw6::entry(changed); } catch (...) { denied=true; }
                require(denied,"every entry identity mismatch"); ++assertions;
            }
            std::cout<<"AW7 assertions: "<<assertions<<"\n"; return 0;
        }
        static Shutdown shutdown; std::atexit(persistence);
        task_aw3::output=task_aw3::exclusive_audit((root+"/audit.jsonl").c_str());
        require(task_aw3::output,"exclusive audit");
        task_aw3::audit_text("provider_kind","model component getters around real passive aggregator; not actual buffers/ROM loader");
        auto cpu=brainage_task_au::terminal_cpu();
        if (mode=="disabled") { task_aw3::armed=false; brainage_task_au::au_control(cpu); return 90; }
        if (mode=="default") {
            require(!task_aw7::waiting() && !task_aw7::owns() && !task_aw::observer,"default inactive");
            task_aw3::armed=false; std::fclose(task_aw3::output); marker("default-normal-return"); return 0;
        }
        task_aw7::arm_diagnostic();
        if (mode=="entry") ++aw6_source::g_cycle_cap;
        if (mode=="short-entry-cap") --aw6_source::g_cycle_cap;
        if (mode=="old-halt") brainage_task_au::finish(0);
        if (mode=="AU-guard") cpu.R[0]^=1;
        try { brainage_task_au::au_control(cpu); }
        catch (const std::exception& error) { task_aw7::fail(error.what()); }
        if (mode=="service") task_aw::emit(task_aw::Kind::device,0x02001980);
        if (mode=="forbidden-account") {
            aw6_source::working.put("ordinal9",8,initial.get("ordinal9")+12);
            task_aw7::check_dispatch();
        }
        if (mode=="forbidden-dispatch") {
            aw6_source::g_cpu.R[15]=0x020019b4;
            task_aw7::check_dispatch();
        }
        stream(); tail(); return 90;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
