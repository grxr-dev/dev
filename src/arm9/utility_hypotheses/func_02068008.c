#include "contracts.h"

ba_u32 func_02068008(ba_u32 value)
{
    ba_u32 low_byte = value & 0xffu;
    ba_u32 high_byte = (value >> 8) & 0xffu;
    return (high_byte | (low_byte << 8)) & 0xffffu;
}
