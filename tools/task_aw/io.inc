
namespace task_aw {
void io_snapshot(Snapshot& out) {
    NdsIoCoreSaveState core{};
    io_savestate_export(&core);
    out.copy("io",core);
    out.values["divcnt"]=g_divcnt;
    out.values["div_deadline"]=g_div_deadline;
    out.values["divider_event_identity"]=g_div_deadline;
    out.copy("numerator",g_div_numer);
    out.copy("denominator",g_div_denom);
    out.copy("quotient",g_div_quot);
    out.copy("remainder",g_div_rem);
    out.values["card_deadline"]=g_card_deadline;
    out.values["spi_deadline"]=g_spi_deadline;
    out.values["auxspi_deadline"]=g_auxspi_deadline;
    out.values["sqrt_deadline"]=g_sqrt_deadline;
    out.values["irq9_ready"]=(g_ime[0]&1u)&&(g_ie[0]&g_if[0]);
    out.values["irq7_ready"]=(g_ime[1]&1u)&&(g_ie[1]&g_if[1]);
    out.values["gpu_stall"]=g_gxfifo_stall;
    const uint8_t* save=nullptr;
    uint32_t size=0;
    bool dirty=false;
    if (nds_io_cartridge_save_snapshot(&save,&size,&dirty))
        out.bytes["save"]=std::vector<uint8_t>(save,save+size);
    out.values["save_dirty"]=dirty;
}
}
