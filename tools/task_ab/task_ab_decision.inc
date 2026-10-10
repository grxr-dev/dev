// Included inside the Task AB namespace after read/log/sample declarations.
// Fixed expected control flow only: no caller-supplied targets or register writes.
inline bool decision_active=false;
inline size_t decision_index=0;
inline unsigned comparison_entries=0;
inline uint32_t decision_sp=0,decision_mode=0;
inline uint64_t decision_ordinal=0,decision_insn7=0;
inline std::vector<uint8_t> decision_ram,decision_slot,decision_stack,decision_flash,decision_dtcm;
template<class CPU> inline void registers(const char* event,const CPU& cpu){
    std::string values="[";for(unsigned i=0;i<16;++i){if(i)values+=",";values+=std::to_string(cpu.R[i]);}values+="]";
    log("{\"event\":\""+std::string(event)+"\",\"pc\":"+std::to_string(cpu.R[15])+",\"opcode\":"+std::to_string(word(cpu.R[15]))+",\"r\":"+values+",\"n\":"+std::to_string(cpu.cpsr.n)+",\"z\":"+std::to_string(cpu.cpsr.z)+",\"c\":"+std::to_string(cpu.cpsr.c)+",\"v\":"+std::to_string(cpu.cpsr.v)+",\"t\":"+std::to_string(cpu.cpsr.t)+",\"mode\":"+std::to_string(cpu.cpsr.mode)+",\"i\":"+std::to_string(cpu.cpsr.i)+",\"f\":"+std::to_string(cpu.cpsr.f)+",\"insn9\":"+std::to_string(g_insn_count[0])+"}");
}
inline std::vector<uint8_t> save_snapshot(){
    const uint8_t* bytes=nullptr;uint32_t size=0;bool dirty=false;
    require(nds_io_cartridge_save_snapshot(&bytes,&size,&dirty)&&size==262144&&!dirty,"unchanged clean Flash required");
    return std::vector<uint8_t>(bytes,bytes+size);
}
template<class CPU> inline void begin_decision(const CPU& cpu){
    require(!decision_active&&decision_index==0&&correctness_entries==0,"exactly one correctness invocation");
    require(hash(read(0x02025698,0x1a4))=="9bb82d605ddda2fea32e5fe4bce42338cb1aec9d3d168609f0d553d92d7716e3","consumer/comparator code identity");
    require(word(0x020266b4)==0xebfffc2fu,"original correctness call opcode");
    require(selected.integer==4&&word(exercise_address+0x4c)==4,"recognized and expected 4");
    require(word(exercise_address+0x20)==0&&word(exercise_address+0x38)==0&&word(exercise_address+0x504)==0&&word(exercise_address+0x50c)==255&&word(exercise_address+0x514)==255,"no pending result before call");
    decision_sp=cpu.R[13];decision_mode=cpu.cpsr.mode;
    require(decision_sp==0x027e3b1c,"exact checkpoint DTCM stack");
    require(decision_sp-64>slot_address+0x370,"stack disjoint from audited objects");
    decision_ram=diagnostics::mainram_snapshot();decision_slot=read(slot_address,0x370);decision_stack=read(decision_sp-64,128);decision_flash=save_snapshot();decision_dtcm=read(0x027e0000,0x4000);file("decision-before-dtcm.bin",decision_dtcm);
    file("decision-before-mainram.bin",decision_ram);file("decision-before-stack.bin",decision_stack);file("decision-before.sav",decision_flash);
    decision_ordinal=g_insn_count[0];decision_insn7=g_insn_count[1];
    registers("decision_before",cpu);sample("decision_before_sample");decision_active=true;
}
template<class CPU> inline int decision_control(CPU& cpu){
    const auto pc=cpu.R[15];
    // The stop PC is included but never dispatched. Any divergent PC fails before dispatch,
    // including the successor instruction, wrong path, repeated entry, save, IRQ or progression.
    require(task_ab_guard::permits(decision_index,pc,g_insn_count[0]-decision_ordinal),"unexpected decision PC / forbidden entry");
    require(!cpu.cpsr.t&&cpu.cpsr.mode==decision_mode&&cpu.R[0]==exercise_address,"decision CPU context");
    require(g_insn_count[0]-decision_ordinal==decision_index&&decision_index<64&&g_insn_count[1]==decision_insn7,"decision instruction budget / scheduler isolation");
    require(word(0x020da464)==0x11&&word(0x020da3ec)==0x11&&word(0x020da3f0)==0x11,"scene identity");
    require(read(manager_address,0x238)==manager_before&&read(slot_address,0x370)==decision_slot,"manager / active slot mutation");
    auto ex=read(exercise_address,0xc34);
    for(unsigned i=0;i<ex.size();++i)if(i!=0x514&&!(decision_index==44&&i==0x504)&&!(decision_index>=43&&i==0x20))require(ex[i]==exercise_before[i],"acceptance / other exercise field changed");
    const bool submitted=decision_index>18;
    require(word(exercise_address+0x504)==(decision_index==44?1u:0u),"second store order");
    require(word(exercise_address+0x20)==(decision_index>=43?1u:0u),"first acceptance store order");
    require(word(exercise_address+0x514)==(submitted?4u:255u),"submitted digit staging order");
    auto current=diagnostics::mainram_snapshot();
    for(unsigned i=0;i<current.size();++i){const auto address=0x02000000u+i;
        if(address==exercise_address+0x514||(decision_index==44&&address==exercise_address+0x504)||(decision_index>=43&&address==exercise_address+0x20)||(address>=decision_sp-20&&address<decision_sp))continue;
        require(current[i]==decision_ram[i],"unexpected RAM change outside input digit / call stack");
    }
    auto dtcm=read(0x027e0000,0x4000);
    for(unsigned i=0;i<dtcm.size();++i){const auto address=0x027e0000u+i;
        if(address>=decision_sp-20&&address<decision_sp)continue;
        require(dtcm[i]==decision_dtcm[i],"unexpected DTCM change outside pushed registers");
    }
    require(save_snapshot()==decision_flash,"Flash mutation");
    if(pc==0x02025778){++correctness_entries;require(correctness_entries==1&&cpu.R[2]==4&&cpu.R[14]==0x020266b8,"consumer entry ABI");}
    if(pc==0x02025698){++comparison_entries;require(comparison_entries==1&&cpu.R[14]==0x02025830,"sole authorized comparison helper entry");}
    if(pc==0x02025728)require(cpu.R[1]==4&&cpu.R[2]==4&&cpu.R[3]==0&&cpu.R[5]==4,"original units comparison operands");
    if(pc==0x0202572c||pc==0x02025730||pc==0x02025734||pc==0x02025738||pc==0x0202573c||pc==0x02025740)require(task_ab_guard::correct(cpu.cpsr.n,cpu.cpsr.z,cpu.cpsr.c,cpu.cpsr.v,cpu.R[3]),"unexpected incorrect predicate");
    registers("decision_step",cpu);
    if(pc==0x02025734){
        require(decision_index==41&&cpu.R[1]==4&&cpu.R[2]==4&&cpu.R[5]==4&&word(pc)==0x03a01001u,"Task Z correct boundary parity");
    }
    if(pc==0x02025738){
        require(decision_index==42&&cpu.R[1]==1&&word(pc)==0x05801020u&&word(exercise_address+0x20)==0,"sole allowed STREQ ABI/opcode");
        file("first-store-before-mainram.bin",current);file("first-store-before-dtcm.bin",dtcm);
        log("{\"event\":\"first_store_armed\",\"pc\":33707832,\"delay_before\":0,\"flag_before\":0}");
    }
    if(pc==0x0202573c){
        const uint32_t opcode=word(pc),rn=(opcode>>16)&15u,rd=(opcode>>12)&15u,offset=opcode&4095u;
        require(decision_index==43&&task_ab_guard::bounded_second_store(opcode,cpu.R[0],cpu.R[1],cpu.cpsr.z),"live fixed instruction/operand decode");
        require(((opcode>>25)&7u)==2&&((opcode>>24)&1u)==1&&((opcode>>23)&1u)==1&&((opcode>>20)&7u)==0&&rn==0&&rd==1,"word store, pre-index positive immediate, no writeback");
        const auto target=cpu.R[rn]+offset;
        require(target==exercise_address+0x504&&target==0x020e9f04u&&word(target)==0&&word(exercise_address+0x20)==1,"bounded RAM destination / AA pre-state");
        require(cpu.R[13]==decision_sp-24&&word(pc+4)==0x028dd004u,"exact pre-state / successor identity");
        file("second-store-before-mainram.bin",current);file("second-store-before-dtcm.bin",dtcm);file("second-store-before.sav",save_snapshot());
        registers("second_store_before",cpu);sample("second_store_before_sample");
        log("{\"event\":\"instruction_identified\",\"pc\":"+std::to_string(pc)+",\"opcode\":"+std::to_string(opcode)+",\"condition\":\"EQ\",\"decoded\":\"STREQ r1,[r0,#0x504]\",\"source_register\":"+std::to_string(rd)+",\"source_value\":"+std::to_string(cpu.R[rd])+",\"target\":"+std::to_string(target)+",\"before\":0,\"width\":4,\"successor\":"+std::to_string(pc+4)+"}");
    }
    if(pc==0x02025740){
        require(correctness_entries==1&&comparison_entries==1&&decision_index==44&&cpu.R[1]==1&&cpu.R[2]==4&&cpu.R[5]==4&&cpu.R[13]==decision_sp-24&&word(pc)==0x028dd004u,"second store complete; successor not dispatched");
        file("decision-after-mainram.bin",current);file("decision-after-dtcm.bin",dtcm);file("decision-after-stack.bin",read(decision_sp-64,128));file("decision-after.sav",save_snapshot());
        file("exercise-decision.bin",ex);file("manager-decision.bin",read(manager_address,0x238));file("slot-decision.bin",read(slot_address,0x370));
        log("{\"event\":\"decision_stopped\",\"correct\":true,\"accepted\":false,\"correctness_entries\":1,\"comparison_entries\":1,\"forbidden_entries\":0,\"acceptance_stores_executed\":2,\"progression_entries\":0,\"save_entries\":0,\"instructions\":"+std::to_string(decision_index)+"}");
        require(!task_ab_guard::dispatches(decision_index,pc,g_insn_count[0]-decision_ordinal),"terminal PC must never dispatch");
        sample("decision_stop_sample");done=true;finish(0);return 2;
    }
    require(task_ab_guard::dispatches(decision_index,pc,g_insn_count[0]-decision_ordinal),"instruction not in dispatch allowlist");
    ++decision_index;return 0;
}
