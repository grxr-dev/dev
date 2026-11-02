#include "contracts.h"

ba_u32 func_020665cc(const unsigned char *input)
{
    ba_u32 count = func_02067f74(input);
    if (input[count - 3] != 0x63) return 0;
    if (input[count - 2] != 0x6d) return 0;
    if (input[count - 1] == 0x70) return 1;
    return 0;
}
