namespace task_aw3 {
void io_snapshot(Snapshot& out) {
    NdsIoCoreSaveState core{};
    io_savestate_export(&core);
    for (unsigned cpu=0;cpu<2;++cpu) {
        const auto irq="irq"+std::to_string(cpu==0 ? 9 : 7)+".";
        out.put(irq+"ime",4,core.ime[cpu]); out.put(irq+"ie",4,core.ie[cpu]); out.put(irq+"if",4,core.irq_flags[cpu]);
        out.put(irq+"cached",4,(core.ime[cpu]&1) && (core.ie[cpu]&core.irq_flags[cpu]));
        out.put(cpu==0 ? "halt9" : "halt7",1,core.cpu_halted[cpu]);
        out.put("service.halt_epoch."+std::to_string(cpu),8,core.halt_entry_cycle[cpu]);
        out.put("service.dma_entry."+std::to_string(cpu),8,core.dma_entry_cycle[cpu]);
        for (unsigned index=0;index<4;++index) {
            const auto dma="dma."+std::to_string(cpu*4+index)+".";
            const auto& state=core.dma[cpu][index];
            out.put(dma+"active",1,state.running || state.in_progress);
            out.put(dma+"running",1,state.running); out.put(dma+"in_progress",1,state.in_progress);
            out.put(dma+"count",4,state.cnt); out.put(dma+"remaining",4,state.remaining);
            out.put(dma+"src",4,state.cur_src); out.put(dma+"dst",4,state.cur_dst);
            out.put(dma+"mode",1,state.start_mode); out.put(dma+"burst",2,state.burst_index);
            const auto timer="timer."+std::to_string(cpu*4+index)+".";
            const auto& tick=core.timer[cpu][index];
            out.put(timer+"control",2,tick.ctrl); out.put(timer+"counter",2,tick.counter);
            out.put(timer+"reload",2,tick.reload); out.put(timer+"accum",8,tick.accum);
            out.put(timer+"last",8,core.timer_last[cpu]);
        }
    }
    out.put("service.irq_cache9",4,g_nds_irq_pending_cache[0]);
    out.put("service.irq_cache7",4,g_nds_irq_pending_cache[1]);
    out.put("gpu_stall",1,core.gxfifo_stall); out.put("card_end",1,g_card_end_event);
    out.put("div.control",2,core.divcnt); out.put("div.deadline",8,core.div_deadline);
    const char* names[]={"div.nlo","div.nhi","div.dlo","div.dhi","div.qlo","div.qhi","div.rlo","div.rhi"};
    const uint32_t values[]={core.div_numer[0],core.div_numer[1],core.div_denom[0],core.div_denom[1],
        core.div_quot[0],core.div_quot[1],core.div_rem[0],core.div_rem[1]};
    for (unsigned index=0;index<8;++index) out.put(names[index],4,values[index]);
    out.put("card.deadline",8,g_card_deadline); out.put("spi.deadline",8,g_spi_deadline);
    out.put("auxspi.deadline",8,g_auxspi_deadline); out.put("sqrt.deadline",8,core.sqrt_deadline);
    out.put("service.card_control",4,g_romctrl); out.put("service.spi_control",2,g_spicnt);
    out.put("service.auxspi_control",2,g_auxspicnt);
    out.put("service.powered_off",1,core.powered_off); out.put("service.firmware_dirty",1,g_fw_dirty);
    out.put("service.display_last",8,core.display_last); out.put("service.rtc_processed",8,g_rtc_processed_ticks);
    const auto system=out.get("system_timestamp");
    out.put("service.rtc_due",8,task_aw2::multiply(system,32768)/33513982);
    const uint8_t* data=nullptr; uint32_t size=0; bool dirty=false;
    require(nds_io_cartridge_save_snapshot(&data,&size,&dirty) && data && size==262144,"passive save source");
    out.hashes["save"]=brainage_custom::resource_detail::sha256(data,size);
    out.put("save_dirty",1,dirty); out.put("logical_saves",8,logical_saves); out.put("flash_commits",8,flash_commits);
    out.hashes["rom"]=rom_identity;
    out.hashes["framework_commit"]="3a57236bb23d25dcb4caad7d58d733311062ff5e";
    out.put("capture.end_cycle",8,g_runtime_cycles); out.put("capture.end_ordinal",8,g_insn_count[0]);
}
}
