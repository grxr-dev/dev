"""Focused static positives/negatives only; no guest or device execution."""
import copy
import analyze as a

r=a.analyze()
assert r==a.load(a.ROOT/'docs/BrainAge_TaskAT_Result.json')
u=r['AU']
assert u['pc_sequence']==['0x02067564','0x02001A14','0x02001A18','0x02001A1C','0x02001974','0x02001978','0x0200197C']
assert u['instruction_count']==7 and u['stop_pc']=='0x02001980'
assert [(d['address'],d['before'],d['after']) for d in u['dtcm_byte_diffs']]==[('0x027E3658',0xe0,0x68),('0x027E3659',0x7a,0x75)]
assert int(u['r'][13],16)==0x027e365c-8
assert int(u['r'][14],16)==0x02001a1c+4
assert u['mmio_accesses']==u['mainram_changed_bytes']==u['save_changed_bytes']==0
assert len(u['mapped_fields'])==35 and all(f['before']==f['after'] for f in u['mapped_fields'])
assert r['safety']==dict(guest_dispatches=0,runtime_mmio_accesses=0,guest_image_writes=0,AU_started=False,input_hashes_unchanged=True)
# Independently derive displacement, ARM rotated-immediate constants and offsets.
def ror32(x,n): return ((x>>n)|(x<<(32-n)))&0xffffffff if n else x
assert 0x02067564+8+((0xfe692a-0x1000000)<<2)==0x02001a14
for op,value in [(0xe3a03a01,0x1000),(0xe2100902,0x8000),(0xe3a00702,0x80000)]:
    assert ror32(op&255,((op>>8)&15)*2)==value
assert (a.WORDS[0x2001980]>>5)&3==1
assert (a.WORDS[0x20019b4]>>20)&1==1
for pc,pointer,offset,address in [(0x2001988,0x4000290,0,0x4000290),
                                (0x2001994,0x4000290,4,0x4000294),
                                (0x2001998,0x4000298,0,0x4000298),
                                (0x200199c,0x4000298,4,0x400029c),
                                (0x20019c8,0x40002a0,0,0x40002a0),
                                (0x20019cc,0x40002a0,4,0x40002a4)]:
    assert (a.WORDS[pc]&0xfff)==offset and pointer+offset==address
assert a.target(0x20019bc,0x1afffffc)==0x20019b4
# Arithmetic implication, not a call to hardware implementation.
numerator=4096*(2**32)
quotient,remainder=divmod(numerator,4096)
assert (quotient&0xffffffff,quotient>>32,remainder)==(0,1,0)
assert ((quotient+524288)>>20)&0xffffffff==4096

def reject(label,attribute,change):
    old=getattr(a,attribute)
    candidate=copy.deepcopy(old)
    change(candidate)
    setattr(a,attribute,candidate)
    try:
        try: a.analyze()
        except AssertionError: print('PASS reject '+label)
        else: raise RuntimeError('accepted '+label)
    finally: setattr(a,attribute,old)
reject('pending BL opcode','PREFIX',lambda x:x.__setitem__(0,(x[0][0],x[0][1]^1,*x[0][2:])))
reject('AS argument','ENTRY',lambda x:x.__setitem__(0,0x2000))
reject('AS saved LR source','PREFIX',lambda x:x[0][2].__setitem__(14,0x206756c))
reject('saved-word SP','PREFIX',lambda x:x[1][2].__setitem__(13,0x27e3654))
reject('frame allocation','PREFIX',lambda x:x[2][2].__setitem__(13,0x27e3650))
reject('literal destination','PREFIX',lambda x:x[4][2].__setitem__(1,0x4000284))
reject('literal pointer','LITERALS',lambda x:x.__setitem__(0x20019a4,0x4000284))
reject('MMIO store width opcode','WORDS',lambda x:x.__setitem__(0x2001980,0xe5813000))
reject('poll mask opcode','WORDS',lambda x:x.__setitem__(0x20019b8,0xe2100901))
reject('MMIO contract value','MMIO',lambda x:x.__setitem__(0,(*x[0][:4],0,*x[0][5:])))
reject('AU terminal registers','FINAL',lambda x:x.__setitem__(12,0))
report=(a.ROOT/'docs/BrainAge_TaskAT_NestedMMIOStaticMap.md').read_text(encoding='utf-8-sig')
for token in ['seven original ARM instructions','02001980 / E1C130B0','027E3658','Astra Medium','no program-local upper bound']:
    assert token in report,token
print('PASS static certificate/report, independent operand/frame arithmetic, 11 negative checks; zero guest/device execution')
