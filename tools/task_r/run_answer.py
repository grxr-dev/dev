"""One original guest answer from a preserved Task G checkpoint; no custom host."""
import argparse,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'task_c'))
from digits import pen_paths
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'task_a'))
from probe_boot import write_frame
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--port',type=int,default=19865);a=p.parse_args()
root=a.out.resolve();root.mkdir(parents=True,exist_ok=False)
repo=Path(__file__).resolve().parents[2];source=repo/'local/task-g/session-001/11-answer-01-63'
previous=json.loads((source.parent/'session.json').read_text());summary=json.loads((source/'summary.json').read_text())
strokes=json.loads(json.dumps(pen_paths('4')))
assert strokes==json.loads((source.parent/'12-answer-02-4/summary.json').read_text())['strokes']
rom=Path(previous['command'][previous['command'].index('--rom')+1]);assert hashlib.sha1(rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
save=(source/'after.sav').read_bytes();digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest(save)=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
state=(source/'checkpoint.state').read_bytes();(root/'source.state').write_bytes(state)
for name in ['initial.sav','disposable.sav']:(root/name).write_bytes(save)
for name in ['flash.jsonl','requests.jsonl']:(root/name).touch()
env={k:v for k,v in os.environ.items() if not k.startswith(('NDS_TASK_','NDS_BRAINAGE_','NDS_FLASH_'))}
env.update(NDS_FLASH_TRACE=str(root/'flash.jsonl'),NDS_TASK_C_TRACE=str(root/'requests.jsonl'),NDS_TASK_R_TRACE=str(root/'recognition.jsonl'),NDS_TASK_F_RTC_PLUS_ONE_DAY='1')
command=list(previous['command']);command[0]=str(repo/'build/task-r-runner/nds_runner.exe');command[1]=str(root);command[command.index('--port')+1]=str(a.port);command[command.index('--save-path')+1]=str(root/'disposable.sav')
assert '--force-tier3' in command
(root/'session.json').write_text(json.dumps({'source':str(source),'state_sha256':digest(state),'command':command},indent=2))
with (root/'stdout.log').open('wb') as out,(root/'stderr.log').open('wb') as err:
 process=subprocess.Popen(command,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 for _ in range(100):
  try:conn=socket.create_connection(('127.0.0.1',a.port),timeout=2);break
  except OSError:
   if process.poll() is not None:raise RuntimeError('runner exited')
   time.sleep(.1)
 else:raise RuntimeError('server unavailable')
 with conn,(root/'debug.jsonl').open('w') as log:
  conn.settimeout(120);wire=conn.makefile('rwb')
  def req(q):
   wire.write(json.dumps(q).encode()+b'\n');wire.flush();r=json.loads(wire.readline());log.write(json.dumps({'request':q,'response':r})+'\n');log.flush();assert 'error' not in r,r;return r
  req({'cmd':'state_load','path':str(root/'source.state')});initial=req({'cmd':'io_state'})
  for k in ['cyc9','cyc7','insn9','insn7']:assert initial['counts'][k]==summary['final']['counts'][k]
  assert bytes.fromhex(req({'cmd':'cart_save'})['hex'])==save
  def frames(label):
   for engine in ['A','B']:
    f=req({'cmd':'framebuffer','engine':engine});write_frame(root/(label+'-'+engine+'.png'),f)
  frames('before')
  current=initial['counts']['cyc9'];start=current;pos=0;events=[];accepted=False;exercise=None
  def monitor():
   global pos,accepted,exercise
   assert (root/'flash.jsonl').stat().st_size==0,'STOP: Flash activity'
   assert (root/'requests.jsonl').stat().st_size==0,'STOP: logical save activity'
   path=root/'recognition.jsonl'
   if path.exists():
    with path.open('rb') as f:
     f.seek(pos)
     for line in f:
      e=json.loads(line)
      if e['pc']==0x020265f8:accepted=True;exercise=e['exercise']
     pos=f.tell()
  def advance(delta):
   global current
   goal=current+delta
   while current<goal and not accepted:
    r=req({'cmd':'run_cycles','arm9':min(current+100000,goal)})
    if not r['reached']:r=req({'cmd':'run_rounds','count':2048})
    assert r['cycles'][0]>current,'no progress';current=r['cycles'][0];monitor()
  for index,stroke in enumerate(strokes):
   for n,(x,y) in enumerate(stroke):
    assert not accepted,'accepted before full intended path'
    req({'cmd':'touch','x':x,'y':y,'down':True});events.append({'kind':'down' if n==0 else 'motion','stroke':index,'xy':[x,y],'cycle9':current});advance(2000000)
   req({'cmd':'touch','down':False});events.append({'kind':'up','stroke':index,'cycle9':current});advance(3000000)
  while not accepted and current<start+85000000:advance(1000000)
  monitor();final=req({'cmd':'io_state'});after=bytes.fromhex(req({'cmd':'cart_save'})['hex']);(root/'after.sav').write_bytes(after)
  frames('after')
  evidence={'accepted_path_observed':accepted,'exercise':exercise,'initial':initial,'final':final,'touch_events':events,'save_sha256_before':digest(save),'save_sha256_after':digest(after),'changed_bytes':sum(x!=y for x,y in zip(save,after)),'logical_events':(root/'requests.jsonl').stat().st_size,'flash_events':(root/'flash.jsonl').stat().st_size,'canonical_source_unchanged':(source/'after.sav').read_bytes()==save and (source/'checkpoint.state').read_bytes()==state}
  if exercise:evidence['exercise_after']=req({'cmd':'read_mem','cpu':9,'addr':exercise,'len':0x54})
  (root/'result.json').write_text(json.dumps(evidence,indent=2));print(json.dumps({k:v for k,v in evidence.items() if k not in ['initial','final','touch_events','exercise_after']},indent=2))
finally:
 process.terminate();process.wait(timeout=10)
