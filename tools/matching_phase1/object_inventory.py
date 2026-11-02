"""Read-only ELF inventory. No relocation patching, object fabrication or linking."""
import struct
from elf_function import region,string


def inventory(data):
    header=struct.unpack('<16sHHIIIIIHHHHHH',region(data,0,52))
    if header[0][:7]!=b'\x7fELF\x01\x01\x01' or header[1:4]!=(1,40,1) or header[11]!=40 or not 0<header[12]<4096:
        raise ValueError('ARM ELF32 ET_REL required')
    sections=[]
    for index in range(header[12]):
        row=struct.unpack('<10I',region(data,header[6]+40*index,40))
        sections.append(dict(zip(('name_offset','type','flags','address','offset','size','link','info','alignment','entry_size'),row)))
    if not 0<=header[13]<len(sections):raise ValueError('section names index')
    names=sections[header[13]]
    name_data=region(data,names['offset'],names['size'])
    tables={};functions=[];undefined=[];mappings=[]
    for index,section in enumerate(sections):
        section['name']=string(name_data,section['name_offset'])
        if section['type']!=8:region(data,section['offset'],section['size'])
        if section['type']!=2:continue
        if section['entry_size']!=16 or section['size']%16 or not 0<=section['link']<len(sections):raise ValueError('symbol table')
        strings=sections[section['link']];text=region(data,strings['offset'],strings['size']);rows=[]
        for position in range(0,section['size'],16):
            name,value,size,info,other,defined=struct.unpack('<IIIBBH',region(data,section['offset']+position,16))
            symbol={'name':string(text,name),'value':value,'size':size,'type':info&15,'binding':info>>4,'section_index':defined}
            rows.append(symbol)
            if symbol['name'] and defined==0:undefined.append(symbol['name'])
            if symbol['name'].startswith(('$a','$t','$d')):mappings.append(symbol)
            if symbol['type']==2 and defined!=0:
                if not 0<defined<len(sections) or value&3 or not size or not sections[defined]['flags']&4:raise ValueError('function state/section')
                region(data,sections[defined]['offset']+value,size)
                if value+size>sections[defined]['size']:raise ValueError('function outside section')
                functions.append(symbol)
        tables[index]=rows
    relocations=[]
    for section in sections:
        if section['type'] not in (4,9):continue
        width=12 if section['type']==4 else 8
        if section['entry_size']!=width or section['size']%width or section['link'] not in tables or not 0<section['info']<len(sections):raise ValueError('relocation table')
        for position in range(0,section['size'],width):
            offset,info=struct.unpack('<II',region(data,section['offset']+position,8));table=tables[section['link']]
            if info>>8>=len(table) or offset>=sections[section['info']]['size']:raise ValueError('relocation bounds')
            relocations.append({'section':sections[section['info']]['name'],'offset':offset,'type':info&255,
                                'symbol':table[info>>8]['name'],'symbol_defined':table[info>>8]['section_index']!=0})
    names=[symbol['name'] for symbol in functions]
    if len(names)!=len(set(names)):raise ValueError('duplicate function symbols')
    return {'elf_type':'ET_REL','machine':'ARM','functions':functions,'undefined_symbols':sorted(set(undefined)),
            'sections':sections,'mapping_symbols':mappings,'relocations':relocations}


def layout(data,name):
    parsed=inventory(data)
    found=[symbol for symbol in parsed['functions'] if symbol['name']==name]
    if len(found)!=1:raise ValueError('one function definition required')
    symbol=found[0];start=symbol['value'];end=start+symbol['size']
    points=sorted((row['value'],row['name'][1]) for row in parsed['mapping_symbols']
        if row['section_index']==symbol['section_index'] and start<=row['value']<end)
    if not points or points[0]!=(start,'a') or len({point[0] for point in points})!=len(points):raise ValueError('missing/duplicate ARM entry mapping')
    spans=[]
    for index,(at,kind) in enumerate(points):
        limit=points[index+1][0] if index+1<len(points) else end
        if kind not in ('a','d') or at%4 or limit%4 or limit<=at:raise ValueError('unsupported ARM/data mapping span')
        spans.append({'offset':at-start,'size':limit-at,'kind':'ARM_CODE' if kind=='a' else 'LITERAL_DATA'})
    return spans
