#include <iostream>
#include "au.h"
#include "io.h"
namespace {
using task_aw8::require;
std::string directory,mode;
void marker(const char* name) { std::ofstream(directory+"/"+name)<<"REACHED"; }
void persistence() { marker("persistence"); }
struct Shutdown { ~Shutdown() { marker("shutdown"); } };
void tail() { for (const auto* name:{"scheduler","device","IRQ","ARM7","guest","halt"}) marker(name); }
void torn_sample() { task_aw8::runtime_mutate("cpu"); }
void fault() {
    using namespace task_aw8;
    if (mode=="ordinal" || mode=="cycle" || mode=="cap" || mode=="hint" || mode=="debt" || mode=="cpu" || mode=="bank") runtime_mutate(mode);
    if (mode=="arm7" || mode=="event") scheduler_mutate(mode);
    if (mode=="irq" || mode=="rtc" || mode=="timer" || mode=="device" || mode=="divider" || mode=="save") io_mutate(mode);
    if (mode=="mainram" || mode=="dtcm" || mode=="code" || mode=="latch") bus_mutate(mode);
    if (mode=="journal") ++task_aw3::history.back().serial;
    if (mode=="journal-source") task_aw3::history.back().source=0;
    if (mode=="rom") task_aw3::rom_identity.at(0)^=1;
    if (mode=="framework") {
        auto changed=*evidence; changed.hashes.at("framework_commit").at(0)^=1;
        evidence=std::make_shared<const task_aw2::Snapshot>(changed);
    }
}
void stream() {
    using namespace task_aw8;
    const uint32_t addresses[11]={0x04000280,0,0x04000290,0,0x020019ac,0x04000294,0x04000298,0x0400029c,0,0,0x020019e4};
    for (unsigned index=0;index<11;++index) {
        const auto pc=g_cpu.R[15];
        if (index==1) fault();
        if (index) task_aw::emit(task_aw::Kind::instruction,pc);
        if (index==1 && mode=="extra") task_aw::emit(task_aw::Kind::instruction,pc);
        auto cpu=brainage_task_au::cpu_copy(); brainage_task_au::au_control(cpu);
        fetch();
        const auto code_cost=fetch_cost(pc);
        if (!index && mode=="forbidden-fetch") task_aw7::access<true>(task_aw6::stop_pc,task_aw6::stop_pc,4,0,false,[] { marker("forbidden"); return 0; });
        if (!index && mode=="real-bus") task_aw7::runtime_access(pc,pc,4,0,false,[] { marker("real-bus"); return 0; });
        task_aw7::access<true>(pc,pc,4,0,false,[&] { return scalar(pc,4); });
        uint32_t memory_cost=0;
        if (const auto address=addresses[index]) {
            const bool write=address>=0x04000000;
            const unsigned width=index==0 ? 2 : 4;
            const uint32_t value=write ? index==0 ? 1 : index==5 || index==6 ? 4096 : 0 : scalar(address,4);
            memory_cost=data_cost(address,width,write);
            auto action=[&] {
                if (!index && mode=="raw-IO-write") nds_io_write(address,value,width);
                if (!index && mode=="raw-IO-read") return nds_io_read(0x04000280,2);
                if (write) model_write(index);
                return value;
            };
            if (!index && mode=="real-MMIO") task_aw7::runtime_access(pc,address,width,value,true,[] { marker("real-MMIO"); return 0; });
            task_aw7::access<true>(pc,mode=="address" && !index ? address+2 : address,
                mode=="width" && !index ? 4 : width,mode=="value" && !index ? value+1 : value,write,action);
        }
        const auto cost=index==8 ? refill_cost(0x02001a20) : index==9 ? refill_cost(0x020019b0) :
            arm9_cycle_combine(code_cost,memory_cost,0,memory_cost ? 1 : 0);
        commit(index,cost);
        if (mode=="cost-"+std::to_string(index)) runtime_mutate("cycle");
        if (mode=="reorder" && index==1) task_aw::emit(task_aw::Kind::retired,pc);
        task_aw::emit(task_aw::Kind::cycle_commit,pc,0,0,cost);
        retire(index);
        if (mode=="missing" && index==10) task_aw::emit(task_aw::Kind::instruction,g_cpu.R[15]);
        task_aw::emit(task_aw::Kind::retired,pc);
        if (index==10) tail();
    }
}
}
int main(int argc,char** argv) {
    try {
        require(argc==4,"mode, authenticated canonical hex, fresh audit directory");
        mode=argv[1]; directory=argv[3];
        static Shutdown shutdown; std::atexit(persistence);
        task_aw3::output=task_aw3::exclusive_audit((directory+"/audit.jsonl").c_str());
        require(task_aw3::output,"exclusive output");
        task_aw8::load(argv[2]);
        task_aw3::audit_text("provenance","AW5 captured canonical evidence; actual getter bodies; three test-only immutable identity adapters; no expected snapshot injection");
        task_aw8::cp15_begin(); task_aw8::bus_begin(); task_aw8::io_begin();
        task_aw8::scheduler_begin(); task_aw8::spu_begin();
        const std::string tag="AW8 ROM-free historical loader metadata:"+task_aw2::digest(task_aw8::entry());
        const auto computed=gba::sha1(reinterpret_cast<const uint8_t*>(tag.data()),tag.size()).hex();
        task_aw8::bind("rom",computed); task_aw8::seal();
        task_aw8::audit_binding();
        task_aw3::arm(task_aw3::output);
        task_aw3::rom_identity=task_aw8::identity("rom",computed);
        task_aw3::rom_epoch=task_aw8::entry().get("capture.rom_epoch");
        task_aw3::logical_saves=task_aw8::entry().get("logical_saves");
        task_aw3::flash_commits=task_aw8::entry().get("flash_commits");
        task_aw8::runtime_begin();
        const auto initial=task_aw3::passive();
        task_aw2::audit_snapshot(task_aw3::output,initial);
        if (!(initial==task_aw8::entry())) {
            for (const auto& item:initial.fields) {
                const auto found=task_aw8::entry().fields.find(item.first);
                if (found==task_aw8::entry().fields.end() || !(item.second==found->second)) std::cerr<<item.first<<" actual="<<item.second.value<<" expected="<<(found==task_aw8::entry().fields.end() ? 0 : found->second.value)<<"\n";
            }
            task_aw3::fail("actual entry differs from authenticated AW5 evidence");
        }
        require(task_aw3::passive()==initial,"repeat actual provider stability");
        if (mode=="inspect") { std::fclose(task_aw3::output); return 0; }
        brainage_task_au::au_ram=task_aw8::ram_copy(); brainage_task_au::au_expected_dtcm=task_aw8::dtcm_copy();
        brainage_task_au::decision_flash=task_aw8::save_copy();
        task_aw7::arm_diagnostic();
        auto cpu=brainage_task_au::cpu_copy();
        if (mode=="AU-guard") cpu.R[0]^=1;
        if (mode=="entry-cap") task_aw8::runtime_mutate("cap");
        if (mode=="torn-sample") {
            task_aw8::mutate_at_read=task_aw8::identity_reads+1;
            task_aw8::sample_mutation=torn_sample;
        }
        if (mode=="rebind") task_aw8::bind("mainram","invalid");
        if (mode=="unsealed") task_aw8::sealed=false;
        brainage_task_au::au_control(cpu);
        if (mode=="forbidden-account") { task_aw8::fetch(); task_aw7::check_dispatch(); }
        if (mode=="forbidden-dispatch") { task_aw8::runtime_mutate("forbidden"); task_aw7::check_dispatch(); }
        if (mode=="old-halt") brainage_task_au::finish(0);
        if (mode=="service") task_aw::emit(task_aw::Kind::device,0x02001980);
        stream(); tail(); return 90;
    } catch (const std::exception& error) { task_aw3::fail(error.what()); }
    catch (...) { task_aw3::fail("unknown fixture failure"); }
}
