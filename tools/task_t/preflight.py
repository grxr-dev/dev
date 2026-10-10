"""Read-only Task T boundary preflight; menu selection only, no recognition."""
import argparse,hashlib,json,os,socket,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--port',type=int,default=19866);p.add_argument('--after-first',action='store_true');a=p.parse_args()
root=a.out.resolve();root.mkdir(parents=True,exist_ok=False)
repo=Path(__file__).resolve().parents[2];source=repo/'local/task-g/session-001/04-training-menu'
previous=json.loads((source.parent/'session.json').read_text());summary=json.loads((source/'summary.json').read_text())
rom=Path(previous['command'][previous['command'].index('--rom')+1]);assert hashlib.sha1(rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
save=(source/'after.sav').read_bytes();digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest(save)=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
state=(source/'checkpoint.state').read_bytes();(root/'source.state').write_bytes(state)
for name in ['initial.sav','disposable.sav']:(root/name).write_bytes(save)
for name in ['flash.jsonl','requests.jsonl']:(root/name).touch()
env={k:v for k,v in os.environ.items() if not k.startswith(('NDS_TASK_','NDS_BRAINAGE_','NDS_FLASH_'))}
env.update(NDS_FLASH_TRACE=str(root/'flash.jsonl'),NDS_TASK_C_TRACE=str(root/'requests.jsonl'),NDS_TASK_K_TRACE=str(root/'entries.jsonl'),NDS_TASK_J_TRACE=str(root/'host-observer.jsonl'),NDS_TASK_F_RTC_PLUS_ONE_DAY='1')
command=list(previous['command']);command[0]=str(repo/'build/task-s-runner/nds_runner.exe');command[1]=str(root);command[command.index('--port')+1]=str(a.port);command[command.index('--save-path')+1]=str(root/'disposable.sav')
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
  assert req({'cmd':'force_tier3','on':0})['forced_tier3']==False
  req({'cmd':'touch','x':166,'y':75,'down':True})
  stopped=req({'cmd':'run_to_pc','pc':0x0204d794 if a.after_first else 0x0204d790,'max_rounds':50000})
  if not stopped['reached']:
   req({'cmd':'touch','down':False})
   stopped=req({'cmd':'run_to_pc','pc':0x0204d794 if a.after_first else 0x0204d790,'max_rounds':1000000})
  finished=stopped['reached'];assert finished,stopped
  (root/'boundary-mainram.bin').write_bytes(bytes.fromhex(req({'cmd':'read_mem','cpu':9,'addr':0x02000000,'len':0x400000})['hex']))
  (root/'boundary-regs.json').write_text(json.dumps(req({'cmd':'regs','cpu':9}),indent=2))
  (root/'force-tier3.json').write_text(json.dumps(req({'cmd':'force_tier3'})))
  final=req({'cmd':'io_state'});after=bytes.fromhex(req({'cmd':'cart_save'})['hex']);(root/'after.sav').write_bytes(after)
  evidence={'finished':finished,'initial':initial,'final':final,'save_sha256_before':digest(save),'save_sha256_after':digest(after),'changed_bytes':sum(x!=y for x,y in zip(save,after)),'logical_events':(root/'requests.jsonl').stat().st_size,'flash_events':(root/'flash.jsonl').stat().st_size,'canonical_source_unchanged':(source/'after.sav').read_bytes()==save and (source/'checkpoint.state').read_bytes()==state}
  (root/'result.json').write_text(json.dumps(evidence,indent=2));print(json.dumps({k:v for k,v in evidence.items() if k not in ['initial','final']},indent=2))
  assert finished

finally:
 process.terminate();process.wait(timeout=10)
