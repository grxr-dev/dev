// Fixed AR certificate execution only; no injected guest register/state mutations.
template<class CPU> inline int as_control(CPU& cpu){
    require(as_armed&&!as_pending&&as_index<=11,"AS exact observation budget");
    const unsigned flags[4]={unsigned(cpu.cpsr.n),unsigned(cpu.cpsr.z),unsigned(cpu.cpsr.c),unsigned(cpu.cpsr.v)};
    require(as_fixed::state(as_index,cpu.R,flags,word(cpu.R[15]),g_insn_count[0])&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AS full CPU/opcode/ordered path");
    require(g_insn_count[1]==96026779&&as_reads==as_fixed::read_count(as_index)&&as_writes==as_fixed::write_count(as_index),"AS read/write/scheduler instruction budget");
    const auto ram=diagnostics::mainram_snapshot(),dtcm=read(0x027e0000,0x4000);
    require(ram==as_ram&&dtcm==as_expected_dtcm&&save_snapshot()==decision_flash,"AS complete memory/save firewall");
    registers("as_step",cpu);
    if(as_index==11){
        require(cpu.R[15]==0x02067564&&as_reads==16&&as_writes==10&&!as_fixed::dispatch(as_index),"AS forbidden BL not dispatched");
        file("decision-after-mainram.bin",ram);file("decision-after-dtcm.bin",dtcm);file("decision-after.sav",save_snapshot());sample("decision_stop_sample");
        log("{\"event\":\"decision_stopped\",\"as_instructions\":11,\"as_writes\":10,\"as_reads\":16,\"successor_fetched\":false,\"successor_dispatched\":false}");done=true;finish(0);return 2;
    }
    require(as_fixed::dispatch(as_index),"AS instruction dispatch budget");as_bus_index=as_index;++as_index;return 0;
}
