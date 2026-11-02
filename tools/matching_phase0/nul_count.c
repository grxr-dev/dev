/* Diagnostic hypothesis, not a recovered original prototype or library name.
 * p is nonnull and points into a stable, readable allocated byte object.
 * Its first zero is at offset n within that object; n fits unsigned int,
 * and advancing through p+n+1 is valid (possibly one-past), without wrap.
 * No volatile/device memory or concurrent modification is modeled.
 * Reads exactly p[0] through p[n], returns n; empty input returns zero.
 */
unsigned int func_02067f74(const unsigned char *p)
{
    unsigned int count = 0;
    unsigned char next = *p++;
    if (next != 0) {
        do {
            next = *p++;
            ++count;
        } while (next != 0);
    }
    return count;
}
