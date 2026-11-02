/* Diagnostic hypothesis, not an identified original source/prototype.
 * Contract: stable nonnull readable NUL-terminated object, n>=3, n fits
 * unsigned int, no address wrap, and the counter's one-past increment valid.
 * No short/null guard is added: the original unconditionally reads p[n-3].
 */
extern unsigned int func_02067f74(const unsigned char *p);

unsigned int func_020665cc(const unsigned char *p)
{
    unsigned int n = func_02067f74(p);
    if (p[n - 3] != 0x63) return 0;
    if (p[n - 2] != 0x6d) return 0;
    if (p[n - 1] == 0x70) return 1;
    return 0;
}
