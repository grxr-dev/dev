
namespace task_aw {
void bus_snapshot(Snapshot& out) {
    out.bytes["ram"]=g_main_ram;
    out.bytes["dtcm"]=g_dtcm;
    out.copy("last_code_pc",g_last_code_pc);
    out.copy("last_data_addr",g_last_data_addr);
    out.copy("timing",g_arm9_code_timing);
    out.values["code_publication_generation"]=g_arm9_code_pub_gen;
    out.values["code_class_shift"]=g_arm9_code_class_shift;
}
}
