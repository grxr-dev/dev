#include "binding.h"
#include "aw8_spu.cpp"
namespace task_aw8 {
void spu_begin() { g_mix_count=entry().get("service.spu_mixes"); }
}
