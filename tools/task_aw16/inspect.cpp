#include "fixture.h"
#include "providers.h"

namespace rail {
struct DisabledRedispatch {};
#include "tail.inc"
#include "next_round.inc"
inline void runtime_dispatch(uint32_t target) {
    task_aw12::Frame frame(g_static_guard!=nullptr,g_tail_dispatch!=nullptr);
    if (++dispatches>1) {
        if (mode=="disabled") throw DisabledRedispatch{};
        forbidden_service();
    }
    if (mode!="disabled") task_aw2::require(target==0x02001980,"scalar pre-existing dispatch context; never a B4 dispatch");
    g_runtime_cycles=baseline.get("cycle9");
    if (mode!="disabled") g_cpu.R[15]=baseline.get("r15");
    if (mode=="disabled") return;
    task_aw::emit(task_aw::Kind::retired,0x020019b0);
    Cpu context=g_cpu;
    if (task_aw12::tier3_exit()) {
        sync_out(context); nds_preserve_unwind_state(); task_aw12::preserved();
    }
}
}

unsigned assertions=0;
void check(bool condition,const std::string& reason) { ++assertions; task_aw2::require(condition,reason); }
template<class Action> void reject(Action action) {
    bool rejected=false;
    try { action(); } catch (const std::exception&) { rejected=true; }
    check(rejected,"expected negative rejection");
}
task_aw2::Snapshot read_snapshot(const char* path) {
    std::ifstream input(path); std::string hex,extra; input>>hex;
    check(!hex.empty() && hex.size()%2==0 && hex.size()<1048576 && !(input>>extra),"canonical metadata input");
    std::vector<uint8_t> bytes;
    for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
    return task_aw2::decode(bytes);
}
void geometry(const task_aw2::Snapshot& observed) {
    auto& gpu=rail::g_nds.GPU.GPU3D;
    gpu.GeometryEnabled=observed.get("gpu.geometry"); gpu.FlushRequest=observed.get("gpu.flush"); gpu.GXStat=observed.get("gpu.stat");
    gpu.CycleCount=observed.get("gpu.cycles"); gpu.Timestamp=observed.get("gpu.timestamp");
    gpu.VertexSlotsFree=observed.get("gpu.vertex_slots_free");
    rail::g_nds.ARM9Timestamp=observed.get("gpu.arm9_timestamp"); rail::g_nds.ARM9ClockShift=observed.get("gpu.clock_shift");
    check(task_aw12::runtime_gpu_observation()==observed,"actual const GPU facade reproduces AW14 metadata");
}
void persistence() { std::fputs("PERSISTENCE_SENTINEL",stderr); }
struct Shutdown { ~Shutdown() { std::fputs("SHUTDOWN_SENTINEL",stderr); } };
bool fault_done=false;
void fault(const std::string& label) {
    using namespace rail;
    if (fault_done) return;
    const bool initial=label=="successor_admitted";
    if (!initial && label!="time_published" && label!="target_selected" && label!="slice_begun_stop") return;
    if (mode=="stale-epoch" && initial) { fault_done=true; ++task_aw3::epoch; }
    if (mode=="ledger" && initial) { fault_done=true; task_aw7::ledger->previous[0]^=1; }
    if (mode=="ledger-seal" && initial) { fault_done=true; task_aw7::ledger->seal.fields.begin()->second.value^=1; }
    if (mode=="journal-bound" && initial) { fault_done=true; task_aw3::bound=true; }
    if (mode=="missing-owner" && initial) { fault_done=true; task_aw16::current=nullptr; task_aw16::mark("scheduler_device"); }
    if (mode=="ledger-plan" && initial) {
        fault_done=true;
        auto changed=std::make_shared<std::vector<task_aw2::Observation>>(*task_aw7::ledger->plan);
        changed->at(1).pc^=4; task_aw7::ledger->plan=changed;
    }
    if (mode=="duplicate-owner" && initial) {
        fault_done=true; task_aw16::receive_fence(task_aw3::output,task_aw3::passive(),task_aw12::runtime_gpu_observation(),1,566,8,
            "10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4");
    }
    if (mode=="duplicate-arm" && initial) { fault_done=true; task_aw16::arm(task_aw3::output); }
    if (mode=="overlay-after" && initial) { fault_done=true; g_live.enabled=true; }
    if (mode=="wifi-after" && initial) { fault_done=true; g_bridge->nds.pending=true; }
    if (mode=="trace-after" && initial) { fault_done=true; ++g_gx_run_trace_count; }
    if (mode=="cap-short" && initial) { fault_done=true; --g_cycle_cap; }
    if (mode=="irq" && initial) { fault_done=true; baseline.fields.at("irq7.if").value|=baseline.get("irq7.ie"); }
    if (mode=="timer" && initial) { fault_done=true; g_timer[0][0].counter=65535; }
    if (mode=="readiness" && initial) { fault_done=true; g_spi_deadline=0; baseline.fields.at("spi.deadline").value=0; }
    if (mode=="fetch" && initial) { fault_done=true; task_aw12::Frame forbidden(false,false); }
    if (mode=="dispatch" && initial) { fault_done=true; runtime_dispatch(0x020019b4); }
    if (mode=="MMIO" && initial) { fault_done=true; task_aw::emit(task_aw::Kind::access_before,0x020019b4,0x04000280,2); }
    if (mode=="unexpected-service" && initial) { fault_done=true; task_aw::emit(task_aw::Kind::irq); }
    if (mode=="reordered" && initial) { fault_done=true; task_aw16::mark("gpu_done"); }
    if (mode=="quantum" && label=="target_selected") { fault_done=true; task_aw16::slice_gate(0,48); }
    if (mode=="cap-new" && label=="slice_begun_stop") { fault_done=true; --g_cycle_cap; }
    if (mode=="omit-phase" && label=="time_published") fault_done=true;
}
bool skip(const std::string& label) { return rail::mode=="omit-phase" && label=="time_published"; }

void units(const task_aw2::Snapshot& terminal) {
    auto core=terminal; core.put("unwinding",1,1); core.put("slot9.cycle",8,core.get("cycle9"));
    const auto extra=task_aw16::auxiliary();
    task_aw16::aux_admit(extra,core);
    const auto gpu=task_aw12::runtime_gpu_observation();
    check(task_aw16::tail_plan(core,gpu,extra).size()==26,"complete fixed host-only plan");
    check(extra.fields.size()==19,"complete new auxiliary schema");
    check(task_aw16::auxiliary()==extra,"repeat passive auxiliary sample");
    for (const auto& item:extra.fields) {
        auto changed=extra; changed.fields.erase(item.first);
        reject([&] { task_aw16::aux_schema(changed); });
        changed=extra; changed.fields.at(item.first).width=item.second.width==8 ? 4 : 8;
        reject([&] { task_aw16::aux_schema(changed); });
        changed=extra; changed.fields.at(item.first).value^=1;
        check(task_aw2::digest(changed)!=task_aw2::digest(extra),"each auxiliary cell binds identity");
    }
    for (const auto* name:{"journal.bound","overlay.enabled","wifi.network_enabled","wifi.worker","wifi.scheduled","scheduler.modulus","scheduler.sample"}) {
        auto changed=extra; changed.fields.at(name).value=1;
        reject([&] { task_aw16::aux_admit(changed,core); });
    }
    rail::g_live.opaque_noninterfering=UINT64_MAX;
    check(task_aw16::auxiliary()==extra,"disabled overlay dominates inaccessible countdown/work state");
    check(!task_aw16::current && !task_aw16::spent && !task_aw::enabled(),"no default owner/observer installed");
    for (const auto* name:{"capture.epoch","capture.serial","scheduler.round_epoch","slice_cap","cycle7","irq9.ie","div.deadline","hidden.yield"}) {
        auto changed=core; changed.fields.at(name).value^=1;
        reject([&] { task_aw16::tail_plan(changed,gpu,extra); });
    }
    for (const auto& identity:core.hashes) {
        auto changed=core; changed.hashes.at(identity.first)[0]^=1;
        reject([&] { task_aw16::tail_plan(changed,gpu,extra); });
    }
    std::cout<<"{\"assertions\":"<<assertions<<",\"guest\":0,\"MMIO\":0}\n";
}
int main(int argc,char** argv) {
    try {
        check(argc==6,"mode terminal prefix-entry GPU audit");
        rail::mode=argv[1];
        const auto terminal=read_snapshot(argv[2]),initial=read_snapshot(argv[3]),gpu=read_snapshot(argv[4]);
        rail::begin(terminal); geometry(gpu);
        if (rail::mode!="no-bridge") rail::g_bridge=std::make_unique<rail::Bridge>();
        if (rail::mode=="no-device") rail::g_bridge->wifi=false;
        if (rail::mode=="trace-wrap") {
            rail::g_gx_run_trace_count=65536;
            rail::g_gx_run_trace[65535]={65536,3416875650,0x80000000,0x80000000,0,0};
        }
        if (rail::mode=="units") { units(terminal); return 0; }
        auto* output=task_aw3::exclusive_audit(argv[5]); check(output,"exclusive test audit"); task_aw3::output=output;
        if (rail::mode=="disabled") {
            reject([&] { task_aw16::arm(output); });
            bool redispatched=false;
            try { rail::run_slice(0,128); } catch (const rail::DisabledRedispatch&) { redispatched=true; }
            check(redispatched && rail::dispatches==2 && !task_aw16::current,"disabled original redispatch");
            std::fputs("{\"event\":\"disabled\",\"guest\":0}\n",output); std::fclose(output); return 0;
        }
        if (rail::mode!="legacy-fence") task_aw16::arm(output);
        task_aw16::test_fault=fault; task_aw16::test_skip=skip;
        task_aw12::Controller predecessor(output,task_aw3::passive,task_aw12::runtime_gpu_observation,task_aw12::runtime_saved_unwind);
        task_aw12::install(predecessor); task_aw12::frame_serial=565;
        task_aw7::ledger=std::make_unique<task_aw6::Ledger>(initial);
        for (unsigned index=0;index<68;++index) {
            const auto event=task_aw7::ledger->plan->at(index);
            check(task_aw7::ledger->accept(event,task_aw7::ledger->previous),"original prefix model receipt");
            if (event.kind==task_aw::Kind::access_after) ++task_aw7::bus_calls;
        }
        task_aw7::armed=task_aw7::owned=true; task_aw7::owner=std::this_thread::get_id();
        task_aw::observer=task_aw7::receive; task_aw::audit=output;
        if (rail::mode=="overlay-entry") rail::g_live.enabled=true;
        if (rail::mode=="wifi-entry") rail::g_bridge->nds.pending=true;
        if (rail::mode=="worker-entry") rail::g_bridge->worker_thread=reinterpret_cast<void*>(uintptr_t(1));
        if (rail::mode=="network-entry") rail::g_network_config.enabled=true;
        if (rail::mode=="trace-overflow") rail::g_gx_run_trace_count=UINT64_MAX;
        if (rail::mode=="old-ledger") --task_aw7::bus_calls;
        Shutdown shutdown; std::atexit(persistence);
        rail::g_cpu.R[15]=0x02001980;
        rail::run_slice(0,128);
        {
            rail::RoundActivityGuard original_round_scope;
            rail::tail_from_fence();
        }
        rail::scheduler_run_round();
        std::fputs("SCHEDULER_DEVICE_IRQ_ARM7_GUEST_SENTINEL",stderr); return 90;
    } catch (const std::exception& error) {
        if (task_aw16::current) task_aw16::current->fail(error.what());
        std::cerr<<error.what()<<'\n'; return 2;
    }
}
