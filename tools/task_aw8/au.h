#pragma once
#include "binding.h"
#include "aw5/capture.h"
#include "task_au_setup_guard.h"
#include "state.h"
namespace brainage_task_au {
inline bool au_armed=true,au_pending=false,done=false;
inline unsigned au_index=7,au_reads=9,au_writes=1,au_bus_index=0;
inline std::vector<uint8_t> au_ram,au_expected_dtcm,decision_flash;
struct Flags { bool n=false,z=false,c=false,v=false,t=false,i=false,f=false; unsigned mode=31; };
struct CPU { uint32_t R[16]{}; Flags cpsr; };
inline void require(bool valid,const char* why) { task_aw2::require(valid,why); }
inline uint32_t word(uint32_t address) { return task_aw8::scalar(address,4); }
namespace diagnostics { inline std::vector<uint8_t> mainram_snapshot() { return task_aw8::ram_copy(); } }
inline std::vector<uint8_t> read(uint32_t address,unsigned size) {
    require(address==0x027e0000 && size==0x4000,"only passive fixture DTCM copy"); return task_aw8::dtcm_copy();
}
inline std::vector<uint8_t> save_snapshot() { return task_aw8::save_copy(); }
template<class Value> void registers(const char*,const Value&) {}
inline void file(const char*,const std::vector<uint8_t>&) { task_aw3::fail("old AU file output forbidden"); }
inline void sample(const char*) {}
inline void log(const std::string&) {}
inline void finish(int) { task_aw3::fail("old AU halt forbidden"); }
#include "task_au_setup.inc"
inline CPU cpu_copy() {
    CPU cpu;
    for (unsigned index=0;index<16;++index) cpu.R[index]=g_cpu.R[index];
    const auto flags=uint32_t(g_cpu.cpsr);
    cpu.cpsr={bool(flags>>31),bool((flags>>30)&1),bool((flags>>29)&1),bool((flags>>28)&1),
        bool(flags&32),bool(flags&128),bool(flags&64),unsigned(flags&31)};
    return cpu;
}
}
