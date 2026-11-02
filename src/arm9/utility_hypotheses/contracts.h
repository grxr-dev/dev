#ifndef BRAINAGE_UTILITY_HYPOTHESES_CONTRACTS_H
#define BRAINAGE_UTILITY_HYPOTHESES_CONTRACTS_H

typedef unsigned int ba_u32;
typedef unsigned short ba_u16;
_Static_assert(sizeof(ba_u32) == 4, "32-bit unsigned hypothesis required");
_Static_assert(sizeof(ba_u16) == 2, "16-bit unsigned hypothesis required");

#define data_020dcbb4 ((char *)0x020dcbb4u)
#define data_020dcbf4 ((unsigned char *)0x020dcbf4u)

extern int func_02019024(char *destination, const char *format, ...);
extern void func_0200aee8(void *context);
extern ba_u32 func_0200abbc(void *context, const unsigned char *input);
extern ba_u32 func_0200acd0(ba_u32 *output_pair, const unsigned char *input);
extern ba_u32 func_0200ac04(void *context, ba_u32 first, ba_u32 second);
extern ba_u32 func_0200aa5c(void *context, void *destination, ba_u32 count);
extern void func_0200ab7c(void *context);

int func_020660f4(void);
char *func_020660fc(const char *format);
ba_u32 func_0206655c(const unsigned char *input);
ba_u32 func_020665cc(const unsigned char *input);
ba_u32 func_02067f74(const unsigned char *input);
ba_u32 func_02068008(ba_u32 value);

#endif
