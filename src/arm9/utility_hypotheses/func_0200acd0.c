#include "contracts.h"

ba_u32 func_0200acd0(ba_u32 *output_pair, const unsigned char *input)
{
    ba_u32 scratch[17];
    func_0200aee8(scratch);
    return func_0200ad94(scratch, input, output_pair, 0) != 0;
}
