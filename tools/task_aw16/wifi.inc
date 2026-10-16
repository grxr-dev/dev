namespace task_aw16 {
void wifi_aux(Snapshot& out) {
    out.put("wifi.network_enabled",1,g_network_config.enabled);
    out.put("wifi.bridge",1,bool(g_bridge));
    out.put("wifi.device",1,g_bridge && bool(g_bridge->wifi));
    out.put("wifi.worker",1,g_bridge && g_bridge->worker_thread!=nullptr);
    out.put("wifi.scheduled",1,g_bridge && g_bridge->nds.HasPendingEvent());
    out.put("wifi.raw_deadline",8,g_bridge ? g_bridge->nds.PendingEventTime() : 0);
    out.put("wifi.timestamp",8,g_bridge ? g_bridge->nds.CurrentSystemTimestamp : 0);
}
}
