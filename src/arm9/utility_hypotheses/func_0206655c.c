#include "contracts.h"

ba_u32 func_0206655c(const unsigned char *input)
{
    unsigned char *context = data_020dcbf4;
    ba_u32 header[8];
    ba_u32 result;
    func_0200aee8(context);
    (void)func_0200abbc(context, input);
    result = *(ba_u32 *)(context + 0x24) - *(ba_u32 *)(context + 0x20);
    if (func_020665cc(input) != 0) {
        (void)func_0200aa5c(context, header, 0x20);
        result = header[0] >> 8;
    }
    func_0200ab7c(context);
    return result;
}
