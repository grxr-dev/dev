#pragma once
#include <cstdio>
#include <cstdlib>
#include <unordered_map>
#include "state.h"
// Opt-in, bounded pre-instruction snapshots. Debug reads have no guest bus effects.
inline bool task_b_armed = false;
inline bool task_b_done = false;
inline FILE* task_b_file() {
 static FILE* f=[] { const char* p=std::getenv("NDS_TASK_B_TRACE"); return p&&*p?std::fopen(p,"wb"):nullptr; }(); return f;
}
inline bool task_b_ram(uint32_t p) { return (p>=0x02000000u&&p<0x02400000u)||(p>=0x027e0000u&&p<0x02800000u)||(p>=0x037f8000u&&p<0x03810000u); }
inline void task_b_snapshot(uint32_t pc, bool thumb, const uint32_t* regs, uint32_t cpsr) {
 FILE* f=task_b_file(); if(!f||task_b_done)return;
 const int cpu=g_nds_active==NDS_ARM9?9:7;
 if(cpu==9 && pc==0x0202fcc0u) task_b_armed=true;
 if(!task_b_armed)return;
 static std::unordered_map<uint64_t,unsigned> hits;
 static unsigned total=0;
 const bool focused=(cpu==9&&((pc>=0x0202fa08&&pc<0x0202fd60)||(pc>=0x0200d000&&pc<0x0200e800))) || (cpu==7&&((pc>=0x03802900&&pc<0x03803600)||(pc>=0x037fe000&&pc<0x037fe800)));
 unsigned& n=hits[(uint64_t(cpu)<<32)|pc]; ++n;
 if(n>(focused?64u:2u)||total>=40000u)return;
 ++total;
 std::fprintf(f,"{\"seq\":%u,\"cpu\":%d,\"pc\":%u,\"thumb\":%s,\"cpsr\":%u,\"cycle\":%llu,\"insn\":%llu,\"hit\":%u,\"r\":[",total,cpu,pc,thumb?"true":"false",cpsr,(unsigned long long)g_runtime_cycles,(unsigned long long)g_insn_count[g_nds_active],n);
 for(int i=0;i<16;++i)std::fprintf(f,"%s%u",i?",":"",regs[i]);
 std::fputs("],\"mem\":[",f);
 uint32_t addresses[7]={regs[0],regs[1],regs[2],regs[3],regs[13],0x03809060u,0};
 for(int k=0;k<4;++k)addresses[6]|=uint32_t(bus_debug_read8(cpu,0x03809060u+k))<<(8*k);
 bool comma=false;
 for(uint32_t p:addresses) { if(!task_b_ram(p)||!task_b_ram(p+63))continue;
 std::fprintf(f,"%s{\"addr\":%u,\"hex\":\"",comma?",":"",p);comma=true;
 for(unsigned i=0;i<64;++i)std::fprintf(f,"%02x",unsigned(bus_debug_read8(cpu,p+i)));
 std::fputs("\"}",f); }
 std::fputs("]}\n",f); std::fflush(f);
}
