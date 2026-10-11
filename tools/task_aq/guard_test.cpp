#include "slice_guard.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main(){unsigned cases=0;
 for(unsigned i=0;i<46;++i){uint32_t regs[16];unsigned flags[4];std::memcpy(regs,aq_fixed::r[i],sizeof(regs));std::memcpy(flags,aq_fixed::flags[i],sizeof(flags));
 assert(aq_fixed::state(i,regs,flags,aq_fixed::opcode[i],281097945ull+i));++cases;
 assert(aq_fixed::dispatch(i)==(i<45));++cases;
 for(unsigned n=0;n<16;++n){regs[n]^=1;assert(!aq_fixed::state(i,regs,flags,aq_fixed::opcode[i],281097945ull+i));regs[n]^=1;++cases;}
 for(unsigned n=0;n<4;++n){flags[n]^=1;assert(!aq_fixed::state(i,regs,flags,aq_fixed::opcode[i],281097945ull+i));flags[n]^=1;++cases;}
 assert(!aq_fixed::state(i,regs,flags,aq_fixed::opcode[i]^1,281097945ull+i));++cases;
 assert(!aq_fixed::state(i,regs,flags,aq_fixed::opcode[i],281097946ull+i));++cases;}
 for(unsigned i=0;i<51;++i){auto q=aq_fixed::reads[i];assert(aq_fixed::read(i,q.index,q.pc,q.address,q.width));assert(!aq_fixed::read(i,q.index,q.pc,q.address+1,q.width));assert(!aq_fixed::read(i,q.index,q.pc,q.address,1));assert(!aq_fixed::read(i,q.index+1,q.pc,q.address,q.width));cases+=4;}
 for(unsigned i=0;i<18;++i){auto q=aq_fixed::writes[i];assert(aq_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value));assert(!aq_fixed::write(i,q.index,q.pc,q.opcode,q.address+1,q.width,q.value));assert(!aq_fixed::write(i,q.index,q.pc,q.opcode,q.address,q.width,q.value^1));assert(!aq_fixed::write(i,q.index+1,q.pc,q.opcode,q.address,q.width,q.value));assert(!aq_fixed::write(i,q.index,q.pc,q.opcode,q.address,1,q.value));cases+=5;}
 assert(!aq_fixed::read(51,45,0x02026044,0x02026044,4));assert(!aq_fixed::write(18,45,0,0,0,4,0));cases+=2;
 std::printf("PASS %u fixed-state/path/opcode/budget/read/write negative and positive assertions\n",cases);}
