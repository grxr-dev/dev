"""Focused AR static certificate and negative checks; no guest execution."""
import copy,json
import analyze as a
r=a.analyze()
assert a.load(a.ROOT/'docs/BrainAge_TaskAR_Result.json')==r
assert (a.ROOT/'docs/BrainAge_TaskAR_Pending6753CStaticMap.md').read_text(encoding='utf-8')==a.report(r)
assert r['AS']['dtcm_changed_bytes']==21
# Independent fixed little-endian word ledger, including both idempotent events.
wanted=[(0x27e3ae8,0x20ea644,0x20e9a00),(0x27e3aec,0,0),(0x27e3af0,0x20e9a00,0xda),(0x27e3af4,0,0x20e9a00),(0x27e3af8,1,0x20e9a00),(0x27e3afc,0x20e9a00,0),(0x27e3b00,0x72,0),(0x27e3b04,0x20e9a00,0),(0x27e3b08,0x2026010,0x2026048),(0x27e3668,0x20e9f70,0x20e9f70)]
assert [(int(w['address'],16),int(w['before'],16),int(w['after'],16)) for w in r['stores']]==wanted
assert r['AS']['r']==list(map(a.hx,a.FINAL)) and r['AS']['nzcv']==[0,0,0,0]
def reject(label,attribute,change):
 old=getattr(a,attribute);candidate=copy.deepcopy(old);change(candidate);setattr(a,attribute,candidate)
 try:
  try:a.analyze()
  except AssertionError:print('PASS reject '+label)
  else:raise RuntimeError('accepted '+label)
 finally:setattr(a,attribute,old)
reject('pending BL opcode','FACTS',lambda x:x.__setitem__(0,(x[0][0],x[0][1]^1,*x[0][2:])))
reject('entry register','ENTRY',lambda x:x.__setitem__(0,x[0]+4))
reject('PUSH SP writeback','FACTS',lambda x:x[1][2].__setitem__(13,0x27e3aec))
reject('local allocation SP','FACTS',lambda x:x[3][2].__setitem__(13,0x27e3660))
reject('store source predecessor','FACTS',lambda x:x[6][2].__setitem__(0,0))
reject('read address','READS',lambda x:x.__setitem__(0x206755c,(0x2132780,*x[0x206755c][1:])))
reject('read value','READS',lambda x:x.__setitem__(0x206754c,(x[0x206754c][0],0x2000,*x[0x206754c][2:])))
print('PASS exact certificate/report, independent ten-word ledger, seven negative checks; zero guest dispatches')
