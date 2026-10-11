// Fixed AR certificate execution only; no injected guest register/state mutations.
template<class CPU> inline int as_control(CPU& cpu){
    require(as_armed&&!as_pending&&as_index<=11,"AS exact observation budget");
    const unsigned flags[4]={unsigned(cpu.cpsr.n),unsigned(cpu.cpsr.z),unsigned(cpu.cpsr.c),unsigned(cpu.cpsr.v)};
    require(au_as_replay_fixed::state(as_index,cpu.R,flags,word(cpu.R[15]),g_insn_count[0])&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AS full CPU/opcode/ordered path");
    require(g_insn_count[1]==96026779&&as_reads==au_as_replay_fixed::read_count(as_index)&&as_writes==au_as_replay_fixed::write_count(as_index),"AS read/write/scheduler instruction budget");
    const auto ram=diagnostics::mainram_snapshot(),dtcm=read(0x027e0000,0x4000);
    require(ram==as_ram&&dtcm==as_expected_dtcm&&save_snapshot()==decision_flash,"AS complete memory/save firewall");
    registers("as_step",cpu);
    if(as_index==11){
        require(cpu.R[15]==0x02067564&&as_reads==16&&as_writes==10&&!au_as_replay_fixed::dispatch(as_index),"AS forbidden BL not dispatched");
        require(g_runtime_cycles==3416875700ull&&scheduler_cpu_cycles(1)==1708437825ull,"AU exact AS cycle checkpoint");
        require(hash(ram)=="84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340"&&hash(dtcm)=="48b89027a274b3268219cdc6a8cd1f7fe15bf442a78b3931d79c4e6ae3ea36e4"&&hash(save_snapshot())=="a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb","AU full AS images");
        for(unsigned k=0;k<8;++k)require(word(au_fixed::r[k][15])==au_fixed::opcode[k],"AU all certified code words");
        for(const auto& w:au_fixed::writes)require(word(w.address)==w.before,"AU DTCM before word");
        for(const auto& q:au_fixed::reads)require(word(q.address)==q.value,"AU exact code/literal values");
        registers("au_before",cpu);sample("au_before_sample");file("au-before-mainram.bin",ram);file("au-before-dtcm.bin",dtcm);file("au-before.sav",save_snapshot());
        au_ram=ram;au_dtcm=dtcm;au_expected_dtcm=dtcm;as_armed=false;au_armed=true;return au_control(cpu);
    }
    require(au_as_replay_fixed::dispatch(as_index),"AS instruction dispatch budget");as_bus_index=as_index;++as_index;return 0;
}
