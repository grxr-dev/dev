
namespace task_aw {
void runtime_snapshot(Snapshot& out) {
    out.values["pc"]=g_cpu.R[15];
    for (unsigned index=0;index<16;++index)
        out.values["r"+std::to_string(index)]=g_cpu.R[index];
    out.values["cpsr"]=g_cpu.cpsr;
    out.values["cycle9"]=g_runtime_cycles;
    out.values["ordinal9"]=g_insn_count[0];
    out.values["ordinal7"]=g_insn_count[1];
    out.values["snapshot_ordinal"]=g_insn_count[0];
    out.values["active_cpu"]=g_nds_active;
    out.values["slice_cap"]=g_cycle_cap;
    out.values["fast_limit"]=g_nds_fast_limit;
    out.values["deferred"]=g_deferred_cycles;
    out.values["terminal"]=g_nds_terminal;
    out.values["insn_stop"]=g_nds_insn_stop;
    out.values["event_break"]=nds_event_break_hit();
    out.values["force_tier3"]=g_nds_force_tier3;
    out.values["unwinding"]=g_nds_unwinding;
    out.values["yield_hint"]=g_yield_poll_hint;
    out.values["cpu_fast_poll"]=g_cpu_fast_poll;
    out.values["return_depth"]=g_crs_depth;
    out.bytes["return_stack"].resize(g_crs_depth*sizeof(uint32_t));
    if (g_crs_depth) std::memcpy(out.bytes["return_stack"].data(),g_crs,g_crs_depth*sizeof(uint32_t));
    NdsRuntimeSaveState runtime{};
    runtime_savestate_export(&runtime);
    out.copy("runtime",runtime);
}
}
