#include "guard.h"
#include <cassert>
#include <cstdio>
using namespace task_ak_guard;
int main(){
 for(unsigned i=0;i<91;++i){assert(permits(i,decision_path[i],i));assert(dispatches(i,decision_path[i],i)==(i<90));assert(!permits(i,decision_path[i]^4,i));assert(!permits(i,decision_path[i],i+1));}
 assert(!permits(91,0x02067be0,91));
 for(unsigned i=0;i<8;++i){auto w=writes[i];assert(ak_write(i,w.pc,w.address,4,w.value));assert(!ak_write(i,w.pc+4,w.address,4,w.value));assert(!ak_write(i,w.pc,w.address+4,4,w.value));assert(!ak_write(i,w.pc,w.address,1,w.value));assert(!ak_write(i,w.pc,w.address,4,w.value^1));}
 assert(!ak_write(8,0x02067bdc,0x020ea1c4,4,0));
 for(unsigned i=0;i<25;++i){assert(ak_read(i,decision_path[65+i],4));assert(!ak_read(i,0x04000000,4));assert(!ak_read(i,decision_path[65+i],1));assert(!ak_read(i,0x020ea1c4,4));}
 assert(!ak_read(25,0x02067bdc,4));
 assert(completed_writes(1)==0&&completed_writes(2)==6&&completed_writes(23)==6&&completed_writes(24)==8);
 puts("PASS: 25-instruction budget, terminal non-dispatch, ordered writes and read/MMIO firewall negatives");
}
