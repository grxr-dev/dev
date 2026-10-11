#include "guard.h"
#include <cassert>
#include <cstdio>
int main(){using namespace task_al_guard;
assert(dispatches(90,0x02067bdc,90));assert(permits(91,0x02067be0,91));assert(!dispatches(91,0x02067be0,91));
assert(!permits(92,0x02067be4,92));assert(!dispatches(90,0x02067be0,90));assert(!dispatches(90,0x02067bdc,91));
assert(al_write(0x02067bdc,0xe5842254,0x020ea1c4,4,0));
assert(!al_write(0x02067bdc,0xe5842254,0x020ea1c8,4,0));assert(!al_write(0x02067bdc,0xe5842254,0x020ea1c4,1,0));assert(!al_write(0x02067bdc,0xe5842254,0x020ea1c4,4,1));assert(!al_write(0x02067be0,0xe5842254,0x020ea1c4,4,0));
puts("PASS 11 AL dispatch/store guard assertions");}
