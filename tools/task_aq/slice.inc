// Fixed AP certificate execution only; no injected guest register/state mutations.
template<class CPU> inline int aq_control(CPU& cpu){
    require(aq_armed&&!aq_pending&&aq_index<=45,"AQ exact observation budget");
    const unsigned flags[4]={unsigned(cpu.cpsr.n),unsigned(cpu.cpsr.z),unsigned(cpu.cpsr.c),unsigned(cpu.cpsr.v)};
    require(aq_fixed::state(aq_index,cpu.R,flags,word(cpu.R[15]),g_insn_count[0])&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AQ full CPU/opcode/ordered path");
    require(g_insn_count[1]==96026779&&aq_reads==aq_fixed::read_count(aq_index)&&aq_writes==aq_fixed::write_count(aq_index),"AQ read/write/scheduler instruction budget");
    const auto ram=diagnostics::mainram_snapshot(),dtcm=read(0x027e0000,0x4000);
    require(ram==aq_expected_ram&&dtcm==aq_dtcm&&save_snapshot()==decision_flash,"AQ complete memory/save firewall");
    registers("aq_step",cpu);
    if(aq_index==45){
        require(cpu.R[15]==0x02026044&&aq_reads==51&&aq_writes==18&&!aq_fixed::dispatch(aq_index),"AQ forbidden BL not dispatched");
        file("decision-after-mainram.bin",ram);file("decision-after-dtcm.bin",dtcm);file("decision-after.sav",save_snapshot());sample("decision_stop_sample");
        log("{\"event\":\"decision_stopped\",\"aq_instructions\":45,\"aq_writes\":18,\"aq_reads\":51,\"successor_fetched\":false,\"successor_dispatched\":false}");done=true;finish(0);return 2;
    }
    require(aq_fixed::dispatch(aq_index),"AQ instruction dispatch budget");aq_bus_index=aq_index;++aq_index;return 0;
}
