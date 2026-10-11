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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-ag') and disabled.is_relative_to(ROOT/'local/task-ag')
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
tests=read(ROOT/'local/task-ag/focused-tests.json');assert all(v['pass'] for v in tests.values())
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']
installed={}
for src,dst in [('diagnostic.h','brainage_task_ag.h'),('guard.h','task_ag_guard.h'),('task_ag_decision.inc','task_ag_decision.inc')]:
 text=(ROOT/'tools/task_ag'/src).read_text(encoding='utf-8-sig');assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text(encoding='utf-8-sig');installed[src]=digest(text.encode())
proof=read(ROOT/'local/task-ag/preflight.json');ae=read(ROOT/'docs/BrainAge_TaskAE_Result.json');af=read(ROOT/'docs/BrainAge_TaskAF_Result.json')
assert proof['safe'] and digest((ROOT/'docs/BrainAge_TaskAE_Result.json').read_bytes())==proof['ae_json_sha256']
assert digest((ROOT/'docs/BrainAge_TaskAF_Result.json').read_bytes())==proof['af_json_sha256']
steps=[r for r in audit if r['event']=='decision_step'];ae_steps=[r for r in rows(ROOT/'local/task-ae/session-001/audit.jsonl') if r['event']=='decision_step']
assert len(steps)==64 and len(ae_steps)==56 and steps[:56]==ae_steps
assert [r['insn9']-steps[0]['insn9'] for r in steps]==list(range(64))
start=event('outer_before');start_sample=event('outer_before_sample');stop_sample=event('decision_stop_sample');stop=steps[-1]
assert start==dict(steps[55],event='outer_before') and steps[55]==ae['safe_stop']==af['ae_safe_stop']
assert steps[55]['r']==proof['ae_start']['r'] and steps[55]['opcode']==0xebfffda0
ag_trace=[]
for actual,expected in zip(steps[55:],proof['states']):
 assert actual['pc']==expected['pc'] and actual['opcode']==expected['opcode'] and actual['r']==expected['r']
 assert [actual[k] for k in ('n','z','c','v')]==expected['nzcv']
 assert [actual[k] for k in ('t','mode','i','f')]==[0,31,0,0]
 ag_trace.append({**actual,'decoded':expected['decoded'],'dispatch_permitted':expected['dispatch']})
assert len(ag_trace)==9 and [r['pc'] for r in ag_trace[:-1]]==[int(f['pc'],16) for f in af['instruction_facts'][:8]]
assert stop['pc']==0x0202624c and stop['opcode']==0xe5840034 and stop['r']==af['ag']['predicted_stop_r']
assert stop['insn9']-start['insn9']==8
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
done=event('decision_stopped');assert done['instructions']==63 and done['acceptance_stores_executed']==2
for key in ('forbidden_entries','progression_entries','save_entries'):assert done[key]==0
assert event('disposable_exit')['code']==0 and not event('disposable_exit')['save_dirty']
register_diffs=[{'register':('SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i)),'before':f"0x{start['r'][i]:08X}",'after':f"0x{stop['r'][i]:08X}"} for i in range(16) if start['r'][i]!=stop['r'][i]]
assert [d['register'] for d in register_diffs]==['r0','r4','SP','LR','PC']
result={
 'classification':'FULL PASS','task':'AG - dynamic AF eight-instruction outer dispatch prefix',
 'authoritative_af_commit':'63ff0c59f995fe9e2df57248ef261d1f4c8c6819','authoritative_ae_commit':'6a43d5bfa4c85773b0f986b9d73944ab5e01700e','branch':'codex/brainage',
 'rom_sha1':proof['rom_sha1'],'framework_baseline':proof['framework_baseline'],'evidence_tier':'Forced Tier-3 exact-context original ARM interpreter; no compiled parity',
 'authoritative_path':out.relative_to(ROOT).as_posix(),'disabled_path':disabled.relative_to(ROOT).as_posix(),
 'runner_sha256':session['runner_sha256'],'installed_source_sha256_normalized_text':installed,
 'preflight':proof,'ae_start':start,'ag_stop':stop,'executed_pcs':[f"0x{r['pc']:08X}" for r in ag_trace[:-1]],'trace':ag_trace,
 'boundary':{'start_pc':'0x02026B90','stop_pc':'0x0202624C','executed_instructions':8,'stop_instruction':'STR r0,[r4,#0x34]','stop_dispatched':False,'inner_call_0x02026254_dispatched':False,'beyond_stop_dispatched':False,'decision_dispatches':63,'observations':64,
 'proof':'Exact ordinal/PC/opcode/register allowlist; live complete AE hash/CPU gate before BL; terminal halt before bank handoff, instruction count, fetch and step; clean unwind and process exit'},
 'control_flow':{'outer_BL_target':'0x02026218','outer_BL_lr':'0x02026B94','phase':1,'CMP_1_5_nzcv':[1,0,0,0],'ADDLS_taken':True,'architectural_pc_operand':'0x02026230','ADDLS_target':'0x02026234','slot_branch_target':'0x02026248'},
 'register_deltas':register_diffs,'flags_before':[1,0,0,0],'flags_after':[1,0,0,0],'no_unexplained_register_flags':True,
 'memory':{'mainram_changed_bytes':0,'mainram_byte_equal_AE':True,'dtcm_changed_bytes':len(byte_diffs),'dtcm_word_diffs':word_diffs,'dtcm_byte_diffs':byte_diffs,'dtcm_write_footprint':'0x027E3B2C..0x027E3B33','only_expected_PUSH_writes':True,'exercise_0x34_written_in_AG':False,'mapped_fields':fields},
 'state_effects':{'score_count_phase_progression_history_result_completion':'No main RAM/object changes; only two stack words overwritten','gameplay_resumed':False,'inner_calls':0,'MMIO_in_AG_instructions':0,'guest_video_touch_scene_unchanged':True,'peripheral_effect_attributable_to_AG':False},
 'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':False},
 'accounting':{'arm9_ordinal_before':start_sample['insn9'],'arm9_ordinal_after':stop_sample['insn9'],'arm9_instruction_delta':8,'arm9_cycles_before':start_sample['cycle9'],'arm9_cycles_after':stop_sample['cycle9'],'arm9_cycle_delta':stop_sample['cycle9']-start_sample['cycle9'],'arm7_ordinal_before':start_sample['insn7'],'arm7_ordinal_after':stop_sample['insn7'],'arm7_instruction_delta':stop_sample['insn7']-start_sample['insn7'],'arm7_cycles_before':start_sample['cycle7'],'arm7_cycles_after':stop_sample['cycle7'],'arm7_cycle_delta':stop_sample['cycle7']-start_sample['cycle7'],'counters_restored':False},
 'hashes':{'AE_mainram':digest(before_ram),'AG_mainram':digest(after_ram),'AE_dtcm':digest(before_dtcm),'AG_dtcm':digest(after_dtcm),'source_checkpoint':digest((source/'checkpoint.state').read_bytes())},
 'complete_ae_prefix_exact':True,'ae_CPU_RAM_DTCM_before_BL_independently_revalidated':True,'input':definition,'input_sha256':freeze['sha256'],'custom_events':10,'custom_guest_deliveries':0,'recognition':recognitions,'private_service_isolation':cleanup,
 'disabled_control':{'pass':True,'input_events':0,'publication':0,'correctness':0,'RAM_save_changes':0,'exit_code':0},'focused_tests':tests,'exit_code':0,'forced_cleanup':False,
 'limitations':['One exact 11 - 7 / recognized-4 context','Original ARM interpreter only; no compiled parity','No store at 0x0202624C or inner helper execution','MMIO attribution follows decoded instructions and bounded RAM/DTCM accesses; normal scheduler bookkeeping is not claimed frozen'],
 'reproduction':['python tools/task_ag/preflight.py','powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ag/build.ps1','python tools/task_ag/check.py','python tools/task_ag/run.py --out local/task-ag/disabled-FRESH --disabled --port 19961','python tools/task_ag/run.py --out local/task-ag/session-FRESH --port 19962','python tools/task_ag/analyze.py --out local/task-ag/session-FRESH --disabled local/task-ag/disabled-FRESH --export docs/BrainAge_TaskAG_Result.json'],
 'recommended_next_smallest_task':'If separately authorized, audit exactly the idempotent STR at 0x0202624C to exercise +0x34 (0xDA -> 0xDA) and stop before 0x02026250. No inner BL.',
 'stop':'Task AG only; no Task AH or gameplay continuation'
}
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'classification':'FULL PASS','new_instructions':8,'stop':'0x0202624C','STR_dispatched':False,'mainram_changed_bytes':0,'dtcm_byte_diffs':byte_diffs,'accounting':result['accounting']}))
