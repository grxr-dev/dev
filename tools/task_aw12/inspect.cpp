#include "fixture.h"

unsigned assertions=0;
void check(bool condition,const std::string& reason) {
    ++assertions;
    task_aw2::require(condition,reason);
}
template<class Action> void reject(Action action) {
    bool failed=false;
    try { action(); } catch (const std::exception&) { failed=true; }
    check(failed,"expected fail-closed rejection");
}
task_aw2::Snapshot read_snapshot(const char* path) {
    std::ifstream input(path); std::string hex; input>>hex;
    check(!hex.empty() && !(hex.size()%2),"canonical file");
    std::vector<uint8_t> bytes;
    for (size_t index=0;index<hex.size();index+=2)
        bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
    auto state=task_aw2::decode(bytes);
    check(task_aw2::canonical(state)==bytes,"canonical round trip");
    return state;
}
void persistence() { std::fputs("PERSISTENCE_SENTINEL",stderr); }
struct Shutdown { ~Shutdown() { std::fputs("SHUTDOWN_SENTINEL",stderr); } };

void units(const task_aw2::Snapshot& terminal) {
    check(task_aw2::digest(terminal)==task_aw12::terminal_identity,"immutable full terminal identity");
    for (const auto& item:terminal.fields) {
        for (unsigned operation=0;operation<3;++operation) {
            auto changed=terminal;
            if (operation==0) changed.fields.erase(item.first);
            if (operation==1) changed.fields.at(item.first).value^=1;
            if (operation==2) changed.fields.at(item.first).width=item.second.width==8 ? 4 : 8;
            reject([&] {
                task_aw4::full_schema(changed); task_aw4::journal_valid(changed);
                task_aw2::require(task_aw2::digest(changed)==task_aw12::terminal_identity,"protected mutation");
            });
        }
    }
    for (const auto& item:terminal.hashes) {
        auto changed=terminal; changed.hashes.at(item.first)[0]^=1;
        reject([&] { task_aw2::require(task_aw2::digest(changed)==task_aw12::terminal_identity,"identity mutation"); });
    }
    rail::Gpu device;
    auto state=task_aw12::gpu_project(device,3416875650,1);
    task_aw12::gpu_admit(state,terminal);
    check(!task_aw12::gpu_work(state) && state.fields.size()==19,"complete idle GPU projection");
    check(task_aw2::decode(task_aw2::canonical(state))==state,"GPU canonical round trip");
    for (const auto& item:state.fields) {
        auto changed=state; changed.fields.erase(item.first);
        reject([&] { task_aw12::gpu_schema(changed); });
        changed=state; changed.fields.at(item.first).width=item.second.width==8 ? 4 : 8;
        reject([&] { task_aw12::gpu_schema(changed); });
        changed=state; changed.fields.at(item.first).value^=1;
        check(task_aw2::digest(changed)!=task_aw2::digest(state),"GPU field bound");
    }
    for (unsigned index=0;index<4;++index) device.CmdPIPE.Write({index+100,uint8_t(index+10)});
    check(device.CmdPIPE.Read().Command==10,"queue read setup");
    device.CmdPIPE.Write({104,14});
    auto queued=task_aw12::gpu_project(device,3416875650,1);
    check(queued.get("gpu.pipe.0.command")==11 && queued.get("gpu.pipe.3.parameter")==104,"logical wrapped FIFO order");
    check(task_aw12::gpu_work(queued),"same debt, different GPU work eligibility");
    reject([&] { task_aw12::gpu_admit(queued,terminal); });
    check(task_aw12::gpu_project(device,3416875650,1)==queued && device.CmdPIPE.Level()==4,"passive queue projection");
    device.CmdPIPE.Clear(); device.GXStat=1u<<27;
    check(task_aw12::gpu_work(task_aw12::gpu_project(device,3416875650,1)),"busy pipeline branch");
    device.GeometryEnabled=false;
    check(!task_aw12::gpu_work(task_aw12::gpu_project(device,3416875650,1)),"geometry gate from source");
    reject([&] { task_aw12::gpu_admit(task_aw12::gpu_project(device,3416875650,1),terminal); });
    check(!task_aw12::current && !task_aw12::spent,"default unowned");
    task_aw12::guard_guest(); task_aw12::pre_device_fence(); task_aw12::slice_saved(0);
    check(!task_aw12::tier3_exit() && !task_aw12::slice_exit(0),"disabled hooks inert");
    std::cout<<"{\"assertions\":"<<assertions<<",\"guest_instructions\":0,\"MMIO\":0}\n";
}

int main(int argc,char** argv) {
    try {
        check(argc==5,"mode terminal initial audit");
        rail::mode=argv[1];
        const auto terminal=read_snapshot(argv[2]);
        if (rail::mode=="units") { units(terminal); return 0; }
        rail::begin(terminal);
        auto* output=task_aw3::exclusive_audit(argv[4]);
        check(output!=nullptr,"exclusive audit");
        task_aw3::output=output;
        task_aw12::Controller controller(output,rail::core_source,rail::gpu_source,task_aw12::runtime_saved_unwind);
        if (rail::mode=="disabled") {
            reject([&] { task_aw12::install(controller); });
            reject([&] { task_aw12::arm_capture_only(output); });
            bool redispatched=false;
            try { rail::run_slice(0,128); } catch (const rail::DisabledRedispatch&) { redispatched=true; }
            check(redispatched && rail::dispatches==2 && !task_aw12::current && !task_aw12::spent,"disabled original under-cap redispatch");
            check(rail::core_source()==terminal && !rail::services,"disabled full state unchanged at redispatch");
            std::fputs("{\"event\":\"disabled\",\"dispatches\":2}\n",output);
            std::fclose(output); return 0;
        }
        if (rail::mode=="runtime-facade") task_aw12::arm_capture_only(output);
        else task_aw12::install(controller);
        if (rail::mode=="prior-frames") {
            for (unsigned index=0;index<3;++index) { task_aw12::Frame completed(false,false); }
        }
        const auto initial=read_snapshot(argv[3]);
        task_aw7::ledger=std::make_unique<task_aw6::Ledger>(initial);
        for (unsigned index=0;index<68;++index) {
            const auto event=(*task_aw7::ledger->plan)[index];
            check(task_aw7::ledger->accept(event,task_aw7::ledger->previous),"authenticated historical prefix receipt");
            if (event.kind==task_aw::Kind::access_after) ++task_aw7::bus_calls;
        }
        check(task_aw7::bus_calls==18 && task_aw7::ledger->cursor==68,"old guards retained");
        task_aw7::armed=true; task_aw7::owned=true; task_aw7::owner=std::this_thread::get_id();
        task_aw::observer=task_aw7::receive; task_aw::audit=output;
        auto& gpu=rail::g_nds.GPU.GPU3D;
        if (rail::mode=="gpu-command") gpu.CmdPIPE.Write({42,16});
        if (rail::mode=="gpu-fifo") gpu.CmdFIFO.Write({42,16});
        if (rail::mode=="gpu-stall") gpu.CmdStallQueue.Write({42,16});
        if (rail::mode=="gpu-busy") gpu.GXStat=1u<<27;
        if (rail::mode=="gpu-latent") { gpu.FlushRequest=1; gpu.VertexPipeline=1; }
        if (rail::mode=="gpu-ahead") gpu.Timestamp=UINT64_MAX;
        if (rail::mode=="gpu-debt") gpu.CycleCount=1;
        if (rail::mode=="static-guard") rail::g_static_guard=reinterpret_cast<void*>(uintptr_t(1));
        if (rail::mode=="tail-parent") rail::g_tail_dispatch=reinterpret_cast<void*>(uintptr_t(1));
        if (rail::mode=="spent") task_aw12::spent=true;
        if (rail::mode=="stale-entry") ++task_aw3::epoch;
        if (rail::mode=="old-bus-count") --task_aw7::bus_calls;
        if (rail::mode=="missing-old-event") --task_aw7::ledger->cursor;
        Shutdown shutdown; std::atexit(persistence);
        rail::run_slice(0,128);
        if (rail::mode=="duplicate-save") task_aw12::slice_saved(0);
        rail::scheduler_boundary();
        std::fputs("SCHEDULER_DEVICE_IRQ_ARM7_SENTINEL",stderr);
        return 90;
    } catch (const std::exception& error) {
        if (task_aw12::current) task_aw12::current->fail(error.what());
        std::cerr<<error.what()<<'\n'; return 2;
    }
}
