namespace task_aw16 {
void overlay_aux(Snapshot& out) {
    out.put("overlay.enabled",1,g_live.enabled);
}
}
