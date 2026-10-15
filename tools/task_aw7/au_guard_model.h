#pragma once
#include "aw5/capture.h"
#include "task_au_setup_guard.h"
namespace brainage_task_au {
inline bool au_armed=true,au_pending=false,done=false;
inline unsigned au_index=7,au_reads=9,au_writes=1,au_bus_index=0;
inline std::vector<uint8_t> au_ram,au_expected_dtcm,decision_flash;
inline uint64_t g_insn_count[2]={281098008,96026779};
struct Flags { bool n=false,z=false,c=false,v=false,t=false,i=false,f=false; unsigned mode=31; };
struct CPU { uint32_t R[16]{}; Flags cpsr; };
inline void require(bool valid,const char* why) { task_aw2::require(valid,why); }
inline uint32_t word(uint32_t) { return au_fixed::opcode[7]; }
namespace diagnostics { inline std::vector<uint8_t> mainram_snapshot() { return {}; } }
inline std::vector<uint8_t> read(uint32_t,unsigned) { return {}; }
inline std::vector<uint8_t> save_snapshot() { return {}; }
template<class Value> void registers(const char*,const Value&) {}
inline void file(const char*,const std::vector<uint8_t>&) {
    if (task_aw3::armed) task_aw3::fail("legacy AU file output reached while armed");
}
inline void sample(const char*) {}
inline void log(const std::string&) {}
inline void finish(int) {
    if (task_aw3::armed) task_aw3::fail("AU finish/halt forbidden during capture");
    std::_Exit(99);
}
#include "task_au_setup.inc"
inline CPU terminal_cpu() {
    CPU cpu;
    for (unsigned index=0;index<16;++index) cpu.R[index]=au_fixed::r[7][index];
    return cpu;
}
}
