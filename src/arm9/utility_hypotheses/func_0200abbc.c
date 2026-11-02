#include "contracts.h"

ba_u32 func_0200abbc(void *context, const unsigned char *input)
{
    ba_u32 pair[2];
    if (func_0200acd0(pair, input) == 0)
        return 0;
    if (func_0200ac04(context, pair[0], pair[1]) == 0)
        return 0;
    return 1;
}
