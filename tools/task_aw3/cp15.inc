namespace task_aw3 {
void cp15_snapshot(Snapshot& out) {
    out.put("cp15.control",4,g_cp15.control); out.put("cp15.generation",4,g_cp15_timing_generation);
    out.put("cp15.dcache",4,g_cache_cfg[0]); out.put("cp15.icache",4,g_cache_cfg[1]);
    for (unsigned index=0;index<8;++index) {
        out.put("cp15.region."+std::to_string(index),4,g_mpu_region[index]);
        out.put("hidden.permission."+std::to_string(index),4,g_access_perm[index]);
    }
    out.put("itcm.enabled",1,g_cp15.itcm_enable); out.put("itcm.base",4,0); out.put("itcm.size",8,g_cp15.itcm_size);
    out.put("dtcm_map.enabled",1,g_cp15.dtcm_enable); out.put("dtcm_map.base",4,g_cp15.dtcm_base);
    out.put("dtcm_map.size",8,g_cp15.dtcm_size);
}
}
