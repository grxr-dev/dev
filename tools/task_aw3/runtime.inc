namespace task_aw3 {
void runtime_snapshot(Snapshot& out) {
    for (unsigned index=0;index<16;++index) out.put("r"+std::to_string(index),4,g_cpu.R[index]);
    out.put("cpsr",4,g_cpu.cpsr);
    out.put("cycle9",8,g_runtime_cycles);
    out.put("ordinal9",8,g_insn_count[0]); out.put("ordinal7",8,g_insn_count[1]);
    out.put("snapshot_ordinal",8,g_insn_count[0]);
    out.put("active_cpu",1,g_nds_active); out.put("force_tier3",1,g_nds_force_tier3);
    out.put("slice_cap",8,g_cycle_cap); out.put("fast_limit",8,g_nds_fast_limit);
    out.put("deferred9",4,g_deferred_cycles); out.put("terminal",1,g_nds_terminal);
    out.put("insn_stop",1,g_nds_insn_stop); out.put("event_break",1,nds_event_break_hit());
    out.put("unwinding",1,g_nds_unwinding); out.put("return_depth",4,g_crs_depth);
    require(g_crs_depth<=32,"unclassified return stack depth");
    for (unsigned index=0;index<g_crs_depth;++index) out.put("return."+std::to_string(index),4,g_crs[index]);
    out.put("hidden.yield",4,g_yield_poll_hint); out.put("hidden.cpu_poll",1,g_cpu_fast_poll);
    out.put("hidden.force_misses",8,g_nds_force_tier3_misses);
    out.put("hidden.fast_enabled",1,g_cycle_fast_limit_enabled);
    out.put("hidden.break_pc",4,g_runtime_break_pc);
    out.put("hidden.static_changed",1,active_static_code_changed());
    out.put("hidden.fast_publishes",8,g_nds_fast_limit_publishes);
    out.put("hidden.dispatch_epoch",8,g_ctx[0].dispatch_epoch);
    for (const auto pc:task_aw2::pcs)
        out.put(task_aw2::address_key("hidden.bank.",pc),1,lookup_static(g_ctx[0],pc,false,nullptr,nullptr)!=nullptr);
}
}
