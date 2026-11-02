"""ROM-free checks of the bounded read/stop checker, not a DS emulator suite."""
import unittest
from nul_count_pilot import trace, verify_case


def fixture(signed=False):
    # Authored counter loop: increment only after testing the loaded byte.
    return [(0x100,'mov','r2, #0'),
            (0x104,'ldrsb' if signed else 'ldrb','r1, [r0], #1'),
            (0x108,'cmp','r1, #0'), (0x10c,'beq','#0x11c'),
            (0x110,'add','r2, r2, #1'), (0x114,'bne','#0x104'),
            (0x118,'mov','r3, #99'),  # unreachable; must not dispatch
            (0x11c,'mov','r0, r2'), (0x120,'bx','lr')]


class NulCountTests(unittest.TestCase):
    def test_empty_exact_last_byte_no_overread(self):
        a,b=verify_case(fixture(),fixture(True),b'\0',3)
        self.assertEqual(len(a['reads']),1)
        self.assertNotIn(0x118,b['path'])

    def test_every_nonzero_byte_signed_and_unsigned(self):
        for byte in range(1,256):
            verify_case(fixture(),fixture(True),bytes((byte,0)))

    def test_embedded_nul_hides_tail(self):
        for alignment in range(4):
            a,_=verify_case(fixture(),fixture(True),b'\xff\x80\x7f\0unread',alignment)
            self.assertEqual([r['offset'] for r in a['reads']],[0,1,2,3])

    def test_long_exact_extent(self):
        verify_case(fixture(),fixture(True),b'\xff'*1024+b'\0')

    def test_invalid_objects_rejected_before_trace(self):
        for data in (b'',b'unterminated',None):
            with self.assertRaises(ValueError):trace(fixture(),data)
        for base in (0,-1,0xffffffff):
            with self.assertRaises(ValueError):trace(fixture(),b'\0',base)

    def test_wrong_counter_detected(self):
        rows=fixture();rows[4]=(0x110,'add','r2, r2, #2')
        with self.assertRaises(AssertionError):verify_case(fixture(),rows,b'x\0')

    def test_overread_rejected_at_load(self):
        rows=[(0x100,'add','r0, r0, #1'),(0x104,'ldrb','r1, [r0]'),(0x108,'bx','lr')]
        with self.assertRaisesRegex(ValueError,'out-of-object'):trace(rows,b'\0')

    def test_writes_calls_and_unbounded_path_rejected(self):
        for op,args in [('str','r0, [r1]'),('bl','#0x200')]:
            with self.assertRaisesRegex(ValueError,'unsupported operation'):
                trace([(0x100,op,args)],b'\0')
        with self.assertRaisesRegex(ValueError,'budget'):
            trace([(0x100,'cmp','r0, #0'),(0x104,'bne','#0x100')],b'\0')


if __name__=='__main__':unittest.main()
