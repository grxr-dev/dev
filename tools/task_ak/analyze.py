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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-ak') and disabled.is_relative_to(ROOT/'local/task-ak')
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
tests=read(ROOT/'local/task-ak/focused-tests.json');assert all(v['pass'] for v in tests.values())
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']

installed={}
for src,dst in [('diagnostic.h','brainage_task_ak.h'),('guard.h','task_ak_guard.h'),('task_ak_decision.inc','task_ak_decision.inc')]:
 text=(ROOT/'tools/task_ak'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=digest(text.encode())
ai=read(ROOT/'docs/BrainAge_TaskAI_Result.json');aj=read(ROOT/'docs/BrainAge_TaskAJ_Result.json');model=read(ROOT/'tools/task_ak/expected.json')
proof=read(ROOT/'local/task-ak/preflight.json');assert proof['safe'] and proof['model_sha256']==digest((ROOT/'tools/task_ak/expected.json').read_bytes())
assert model['facts']==aj['instruction_facts'][:26] and model['writes']==aj['stack_writes']
steps=[r for r in audit if r['event']=='decision_step'];previous=[r for r in rows(ROOT/'local/task-ai/session-001/audit.jsonl') if r['event']=='decision_step']
assert len(steps)==91 and steps[:66]==previous and steps[65]==ai['ai_stop']
assert [s['insn9']-steps[0]['insn9'] for s in steps]==list(range(91))
start=event('ak_before');start_sample=event('ak_before_sample');stop=steps[-1];stop_sample=event('decision_stop_sample')
assert start==dict(steps[65],event='ak_before')
trace=[]
for index,(actual,expected,fact) in enumerate(zip(steps[65:],model['states'],model['facts'])):
 assert actual['r']==expected['r'] and actual['pc']==int(fact['pc'],16) and actual['opcode']==int(fact['opcode'],16)
 assert [actual[k] for k in ['n','z','c','v']]==expected['nzcv']
 assert [actual[k] for k in ['t','mode','i','f']]==[0,31,0,0]
 assert actual['insn9']==281097899+index
 trace.append({**actual,'decoded':fact['decoded'],'dispatched':index<25})
assert len(trace)==26 and stop['pc']==0x02067bdc and stop['opcode']==0xe5842254
writes=[r for r in audit if r['event']=='ak_write_event'];assert len(writes)==8
for actual,expected in zip(writes,model['writes']):
 assert actual==dict(event='ak_write_event',pc=int(expected['pc'],16),opcode=0xe92d41f0 if expected['pc']=='0x02025F78' else 0xe92d4010,address=int(expected['address'],16),width=4,source_register=14 if expected['source']=='lr' else int(expected['source'][1:]),before=int(expected['before'],16),after=int(expected['after'],16))
 assert audit.index(steps[66 if actual['pc']==0x02025f78 else 88])<audit.index(actual)<audit.index(steps[67 if actual['pc']==0x02025f78 else 89])
reads=[r for r in audit if r['event']=='ak_read_event']
expected_reads=[]
for index,fact in enumerate(model['facts'][:25]):
 pc=int(fact['pc'],16);expected_reads.append(dict(event='ak_read_event',pc=pc,address=pc,width=4,value=int(fact['opcode'],16)))
 for ri,address,value in model['reads']:
  if ri==index:expected_reads.append(dict(event='ak_read_event',pc=pc,address=address,width=4,value=value))
assert reads==expected_reads and len(reads)==31
before_ram=(out/'ak-before-mainram.bin').read_bytes();after_ram=(out/'decision-after-mainram.bin').read_bytes()
before_dtcm=(out/'ak-before-dtcm.bin').read_bytes();after_dtcm=(out/'decision-after-dtcm.bin').read_bytes()
assert len(before_ram)==len(after_ram)==0x400000 and len(before_dtcm)==len(after_dtcm)==0x4000
assert before_ram==after_ram==(ROOT/'local/task-ai/session-001/decision-after-mainram.bin').read_bytes()
assert before_dtcm==(ROOT/'local/task-ai/session-001/decision-after-dtcm.bin').read_bytes()
assert digest(before_ram)==ai['memory']['mainram_after_sha256'] and digest(before_dtcm)==ai['memory']['dtcm_after_sha256']
projection=bytearray(before_dtcm)
for w in writes:
 off=w['address']-0x027e0000;assert struct.unpack_from('<I',before_dtcm,off)[0]==w['before'];struct.pack_into('<I',projection,off,w['after'])
assert after_dtcm==projection and digest(after_dtcm)==aj['ak']['predicted_dtcm_sha256']
byte_diffs=[dict(address=f'0x{0x027e0000+i:08X}',before=a,after=b) for i,(a,b) in enumerate(zip(before_dtcm,after_dtcm)) if a!=b]
assert byte_diffs==aj['ak']['dtcm_byte_changes'] and len(byte_diffs)==28
fields=aj['ak']['mapped_fields']
for field in fields:
 off=int(field['address'],16)-0x02000000;n=field['width'];assert int.from_bytes(before_ram[off:off+n],'little')==int.from_bytes(after_ram[off:off+n],'little')==field['before']==field['after']
for name,base,size in [('exercise',0x020e9a00,0xc34),('manager',0x020fa808,0x238),('slot',0x020faa50,0x370)]:assert (out/(name+'-decision.bin')).read_bytes()==before_ram[base-0x02000000:base-0x02000000+size]
for name in ('ak-before.sav','decision-after.sav','initial.sav','session.sav','final.sav'):assert (out/name).read_bytes()==save
assert [r['event'] for r in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()==before
assert not (disabled/'frontend-input.jsonl').stat().st_size and not control['input_events']
for name in ('initial.sav','session.sav','final.sav'):assert (disabled/name).read_bytes()==save
assert (out/'source.state').read_bytes()==(disabled/'source.state').read_bytes()==(source/'checkpoint.state').read_bytes()
for key in ('insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents'):assert start_sample[key]==stop_sample[key]
for k,s in [('insn9',281097899),('insn7',96026779),('cycle9',3416875451),('cycle7',1708437703)]:assert start_sample[k]==s
assert event('decision_stopped')==dict(event='decision_stopped',instructions=90,ak_instructions=25,ak_writes=8,forbidden_store_dispatched=False)
assert event('disposable_exit')['code']==0 and not event('disposable_exit')['save_dirty']
deltas=[dict(register='SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i),before=f"0x{start['r'][i]:08X}",after=f"0x{stop['r'][i]:08X}") for i in range(16) if start['r'][i]!=stop['r'][i]]
accounting={}
for cpu in (9,7):
 for metric,key in [('ordinal','insn'),('cycles','cycle')]:
  accounting[f'arm{cpu}_{metric}_before']=start_sample[key+str(cpu)];accounting[f'arm{cpu}_{metric}_after']=stop_sample[key+str(cpu)]
 accounting[f'arm{cpu}_instruction_delta']=stop_sample['insn'+str(cpu)]-start_sample['insn'+str(cpu)]
 accounting[f'arm{cpu}_cycle_delta']=stop_sample['cycle'+str(cpu)]-start_sample['cycle'+str(cpu)]
assert accounting['arm9_instruction_delta']==25 and accounting['arm7_instruction_delta']==accounting['arm7_cycle_delta']==0
result=dict(task='AK - dynamic 25-instruction inner-helper prefix',classification='FULL PASS',branch='codex/brainage',authoritative_aj_commit='a1d2c76baedc0ae841086eeccaf9aa5daebe8d16',authoritative_ai_commit='5e086cb667a87d41eda1aec016e6418a57f64356',rom_sha1=ai['rom_sha1'],framework_baseline=ai['framework_baseline'],evidence_tier='Forced Tier-3 exact-context original ARM interpreter; no compiled parity',authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),runner_sha256=session['runner_sha256'],installed_source_sha256_normalized_text=installed,complete_AI_prefix_exact=True,AI_CPU_RAM_DTCM_save_ROM_ordinals_revalidated=True,ai_start=start,ak_stop=stop,trace=trace,executed_pcs=[f['pc'] for f in model['facts'][:25]],terminal_pc='0x02067BDC',terminal_dispatched=False,AK_instruction_count=25,decision_observations=91,decision_dispatches=90,register_deltas=deltas,flags_before=[1,0,0,0],flags_after=[0,0,1,0],memory=dict(mainram_changed_bytes=0,object_global_writes=0,dtcm_changed_bytes=28,architectural_word_writes=8,written_bytes=32,write_events=writes,dtcm_byte_changes=byte_diffs,read_events=reads,instruction_fetches=25,object_reads=6,mapped_fields=fields,mainram_before_sha256=digest(before_ram),mainram_after_sha256=digest(after_ram),dtcm_before_sha256=digest(before_dtcm),dtcm_after_sha256=digest(after_dtcm),local_unwritten_range=aj['ak']['local_unwritten_range']),save=dict(before_sha256=digest(save),after_sha256=digest((out/'final.sav').read_bytes()),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,unexpected_writes=0,peripheral_effect_attributable_to_AK=False,gameplay_resumed=False,score_count_phase_progression_history_result_completion_effect=False,video_touch_scene_unchanged=True,full_helper_return=False),accounting=accounting,source_checkpoint_sha256=digest((source/'checkpoint.state').read_bytes()),input_sha256=freeze['sha256'],native_SDL_events=10,custom_guest_touch_deliveries=0,disabled_control={'pass':True,'input_events':0,'RAM_save_changes':0,'exit_code':0},focused_tests=tests,exit_code=0,forced_cleanup=False,limitations=['Exact frozen 11 - 7 / recognized-4 context only','Original interpreter only; no compiled parity','No forbidden object store, full helper return or gameplay-completion proof','Unknown fields retain offset-based descriptions'],recommended_next_smallest_task='Separately authorize and audit only the first value-changing store at 0x02067BDC to exercise+0x7C4 (1 -> 0), with a stop before its successor. Task AL not started.',stop='Stopped after AK; forbidden STR and Task AL not executed')
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(classification=result['classification'],terminal_pc=result['terminal_pc'],write_events=8,dtcm_changed_bytes=28,mainram_changed_bytes=0,accounting=accounting)))
