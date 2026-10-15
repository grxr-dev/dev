#include <fstream>
#include <iostream>
#include "aw7/integration.h"
#include "../task_aw4/fixture.h"
#include "au_guard_model.h"

namespace {
std::string root;
void marker(const char* name) { std::ofstream(root+"/"+name)<<"REACHED"; }
void persistence() { marker("persistence"); }
struct Shutdown { ~Shutdown() { marker("shutdown"); } };
}

int main(int argc,char** argv) {
    try {
        task_aw2::require(argc==2,"fresh provider audit directory required");
        const std::string directory=argv[1];
        root=directory; static Shutdown shutdown; std::atexit(persistence);
        auto* output=task_aw3::exclusive_audit((directory+"/audit.jsonl").c_str());
        task_aw3::arm(output);
        const std::string identity="AW7 ROM-free actual provider fixture; not Brain Age";
        task_aw3::rom_identity=gba::sha1(reinterpret_cast<const uint8_t*>(identity.data()),identity.size()).hex();
        task_aw3::rom_epoch=1;
        task_aw3::audit_text("provider_kind","actual runtime/bus/CP15/IO/scheduler/SPU/GPU/Wifi getters on ROM-free synthetic buffers; no identity override");
        using namespace task_aw4::fixture;
        bus_begin(); io_begin(); scheduler_begin(); spu_begin(); runtime_begin();
        const auto observed=task_aw3::passive();
        task_aw2::audit_snapshot(output,observed);
        task_aw7::arm_diagnostic();
        auto cpu=brainage_task_au::terminal_cpu();
        brainage_task_au::au_control(cpu);
        std::ofstream(directory+"/actual-provider-returned")<<"REACHED";
        return 90;
    } catch (const std::exception& error) { task_aw3::fail(error.what()); }
}
