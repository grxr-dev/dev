#include "binding.h"
#include "aw8_runtime.cpp"
namespace task_aw8 {
void runtime_begin() {
    const auto& saved=entry();
    for (unsigned index=0;index<16;++index) g_cpu.R[index]=saved.get("r"+std::to_string(index));
    g_cpu.cpsr=saved.get("cpsr");
    g_nds_active=NdsCpu(saved.get("active_cpu")); g_nds_force_tier3=saved.get("force_tier3");
    g_insn_count[0]=saved.get("ordinal9"); g_insn_count[1]=saved.get("ordinal7");
    g_deferred_cycles=saved.get("deferred9"); g_nds_terminal=saved.get("terminal");
    g_nds_insn_stop=saved.get("insn_stop"); g_nds_unwinding=saved.get("unwinding");
    g_runtime_break_pc=saved.get("hidden.break_pc"); g_static_guard=nullptr;
    g_cpu_fast_poll=saved.get("hidden.cpu_poll"); g_cycle_fast_limit_enabled=saved.get("hidden.fast_enabled");
    g_nds_force_tier3_misses=saved.get("hidden.force_misses"); g_ctx[0].dispatch_epoch=saved.get("hidden.dispatch_epoch");
    g_crs_depth=saved.get("return_depth");
    for (unsigned index=0;index<g_crs_depth;++index) g_crs[index]=saved.get(task_aw2::numbered("return.",index));
    g_runtime_cycles=saved.get("cap.0.cycle"); g_cycle_cap=saved.get("cap.0.observed_before");
    task_aw3::epoch=saved.get("capture.epoch")-1; task_aw3::serial=saved.get("capture.serial")-1;
    nds_slice_begin(saved.get("slice_cap"));
    g_runtime_cycles=saved.get("cycle9");
    g_nds_fast_limit_publishes=saved.get("hidden.fast_publishes")-1;
    runtime_publish_fast_limit();
    require(g_yield_poll_hint==saved.get("hidden.yield"),"slice source-derived hint");
}
void fetch() {
    require(!nds_has_bank(g_cpu.R[15],0),"unexpected compiled takeover in Tier-3 fixture");
    nds_note_insn_retired(NDS_ARM9);
}
void commit(unsigned index,uint32_t cost) {
    if (index==1) g_cpu.R[12]=0;
    if (index==3) g_cpu.R[3]=4096;
    if (index==4) g_cpu.R[1]=0x04000298;
    if (index==9) g_cpu.R[14]=0x02001a24;
    if (index==10) g_cpu.R[1]=0x04000280;
    g_cpu.R[15]=index+1<11 ? task_aw2::pcs[index+1] : task_aw6::stop_pc;
    g_runtime_cycles+=cost+runtime_deferred_cycles_take();
}
void retire(unsigned index) {
    if (index==8) require(runtime_call_should_return(0x02001a20),"actual return-stack pop");
    if (index==9) runtime_call_push_return(0x02001a24);
}
void runtime_mutate(const std::string& name) {
    if (name=="ordinal") ++g_insn_count[0];
    else if (name=="cycle") ++g_runtime_cycles;
    else if (name=="cap") --g_cycle_cap;
    else if (name=="hint") g_yield_poll_hint^=1;
    else if (name=="debt") ++g_deferred_cycles;
    else if (name=="cpu") g_cpu.R[4]^=1;
    else if (name=="bank") ++g_ctx[0].dispatch_epoch;
    else if (name=="forbidden") g_cpu.R[15]=task_aw6::stop_pc;
    else require(false,"unknown runtime mutation");
}
}
