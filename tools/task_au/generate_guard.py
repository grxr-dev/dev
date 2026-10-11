"""Compile frozen AP into fixed tables; no guest dispatch."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
x=json.loads((ROOT/'tools/task_au/expected.json').read_text())
h=lambda s:int(s,16)
inst=x['prefix'];assert len(inst)==7
rs=[v['r_before'] for v in inst]+[x['AU']['r']]
fs=[v['nzcv_before'] for v in inst]+[x['AU']['nzcv']]
op=[v['opcode'] for v in inst]+[x['AU']['forbidden_next']['opcode']]
read=[];writes=[]
for i,v in enumerate(inst):
 read.append([i,h(v['pc']),h(v['pc']),4,h(v['opcode'])])
 for q in x['AU']['data_reads']:
  if q['pc']==v['pc']:read.append([i,h(q['pc']),h(q['address']),q['width'],h(q['value'])])
 for q in [q for q in x['AU']['stores'] if q['pc']==v['pc']]:
  writes.append([i,h(q['pc']),h(q['opcode']),h(q['address']),q['width'],14 if q['source']=='LR' else int(q['source'][1:]),h(q['after']),h(q['before'])])
assert len(read)==9 and len(writes)==1
s='#pragma once\n#include <cstdint>\n#include <cstddef>\nnamespace au_fixed {\n'
s+='inline constexpr uint32_t r[8][16]={'+','.join('{'+','.join(hex(h(n)) for n in row)+'}' for row in rs)+'};\n'
s+='inline constexpr uint32_t flags[8][4]={'+','.join('{'+','.join(map(str,row))+'}' for row in fs)+'};\n'
s+='inline constexpr uint32_t opcode[8]={'+','.join(op)+'};\n'
s+='struct Read {unsigned index;uint32_t pc,address;unsigned width;uint32_t value;};\n'
s+='inline constexpr Read reads[9]={'+','.join('{'+','.join(hex(n) for n in row)+'}' for row in read)+'};\n'
s+='struct Write {unsigned index;uint32_t pc,opcode,address;unsigned width,reg;uint32_t value,before;};\n'
s+='inline constexpr Write writes[1]={'+','.join('{'+','.join(hex(n) for n in row)+'}' for row in writes)+'};\n'
s+="""inline bool state(unsigned index,const uint32_t* regs,const unsigned* f,uint32_t op,uint64_t ordinal){
 if(index>7||ordinal!=281098001ull+index||op!=opcode[index])return false;
 for(unsigned i=0;i<16;++i)if(regs[i]!=r[index][i])return false;
 for(unsigned i=0;i<4;++i)if(f[i]!=flags[index][i])return false;
 return true;
}
inline bool dispatch(unsigned index){return index<7;}
inline bool read(unsigned count,unsigned index,uint32_t pc,uint32_t address,unsigned width){
 return count<9&&reads[count].index==index&&reads[count].pc==pc&&reads[count].address==address&&reads[count].width==width;
}
inline bool write(unsigned count,unsigned index,uint32_t pc,uint32_t op,uint32_t address,unsigned width,uint32_t value){
 return count<1&&writes[count].index==index&&writes[count].pc==pc&&writes[count].opcode==op&&writes[count].address==address&&writes[count].width==width&&writes[count].value==value;
}
inline unsigned read_count(unsigned index){unsigned n=0;for(auto& q:reads)if(q.index<index)++n;return n;}
inline unsigned write_count(unsigned index){unsigned n=0;for(auto& q:writes)if(q.index<index)++n;return n;}
}
"""
(ROOT/'tools/task_au/setup_guard.h').write_text(s)
print('AT compiled:8 observations,9 exact reads,1 ordered write')
