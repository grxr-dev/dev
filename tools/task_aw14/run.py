"""Single authorized AW14 replay/capture. No retry, status read or tail continuation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
from common import ROOT, ATTEMPT, BUILD, ENTRY, load, preserved, require, rows, sha


def main():
    preflight=load(ATTEMPT/'preflight.json')
    require(preflight['artifact_preflight_passed'] and not preflight['retry_authorized'],'preflight/attempt guard')
    require((ATTEMPT.parent/'one-shot.lock').read_text().strip()==str(ATTEMPT),'attempt reservation')
    with (ATTEMPT/'launch.claim').open('x') as claim:
        claim.write('single AW14 authorized replay/capture launch; never delete or retry\n')
    evidence={'task':'AW14','runner_launches':0,'retry_authorized':False,'events':[],'admitted':False,'fence_success':False}
    process=None
    state=None
    save=None
    source=ROOT/'local/task-g/session-001/11-answer-01-63'
    try:
        build=load(BUILD/'build.json')
        require(build['safe'] and not build['fixture_adapters_present'],'safe private build required')
        executable=BUILD/'nds_runner.exe'
        require(sha(executable)==build['runner_sha256'] and sha(BUILD/'SDL3.dll')==build['runtime_dll_sha256'],'binary/DLL identity')
        preserved(preflight['protected_artifacts'])
        for name,identity in build['helper_sha256'].items():
            require(sha(ROOT/'tools/task_aw14'/name)==identity,'helper changed after build: '+name)
        for row in load(BUILD/'compile.json'):
            require(sha(row['source'])==row['source_sha256'] and row['exit']==0,'compiled native source changed')
        for name,identity in build['overlay_changes'].items():
            require(sha(BUILD/'source'/name)==identity,'overlay changed: '+name)
        state=(source/'checkpoint.state').read_bytes()
        save=(source/'after.sav').read_bytes()
        require(hashlib.sha256(state).hexdigest()==preflight['checkpoint_sha256'],'source checkpoint changed')
        require(hashlib.sha256(save).hexdigest()=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb','source save changed')
        definition=load(ROOT/'tools/task_y/input.json')
        require(hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()==preflight['input_sha256'],'input changed')
        expected=(ROOT/'local/task-aw9/attempt-001/expected-entry.hex').read_text().strip()
        require(hashlib.sha256(bytes.fromhex(expected)).hexdigest()==ENTRY,'historical comparison metadata changed')
        with (ATTEMPT/'expected-entry.hex').open('x') as output:
            output.write(expected+'\n')
        command=list(load(ROOT/'local/task-aw9/attempt-001/session.json')['command'])
        command[0]=str(executable); command[1]=str(ATTEMPT)
        command[command.index('--port')+1]='20264'
        command[command.index('--save-path')+1]=str(ATTEMPT/'session.sav')
        require('--interactive' in command and '--force-tier3' not in command,'historical launch mode')
        rom=Path(command[command.index('--rom')+1])
        require(hashlib.sha1(rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2','ROM changed before launch')
        for name,data in [('source.state',state),('initial.sav',save),('session.sav',save)]:
            with (ATTEMPT/name).open('xb') as output:
                output.write(data)
        for name in ['requests.jsonl','flash.jsonl','frontend-input.jsonl']:
            (ATTEMPT/name).touch(exist_ok=False)
        token=uuid.uuid4().hex
        permit=ATTEMPT/'runtime.permit'
        with permit.open('x') as output:
            output.write(preflight['contract_sha256']+' '+ENTRY+' '+token+'\n')
        environment={key:value for key,value in os.environ.items() if not key.startswith('NDS_')}
        environment.update(NDS_TASK_AU_OUT=str(ATTEMPT),NDS_TASK_AU_PUBLICATION='1',NDS_TASK_AW3_CAPTURE_ONLY='1',
            NDS_TASK_AW3_AUDIT=str(ATTEMPT/'capture.jsonl'),NDS_TASK_AW14_ONCE='1',NDS_TASK_AW14_PERMIT=str(permit),
            NDS_TASK_AW14_EXPECTED=str(ATTEMPT/'expected-entry.hex'),NDS_TASK_O_START_STATE=str(ATTEMPT/'source.state'),
            NDS_TASK_F_RTC_PLUS_ONE_DAY='1',NDS_SDL_RENDER_DRIVER='software',
            NDS_TASK_O_WINDOW_CONTROL=str(ATTEMPT/'window-control.txt'),NDS_TASK_O_CONTROL_TOKEN=token,
            NDS_TASK_O_FRONTEND_TRACE=str(ATTEMPT/'frontend-input.jsonl'),NDS_TASK_C_TRACE=str(ATTEMPT/'requests.jsonl'),
            NDS_FLASH_TRACE=str(ATTEMPT/'flash.jsonl'))
        evidence.update(command=command,runner_sha256=build['runner_sha256'],checkpoint_sha256=preflight['checkpoint_sha256'],
                        input_sha256=preflight['input_sha256'],source_save_sha256=hashlib.sha256(save).hexdigest(),
                        contract_sha256=preflight['contract_sha256'],runner_launches=1)
        (ATTEMPT/'session.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
        with (ATTEMPT/'stdout.log').open('xb') as stdout,(ATTEMPT/'stderr.log').open('xb') as stderr:
            process=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        evidence['pid']=process.pid

        def safety():
            require(not (ATTEMPT/'requests.jsonl').stat().st_size and not (ATTEMPT/'flash.jsonl').stat().st_size,'STOP: save activity')
            captured=rows(ATTEMPT/'capture.jsonl')
            failure=next((row for row in captured if row['event'] in ['failure','observer_failure']),None)
            if failure:
                raise RuntimeError(failure.get('reason','observer failure'))
            require(process.poll() in (None,73),'one-shot runtime rejected: '+str(process.poll()))
            return captured

        def wait(predicate,seconds=90):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                safety()
                value=predicate()
                if value:
                    return value
                time.sleep(.05)
            raise TimeoutError('one-shot bounded observation timeout; no retry')

        wait(lambda:any(row['event']=='panel_active' for row in rows(ATTEMPT/'audit.jsonl')))
        time.sleep(2)
        sequence=0
        for stroke_index,stroke in enumerate(definition['strokes'],1):
            for kind,point in [(1,stroke[0]),*[(2,point) for point in stroke[1:]],(0,stroke[-1])]:
                safety(); sequence+=1
                client=[point[0]*2,(192+point[1])*2]
                temporary=ATTEMPT/'window-control.next'
                temporary.write_text(f'{token} {sequence} {kind} {client[0]} {client[1]}\n')
                temporary.replace(ATTEMPT/'window-control.txt')
                evidence['events'].append({'sequence':sequence,'kind':kind,'stroke':stroke_index,'ds':point,'client':client})
                wait(lambda:any(row.get('control_sequence')==sequence for row in rows(ATTEMPT/'frontend-input.jsonl')))
                time.sleep(.12)
            wait(lambda:sum(row['event']=='recognition' for row in rows(ATTEMPT/'audit.jsonl'))==stroke_index)
        wait(lambda:any(row['event']=='terminal' for row in rows(ATTEMPT/'capture.jsonl')))
        evidence['exit_code']=process.wait(timeout=10)
        require(evidence['exit_code']==73,'terminal exit mismatch')
        evidence['fence_success']=True
    except Exception as error:
        evidence['first_failure']=str(error)
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                evidence['emergency_process_termination']=True
                process.terminate(); process.wait(timeout=10)
    finally:
        evidence['exit_code']=process.poll() if process is not None else None
        captured=rows(ATTEMPT/'capture.jsonl')
        evidence['admitted']=any(row['event']=='aw14_preflight_accepted' for row in captured)
        evidence['runtime_first_failure']=next((row.get('reason','observer failure') for row in captured if row['event'] in ['failure','observer_failure']),None)
        evidence['capture_audit_sha256']=sha(ATTEMPT/'capture.jsonl') if (ATTEMPT/'capture.jsonl').exists() else None
        if state is not None:
            evidence['source_checkpoint_unchanged']=(source/'checkpoint.state').read_bytes()==state
            evidence['copied_checkpoint_unchanged']=(ATTEMPT/'source.state').read_bytes()==state if (ATTEMPT/'source.state').exists() else None
        if save is not None:
            evidence['source_save_unchanged']=(source/'after.sav').read_bytes()==save
            evidence['disposable_save_sha256']=sha(ATTEMPT/'session.sav') if (ATTEMPT/'session.sav').exists() else None
        evidence['logical_request_trace_bytes']=(ATTEMPT/'requests.jsonl').stat().st_size if (ATTEMPT/'requests.jsonl').exists() else None
        evidence['flash_trace_bytes']=(ATTEMPT/'flash.jsonl').stat().st_size if (ATTEMPT/'flash.jsonl').exists() else None
        evidence['ordinary_final_save_written']=(ATTEMPT/'final.sav').exists()
        try:
            preserved(preflight['protected_artifacts'])
            evidence['protected_artifacts_unchanged']=True
        except Exception as error:
            evidence['protected_artifacts_unchanged']=False
            evidence.setdefault('first_failure',str(error))
        (ATTEMPT/'session.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:evidence.get(key) for key in ['runner_launches','admitted','fence_success','runtime_first_failure','first_failure','exit_code','emergency_process_termination']},indent=2))
    if not evidence['fence_success']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
