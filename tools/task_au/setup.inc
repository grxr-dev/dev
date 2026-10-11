// Fixed AT certificate execution only; no injected guest register/state mutations.
template<class CPU> inline int au_control(CPU& cpu){
    require(au_armed&&!au_pending&&au_index<=7,"AU exact observation budget");
    const unsigned flags[4]={unsigned(cpu.cpsr.n),unsigned(cpu.cpsr.z),unsigned(cpu.cpsr.c),unsigned(cpu.cpsr.v)};
    require(au_fixed::state(au_index,cpu.R,flags,word(cpu.R[15]),g_insn_count[0])&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AU full CPU/opcode/ordered path");
    require(g_insn_count[1]==96026779&&au_reads==au_fixed::read_count(au_index)&&au_writes==au_fixed::write_count(au_index),"AU read/write/scheduler instruction budget");
    const auto ram=diagnostics::mainram_snapshot(),dtcm=read(0x027e0000,0x4000);
    require(ram==au_ram&&dtcm==au_expected_dtcm&&save_snapshot()==decision_flash,"AU complete memory/save firewall");
    registers("au_step",cpu);
    if(au_index==7){
        require(cpu.R[15]==0x02001980&&au_reads==9&&au_writes==1&&!au_fixed::dispatch(au_index),"AU forbidden STRH not dispatched");
        file("decision-after-mainram.bin",ram);file("decision-after-dtcm.bin",dtcm);file("decision-after.sav",save_snapshot());sample("decision_stop_sample");
        log("{\"event\":\"decision_stopped\",\"au_instructions\":7,\"au_writes\":1,\"au_reads\":9,\"successor_fetched\":false,\"successor_dispatched\":false}");done=true;finish(0);return 2;
    }
    require(au_fixed::dispatch(au_index),"AU instruction dispatch budget");au_bus_index=au_index;++au_index;return 0;
}
