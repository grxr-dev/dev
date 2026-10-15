#include "aw5/capture.h"
#define main aw3_historical_main
#include "../task_aw3/test.cpp"
#undef main

int main(int argc,char** argv) {
    try {
        task_aw2::require(argc==3,"mode and output required");
        prepare(argv[2]);
        const std::string mode=argv[1];
        _putenv("NDS_TASK_AW5_CAPTURE_ONLY=1");
        for (const auto& field:task_aw4::full_layout(provided))
            if (!provided.fields.count(field.first)) provided.put(field.first,field.second,0);
        provided.put("hidden.fast_enabled",1,1);
        static Shutdown shutdown;
        std::atexit(onexit);
        if (mode=="missing") provided.fields.erase("hidden.bank.02001980");
        if (mode=="yield") provided.put("hidden.yield",4,1);
        if (mode=="cap") provided.put("slice_cap",8,task_aw2::entry_cycle+1);
        if (mode=="save") provided.hashes.at("save")[0]='0';
        if (mode=="readiness") provided.put("timer.0.control",2,128);
        if (mode=="journal") task_aw3::sticky="stale journal test";
        if (mode=="legacy") _putenv("NDS_TASK_AW5_CAPTURE_ONLY=0");
        if (mode=="disabled") { task_aw3::armed=false; _putenv("NDS_TASK_AW5_CAPTURE_ONLY=0"); }
        brainage_task_au::CPU cpu{};
        for (unsigned index=0;index<16;++index) cpu.R[index]=au_fixed::r[7][index];
        if (mode=="bad-au") cpu.R[0]^=1;
        try { brainage_task_au::au_control(cpu); }
        catch (const std::exception& error) { if (task_aw3::armed) task_aw3::fail(error.what()); throw; }
        for (const auto* name:{"post-boundary-instruction","scheduler-tail","device-tail","IRQ-tail","ARM7-tail"}) marker(name);
        return 90;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
