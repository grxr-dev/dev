/* Address-derived labels and minimal used-argument prototypes, not recovered
 * library APIs. This hypothesis requires normal ARM call preservation, stable
 * readable n>=3 terminated input, and non-reentrant access to the context.
 * If the predicate is nonzero, the opaque 32-byte call must initialize header[0]
 * before it is read. No failure guard or extra parameters are invented.
 */
typedef unsigned int u32;
extern void func_0200aee8(void *context);
extern u32 func_0200abbc(void *context, const unsigned char *input);
extern u32 func_020665cc(const unsigned char *input);
extern u32 func_0200aa5c(void *context, void *destination, u32 count);
extern void func_0200ab7c(void *context);

u32 func_0206655c(const unsigned char *input)
{
    unsigned char *context = (unsigned char *)0x020dcbf4u;
    u32 header[8];
    u32 result;
    func_0200aee8(context);
    (void)func_0200abbc(context, input);
    result = *(u32 *)(context + 0x24) - *(u32 *)(context + 0x20);
    if (func_020665cc(input) != 0) {
        (void)func_0200aa5c(context, header, 0x20);
        result = header[0] >> 8;
    }
    func_0200ab7c(context);
    return result;
}
