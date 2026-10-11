"""Exhaustive AU audit against frozen AT and independently retained AS prefix."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def h(s):return int(s,16)
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--disabled',type=Path,required=True);a.add_argument('--export',type=Path,required=True);args=a.parse_args()
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-au') and disabled.is_relative_to(ROOT/'local/task-au')
x=load(ROOT/'tools/task_au/expected.json');assert x==load(ROOT/'docs/BrainAge_TaskAT_Result.json')
pre=load(ROOT/'local/task-au/preflight.json');assert pre['safe'] and pre['model_sha256']==sha((ROOT/'tools/task_au/expected.json').read_bytes())
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
prior=load(ROOT/'docs/BrainAge_TaskAS_Result.json')
prior_audit=rows(ROOT/prior['authoritative_path']/'audit.jsonl')
for name in ['aq_step','aq_read_event','aq_write_event','as_step','as_read_event','as_write_event']:
 assert [v for v in audit if v['event']==name]==[v for v in prior_audit if v['event']==name],name
start=event('au_before');assert start==dict(x['entry'],event='au_before')
steps=[v for v in audit if v['event']=='au_step'];assert len(steps)==8
for i,v in enumerate(steps):
 expected=x['prefix'][i] if i<7 else {'pc':x['AU']['stop_pc'],'opcode':x['AU']['forbidden_next']['opcode'],'r_before':x['AU']['r'],'nzcv_before':x['AU']['nzcv']}
 assert v['pc']==h(expected['pc']) and v['opcode']==h(expected['opcode']) and v['r']==list(map(h,expected['r_before']))
 assert [v[k] for k in ['n','z','c','v']]==expected['nzcv_before']
 assert [v[k] for k in ['t','mode','i','f']]==[0,31,0,0] and v['insn9']==281098001+i
 if i<7:
  nxt=x['prefix'][i]['r_after'];assert steps[i+1]['r']==list(map(h,nxt))
stop=steps[-1]
reads=[v for v in audit if v['event']=='au_read_event'];expected_reads=[]
for i,v in enumerate(x['prefix']):
 expected_reads.append(dict(event='au_read_event',index=i,pc=h(v['pc']),address=h(v['pc']),width=4,value=h(v['opcode'])))
 for q in x['AU']['data_reads']:
  if q['pc']==v['pc']:expected_reads.append(dict(event='au_read_event',index=i,pc=h(q['pc']),address=h(q['address']),width=q['width'],value=h(q['value'])))
assert len(reads)==9 and reads==expected_reads
writes=[v for v in audit if v['event']=='au_write_event'];expected_writes=[]
for i,v in enumerate(x['prefix']):
 for q in [q for q in x['AU']['stores'] if q['pc']==v['pc']]:
  expected_writes.append(dict(event='au_write_event',index=i,pc=h(q['pc']),opcode=h(q['opcode']),address=h(q['address']),width=q['width'],source_register=14 if q['source']=='LR' else int(q['source'][1:]),before=h(q['before']),after=h(q['after'])))
assert len(writes)==1 and writes==expected_writes
assert sum(w['before']!=w['after'] for w in writes)==1 and sum(w['before']==w['after'] for w in writes)==0
# Verify interleaved actual access ordering, independently of separate read/write ledgers.
access=[v for v in audit if v['event'] in ('au_step','au_read_event','au_write_event')];pos=0
for i in range(8):
 assert access[pos]==steps[i];pos+=1
 if i<7:
  for q in [v for v in expected_reads if v['index']==i]:assert access[pos]==q;pos+=1
  for q in [v for v in expected_writes if v['index']==i]:assert access[pos]==q;pos+=1
assert pos==len(access)
b=(out/'au-before-mainram.bin').read_bytes();e=(out/'decision-after-mainram.bin').read_bytes();dt=(out/'au-before-dtcm.bin').read_bytes();de=(out/'decision-after-dtcm.bin').read_bytes()
assert len(b)==len(e)==0x400000 and len(dt)==len(de)==0x4000
assert sha(b)==x['entry_hashes']['mainram'] and sha(dt)==x['entry_hashes']['dtcm'] and b==e
expected=bytearray(dt)
for w in writes:
 off=w['address']-0x027e0000;width=w['width'];assert int.from_bytes(expected[off:off+width],'little')==w['before'];expected[off:off+width]=w['after'].to_bytes(width,'little')
assert bytes(expected)==de and sha(de)==x['AU']['dtcm_after_sha256']
changes=[dict(address=f'0x{0x027e0000+i:08X}',before=u,after=v) for i,(u,v) in enumerate(zip(dt,de)) if u!=v]
assert changes==x['AU']['dtcm_byte_diffs'] and len(changes)==2
fields=[]
for q in x['AU']['mapped_fields']:
 off=h(q['address'])-0x02000000;width=q['width'];u=int.from_bytes(b[off:off+width],'little');v=int.from_bytes(e[off:off+width],'little');assert (u,v)==(q['before'],q['after']);fields.append(q)
save=(out/'au-before.sav').read_bytes();assert sha(save)==x['entry_hashes']['save']
for path in [out,disabled]:
 for name in ['initial.sav','session.sav','final.sav']:assert (path/name).read_bytes()==save
 assert not (path/'requests.jsonl').stat().st_size and not (path/'flash.jsonl').stat().st_size
 assert not any(v.get('save_dirty',False) for v in rows(path/'audit.jsonl'))
assert (out/'decision-after.sav').read_bytes()==save
assert [v['event'] for v in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert not ds['input_events'] and (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()
before=event('au_before_sample');after=event('decision_stop_sample')
for key in ['insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents']:assert before[key]==after[key],key
assert before['insn9']==281098001 and before['cycle9']==3416875700 and before['cycle7']==1708437825
account={k:dict(before=before[k],after=after[k],delta=after[k]-before[k]) for k in ['insn9','cycle9','insn7','cycle7']};assert account['insn9']['delta']==7
assert event('decision_stopped')==dict(event='decision_stopped',au_instructions=7,au_writes=1,au_reads=9,successor_fetched=False,successor_dispatched=False)
assert not any(v['pc']==0x02001980 for v in reads) and not any(v['pc']==0x02001980 for v in steps[:-1])
# Reused real SDL causal input and isolated service lifecycle remain authoritative.
assert len(s['input_events'])==10
old_session=load(ROOT/ao['authoritative_path']/'session.json');assert s['input_events']==old_session['input_events']
for path in ['definition_sha256','source_state_sha256','source_save_sha256']:assert s[path]==old_session[path]
assert event('service_cleanup')['cpu_equal'] and event('service_cleanup')['live_ram_equal'] and not event('service_cleanup')['active']
assert (out/'hold-mainram.bin').read_bytes()==(out/'service-clean-mainram.bin').read_bytes()
assert [v['integer'] for v in audit if v['event']=='recognition']==[2,4]
installed={}
for src,dst in [('diagnostic.h','brainage_task_au.h'),('guard.h','task_au_guard.h'),('task_au_decision.inc','task_au_decision.inc'),('slice_guard.h','task_au_slice_guard.h'),('slice.inc','task_au_slice.inc'),('entry_guard.h','task_au_entry_guard.h'),('entry.inc','task_au_entry.inc'),('setup_guard.h','task_au_setup_guard.h'),('setup.inc','task_au_setup.inc')]:
 text=(ROOT/'tools/task_au'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=sha(text.encode())
deltas=[dict(register=('SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i)),before=f'0x{u:08X}',after=f'0x{v:08X}') for i,(u,v) in enumerate(zip(start['r'],stop['r'])) if u!=v]
classified=[dict(q,actual_match=True,actual_event=w) for q,w in zip(x['AU']['stores'],writes)]
result=dict(task='AU',classification='FULL PASS',authoritative_AT_commit=pre['AT_commit'],authoritative_AS_commit=pre['AS_commit'],branch='codex/brainage',rom_sha1=x['rom_sha1'],framework_baseline=x['framework_baseline'],evidence_tier='Forced Tier-3 exact-context original ARM interpreter; no compiled parity',authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),model_sha256=pre['model_sha256'],complete_AS_prefix_exact=True,prior_decision_observations=112,prior_AQ_observations=46,prior_AS_observations=12,entry_hashes=x['entry_hashes'],au_start=start,au_stop=stop,executed_instruction_count=7,executed_pcs=x['AU']['pc_sequence'],instruction_observations=steps,architectural_stores=classified,value_changing_stores=1,idempotent_stores=0,entry_call=x['call'],setup_call=dict(pc='0x02001A1C',opcode='0xEBFFFFD4',target='0x02001974',created_LR='0x02001A20',actual_match=True),frame=dict(SP_before='0x027E365C',SP_after='0x027E3654',allocated_bytes=8,saved_LR_address='0x027E3658',actual_match=True),returns=[],bus_reads=reads,data_reads=x['AU']['data_reads'],forbidden_next=dict(x['AU']['forbidden_next'],interpreter_fetched=False,dispatched=False,MMIO_accessed=False),register_deltas=deltas,flags_before=x['prefix'][0]['nzcv_before'],flags_after=x['AU']['nzcv'],memory=dict(mainram_changed_bytes=0,dtcm_changed_bytes=2,byte_changes=[],dtcm_byte_changes=changes,mapped_fields=fields,mainram_before_sha256=sha(b),mainram_after_sha256=sha(e),dtcm_before_sha256=sha(dt),dtcm_after_sha256=sha(de)),save=dict(before_sha256=sha(save),after_sha256=sha(save),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,MMIO_ledger=[],unexpected_writes=0,video_touch_scene_unchanged=True,gameplay_resumed=False,score_count_phase_history_unchanged=True,extra_effect_beyond_certified_offset_stores=False),accounting=account,focused_tests=load(ROOT/'local/task-au/focused-tests.json'),disabled_control_pass=True,runner_sha256=s['runner_sha256'],installed_source_sha256=installed,limitations=['Forced Tier-3 frozen exact context; no compiled parity','Only the entry prologue is validated; whole callee MMIO/termination is not certified','No first MMIO STRH fetched/dispatched; no return or gameplay resume','ARM7 cycles observed rather than claimed frozen'],next_smallest_task='Separately authorized static safety analysis of the pending divider Write16 and modeled time/polling boundary; no MMIO execution or successor task started')
args.export.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':'FULL PASS','AU_dispatches':7,'writes':1,'RAM_bytes':0,'DTCM_bytes':2,'accounting':account}))
