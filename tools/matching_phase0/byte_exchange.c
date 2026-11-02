/* Behavioral hypothesis for 0x02068008; original name/prototype are unknown.
 * r0 supplies an integer; r0 returns a zero-extended low-halfword byte exchange.
 * unsigned int is 32 bits on the qualified diagnostic ARM target. Choosing a
 * full-width argument avoids assuming the caller has already cleared high bits.
 * The observed arithmetic shift's sign extension is masked away by & 0xff.
 */
unsigned int func_02068008(unsigned int value)
{
    unsigned int low_byte = value & 0xffu;
    unsigned int high_byte = (value >> 8) & 0xffu;
    return (high_byte | (low_byte << 8)) & 0xffffu;
}
