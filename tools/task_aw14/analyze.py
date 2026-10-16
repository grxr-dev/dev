"""Read-only validation of the single AW14 attempt; never launches or repairs it."""
import hashlib
import json
import sys
from common import ROOT, ATTEMPT, BUILD, ENTRY, TERMINAL, load, module, preserved, require, rows, sha, write_new


def observations(audit):
    result=[]
    snapshot=None
    for record in audit:
        if record['event']=='canonical_snapshot':
            require(hashlib.sha256(bytes.fromhex(record['canonical_hex'])).hexdigest()==record['sha256'],'canonical audit identity')
            snapshot=record
        elif record['event']=='observation':
            require(snapshot is not None,'observation missing snapshot')
            result.append((record,snapshot))
    return result


def main():
    session=load(ATTEMPT/'session.json')
    require(session['runner_launches']==1 and not session['retry_authorized'],'single runtime attempt')
    require((ATTEMPT/'launch.claim').exists(),'launch claim missing')
    preflight=load(ATTEMPT/'preflight.json')
    preserved(preflight['protected_artifacts'])
    build=load(BUILD/'build.json')
    require(sha(BUILD/'nds_runner.exe')==session['runner_sha256']==build['runner_sha256'],'runner identity')
    audit=rows(ATTEMPT/'capture.jsonl')
    checks=module('aw14_aw6_chain',ROOT/'tools/task_aw6/check.py')
    require(checks.verify_chain(audit)==len(observations(audit)),'original controller chain')
    live=observations(audit)
    reference=observations(rows(ROOT/'local/task-aw9/attempt-001/capture.jsonl'))
    prefix_match=len(live)==69 and live==reference and all(event['accepted'] for event,snapshot in live)
    sys.path.insert(0,str(ROOT/'tools/task_aw12'))
    fence_checks=module('aw14_aw12_audit',ROOT/'tools/task_aw12/check.py')
    state=__import__('state')
    chain=None
    if session['fence_success']:
        require(prefix_match,'prefix transcript mismatch')
        end=next(index for index,record in enumerate(audit) if record['event']=='observation' and record['index']==68)
        suffix=audit[end-1:]
        path=ATTEMPT/'fence-only.jsonl'
        with path.open('x',encoding='utf-8') as output:
            output.write('\n'.join(json.dumps(record) for record in suffix)+'\n')
        chain=fence_checks.inspect_audit(path,True)
    gpu_snapshots=[record for record in audit if record['event']=='gpu_snapshot']
    gpu=None
    if gpu_snapshots:
        fields,identities=state.decode(bytes.fromhex(gpu_snapshots[0]['canonical_hex']))
        require(not identities,'unexpected GPU identity domain')
        gpu={name:value for name,width,value in fields}
        require(all(record==gpu_snapshots[0] for record in gpu_snapshots),'GPU repeat observation changed')
    events=['yield_requested','tier3_exit','unwind_preserved','slice_consumed','slot_saved',
            'pre_device_fence','gpu_observed','scheduler_admitted_capture_only']
    transfer=[record for record in audit if record['event'] in events]
    failure=next((record.get('reason') for record in audit if record['event']=='failure'),None)
    kinds={kind:sum(event['kind']==kind for event,snapshot in live) for kind in range(10)}
    forbidden=[event for event,snapshot in live if event['pc']==0x020019b4]
    writes=[]
    for event,snapshot in live:
        if event['kind']==2 and event['write']:
            fields,_=state.decode(bytes.fromhex(snapshot['canonical_hex']))
            values={name:value for name,width,value in fields}
            writes.append({key:event[key] for key in ['pc','address','width','value']})
            writes[-1].update(cycle=values['cycle9'],deadline=values['div.deadline'],serial=values['capture.serial'])
    final_fields=None
    if live:
        fields,identities=state.decode(bytes.fromhex(live[-1][1]['canonical_hex']))
        final_fields={name:value for name,width,value in fields}
    before=rows(ATTEMPT/'audit.jsonl')
    recognition=[record['integer'] for record in before if record['event']=='recognition']
    frontend=rows(ATTEMPT/'frontend-input.jsonl')
    queued=[record for record in frontend if 'control_sequence' in record]
    save_safe=all(session.get(name) for name in ['source_checkpoint_unchanged','copied_checkpoint_unchanged','source_save_unchanged','protected_artifacts_unchanged'])
    save_safe=save_safe and session['logical_request_trace_bytes']==session['flash_trace_bytes']==0 and not session['ordinary_final_save_written']
    save_safe=save_safe and session['disposable_save_sha256']=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
    require(save_safe,'save/checkpoint/protected evidence invariance failed')
    if session['fence_success']:
        require(session['exit_code']==73 and not session.get('emergency_process_termination') and not failure,'terminal disposal mismatch')
        require(recognition==[2,4] and [record['control_sequence'] for record in queued]==list(range(1,11)),'historical SDL input path mismatch')
        require(sum(record['event']=='aw14_capture_armed' for record in audit)==1 and
                sum(record['event']=='aw14_preflight_accepted' for record in audit)==1 and
                sum(record['event']=='aw14_runtime_permission' for record in audit)==1,'one-use admission mismatch')
        require((ATTEMPT/'runtime.permit.claimed').exists(),'fresh runtime claim absent')
        require(kinds=={0:11,1:18,2:18,3:11,4:11,5:0,6:0,7:0,8:0,9:0} and not forbidden,'unexpected protected service/guest instruction')
        require(final_fields['cycle9']==3416875777 and final_fields['slice_cap']==3416875778,'terminal timing')
    classification='FULL PASS' if session['fence_success'] and chain else 'PARTIAL' if prefix_match else 'BLOCKED'
    result={'task':'AW14','classification':classification,'runner_launches':session['runner_launches'],'retries':0,
            'source_artifact_preflight_passed':preflight['artifact_preflight_passed'],'live_prefix_admitted':session['admitted'],
            'prefix_observations':len(live),'prefix_full_state_event_chain_exact_AW9_match':prefix_match,
            'prerequisite_instruction_count':kinds[0],'prerequisite_MMIO_writes':writes,'prerequisite_MMIO_reads':0 if prefix_match else None,
            'historical_recognition_sequence':recognition,'frontend_sequences':[record['control_sequence'] for record in queued],
            'expected_terminal_digest':TERMINAL,'actual_terminal_digest':live[-1][1]['sha256'] if live else None,
            'terminal_cycle9':final_fields.get('cycle9') if final_fields else None,'retained_cap':final_fields.get('slice_cap') if final_fields else None,
            'ownership_fence_transcript':transfer,'fence_chain_verification':chain,'live_GPU_observations':gpu,
            'GPU_sha256':gpu_snapshots[0]['sha256'] if gpu_snapshots else None,'first_runtime_failure':failure,
            'driver_first_failure':session.get('first_failure'),'exit_code':session['exit_code'],
            'fresh_runtime_permit_claimed':(ATTEMPT/'runtime.permit.claimed').exists(),'old_permits_unchanged':True,
            'forbidden_B4_events':len(forbidden),'post_terminal_guest_instructions':0 if chain else None,
            'post_terminal_MMIO':0 if chain else None,'post_fence_service':0 if chain else None,
            'source_and_disposable_save_checkpoint_invariance':save_safe,'logical_save_requests':0,'Flash_commits':0,'changed_save_bytes':0,
            'before_after_save_sha256':session['disposable_save_sha256'],'ordinary_final_save_written':False,
            'emergency_process_termination':session.get('emergency_process_termination',False),
            'runner_sha256':session['runner_sha256'],'capture_audit_sha256':sha(ATTEMPT/'capture.jsonl'),
            'contract_sha256':preflight['contract_sha256'],'dynamic_execution_ready':False,
            'next_scheduler_tail_certification_justified':bool(chain),'status_read_or_tail_authorized':False}
    write_new(ATTEMPT/'analysis.json',result)
    print(json.dumps({key:result[key] for key in ['classification','live_prefix_admitted','prefix_observations','prefix_full_state_event_chain_exact_AW9_match','actual_terminal_digest','exit_code','first_runtime_failure','GPU_sha256','next_scheduler_tail_certification_justified']},indent=2))


if __name__=='__main__':
    main()
