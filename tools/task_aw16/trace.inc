namespace task_aw16 {
void trace_aux(Snapshot& out) {
    const auto count=nds_gpu3d_run_trace_count();
    NdsGxRunTraceEntry entry{};
    require(!count || nds_gpu3d_run_trace_get(count,&entry),"AW16 passive trace last-record mismatch");
    out.put("trace.count",8,count);
    out.put("trace.last.count",8,entry.count);
    out.put("trace.last.cycle",8,entry.arm9_cycles);
    out.put("trace.last.before",4,entry.gxstat_before);
    out.put("trace.last.after",4,entry.gxstat_after);
    out.put("trace.last.debt_before",4,uint32_t(entry.cycle_count_before));
    out.put("trace.last.debt_after",4,uint32_t(entry.cycle_count_after));
}
}
