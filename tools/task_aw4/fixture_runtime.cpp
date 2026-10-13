#include "runtime_arm.cpp"
#include "fixture.h"
namespace task_aw4::fixture {
void runtime_begin() {
    const auto anchors=task_aw2::au_manifest();
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=anchors.get("r"+std::to_string(index));
    g_cpu.cpsr=anchors.get("cpsr");
    g_nds_active=NDS_ARM9; g_nds_force_tier3=true;
    g_insn_count[0]=anchors.get("ordinal9"); g_insn_count[1]=anchors.get("ordinal7");
    g_runtime_cycles=task_aw2::entry_cycle-9;
    g_yield_poll_hint=0; g_cpu_fast_poll=true; g_cycle_fast_limit_enabled=true;
    g_deferred_cycles=0; g_runtime_break_pc=0; g_static_guard=nullptr;
    g_nds_terminal=false; g_nds_unwinding=0;
    g_crs_depth=2; g_crs[0]=0x02067568; g_crs[1]=0x02001a20;
    nds_slice_begin(task_aw2::entry_cycle+119);
    g_runtime_cycles=task_aw2::entry_cycle;
    task_aw2::require(!runtime_should_yield_slow(),"real clean synthetic entry predicate");
}
void runtime_banks() {
    static DispatchEntry rows[12]{};
    for (unsigned index=0;index<12;++index) {
        rows[index].addr=task_aw2::pcs[index]; rows[index].fn=[] { std::abort(); };
        g_ctx[0].dispatch_index.push_back(&rows[index]);
    }
    std::sort(g_ctx[0].dispatch_index.begin(),g_ctx[0].dispatch_index.end(),
        [](const auto* left,const auto* right) { return left->addr<right->addr; });
    ++g_ctx[0].dispatch_epoch;
}
void runtime_fetch() {
    task_aw2::require(!nds_has_bank(g_cpu.R[15],0),"synthetic forced Tier-3 lookup cannot invoke a bank");
    nds_note_insn_retired(NDS_ARM9);
}
void runtime_commit(unsigned index,uint32_t cost) {
    if (index==1) g_cpu.R[12]=0;
    if (index==3) g_cpu.R[3]=4096;
    if (index==4) g_cpu.R[1]=0x04000298;
    if (index==9) g_cpu.R[14]=0x02001a24;
    if (index==10) g_cpu.R[1]=0x04000280;
    if (index==11) g_cpu.R[0]=0x8001;
    g_cpu.R[15]=index+1<task_aw2::pcs.size() ? task_aw2::pcs[index+1] : task_aw2::terminal_pc;
    g_runtime_cycles+=cost+runtime_deferred_cycles_take();
}
void runtime_retire(unsigned index) {
    if (index==8) task_aw2::require(runtime_call_should_return(0x02001a20),"synthetic real return-stack pop");
    if (index==9) runtime_call_push_return(0x02001a24);
}
void runtime_poll() { if (g_runtime_cycles>=g_nds_fast_limit) runtime_publish_fast_limit(); }
void mutate(const std::string& name) {
    if (name=="ordinal") ++g_insn_count[0];
    else if (name=="debt") g_deferred_cycles=1;
    else if (name=="cap") g_cycle_cap=g_runtime_cycles+1;
    else if (name=="latch") g_yield_poll_hint=1;
    else if (name=="cost") ++g_runtime_cycles;
    else if (name=="cpu") g_cpu.R[4]^=1;
    else task_aw2::require(false,"unknown runtime mutation");
}
}
