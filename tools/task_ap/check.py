"""Focused static-certificate negative checks. No guest execution or image mutation."""
import copy, json
import analyze as a
r=a.analyze()
assert json.loads((a.ROOT/'docs/BrainAge_TaskAP_Result.json').read_text())==r
assert (a.ROOT/'docs/BrainAge_TaskAP_PostAOStaticMap.md').read_text()==a.report(r)
def rejected(name,attribute,change):
 original=getattr(a,attribute);candidate=copy.deepcopy(original);change(candidate);setattr(a,attribute,candidate)
 try:
  try:a.analyze()
  except AssertionError:print('PASS reject '+name)
  else:raise RuntimeError('accepted '+name)
 finally:setattr(a,attribute,original)
rejected('wrong ROM opcode','FACTS',lambda x:x.__setitem__(0,(x[0][0],x[0][1]^1,x[0][2])))
rejected('divergent branch predicate','FLAG_CHANGES',lambda x:x.__setitem__(0x20672b0,[1,0,0,0]))
rejected('wrong store address','STORES',lambda x:x.__setitem__(0,(x[0][0],0x7c0,*x[0][2:])))
rejected('wrong store source value','STORES',lambda x:x.__setitem__(0,(*x[0][:4],1)))
rejected('wrong stack restoration','CHANGES',lambda x:x[0x2067d60].__setitem__(13,0x27e3b08))
print('PASS exact certificate/report reproducibility; five static negative checks; zero guest dispatches')
