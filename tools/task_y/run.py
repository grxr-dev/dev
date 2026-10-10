"""One frozen SDL gesture into a disposable original publication boundary; never accept an answer."""
import argparse,hashlib,json,os,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(data):return hashlib.sha256(data).hexdigest()
def rows(path):return [json.loads(line) for line in path.read_text().splitlines(keepends=True) if line.endswith('\n')] if path.exists() else []
def wait(predicate,seconds=45):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.05)
    raise TimeoutError('bounded Task Y observation timeout')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--disabled',action='store_true');parser.add_argument('--port',type=int,default=19889);args=parser.parse_args()
    source=ROOT/'local/task-g/session-001/11-answer-01-63';out=args.out.resolve();assert out.is_relative_to(ROOT/'local/task-y')
    definition=json.loads((ROOT/'tools/task_y/input.json').read_text());freeze=json.loads((ROOT/'tools/task_y/freeze.json').read_text())
    assert digest(json.dumps(definition,sort_keys=True,separators=(',',':')).encode())==freeze['sha256']
    initial=(source/'after.sav').read_bytes();state=(source/'checkpoint.state').read_bytes()
    assert digest(state)==freeze['checkpoint_sha256'] and digest(initial)=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
    command=json.loads((ROOT/'local/task-n/normal-enabled-002/session.json').read_text())['command']
    command[0]=str(ROOT/'build/task-o-sdl-runner/nds_runner.exe');command[1]=str(out);command[command.index('--serve')]='--interactive';command[command.index('--port')+1]=str(args.port);command[command.index('--save-path')+1]=str(out/'session.sav')
    assert '--force-tier3' not in command
    assert hashlib.sha1(Path(command[command.index('--rom')+1]).read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
    out.mkdir(parents=True,exist_ok=False)
    (out/'source.state').write_bytes(state)
    for name in ('initial.sav','session.sav'):(out/name).write_bytes(initial)
    for name in ('requests.jsonl','flash.jsonl','frontend-input.jsonl'):(out/name).touch()
    token=uuid.uuid4().hex;sequence=0
    env={key:value for key,value in os.environ.items() if not key.startswith(('NDS_TASK_','NDS_BRAINAGE_','NDS_FRONTEND_','NDS_FLASH_'))}
    env.update(NDS_TASK_Y_OUT=str(out),NDS_TASK_Y_PUBLICATION='0' if args.disabled else '1',NDS_TASK_O_START_STATE=str(out/'source.state'),NDS_TASK_F_RTC_PLUS_ONE_DAY='1',NDS_SDL_RENDER_DRIVER='software',NDS_TASK_O_WINDOW_CONTROL=str(out/'window-control.txt'),NDS_TASK_O_CONTROL_TOKEN=token,NDS_TASK_O_FRONTEND_TRACE=str(out/'frontend-input.jsonl'),NDS_TASK_C_TRACE=str(out/'requests.jsonl'),NDS_FLASH_TRACE=str(out/'flash.jsonl'))
    evidence={'definition_sha256':freeze['sha256'],'source_state_sha256':digest(state),'source_save_sha256':digest(initial),'command':command,'backend':'fixed title experiment, forced Tier-3 after SDL state restore','disabled':args.disabled,'input_events':[],'window':[],'runner_sha256':digest(Path(command[0]).read_bytes())}
    (out/'session.json').write_text(json.dumps(evidence,indent=2)+'\n')
    with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
    evidence['pid']=process.pid
    def helper(action,*values):
        reply=subprocess.run([str(ROOT/'build/task-o-tools/window_probe.exe'),action,str(process.pid),command[0],*map(str,values)],capture_output=True,text=True,timeout=10)
        assert reply.returncode==0,reply.stderr
        value=json.loads(reply.stdout);evidence['window'].append(value);return value
    def observe(event):
        def check():
            data=rows(out/'audit.jsonl')
            assert not any(row['event']=='failure' for row in data),data[-1:]
            assert process.poll() in (None,0),'runner exited with failure before evidence'
            assert not (out/'requests.jsonl').stat().st_size and not (out/'flash.jsonl').stat().st_size,'STOP save activity'
            return next((row for row in data if row['event']==event),None)
        return wait(check)
    def capture(label):
        helper('capture',out/(label+'-window.bmp'),'print')
    try:
        def window_ready():
            assert process.poll() is None,'runner exited during window startup'
            try:return helper('observe')
            except AssertionError as error:
                if 'expected exactly one visible process-owned window' not in str(error):raise
                return None
        if args.disabled:
            observe('disabled_control')
        else:
            helper_window=wait(window_ready)
            assert helper_window['client']==[512,768]
            observe('panel_active');capture('initial')
            time.sleep(2)
            for index,stroke in enumerate(definition['strokes'],1):
                for kind,point in [(1,stroke[0]),*[(2,point) for point in stroke[1:]],(0,stroke[-1])]:
                    sequence+=1;client=[point[0]*2,(192+point[1])*2]
                    temporary=out/'window-control.next';temporary.write_text(f'{token} {sequence} {kind} {client[0]} {client[1]}\n');temporary.replace(out/'window-control.txt')
                    wait(lambda:any(row.get('control_sequence')==sequence for row in rows(out/'frontend-input.jsonl')))
                    time.sleep(.12)
                    evidence['input_events'].append({'sequence':sequence,'kind':kind,'stroke':index,'ds':point,'client':client})
                wait(lambda:sum(row['event']=='recognition' for row in rows(out/'audit.jsonl'))==index)
                if index==1:capture('stroke1')
            observe('publication_blocked')
        evidence['exit_code']=process.wait(timeout=20);assert evidence['exit_code']==0
        final=(out/'final.sav').read_bytes()
        evidence['live_final_sha256']=digest(final);assert final==initial
        assert (source/'checkpoint.state').read_bytes()==state and (source/'after.sav').read_bytes()==initial
        assert not (out/'requests.jsonl').stat().st_size and not (out/'flash.jsonl').stat().st_size
        evidence['pass']=True
    except Exception as error:evidence['failure']=str(error);raise
    finally:
        if process.poll() is None:evidence['forced_cleanup']=True;process.terminate();process.wait(timeout=10)
        evidence['final_save_sha256']=digest((out/'session.sav').read_bytes());assert (out/'session.sav').read_bytes()==initial
        (out/'session.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({key:evidence.get(key) for key in ('pass','disabled','exit_code','live_final_sha256','final_save_sha256')}))
if __name__=='__main__':main()
