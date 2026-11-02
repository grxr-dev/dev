#include "contracts.h"

ba_u32 func_0200ac04(void *context, ba_u32 first, ba_u32 second)
{
    if (first == 0)
        return 0;
    ba_u32 *words = context;
    words[2] = first;
    words[11] = first;
    words[12] = second;
    if (func_0200a464(context, 6, second, first) == 0)
        return 0;
    words[3] |= 0x10u;
    words[3] &= ~0x20u;
    return 1;
}
