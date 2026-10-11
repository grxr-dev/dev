// Included inside the Task AH namespace after read/log/sample declarations.
// Fixed expected control flow only: no caller-supplied targets or register writes.
inline bool decision_active=false;
inline size_t decision_index=0;
inline unsigned comparison_entries=0;
inline uint32_t decision_sp=0,decision_mode=0;
inline uint64_t decision_ordinal=0,decision_insn7=0;
inline std::vector<uint8_t> outer_ram,outer_dtcm;
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
    require(task_ah_guard::permits(decision_index,pc,g_insn_count[0]-decision_ordinal),"unexpected decision PC / forbidden entry");
    require(!cpu.cpsr.t&&cpu.cpsr.mode==decision_mode&&(decision_index<49?cpu.R[0]==exercise_address:cpu.R[8]==exercise_address),"decision CPU context");
    require(g_insn_count[0]-decision_ordinal==decision_index&&decision_index<65&&g_insn_count[1]==decision_insn7,"decision instruction budget / scheduler isolation");
    require(word(0x020da464)==0x11&&word(0x020da3ec)==0x11&&word(0x020da3f0)==0x11,"scene identity");
    require(read(manager_address,0x238)==manager_before&&read(slot_address,0x370)==decision_slot,"manager / active slot mutation");
    auto ex=read(exercise_address,0xc34);
    for(unsigned i=0;i<ex.size();++i)if(i!=0x514&&!(decision_index>=44&&i==0x504)&&!(decision_index>=43&&i==0x20))require(ex[i]==exercise_before[i],"acceptance / other exercise field changed");
    const bool submitted=decision_index>18;
    require(word(exercise_address+0x504)==(decision_index>=44?1u:0u),"second store order");
    require(word(exercise_address+0x20)==(decision_index>=43?1u:0u),"first acceptance store order");
    require(word(exercise_address+0x514)==(submitted?4u:255u),"submitted digit staging order");
    auto current=diagnostics::mainram_snapshot();
    for(unsigned i=0;i<current.size();++i){const auto address=0x02000000u+i;
        if(address==exercise_address+0x514||(decision_index>=44&&address==exercise_address+0x504)||(decision_index>=43&&address==exercise_address+0x20)||(address>=decision_sp-20&&address<decision_sp))continue;
        require(current[i]==decision_ram[i],"unexpected RAM change outside input digit / call stack");
    }
    auto dtcm=read(0x027e0000,0x4000);
    for(unsigned i=0;i<dtcm.size();++i){const auto address=0x027e0000u+i;
        if(address>=decision_sp-20&&address<decision_sp)continue;
        if(decision_index>=57&&address>=0x027e3b2cu&&address<0x027e3b34u){require(dtcm[i]==task_ah_guard::pushed_byte(address),"only exact outer PUSH bytes allowed");continue;}
        require(dtcm[i]==decision_dtcm[i],"unexpected DTCM change outside pushed registers");
    }
    require(save_snapshot()==decision_flash,"Flash mutation");
    if(pc==0x02025778){++correctness_entries;require(correctness_entries==1&&cpu.R[2]==4&&cpu.R[14]==0x020266b8,"consumer entry ABI");}
    if(pc==0x02025698){++comparison_entries;require(comparison_entries==1&&cpu.R[4]==1&&cpu.R[5]==exercise_address&&cpu.R[13]==0x027e3b14&&cpu.R[14]==0x02025830,"sole authorized comparison helper entry");}
    if(pc==0x02025728)require(cpu.R[1]==4&&cpu.R[2]==4&&cpu.R[3]==0&&cpu.R[5]==4,"original units comparison operands");
    if(pc==0x0202572c||pc==0x02025730||pc==0x02025734||pc==0x02025738||pc==0x0202573c||pc==0x02025740||pc==0x02025744)require(task_ah_guard::correct(cpu.cpsr.n,cpu.cpsr.z,cpu.cpsr.c,cpu.cpsr.v,cpu.R[3]),"unexpected incorrect predicate");
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
        require(decision_index==43&&task_ah_guard::bounded_second_store(opcode,cpu.R[0],cpu.R[1],cpu.cpsr.z),"live fixed instruction/operand decode");
        require(((opcode>>25)&7u)==2&&((opcode>>24)&1u)==1&&((opcode>>23)&1u)==1&&((opcode>>20)&7u)==0&&rn==0&&rd==1,"word store, pre-index positive immediate, no writeback");
        const auto target=cpu.R[rn]+offset;
        require(target==exercise_address+0x504&&target==0x020e9f04u&&word(target)==0&&word(exercise_address+0x20)==1,"bounded RAM destination / AA pre-state");
        require(cpu.R[13]==decision_sp-24&&word(pc+4)==0x028dd004u,"exact pre-state / successor identity");
        file("second-store-before-mainram.bin",current);file("second-store-before-dtcm.bin",dtcm);file("second-store-before.sav",save_snapshot());
        registers("second_store_before",cpu);sample("second_store_before_sample");
        log("{\"event\":\"second_store_identified\",\"pc\":"+std::to_string(pc)+",\"opcode\":"+std::to_string(opcode)+",\"condition\":\"EQ\",\"decoded\":\"STREQ r1,[r0,#0x504]\",\"source_register\":"+std::to_string(rd)+",\"source_value\":"+std::to_string(cpu.R[rd])+",\"target\":"+std::to_string(target)+",\"before\":0,\"width\":4,\"successor\":"+std::to_string(pc+4)+"}");
    }
    if(pc==0x02025740){
        const uint32_t opcode=word(pc),rn=(opcode>>16)&15u,rd=(opcode>>12)&15u,imm=opcode&255u,rotate=((opcode>>8)&15u)*2u;
        require(decision_index==44&&task_ah_guard::bounded_stack_adjust(opcode,cpu.R[13],cpu.cpsr.z),"live fixed stack-adjust decode/operand");
        require(((opcode>>25)&7u)==1&&((opcode>>21)&15u)==4&&((opcode>>20)&1u)==0&&rn==13&&rd==13&&imm==4&&rotate==0,"immediate ADD SP,SP,4 without flag update");
        require(word(pc+4)==0x08bd8030u&&cpu.R[14]==0,"exact successor POP / preserved LR pre-state");
        file("stack-adjust-before-mainram.bin",current);file("stack-adjust-before-dtcm.bin",dtcm);file("stack-adjust-before.sav",save_snapshot());
        registers("stack_adjust_before",cpu);sample("stack_adjust_before_sample");
        log("{\"event\":\"stack_adjust_identified\",\"pc\":"+std::to_string(pc)+",\"opcode\":"+std::to_string(opcode)+",\"condition\":\"EQ\",\"decoded\":\"ADDEQ sp,sp,#4\",\"source_register\":"+std::to_string(rn)+",\"destination_register\":"+std::to_string(rd)+",\"source_value\":"+std::to_string(cpu.R[rn])+",\"immediate\":4,\"expected_value\":"+std::to_string(cpu.R[rn]+4)+",\"memory_write\":false,\"branch_or_call\":false,\"lr\":"+std::to_string(cpu.R[14])+",\"successor\":"+std::to_string(pc+4)+"}");
    }
    if(pc==0x02025744){
        const uint32_t opcode=word(pc),sp=cpu.R[13];
        require(decision_index==45&&cpu.R[4]==10&&cpu.R[5]==4&&cpu.R[14]==0,"Task AC exact pre-POP registers");
        require(task_ah_guard::bounded_pop(opcode,sp,cpu.cpsr.z,word(sp),word(sp+4),word(sp+8)),"fixed POP stack/condition/decode");
        require(((opcode>>25)&7u)==4&&((opcode>>20)&31u)==11&&((opcode>>16)&15u)==13&&(opcode&65535u)==0x8030u,"LDMIA SP writeback, S clear, fixed register list");
        require(word(0x0202582c)==0xebffff99u&&word(0x02025698)==0xe92d4030u&&word(0x02025830)==0xe8bd8010u,"original BL/PUSH provenance and return-site identity");
        file("pop-before-mainram.bin",current);file("pop-before-dtcm.bin",dtcm);file("pop-before.sav",save_snapshot());
        registers("pop_before",cpu);sample("pop_before_sample");
        log("{\"event\":\"instruction_identified\",\"pc\":"+std::to_string(pc)+",\"opcode\":"+std::to_string(opcode)+",\"decoded\":\"POPEQ {r4,r5,pc} / LDMEQIA sp!,{r4,r5,pc}\",\"condition\":\"EQ\",\"register_list\":[4,5,15],\"sp_before\":"+std::to_string(sp)+",\"stack_reads\":[{\"address\":"+std::to_string(sp)+",\"value\":1,\"register\":4},{\"address\":"+std::to_string(sp+4)+",\"value\":"+std::to_string(exercise_address)+",\"register\":5},{\"address\":"+std::to_string(sp+8)+",\"value\":33708080,\"register\":15}],\"sp_after\":"+std::to_string(sp+12)+",\"expected_target\":33708080,\"lr\":0,\"memory_write\":false}");
    }
    if(decision_index>=46&&decision_index<56){
        require(task_ah_guard::slice_opcode(decision_index,word(pc)),"fixed caller-slice opcode identity");
        if(decision_index==46){
            require(cpu.R[13]==0x027e3b14&&word(0x027e3b14)==1&&word(0x027e3b18)==0x020266b8u,"outer consumer return words");
            file("slice-before-mainram.bin",current);file("slice-before-dtcm.bin",dtcm);file("slice-before.sav",save_snapshot());registers("slice_before",cpu);sample("slice_before_sample");
        }
        if(decision_index==50)require(cpu.R[13]==0x027e3b24&&word(0x027e3b24)==3&&word(0x027e3b28)==0&&word(0x027e3b2c)==114&&word(0x027e3b30)==0x02026988u,"publication return stack identity");
        if(decision_index==51)require(cpu.R[8]==exercise_address&&(word(exercise_address+0x10)&65535u)==1,"bounded phase RAM read");
        if(decision_index==53)require(cpu.R[0]==1&&cpu.cpsr.n&&!cpu.cpsr.z&&!cpu.cpsr.c&&!cpu.cpsr.v,"phase-one BNE predicate");
    }
    if(decision_index>=55){
        require(task_ah_guard::outer_opcode(decision_index,word(pc)),"AF fixed outer instruction word");
        for(unsigned reg=0;reg<16;++reg)require(task_ah_guard::outer_register(decision_index,reg,cpu.R[reg]),"AF exact architectural register state");
        require(cpu.cpsr.n&&!cpu.cpsr.z&&!cpu.cpsr.c&&!cpu.cpsr.v&&!cpu.cpsr.t&&cpu.cpsr.mode==31&&!cpu.cpsr.i&&!cpu.cpsr.f,"AF exact full flags/mode/masks");
        if(decision_index==55){
            require(hash(current)=="b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9"&&hash(dtcm)=="e2ab6955f9cfa7e43239c75a004e386609c55a282d291c6a286ea97954e062ff","live complete AE RAM/DTCM identity");
            for(size_t k=0;k<10;++k)require(word(task_ah_guard::decision_path[55+k])==task_ah_guard::outer_opcodes[k],"all AF words verified before outer BL");
            require((word(exercise_address+0x10)&65535u)==1&&word(exercise_address+0x20)==1&&word(exercise_address+0x504)==1&&word(exercise_address+0x44)==1&&word(exercise_address+0x34)==0xdau,"AE mapped start fields");
            outer_ram=current;outer_dtcm=dtcm;
            file("outer-before-mainram.bin",current);file("outer-before-dtcm.bin",dtcm);file("outer-before.sav",save_snapshot());registers("outer_before",cpu);sample("outer_before_sample");
        }
        require(current==outer_ram,"AG main RAM must never change");
        for(unsigned i=0;i<dtcm.size();++i){const uint32_t address=0x027e0000u+i;const auto expected=(decision_index>=57&&address>=0x027e3b2cu&&address<0x027e3b34u)?task_ah_guard::pushed_byte(address):outer_dtcm[i];require(dtcm[i]==expected,"AG exact DTCM PUSH footprint only");}
    }
    if(pc==0x0202624c){
        require(decision_index==63&&g_insn_count[0]==281097897&&g_insn_count[1]==96026779,"AH authoritative AG ordinal gate");
        require(hash(current)=="b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9"&&hash(dtcm)=="ffebd1000bf8222fd3b1224bfed4f6596f4288e38b82d6c22b1aa6c14bc37547","AH complete authoritative AG RAM/DTCM gate");
        require(hash(save_snapshot())=="a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb","AH AG save identity");
        file("ah-before-mainram.bin",current);file("ah-before-dtcm.bin",dtcm);file("ah-before.sav",save_snapshot());registers("ah_before",cpu);sample("ah_before_sample");
        require(!ah_armed&&ah_writes==0,"AH single arming");ah_armed=true;
    }
    if(pc==0x02026250){
        require(ah_armed&&ah_writes==1,"AH exactly one actual interpreter write event");ah_armed=false;
        require(correctness_entries==1&&comparison_entries==1&&decision_index==64&&cpu.R[0]==0xda&&cpu.R[4]==exercise_address&&cpu.R[13]==0x027e3b2c&&cpu.R[14]==0x02026b94&&word(pc)==0xe1a00004u,"AH terminal MOV never dispatched");
        file("decision-after-mainram.bin",current);file("decision-after-dtcm.bin",dtcm);file("decision-after-stack.bin",read(decision_sp-64,128));file("decision-after.sav",save_snapshot());
        file("exercise-decision.bin",ex);file("manager-decision.bin",read(manager_address,0x238));file("slot-decision.bin",read(slot_address,0x370));
        log("{\"event\":\"decision_stopped\",\"correct\":true,\"accepted\":false,\"correctness_entries\":1,\"comparison_entries\":1,\"forbidden_entries\":0,\"acceptance_stores_executed\":2,\"progression_entries\":0,\"save_entries\":0,\"instructions\":"+std::to_string(decision_index)+"}");
        require(!task_ah_guard::dispatches(decision_index,pc,g_insn_count[0]-decision_ordinal),"terminal PC must never dispatch");
        sample("decision_stop_sample");done=true;finish(0);return 2;
    }
    require(task_ah_guard::dispatches(decision_index,pc,g_insn_count[0]-decision_ordinal),"instruction not in dispatch allowlist");
    ++decision_index;return 0;
}
