#include <fstream>
#include <iostream>
#include "aw6/prefix.h"
#include "source_path.h"

unsigned assertions=0;
void check(bool condition,const std::string& reason) {
    ++assertions;
    if (!condition) throw std::runtime_error(reason);
}
template<class Action> void reject(Action action) {
    bool failed=false;
    try { action(); } catch (const std::exception&) { failed=true; }
    check(failed,"expected fail-closed rejection");
}
void bind(const task_aw2::Snapshot& state) {
    task_aw4::full_schema(state);
    task_aw4::journal_valid(state);
    task_aw2::require(task_aw2::digest(state)=="ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526","terminal identity");
}
void persistence() { std::fputs("PERSISTENCE_SENTINEL",stderr); }
struct Shutdown { ~Shutdown() { std::fputs("SHUTDOWN_SENTINEL",stderr); } };
int main(int argc,char** argv) {
    try {
        check(argc==2 || argc==4,"canonical input, optional disposal mode/audit");
        std::ifstream input(argv[1]); std::string hex; input>>hex;
        check(!hex.empty() && hex.size()%2==0,"input encoding");
        std::vector<uint8_t> bytes;
        for (size_t index=0;index<hex.size();index+=2)
            bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
        const auto state=task_aw2::decode(bytes);
        bind(state);
        check(task_aw2::canonical(state)==bytes && state.fields.size()==411 && state.hashes.size()==5,"lossless full layout");
        if (argc==4) {
            Shutdown shutdown; std::atexit(persistence);
            FILE* audit=task_aw3::exclusive_audit(argv[3]);
            check(audit,"exclusive audit");
            task_aw2::audit_snapshot(audit,state);
            const bool success=std::string(argv[2])=="bound_terminal";
            bool binding_rejected=false;
            if (!success) {
                auto stale=state;
                ++stale.fields.at("capture.epoch").value;
                task_aw2::audit_snapshot(audit,stale);
                try { bind(stale); }
                catch (const std::exception&) { binding_rejected=true; }
                check(binding_rejected,"stale epoch must fail before disposal");
            }
            std::fprintf(audit,"{\"event\":\"%s\",\"binding_rejected\":%s,\"guest_instructions\":0,\"MMIO\":0}\n",
                success ? "bound_terminal" : "rejection",binding_rejected ? "true" : "false");
            task_aw::dispose(audit,success ? 73 : 79);
            std::fputs("SCHEDULER_DEVICE_IRQ_ARM7_SENTINEL",stderr);
        }
        check(!task_aw::enabled(),"default observer inert");
        task_aw6::ready_before(state,state.get("cycle9"));
        check(task_aw2::cost(state,11)==8,"source-grounded status-read cost");
        reject([&] { task_aw6::ready_before(state,state.get("cycle9")+8); });
        for (const auto& item:state.fields) {
            auto changed=state; changed.fields.erase(item.first);
            reject([&] { bind(changed); });
            changed=state; changed.fields.at(item.first).value^=1;
            reject([&] { bind(changed); });
            changed=state; changed.fields.at(item.first).width=item.second.width==8 ? 4 : 8;
            reject([&] { bind(changed); });
        }
        for (const auto& item:state.hashes) {
            auto changed=state; changed.hashes.at(item.first)[0]=item.second[0]=='0' ? '1' : '0';
            reject([&] { bind(changed); });
        }
        check(slice_rail::probe(state,0) && slice_rail::dispatches==2,"ordinary return redispatches before slice exit");
        check(slice_rail::g_runtime_cycles==state.get("cycle9") && slice_rail::g_slot[0].cycles==state.get("slot9.cycle"),"slot clock remains stale while redispatching");
        check(slice_rail::probe(state,1) && slice_rail::dispatches==2,"unwind-only return redispatches");
        check(slice_rail::probe(state,3) && slice_rail::dispatches==2,"insn-stop alone not a run_slice break");
        check(!slice_rail::probe(state,2) && slice_rail::g_runtime_cycles==state.get("slice_cap"),"at-cap synthetic control exits, but differs from immutable entry");
        check(!slice_rail::probe(state,4) && slice_rail::event_break,"fake-event synthetic control exits, but differs from immutable entry");
        slice_rail::probe(state,0);
        const unsigned before=slice_rail::dispatches;
        slice_rail::run_slice(1,63);
        check(slice_rail::g_slot[1].cycles==1708437888ULL && slice_rail::g_slot[1].deferred_cycles==2,"conditional ARM7 HALT catch-up preserves parked debt");
        check(slice_rail::dispatches==before && !slice_rail::irq_calls && !slice_rail::dma_calls,"conditional ARM7 catch-up no CPU instruction");
        timer_rail::begin(state);
        timer_rail::nds_tick_timers(0,state.get("cycle9"));
        timer_rail::nds_tick_timers(1,state.get("cycle9")>>1);
        check(timer_rail::g_timer[0][0].counter==14558 && timer_rail::g_timer[0][0].accum==62,"timer0 conditional evolution");
        check(timer_rail::g_timer[1][0].counter==50776 && timer_rail::g_timer[1][0].accum==43,"timer4 conditional evolution");
        check(timer_rail::g_timer[1][1].counter==64195 && timer_rail::g_timer[1][1].accum==39,"timer5 conditional evolution");
        check(!timer_rail::irq_calls && !timer_rail::break_calls && !timer_rail::g_counts.timer_ovf,"conditional timer phase no overflow/IRQ");
        gpu_rail::GPU3D idle,queued;
        queued.GeometryEnabled=true; queued.CmdPIPE.empty=false;
        check(idle.CyclesToRunFor()==0 && queued.CyclesToRunFor()==0 && state.get("service.gpu_debt")==0,"equal observed GPU debt");
        idle.Run(); queued.Run();
        check(idle.commands==0 && queued.commands==1,"same debt has different actual Run branches");
        check(idle.Timestamp==1708437888 && queued.Timestamp==1708437888,"hidden GPU timestamp also changes");
        bind(state);
        check(!task_aw::enabled(),"no observer/activation installed by tests");
        std::cout<<"{\"assertions\":"<<assertions<<",\"guest_instructions\":0,\"runtime_MMIO\":0,\"redispatch_proven\":true,\"GPU_projection_ambiguous\":true}\n";
        return 0;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
