"""Fail-closed publication/input/isolation audit; export derived ROM-free facts only."""
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text())
def rows(path):return [json.loads(line) for line in path.read_text().splitlines()]
def ranges(before,after,base=0):
    starts=[];active=False
    for index,(first,second) in enumerate(zip(before,after)):
        if first!=second:
            if not active:starts.append([base+index,base+index]);active=True
            starts[-1][1]=base+index
        else:active=False
    return [{'start':hex(first),'end_inclusive':hex(last),'length':last-first+1} for first,last in starts]
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--disabled',type=Path,required=True);parser.add_argument('--export',type=Path,required=True);args=parser.parse_args()
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-aa') and disabled.is_relative_to(ROOT/'local/task-aa')
audit=rows(out/'audit.jsonl');session=read(out/'session.json');control=read(disabled/'session.json');assert session['pass'] and control['pass'] and session['exit_code']==control['exit_code']==0
assert not any(row['event']=='failure' for row in audit)
def event(name):
    found=[row for row in audit if row['event']==name];assert len(found)==1,(name,len(found));return found[0]
recognitions=[row for row in audit if row['event']=='recognition'];assert len(recognitions)==2
assert [row['integer'] for row in recognitions]==[2,4] and [row['countdown_before_update'] for row in recognitions]==[41,1] and [row['publishable_this_update'] for row in recognitions]==[False,True]
assert all(row['groups'][0]=={'count':0,'codes':[],'secondary':[]} for row in recognitions)
assert [row['groups'][1] for row in recognitions]==[{'count':1,'codes':[50],'secondary':[48]},{'count':1,'codes':[52],'secondary':[48]}]
for row in recognitions:row['interpreted_decimal_text']=''.join(chr(code) for code in row['chosen'])
definition=read(ROOT/'tools/task_y/input.json');freeze=read(ROOT/'tools/task_y/freeze.json');assert digest(json.dumps(definition,sort_keys=True,separators=(',',':')).encode())==freeze['sha256']==session['definition_sha256']
frontend=rows(out/'frontend-input.jsonl');touches=[row for row in frontend if row['event']=='frontend_touch'];native=[row for row in audit if row['event']=='native_touch']
assert len(touches)==len(native)==10
expected=[]
for stroke in definition['strokes']:expected.extend([*(point+[True] for point in stroke),[0,0,False]])
assert [[row['ds_x'],row['ds_y'],row['down']] for row in touches]==expected
assert [[row['x'],row['y'],row['down']] for row in native]==expected
assert all(row['owner'] and row['consumed'] and row['guest_before']==row['guest_after'] for row in touches)
assert len([row for row in frontend if row['event']=='sdl_queue_motion'])==6
assert len([row for row in frontend if row['event']=='sdl_queue_button'])==4
entry=event('entry');held=[event('panel_active'),*[row for row in audit if row['event']=='released_stroke'],event('owners_removed')]
keys=('pc','cycle9','cycle7','insn9','insn7','guest_deliveries','down','video_sha1','flash_sha1','current','requested','selected')
assert all({key:row[key] for key in keys}=={key:entry[key] for key in keys} for row in held)
assert held[-1]['presents']>held[0]['presents'] and not held[-1]['owner']
cleanup=event('service_cleanup');assert cleanup['live_ram_equal'] and cleanup['cpu_equal'] and not cleanup['active'] and cleanup['return']==0
before=(out/'hold-mainram.bin').read_bytes();clean=(out/'service-clean-mainram.bin').read_bytes();final=(out/'publication-mainram.bin').read_bytes();assert before==clean and digest(before)==cleanup['ram_sha256']
published=event('publication_blocked');assert published['pc']==0x020266b4 and published['integer']==4 and published['publication_entries']==published['slot_reads']==1 and published['correctness_entries']==0
stages=[row for row in audit if row['event']=='stage'];slot=published['slot'];assert [(row['address'],row['after']) for row in stages]==[(slot+0x320,4),(slot+0x364,1)]
offset=slot+0x320-0x02000000
assert before[:offset]==final[:offset] and before[offset+4:]==final[offset+4:]
assert int.from_bytes(final[offset:offset+4],'little')==published['integer']
objects={}
for name,size in [('exercise',0xc34),('manager',0x238),('slot',0x370)]:
    first=(out/(name+'-before.bin')).read_bytes();last=(out/(name+'-after.bin')).read_bytes();assert len(first)==len(last)==size
    if name!='slot':assert first==last
    objects[name]={'before_sha256':digest(first),'after_sha256':digest(last),'changed_bytes':sum(left!=right for left,right in zip(first,last)),'changed_ranges':ranges(first,last,published[name])}
assert struct.unpack_from('<I',(out/'slot-after.bin').read_bytes(),0x320)[0]==4
assert struct.unpack_from('<I',(out/'slot-after.bin').read_bytes(),0x364)[0]==0
assert struct.unpack_from('<I',(out/'exercise-after.bin').read_bytes(),0x44)[0]==1
assert struct.unpack_from('<H',(out/'exercise-after.bin').read_bytes(),0x10)[0]==1
source=ROOT/'local/task-g/session-001/11-answer-01-63';assert digest((source/'checkpoint.state').read_bytes())==freeze['checkpoint_sha256']
save=(out/'initial.sav').read_bytes();assert digest(save)==session['live_final_sha256']==session['final_save_sha256']=='a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb'
assert save==(out/'final.sav').read_bytes()==(out/'session.sav').read_bytes()==(source/'after.sav').read_bytes()
for directory in (out,disabled):assert not (directory/'requests.jsonl').stat().st_size and not (directory/'flash.jsonl').stat().st_size
assert any(row['event']=='disabled_control' for row in rows(disabled/'audit.jsonl')) and not any(row['event']=='stage' for row in rows(disabled/'audit.jsonl'))
tests=read(ROOT/'local/task-aa/focused-tests.json');assert all(value['pass'] for value in tests.values())
# Extend the exact Task Z byte/stack audit by the single authorized store.
import re
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']
installed={}
for src,dst in [('diagnostic.h','brainage_task_aa.h'),('guard.h','task_aa_guard.h'),('task_aa_decision.inc','task_aa_decision.inc')]:
    text=(ROOT/'tools/task_aa'/src).read_text(encoding='utf-8-sig');assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text(encoding='utf-8-sig')
    installed[src]=digest(text.encode())
for filename in ('02025698.txt','02026510.txt','02026BE4.txt','ranges.json'):
    assert (ROOT/'local/task-z/static-001'/filename).read_bytes()==(ROOT/'local/task-z/static-verified-002'/filename).read_bytes()
def changes(first,last,base):
    assert len(first)==len(last)
    return [{'address':f'0x{base+i:08X}','before':x,'after':y} for i,(x,y) in enumerate(zip(first,last)) if x!=y]
steps=[r for r in audit if r['event']=='decision_step']
path=[int(v,16) for v in re.search(r'decision_path\[\]=\{(.*?)\}',(ROOT/'tools/task_aa/guard.h').read_text(),re.S)[1].split(',') if v.strip()]
assert [s['pc'] for s in steps]==path and len(path)==44
assert [s['insn9']-steps[0]['insn9'] for s in steps]==list(range(44))
db=(out/'decision-before-mainram.bin').read_bytes();da=(out/'decision-after-mainram.bin').read_bytes();assert db==final
for s in steps:assert s['opcode']==struct.unpack_from('<I',db,s['pc']-0x02000000)[0]
consumer=[s for s in steps if s['pc']==0x02025778];helper=[s for s in steps if s['pc']==0x02025698]
assert len(consumer)==len(helper)==1 and consumer[0]['r'][2]==4
compare=next(s for s in steps if s['pc']==0x02025728);assert compare['r'][1]==compare['r'][5]==4
stop=steps[-1];assert stop['pc']==0x0202573c and stop['opcode']==0x05801504
assert [stop[k] for k in ('n','z','c','v')]==[0,1,1,0] and stop['r'][3]==0 and stop['r'][0]==0x020e9a00
done=event('decision_stopped');assert done['correct'] and not done['accepted'] and done['instructions']==43
for key in ('forbidden_entries','progression_entries','save_entries'):assert done[key]==0
main_changes=changes(db,da,0x02000000);assert main_changes==[{'address':'0x020E9A20','before':0,'after':1},{'address':'0x020E9F14','before':255,'after':4}]
bt=(out/'decision-before-dtcm.bin').read_bytes();at=(out/'decision-after-dtcm.bin').read_bytes()
stack_changes=changes(bt,at,0x027e0000)
reconstructed=bytearray(bt)
struct.pack_into('<II',reconstructed,0x3b14,consumer[0]['r'][4],consumer[0]['r'][14])
struct.pack_into('<III',reconstructed,0x3b08,helper[0]['r'][4],helper[0]['r'][5],helper[0]['r'][14])
assert bytes(reconstructed)==at and stop['r'][13]==0x027e3b04
objects={}
for name,base,size in [('exercise',0x020e9a00,0xc34),('manager',0x020fa808,0x238),('slot',0x020faa50,0x370)]:
    b=(out/(name+'-after.bin')).read_bytes();e=(out/(name+'-decision.bin')).read_bytes()
    assert b==db[base-0x02000000:base-0x02000000+size] and e==da[base-0x02000000:base-0x02000000+size]
    if name!='exercise':assert b==e
    objects[name]={'before_sha256':digest(b),'after_sha256':digest(e),'changes':changes(b,e,base)}
fields={}
for name,offset,fmt in [('correct_count',0x44,'I'),('phase',0x10,'H'),('expected',0x4c,'I'),('result_delay',0x20,'I'),('result_flag',0x504,'I'),('input_status',0x38,'I'),('submitted_tens',0x50c,'I'),('submitted_units',0x514,'I'),('later_outcome',0x51c,'I')]:
    fields[name]=[struct.unpack_from('<'+fmt,b,0xe9a00+offset)[0] for b in (db,da)]
assert fields['correct_count']==fields['phase']==[1,1] and fields['expected']==[4,4] and fields['result_delay']==[0,1] and fields['result_flag']==[0,0]
assert (out/'decision-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
assert [r['event'] for r in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()==before
assert not (disabled/'frontend-input.jsonl').stat().st_size and not control['input_events']
for d in (out,disabled):
    for f in ('initial.sav','session.sav','final.sav'):assert (d/f).read_bytes()==save
    assert (d/'source.state').read_bytes()==(source/'checkpoint.state').read_bytes()
assert done['acceptance_stores_executed']==1
assert len(db)==len(da)==4*1024*1024 and len(bt)==len(at)==16384
first_store=next(s for s in steps if s['pc']==0x02025738)
assert first_store['r'][1]==stop['r'][1]==1 and first_store['opcode']==0x05801020
armed=event('first_store_armed');assert armed['pc']==0x02025738 and armed['delay_before']==armed['flag_before']==0
immediate=(out/'first-store-before-mainram.bin').read_bytes()
immediate_stack=(out/'first-store-before-dtcm.bin').read_bytes()
assert changes(immediate,da,0x02000000)==[{'address':'0x020E9A20','before':0,'after':1}]
assert immediate_stack==at
# The first 42 pre-dispatch observations match the committed Task Z run, including every register.
z=read(ROOT/'docs/BrainAge_TaskZ_Result.json')
zsteps=[r for r in rows(ROOT/'local/task-z/session-001/audit.jsonl') if r['event']=='decision_step']
assert steps[:42]==zsteps
assert first_store['insn9']==z['safe_stop']['insn9']+1 and stop['insn9']==z['safe_stop']['insn9']+2
pre=event('decision_before_sample');post=event('decision_stop_sample')
for key in ('cycle7','insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):
    assert pre[key]==post[key],key
assert post['insn9']-pre['insn9']==43
assert fields['input_status']==[0,0] and fields['submitted_tens']==fields['later_outcome']==[255,255]
assert fields['submitted_units']==[255,4]
# The terminal observation is read-only; the final ordinal is only 43 dispatched instructions.
assert stop['insn9']-event('decision_before')['insn9']==43
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
for row in steps:
    assert row['t']==0 and row['mode']==31 and row['i']==0 and row['f']==0
result={
    'classification':'FULL PASS',
    'task':'AA - first original acceptance mutation only',
    'predecessor':'343a3daf41f05ab5ff14ea05124da2045cafe6cb',
    'branch':'codex/brainage',
    'evidence_tier':'Forced Tier-3 original ARM interpreter; no compiled acceptance parity claim',
    'rom_sha1':'b8a105bacc3234dede8d4465df0869f2b922a0e2',
    'framework_baseline':'3a57236bb23d25dcb4caad7d58d733311062ff5e',
    'authoritative_path':str(out.relative_to(ROOT)), 'disabled_path':str(disabled.relative_to(ROOT)),
    'runner_sha256':session['runner_sha256'], 'installed_source_sha256_normalized_text':installed,
    'input_sha256':freeze['sha256'],'checkpoint_sha256':freeze['checkpoint_sha256'],
    'input':definition, 'input_source':'SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> native owner -> private recognizer -> original publication/correctness',
    'custom_events':10,'button_edges':4,'motion_events':6,'custom_guest_deliveries':0,
    'recognition':recognitions,'publication':published,'private_isolation':cleanup,
    'decision':done, 'correct_predicate':steps[41], 'first_store_before':first_store,'safe_stop':stop,
    'boundary':{'allowed_instructions':['0x02025734 / 03A01001 MOVEQ r1,#1','0x02025738 / 05801020 STREQ r1,[r0,#0x20]'],
        'first_acceptance_store_executed':1,'next_pc':'0x0202573C','next_opcode':'0x05801504',
        'next_instruction_executed':False,'decision_dispatch_count':43,'pre_dispatch_observations':44,
        'proof':'Exact allowlist; terminal dispatches() is false; hook returns 2 and preserves unwind before interpreter count/fetch/step; clean process exit, no resume'},
    'trace':[{**r,'dispatch_permitted':index<43} for index,r in enumerate(steps) if r['pc']>=0x02025728 and r['pc']<=0x0202573c],
    'fields':fields,'objects':objects,'decision_mainram_changes':main_changes,'decision_dtcm_changes':stack_changes,
    'immediate_store_changes':[{'address':'0x020E9A20','before':0,'after':1}],
    'immediate_store_dtcm_changed_bytes':0,
    'prohibited_state':{'result_flag_0x504_unchanged':True,'correct_count_unchanged':True,'phase_unchanged':True,
        'score_progression_history':'No additional main-RAM changes anywhere; exact call path contains no downstream routine entry',
        'downstream_entries':0,'manager_changed_bytes':0,'slot_changed_bytes':0,
        'exercise_other_than_input_units_and_delay_changed_bytes':0,'mainram_other_than_input_units_and_delay_changed_bytes':0,
        'no_scheduler_or_ARM7_advancement_during_decision':True,'guest_video_unchanged':True},
    'decision_samples':[pre,post],
    'decision_memory_hashes':{'mainram_before':digest(db),'mainram_immediately_before_store':digest(immediate),'mainram_after':digest(da),'dtcm_before':digest(bt),'dtcm_after':digest(at)},
    'stack_write_footprint':{'bytes_written':20,'bytes_changed':len(stack_changes),'reconstructed_pushes_equal_full_dtcm':True,'reserved_unwritten_bytes':4},
    'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':False},
    'disabled_control':{'pass':True,'input_events':0,'recognition_entries':0,'publication_entries':0,'correctness_entries':0,'mainram_changed_bytes':0,'save_changed_bytes':0,'exit_code':0},
    'task_z_prefix_exact_register_flags_opcode_ordinal_match':True,
    'deviations_from_task_z':['Fresh explicitly authorized run; extends terminal boundary by exactly two dispatched ARM instructions','Result-delay byte at +0x20 changes 0 to 1','SDL hold presentation count can differ with host timing'],
    'focused_tests':tests,'exit_code':0,'source_checkpoint_save_unchanged':True,
    'no_counter_restoration':True,'no_rom_or_generated_code_edit':True,'gameplay_resumed':False,'answer_completed':False,
    'limitations':['One exact 11 - 7 / recognized 4 context only','Tier-3 evidence; no compiled acceptance parity','Score/progression/history are bounded by exhaustive main-RAM audit and exact-entry exclusion; no invented field offsets','Task Z input is two strokes / four button edges; no additional gestures introduced'],
    'reproduction':['powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_aa/build.ps1','python tools/task_aa/check.py','python tools/task_aa/run.py --out local/task-aa/disabled-<fresh> --disabled --port 19901','python tools/task_aa/run.py --out local/task-aa/session-<fresh> --port 19902','python tools/task_aa/analyze.py --out local/task-aa/session-<fresh> --disabled local/task-aa/disabled-<fresh> --export docs/BrainAge_TaskAA_Result.json'],
    'stop':'No second store, answer completion, count/phase progression, history/save integration or Task AB'
}
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'classification':result['classification'],'delay':fields['result_delay'],'flag':fields['result_flag'],'next_pc':'0x0202573C','next_executed':False,'acceptance_stores':1,'mainram_changed_bytes':len(main_changes),'dtcm_changed_bytes':len(stack_changes)}))
