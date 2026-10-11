#include "guard.h"
#include <cassert>
#include <cstdio>
int main(){using namespace task_ao_guard;
assert(dispatches(110,0x02067c44,110));assert(permits(111,0x02067c48,111));assert(!dispatches(111,0x02067c48,111));
assert(!permits(112,0x02067c4c,112));assert(!dispatches(110,0x02067c48,110));assert(!dispatches(110,0x02067c44,111));
assert(ao_write(0x02067c44,0xe5840250,0x020ea1c0,4,0x02132750));
assert(!ao_write(0x02067c44,0xe5840250,0x020ea1c8,4,0x02132750));assert(!ao_write(0x02067c44,0xe5840250,0x020ea1c0,1,0x02132750));assert(!ao_write(0x02067c44,0xe5840250,0x020ea1c0,4,1));assert(!ao_write(0x02067c48,0xe5840250,0x020ea1c0,4,0x02132750));
puts("PASS 11 AO dispatch/store guard assertions");}
