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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-ac') and disabled.is_relative_to(ROOT/'local/task-ac')
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
tests=read(ROOT/'local/task-ac/focused-tests.json');assert all(value['pass'] for value in tests.values())
# Extend the exact Task Z byte/stack audit by the single authorized store.
import re
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']
installed={}
for src,dst in [('diagnostic.h','brainage_task_ac.h'),('guard.h','task_ac_guard.h'),('task_ac_decision.inc','task_ac_decision.inc')]:
    text=(ROOT/'tools/task_ac'/src).read_text(encoding='utf-8-sig');assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text(encoding='utf-8-sig')
    installed[src]=digest(text.encode())
for filename in ('02025698.txt','02026510.txt','02026BE4.txt','ranges.json'):
    assert (ROOT/'local/task-z/static-001'/filename).read_bytes()==(ROOT/'local/task-z/static-verified-002'/filename).read_bytes()
def changes(first,last,base):
    assert len(first)==len(last)
    return [{'address':f'0x{base+i:08X}','before':x,'after':y} for i,(x,y) in enumerate(zip(first,last)) if x!=y]
steps=[r for r in audit if r['event']=='decision_step']
path=[int(v,16) for v in re.search(r'decision_path\[\]=\{(.*?)\}',(ROOT/'tools/task_ac/guard.h').read_text(),re.S)[1].split(',') if v.strip()]
assert [s['pc'] for s in steps]==path and len(path)==46
assert [s['insn9']-steps[0]['insn9'] for s in steps]==list(range(46))
db=(out/'decision-before-mainram.bin').read_bytes();da=(out/'decision-after-mainram.bin').read_bytes();assert db==final
for s in steps:assert s['opcode']==struct.unpack_from('<I',db,s['pc']-0x02000000)[0]
consumer=[s for s in steps if s['pc']==0x02025778];helper=[s for s in steps if s['pc']==0x02025698]
assert len(consumer)==len(helper)==1 and consumer[0]['r'][2]==4
compare=next(s for s in steps if s['pc']==0x02025728);assert compare['r'][1]==compare['r'][5]==4
stop=steps[-1];assert stop['pc']==0x02025744 and stop['opcode']==0x08bd8030
assert [stop[k] for k in ('n','z','c','v')]==[0,1,1,0] and stop['r'][3]==0 and stop['r'][0]==0x020e9a00
done=event('decision_stopped');assert done['correct'] and not done['accepted'] and done['instructions']==45
for key in ('forbidden_entries','progression_entries','save_entries'):assert done[key]==0
main_changes=changes(db,da,0x02000000);assert main_changes==[{'address':'0x020E9A20','before':0,'after':1},{'address':'0x020E9F04','before':0,'after':1},{'address':'0x020E9F14','before':255,'after':4}]
bt=(out/'decision-before-dtcm.bin').read_bytes();at=(out/'decision-after-dtcm.bin').read_bytes()
stack_changes=changes(bt,at,0x027e0000)
reconstructed=bytearray(bt)
struct.pack_into('<II',reconstructed,0x3b14,consumer[0]['r'][4],consumer[0]['r'][14])
struct.pack_into('<III',reconstructed,0x3b08,helper[0]['r'][4],helper[0]['r'][5],helper[0]['r'][14])
assert bytes(reconstructed)==at and stop['r'][13]==0x027e3b08
objects={}
for name,base,size in [('exercise',0x020e9a00,0xc34),('manager',0x020fa808,0x238),('slot',0x020faa50,0x370)]:
    b=(out/(name+'-after.bin')).read_bytes();e=(out/(name+'-decision.bin')).read_bytes()
    assert b==db[base-0x02000000:base-0x02000000+size] and e==da[base-0x02000000:base-0x02000000+size]
    if name!='exercise':assert b==e
    objects[name]={'before_sha256':digest(b),'after_sha256':digest(e),'changes':changes(b,e,base)}
fields={}
for name,offset,fmt in [('correct_count',0x44,'I'),('phase',0x10,'H'),('expected',0x4c,'I'),('result_delay',0x20,'I'),('result_flag',0x504,'I'),('input_status',0x38,'I'),('submitted_tens',0x50c,'I'),('submitted_units',0x514,'I'),('later_outcome',0x51c,'I')]:
    fields[name]=[struct.unpack_from('<'+fmt,b,0xe9a00+offset)[0] for b in (db,da)]
assert fields['correct_count']==fields['phase']==[1,1] and fields['expected']==[4,4] and fields['result_delay']==[0,1] and fields['result_flag']==[0,1]
assert (out/'decision-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
assert [r['event'] for r in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()==before
assert not (disabled/'frontend-input.jsonl').stat().st_size and not control['input_events']
for d in (out,disabled):
    for f in ('initial.sav','session.sav','final.sav'):assert (d/f).read_bytes()==save
    assert (d/'source.state').read_bytes()==(source/'checkpoint.state').read_bytes()
assert done['acceptance_stores_executed']==2
assert len(db)==len(da)==4*1024*1024 and len(bt)==len(at)==16384
first_store=next(s for s in steps if s['pc']==0x02025738)
assert first_store['r'][1]==stop['r'][1]==1 and first_store['opcode']==0x05801020
armed=event('first_store_armed');assert armed['pc']==0x02025738 and armed['delay_before']==armed['flag_before']==0
immediate=(out/'first-store-before-mainram.bin').read_bytes()
immediate_stack=(out/'first-store-before-dtcm.bin').read_bytes()
second_before=(out/'second-store-before-mainram.bin').read_bytes()
assert changes(immediate,second_before,0x02000000)==[{'address':'0x020E9A20','before':0,'after':1}]
assert immediate_stack==at
# The first 42 pre-dispatch observations match the committed Task Z run, including every register.
aa=read(ROOT/'docs/BrainAge_TaskAA_Result.json')
aasteps=[r for r in rows(ROOT/'local/task-aa/session-001/audit.jsonl') if r['event']=='decision_step']
assert steps[:44]==aasteps
assert stop['insn9']==aa['safe_stop']['insn9']+2
pre=event('decision_before_sample');post=event('decision_stop_sample')
for key in ('cycle7','insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):
    assert pre[key]==post[key],key
assert post['insn9']-pre['insn9']==45
assert fields['input_status']==[0,0] and fields['submitted_tens']==fields['later_outcome']==[255,255]
assert fields['submitted_units']==[255,4]
# The terminal observation is read-only; the final ordinal is only 43 dispatched instructions.
assert stop['insn9']-event('decision_before')['insn9']==45
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
for row in steps:
    assert row['t']==0 and row['mode']==31 and row['i']==0 and row['f']==0

identified=event('second_store_identified');live=event('second_store_before');live_sample=event('second_store_before_sample')
assert identified['pc']==0x0202573c and identified['opcode']==0x05801504 and identified['condition']=='EQ'
assert identified['source_register']==1 and identified['source_value']==1 and identified['target']==0x020e9f04
assert identified['before']==0 and identified['width']==4 and identified['successor']==0x02025740
assert live==dict(steps[43],event='second_store_before')
assert changes(second_before,da,0x02000000)==[{'address':'0x020E9F04','before':0,'after':1}]
assert (out/'second-store-before-dtcm.bin').read_bytes()==at
assert (out/'second-store-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
assert second_before==(ROOT/'local/task-aa/session-001/decision-after-mainram.bin').read_bytes()
assert live['r'][:15]==steps[44]['r'][:15]
for key in ('n','z','c','v','t','mode','i','f'):assert live[key]==stop[key]
for key in ('cycle7','insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert live_sample[key]==post[key]
assert steps[44]['insn9']-live['insn9']==1

preflight=read(ROOT/'local/task-ac/preflight.json');assert preflight['safe']
adjust=event('instruction_identified');adjust_state=event('stack_adjust_before');adjust_sample=event('stack_adjust_before_sample')
assert adjust['pc']==0x02025740 and adjust['opcode']==0x028dd004 and adjust['condition']=='EQ'
assert adjust['source_register']==adjust['destination_register']==13 and adjust['source_value']==0x027e3b04
assert adjust['immediate']==4 and adjust['expected_value']==0x027e3b08 and adjust['lr']==0
assert not adjust['memory_write'] and not adjust['branch_or_call'] and adjust['successor']==0x02025744
assert adjust_state==dict(steps[44],event='stack_adjust_before')
ac_before=(out/'stack-adjust-before-mainram.bin').read_bytes()
ac_dtcm=(out/'stack-adjust-before-dtcm.bin').read_bytes()
assert ac_before==da and ac_dtcm==at
assert (out/'stack-adjust-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
ab=read(ROOT/'docs/BrainAge_TaskAB_Result.json')
absteps=[r for r in rows(ROOT/'local/task-ab/session-001/audit.jsonl') if r['event']=='decision_step']
assert steps[:45]==absteps
assert ac_before==(ROOT/'local/task-ab/session-001/decision-after-mainram.bin').read_bytes()
assert ac_dtcm==(ROOT/'local/task-ab/session-001/decision-after-dtcm.bin').read_bytes()
assert adjust_state['r'][13]+4==stop['r'][13]==0x027e3b08
assert [i for i in range(16) if adjust_state['r'][i]!=stop['r'][i]]==[13,15]
assert adjust_state['r'][14]==stop['r'][14]==0
for key in ('n','z','c','v','t','mode','i','f'):assert adjust_state[key]==stop[key]
for key in ('cycle7','insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert adjust_sample[key]==post[key]
assert stop['insn9']-adjust_state['insn9']==1
assert preflight['opcode']=='0x028DD004' and preflight['expected_successor']=='0x02025744'
immediate_fields={name:[struct.unpack_from('<'+fmt,b,0xe9a00+off)[0] for b in (ac_before,da)] for name,off,fmt in [('result_delay',0x20,'I'),('result_flag',0x504,'I'),('correct_count',0x44,'I'),('phase',0x10,'H')]}
assert all(pair==[1,1] for pair in immediate_fields.values())
result={
 'classification':'FULL PASS','task':'AC - one instruction beyond Task AB',
 'predecessor':'9b3396619e0b853ea8445929428beee6919aa15d','branch':'codex/brainage',
 'evidence_tier':'Forced Tier-3 original ARM interpreter; no compiled acceptance parity claim',
 'rom_sha1':preflight['rom_sha1'],'framework_baseline':'3a57236bb23d25dcb4caad7d58d733311062ff5e',
 'authoritative_path':str(out.relative_to(ROOT)),'disabled_path':str(disabled.relative_to(ROOT)),
 'runner_sha256':session['runner_sha256'],'installed_source_sha256_normalized_text':installed,
 'pre_execution_decode':preflight,'live_pre_execution_decode':adjust,'pre_instruction_state':adjust_state,'safe_stop':stop,
 'boundary':{'executed_pc':'0x02025740','opcode':'0x028DD004','decoded':'ADDEQ sp,sp,#4','condition':'EQ, Z=1',
  'source_and_destination_register':'r13 / SP','source_value':'0x027E3B04','destination_value':'0x027E3B08','immediate':4,
  'memory_write':False,'branch_or_call':False,'branch_call_target':None,'lr_before':0,'lr_after':0,
  'successor_pc':'0x02025744','successor_opcode':'0x08BD8030','successor_instruction_executed':False,
  'new_instructions_beyond_AB':1,'decision_dispatches':45,'observations':46,
  'proof':'Fixed pre-dispatch allowlist rejects successor at every index; terminal hook halts and preserves unwind before instruction count/fetch/step; clean exit'},
 'trace':[{**s,'dispatch_permitted':index<45} for index,s in enumerate(steps) if 0x02025738<=s['pc']<=0x02025744],
 'immediate_fields':immediate_fields,'decision_fields':fields,'immediate_ram_changes':[],
 'immediate_ram_changed_bytes':0,'immediate_dtcm_changed_bytes':0,
 'register_changes':[{'register':'SP','before':'0x027E3B04','after':'0x027E3B08'},{'register':'PC','before':'0x02025740','after':'0x02025744'}],
 'flags_unchanged':True,'objects':objects,'decision_mainram_changes':main_changes,'decision_dtcm_changes':stack_changes,
 'task_ab_prefix_exact_register_flags_opcode_ordinal_match':True,'immediate_before_ram_and_dtcm_equal_task_ab_stop':True,
 'input_sha256':freeze['sha256'],'checkpoint_sha256':freeze['checkpoint_sha256'],'input':definition,
 'input_source':'SDL_PushEvent -> frontend mapping -> nds_set_touch -> native owner -> isolated recognizer -> original publication/correctness',
 'custom_events':10,'custom_guest_deliveries':0,'recognition':recognitions,'private_isolation':cleanup,
 'decision':done,'decision_samples':[pre,adjust_sample,post],
 'prohibited_state':{'result_delay_unchanged_from_AB':True,'result_flag_unchanged_from_AB':True,'correct_count_unchanged':True,'phase_unchanged':True,
  'mainram_changed_bytes_during_AC':0,'dtcm_changed_bytes_during_AC':0,
  'score_progression_history':'No RAM/DTCM bytes changed; no downstream entry; no invented offsets',
  'downstream_routine_entries':0,'ARM7_cycles_and_ordinal_unchanged':True,'guest_video_touch_scene_unchanged':True},
 'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':False},
 'hashes':{'immediate_mainram_before':digest(ac_before),'immediate_mainram_after':digest(da),'immediate_dtcm_before':digest(ac_dtcm),'immediate_dtcm_after':digest(at)},
 'disabled_control':{'pass':True,'recognition_entries':0,'publication_entries':0,'correctness_entries':0,'ram_changed_bytes':0,'save_changed_bytes':0,'exit_code':0},
 'focused_tests':tests,'exit_code':0,'source_checkpoint_and_save_unchanged':True,'gameplay_resumed':False,'answer_completed':False,
 'deviations_from_task_ab':['Fresh authorized SDL replay, exact prefix and immediate pre-RAM/DTCM match','One more ARM instruction; SP adds four; no new RAM mutation','Host hold presentation count may vary; no guest divergence'],
 'limitations':['One exact 11 - 7 / recognized 4 context','Forced Tier-3 only; no compiled parity','Score/progression/history excluded by exhaustive RAM/DTCM audit and exact path, no speculative field offsets'],
 'reproduction':['python tools/task_ac/preflight.py','powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ac/build.ps1','python tools/task_ac/check.py','python tools/task_ac/run.py --out local/task-ac/disabled-FRESH --disabled --port 19921','python tools/task_ac/run.py --out local/task-ac/session-FRESH --port 19922','python tools/task_ac/analyze.py --out local/task-ac/session-FRESH --disabled local/task-ac/disabled-FRESH --export docs/BrainAge_TaskAC_Result.json'],
 'stop':'No successor POP, answer completion, count/phase progression, score/history/save/menu/optimization integration or Task AD'
}
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'classification':'FULL PASS','opcode':'0x028DD004','SP':['0x027E3B04','0x027E3B08'],'immediate_ram_changed_bytes':0,'immediate_fields':immediate_fields,'successor':'0x02025744','successor_executed':False}))
