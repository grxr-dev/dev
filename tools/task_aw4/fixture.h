#pragma once
#include "aw3/bridge.h"
namespace task_aw4::fixture {
void runtime_begin();
void runtime_banks();
void bus_begin();
void io_begin();
void scheduler_begin();
void spu_begin();
void runtime_fetch();
void runtime_commit(unsigned index, uint32_t cost);
void runtime_retire(unsigned index);
void runtime_poll();
void io_model_write(unsigned index);
void mutate(const std::string& name);
void io_mutate(const std::string& name);
void scheduler_mutate(const std::string& name);
void bus_mutate(const std::string& name);
}
