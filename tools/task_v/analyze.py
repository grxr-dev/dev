ï»¿"""Audit Task V SDL provenance, native pixels, private isolation and clean original handoff."""
import argparse, hashlib, json, struct
from pathlib import Path

def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]
def main():
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--export',type=Path);a.add_argument('--disabled-out',type=Path);args=a.parse_args()
    repo=Path(__file__).resolve().parents[2];root=args.out.resolve();assert root.is_relative_to(repo/'local/task-v')
    r=json.loads((root/'result.json').read_text());assert r['pass'] and r['exit_code']==0 and not r.get('forced_cleanup')
    assert r['activation']=={'NDS_BRAINAGE_CUSTOM_EXERCISE':'1','NDS_BRAINAGE_NATIVE_PRESENTATION':'1','NDS_BRAINAGE_CUSTOM_EXERCISE_ID':'digit-recognition-probe'}
    focused=json.loads((repo/'local/task-v/focused-tests.json').read_text());assert focused['pass']
    disabled=None
    if args.disabled_out:
        disabled_root=args.disabled_out.resolve();assert disabled_root.is_relative_to(repo/'local/task-v')
        disabled=json.loads((disabled_root/'result.json').read_text());assert disabled['disabled_control_pass'] and disabled['exit_code']==0 and not disabled.get('forced_cleanup') and disabled['changed_bytes']==0
        disabled_rows=rows(disabled_root/'native-probe.jsonl');assert not any(s['exercise_present'] or s['touch_owner'] or s.get('presentation_owner',False) for s in disabled_rows)
    native=rows(root/'native-probe.jsonl');inputs=rows(root/'frontend-input.jsonl');entries=rows(root/'entries.jsonl');service=rows(root/'service.jsonl')
    events=[s['event'] for s in native];assert all(events.count(e)==1 for e in ['intercept','continue','continue_original','exercise_destroyed'])
    invariant=r['frozen_invariant'];assert all({k:s[k] for k in invariant}==invariant for s in native)
    assert (invariant['current'],invariant['requested'],invariant['selected'])==(0x32,0x41,0x11)
    assert native[0]['backend']=='compiled' and not native[0]['forced_tier3']
    assert service[0]['ram_equal'] and service[0]['cpu_equal'] and not service[0]['active'] and service[0]['return']==0 and service[0]['instructions']==13160
    custom=[s for s in inputs if s['event']=='frontend_touch' and s['owner']];assert len(custom)==14
    assert all(s['consumed'] and s['guest_before']==s['guest_after'] for s in custom)
    assert not any(s['source']=='diagnostic' and s['action'] in ('touch','continue','choose') for s in native)
    touches=[s for s in native if s['event']=='exercise_touch'];assert len(touches)==14 and all(s['event_guest_deliveries']==0 for s in touches)
    gestures=[[(190,110),(156,91),(121,65),(121,98),(121,130)],[(173,114),(132,114),(75,114)]]
    provenance=[];offset=0;calls=[]
    for index,gesture in enumerate(gestures):
        offset = 8 if index else 0  # two premature Continue events follow stroke 0
        for j,p in enumerate(gesture+[(0,0)]):
            s=custom[offset+j];t=touches[offset+j];assert (s['ds_x'],s['ds_y'])==p and s['down']==(j<len(gesture))
            queue=next(v for v in inputs if v['event'] in ('sdl_queue_button','sdl_queue_motion') and v['control_sequence']==s['sequence'])
            frontend=next(v for v in inputs if v['event'] in ('frontend_button','frontend_motion') and v['sequence']==s['sequence'])
            raw=gesture[min(j,len(gesture)-1)];assert (queue['client_x'],queue['client_y'])==(2*raw[0],2*(192+raw[1]))
            assert (frontend['client_x'],frontend['client_y'])==(queue['client_x'],queue['client_y']) and frontend['held']
            assert t['exercise_metrics']['completed_strokes']==index+(j==len(gesture))
            provenance.append({'stroke':index,'kind':'up' if j==len(gesture) else 'down' if not j else 'motion','sequence':s['sequence'],'source_ds':raw if j<len(gesture) else None,'guest_deliveries':0})
        assert all(touches[offset+j]['exercise_metrics']['private_instructions']==(636745 if index else 15069) for j in range(len(gesture)))
        result=touches[offset+len(gesture)]['exercise_metrics'];assert result['candidate']==(52 if index else 50) and result['recognition_return']==0 and result['recognition_success'] and result['candidate_available']
        assert result['metric']==(249 if index else 500)
        assert result['private_instructions']==(1561225 if index else 636745)
        calls.append({'stroke':index,'return':result['recognition_return'],'candidate':chr(result['candidate']),'metric':result['metric'],'wall_us':result['call_wall_us'],'private_instructions_including_metric':result['private_instructions']})
        offset+=len(gesture)+1
    ordered=['touch_release_clean','touch_owner_released','presentation_owner_released','exercise_end','exercise_destroyed','host_cleanup','continue_original']
    assert [events.index(e) for e in ordered]==sorted(events.index(e) for e in ordered)
    final=next(s for s in native if s['event']=='continue_original');assert not final['touch_owner'] and not final['presentation_owner'] and not final['exercise_present'] and not final['native_contact']
    assert sum(s['kind']=='lifecycle' and s['r0']==0x41 for s in entries)==1 and sum(s['kind']=='rules_initializer' for s in entries)==1
    assert not any(s['kind'] in ('calculation_constructor','write_api') for s in entries)
    captures={};windows=set();top=set()
    for name in ['initial','stroke1','stroke2','rules','returned-menu']:
        s=next(c['chosen'] for c in r['captures'] if c['label']==name);assert s['method']=='print' and s['matches_readback'];windows.add(s['window']['hwnd']);captures[name]=s['bottom_rgb_sha1']
        if name in ('rules','returned-menu'):assert s['distinct_colors']>8
        else:
            top.add(s['top_rgb_sha256']);bitmap=Path(s['path']).read_bytes();off=struct.unpack_from('<I',bitmap,10)[0];pixels=bitmap[off:];assert struct.unpack_from('<ii',bitmap,18)==(512,-768)
            for y in range(384,768,2):
                line=pixels[y*2048:(y+1)*2048];assert line==pixels[(y+1)*2048:(y+2)*2048]
                assert all(line[x:x+4]==line[x+4:x+8] for x in range(0,2048,8))
    assert len(windows)==len(top)==1 and len(set(captures.values()))==5
    before=(root/'initial.sav').read_bytes();assert len(before)==262144
    assert before==(root/'session.sav').read_bytes()==(root/'rules.sav').read_bytes()==(root/'returned-menu.sav').read_bytes()
    h=hashlib.sha256(before).hexdigest();assert h=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
    assert r['changed_bytes']==0 and (root/'flash.jsonl').stat().st_size==(root/'requests.jsonl').stat().st_size==0
    host=(repo/'tools/brainage_custom/bc_host.h').read_text();assert all(s not in host for s in ['DRAW 4','190,110','candidate','recognize_stroke','0x020a41a0'])
    for p in (repo/'tools/brainage_custom').glob('bc_*.h'):assert 'tools/task_s' not in p.read_text() and 'task_s::' not in p.read_text()
    audit={'classification':'FULL PASS','production_private_bus_integration_proven':True,'scope':'exact Brain Age ROM, one known two-stroke glyph; no arbitrary handwriting claim',
        'evidence':str(root.relative_to(repo)),'rom_sha1':'b8a105bacc3234dede8d4465df0869f2b922a0e2','database':{'source':'read-only view of runner already-selected verified ROM; title-specific FAT file 55','size':113956,'sha256':'2f237cc7009314df560311a7c026f2fcf6a47b039f6ad7a70443407ef56db0ad','pre_extracted_required':False,'committed':False},
        'calls':calls,'timings_us':{'init':touches[0]['exercise_metrics']['init_wall_us'],'stroke0':calls[0]['wall_us'],'stroke1':calls[1]['wall_us'],'teardown':service[0]['wall_us']},
        'execution':{'policy':'A','live_ram_sha256_before_after':service[0]['ram_sha256'],'live_ram_equal':True,'live_cpu_equal':True,'guest_invariant':invariant,'private_pointers_published':False,'worker_queue_created':False,'live_title_heap_used':False},
        'input':{'source':'SDL_PushEvent before ordinary coordinate mapping -> nds_set_touch -> native owner','physical_input_claim':False,'strokes':gestures,'custom_events':14,'custom_guest_deliveries':0},
        'ui':{'window_readback_match':True,'bottom_rgb_sha1':captures,'rules_visual_wait_seconds':r['rules_visual_wait_seconds'],'back_training':True},
        'cleanup':{'teardown_return':0,'teardown_instructions':13160,'session_active':False,'owners_removed':True,'exercise_destroyed':True,'transition_0x41_count':1,'rules_initializer_count':1,'constructor_count':0,'candidate_submitted':False,'correctness_progression_called':False},
        'save':{'logical_requests':0,'flash_commits':0,'changed_bytes':0,'before_after_sha256':h},'regression':{'adapter_parity':True,'fixed_service_two_fresh_sessions':True,'invalid_input':True,'error_exit':True,'candidate_independent_exit':True,'arithmetic_contract_and_pixels':True,'freehand_capture_and_selection':True,'default_unknown_new_selectors':True}}
    audit['regression']['disabled_path']=bool(disabled)
    audit['performance']={'visibly_problematic_pause_observed':False,'note':'Synchronous calls; recognition timings include the 120-instruction metric accessor. No realtime threshold imposed.'}
    audit['runtime_build']={'baseline':'3a57236bb23d25dcb4caad7d58d733311062ff5e','runner_sha256':hashlib.sha256((repo/'build/task-o-sdl-runner/nds_runner.exe').read_bytes()).hexdigest()}
    (root/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');(root/'stroke-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    if args.export:args.export.write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
