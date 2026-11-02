#include "contracts.h"

void func_0200aee8(void *context)
{
    ba_u32 *words = context;
    words[0] = 0;
    words[1] = words[0];
    *(ba_u16 *)((unsigned char *)context + 0x18) = 0;
    words[2] = 0;
    words[4] = 14;
    words[3] = 0;
}
