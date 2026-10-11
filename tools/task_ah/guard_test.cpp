#include "guard.h"
#include "../task_ag/guard.h"
#include <cassert>
#include <cstdio>
int main(){using namespace task_ah_guard;
 assert(sizeof(decision_path)/sizeof(*decision_path)==65);
 for(size_t i=0;i<64;i++)assert(decision_path[i]==task_ag_guard::decision_path[i]);
 for(size_t i=0;i<65;i++){
  assert(permits(i,decision_path[i],i));assert(dispatches(i,decision_path[i],i)==(i<64));
  assert(!permits(i,decision_path[i],i+1));assert(!dispatches(i,0x02026250,i));
  assert(!permits(i,0x02026254,i)&&!permits(i,0x02025f78,i));
  if(i>=55){assert(outer_opcode(i,outer_opcodes[i-55]));assert(!outer_opcode(i,outer_opcodes[i-55]^1));for(unsigned k=0;k<16;k++){assert(outer_register(i,k,outer_r[i-55][k]));assert(!outer_register(i,k,outer_r[i-55][k]^1));}}
 }
 assert(dispatches(63,0x0202624c,63));assert(!permits(65,0x02026254,65));
 assert(store_event(0x0202624c,0xe5840034,0x020e9a34,4,0xda));
 assert(!store_event(0x02026250,0xe5840034,0x020e9a34,4,0xda));
 assert(!store_event(0x0202624c,0xe5840035,0x020e9a34,4,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a35,4,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a34,1,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a34,4,0xdb));
 puts("PASS: complete AG prefix; exactly one AH store; terminal never dispatched; all registers/opcodes/ordinals and write-event operands fail closed");
}
