#include "spu.cpp"
#include "fixture.h"
namespace task_aw4::fixture {
void spu_begin() { g_mix_count=((task_aw2::entry_cycle-9)>>1)/1024; }
}
