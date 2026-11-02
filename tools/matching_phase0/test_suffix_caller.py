"""ROM-free safe-domain and explicit ARM-call relocation regression tests."""
import struct
import unittest
from elf_function import function
from suffix_caller_pilot import valid_object


def call_object(kind=28, word=0xebfffffe):
    names=b'\0.text\0.symtab\0.strtab\0.shstrtab\0.rel.text\0'
    strings=b'\0pilot\0helper\0'
    symbols=bytes(16)+struct.pack('<IIIBBH',1,4,8,0x12,0,1)+struct.pack('<IIIBBH',7,0,0,0x12,0,0)
    data=bytearray(52);sections=[(0,)*10]
    def section(name,typ,flags,payload,link=0,info=0,entsize=0):
        while len(data)%4:data.append(0)
        start=len(data);data.extend(payload)
        sections.append((names.index(name+b'\0'),typ,flags,0,start,len(payload),link,info,4,entsize))
    section(b'.text',1,6,b'HEAD'+struct.pack('<II',word,0xe12fff1e)+b'TAIL')
    section(b'.symtab',2,0,symbols,3,1,16)
    section(b'.strtab',3,0,strings)
    section(b'.shstrtab',3,0,names)
    section(b'.rel.text',9,0,struct.pack('<II',4,(2<<8)|kind),2,1,8)
    shoff=len(data)
    for s in sections:data.extend(struct.pack('<10I',*s))
    data[:52]=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+bytes(9),1,40,1,0,0,shoff,0x5000000,52,0,0,40,len(sections),4)
    return bytes(data)


class SuffixCallerTests(unittest.TestCase):
    def test_explicit_call_resolution_forward_backward(self):
        for target in (0x02000040,0x01ffffe0):
            body,info=function(call_object(),'pilot',arm_calls={'helper':target},runtime_address=0x02000000)
            word=struct.unpack_from('<I',body)[0];imm=word&0xffffff
            if imm&(1<<23):imm-=1<<24
            self.assertEqual(0x02000000+8+4*imm,target)
            self.assertEqual(info['code_relocations'],1)
            self.assertEqual(info['resolved_code_relocations'],1)
            self.assertEqual(body[4:],struct.pack('<I',0xe12fff1e))

    def test_relocation_stays_closed_by_default(self):
        with self.assertRaisesRegex(ValueError,'unresolved'):function(call_object(),'pilot')

    def test_wrong_symbol_type_addend_and_target_rejected(self):
        for data,calls,pc in ((call_object(),{'wrong':0x02000040},0x02000000),
                              (call_object(kind=2),{'helper':0x02000040},0x02000000),
                              (call_object(word=0xeb000000),{'helper':0x02000040},0x02000000),
                              (call_object(),{'helper':0x02000041},0x02000000),
                              (call_object(),{'helper':0x08000000},0x02000000),
                              (call_object(),{'helper':0x02000040},0x02000001)):
            with self.assertRaises(ValueError):function(data,'pilot',arm_calls=calls,runtime_address=pc)

    def test_short_null_unterminated_rejected_before_execution(self):
        for data in (None,b'',b'\0',b'x\0',b'xx\0',b'abc'):
            with self.assertRaises(ValueError):valid_object(data)

    def test_safe_domain_and_first_nul(self):
        self.assertEqual(valid_object(b'cmp\0'),3)
        self.assertEqual(valid_object(b'abc\0ignored'),3)
        self.assertEqual(valid_object(b'xcmp\0'),4)


if __name__=='__main__':unittest.main()
