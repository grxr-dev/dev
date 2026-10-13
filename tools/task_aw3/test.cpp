#include <filesystem>
#include <fstream>
#include <iostream>
#include "aw3/bridge.h"
#include "aw3/aw2/fixture.h"
#include "task_au_setup_guard.h"

namespace {
task_aw3::Snapshot provided;
std::string root;
unsigned checks=0;
void check(bool condition,const std::string& text) { ++checks; task_aw2::require(condition,text); }
template<class Action> void rejects(Action action,const std::string& text) {
    bool rejected=false;
    try { action(); } catch (const std::exception&) { rejected=true; }
    check(rejected,text);
}
void marker(const std::string& name) { std::ofstream(root+"/"+name)<<"REACHED"; }
struct Shutdown { ~Shutdown() { marker("destructor"); } };
void onexit() { marker("persistence-shutdown"); }
task_aw3::Snapshot fixture() {
    using namespace task_aw3;
    auto out=task_aw2::synthetic::entry();
    export_history(out);
    out.put("capture.end_cycle",8,out.get("cycle9"));
    out.put("capture.end_ordinal",8,out.get("ordinal9"));
    out.put("hidden.code_pc9",4,0x0200197c); out.put("hidden.data_addr9",4,0x020019a8);
    out.put("hidden.cache_page",4,0x02001000); out.put("hidden.cache_generation",4,9);
    out.put("hidden.cache_class",4,1); out.put("hidden.region_valid",1,1); out.put("hidden.region_class",4,1);
    out.put("hidden.class_ready",1,1); out.put("hidden.yield",4,0); out.put("hidden.cpu_poll",1,1);
    for (const auto address:task_aw2::pcs) out.put(task_aw2::address_key("hidden.code_bit.",address),1,1);
    for (const uint32_t address:{0x020019acu,0x020019e4u,0x04000280u,0x04000290u,0x04000294u,0x04000298u,0x0400029cu})
        out.put(task_aw2::address_key("hidden.data_bit.",address),1,address<0x04000000);
    out.put("service.powered_off",1,0); out.put("service.firmware_dirty",1,0);
    const auto due=task_aw2::multiply(out.get("system_timestamp"),32768)/33513982;
    out.put("service.rtc_processed",8,due); out.put("service.rtc_due",8,due);
    out.put("service.display_last",8,out.get("system_timestamp")); out.put("service.irq_cache9",4,0);
    out.put("service.irq_cache7",4,0);
    out.put("service.spu_mixes",8,out.get("system_timestamp")/1024); out.put("service.gpu_debt",4,0);
    out.put("scheduler.round_epoch",8,1); out.put("scheduler.planned_target",8,out.get("slot9.target"));
    out.put("scheduler.next_event",8,task_aw2::periodic_next(out.get("system_timestamp")));
    return out;
}
void prepare(const std::string& directory) {
    using namespace task_aw3;
    root=directory;
    auto* file=std::fopen((root+"/audit.jsonl").c_str(),"wb");
    arm(file);
    rom_identity=task_aw2::au_manifest().hashes.at("rom"); rom_epoch=1;
    cap_note(0,0,task_aw2::entry_cycle-9,0,task_aw2::entry_cycle+119);
    provided=fixture();
}
}
namespace task_aw3 {
void scheduler_snapshot(Snapshot& out) { out=provided; }
void runtime_snapshot(Snapshot&) {}
void bus_snapshot(Snapshot&) {}
void io_snapshot(Snapshot&) {}
void cp15_snapshot(Snapshot&) {}
}
namespace brainage_task_au {
bool au_armed=true,au_pending=false,done=false;
unsigned au_index=7,au_reads=9,au_writes=1,au_bus_index=0;
std::vector<uint8_t> au_ram,au_expected_dtcm,decision_flash;
struct Flags { bool n=false,z=false,c=false,v=false,t=false,i=false,f=false; unsigned mode=31; };
struct CPU { uint32_t R[16]; Flags cpsr; };
uint64_t g_insn_count[2]={281098008,96026779};
void require(bool value,const char* why) { task_aw2::require(value,why); }
uint32_t word(uint32_t) { return au_fixed::opcode[7]; }
namespace diagnostics { std::vector<uint8_t> mainram_snapshot() { return {}; } }
std::vector<uint8_t> read(uint32_t,unsigned) { return {}; }
std::vector<uint8_t> save_snapshot() { return {}; }
template<class Value> void registers(const char*,const Value&) {}
void file(const char*,const std::vector<uint8_t>&) { marker("legacy-file-output"); }
void sample(const char*) {}
void log(const std::string&) {}
void finish(int) { marker("old-halt"); std::_Exit(99); }
#include "task_au_setup.inc"
}
int main(int argc,char** argv) {
    using namespace task_aw3;
    try {
        require(argc==3,"test mode and evidence directory required");
        prepare(argv[2]);
        const std::string mode=argv[1];
        if (mode=="unit") {
            entry_preflight(provided);
            check(task_aw2::decode(task_aw2::canonical(passive()))==provided,"canonical passive round trip");
            const auto identity=task_aw2::digest(provided);
            for (const auto& field:provided.fields) {
                auto mutated=provided;
                mutated.fields.at(field.first).value^=1;
                check(task_aw2::digest(mutated)!=identity,"every scalar protected by canonical identity");
                seal(provided);
                rejects([&] { verify_seal(mutated); },"immutable field mutation");
                bound=false;
                mutated=provided; mutated.fields.erase(field.first);
                seal(provided);
                rejects([&] { verify_seal(mutated); },"immutable field omission");
                bound=false;
            }
            for (const auto& hash:provided.hashes) {
                auto mutated=provided; mutated.hashes.at(hash.first)[0]^=1;
                rejects([&] { entry_preflight(mutated); },"image/ROM/code/save identity mismatch");
            }
            for (const auto* name:{"capture.epoch","capture.serial","capture.rom_epoch","hidden.cache_generation",
                    "hidden.cache_page","hidden.region_valid","hidden.class_ready","hidden.code_pc9","hidden.data_addr9",
                    "service.rtc_processed","service.display_last","scheduler.planned_target","scheduler.round_epoch",
                    "scheduler.next_event","hidden.yield","service.irq_cache9","service.irq_cache7","service.spu_mixes","service.gpu_debt"}) {
                auto mutated=provided; mutated.fields.at(name).value^=1;
                rejects([&] { entry_preflight(mutated); },name);
            }
            auto changed=provided; changed.put("deferred7",4,1);
            rejects([&] { entry_preflight(changed); },"ARM7 debt");
            changed=provided; changed.put("wifi.deadline",8,task_aw2::entry_cycle>>1);
            rejects([&] { entry_preflight(changed); },"unexpected scheduler device event");
            changed=provided; changed.put("div.deadline",8,task_aw2::entry_cycle>>1);
            rejects([&] { entry_preflight(changed); },"divider already ready");
            changed=provided; changed.put("timer.0.control",2,128);
            rejects([&] { entry_preflight(changed); },"unknown enabled timer");
            changed=provided; changed.put("dma.0.active",1,1);
            rejects([&] { entry_preflight(changed); },"DMA ready");
            changed=provided; changed.put("irq9.cached",4,1);
            rejects([&] { entry_preflight(changed); },"IRQ cache mismatch");
            for (const auto address:task_aw2::pcs) {
                changed=provided; changed.put(task_aw2::address_key("hidden.code_bit.",address),1,0);
                rejects([&] { entry_preflight(changed); },"stale actual code bitmap");
            }
            const auto core=core_projection(provided);
            const auto plan=task_aw2::transcript(core);
            task_aw2::Ledger ledger(core);
            for (const auto& event:plan) check(ledger.accept(event),"AW2 ordered model still accepted");
            check(ledger.complete(),"AW2 model terminal");
            task_aw2::Ledger mismatch(core);
            for (unsigned index=0;index<4;++index) require(mismatch.accept(plan[index]),"ordered prefix");
            auto actual=plan[4];
            reschedule(0,task_aw2::entry_cycle,history.back().after,(task_aw2::entry_cycle>>1)+34);
            auto full=provided;
            export_history(full);
            full.put("slice_cap",8,history.back().after);
            actual.state=core_projection(full);
            check(!mismatch.accept(actual),"trusted real journal cannot be silently dropped to satisfy AW2 ledger");
            cap_note(0,0,task_aw2::entry_cycle-9,0,task_aw2::entry_cycle+119);
            provided=fixture();
            cap_note(2,0,task_aw2::entry_cycle,history.back().after,task_aw2::entry_cycle+100);
            rejects([&] { passive(); },"unknown cap setter makes epoch ineligible");
            cap_note(0,0,task_aw2::entry_cycle-9,0,task_aw2::entry_cycle+119);
            provided=fixture();
            const auto initial=history.back().after;
            reschedule(0,task_aw2::entry_cycle,initial,(task_aw2::entry_cycle>>1)+34);
            const auto shortened=history.back().after;
            reschedule(0,task_aw2::entry_cycle+8,shortened,(task_aw2::entry_cycle>>1)+38);
            check(history.back().after==shortened && history.size()==3,"all reschedules recorded; earlier cap retained");
            invalidate();
            rejects([&] { passive(); },"state import stales cap epoch");
            armed=false;
            const auto count=history.size();
            cap_note(0,0,0,0,10); reschedule(0,0,10,2);
            check(history.size()==count,"disabled journal is inert");
            std::fclose(output);
            std::cout<<"AW3 assertions: "<<checks<<"\n";
            return 0;
        }
        static Shutdown shutdown;
        std::atexit(onexit);
        if (mode=="stale") provided.put("capture.serial",8,0);
        if (mode=="manifest") provided.hashes["mainram"][0]^=1;
        if (mode=="hidden") provided.put("hidden.cache_page",4,0);
        if (mode=="readiness") provided.put("timer.0.control",2,128);
        if (mode=="guard") {
            guarded_handoff([] { throw std::runtime_error("preserved AU guard failure"); });
        }
        if (mode=="rom") {
            const uint8_t bytes[3]={'a','b','c'};
            loaded_rom(bytes,3);
        }
        if (mode=="overflow") reschedule(0,task_aw2::entry_cycle,history.back().after,UINT64_MAX);
        if (mode=="thread") { std::thread worker([] { cap_note(0,0,0,0,128); }); worker.join(); }
        if (mode=="missing") provided.fields.erase("hidden.region_class");
        if (mode=="bound-cap") { seal(provided); reschedule(0,task_aw2::entry_cycle,history.back().after,1); }
        if (mode=="bound-import") { seal(provided); invalidate(); }
        if (mode=="disabled") armed=false;
        brainage_task_au::CPU cpu{};
        for (unsigned index=0;index<16;++index) cpu.R[index]=au_fixed::r[7][index];
        if (mode=="bad-au") cpu.R[0]^=1;
        try { brainage_task_au::au_control(cpu); }
        catch (const std::exception& error) { if (armed) fail(error.what()); throw; }
        marker("post-boundary-instruction"); marker("device-tail"); marker("IRQ-tail"); marker("ARM7-tail");
        return 90;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
