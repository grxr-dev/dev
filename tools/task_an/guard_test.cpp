#include "guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
using namespace task_an_guard;
int main(){
 for(unsigned i=0;i<111;++i){assert(permits(i,decision_path[i],i));assert(dispatches(i,decision_path[i],i)==(i<110));assert(!permits(i,decision_path[i]^4,i));assert(!permits(i,decision_path[i],i+1));}
 assert(!permits(111,0x02067c48,111));
 for(unsigned i=0;i<20;++i){assert(an_opcode(i,an_opcodes[i]));assert(!an_opcode(i,an_opcodes[i]^1));for(unsigned r=0;r<16;++r){assert(an_register(i,r,an_r[i][r]));assert(!an_register(i,r,an_r[i][r]^1));}auto f=an_flags[i];assert(an_flag_state(i,f[0],f[1],f[2],f[3]));assert(!an_flag_state(i,!f[0],f[1],f[2],f[3]));assert(!an_flag_state(i,f[0],!f[1],f[2],f[3]));assert(!an_flag_state(i,f[0],f[1],!f[2],f[3]));assert(!an_flag_state(i,f[0],f[1],f[2],!f[3]));}
 for(unsigned i=0;i<22;++i){auto e=an_reads[i];assert(an_read(i,e.index,e.pc,e.address,4,e.value));assert(!an_read(i,e.index,e.pc,e.address,1,e.value));assert(!an_read(i,e.index,e.pc,e.address^4,4,e.value));assert(!an_read(i,e.index,e.pc,e.address,4,e.value^1));assert(!an_read(i,e.index,e.pc,0x04000000,4,e.value));}
 assert(!an_read(22,19,0x02067c44,0x02067c44,4,0xe5840250));
 for(unsigned w:{1u,2u,4u}){assert(!an_write(0x020ea1c0,w,0x02132750));assert(!an_write(0x027e3b04,w,0));}
 puts("PASS: ordered 19-dispatch budget, terminal non-dispatch, all CPU/opcode negatives, exactly 22 reads and zero allowed writes");
}
