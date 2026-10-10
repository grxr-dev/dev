#pragma once
#include "task_z_guard.h"
#include "bc_host.h"
#include "bc_digit_entry.h"
#include "bc_calculations_policy.h"
namespace brainage_task_z {
using namespace brainage_custom;
inline bool entered=false,staged=false,done=false;
inline uint32_t exercise_address=0,manager_address=0,slot_address=0;
inline unsigned publication_entries=0,slot_reads=0,correctness_entries=0;

inline uint64_t start_ordinal=0;
inline CalculationsSelection selected;
inline std::vector<uint8_t> exercise_before,manager_before,slot_before;
inline const char* root(){return std::getenv("NDS_TASK_Z_OUT");}
inline void require(bool valid,const char* why){if(!valid)throw std::runtime_error(why);}
inline uint32_t word(uint32_t address){return peek_word(address);}
inline std::vector<uint8_t> read(uint32_t address,unsigned size){std::vector<uint8_t> bytes(size);for(unsigned index=0;index<size;++index)bytes[index]=bus_debug_read8(9,address+index);return bytes;}
inline std::string hash(const std::vector<uint8_t>& bytes){return resource_detail::sha256(bytes.data(),bytes.size());}
inline void file(const std::string& name,const std::vector<uint8_t>& bytes){
    FILE* output=std::fopen((std::string(root())+"/"+name).c_str(),"wb");require(output,"Task Z output open");
    const auto count=std::fwrite(bytes.data(),1,bytes.size(),output);std::fclose(output);require(count==bytes.size(),"Task Z output write");
}
inline void log(const std::string& line){FILE* output=std::fopen((std::string(root())+"/audit.jsonl").c_str(),"ab");require(output,"Task Z audit open");std::fprintf(output,"%s\n",line.c_str());std::fclose(output);}
inline void finish(int code){
    const uint8_t* bytes=nullptr;uint32_t size=0;bool dirty=false;
    require(nds_io_cartridge_save_snapshot(&bytes,&size,&dirty)&&size==262144,"final Flash snapshot");
    file("final.sav",std::vector<uint8_t>(bytes,bytes+size));
    log("{\"event\":\"disposable_exit\",\"code\":"+std::to_string(code)+",\"save_sha256\":\""+resource_detail::sha256(bytes,size)+"\",\"save_dirty\":"+(dirty?"true":"false")+"}");
    nds_halt(code==0?"Task Z disposable proof stopped before acceptance":"Task Z firewall failure");
}
inline std::string array(const std::vector<uint16_t>& values){std::string text="[";for(auto value:values){if(text.size()>1)text+=",";text+=std::to_string(value);}return text+"]";}
inline void sample(const char* event){
    const auto touch=nds_touch_observation();
    log("{\"event\":\""+std::string(event)+"\",\"pc\":"+std::to_string(g_cpu.R[15])+",\"cycle9\":"+std::to_string(g_runtime_cycles)+",\"cycle7\":"+std::to_string(scheduler_cpu_cycles(1))+",\"insn9\":"+std::to_string(g_insn_count[0])+",\"insn7\":"+std::to_string(g_insn_count[1])+",\"guest_deliveries\":"+std::to_string(touch.guest_deliveries)+",\"owner\":"+(touch.owned?"true":"false")+",\"down\":"+(touch.down?"true":"false")+",\"video_sha1\":\""+diagnostics::video_digest()+"\",\"flash_sha1\":\""+flash_digest()+"\",\"current\":"+std::to_string(word(0x020da464))+",\"requested\":"+std::to_string(word(0x020da3ec))+",\"selected\":"+std::to_string(word(0x020da3f0))+",\"presents\":"+std::to_string(frontend_hold_presents())+"}");
}
class RecognizedPolicy final:public DigitRecognizer {
    digit_detail::PrivateDigitRecognizer service;
    CalculationsPolicy policy;
    unsigned releases=0;
public:
    bool active() const override{return service.active();}
    DigitResult begin_session() override{return service.begin_session();}
    DigitResult end_session() override{return service.end_session();}
    DigitResult recognize_stroke(const decuma::Stroke& stroke) override{
        auto result=service.recognize_stroke(stroke);
        selected=policy.consume(result,int(word(exercise_address+0x4c)),++releases);
        require(selected.timing_supported,"unsupported publication timing");
        std::string text="{\"event\":\"recognition\",\"release\":"+std::to_string(releases)+",\"integer\":"+std::to_string(selected.integer)+",\"countdown_before_update\":"+std::to_string(selected.countdown)+",\"publishable_this_update\":"+(selected.countdown==1?"true":"false")+",\"primary\":"+array(selected.primary)+",\"secondary\":"+array(selected.secondary)+",\"chosen\":"+array(selected.chosen)+",\"metric\":"+std::to_string(result.metric)+",\"private_instructions\":"+std::to_string(result.instructions)+",\"wall_us\":"+std::to_string(result.wall_us)+",\"groups\":[";
        for(unsigned group=0;group<2;++group){const auto& value=result.groups[group];if(group)text+=",";text+="{\"count\":"+std::to_string(value.returned_count)+",\"codes\":"+array(std::vector<uint16_t>(value.codes.begin(),value.codes.begin()+value.code_count))+",\"secondary\":"+array(std::vector<uint16_t>(value.accessor_codes.begin(),value.accessor_codes.begin()+value.code_count))+"}";}
        log(text+"]}");sample("released_stroke");return result;
    }
};
struct Input {
    DigitEntryProbe* activity;
    Surface* surface;
    bool publish=false;
};
inline bool touch(void* context,uint16_t x,uint16_t y,bool down){
    auto& input=*static_cast<Input*>(context);const auto before=nds_touch_observation().guest_deliveries;
    const auto event=input.activity->touch(x,y,down);if(event.changed)input.activity->render(*input.surface);
    require(!event.request_exit,"Continue is not the Task Z publication trigger");
    input.publish=!down&&selected.timing_supported&&selected.countdown==1&&selected.integer!=0xffff;
    log("{\"event\":\"native_touch\",\"x\":"+std::to_string(x)+",\"y\":"+std::to_string(y)+",\"down\":"+(down?"true":"false")+",\"consumed\":true,\"guest_deliveries\":"+std::to_string(before)+"}");
    return true;
}
inline bool ram(uint32_t address,unsigned size){return address>=0x020d3218u&&address<0x02400000u&&size<=0x02400000u-address;}
inline void store(uint32_t address,uint32_t value){
    require(address==slot_address+0x320||address==slot_address+0x364,"only fixed publication fields may be staged");
    log("{\"event\":\"stage\",\"address\":"+std::to_string(address)+",\"before\":"+std::to_string(word(address))+",\"after\":"+std::to_string(value)+"}");
    for(unsigned index=0;index<4;++index)bus_write_u8_slow(address+index,uint8_t(value>>(8*index)));
    require(word(address)==value,"publication readback");
}
#include "task_z_decision.inc"
template<class CPU> inline int control(CPU& cpu){
    if(!root()||!*root()||done||g_nds_active!=NDS_ARM9)return 0;
    try{
        const auto pc=cpu.R[15];
        if(entered){
            if(decision_active)return decision_control(cpu);
            if(pc==0x02025778||pc==0x02025698||pc==0x020265f8||pc==0x0200de78||pc==0x02027a28||pc==0x020531c8||pc==0x02051a30){++correctness_entries;throw std::runtime_error("side-effect firewall reached forbidden entry");}
            require(g_insn_count[0]-start_ordinal<10000,"publication instruction bound");
            if(pc==0x02052424)++publication_entries;
            if(pc==0x020266ac)++slot_reads;
            if(pc==0x020266b4){
                require(staged&&publication_entries==1&&slot_reads==1,"original publication path count");
                require(cpu.R[0]==exercise_address&&cpu.R[1]==0&&cpu.R[2]==selected.integer&&word(slot_address+0x364)==0,"published integer/context mismatch");
                require(read(exercise_address,0xc34)==exercise_before&&read(manager_address,0x238)==manager_before,"problem or manager accepted answer");
                auto after=read(slot_address,0x370);for(unsigned index=0;index<after.size();++index)if(index<0x320||index>=0x324)require(after[index]==slot_before[index],"unexpected slot mutation");
                file("publication-mainram.bin",diagnostics::mainram_snapshot());file("exercise-after.bin",read(exercise_address,0xc34));file("manager-after.bin",read(manager_address,0x238));file("slot-after.bin",after);
                log("{\"event\":\"publication_blocked\",\"pc\":"+std::to_string(pc)+",\"integer\":"+std::to_string(cpu.R[2])+",\"slot\":"+std::to_string(slot_address)+",\"exercise\":"+std::to_string(exercise_address)+",\"manager\":"+std::to_string(manager_address)+",\"publication_entries\":"+std::to_string(publication_entries)+",\"slot_reads\":"+std::to_string(slot_reads)+",\"correctness_entries\":"+std::to_string(correctness_entries)+",\"exercise_equal\":true,\"manager_equal\":true}");
                sample("terminal_publication");begin_decision(cpu);return decision_control(cpu);
            }
            return 0;
        }
        if(pc!=0x0202668c||cpu.cpsr.t)return 0;
        require(identity_ok&&g_nds_force_tier3&&word(pc)==0xeb00af64u,"exact title/instruction/backend gate");
        exercise_address=cpu.R[5];manager_address=cpu.R[0];slot_address=word(manager_address+4);
        require(ram(exercise_address,0xc34)&&ram(manager_address,0x238)&&ram(slot_address,0x370),"problem allocation gate");
        require(word(exercise_address+0xc24)==manager_address&&word(exercise_address+0x4c)==4&&word(exercise_address+0x44)==1&&(word(exercise_address+0x10)&65535)==1,"preserved 11 - 7 problem gate");
        require(word(manager_address)==1&&word(manager_address+0x230)==0&&read(manager_address+0x234,1)[0]==0&&word(slot_address)==0&&word(slot_address+8)==0&&word(slot_address+0x218)==0&&word(slot_address+0x214)==0&&word(slot_address+0x31c)==2&&word(slot_address+0x224)==4&&word(slot_address+0x364)==0,"idle policy-2 slot gate");
        require(exercise_address==0x020e9a00&&manager_address==0x020fa808&&slot_address==0x020faa50,"exact Task Y objects");
        require(word(0x020da464)==0x11&&word(0x020da3ec)==0x11&&word(0x020da3f0)==0x11,"exact scene");
        require(hash(read(exercise_address,0xc34))=="fdca8f671499c5e6d759c915832815b94928dbe899f83a16eba37808b1ba5d5e","exact Task Y exercise");
        require(hash(read(manager_address,0x238))=="a95b2c77f8a822a80809f06aa3f9de9e72cd7b82b4af526c6eb13212add2cbf8","exact Task Y manager");
        require(hash(read(slot_address,0x370))=="7a228568f985a7cbd84c35a794765e34a0faa72eccd0b16922f67c9ad8533c50","exact Task Y slot");
        exercise_before=read(exercise_address,0xc34);manager_before=read(manager_address,0x238);slot_before=read(slot_address,0x370);
        file("exercise-before.bin",exercise_before);file("manager-before.bin",manager_before);file("slot-before.bin",slot_before);
        sample("entry");file("disabled-entry-mainram.bin",diagnostics::mainram_snapshot());
        const auto* enable=std::getenv("NDS_TASK_Z_PUBLICATION");
        if(!enable||std::strcmp(enable,"1")){log("{\"event\":\"disabled_control\",\"custom_publication\":false}");file("disabled-stop-mainram.bin",diagnostics::mainram_snapshot());done=true;finish(0);return 2;}
        entered=true;start_ordinal=g_insn_count[0];
        auto ram_before=diagnostics::mainram_snapshot();file("hold-mainram.bin",ram_before);const auto cpu_before=g_cpu;const auto interpreter_before=cpu;
        const auto cycles9=g_runtime_cycles,cycles7=scheduler_cpu_cycles(1),ordinal9=g_insn_count[0],ordinal7=g_insn_count[1];
        const auto video_before=diagnostics::video_digest(),flash_before=flash_digest();const auto deliveries=nds_touch_observation().guest_deliveries;
        require(!nds_touch_observation().down&&!nds_touch_observation().owned&&!nds_gpu2d_bottom_presentation_owned(),"clean ownership gate");
        RecognizedPolicy recognizer;ExerciseServices services{&recognizer};
        {
            DigitEntryProbe activity(services);activity.begin();Surface surface;activity.render(surface);Input input{&activity,&surface,false};
            struct Owners {~Owners(){nds_set_touch_owner(nullptr,nullptr);nds_gpu2d_set_bottom_presentation(nullptr);}} owners;
            nds_gpu2d_set_bottom_presentation(surface.pixels.data());nds_set_touch_owner(touch,&input);sample("panel_active");
            while(!input.publish){require(nds_frontend_service_native_hold(),"frontend cancelled Task Z hold");std::this_thread::sleep_for(std::chrono::milliseconds(20));}
            require(!activity.status().contact_down&&!nds_touch_observation().down&&nds_touch_observation().adc_x==0&&nds_touch_observation().adc_y==4095,"release before publication");
            nds_set_touch_owner(nullptr,nullptr);nds_gpu2d_set_bottom_presentation(nullptr);sample("owners_removed");
        }
        auto cleanup=recognizer.end_session();require(cleanup.success&&!recognizer.active(),"recognizer cleanup");
        require(diagnostics::mainram_snapshot()==ram_before&&std::memcmp(&cpu_before,&g_cpu,sizeof(g_cpu))==0&&std::memcmp(&interpreter_before,&cpu,sizeof(cpu))==0,"private service RAM/CPU isolation");
        require(g_runtime_cycles==cycles9&&scheduler_cpu_cycles(1)==cycles7&&g_insn_count[0]==ordinal9&&g_insn_count[1]==ordinal7&&diagnostics::video_digest()==video_before&&flash_digest()==flash_before&&nds_touch_observation().guest_deliveries==deliveries,"hold counters/video/save/input isolation");
        file("service-clean-mainram.bin",diagnostics::mainram_snapshot());
        log("{\"event\":\"service_cleanup\",\"return\":"+std::to_string(cleanup.error)+",\"private_instructions\":"+std::to_string(cleanup.instructions)+",\"live_ram_equal\":true,\"cpu_equal\":true,\"active\":false,\"ram_sha256\":\""+hash(ram_before)+"\"}");
        require(selected.integer!=0xffff&&selected.countdown==1&&selected.timing_supported,"policy publication eligibility");
        store(slot_address+0x320,selected.integer);store(slot_address+0x364,selected.countdown);staged=true;
        sample("resume_original_publication");return 0;
    }catch(const std::exception& error){log("{\"event\":\"failure\",\"message\":\""+std::string(error.what())+"\"}");done=true;finish(2);return 2;}
}
}
