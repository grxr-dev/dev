#include "contracts.h"

ba_u32 func_02067f74(const unsigned char *input)
{
    ba_u32 count = 0;
    unsigned char next = *input++;
    if (next != 0) {
        do {
            next = *input++;
            ++count;
        } while (next != 0);
    }
    return count;
}
