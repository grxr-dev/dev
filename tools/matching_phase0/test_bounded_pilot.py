"""ROM-free tests of the bounded static bit proof; no guest execution."""
import unittest
from bounded_pilot import bit_origins


def sample(shift='lsr',mask='#0xff'):
    # Authored synthetic program, not a stored ROM/disassembly fixture.
    return [{'mnemonic':op,'operands':args} for op,args in (
        (shift,'r1, r0, #8'),('and','r1, r1, '+mask),
        ('and','r0, r0, #0xff'),('lsl','r0, r0, #8'),
        ('orr','r0, r0, r1'),('bx','lr'))]


class BitProofTests(unittest.TestCase):
    def test_expected_permutation_and_zero_extension(self):
        self.assertEqual(bit_origins(sample()),['x'+str(i) for i in [*range(8,16),*range(8)]]+[0]*16)

    def test_mask_makes_signed_and_unsigned_shift_equivalent(self):
        self.assertEqual(bit_origins(sample('asr')),bit_origins(sample('lsr')))

    def test_wrong_mask_is_detectably_different(self):
        self.assertNotEqual(bit_origins(sample(mask='#0xf')),bit_origins(sample()))

    def test_all_halfwords_and_high_bit_cases(self):
        origins=bit_origins(sample())
        def evaluate(x):return sum((v if isinstance(v,int) else ((x>>int(v[1:]))&1))<<i for i,v in enumerate(origins))
        for x in range(65536):self.assertEqual(evaluate(x),((x&255)<<8)|(x>>8))
        for x in (0x80000000,0xffffffff,0x80001234,0x7fffabcd,0x12345678):
            self.assertEqual(evaluate(x),((x&255)<<8)|((x>>8)&255))

    def test_no_memory_calls_conditionals_or_unknown_boolean_claim(self):
        for ins in ({'mnemonic':'ldr','operands':'r0, [r1]'},
                    {'mnemonic':'bl','operands':'#0x100'},
                    {'mnemonic':'movs','operands':'r0, #0'}):
            with self.assertRaises(ValueError):bit_origins([ins,{'mnemonic':'bx','operands':'lr'}])
        with self.assertRaises(ValueError):bit_origins([
            {'mnemonic':'lsr','operands':'r1, r0, #1'},
            {'mnemonic':'orr','operands':'r0, r0, r1'},
            {'mnemonic':'bx','operands':'lr'}])

    def test_requires_final_return(self):
        with self.assertRaises(ValueError):bit_origins(sample()[:-1])


if __name__=='__main__':unittest.main()
