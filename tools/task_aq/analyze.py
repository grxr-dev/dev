"""Exhaustive AQ audit against frozen AP and independently retained AO prefix."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def h(s):return int(s,16)
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--disabled',type=Path,required=True);a.add_argument('--export',type=Path,required=True);args=a.parse_args()
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-aq') and disabled.is_relative_to(ROOT/'local/task-aq')
x=load(ROOT/'tools/task_aq/expected.json');assert x==load(ROOT/'docs/BrainAge_TaskAP_Result.json')
pre=load(ROOT/'local/task-aq/preflight.json');assert pre['safe'] and pre['model_sha256']==sha((ROOT/'tools/task_aq/expected.json').read_bytes())
ao=load(ROOT/'docs/BrainAge_TaskAO_Result.json');audit=rows(out/'audit.jsonl');s=load(out/'session.json');ds=load(disabled/'session.json')
assert s['pass'] and ds['pass'] and s['exit_code']==ds['exit_code']==0 and not s.get('forced_cleanup') and not ds.get('forced_cleanup')
assert s['runner_sha256']==ds['runner_sha256']==sha((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())
assert not any(v['event']=='failure' for v in audit)
def event(n):
 v=[q for q in audit if q['event']==n];assert len(v)==1,n;return v[0]
old=[v for v in rows(ROOT/ao['authoritative_path']/'audit.jsonl') if v['event']=='decision_step']
replay=[v for v in audit if v['event']=='decision_step'];assert len(replay)==112 and replay==old
assert replay[-1]==ao['ao_stop']==x['entry']
for name in ['ao_write_event','an_read_event','ak_write_event']:
 assert [v for v in audit if v['event']==name]==[v for v in rows(ROOT/ao['authoritative_path']/'audit.jsonl') if v['event']==name]
start=event('aq_before');assert start==dict(x['entry'],event='aq_before')
steps=[v for v in audit if v['event']=='aq_step'];assert len(steps)==46
for i,v in enumerate(steps):
 expected=x['instructions'][i] if i<45 else {'pc':x['aq']['stop_pc'],'opcode':x['forbidden_next']['opcode'],'r_before':x['aq']['r'],'nzcv_before':x['aq']['nzcv']}
 assert v['pc']==h(expected['pc']) and v['opcode']==h(expected['opcode']) and v['r']==list(map(h,expected['r_before']))
 assert [v[k] for k in ['n','z','c','v']]==expected['nzcv_before']
 assert [v[k] for k in ['t','mode','i','f']]==[0,31,0,0] and v['insn9']==281097945+i
 if i<45:
  nxt=x['instructions'][i]['r_after'];assert steps[i+1]['r']==list(map(h,nxt))
stop=steps[-1]
reads=[v for v in audit if v['event']=='aq_read_event'];expected_reads=[]
for i,v in enumerate(x['instructions']):
 expected_reads.append(dict(event='aq_read_event',index=i,pc=h(v['pc']),address=h(v['pc']),width=4,value=h(v['opcode'])))
 for q in x['data_reads']:
  if q['pc']==v['pc']:expected_reads.append(dict(event='aq_read_event',index=i,pc=h(q['pc']),address=h(q['address']),width=q['width'],value=h(q['value'])))
assert len(reads)==51 and reads==expected_reads
writes=[v for v in audit if v['event']=='aq_write_event'];expected_writes=[]
for i,v in enumerate(x['instructions']):
 if 'store' in v:
  q=v['store'];expected_writes.append(dict(event='aq_write_event',index=i,pc=h(q['pc']),opcode=h(q['opcode']),address=h(q['address']),width=q['width'],source_register=int(q['source'][1:]),before=h(q['before']),after=h(q['after'])))
assert len(writes)==18 and writes==expected_writes
assert sum(w['before']!=w['after'] for w in writes)==6 and sum(w['before']==w['after'] for w in writes)==12
# Verify interleaved actual access ordering, independently of separate read/write ledgers.
access=[v for v in audit if v['event'] in ('aq_step','aq_read_event','aq_write_event')];pos=0
for i in range(46):
 assert access[pos]==steps[i];pos+=1
 if i<45:
  for q in [v for v in expected_reads if v['index']==i]:assert access[pos]==q;pos+=1
  for q in [v for v in expected_writes if v['index']==i]:assert access[pos]==q;pos+=1
assert pos==len(access)
b=(out/'aq-before-mainram.bin').read_bytes();e=(out/'decision-after-mainram.bin').read_bytes();dt=(out/'aq-before-dtcm.bin').read_bytes();de=(out/'decision-after-dtcm.bin').read_bytes()
assert len(b)==len(e)==0x400000 and len(dt)==len(de)==0x4000
assert sha(b)==x['entry_hashes']['mainram'] and sha(dt)==x['entry_hashes']['dtcm'] and dt==de
expected=bytearray(b)
for w in writes:
 off=w['address']-0x02000000;width=w['width'];assert int.from_bytes(expected[off:off+width],'little')==w['before'];expected[off:off+width]=w['after'].to_bytes(width,'little')
assert bytes(expected)==e
changes=[dict(address=f'0x{0x02000000+i:08X}',before=u,after=v) for i,(u,v) in enumerate(zip(b,e)) if u!=v]
assert changes==x['aq']['byte_diffs'] and len(changes)==5
fields=[]
for q in x['aq']['mapped_fields']:
 off=h(q['address'])-0x02000000;width=q['width'];u=int.from_bytes(b[off:off+width],'little');v=int.from_bytes(e[off:off+width],'little');assert (u,v)==(q['before'],q['after']);fields.append(q)
save=(out/'aq-before.sav').read_bytes();assert sha(save)==x['entry_hashes']['save']
for path in [out,disabled]:
 for name in ['initial.sav','session.sav','final.sav']:assert (path/name).read_bytes()==save
 assert not (path/'requests.jsonl').stat().st_size and not (path/'flash.jsonl').stat().st_size
 assert not any(v.get('save_dirty',False) for v in rows(path/'audit.jsonl'))
assert (out/'decision-after.sav').read_bytes()==save
assert [v['event'] for v in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert not ds['input_events'] and (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes()
before=event('aq_before_sample');after=event('decision_stop_sample')
for key in ['insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents']:assert before[key]==after[key],key
assert before['insn9']==281097945 and before['cycle9']==3416875553 and before['cycle7']==1708437767
account={k:dict(before=before[k],after=after[k],delta=after[k]-before[k]) for k in ['insn9','cycle9','insn7','cycle7']};assert account['insn9']['delta']==45
assert event('decision_stopped')==dict(event='decision_stopped',aq_instructions=45,aq_writes=18,aq_reads=51,successor_fetched=False,successor_dispatched=False)
assert not any(v['pc']==0x02026044 for v in reads) and not any(v['pc']==0x0206753c for v in steps)
# Reused real SDL causal input and isolated service lifecycle remain authoritative.
assert len(s['input_events'])==10
old_session=load(ROOT/ao['authoritative_path']/'session.json');assert s['input_events']==old_session['input_events']
for path in ['definition_sha256','source_state_sha256','source_save_sha256']:assert s[path]==old_session[path]
assert event('service_cleanup')['cpu_equal'] and event('service_cleanup')['live_ram_equal'] and not event('service_cleanup')['active']
assert (out/'hold-mainram.bin').read_bytes()==(out/'service-clean-mainram.bin').read_bytes()
assert [v['integer'] for v in audit if v['event']=='recognition']==[2,4]
installed={}
for src,dst in [('diagnostic.h','brainage_task_aq.h'),('guard.h','task_aq_guard.h'),('task_aq_decision.inc','task_aq_decision.inc'),('slice_guard.h','task_aq_slice_guard.h'),('slice.inc','task_aq_slice.inc')]:
 text=(ROOT/'tools/task_aq'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=sha(text.encode())
deltas=[dict(register=('SP' if i==13 else 'LR' if i==14 else 'PC' if i==15 else 'r'+str(i)),before=f'0x{u:08X}',after=f'0x{v:08X}') for i,(u,v) in enumerate(zip(start['r'],stop['r'])) if u!=v]
classified=[dict(q,actual_match=True,actual_event=w) for q,w in zip(x['stores'],writes)]
result=dict(task='AQ',classification='FULL PASS',authoritative_AP_commit=pre['AP_commit'],authoritative_AO_commit=pre['AO_commit'],branch='codex/brainage',rom_sha1=x['rom_sha1'],framework_baseline=x['framework_baseline'],evidence_tier=x['evidence_tier'],authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),model_sha256=pre['model_sha256'],complete_AO_prefix_exact=True,prior_decision_observations=112,entry_hashes=x['entry_hashes'],aq_start=start,aq_stop=stop,executed_instruction_count=45,executed_pcs=x['aq']['pc_sequence'],instruction_observations=steps,architectural_stores=classified,value_changing_stores=6,idempotent_stores=12,bounded_calls=x['calls'],returns=x['returns'],bus_reads=reads,data_reads=x['data_reads'],forbidden_next=dict(x['forbidden_next'],interpreter_fetched=False,dispatched=False,target_entered=False),register_deltas=deltas,flags_before=x['instructions'][0]['nzcv_before'],flags_after=x['aq']['nzcv'],memory=dict(mainram_changed_bytes=5,dtcm_changed_bytes=0,byte_changes=changes,dtcm_byte_changes=[],mapped_fields=fields,mainram_before_sha256=sha(b),mainram_after_sha256=sha(e),dtcm_before_sha256=sha(dt),dtcm_after_sha256=sha(de)),save=dict(before_sha256=sha(save),after_sha256=sha(save),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,unexpected_writes=0,video_touch_scene_unchanged=True,gameplay_resumed=False,score_count_phase_history_unchanged=True,extra_effect_beyond_certified_offset_stores=False),accounting=account,focused_tests=load(ROOT/'local/task-aq/focused-tests.json'),disabled_control_pass=True,runner_sha256=s['runner_sha256'],installed_source_sha256=installed,resolved_predecessor_evidence_discrepancy=x['resolved_evidence_discrepancy'],limitations=['Forced Tier-3 frozen exact context; no compiled parity','Written helper offsets have no proven gameplay semantic names','No forbidden callee instruction fetched or executed; outer helper has not returned','ARM7 cycles observed rather than claimed frozen'],next_smallest_task='Read-only static bounding of pending call 02026044 -> 0206753C using this exact ABI; no successor task started')
args.export.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':'FULL PASS','AQ_dispatches':45,'writes':18,'RAM_bytes':5,'DTCM_bytes':0,'accounting':account}))
