namespace task_aw16 {
void scheduler_aux(Snapshot& out) {
    out.put("scheduler.modulus",8,profile_modulus());
    out.put("scheduler.sample",1,g_sample_active);
}
}
