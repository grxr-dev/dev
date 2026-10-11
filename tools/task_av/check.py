"""Static certificate/source checks only. Never launches guest/runtime code."""
import copy
import analyze as a
r=a.analyze()
assert r==a.load(a.ROOT/'docs/BrainAge_TaskAV_Result.json')
assert r['safety']==dict(guest_dispatches=0,runtime_mmio_accesses=0,guest_image_writes=0,event_service_calls=0,AW_started=False,input_hashes_unchanged=True)
w=r['AW']
assert w['instruction_count']==12 and w['stop_pc']=='0x020019B8'
assert len(w['mmio_ledger'])==6 and sum(x['direction']=='write' for x in w['mmio_ledger'])==5
assert w['conditional_cycle9']==3416875785 and w['final_deadline']==1708437913
assert w['final_deadline']*2-a.C0==105
# Independent conditional cycle/deadline arithmetic, no runtime execution.
cost=[8,1,8,1,3,8,8,8,4,4,3,8]
assert sum(cost[:11])==56 and sum(cost)==64
for index,deadline in zip([0,2,5,6,7],[1708437894,1708437899,1708437905,1708437909,1708437913]):
 assert (3416875721+sum(cost[:index]))//2+34==deadline
assert 3416875721+sum(cost)+3==1708437894*2
assert [56+15*i for i in range(5)]==[56,71,86,101,116]
assert 101 < 105 < 101+8 and 116>105 and 56+4*15+8+3+1==128
assert divmod(4096<<32,4096)==(1<<32,0)
negatives=[]
def reject(label,attribute,change):
 old=getattr(a,attribute);candidate=copy.deepcopy(old);change(candidate);setattr(a,attribute,candidate)
 try:
  try:a.analyze()
  except AssertionError:negatives.append(label)
  else:raise RuntimeError('accepted '+label)
 finally:setattr(a,attribute,old)
reject('AU entry argument','ENTRY',lambda x:x.__setitem__(0,0x2000))
reject('pending opcode','PATH',lambda x:x.__setitem__(0,(x[0][0],x[0][1]^1,*x[0][2:])))
reject('write timing','PATH',lambda x:x.__setitem__(0,(*x[0][:4],9)))
reject('literal pointer','LITERALS',lambda x:x.__setitem__(0x20019ac,0x400029c))
reject('denominator address','MMIO',lambda x:x.__setitem__(3,(x[3][0],0x400029c,*x[3][2:])))
reject('numerator source','MMIO',lambda x:x.__setitem__(2,(*x[2][:4],0x2000)))
reject('status value','MMIO',lambda x:x.__setitem__(5,(*x[5][:4],1)))
reject('LR result','PATH',lambda x:x[9][3].__setitem__(14,0x2001a28))
reject('poll mask','LOOKAHEAD',lambda x:x.__setitem__(0x20019b8,0xe2100901))
reject('instruction budget extension','PATH',lambda x:x.append((0x20019b8,0xe2100902,'ANDS',{0:0x8000},3)))
report=(a.ROOT/'docs/BrainAge_TaskAV_DividerMMIOSafetyMap.md').read_text(encoding='utf-8-sig')
for token in ['PARTIAL','3416875785','1708437913','not ready to execute','scheduler tail','Stopped after AV']:
 assert token in report,token
print('PASS committed evidence/ROM/source certificate; conditional timing and loop arithmetic; '+str(len(negatives))+' negative checks: '+', '.join(negatives))
print('ZERO guest execution, runtime MMIO, event service, or checkpoint/save mutation. AW not started.')
