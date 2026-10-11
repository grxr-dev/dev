#include "entry_guard.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main(){unsigned cases=0;
 for(unsigned i=0;i<12;++i){uint32_t regs[16];unsigned flags[4];std::memcpy(regs,as_fixed::r[i],sizeof(regs));std::memcpy(flags,as_fixed::flags[i],sizeof(flags));
 assert(as_fixed::state(i,regs,flags,as_fixed::opcode[i],281097990ull+i));++cases;
 assert(as_fixed::dispatch(i)==(i<11));++cases;
 for(unsigned n=0;n<16;++n){regs[n]^=1;assert(!as_fixed::state(i,regs,flags,as_fixed::opcode[i],281097990ull+i));regs[n]^=1;++cases;}
 for(unsigned n=0;n<4;++n){flags[n]^=1;assert(!as_fixed::state(i,regs,flags,as_fixed::opcode[i],281097990ull+i));flags[n]^=1;++cases;}
 assert(!as_fixed::state(i,regs,flags,as_fixed::opcode[i]^1,281097990ull+i));++cases;
 assert(!as_fixed::state(i,regs,flags,as_fixed::opcode[i],281097991ull+i));++cases;}
 for(unsigned i=0;i<16;++i){auto q=as_fixed::reads[i];assert(as_fixed::read(i,q.index,q.pc,q.address,q.width));assert(!as_fixed::read(i,q.index,q.pc,q.address+1,q.width));assert(!as_fixed::read(i,q.index,q.pc,q.address,1));assert(!as_fixed::read(i,q.index+1,q.pc,q.address,q.width));cases+=4;}
 for(unsigned i=0;i<10;++i){auto q=as_fixed::writes[i];assert(as_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value));assert(!as_fixed::write(i,q.index,q.pc,q.opcode,q.address+1,q.width,q.value));assert(!as_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value^1));assert(!as_fixed::write(i,q.index+1,q.pc,q.opcode,q.address,q.width,q.value));assert(!as_fixed::write(i,q.index,q.pc,q.opcode,q.address,1,q.value));cases+=5;}
 assert(!as_fixed::read(16,11,0x02067564,0x02067564,4));assert(!as_fixed::write(10,11,0,0,0,4,0));cases+=2;
 std::printf("PASS %u fixed-state/path/opcode/budget/read/write negative and positive assertions\n",cases);}
