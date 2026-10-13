namespace task_aw3 {
void scheduler_snapshot(Snapshot& out) {
    out.put("owner_thread",1,std::this_thread::get_id()==g_owner_thread);
    if (!out.get("owner_thread")) return;
    out.put("round_active",1,g_round_active);
    require(g_cur==0,"capture requires active ARM9 scheduler slot");
    out.put("current_slot",1,g_cur); out.put("system_timestamp",8,g_sys_timestamp);
    out.put("cycle7",8,g_slot[1].cycles); out.put("slot9.cycle",8,g_slot[0].cycles);
    out.put("slot9.deferred",4,g_slot[0].deferred_cycles); out.put("deferred7",4,g_slot[1].deferred_cycles);
    out.put("arm7_started",1,g_slot[1].started); out.put("arm7_terminal",1,g_slot[1].halted);
    out.put("slot9.target",8,history.front().after);
    const auto* synth=std::getenv("NDS_SYNTH_EVENT_US");
    out.put("synth_config",1,synth && *synth && std::strcmp(synth,"0")!=0);
    out.put("scheduler.round_epoch",8,g_aw3_round_epoch);
    out.put("scheduler.planned_target",8,g_aw3_planned_target);
    out.put("scheduler.next_event",8,g_aw3_next_event);
    out.put("wifi.deadline",8,nds_wifi_next_event_time());
    NdsSpuSaveState audio{};
    require(spu_savestate_export(&audio),"passive SPU phase unavailable");
    out.put("service.spu_mixes",8,audio.mix_count);
    out.put("service.gpu_debt",4,uint32_t(nds_gpu3d_cycles_to_run()));
    for (unsigned cpu=0;cpu<2;++cpu) {
        out.put("scheduler.started."+std::to_string(cpu),1,g_slot[cpu].started);
        out.put("scheduler.halted."+std::to_string(cpu),1,g_slot[cpu].halted);
    }
}
}
