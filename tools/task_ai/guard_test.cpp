#include "guard.h"
#include "../task_ah/guard.h"
#include <cassert>
#include <cstdio>
int main(){using namespace task_ai_guard;
 assert(sizeof(decision_path)/sizeof(*decision_path)==66);
 for(size_t i=0;i<65;i++)assert(decision_path[i]==task_ah_guard::decision_path[i]);
 for(size_t i=0;i<66;i++){
  assert(permits(i,decision_path[i],i));assert(dispatches(i,decision_path[i],i)==(i<65));
  assert(!permits(i,decision_path[i],i+1));assert(!dispatches(i,0x02026254,i));
  assert(!dispatches(i,0x02026254,i)&&!permits(i,0x02025f78,i));
  if(i>=55){assert(outer_opcode(i,outer_opcodes[i-55]));assert(!outer_opcode(i,outer_opcodes[i-55]^1));for(unsigned k=0;k<16;k++){assert(outer_register(i,k,outer_r[i-55][k]));assert(!outer_register(i,k,outer_r[i-55][k]^1));}}
 }
 assert(dispatches(64,0x02026250,64));
 assert(dispatches(63,0x0202624c,63));assert(!permits(66,0x02026254,66));
 assert(store_event(0x0202624c,0xe5840034,0x020e9a34,4,0xda));
 assert(!store_event(0x02026250,0xe5840034,0x020e9a34,4,0xda));
 assert(!store_event(0x0202624c,0xe5840035,0x020e9a34,4,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a35,4,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a34,1,0xda));
 assert(!store_event(0x0202624c,0xe5840034,0x020e9a34,4,0xdb));
 puts("PASS: complete AH prefix; exactly one AI MOV; terminal never dispatched; all registers/opcodes/ordinals and write-event operands fail closed");
}
