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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-ah') and disabled.is_relative_to(ROOT/'local/task-ah')
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
tests=read(ROOT/'local/task-ah/focused-tests.json');assert all(v['pass'] for v in tests.values())
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']
installed={}
for src,dst in [('diagnostic.h','brainage_task_ah.h'),('guard.h','task_ah_guard.h'),('task_ah_decision.inc','task_ah_decision.inc')]:
 text=(ROOT/'tools/task_ah'/src).read_text(encoding='utf-8-sig');assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text(encoding='utf-8-sig');installed[src]=digest(text.encode())
proof=read(ROOT/'local/task-ag/preflight.json');proof['states'][-1]['dispatch']=True;proof['states'].append({**proof['states'][-1],'pc':0x02026250,'opcode':0xe1a00004,'r':proof['states'][-1]['r'][:-1]+[0x02026250],'decoded':'mov r0, r4','dispatch':False});ae=read(ROOT/'docs/BrainAge_TaskAE_Result.json');af=read(ROOT/'docs/BrainAge_TaskAF_Result.json')
assert proof['safe'] and digest((ROOT/'docs/BrainAge_TaskAE_Result.json').read_bytes())==proof['ae_json_sha256']
assert digest((ROOT/'docs/BrainAge_TaskAF_Result.json').read_bytes())==proof['af_json_sha256']
steps=[r for r in audit if r['event']=='decision_step'];ae_steps=[r for r in rows(ROOT/'local/task-ae/session-001/audit.jsonl') if r['event']=='decision_step']
assert len(steps)==65 and len(ae_steps)==56 and steps[:56]==ae_steps
assert [r['insn9']-steps[0]['insn9'] for r in steps]==list(range(65))
start=event('outer_before');start_sample=event('outer_before_sample');stop_sample=event('decision_stop_sample');stop=steps[-1]
assert start==dict(steps[55],event='outer_before') and steps[55]==ae['safe_stop']==af['ae_safe_stop']
assert steps[55]['r']==proof['ae_start']['r'] and steps[55]['opcode']==0xebfffda0
ag_trace=[]
for actual,expected in zip(steps[55:],proof['states']):
 assert actual['pc']==expected['pc'] and actual['opcode']==expected['opcode'] and actual['r']==expected['r']
 assert [actual[k] for k in ('n','z','c','v')]==expected['nzcv']
 assert [actual[k] for k in ('t','mode','i','f')]==[0,31,0,0]
 ag_trace.append({**actual,'decoded':expected['decoded'],'dispatch_permitted':expected['dispatch']})
assert len(ag_trace)==10 and [r['pc'] for r in ag_trace[:-1]]==[int(f['pc'],16) for f in af['instruction_facts'][:9]]
assert stop['pc']==0x02026250 and stop['opcode']==0xe1a00004 and stop['r']==af['ag']['predicted_stop_r'][:-1]+[0x02026250]
assert stop['insn9']-start['insn9']==9
before_ram=(out/'outer-before-mainram.bin').read_bytes();after_ram=(out/'decision-after-mainram.bin').read_bytes()
before_dtcm=(out/'outer-before-dtcm.bin').read_bytes();after_dtcm=(out/'decision-after-dtcm.bin').read_bytes()
assert len(before_ram)==len(after_ram)==0x400000 and len(before_dtcm)==len(after_dtcm)==0x4000
assert before_ram==after_ram==(ROOT/'local/task-ae/session-001/decision-after-mainram.bin').read_bytes()
assert before_dtcm==(ROOT/'local/task-ae/session-001/decision-after-dtcm.bin').read_bytes()
assert digest(before_ram)==proof['mainram_sha256'] and digest(before_dtcm)==proof['dtcm_sha256']
expected_dtcm=bytearray(before_dtcm);word_diffs=[]
for word in proof['stack_words']:
 a=int(word['address'],16)-0x027e0000;before_value=struct.unpack_from('<I',before_dtcm,a)[0];after_value=struct.unpack_from('<I',after_dtcm,a)[0]
 assert before_value==word['before'] and after_value==word['predicted_after']
 struct.pack_into('<I',expected_dtcm,a,word['predicted_after']);word_diffs.append({'address':word['address'],'before':f'0x{before_value:08X}','after':f'0x{after_value:08X}'})
assert after_dtcm==bytes(expected_dtcm) and digest(after_dtcm)==proof['expected_dtcm_after_sha256']
byte_diffs=[{'address':f'0x{0x027e0000+i:08X}','before':a,'after':b} for i,(a,b) in enumerate(zip(before_dtcm,after_dtcm)) if a!=b]
assert byte_diffs==[{'address':'0x027E3B2C','before':114,'after':3},{'address':'0x027E3B30','before':136,'after':148},{'address':'0x027E3B31','before':105,'after':107}]
fields=[]
for field in proof['fields']:
 off=int(field['address'],16)-0x02000000;n=field['width'];v1=int.from_bytes(before_ram[off:off+n],'little');v2=int.from_bytes(after_ram[off:off+n],'little');assert v1==v2==field['value'];fields.append({**field,'before':v1,'after':v2})
for offset,width,value in ((0x38,4,0),(0x50c,4,255),(0x514,4,4),(0x7c4,4,1)):
 a=0xe9a00+offset;assert int.from_bytes(before_ram[a:a+width],'little')==int.from_bytes(after_ram[a:a+width],'little')==value
 fields.append({'offset':hex(offset),'address':f'0x{0x020e9a00+offset:08X}','width':width,'before':value,'after':value,'name':'retained previously mapped field'})
for name,base,size in [('exercise',0x020e9a00,0xc34),('manager',0x020fa808,0x238),('slot',0x020faa50,0x370)]:
 assert (out/(name+'-decision.bin')).read_bytes()==before_ram[base-0x02000000:base-0x02000000+size]
for name in ('outer-before.sav','decision-after.sav','initial.sav','session.sav','final.sav'):assert (out/name).read_bytes()==save
assert [r['event'] for r in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()==before
assert not (disabled/'frontend-input.jsonl').stat().st_size and not control['input_events']
for name in ('initial.sav','session.sav','final.sav'):assert (disabled/name).read_bytes()==save
assert (out/'source.state').read_bytes()==(disabled/'source.state').read_bytes()==(source/'checkpoint.state').read_bytes()
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert start_sample[key]==stop_sample[key]
assert start_sample['insn9']==start['insn9'] and stop_sample['insn9']==stop['insn9']
done=event('decision_stopped');assert done['instructions']==64 and done['acceptance_stores_executed']==2
for key in ('forbidden_entries','progression_entries','save_entries'):assert done[key]==0
assert event('disposable_exit')['code']==0 and not event('disposable_exit')['save_dirty']
register_diffs=[{'register':('SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i)),'before':f"0x{start['r'][i]:08X}",'after':f"0x{stop['r'][i]:08X}"} for i in range(16) if start['r'][i]!=stop['r'][i]]
assert [d['register'] for d in register_diffs]==['r0','r4','SP','LR','PC']
ag=read(ROOT/'docs/BrainAge_TaskAG_Result.json')
ag_steps=[row for row in rows(ROOT/'local/task-ag/session-001/audit.jsonl') if row['event']=='decision_step']
assert steps[:64]==ag_steps and steps[63]==ag['ag_stop']
ah_start=event('ah_before');ah_sample=event('ah_before_sample')
assert ah_start==dict(steps[63],event='ah_before')
for k,v in [('insn9',ag['accounting']['arm9_ordinal_after']),('insn7',ag['accounting']['arm7_ordinal_after']),('cycle9',ag['accounting']['arm9_cycles_after']),('cycle7',ag['accounting']['arm7_cycles_after'])]:assert ah_sample[k]==v
ah_ram=(out/'ah-before-mainram.bin').read_bytes();ah_dtcm=(out/'ah-before-dtcm.bin').read_bytes()
assert ah_ram==after_ram==(ROOT/'local/task-ag/session-001/decision-after-mainram.bin').read_bytes()
assert ah_dtcm==after_dtcm==(ROOT/'local/task-ag/session-001/decision-after-dtcm.bin').read_bytes()
assert (out/'ah-before.sav').read_bytes()==save
write=event('ah_write_event')
assert write=={'event':'ah_write_event','path':'Interpreter::step -> RtBus::write32 -> bus_write_u32','pc':0x0202624c,'opcode':0xe5840034,'address':0x020e9a34,'width':4,'source_register':0,'value':218,'before':218,'after':218}
assert audit.index(ah_start)<audit.index(write)<audit.index(steps[-1])
deltas=[{'register':'PC' if i==15 else 'r'+str(i),'before':f"0x{ah_start['r'][i]:08X}",'after':f"0x{stop['r'][i]:08X}"} for i in range(16) if ah_start['r'][i]!=stop['r'][i]]
assert deltas==[{'register':'PC','before':'0x0202624C','after':'0x02026250'}]
for k in ('n','z','c','v','t','mode','i','f'):assert ah_start[k]==stop[k]
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert ah_sample[key]==stop_sample[key]
accounting={'arm9_ordinal_before':ah_sample['insn9'],'arm9_ordinal_after':stop_sample['insn9'],'arm9_instruction_delta':stop_sample['insn9']-ah_sample['insn9'],'arm9_cycles_before':ah_sample['cycle9'],'arm9_cycles_after':stop_sample['cycle9'],'arm9_cycle_delta':stop_sample['cycle9']-ah_sample['cycle9'],'arm7_ordinal_before':ah_sample['insn7'],'arm7_ordinal_after':stop_sample['insn7'],'arm7_instruction_delta':stop_sample['insn7']-ah_sample['insn7'],'arm7_cycles_before':ah_sample['cycle7'],'arm7_cycles_after':stop_sample['cycle7'],'arm7_cycle_delta':stop_sample['cycle7']-ah_sample['cycle7'],'counters_restored':False}
assert accounting['arm9_instruction_delta']==1 and accounting['arm7_instruction_delta']==accounting['arm7_cycle_delta']==0
ahproof=read(ROOT/'local/task-ah/preflight.json')
assert digest((ROOT/'docs/BrainAge_TaskAG_Result.json').read_bytes())==ahproof['ag_result_sha256']
result={'task':'AH - dynamic audit of one idempotent object store','classification':'FULL PASS','branch':'codex/brainage','authoritative_ag_commit':'e2bc0765d9d70f8d3e8b12dbc7fbf5c42ac3b5a5','authoritative_af_commit':'63ff0c59f995fe9e2df57248ef261d1f4c8c6819','authoritative_ae_commit':'6a43d5bfa4c85773b0f986b9d73944ab5e01700e','rom_sha1':ag['rom_sha1'],'framework_baseline':ag['framework_baseline'],'evidence_tier':'Forced Tier-3 exact-context original ARM interpreter; explicit interpreter Bus write event; no compiled parity','authoritative_path':out.relative_to(ROOT).as_posix(),'disabled_path':disabled.relative_to(ROOT).as_posix(),'runner_sha256':session['runner_sha256'],'installed_source_sha256_normalized_text':installed,'complete_ag_prefix_exact':True,'ag_cpu_ram_dtcm_save_revalidated_before_store':True,'ag_start':ah_start,'ah_stop':stop,'executed_pcs':['0x0202624C'],'terminal_pc':'0x02026250','terminal_dispatched':False,'inner_BL_dispatched':False,'AH_instruction_count':1,'decision_observations':65,'decision_dispatches':64,'store_write_event':write,'write_event_count':1,'register_deltas':deltas,'flags_before':[1,0,0,0],'flags_after':[1,0,0,0],'memory':{'mainram_changed_bytes':0,'dtcm_changed_bytes':0,'mapped_fields':fields,'mainram_before_sha256':digest(ah_ram),'mainram_after_sha256':digest(after_ram),'dtcm_before_sha256':digest(ah_dtcm),'dtcm_after_sha256':digest(after_dtcm)},'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':False},'state_effects':{'AH_mmio_accesses':0,'AH_unexpected_writes':0,'peripheral_effect_attributable_to_AH':False,'gameplay_resumed':False,'score_count_phase_progression_history_result_completion_effect':False,'video_touch_scene_unchanged':True,'inner_calls':0},'accounting':accounting,'source_checkpoint_sha256':digest((source/'checkpoint.state').read_bytes()),'input_sha256':freeze['sha256'],'native_SDL_events':10,'custom_guest_touch_deliveries':0,'disabled_control':{'pass':True,'input_events':0,'RAM_save_changes':0,'exit_code':0},'focused_tests':tests,'exit_code':0,'forced_cleanup':False,'limitations':['One frozen 11 - 7 / recognized-4 context','Original interpreter only; no compiled parity','No dispatch at 0x02026250 or inner BL; +0x34 semantic role unproven','Interpreter bus hooks cover actual AH memory accesses; no claim that all normal scheduler internal bookkeeping is frozen'],'recommended_next_smallest_task':'If separately authorized, execute only MOV r0,r4 at 0x02026250 and halt before inner BL at 0x02026254. Do not start AI here.','stop':'Stopped after Task AH; Task AI not started'}
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'classification':result['classification'],'executed_pcs':result['executed_pcs'],'store':write,'stop':result['terminal_pc'],'memory_diffs':[0,0],'accounting':accounting}))
