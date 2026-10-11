#include "guard.h"
#include "../task_ae/guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main(){using namespace task_ag_guard;
 const auto count=sizeof(decision_path)/sizeof(*decision_path);assert(count==64);
 for(size_t i=0;i<56;++i)assert(decision_path[i]==task_ae_guard::decision_path[i]);
 for(size_t i=0;i<count;++i){
  assert(permits(i,decision_path[i],i));assert(dispatches(i,decision_path[i],i)==(i<63));
  assert(!permits(i,decision_path[i],i+1));assert(!dispatches(i,0x0202624c,i));
  for(auto bad:{0x02026250u,0x02026254u,0x02025f78u,0x0202622cu,0x02026230u,0x0200de78u})assert(!permits(i,bad,i));
  if(i>=55){assert(outer_opcode(i,outer_opcodes[i-55]));assert(!outer_opcode(i,outer_opcodes[i-55]^1));
   for(unsigned reg=0;reg<16;++reg){assert(outer_register(i,reg,outer_r[i-55][reg]));assert(!outer_register(i,reg,outer_r[i-55][reg]^1));}}
 }
 assert(!permits(64,0x02026250,64)&&!outer_opcode(54,0xebfffda0)&&!outer_opcode(64,0xe5840034));
 assert(pushed_byte(0x027e3b2c)==3&&pushed_byte(0x027e3b2d)==0&&pushed_byte(0x027e3b30)==0x94&&pushed_byte(0x027e3b31)==0x6b&&pushed_byte(0x027e3b32)==2&&pushed_byte(0x027e3b33)==2);
 std::puts("PASS: exact AE prefix; 63 dispatches; eight AF instructions; terminal STR/inner call/alternate path forbidden; every opcode and register negative; exact PUSH bytes");
}
