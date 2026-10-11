#include "setup_guard.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main(){unsigned cases=0;
 for(unsigned i=0;i<8;++i){uint32_t regs[16];unsigned flags[4];std::memcpy(regs,au_fixed::r[i],sizeof(regs));std::memcpy(flags,au_fixed::flags[i],sizeof(flags));
 assert(au_fixed::state(i,regs,flags,au_fixed::opcode[i],281098001ull+i));++cases;
 assert(au_fixed::dispatch(i)==(i<7));++cases;
 for(unsigned n=0;n<16;++n){regs[n]^=1;assert(!au_fixed::state(i,regs,flags,au_fixed::opcode[i],281098001ull+i));regs[n]^=1;++cases;}
 for(unsigned n=0;n<4;++n){flags[n]^=1;assert(!au_fixed::state(i,regs,flags,au_fixed::opcode[i],281098001ull+i));flags[n]^=1;++cases;}
 assert(!au_fixed::state(i,regs,flags,au_fixed::opcode[i]^1,281098001ull+i));++cases;
 assert(!au_fixed::state(i,regs,flags,au_fixed::opcode[i],281098002ull+i));++cases;}
 for(unsigned i=0;i<9;++i){auto q=au_fixed::reads[i];assert(au_fixed::read(i,q.index,q.pc,q.address,q.width));assert(!au_fixed::read(i,q.index,q.pc,q.address+1,q.width));assert(!au_fixed::read(i,q.index,q.pc,q.address,1));assert(!au_fixed::read(i,q.index+1,q.pc,q.address,q.width));cases+=4;}
 for(unsigned i=0;i<1;++i){auto q=au_fixed::writes[i];assert(au_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value));assert(!au_fixed::write(i,q.index,q.pc,q.opcode,q.address+1,q.width,q.value));assert(!au_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value^1));assert(!au_fixed::write(i,q.index+1,q.pc,q.opcode,q.address,q.width,q.value));assert(!au_fixed::write(i,q.index,q.pc,q.opcode,q.address,1,q.value));cases+=5;}
 assert(!au_fixed::read(9,7,0x02001980,0x02001980,4));assert(!au_fixed::write(1,7,0,0,0,4,0));cases+=2;
 assert(!au_fixed::read(9,7,0x02001980,0x04000280,2));assert(!au_fixed::write(1,7,0x02001980,0xe1c130b0,0x04000280,2,1));cases+=2;
 std::printf("PASS %u fixed-state/path/opcode/budget/read/write negative and positive assertions\n",cases);}
