#include <fstream>
#include <iostream>
#include "controller.h"
#include "fixture.h"
#include "observed_timing.h"
#include "scheduler.h"

namespace task_aw { void runtime_snapshot(Snapshot&); }
extern "C" {
uint32_t g_insn_hook_armed=0;
void runtime_insn_slow() {
    std::fputs("FORBIDDEN guest instruction payload in AW2 runtime test\n",stderr);
    std::abort();
}
}
namespace {
task_aw2::Snapshot supplied;
std::string directory;
void sentinel(const char* name) { std::ofstream(directory+"/"+name)<<"REACHED\n"; }
struct Destructor { ~Destructor() { sentinel("destructor"); } };
void at_exit() { sentinel("atexit"); }
task_aw2::Snapshot copied_source() {
    auto result=supplied;
    task_aw::Snapshot observed;
    task_aw::runtime_snapshot(observed);
    for (const auto* name:{"cycle9","slice_cap","fast_limit"})
        result.put(name,8,observed.values.at(name));
    for (unsigned index=0;index<16;++index)
        result.put("r"+std::to_string(index),4,g_cpu.R[index]);
    return result;
}
void seed_cpu(const task_aw2::Snapshot& state) {
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=uint32_t(state.get("r"+std::to_string(index)));
    g_cpu.cpsr=uint32_t(state.get("cpsr"));
    g_runtime_cycles=state.get("cycle9");
    nds_set_cycle_cap(state.get("slice_cap"));
    g_nds_fast_limit=state.get("fast_limit");
}
}
int main(int argc, char** argv) {
    using namespace task_aw2;
    try {
        bus_init();
        scheduler_init();
        supplied=synthetic::entry();
        NdsCp15SaveState cp15{};
        cp15.visible.control=uint32_t(supplied.get("cp15.control"));
        cp15.visible.dtcm_enable=true;
        cp15.visible.dtcm_base=0x027e0000;
        cp15.visible.dtcm_size=0x4000;
        cp15.timing_generation=9;
        cp15.cache_cfg[0]=cp15.cache_cfg[1]=1;
        cp15.mpu_region[0]=0x0200002b;
        cp15.mpu_region[1]=0x0400002f;
        std::string import_error;
        require(cp15_savestate_import(cp15,&import_error),"synthetic CP15 import: "+import_error);
        g_nds_active=NDS_ARM9;
        seed_cpu(supplied);
        arm9_refill_cycles(pcs.front());
        const auto before=observed_timing();
        require(before==observed_timing(),"passive actual timing copies invariant");
        auto captured=supplied;
        for (const auto& item:before.fields) captured.fields[item.first]=item.second;
        unsigned checks=0;
        for (unsigned index=0;index<pcs.size();++index) {
            const auto num_code=runtime_code_cycles(pcs[index]);
            require(num_code==code_cost(captured,pcs[index]),"actual cached prefetch cost");
            ++checks;
            uint32_t actual=0;
            if (index==8 || index==9) actual=arm9_refill_cycles(index==8 ? 0x02001a20 : 0x020019b0);
            else {
                const auto num_data=(index==4 || index==10) ? runtime_mem_cycles(0x020019ac,4,0) :
                    (index==0 || index==2 || index==5 || index==6 || index==7 || index==11) ?
                    runtime_mem_cycles(0x04000280,index==0 || index==11 ? 2 : 4,0) : 0;
                actual=arm9_cycle_combine(num_code,num_data,0,num_data!=0);
            }
            require(actual==cost(captured,index),"prospective cost matches real runtime functions");
            ++checks;
        }
        require(before==observed_timing(),"timing snapshot excludes mutable access counters/addresses");
        ++checks;
        task_aw::Snapshot passive;
        task_aw::runtime_snapshot(passive);
        auto projected=task_aw2::Snapshot{};
        for (const auto& item:before.fields) projected.fields[item.first]=item.second;
        for (const auto* name:{"cycle9","slice_cap","fast_limit"}) projected.put(name,8,passive.values.at(name));
        require(decode(canonical(projected))==projected,"actual copied scalars canonical round trip");
        ++checks;
        nds_set_cycle_cap(1000);
        nds_reschedule_slice(600);
        task_aw::runtime_snapshot(passive);
        require(passive.values.at("slice_cap")==1000,"disabled reschedule keeps earlier cap");
        nds_reschedule_slice(400);
        task_aw::runtime_snapshot(passive);
        require(passive.values.at("slice_cap")==800 && passive.values.at("fast_limit")==0,
                "disabled real runtime shortens cap and completes original body");
        checks+=2;
        if (argc==3) {
            directory=argv[2];
            static Destructor destroy;
            std::atexit(at_exit);
            supplied=synthetic::entry();
            seed_cpu(supplied);
            auto* output=std::fopen((directory+"/audit.jsonl").c_str(),"wb");
            require(output!=nullptr,"actual-runtime child audit");
            Controller controller;
            controller.start(output,copied_source);
            const auto plan=transcript(supplied);
            for (size_t index=0;index<4;++index) {
                supplied=plan[index].state;
                seed_cpu(supplied);
                const auto& event=plan[index];
                task_aw::emit(event.kind,event.pc,event.address,event.width,event.value,event.write);
            }
            supplied=plan[4].state;
            nds_reschedule_slice((entry_cycle>>1)+33);
            sentinel("runtime-return");
            sentinel("scheduler-tail");
            sentinel("device-service");
            sentinel("irq-acceptance");
            sentinel("arm7-catchup");
            sentinel("shutdown-save");
            return 90;
        }
        std::cout<<"Actual runtime ROM-free timing/passive/disabled checks: "<<checks<<"\n";
        std::cout<<"observed_timing_sha256="<<digest(before)<<"\n";
        return 0;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
