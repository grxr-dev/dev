#include "scheduler.cpp"
#include "fixture.h"
namespace task_aw4::fixture {
void scheduler_begin() {
    g_owner_thread=std::this_thread::get_id(); g_round_active=true; g_cur=0;
    g_sys_timestamp=(task_aw2::entry_cycle-9)>>1;
    g_slot[0].cycles=task_aw2::entry_cycle-9; g_slot[0].started=true;
    g_slot[1].cycles=task_aw2::au_manifest().get("cycle7"); g_slot[1].started=true;
    g_aw3_round_epoch=1; g_aw3_planned_target=task_aw2::entry_cycle+119;
    g_aw3_next_event=task_aw2::periodic_next(g_sys_timestamp);
}
void scheduler_mutate(const std::string& name) {
    if (name=="arm7") ++g_slot[1].cycles;
    else if (name=="event") g_aw3_next_event=g_sys_timestamp;
    else task_aw2::require(false,"unknown scheduler mutation");
}
}
