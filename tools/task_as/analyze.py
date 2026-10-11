"""Exhaustive AS audit against frozen AR and independently retained AQ prefix."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def h(s):return int(s,16)
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--disabled',type=Path,required=True);a.add_argument('--export',type=Path,required=True);args=a.parse_args()
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-as') and disabled.is_relative_to(ROOT/'local/task-as')
x=load(ROOT/'tools/task_as/expected.json');assert x==load(ROOT/'docs/BrainAge_TaskAR_Result.json')
pre=load(ROOT/'local/task-as/preflight.json');assert pre['safe'] and pre['model_sha256']==sha((ROOT/'tools/task_as/expected.json').read_bytes())
ao=load(ROOT/'docs/BrainAge_TaskAO_Result.json');audit=rows(out/'audit.jsonl');s=load(out/'session.json');ds=load(disabled/'session.json')
assert s['pass'] and ds['pass'] and s['exit_code']==ds['exit_code']==0 and not s.get('forced_cleanup') and not ds.get('forced_cleanup')
assert s['runner_sha256']==ds['runner_sha256']==sha((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())
assert not any(v['event']=='failure' for v in audit)
def event(n):
 v=[q for q in audit if q['event']==n];assert len(v)==1,n;return v[0]
old=[v for v in rows(ROOT/ao['authoritative_path']/'audit.jsonl') if v['event']=='decision_step']
replay=[v for v in audit if v['event']=='decision_step'];assert len(replay)==112 and replay==old
assert replay[-1]==ao['ao_stop']
for name in ['ao_write_event','an_read_event','ak_write_event']:
 assert [v for v in audit if v['event']==name]==[v for v in rows(ROOT/ao['authoritative_path']/'audit.jsonl') if v['event']==name]
prior=load(ROOT/'docs/BrainAge_TaskAQ_Result.json')
prior_audit=rows(ROOT/prior['authoritative_path']/'audit.jsonl')
for name in ['aq_step','aq_read_event','aq_write_event']:
 assert [v for v in audit if v['event']==name]==[v for v in prior_audit if v['event']==name],name
start=event('as_before');assert start==dict(x['entry'],event='as_before')
steps=[v for v in audit if v['event']=='as_step'];assert len(steps)==12
for i,v in enumerate(steps):
 expected=x['instructions'][i] if i<11 else {'pc':x['AS']['stop_pc'],'opcode':x['forbidden_next']['opcode'],'r_before':x['AS']['r'],'nzcv_before':x['AS']['nzcv']}
 assert v['pc']==h(expected['pc']) and v['opcode']==h(expected['opcode']) and v['r']==list(map(h,expected['r_before']))
 assert [v[k] for k in ['n','z','c','v']]==expected['nzcv_before']
 assert [v[k] for k in ['t','mode','i','f']]==[0,31,0,0] and v['insn9']==281097990+i
 if i<11:
  nxt=x['instructions'][i]['r_after'];assert steps[i+1]['r']==list(map(h,nxt))
stop=steps[-1]
reads=[v for v in audit if v['event']=='as_read_event'];expected_reads=[]
for i,v in enumerate(x['instructions']):
 expected_reads.append(dict(event='as_read_event',index=i,pc=h(v['pc']),address=h(v['pc']),width=4,value=h(v['opcode'])))
 for q in x['data_reads']:
  if q['pc']==v['pc']:expected_reads.append(dict(event='as_read_event',index=i,pc=h(q['pc']),address=h(q['address']),width=q['width'],value=h(q['value'])))
assert len(reads)==16 and reads==expected_reads
writes=[v for v in audit if v['event']=='as_write_event'];expected_writes=[]
for i,v in enumerate(x['instructions']):
 for q in v.get('stores',[]):
  expected_writes.append(dict(event='as_write_event',index=i,pc=h(q['pc']),opcode=h(q['opcode']),address=h(q['address']),width=q['width'],source_register=14 if q['source']=='LR' else int(q['source'][1:]),before=h(q['before']),after=h(q['after'])))
assert len(writes)==10 and writes==expected_writes
assert sum(w['before']!=w['after'] for w in writes)==8 and sum(w['before']==w['after'] for w in writes)==2
# Verify interleaved actual access ordering, independently of separate read/write ledgers.
access=[v for v in audit if v['event'] in ('as_step','as_read_event','as_write_event')];pos=0
for i in range(12):
 assert access[pos]==steps[i];pos+=1
 if i<11:
  for q in [v for v in expected_reads if v['index']==i]:assert access[pos]==q;pos+=1
  for q in [v for v in expected_writes if v['index']==i]:assert access[pos]==q;pos+=1
assert pos==len(access)
b=(out/'as-before-mainram.bin').read_bytes();e=(out/'decision-after-mainram.bin').read_bytes();dt=(out/'as-before-dtcm.bin').read_bytes();de=(out/'decision-after-dtcm.bin').read_bytes()
assert len(b)==len(e)==0x400000 and len(dt)==len(de)==0x4000
assert sha(b)==x['entry_hashes']['mainram'] and sha(dt)==x['entry_hashes']['dtcm'] and b==e
expected=bytearray(dt)
for w in writes:
 off=w['address']-0x027e0000;width=w['width'];assert int.from_bytes(expected[off:off+width],'little')==w['before'];expected[off:off+width]=w['after'].to_bytes(width,'little')
assert bytes(expected)==de
changes=[dict(address=f'0x{0x027e0000+i:08X}',before=u,after=v) for i,(u,v) in enumerate(zip(dt,de)) if u!=v]
assert changes==x['AS']['dtcm_byte_diffs'] and len(changes)==21
fields=[]
for q in x['AS']['mapped_fields']:
 off=h(q['address'])-0x02000000;width=q['width'];u=int.from_bytes(b[off:off+width],'little');v=int.from_bytes(e[off:off+width],'little');assert (u,v)==(q['before'],q['after']);fields.append(q)
save=(out/'as-before.sav').read_bytes();assert sha(save)==x['entry_hashes']['save']
for path in [out,disabled]:
 for name in ['initial.sav','session.sav','final.sav']:assert (path/name).read_bytes()==save
 assert not (path/'requests.jsonl').stat().st_size and not (path/'flash.jsonl').stat().st_size
 assert not any(v.get('save_dirty',False) for v in rows(path/'audit.jsonl'))
assert (out/'decision-after.sav').read_bytes()==save
assert [v['event'] for v in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert not ds['input_events'] and (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()
before=event('as_before_sample');after=event('decision_stop_sample')
for key in ['insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents']:assert before[key]==after[key],key
assert before['insn9']==281097990 and before['cycle9']==3416875664 and before['cycle7']==1708437825
account={k:dict(before=before[k],after=after[k],delta=after[k]-before[k]) for k in ['insn9','cycle9','insn7','cycle7']};assert account['insn9']['delta']==11
assert event('decision_stopped')==dict(event='decision_stopped',as_instructions=11,as_writes=10,as_reads=16,successor_fetched=False,successor_dispatched=False)
assert not any(v['pc']==0x02067564 for v in reads) and not any(v['pc']==0x02001a14 for v in steps)
# Reused real SDL causal input and isolated service lifecycle remain authoritative.
assert len(s['input_events'])==10
old_session=load(ROOT/ao['authoritative_path']/'session.json');assert s['input_events']==old_session['input_events']
for path in ['definition_sha256','source_state_sha256','source_save_sha256']:assert s[path]==old_session[path]
assert event('service_cleanup')['cpu_equal'] and event('service_cleanup')['live_ram_equal'] and not event('service_cleanup')['active']
assert (out/'hold-mainram.bin').read_bytes()==(out/'service-clean-mainram.bin').read_bytes()
assert [v['integer'] for v in audit if v['event']=='recognition']==[2,4]
installed={}
for src,dst in [('diagnostic.h','brainage_task_as.h'),('guard.h','task_as_guard.h'),('task_as_decision.inc','task_as_decision.inc'),('slice_guard.h','task_as_slice_guard.h'),('slice.inc','task_as_slice.inc'),('entry_guard.h','task_as_entry_guard.h'),('entry.inc','task_as_entry.inc')]:
 text=(ROOT/'tools/task_as'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=sha(text.encode())
deltas=[dict(register=('SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i)),before=f'0x{u:08X}',after=f'0x{v:08X}') for i,(u,v) in enumerate(zip(start['r'],stop['r'])) if u!=v]
classified=[dict(q,actual_match=True,actual_event=w) for q,w in zip(x['stores'],writes)]
result=dict(task='AS',classification='FULL PASS',authoritative_AR_commit=pre['AR_commit'],authoritative_AQ_commit=pre['AQ_commit'],branch='codex/brainage',rom_sha1=x['rom_sha1'],framework_baseline=x['framework_baseline'],evidence_tier='Forced Tier-3 exact-context original ARM interpreter; no compiled parity',authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),model_sha256=pre['model_sha256'],complete_AQ_prefix_exact=True,prior_decision_observations=112,prior_AQ_observations=46,entry_hashes=x['entry_hashes'],as_start=start,as_stop=stop,executed_instruction_count=11,executed_pcs=x['AS']['pc_sequence'],instruction_observations=steps,architectural_stores=classified,value_changing_stores=8,idempotent_stores=2,entry_call=x['call'],returns=x['returns'],bus_reads=reads,data_reads=x['data_reads'],forbidden_next=dict(x['forbidden_next'],interpreter_fetched=False,dispatched=False,target_entered=False),register_deltas=deltas,flags_before=x['instructions'][0]['nzcv_before'],flags_after=x['AS']['nzcv'],memory=dict(mainram_changed_bytes=0,dtcm_changed_bytes=21,byte_changes=[],dtcm_byte_changes=changes,mapped_fields=fields,mainram_before_sha256=sha(b),mainram_after_sha256=sha(e),dtcm_before_sha256=sha(dt),dtcm_after_sha256=sha(de)),save=dict(before_sha256=sha(save),after_sha256=sha(save),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,unexpected_writes=0,video_touch_scene_unchanged=True,gameplay_resumed=False,score_count_phase_history_unchanged=True,extra_effect_beyond_certified_offset_stores=False),accounting=account,focused_tests=load(ROOT/'local/task-as/focused-tests.json'),disabled_control_pass=True,runner_sha256=s['runner_sha256'],installed_source_sha256=installed,limitations=['Forced Tier-3 frozen exact context; no compiled parity','Only the entry prologue is validated; whole callee MMIO/termination is not certified','No nested BL fetched/dispatched; no return or gameplay resume','ARM7 cycles observed rather than claimed frozen'],next_smallest_task='Read-only analysis of nested call 02067564 -> 02001A14 and required MMIO model/safety boundary; no successor task started')
args.export.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':'FULL PASS','AS_dispatches':11,'writes':10,'RAM_bytes':0,'DTCM_bytes':21,'accounting':account}))
