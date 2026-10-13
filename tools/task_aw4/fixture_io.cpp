#include "io.cpp"
#include "fixture.h"
namespace task_aw4::fixture {
void io_begin() {
    g_insn_hook_armed=0;
    g_cart_backup.sram.assign(262144,0xa5); g_cart_backup.dirty=false;
    g_display_last=(task_aw2::entry_cycle-9)>>1;
    g_rtc_processed_ticks=task_aw2::multiply(g_display_last,32768)/33513982;
    g_divcnt=0; g_div_deadline=UINT64_MAX;
    g_div_quot[0]=0x12345678; g_div_quot[1]=0x9abcdef0;
    g_div_rem[0]=0x87654321; g_div_rem[1]=0xdeadbeef;
}
void io_model_write(unsigned index) {
    if (index==0) g_divcnt=1;
    else if (index==2) g_div_numer[0]=0;
    else if (index==5) g_div_numer[1]=4096;
    else if (index==6) g_div_denom[0]=4096;
    else if (index==7) g_div_denom[1]=0;
    else task_aw2::require(false,"synthetic write index");
    g_divcnt|=0x8000;
    g_div_deadline=(g_runtime_cycles>>1)+34;
    nds_reschedule_slice(g_div_deadline);
}
void io_mutate(const std::string& name) {
    if (name=="irq") { g_ime[0]=1; g_ie[0]=1; g_if[0]=1; g_nds_irq_pending_cache[0]=1; }
    else if (name=="device") g_timer[0][0].ctrl=128;
    else if (name=="divider") g_div_numer[1]^=1;
    else if (name=="save") g_cart_backup.sram.at(1)^=1;
    else task_aw2::require(false,"unknown IO mutation");
}
}
