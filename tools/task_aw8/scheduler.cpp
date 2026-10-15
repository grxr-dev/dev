#include "binding.h"
#include "aw8_scheduler.cpp"
namespace task_aw8 {
void scheduler_begin() {
    const auto& saved=entry();
    g_owner_thread=std::this_thread::get_id(); g_round_active=saved.get("round_active"); g_cur=saved.get("current_slot");
    g_sys_timestamp=saved.get("system_timestamp");
    g_slot[0].cycles=saved.get("slot9.cycle"); g_slot[1].cycles=saved.get("cycle7");
    g_slot[0].deferred_cycles=saved.get("slot9.deferred"); g_slot[1].deferred_cycles=saved.get("deferred7");
    for (unsigned cpu=0;cpu<2;++cpu) {
        g_slot[cpu].started=saved.get(task_aw2::numbered("scheduler.started.",cpu));
        g_slot[cpu].halted=saved.get(task_aw2::numbered("scheduler.halted.",cpu));
    }
    g_aw3_round_epoch=saved.get("scheduler.round_epoch");
    g_aw3_planned_target=saved.get("scheduler.planned_target"); g_aw3_next_event=saved.get("scheduler.next_event");
}
void scheduler_mutate(const std::string& name) {
    if (name=="arm7") ++g_slot[1].deferred_cycles;
    else if (name=="event") g_aw3_next_event=g_sys_timestamp;
    else require(false,"unknown scheduler mutation");
}
}
