
namespace task_aw {
void scheduler_snapshot(Snapshot& out) {
    out.values["owner_thread"]=std::this_thread::get_id()==g_owner_thread;
    if (out.values.at("owner_thread")!=1) return;
    out.values["round_active"]=g_round_active;
    out.values["system_timestamp"]=g_sys_timestamp;
    out.values["cycle7"]=g_slot[1].cycles;
    out.values["current_slot"]=static_cast<uint64_t>(g_cur);
    NdsSchedulerSaveState copy{};
    for (unsigned cpu=0;cpu<2;++cpu) {
        copy.cpu[cpu]=g_slot[cpu].state;
        copy.cycles[cpu]=g_slot[cpu].cycles;
        copy.crs_depth[cpu]=g_slot[cpu].crs_depth;
        copy.deferred_cycles[cpu]=g_slot[cpu].deferred_cycles;
        copy.started[cpu]=g_slot[cpu].started;
        copy.terminal_halted[cpu]=g_slot[cpu].halted;
        std::memcpy(copy.crs[cpu],g_slot[cpu].crs,sizeof(copy.crs[cpu]));
    }
    copy.system_timestamp=g_sys_timestamp;
    out.copy("scheduler",copy);
}
}
