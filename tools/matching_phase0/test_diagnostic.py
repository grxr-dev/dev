"""ROM-free ELF/comparison regression tests; synthetic sections, never game data."""
import struct
import unittest
from elf_function import function,compare


def elf(*,machine=40,value=4,size=8,relocation=False):
    names=b'\0.text\0.symtab\0.strtab\0.shstrtab\0.rel.text\0'
    strings=b'\0pilot\0'
    symbol=bytes(16)+struct.pack('<IIIBBH',1,value,size,0x12,0,1)
    data=bytearray(52);sections=[(0,0,0,0,0,0,0,0,0,0)]
    def section(name,kind,flags,payload,link=0,info=0,entsize=0):
        while len(data)%4:data.append(0)
        start=len(data);data.extend(payload)
        sections.append((names.index(name+b'\0'),kind,flags,0,start,len(payload),link,info,4,entsize))
    section(b'.text',1,6,b'HEADabcdefghTAIL')
    section(b'.symtab',2,0,symbol,3,1,16)
    section(b'.strtab',3,0,strings)
    section(b'.shstrtab',3,0,names)
    if relocation:section(b'.rel.text',9,0,struct.pack('<II',4,0x102),2,1,8)
    shoff=len(data)
    for s in sections:data.extend(struct.pack('<10I',*s))
    data[:52]=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+bytes(9),1,machine,1,0,0,shoff,0x5000000,52,0,0,40,len(sections),4)
    return bytes(data)


class DiagnosticTests(unittest.TestCase):
    def test_extracts_symbol_bounds_not_entire_text_or_byte_search(self):
        body,info=function(elf(),'pilot')
        self.assertEqual(body,b'abcdefgh');self.assertEqual(info['symbol_value'],4)
        self.assertEqual(info['symbol_size'],8);self.assertEqual(info['code_relocations'],0)

    def test_rejects_wrong_machine(self):
        with self.assertRaises(ValueError):function(elf(machine=62),'pilot')

    def test_rejects_thumb_function(self):
        with self.assertRaises(ValueError):function(elf(value=5),'pilot')

    def test_rejects_symbol_outside_section(self):
        with self.assertRaises(ValueError):function(elf(size=100),'pilot')

    def test_rejects_unresolved_code_relocation(self):
        with self.assertRaises(ValueError):function(elf(relocation=True),'pilot')

    def test_equal_changed_and_extra_bytes_are_distinguished(self):
        self.assertTrue(compare(b'ab',b'ab')['equal'])
        self.assertFalse(compare(b'ab',b'ac')['equal'])
        self.assertEqual(compare(b'ab',b'abc')['differences'],[{'offset':2,'expected':None,'actual':99}])

    def test_rejects_truncated_object_and_missing_symbol(self):
        with self.assertRaises(ValueError):function(elf()[:60],'pilot')
        with self.assertRaises(ValueError):function(elf(),'not-defined')


if __name__=='__main__':unittest.main()
