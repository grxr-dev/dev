#include <iostream>
#include <fstream>
#include "aw3/bridge.h"
#include "runtime_arm.h"
#include "state.h"
#include "savestate.h"
extern "C" { uint32_t g_insn_hook_armed=0; void runtime_insn_slow() { std::abort(); } }
namespace task_aw3 { void io_snapshot(Snapshot&) { throw std::runtime_error("real IO provider not linked in this device-stub rail"); } }
int main(int argc,char** argv) {
    using namespace task_aw3;
    try {
        if (argc!=2) return 2;
        auto* file=std::fopen(argv[1],"wb");
        arm(file);
        g_nds_active=NDS_ARM9; g_runtime_cycles=100;
        nds_slice_begin(228);
        require(history.size()==1 && history.back().source==0 && history.back().cycle==100,"real slice-origin journal");
        nds_reschedule_slice(90);
        require(history.size()==2 && history.back().before==228 && history.back().after==180,"real shortening journal");
        nds_reschedule_slice(100);
        require(history.size()==3 && history.back().after==180 && history.back().deadline==100,"real retained-cap provenance");
        task_aw2::Snapshot copied;
        runtime_snapshot(copied);
        require(copied.get("slice_cap")==180 && copied.get("cycle9")==100,"actual passive cap/cycle copy");
        const auto identity=task_aw2::digest(copied);
        task_aw2::Snapshot repeated;
        runtime_snapshot(repeated);
        require(task_aw2::digest(repeated)==identity,"actual passive runtime copy is stable");
        nds_set_cycle_cap(300);
        require(!sticky.empty(),"real unclassified setter invalidates eligibility");
        nds_slice_begin(228);
        require(sticky.empty() && history.size()==1 && epoch==3,"fresh real slice creates new trusted epoch");
        NdsCp15SaveState copied_cp15{};
        cp15_savestate_export(&copied_cp15);
        std::string import_error;
        require(cp15_savestate_import(copied_cp15,&import_error) && epoch==4 && !sticky.empty(),"real CP15 import invalidates provenance");
        nds_slice_begin(228);
        require(epoch==5 && sticky.empty(),"new slice follows imported epoch");
        armed=false;
        const auto sequence=serial;
        nds_reschedule_slice(80);
        runtime_snapshot(copied);
        require(serial==sequence && copied.get("slice_cap")==160,"disabled real runtime behavior preserved");
        std::fclose(file);
        std::cout<<"AW3 actual-runtime checks: 10\n";
        return 0;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
