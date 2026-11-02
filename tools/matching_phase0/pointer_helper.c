/* Diagnostic hypothesis: one incoming format pointer in r0, not a selector
 * argument in r1. The shared writable buffer has no bound enforced here.
 * Requires the opaque formatting call to write within valid storage and return
 * normally. The result aliases shared storage and is not independently owned.
 */
extern int func_02019024(char *destination, const char *format, ...);

char *func_020660fc(const char *format)
{
    char *shared = (char *)0x020dcbb4u;
    (void)func_02019024(shared, format, 0x65);
    return shared;
}
