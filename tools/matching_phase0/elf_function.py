"""Small fail-closed ELF32-LE ARM relocatable symbol extractor, not a linker.

No ROM knowledge. Section/symbol bounds, ARM state and code relocations are
checked; .ARM.exidx metadata is reported separately from function instructions.
"""
import struct


def region(data, offset, size):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError('ELF range outside file')
    return data[offset:offset + size]


def string(data, offset):
    if not 0 <= offset < len(data):
        raise ValueError('ELF string offset')
    end = data.find(b'\0', offset)
    if end < 0:
        raise ValueError('unterminated ELF string')
    return data[offset:end].decode('ascii')


def function(data, name):
    header = struct.unpack('<16sHHIIIIIHHHHHH', region(data, 0, 52))
    ident, kind, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = header
    if ident[:7] != b'\x7fELF\x01\x01\x01' or kind != 1 or machine != 40 or version != 1:
        raise ValueError('expected ELF32 little-endian ARM ET_REL')
    if ehsize != 52 or shsize != 40 or not 0 < shnum < 4096 or not 0 <= shstr < shnum:
        raise ValueError('unsupported ELF section table')
    sections = []
    for i in range(shnum):
        values = struct.unpack('<10I', region(data, shoff + i * shsize, shsize))
        section = dict(zip(('name_offset','type','flags','address','offset','size','link','info','alignment','entry_size'), values))
        section['index'] = i
        section['data'] = b'' if section['type'] == 8 else region(data, section['offset'], section['size'])
        sections.append(section)
    names = sections[shstr]['data']
    for section in sections:
        section['name'] = string(names, section['name_offset'])
    found = []
    for table in sections:
        if table['type'] != 2:
            continue
        if table['entry_size'] != 16 or table['size'] % 16 or not 0 <= table['link'] < shnum:
            raise ValueError('invalid ELF symbol table')
        strings = sections[table['link']]['data']
        for offset in range(0, table['size'], 16):
            n, value, size, info, other, section_index = struct.unpack_from('<IIIBBH', table['data'], offset)
            if string(strings, n) != name:
                continue
            if info & 15 != 2 or not 0 < section_index < shnum or value & 3:
                raise ValueError('symbol must be a defined word-aligned ARM function, not Thumb')
            section = sections[section_index]
            if section['type'] != 1 or not section['flags'] & 4 or section['address'] != 0 or not 0 < size <= 4096:
                raise ValueError('invalid executable function section/bounds')
            body = region(section['data'], value, size)
            relocs = []
            for rel in sections:
                if rel['type'] not in (4, 9):
                    continue
                width = 12 if rel['type'] == 4 else 8
                if rel['entry_size'] != width or rel['size'] % width:
                    raise ValueError('invalid relocation section')
                for j in range(0, rel['size'], width):
                    where, rinfo = struct.unpack_from('<II', rel['data'], j)
                    relocs.append({'section':rel['name'],'target_section':rel['info'],
                                   'offset':where,'type':rinfo & 255,
                                   'in_function':rel['info'] == section_index and value <= where < value + size})
            found.append((body, {'symbol':name,'section':section['name'],'section_index':section_index,
                                'symbol_value':value,'symbol_size':size,'object_file_offset':section['offset'] + value,
                                'elf_flags':hex(flags),'relocations':relocs,
                                'code_relocations':sum(r['in_function'] for r in relocs)}))
    if len(found) != 1:
        raise ValueError('expected exactly one named function definition')
    if found[0][1]['code_relocations']:
        raise ValueError('unresolved function-code relocations; byte-only comparison is insufficient')
    return found[0]


def compare(expected, actual):
    """Exact lengths and every byte; missing/extra bytes are mismatches too."""
    differences = [{'offset':i,'expected':expected[i] if i < len(expected) else None,
                    'actual':actual[i] if i < len(actual) else None}
                   for i in range(max(len(expected), len(actual)))
                   if (expected[i] if i < len(expected) else None) != (actual[i] if i < len(actual) else None)]
    return {'equal':not differences,'expected_size':len(expected),'actual_size':len(actual),'differences':differences}
