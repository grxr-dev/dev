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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-ae') and disabled.is_relative_to(ROOT/'local/task-ae')
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
tests=read(ROOT/'local/task-ae/focused-tests.json');assert all(value['pass'] for value in tests.values())
# Extend the exact Task Z byte/stack audit by the single authorized store.
import re
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']
installed={}
for src,dst in [('diagnostic.h','brainage_task_ae.h'),('guard.h','task_ae_guard.h'),('task_ae_decision.inc','task_ae_decision.inc')]:
    text=(ROOT/'tools/task_ae'/src).read_text(encoding='utf-8-sig');assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text(encoding='utf-8-sig')
    installed[src]=digest(text.encode())
for filename in ('02025698.txt','02026510.txt','02026BE4.txt','ranges.json'):
    assert (ROOT/'local/task-z/static-001'/filename).read_bytes()==(ROOT/'local/task-z/static-verified-002'/filename).read_bytes()
def changes(first,last,base):
    assert len(first)==len(last)
    return [{'address':f'0x{base+i:08X}','before':x,'after':y} for i,(x,y) in enumerate(zip(first,last)) if x!=y]
steps=[r for r in audit if r['event']=='decision_step']
path=[int(v,16) for v in re.search(r'decision_path\[\]=\{(.*?)\}',(ROOT/'tools/task_ae/guard.h').read_text(),re.S)[1].split(',') if v.strip()]
assert [s['pc'] for s in steps]==path and len(path)==56
assert [s['insn9']-steps[0]['insn9'] for s in steps]==list(range(56))
db=(out/'decision-before-mainram.bin').read_bytes();da=(out/'decision-after-mainram.bin').read_bytes();assert db==final
for s in steps:assert s['opcode']==struct.unpack_from('<I',db,s['pc']-0x02000000)[0]
consumer=[s for s in steps if s['pc']==0x02025778];helper=[s for s in steps if s['pc']==0x02025698]
assert len(consumer)==len(helper)==1 and consumer[0]['r'][2]==4
compare=next(s for s in steps if s['pc']==0x02025728);assert compare['r'][1]==compare['r'][5]==4
stop=steps[46];ae_stop=steps[-1];assert stop['pc']==0x02025830 and stop['opcode']==0xe8bd8010
assert [stop[k] for k in ('n','z','c','v')]==[0,1,1,0] and stop['r'][3]==0 and stop['r'][0]==0x020e9a00
done=event('decision_stopped');assert done['correct'] and not done['accepted'] and done['instructions']==55
for key in ('forbidden_entries','progression_entries','save_entries'):assert done[key]==0
main_changes=changes(db,da,0x02000000);assert main_changes==[{'address':'0x020E9A20','before':0,'after':1},{'address':'0x020E9F04','before':0,'after':1},{'address':'0x020E9F14','before':255,'after':4}]
bt=(out/'decision-before-dtcm.bin').read_bytes();at=(out/'decision-after-dtcm.bin').read_bytes()
stack_changes=changes(bt,at,0x027e0000)
reconstructed=bytearray(bt)
struct.pack_into('<II',reconstructed,0x3b14,consumer[0]['r'][4],consumer[0]['r'][14])
struct.pack_into('<III',reconstructed,0x3b08,helper[0]['r'][4],helper[0]['r'][5],helper[0]['r'][14])
assert bytes(reconstructed)==at and stop['r'][13]==0x027e3b14
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
assert stop['insn9']==aa['safe_stop']['insn9']+3
pre=event('decision_before_sample');post=event('decision_stop_sample')
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):
    assert pre[key]==post[key],key
assert post['insn9']-pre['insn9']==55
assert fields['input_status']==[0,0] and fields['submitted_tens']==fields['later_outcome']==[255,255]
assert fields['submitted_units']==[255,4]
# The terminal observation is read-only; the final ordinal is exactly 55 dispatched instructions.
assert ae_stop['insn9']-event('decision_before')['insn9']==55
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
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert live_sample[key]==post[key]
assert steps[44]['insn9']-live['insn9']==1

preflight=read(ROOT/'local/task-ad/preflight.json');assert preflight['safe']
adjust=event('stack_adjust_identified');adjust_state=event('stack_adjust_before');adjust_sample=event('stack_adjust_before_sample')
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
assert adjust_state['r'][13]+4==steps[45]['r'][13]==0x027e3b08
assert [i for i in range(16) if adjust_state['r'][i]!=steps[45]['r'][i]]==[13,15]
assert adjust_state['r'][14]==stop['r'][14]==0
for key in ('n','z','c','v','t','mode','i','f'):assert adjust_state[key]==stop[key]
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert adjust_sample[key]==post[key]
assert steps[45]['insn9']-adjust_state['insn9']==1
assert preflight['opcode']=='0x08BD8030' and preflight['expected_successor']=='0x02025830'
immediate_fields={name:[struct.unpack_from('<'+fmt,b,0xe9a00+off)[0] for b in (ac_before,da)] for name,off,fmt in [('result_delay',0x20,'I'),('result_flag',0x504,'I'),('correct_count',0x44,'I'),('phase',0x10,'H')]}
assert all(pair==[1,1] for pair in immediate_fields.values())
# Audit the retained Task AD POP against the byte-identical Task AC stop.
ac=read(ROOT/'docs/BrainAge_TaskAC_Result.json')
acsteps=[s for s in rows(ROOT/'local/task-ac/session-001/audit.jsonl') if s['event']=='decision_step']
assert steps[:46]==acsteps
pop=event('instruction_identified');pop_state=event('pop_before');pop_sample=event('pop_before_sample')
assert pop_state==dict(steps[45],event='pop_before')
assert pop['pc']==0x02025744 and pop['opcode']==0x08bd8030 and pop['condition']=='EQ'
assert pop['register_list']==[4,5,15] and pop['sp_before']==0x027e3b08 and pop['sp_after']==0x027e3b14
assert pop['expected_target']==0x02025830 and pop['lr']==0 and not pop['memory_write']
assert pop['stack_reads']==preflight['stack_reads']
ad_before=(out/'pop-before-mainram.bin').read_bytes();ad_dtcm=(out/'pop-before-dtcm.bin').read_bytes()
assert ad_before==da==(ROOT/'local/task-ac/session-001/decision-after-mainram.bin').read_bytes()
assert ad_dtcm==at==(ROOT/'local/task-ac/session-001/decision-after-dtcm.bin').read_bytes()
assert (out/'pop-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
for i,reg in enumerate((4,5,15)):
    address=0x027e3b08+4*i;value=struct.unpack_from('<I',ad_dtcm,address-0x027e0000)[0]
    assert pop['stack_reads'][i]=={'address':address,'value':value,'register':reg}
    assert value==helper[0]['r'][(4,5,14)[i]]==stop['r'][reg]
assert helper[0]['r'][13]==0x027e3b14 and helper[0]['opcode']==0xe92d4030
assert next(s for s in steps if s['pc']==0x0202582c)['opcode']==0xebffff99
assert [i for i in range(16) if pop_state['r'][i]!=stop['r'][i]]==[4,5,13,15]
assert stop['r'][13]==0x027e3b14 and stop['r'][14]==pop_state['r'][14]==0
for key in ('n','z','c','v','t','mode','i','f'):assert pop_state[key]==stop[key]
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert pop_sample[key]==post[key]
assert stop['insn9']-pop_state['insn9']==1
assert all(value==[1,1] for value in immediate_fields.values())
register_changes=[{'register':('SP' if i==13 else 'PC' if i==15 else 'r'+str(i)),'before':f"0x{pop_state['r'][i]:08X}",'after':f"0x{stop['r'][i]:08X}"} for i in (4,5,13,15)]
# Task AE: audit the entire independently frozen nine-instruction slice.
ae_preflight=read(ROOT/'local/task-ae/preflight.json');assert ae_preflight['safe']
ads=read(ROOT/'docs/BrainAge_TaskAD_Result.json')
adsteps=[s for s in rows(ROOT/'local/task-ad/session-001/audit.jsonl') if s['event']=='decision_step']
assert steps[:47]==adsteps
slice_state=event('slice_before');slice_sample=event('slice_before_sample')
assert slice_state==dict(steps[46],event='slice_before')
ae_ram=(out/'slice-before-mainram.bin').read_bytes();ae_dtcm=(out/'slice-before-dtcm.bin').read_bytes()
assert ae_ram==da==(ROOT/'local/task-ad/session-001/decision-after-mainram.bin').read_bytes()
assert ae_dtcm==at==(ROOT/'local/task-ad/session-001/decision-after-dtcm.bin').read_bytes()
assert (out/'slice-before.sav').read_bytes()==(out/'decision-after.sav').read_bytes()==save
assert len(steps[46:])==len(ae_preflight['states'])==10
slice_trace=[]
for index,(actual,expected) in enumerate(zip(steps[46:],ae_preflight['states'])):
 assert actual['pc']==expected['pc'] and actual['opcode']==expected['opcode'] and actual['r']==expected['r']
 assert [actual[k] for k in ('n','z','c','v')]==expected['nzcv']
 assert actual['insn9']-slice_state['insn9']==index
 assert actual['r'][14]==0
 slice_trace.append({**actual,'decoded':expected['decoded'],'dispatch_permitted':expected['dispatch']})
assert pre['cycle7']==slice_sample['cycle7'] and post['cycle7']>=slice_sample['cycle7']
assert ae_stop['pc']==0x02026b90 and ae_stop['opcode']==0xebfffda0 and ae_stop['insn9']-slice_state['insn9']==9
assert ae_stop['r'][0]==0x020e9a00 and ae_stop['r'][13]==0x027e3b34
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert slice_sample[key]==post[key]
register_changes=[{'register':('SP' if i==13 else 'PC' if i==15 else 'r'+str(i)),'before':f"0x{slice_state['r'][i]:08X}",'after':f"0x{ae_stop['r'][i]:08X}"} for i in range(16) if slice_state['r'][i]!=ae_stop['r'][i]]
assert [x['register'] for x in register_changes]==['r4','r5','SP','PC']
result={
 'classification':'FULL PASS','task':'AE - bounded original caller slice after Task AD',
 'predecessor':'a8502da4a156cf4cee756ee85afc2e016533bab8','branch':'codex/brainage',
 'evidence_tier':'Forced Tier-3 original ARM interpreter; no compiled acceptance parity claim',
 'rom_sha1':ae_preflight['rom_sha1'],'framework_baseline':'3a57236bb23d25dcb4caad7d58d733311062ff5e',
 'authoritative_path':str(out.relative_to(ROOT)),'disabled_path':str(disabled.relative_to(ROOT)),
 'runner_sha256':session['runner_sha256'],'installed_source_sha256_normalized_text':installed,
 'pre_execution_analysis':ae_preflight,'slice_before':slice_state,'safe_stop':ae_stop,
 'boundary':{'start_pc':'0x02025830','stop_before_pc':'0x02026B90','stop_opcode':'0xEBFFFDA0','decoded':'BL 0x02026218','call_executed':False,'call_target':'0x02026218','call_target_dispatches':0,
  'call_arguments':ae_stop['r'][:4],'r0_meaning':'exercise pointer','r1_r2_r3_semantic_status':'Residual registers; callee ABI beyond r0 not established',
  'expected_lr_if_call_executed':'0x02026B94','actual_lr':0,'new_instructions_beyond_AD':9,'decision_dispatches':55,'observations':56,
  'reason':ae_preflight['boundary_reason'],'proof':'Exact fixed path and opcode allowlist; stop before bank handoff/count/fetch/step. No call or save/MMIO routine entered.'},
 'slice_trace':slice_trace,'slice_stack_reads':ae_preflight['stack_reads'],'phase_read':ae_preflight['phase_read'],
 'immediate_fields':immediate_fields,'decision_fields':fields,'immediate_ram_changes':[],
 'immediate_ram_changed_bytes':0,'immediate_dtcm_changed_bytes':0,
 'register_changes':register_changes,'flags':{'before':[0,1,1,0],'after':[1,0,0,0],'changed_at':'0x0202698C CMP r0,#2; 1-2'},
 'objects':objects,'decision_mainram_changes':main_changes,'decision_dtcm_changes':stack_changes,
 'task_ad_prefix_exact_register_flags_opcode_ordinal_match':True,'immediate_before_ram_and_dtcm_equal_task_ad_stop':True,
 'input_sha256':freeze['sha256'],'checkpoint_sha256':freeze['checkpoint_sha256'],'input':definition,
 'input_source':'SDL_PushEvent -> frontend mapping -> nds_set_touch -> native owner -> isolated recognizer -> original publication/correctness -> original caller slice',
 'custom_events':10,'custom_guest_deliveries':0,'recognition':recognitions,'private_isolation':cleanup,
 'decision':done,'decision_samples':[pre,slice_sample,post],
 'state_classification':{'result_delay':{'before':1,'after':1},'result_flag':{'before':1,'after':1},'correct_count':{'before':1,'after':1},'phase':{'before':1,'after':1},
  'score_progression_history_result_completion':'No new RAM/DTCM mutations or semantic callee entry; no speculative score/history offsets',
  'gameplay_resumed':False,'new_phase_dispatch_call_executed':False,'ARM7_ordinal_unchanged':True,'ARM7_cycles_before':slice_sample['cycle7'],'ARM7_cycles_after':post['cycle7'],'ARM7_cycle_delta':post['cycle7']-slice_sample['cycle7'],'guest_video_touch_scene_unchanged':True},
 'runtime_timing':{'arm9_cycles_before':slice_sample['cycle9'],'arm9_cycles_after':post['cycle9'],'arm9_cycle_delta':post['cycle9']-slice_sample['cycle9'],'arm7_cycles_before':slice_sample['cycle7'],'arm7_cycles_after':post['cycle7'],'arm7_cycle_delta':post['cycle7']-slice_sample['cycle7'],'arm7_instruction_delta':post['insn7']-slice_sample['insn7'],'note':'Normal scheduler slice/idle cycle accounting advances ARM7 time without ARM7 instruction retirement; no counters restored'},
 'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':False},
 'hashes':{'immediate_mainram_before':digest(ae_ram),'immediate_mainram_after':digest(da),'immediate_dtcm_before':digest(ae_dtcm),'immediate_dtcm_after':digest(at)},
 'disabled_control':{'pass':True,'recognition_entries':0,'publication_entries':0,'correctness_entries':0,'ram_changed_bytes':0,'save_changed_bytes':0,'exit_code':0},
 'focused_tests':tests,'exit_code':0,'source_checkpoint_and_save_unchanged':True,'gameplay_resumed':False,'answer_completed':False,
 'deviations_from_task_ad':['Fresh authorized SDL replay, exact 47-observation prefix and immediate pre-RAM/DTCM match','Nine original instructions across two returns and a phase-one branch; no new memory mutation','ARM7 scheduler cycle accounting advances 65 with zero ARM7 instructions; RAM/DTCM/video unchanged','Host presentation count may vary; no prefix divergence'],
 'limitations':['One exact 11 - 7 / recognized 4 context','Forced Tier-3 only; no compiled parity','Exhaustive 4 MiB RAM/16 KiB DTCM diff, no speculative score/history field labels','Call at 0x02026B90 and callee at 0x02026218 remain unexecuted'],
 'next_phase_one_store':{'pc':'0x0202624C','address':'0x020E9A34','value':218,'current_value_at_AE_stop':struct.unpack_from('<I',da,0xe9a34)[0],'executed':False},
 'recommended_task_af':'Read-only bound 0x02026218 phase-one path before authorizing BL at 0x02026B90; first visible phase-one store is 0x0202624C to exercise +0x34. Bound its later call separately.',
 'reproduction':['python tools/task_ae/preflight.py','powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ae/build.ps1','python tools/task_ae/check.py','python tools/task_ae/run.py --out local/task-ae/disabled-FRESH --disabled --port 19941','python tools/task_ae/run.py --out local/task-ae/session-FRESH --port 19942','python tools/task_ae/analyze.py --out local/task-ae/session-FRESH --disabled local/task-ae/disabled-FRESH --export docs/BrainAge_TaskAE_Result.json'],
 'stop':'Before phase-dispatch BL, no gameplay resume, later progression, scoring/history/save/menu/optimization integration or Task AF'
}
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'classification':'FULL PASS','new_instructions':9,'start':'0x02025830','stop':'0x02026B90','call_executed':False,'immediate_ram_changed_bytes':0,'immediate_dtcm_changed_bytes':0,'fields':immediate_fields,'register_changes':register_changes}))
