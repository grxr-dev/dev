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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-an') and disabled.is_relative_to(ROOT/'local/task-an')
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
tests=read(ROOT/'local/task-an/focused-tests.json');assert all(v.startswith('PASS') for v in tests.values())
assert not session.get('forced_cleanup') and not control.get('forced_cleanup')
assert digest((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==session['runner_sha256']==control['runner_sha256']


al=read(ROOT/'docs/BrainAge_TaskAL_Result.json');am=read(ROOT/'docs/BrainAge_TaskAM_Result.json');model=read(ROOT/'tools/task_an/expected.json');proof=read(ROOT/'local/task-an/preflight.json')
assert proof['safe'] and proof['model_sha256']==digest((ROOT/'tools/task_an/expected.json').read_bytes())
assert model['facts']==am['prefix']+[am['first_next_meaningful_action']]
installed={}
for src,dst in [('diagnostic.h','brainage_task_an.h'),('guard.h','task_an_guard.h'),('task_an_decision.inc','task_an_decision.inc')]:
 text=(ROOT/'tools/task_an'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=digest(text.encode())
steps=[r for r in audit if r['event']=='decision_step'];old=[r for r in rows(ROOT/al['authoritative_path']/'audit.jsonl') if r['event']=='decision_step']
assert len(steps)==111 and steps[:92]==old and steps[91]==al['al_stop']==am['entry']
assert [r['insn9']-steps[0]['insn9'] for r in steps]==list(range(111))
start=event('an_before');stop=steps[-1];x=event('an_before_sample');y=event('decision_stop_sample')
assert start==dict(steps[91],event='an_before')
trace=[]
for i,(actual,expected,fact) in enumerate(zip(steps[91:],model['states'],model['facts'])):
 assert actual['pc']==int(fact['pc'],16) and actual['opcode']==int(fact['opcode'],16) and actual['r']==expected['r']
 assert [actual[k] for k in ['n','z','c','v']]==expected['nzcv'] and [actual[k] for k in ['t','mode','i','f']]==[0,31,0,0]
 assert actual['insn9']==281097925+i
 trace.append({**actual,'decoded':fact['decoded'],'effect':fact['effect'],'dispatched':i<19})
assert [f'0x{r["pc"]:08X}' for r in trace[:-1]]==am['an']['pc_sequence'] and stop['r']==[int(v,16) for v in am['an']['r']]
assert stop['pc']==0x02067c44 and stop['opcode']==0xe5840250 and stop['insn9']==281097944
observed=[r for r in audit if r['event']=='an_read_event']
assert observed==[dict(event='an_read_event',pc=e['pc'],address=e['address'],width=4,value=e['value']) for e in model['reads']] and len(observed)==22
object_reads=[{**a,'class':'object_read'} for a in observed if a['address']!=a['pc']];assert len(object_reads)==3
# Every actual read falls between its exact pre/post CPU observations.
for actual,e in zip(observed,model['reads']):assert audit.index(steps[91+e['index']])<audit.index(actual)<audit.index(steps[92+e['index']])
assert not any(r['event'].endswith('write_event') for r in audit[audit.index(start):])
assert event('al_write_event')==al['store_event'] and audit.index(event('al_write_event'))<audit.index(start)
assert [r for r in audit if r['event']=='ak_write_event']==read(ROOT/'docs/BrainAge_TaskAK_Result.json')['memory']['write_events']
assert len([r for r in audit if r['event']=='al_read_event'])==1
b=(out/'an-before-mainram.bin').read_bytes();e=(out/'decision-after-mainram.bin').read_bytes();dt=(out/'an-before-dtcm.bin').read_bytes();de=(out/'decision-after-dtcm.bin').read_bytes()
assert len(b)==len(e)==0x400000 and len(dt)==len(de)==0x4000 and b==e and dt==de
assert b==(ROOT/al['authoritative_path']/'decision-after-mainram.bin').read_bytes() and dt==(ROOT/al['authoritative_path']/'decision-after-dtcm.bin').read_bytes()
assert digest(b)==al['memory']['mainram_after_sha256']==am['an']['mainram_sha256'] and digest(dt)==al['memory']['dtcm_after_sha256']==am['an']['dtcm_sha256']
fields=[dict(f) for f in am['an']['mapped_fields']]
for offset,value in [(0x630,1),(0x5f0,0x44),(0x5d0,0x02131d24),(0x7c0,0x02133a18)]:fields.append(dict(offset=hex(offset),address=f'0x{0x020e9a00+offset:08X}',width=4,before=value,after=value))
for f in am['all_helper_tail_stores']:
 if any(int(v['address'],16)==int(f['address'],16) for v in fields):continue
 fields.append(dict(offset=f['exercise_offset'],address=f['address'],width=f['width'],before=int(f['before'],16),after=int(f['before'],16)))
for f in fields:
 off=int(f['address'],16)-0x02000000;n=f['width'];assert int.from_bytes(b[off:off+n],'little')==int.from_bytes(e[off:off+n],'little')==f['before']==f['after']
assert struct.unpack_from('<I',e,0xea1c0)[0]==0x02133a18 and struct.unpack_from('<I',e,0xea1c4)[0]==0
for name in ('an-before.sav','decision-after.sav','initial.sav','session.sav','final.sav'):assert (out/name).read_bytes()==save
for k in ['insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents']:assert x[k]==y[k]
assert x['insn9']==281097925 and x['cycle9']==3416875515 and x['insn7']==96026779 and x['cycle7']==1708437703
account={k:dict(before=x[k],after=y[k],delta=y[k]-x[k]) for k in ['insn9','cycle9','insn7','cycle7']};assert account['insn9']['delta']==19 and account['insn7']['delta']==0
assert event('decision_stopped')==dict(event='decision_stopped',an_instructions=19,an_writes=0,forbidden_store_dispatched=False)
assert event('disposable_exit')['code']==0 and not event('disposable_exit')['save_dirty']
assert [r['event'] for r in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()==before
assert not (disabled/'frontend-input.jsonl').stat().st_size and not control['input_events']
for name in ('initial.sav','session.sav','final.sav'):assert (disabled/name).read_bytes()==save
assert (out/'source.state').read_bytes()==(disabled/'source.state').read_bytes()==(source/'checkpoint.state').read_bytes()
deltas=[dict(register='SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i),before=f"0x{start['r'][i]:08X}",after=f"0x{stop['r'][i]:08X}") for i in range(16) if start['r'][i]!=stop['r'][i]]
assert [d['register'] for d in deltas]==['r0','r1','PC']
result=dict(task='AN - dynamic 19-instruction post-AL prefix',classification='FULL PASS',branch='codex/brainage',authoritative_am_commit='cb2126cfa0c2e75714b993cdc0124c49c8e1b680',authoritative_al_commit='7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70',authoritative_ak_commit='dd29b71e182611fb73016aa1a13367e70c9cd290',rom_sha1=al['rom_sha1'],framework_baseline=al['framework_baseline'],evidence_tier='Forced Tier-3 exact-context original ARM interpreter; no compiled parity',authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),complete_AL_prefix_exact=True,AL_full_CPU_ROM_RAM_DTCM_save_ordinals_revalidated=True,al_start=start,an_stop=stop,executed_pcs=am['an']['pc_sequence'],trace=trace,terminal_pc='0x02067C44',terminal_dispatched=False,forbidden_store=am['first_next_meaningful_action'],AN_instruction_count=19,decision_dispatches=110,decision_observations=111,register_deltas=deltas,flags_before=[0,0,1,0],flags_after=[1,0,0,0],memory=dict(mainram_changed_bytes=0,dtcm_changed_bytes=0,architectural_writes=0,write_events=[],read_events=observed,object_reads=object_reads,instruction_fetches=19,mapped_fields=fields,mainram_before_sha256=digest(b),mainram_after_sha256=digest(e),dtcm_before_sha256=digest(dt),dtcm_after_sha256=digest(de)),save=dict(before_sha256=digest(save),after_sha256=digest(save),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,unexpected_writes=0,calls=0,returns=0,peripheral_effect_attributable_to_AN=False,gameplay_resumed=False,score_count_phase_progression_history_result_completion_effect=False,video_touch_scene_unchanged=True),accounting=account,source_checkpoint_sha256=digest((source/'checkpoint.state').read_bytes()),input_sha256=freeze['sha256'],native_SDL_events=10,custom_guest_touch_deliveries=0,disabled_control_pass=True,focused_tests=tests,runner_sha256=session['runner_sha256'],installed_source_sha256=installed,model_sha256=proof['model_sha256'],exit_code=0,forced_cleanup=False,limitations=['Frozen 11 - 7 / recognized-4 context only','Forced original interpreter; no compiled parity','No forbidden pointer store, helper return or gameplay completion','Unknown fields retain offset-only semantics','ARM7 cycle counter advanced by 64 with zero ARM7 instructions; no scheduler refactor or broader accounting investigation'],next_smallest_task='Separately audit the pending 0x02067C44 store to exercise+0x7C0, 0x02133A18 -> 0x02132750, and stop before its successor. Task AO not started.')
args.export.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(classification='FULL PASS',terminal_pc='0x02067C44',object_reads=object_reads,memory_diff=[0,0],accounting=account)))
