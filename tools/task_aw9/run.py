"""Exactly one AW9 launch. No retries, alternate profiles, normalization or fixture adapters."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
ATTEMPT=ROOT/'local/task-aw9/attempt-001'
BUILD=ROOT/'build/task-aw9-once'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(path):
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text().splitlines(keepends=True) if line.endswith('\n')]


def main():
    preflight=json.loads((ATTEMPT/'preflight.json').read_text())
    assert preflight['artifact_preflight_passed'] and not preflight['retry_authorized']
    assert (ATTEMPT.parent/'one-shot.lock').read_text().strip()==str(ATTEMPT)
    with (ATTEMPT/'launch.claim').open('x') as claim: claim.write('single AW9 launch reservation; never delete or retry\n')
    evidence={'task':'AW9','runner_launches':0,'retry_authorized':False,'events':[],'admitted':False,'exact_prefix_completed':False}
    process=None
    source=ROOT/'local/task-g/session-001/11-answer-01-63'
    state=None; save=None
    try:
        build=json.loads((BUILD/'build.json').read_text())
        assert build['safe'] and not build['fixture_adapters_present']
        executable=BUILD/'nds_runner.exe'
        assert digest(executable.read_bytes())==build['runner_sha256']
        for name,expected in build['preserved_artifacts'].items(): assert digest((ROOT/name).read_bytes())==expected,name
        for row in json.loads((BUILD/'compile.json').read_text()):
            assert digest(Path(row['source']).read_bytes())==row['source_sha256']
        for name,expected in build['overlay_changes'].items(): assert digest((BUILD/'source'/name).read_bytes())==expected,name
        assert digest((BUILD/'source/aw9_permission.h').read_bytes())==digest((ROOT/'tools/task_aw9/permission.h').read_bytes())
        state=(source/'checkpoint.state').read_bytes(); save=(source/'after.sav').read_bytes()
        assert digest(state)==preflight['checkpoint_sha256']
        assert digest(save)=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
        definition=json.loads((ROOT/'tools/task_y/input.json').read_text())
        assert digest(json.dumps(definition,sort_keys=True,separators=(',',':')).encode())==preflight['input_sha256']
        original=rows(ROOT/'local/task-aw5/capture-001/capture.jsonl')
        snapshot=next(row for row in original if row['event']=='canonical_snapshot')
        assert digest(bytes.fromhex(snapshot['canonical_hex']))=='0c4d6082c1a7eb2ec11c57447b26d5dd984599e12fdf6dc5b40465f68ac9304c'
        (ATTEMPT/'expected-entry.hex').write_text(snapshot['canonical_hex']+'\n')
        command=json.loads((ROOT/'local/task-n/normal-enabled-002/session.json').read_text())['command']
        command[0]=str(executable); command[1]=str(ATTEMPT)
        command[command.index('--serve')]='--interactive'
        command[command.index('--port')+1]='20259'
        command[command.index('--save-path')+1]=str(ATTEMPT/'session.sav')
        assert '--force-tier3' not in command
        rom=Path(command[command.index('--rom')+1])
        assert hashlib.sha1(rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
        (ATTEMPT/'source.state').write_bytes(state)
        for name in ['initial.sav','session.sav']: (ATTEMPT/name).write_bytes(save)
        for name in ['requests.jsonl','flash.jsonl','frontend-input.jsonl']: (ATTEMPT/name).touch(exist_ok=False)
        token=uuid.uuid4().hex
        permit=ATTEMPT/'runtime.permit'
        with permit.open('x') as ticket:
            ticket.write(preflight['certificate_payload_sha256']+' '+snapshot['sha256']+' '+token+'\n')
        environment={key:value for key,value in os.environ.items() if not key.startswith('NDS_')}
        environment.update(NDS_TASK_AU_OUT=str(ATTEMPT),NDS_TASK_AU_PUBLICATION='1',NDS_TASK_AW3_CAPTURE_ONLY='1',
            NDS_TASK_AW3_AUDIT=str(ATTEMPT/'capture.jsonl'),NDS_TASK_AW9_ONCE='1',NDS_TASK_AW9_PERMIT=str(permit),
            NDS_TASK_AW9_EXPECTED=str(ATTEMPT/'expected-entry.hex'),NDS_TASK_O_START_STATE=str(ATTEMPT/'source.state'),
            NDS_TASK_F_RTC_PLUS_ONE_DAY='1',NDS_SDL_RENDER_DRIVER='software',
            NDS_TASK_O_WINDOW_CONTROL=str(ATTEMPT/'window-control.txt'),NDS_TASK_O_CONTROL_TOKEN=token,
            NDS_TASK_O_FRONTEND_TRACE=str(ATTEMPT/'frontend-input.jsonl'),NDS_TASK_C_TRACE=str(ATTEMPT/'requests.jsonl'),
            NDS_FLASH_TRACE=str(ATTEMPT/'flash.jsonl'))
        evidence.update(command=command,runner_sha256=build['runner_sha256'],checkpoint_sha256=digest(state),
            source_save_sha256=digest(save),input_sha256=preflight['input_sha256'],runner_launches=1,
            backend='historical guarded AU replay; forced Tier-3 after restore; AW9 permission only after exact live preflight')
        (ATTEMPT/'session.json').write_text(json.dumps(evidence,indent=2)+'\n')
        with (ATTEMPT/'stdout.log').open('wb') as stdout,(ATTEMPT/'stderr.log').open('wb') as stderr:
            process=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        evidence['pid']=process.pid

        def safety():
            assert not (ATTEMPT/'requests.jsonl').stat().st_size and not (ATTEMPT/'flash.jsonl').stat().st_size,'STOP save activity'
            captured=rows(ATTEMPT/'capture.jsonl')
            failure=next((row for row in captured if row['event']=='failure'),None)
            if failure: raise RuntimeError(failure['reason'])
            assert process.poll() in (None,73),'one-shot process rejected or failed: '+str(process.poll())
            return captured

        def wait(predicate,seconds=90):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                safety()
                value=predicate()
                if value: return value
                time.sleep(.05)
            raise TimeoutError('single-attempt bounded observation timeout; no retry')

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
        assert evidence['exit_code']==73
        evidence['exact_prefix_completed']=True
    except Exception as error:
        evidence['first_failure']=str(error)
        if process is not None and process.poll() is None:
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                evidence['emergency_process_termination']=True
                process.terminate(); process.wait(timeout=10)
    finally:
        evidence['exit_code']=process.poll() if process is not None else None
        captured=rows(ATTEMPT/'capture.jsonl')
        evidence['admitted']=any(row['event']=='aw9_preflight_accepted' for row in captured)
        evidence['capture_audit_sha256']=digest((ATTEMPT/'capture.jsonl').read_bytes()) if (ATTEMPT/'capture.jsonl').exists() else None
        evidence['first_mismatch']=next((row['reason'] for row in captured if row['event']=='aw9_first_mismatch'),None)
        if state is not None:
            evidence['source_checkpoint_unchanged']=(source/'checkpoint.state').read_bytes()==state
            evidence['copied_checkpoint_unchanged']=(ATTEMPT/'source.state').read_bytes()==state if (ATTEMPT/'source.state').exists() else None
        if save is not None:
            evidence['source_save_unchanged']=(source/'after.sav').read_bytes()==save
            evidence['disposable_save_sha256']=digest((ATTEMPT/'session.sav').read_bytes()) if (ATTEMPT/'session.sav').exists() else None
        evidence['logical_request_trace_bytes']=(ATTEMPT/'requests.jsonl').stat().st_size if (ATTEMPT/'requests.jsonl').exists() else None
        evidence['flash_trace_bytes']=(ATTEMPT/'flash.jsonl').stat().st_size if (ATTEMPT/'flash.jsonl').exists() else None
        evidence['ordinary_final_save_written']=(ATTEMPT/'final.sav').exists()
        evidence['protected_artifacts_unchanged']=all(digest((ROOT/name).read_bytes())==wanted for name,wanted in build['preserved_artifacts'].items()) if 'build' in locals() else None
        (ATTEMPT/'session.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({key:evidence.get(key) for key in ['runner_launches','admitted','exact_prefix_completed','first_mismatch','first_failure','exit_code','emergency_process_termination']},indent=2))
    if not evidence['exact_prefix_completed']: raise SystemExit(1)


if __name__=='__main__':
    main()
