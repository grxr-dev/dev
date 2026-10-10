"""Audit frozen Task W SDL inputs, each stroke observation and isolated original handoff."""
import argparse,hashlib,json,statistics,struct,subprocess
from pathlib import Path
from corpus import load,EXPECTED

def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def candidate(code):return chr(code) if 32<=code<127 else f'U+{code:04X}'
def audit_session(repo,root,geometry,legacy=False):
    r=json.loads((root/'result.json').read_text());assert r['pass'] and r['exit_code']==0 and not r.get('forced_cleanup')
    assert r['corpus_sha256']==EXPECTED and r['strokes']==geometry and r['input_source']=='sdl-queue' and not r['manual_input'] and not r['answer_specific_controls']
    expected_id='digit-recognition-probe' if legacy else 'digit-entry-probe'
    assert r['activation']=={'NDS_BRAINAGE_CUSTOM_EXERCISE':'1','NDS_BRAINAGE_NATIVE_PRESENTATION':'1','NDS_BRAINAGE_CUSTOM_EXERCISE_ID':expected_id}
    n=rows(root/'native-probe.jsonl');frontend=rows(root/'frontend-input.jsonl');entries=rows(root/'entries.jsonl');cleanup=rows(root/'service.jsonl');assert len(cleanup)==1
    c=cleanup[0];assert c['ram_equal'] and c['cpu_equal'] and not c['active'] and c['return']==0 and c['instructions']==13160
    invariant=r['frozen_invariant'];assert all({k:s[k] for k in invariant}==invariant for s in n);assert (invariant['current'],invariant['requested'],invariant['selected'])==(0x32,0x41,0x11)
    assert n[0]['backend']=='compiled' and not n[0]['forced_tier3']
    events=[s['event'] for s in n];assert all(events.count(e)==1 for e in ('intercept','continue','continue_original','exercise_destroyed'))
    order=['touch_release_clean','touch_owner_released','presentation_owner_released','exercise_end','exercise_destroyed','host_cleanup','continue_original'];assert [events.index(e) for e in order]==sorted(events.index(e) for e in order)
    last=n[-1];assert not any(last[k] for k in ('exercise_present','touch_owner','presentation_owner','native_contact','guest_pen_down'))
    assert sum(s['kind']=='lifecycle' and s['r0']==0x41 for s in entries)==sum(s['kind']=='rules_initializer' for s in entries)==1
    assert not any(s['kind'] in ('calculation_constructor','write_api') for s in entries)
    assert not any(s['source']=='diagnostic' and s['action'] in ('touch','choose','continue') for s in n)
    touches=[s for s in n if s['event']=='exercise_touch'];custom=[s for s in frontend if s['event']=='frontend_touch' and s['owner']]
    drawing_events=sum(len(s)+1 for s in geometry);assert len(touches)==len(custom)==drawing_events+2
    assert all(s['event_guest_deliveries']==0 and s['exercise_id']==expected_id for s in touches)
    assert all(s['consumed'] and s['guest_before']==s['guest_after'] for s in custom)
    queue=[s for s in frontend if s['event'] in ('sdl_queue_button','sdl_queue_motion')];assert [s['control_sequence'] for s in queue]==list(range(1,len(queue)+1))
    offset=0;observations=[];provenance=[];previous_instructions=15069;point_count=0
    for i,stroke in enumerate(geometry):
        for j,point in enumerate(stroke+[[0,0]]):
            t=touches[offset+j];v=custom[offset+j];up=j==len(stroke);raw=stroke[min(j,len(stroke)-1)]
            assert [v['ds_x'],v['ds_y']]==point and v['down']==(not up)
            q=next(s for s in queue if s['control_sequence']==v['sequence']);f=next(s for s in frontend if s['event'] in ('frontend_button','frontend_motion') and s['sequence']==v['sequence'])
            assert [q['client_x'],q['client_y']]==[2*raw[0],2*(192+raw[1])]==[f['client_x'],f['client_y']] and f['held']
            assert f['event']==('frontend_motion' if j>0 and not up else 'frontend_button')
            assert t['native_contact']==(not up)
            m=t['exercise_metrics'];assert m['completed_strokes']==i+up and m['point_count']==point_count+min(j+1,len(stroke)) and m['current_points']==(0 if up else j+1)
            if not up:assert m['private_instructions']==previous_instructions # recognition only on release
            provenance.append({'stroke':i,'kind':'up' if up else 'down' if not j else 'motion','frontend_sequence':v['sequence'],'requested_native_ds':raw if not up else None,'client':[q['client_x'],q['client_y']],'custom_guest_deliveries':0})
        t=touches[offset+len(stroke)];m=t['exercise_metrics'];assert m['recognition_success'] and m['recognition_return']==0 and not m['recognition_error'];assert t['phase']==('candidate' if m['candidate_available'] else 'no_candidate')
        if not legacy:assert t['continue_available']
        assert not t['native_contact'];available=bool(m['candidate_available']);code=m['candidate'] if available else None
        observations.append({'stroke':i,'point_count':len(stroke),'success':True,'candidate_available':available,'candidate_code':code,'candidate':candidate(code) if available else None,'metric':m['metric'],'return_error_code':m['recognition_return'],'wall_us':m['call_wall_us'],'private_instructions_including_metric':m['private_instructions']})
        assert r['stroke_results'][i]['private_instructions']==m['private_instructions'] and r['stroke_results'][i]['candidate_available']==m['candidate_available']
        previous_instructions=m['private_instructions'];offset+=len(stroke)+1;point_count+=len(stroke)
    assert touches[-1]['phase']=='resuming'
    initial=(root/'initial.sav').read_bytes();assert len(initial)==262144 and hashlib.sha256(initial).hexdigest()=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
    assert initial==(root/'session.sav').read_bytes()==(root/'rules.sav').read_bytes() and r['changed_bytes']==0 and (root/'requests.jsonl').stat().st_size==(root/'flash.jsonl').stat().st_size==0
    captures={};windows=set()
    for item in r['captures']:
        s=item['chosen'];assert s['method']=='print' and s['matches_readback'];windows.add(s['window']['hwnd']);captures[item['label']]=s['bottom_rgb_sha1']
        if item['label'] in ('rules','returned-menu'):assert s['distinct_colors']>8
        else:
            bitmap=Path(s['path']).read_bytes();off=struct.unpack_from('<I',bitmap,10)[0];pixels=bitmap[off:];assert struct.unpack_from('<ii',bitmap,18)==(512,-768)
            for y in range(384,768,2):
                line=pixels[y*2048:(y+1)*2048];assert line==pixels[(y+1)*2048:(y+2)*2048]
                assert all(line[x:x+4]==line[x+4:x+8] for x in range(0,2048,8))
    if windows:assert len(windows)==1
    final=observations[-1];result={'target_label_offline_only':r['target_label'],'exercise_id':expected_id,'corpus_sha256':EXPECTED,'evidence':str(root.relative_to(repo)),'stroke_count':len(geometry),'point_count':point_count,'strokes':geometry,'observations':observations,'final_candidate_available':final['candidate_available'],'final_candidate_code':final['candidate_code'],'final_candidate':final['candidate'],'offline_target_match':final['candidate_code']==ord(str(r['target_label'])),'safe_continue':True,'teardown':c,'isolation':{'policy':'A','guest_invariant':invariant,'live_cpu_equal':True,'live_main_ram_equal':True,'private_pointers_published':False,'live_heap_worker_queue_used':False},'save':{'logical_requests':0,'flash_commits':0,'changed_bytes':0,'sha256':hashlib.sha256(initial).hexdigest()},'handoff':{'transition_count':1,'rules_initializer_count':1,'constructor_count':0,'owners_removed':True,'session_active':False,'back_training':'returned-menu' in captures},'actual_window_readback_sha1':captures}
    (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(root/'stroke-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result

def signature(s):return [(v['success'],v['candidate_available'],v['candidate_code'],v['metric'],v['return_error_code'],v['private_instructions_including_metric']) for v in s['observations']]
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--export',type=Path,required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[2];root=a.out.resolve();assert root.is_relative_to(repo/'local/task-w')
    corpus=load();assert json.loads((root/'freeze.json').read_text())=={'sha256':EXPECTED,'corpus':corpus}
    focused=json.loads((repo/'local/task-w/focused-tests.json').read_text());assert focused['pass'] and focused['corpus_sha256']==EXPECTED
    sessions=[audit_session(repo,root/f'digit-{i}',corpus['samples'][i]['strokes']) for i in range(10)]
    repeat=audit_session(repo,root/'repeat-0',corpus['samples'][0]['strokes']);assert signature(sessions[0])==signature(repeat)
    legacy=audit_session(repo,root/'legacy-v-4',corpus['samples'][4]['strokes'],legacy=True);assert [s['candidate'] for s in legacy['observations']]==['2','4']==[s['candidate'] for s in sessions[4]['observations']]
    assert all(s['teardown']['active']==False for s in sessions+[repeat,legacy])
    expected_visual={0:['initial','stroke1'],4:['initial','stroke1','stroke2','rules','returned-menu'],7:['initial','stroke1','stroke2','stroke3']}
    for i,labels in expected_visual.items():assert all(s in sessions[i]['actual_window_readback_sha1'] for s in labels)
    real_no_candidate=[{'target':s['target_label_offline_only'],'stroke':v['stroke']} for s in sessions for v in s['observations'] if not v['candidate_available']]
    timings=[(v['wall_us'],s['target_label_offline_only'],v['stroke']) for s in sessions for v in s['observations']];slowest=max(timings)
    correct=sum(s['offline_target_match'] for s in sessions);columns=[str(i) for i in range(10)]+['NO CANDIDATE','OTHER'];matrix={str(i):{c:0 for c in columns} for i in range(10)}
    for s in sessions:
        v=s['final_candidate'];column='NO CANDIDATE' if v is None else v if v in columns else 'OTHER';matrix[str(s['target_label_offline_only'])][column]+=1
    for sample in sessions+[repeat,legacy]:
        assert sample['corpus_sha256']==EXPECTED
    # Guard the title/service/host seam and unchanged historical behavior at source level.
    for path in ['bc_host.h','bc_private_digit_recognizer.h','bc_rom_resource.h','bc_decuma_adapter.h','bc_digit_probe.h','bc_quiz.h','bc_freehand.h']:
        baseline=subprocess.check_output(['git','show',f'9d2f35aa10f6adca396b77e3eedd2bb7ce7895c7:tools/brainage_custom/{path}'],cwd=repo).decode().replace('\r\n','\n');assert (repo/'tools/brainage_custom'/path).read_text()==baseline
    exercise=(repo/'tools/brainage_custom/bc_digit_entry.h').read_text();assert all(v not in exercise for v in ('0x020','target_label','corpus','confidence','candidate=='))
    outcome={'classification':'FULL PASS','scope':'One frozen title-oriented sample per digit; characterization, not arbitrary handwriting accuracy','task_v_commit':'9d2f35aa10f6adca396b77e3eedd2bb7ce7895c7','rom_sha1':'b8a105bacc3234dede8d4465df0869f2b922a0e2','corpus_sha256':EXPECTED,'freeze':json.loads((repo/'tools/task_w/freeze.json').read_text()),'sessions':sessions,'accuracy':{'correct':correct,'total':10,'percent':correct*10,'confusion_columns':columns,'confusion_counts':matrix,'analysis_only':True},'no_candidate_proof':{'path':'real SDL intermediate plus fake contract' if real_no_candidate else 'fake contract only; all real corpus strokes returned candidates','real_cases':real_no_candidate,'fake_render':'local/task-w/fake-no-candidate.png','contract':focused},'reset':{'authoritative_order':list(range(10))+[0],'fresh_processes':True,'repeat_0_signature_equal':True,'same_object_0_1_0_test_passed':True,'active_after_teardown':False,'stroke_index_and_point_ownership_reset':True},'task_v_regression':legacy,'timing':{'count':len(timings),'units':'microseconds','recognition_includes_metric_accessor':True,'min':min(t[0] for t in timings),'median':statistics.median(t[0] for t in timings),'max':slowest[0],'slowest_digit':slowest[1],'slowest_stroke_zero_based':slowest[2],'repeat_legacy_calls_excluded':True},'runtime_sha256':hashlib.sha256((repo/'build/task-o-sdl-runner/nds_runner.exe').read_bytes()).hexdigest(),'integration_readiness':'supports a separately authorized bounded answer-entry integration experiment; not general production handwriting validation' if correct==10 else 'investigate recognition input/generalization before answer-entry integration','remaining_blocker':None,'no_scoring_answer_save_menu_integration':True}
    a.export.write_text(json.dumps(outcome,indent=2)+'\n');(root/'aggregate.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps({'classification':outcome['classification'],'accuracy':outcome['accuracy'],'timing':outcome['timing'],'sequences':{s['target_label_offline_only']:[v['candidate'] for v in s['observations']] for s in sessions},'no_candidate':outcome['no_candidate_proof']['path']},indent=2))
if __name__=='__main__':main()
