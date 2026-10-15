"""Read-only independent audit of the consumed AW9 attempt. Never launches anything."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ATTEMPT=ROOT/'local/task-aw9/attempt-001'


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def observations(audit):
    result=[]; snapshot=None
    for row in audit:
        if row['event']=='canonical_snapshot':
            snapshot=row
            assert hashlib.sha256(bytes.fromhex(row['canonical_hex'])).hexdigest()==row['sha256']
        elif row['event']=='observation':
            result.append((row,snapshot))
    return result


def main():
    verify=load_module('aw6_verify',ROOT/'tools/task_aw6/check.py')
    decoder=load_module('aw5_decode',ROOT/'tools/task_aw5/analyze.py')
    certificate=json.loads((ROOT/'tools/task_aw8/certificate.json').read_text())
    payload=certificate['certificate']
    assert hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()==certificate['sha256']
    session=json.loads((ATTEMPT/'session.json').read_text())
    assert session['runner_launches']==1 and session['admitted'] and session['exact_prefix_completed'] and session['exit_code']==73
    assert not session.get('emergency_process_termination') and not session.get('first_mismatch') and not session.get('first_failure')
    assert (ATTEMPT.parent/'one-shot.lock').exists() and (ATTEMPT/'launch.claim').exists() and (ATTEMPT/'runtime.permit.claimed').exists()
    actual=rows(ATTEMPT/'capture.jsonl')
    reference=rows(ROOT/payload['local_evidence']/'success/audit.jsonl')
    assert sha(ROOT/payload['local_evidence']/'success/audit.jsonl')==payload['success_audit_sha256']
    assert verify.verify_chain(actual)==verify.verify_chain(reference)==69
    live=observations(actual); expected=observations(reference)
    assert len(live)==len(expected)==69 and actual[-1]['event']=='terminal'
    assert not any(row['event'] in ['failure','observer_failure','aw9_first_mismatch'] for row in actual)
    assert sum(row['event']=='aw9_preflight_accepted' for row in actual)==1
    assert sum(row['event']=='aw9_runtime_permission' for row in actual)==1
    for (event,state),(wanted,baseline) in zip(live,expected):
        assert event==wanted and state==baseline,'exact event/full-state/chain mismatch at '+str(event['index'])
        assert event['accepted'] and event['kind'] in range(5)
        assert event['pc']!=0x020019b4
    initial=next(row for row in actual if row['event']=='canonical_snapshot')
    final=live[-1][1]
    assert initial['sha256']==payload['entry_canonical_sha256']
    assert final['sha256']==payload['final_canonical_sha256']
    first,initial_ids=decoder.decode(bytes.fromhex(initial['canonical_hex']))
    last,final_ids=decoder.decode(bytes.fromhex(final['canonical_hex']))
    assert initial_ids==final_ids==payload['unchanged_identities']
    assert len(first)==361 and len(last)==411 and len(initial_ids)==5
    for index,value in enumerate(payload['final_registers']): assert last['r'+str(index)]==int(value,16)
    assert last['cpsr']==31 and last['cycle9']==3416875777 and last['slice_cap']==3416875778
    assert last['cycle9']-first['cycle9']==56 and last['ordinal9']-first['ordinal9']==11
    assert first['cycle7']==last['cycle7'] and first['ordinal7']==last['ordinal7']
    assert first['system_timestamp']==last['system_timestamp'] and first['hidden.fast_publishes']==last['hidden.fast_publishes']
    assert first['capture.epoch']==last['capture.epoch']==496 and first['capture.serial']==501 and last['capture.serial']==506
    assert first['cap.count']==1 and last['cap.count']==6
    kinds={index:sum(event['kind']==index for event,state in live) for index in range(10)}
    assert kinds=={0:11,1:18,2:18,3:11,4:11,5:0,6:0,7:0,8:0,9:0}
    instruction_pcs=[event['pc'] for event,state in live if event['kind']==0]
    assert instruction_pcs==[int(row['pc'],16) for row in payload['instructions']]
    commits=[event for event,state in live if event['kind']==3]
    assert [row['value'] for row in commits]==[row['cost'] for row in payload['instructions']]
    accesses=[]; writes=[]
    for event,snapshot in live:
        fields,identities=decoder.decode(bytes.fromhex(snapshot['canonical_hex']))
        assert identities==initial_ids and fields['logical_saves']==fields['flash_commits']==fields['save_dirty']==0
        if event['kind']==2 and event['address']!=event['pc']:
            accesses.append({key:event[key] for key in ['pc','address','width','value','write']})
            if event['write']:
                writes.append(dict(accesses[-1],cycle=fields['cycle9'],deadline=fields['div.deadline'],
                                   control=fields['div.control'],serial=fields['capture.serial'],cap=fields['slice_cap']))
    assert len(accesses)==7 and len(writes)==5
    assert all(not (row['address']>=0x04000000 and not row['write']) for row in accesses)
    for actual_access,wanted in zip(accesses,payload['data_accesses']):
        assert actual_access=={'pc':int(wanted['pc'],16),'address':int(wanted['address'],16),'width':wanted['width'],'value':wanted['value'],'write':wanted['write']}
    expected_writes=[row for row in payload['data_accesses'] if row['write']]
    for write,wanted in zip(writes,expected_writes):
        assert write['cycle']==wanted['precommit_cycle'] and write['deadline']==wanted['divider_deadline']
        assert write['serial']==wanted['serial'] and write['control']==wanted['divider_control'] and write['cap']==wanted['cap']
    preceding=rows(ATTEMPT/'audit.jsonl')
    au=[row for row in preceding if row['event']=='au_step']
    assert len(au)==8 and au[-1]['pc']==0x02001980 and au[-1]['insn9']==281098008
    assert sum(row['event']=='au_read_event' for row in preceding)==9
    assert sum(row['event']=='au_write_event' for row in preceding)==1
    assert [row['integer'] for row in preceding if row['event']=='recognition']==[2,4]
    assert not any(row['event'] in ['decision_stopped','disposable_exit'] for row in preceding)
    touches=[row for row in preceding if row['event']=='native_touch']
    definition=json.loads((ROOT/'tools/task_y/input.json').read_text())
    points=[point for stroke in definition['strokes'] for point in stroke]
    assert [[row['x'],row['y']] for row in touches if row['down']]==points
    assert len(touches)==10 and sum(not row['down'] for row in touches)==2
    assert all(row['consumed'] for row in touches) and len({row['guest_deliveries'] for row in touches})==1
    frontend=rows(ATTEMPT/'frontend-input.jsonl')
    queued=[row for row in frontend if 'control_sequence' in row]
    assert [row['control_sequence'] for row in queued]==list(range(1,11))
    assert all(row['event'] in ['sdl_queue_button','sdl_queue_motion'] for row in queued)
    assert session['source_checkpoint_unchanged'] and session['copied_checkpoint_unchanged'] and session['source_save_unchanged']
    assert session['disposable_save_sha256']==initial_ids['save'] and session['protected_artifacts_unchanged']
    assert not session['ordinary_final_save_written'] and session['logical_request_trace_bytes']==session['flash_trace_bytes']==0
    build=json.loads((ROOT/'build/task-aw9-once/build.json').read_text())
    assert sha(ROOT/'build/task-aw9-once/nds_runner.exe')==build['runner_sha256']==session['runner_sha256']
    assert not build['fixture_adapters_present'] and not build['generated_C_edited_or_regenerated']
    for name,digest in build['preserved_artifacts'].items(): assert sha(ROOT/name)==digest
    for part in ['bus','io','cp15','runtime','scheduler']:
        original=ROOT/'local/ndsrecomp/runner/src/aw3'/f'{part}.inc'
        overlay=ROOT/'build/task-aw9-once/source/aw3'/f'{part}.inc'
        assert sha(original)==sha(overlay) and 'task_aw8::identity' not in overlay.read_text()
    for row in json.loads((ROOT/'build/task-aw9-once/compile.json').read_text()):
        assert '-DAW9_LIVE_ONCE=1' in row['command'] and '-DAW7_DIAGNOSTIC_HARNESS=1' in row['command']
        assert '-DAW7_ROMFREE_MODEL' not in row['command'] and '-DAW8_ROMFREE_FIXTURE' not in row['command']
    result={'task':'AW9','classification':'FULL PASS','attempts':1,'retries':0,'live_entry_preflight':'PASS',
            'transcript_exact_AW8_match':True,'observations':69,'instruction_count':11,'cycle_cost':56,
            'instructions':[{'pc':row['pc'],'cost':row['cost'],'commit_cycle':row['cycle_after']} for row in payload['instructions']],
            'MMIO_writes':writes,'MMIO_reads':0,'literal_reads':2,'initial_digest':initial['sha256'],'final_digest':final['sha256'],
            'final_state_match':True,'initial_cycle9':first['cycle9'],'final_cycle9':last['cycle9'],'cap':last['slice_cap'],
            'initial_ordinal9':first['ordinal9'],'final_ordinal9':last['ordinal9'],'cycle7':last['cycle7'],'ordinal7':last['ordinal7'],
            'final_registers':payload['final_registers'],'final_CPSR':last['cpsr'],'entry_identities':initial_ids,'final_identities':final_ids,
            'forbidden_instruction_events':0,'forbidden_fetches':0,'forbidden_accounting':0,'forbidden_dispatch':0,
            'architectural_terminal_PC':'0x020019B4; not fetched/accounted/dispatched',
            'unexpected_service_observations':0,'process_exit':73,'last_event':actual[-1],
            'logical_save_requests':0,'Flash_commits':0,'changed_save_bytes':0,'original_RAM_DTCM_identity_unchanged_during_candidate':True,
            'no_fixture_identity_adapters':True,'no_emergency_termination':True,'prior_artifacts_unchanged':True,
            'source_checkpoint_unchanged':True,'source_save_unchanged':True,'original_AU_guards_passed':True,
            'audit_sha256':sha(ATTEMPT/'capture.jsonl'),'runner_sha256':build['runner_sha256'],
            'certificate_payload_sha256':certificate['sha256'],'prefix_executed_once':True,'full_12_instruction_route_executed':False}
    with (ATTEMPT/'analysis.json').open('x') as output: json.dump(result,output,indent=2); output.write('\n')
    print(json.dumps({key:result[key] for key in ['classification','attempts','transcript_exact_AW8_match','instruction_count','observations','final_digest','forbidden_fetches','process_exit','changed_save_bytes']},indent=2))


if __name__=='__main__':
    main()
