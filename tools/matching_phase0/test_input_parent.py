"""ROM-free tests of the parent control model, not external library behavior."""
import unittest
from input_parent_pilot import parent_trace, split_pool, ADDRESS, CONTEXT


def fixture():
    # Authored semantic fixture; not original code or a stored disassembly.
    operations=[('push','{r4, r5, r6, lr}'),('sub','sp, sp, #0x20'),
        ('mov','r4, r0'),('mov',f'r0, #{CONTEXT}'),('bl','#0x0200aee8'),
        ('mov',f'r0, #{CONTEXT}'),('mov','r1, r4'),('bl','#0x0200abbc'),
        ('mov',f'r0, #{CONTEXT}'),('ldr','r5, [r0, #0x20]'),('ldr','r6, [r0, #0x24]'),
        ('sub','r5, r6, r5'),('mov','r0, r4'),('bl','#0x020665cc'),('cmp','r0, #0'),
        ('beq',f'#{ADDRESS+23*4}'),('mov',f'r0, #{CONTEXT}'),('mov','r1, sp'),
        ('mov','r2, #0x20'),('bl','#0x0200aa5c'),('ldr','r0, [sp]'),
        ('lsr','r5, r0, #8'),('b',f'#{ADDRESS+23*4}'),
        ('mov',f'r0, #{CONTEXT}'),('bl','#0x0200ab7c'),('mov','r0, r5'),
        ('add','sp, sp, #0x20'),('pop','{r4, r5, r6, pc}')]
    return [(ADDRESS+4*i,op,args) for i,(op,args) in enumerate(operations)]


def scenario(**kwargs):
    values=dict(predicate=0,start=0x20,end=0x100,header=0x87654321)
    values.update(kwargs)
    return parent_trace(fixture(),{'address':'0x100'},**values)


class ParentTests(unittest.TestCase):
    def test_false_path_uses_snapshot_not_later_mutated_context(self):
        result=scenario(initialize_header=False)
        self.assertEqual(result['return'],0xe0)
        self.assertEqual([c['target'] for c in result['calls']],['0x200aee8','0x200abbc','0x20665cc','0x200ab7c'])

    def test_true_path_uses_unsigned_header_shift_ignores_return_codes(self):
        result=scenario(predicate=1,prepare_result=0,read_result=0)
        self.assertEqual(result['return'],0x876543)
        self.assertEqual(result['calls'][3],{'target':'0x200aa5c','args':[CONTEXT,'frame+0',32]})

    def test_zero_header_and_wrapped_difference(self):
        self.assertEqual(scenario(predicate=1,header=0)['return'],0)
        self.assertEqual(scenario(start=0x100,end=0x80)['return'],0xffffff80)

    def test_uninitialized_header_is_not_given_fabricated_value(self):
        with self.assertRaisesRegex(ValueError,'uninitialized'):scenario(predicate=1,initialize_header=False)

    def test_unknown_predicate_and_call_rejected(self):
        with self.assertRaises(ValueError):scenario(predicate=2)
        rows=fixture();rows[4]=(rows[4][0],'bl','#0x1234')
        with self.assertRaisesRegex(ValueError,'unapproved'):
            parent_trace(rows,{'address':'0x100'},predicate=0,start=0,end=0,header=0)

    def test_literal_data_is_not_silently_decoded_as_instruction(self):
        # Generated ARM LDR r0,[pc,#0]; BX LR; final explicit context word.
        import struct
        rows,pool=split_pool(struct.pack('<III',0xe59f0000,0xe12fff1e,CONTEXT))
        self.assertEqual(len(rows),2)
        self.assertEqual(pool['address'],hex(ADDRESS+8))
        with self.assertRaises(ValueError):split_pool(struct.pack('<III',0xe59f0000,0xe12fff1e,0))


if __name__=='__main__':unittest.main()
