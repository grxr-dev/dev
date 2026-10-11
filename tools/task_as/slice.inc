// Fixed AP certificate execution only; no injected guest register/state mutations.
template<class CPU> inline int aq_control(CPU& cpu){
    require(aq_armed&&!aq_pending&&aq_index<=45,"AQ exact observation budget");
    const unsigned flags[4]={unsigned(cpu.cpsr.n),unsigned(cpu.cpsr.z),unsigned(cpu.cpsr.c),unsigned(cpu.cpsr.v)};
    require(as_aq_replay_fixed::state(aq_index,cpu.R,flags,word(cpu.R[15]),g_insn_count[0])&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AQ full CPU/opcode/ordered path");
    require(g_insn_count[1]==96026779&&aq_reads==as_aq_replay_fixed::read_count(aq_index)&&aq_writes==as_aq_replay_fixed::write_count(aq_index),"AQ read/write/scheduler instruction budget");
    const auto ram=diagnostics::mainram_snapshot(),dtcm=read(0x027e0000,0x4000);
    require(ram==aq_expected_ram&&dtcm==aq_dtcm&&save_snapshot()==decision_flash,"AQ complete memory/save firewall");
    registers("aq_step",cpu);
    if(aq_index==45){
        require(cpu.R[15]==0x02026044&&aq_reads==51&&aq_writes==18&&!as_aq_replay_fixed::dispatch(aq_index),"AQ forbidden BL not dispatched");
        require(g_runtime_cycles==3416875664ull&&scheduler_cpu_cycles(1)==1708437825ull,"AS authoritative AQ cycles");
        require(hash(ram)=="84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340"&&hash(dtcm)=="1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716"&&hash(save_snapshot())=="a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb","AS complete AQ entry images");
        for(unsigned k=0;k<12;++k)require(word(as_fixed::r[k][15])==as_fixed::opcode[k],"AS every AR word before arming");
        for(const auto& w:as_fixed::writes)require(word(w.address)==w.before,"AS all AR DTCM before words");
        for(const auto& q:as_fixed::reads)require(word(q.address)==q.value,"AS all AR code/literal/data identities");
        registers("as_before",cpu);sample("as_before_sample");file("as-before-mainram.bin",ram);file("as-before-dtcm.bin",dtcm);file("as-before.sav",save_snapshot());
        as_ram=ram;as_dtcm=dtcm;as_expected_dtcm=dtcm;aq_armed=false;as_armed=true;return as_control(cpu);
    }
    require(as_aq_replay_fixed::dispatch(aq_index),"AQ instruction dispatch budget");aq_bus_index=aq_index;++aq_index;return 0;
}
