#include "binding.h"
#include "aw8_io.cpp"
namespace task_aw8 {
void io_begin() {
    const auto& saved=entry();
    g_insn_hook_armed=0;
    g_cart_backup.sram.assign(262144,0xa5); g_cart_backup.dirty=saved.get("save_dirty");
    g_display_last=saved.get("service.display_last"); g_rtc_processed_ticks=saved.get("service.rtc_processed");
    g_divcnt=saved.get("div.control"); g_div_deadline=saved.get("div.deadline");
    g_sqrt_deadline=saved.get("sqrt.deadline");
    g_card_deadline=saved.get("card.deadline"); g_spi_deadline=saved.get("spi.deadline"); g_auxspi_deadline=saved.get("auxspi.deadline");
    g_card_end_event=saved.get("card_end"); g_gxfifo_stall=saved.get("gpu_stall");
    g_romctrl=saved.get("service.card_control"); g_spicnt=saved.get("service.spi_control"); g_auxspicnt=saved.get("service.auxspi_control");
    g_powered_off=saved.get("service.powered_off"); g_fw_dirty=saved.get("service.firmware_dirty");
    const char* names[]={"div.nlo","div.nhi","div.dlo","div.dhi","div.qlo","div.qhi","div.rlo","div.rhi"};
    uint32_t* targets[]={&g_div_numer[0],&g_div_numer[1],&g_div_denom[0],&g_div_denom[1],&g_div_quot[0],&g_div_quot[1],&g_div_rem[0],&g_div_rem[1]};
    for (unsigned index=0;index<8;++index) *targets[index]=saved.get(names[index]);
    for (unsigned cpu=0;cpu<2;++cpu) {
        const auto irq=task_aw2::numbered("irq",cpu ? 7 : 9)+".";
        g_ime[cpu]=saved.get(irq+"ime"); g_ie[cpu]=saved.get(irq+"ie"); g_if[cpu]=saved.get(irq+"if");
        g_nds_irq_pending_cache[cpu]=saved.get(cpu ? "service.irq_cache7" : "service.irq_cache9");
        g_cpu_halted[cpu]=saved.get(cpu ? "halt7" : "halt9");
        g_halt_entry_cycle[cpu]=saved.get(task_aw2::numbered("service.halt_epoch.",cpu));
        g_dma_entry_cycle[cpu]=saved.get(task_aw2::numbered("service.dma_entry.",cpu));
        g_timer_last[cpu]=saved.get(task_aw2::numbered("timer.",cpu*4)+".last");
        for (unsigned index=0;index<4;++index) {
            const auto dma=task_aw2::numbered("dma.",cpu*4+index)+".";
            auto& channel=g_dma[cpu][index];
            channel.running=saved.get(dma+"running"); channel.in_progress=saved.get(dma+"in_progress");
            channel.cnt=saved.get(dma+"count"); channel.remaining=saved.get(dma+"remaining");
            channel.cur_src=saved.get(dma+"src"); channel.cur_dst=saved.get(dma+"dst");
            channel.start_mode=saved.get(dma+"mode"); channel.burst_index=saved.get(dma+"burst");
            const auto timer=task_aw2::numbered("timer.",cpu*4+index)+".";
            auto& tick=g_timer[cpu][index];
            tick.ctrl=saved.get(timer+"control"); tick.counter=saved.get(timer+"counter");
            tick.reload=saved.get(timer+"reload"); tick.accum=saved.get(timer+"accum");
        }
    }
    bind("save",brainage_custom::resource_detail::sha256(g_cart_backup.sram.data(),g_cart_backup.sram.size()));
}
void model_write(unsigned index) {
    if (index==0) g_divcnt=1;
    else if (index==2) g_div_numer[0]=0;
    else if (index==5) g_div_numer[1]=4096;
    else if (index==6) g_div_denom[0]=4096;
    else if (index==7) g_div_denom[1]=0;
    else require(false,"unexpected modeled divider write");
    g_divcnt|=0x8000;
    g_div_deadline=(g_runtime_cycles>>1)+34;
    nds_reschedule_slice(g_div_deadline);
}
std::vector<uint8_t> save_copy() { return g_cart_backup.sram; }
void io_mutate(const std::string& name) {
    if (name=="save") g_cart_backup.sram.at(1)^=1;
    else if (name=="irq") g_if[0]|=1;
    else if (name=="rtc") --g_rtc_processed_ticks;
    else if (name=="timer") g_timer[0][0].counter=65535;
    else if (name=="device") g_spi_deadline=0;
    else if (name=="divider") ++g_div_deadline;
    else require(false,"unknown IO mutation");
}
}
