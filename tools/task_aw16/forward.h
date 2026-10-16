#pragma once
#include "aw3/bridge.h"
namespace task_aw16 {
class Controller;
bool receive_fence(FILE*,const task_aw2::Snapshot&,const task_aw2::Snapshot&,
                   uint64_t,uint64_t,uint64_t,const std::string&);
void mark(const char*);
void slice_gate(int,uint32_t);
void slice_begun(int,uint32_t);
}
