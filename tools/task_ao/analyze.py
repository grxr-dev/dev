"""Compare full reconstructed prefix to committed AK and audit exactly one store."""
import argparse,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--disabled',type=Path,required=True);a.add_argument('--export',type=Path,required=True);args=a.parse_args()
out=args.out.resolve();disabled=args.disabled.resolve()
assert out.is_relative_to(ROOT/'local/task-ao') and disabled.is_relative_to(ROOT/'local/task-ao')
ak=read(ROOT/'docs/BrainAge_TaskAN_Result.json');audit=rows(out/'audit.jsonl');s=read(out/'session.json');ds=read(disabled/'session.json')
assert sha((ROOT/'build/task-o-sdl-runner/nds_runner.exe').read_bytes())==s['runner_sha256']==ds['runner_sha256']
assert s['pass'] and ds['pass'] and s['exit_code']==ds['exit_code']==0 and not s.get('forced_cleanup') and not ds.get('forced_cleanup')
assert not any(x['event']=='failure' for x in audit)
def event(n):
 x=[v for v in audit if v['event']==n];assert len(x)==1;return x[0]
steps=[x for x in audit if x['event']=='decision_step'];old=[x for x in rows(ROOT/ak['authoritative_path']/'audit.jsonl') if x['event']=='decision_step']
assert len(steps)==112 and steps[:111]==old and steps[110]==ak['an_stop']
start=event('ao_before');stop=steps[-1];assert start==dict(steps[110],event='ao_before')
assert stop['pc']==0x02067c48 and stop['insn9']==281097945 and stop['r'][:15]==start['r'][:15]
assert all(stop[k]==start[k] for k in ['n','z','c','v','t','mode','i','f'])
w=event('ao_write_event');assert w==dict(event='ao_write_event',path='Interpreter::step -> RtBus::write32 -> bus_write_u32',pc=0x02067c44,opcode=0xe5840250,address=0x020ea1c0,width=4,source_register=0,value=0x02132750,before=0x02133a18,after=0x02132750)
assert audit.index(steps[110])<audit.index(w)<audit.index(stop)
assert len([v for v in audit if v['event']=='ao_read_event'])==1
assert [v for v in audit if v['event']=='an_read_event']==ak['memory']['read_events']
assert [v for v in audit if v['event']=='ak_write_event']==read(ROOT/'docs/BrainAge_TaskAK_Result.json')['memory']['write_events']
b=(out/'ao-before-mainram.bin').read_bytes();e=(out/'decision-after-mainram.bin').read_bytes();dt=(out/'ao-before-dtcm.bin').read_bytes();de=(out/'decision-after-dtcm.bin').read_bytes()
assert len(b)==len(e)==0x400000 and len(dt)==len(de)==0x4000
assert sha(b)==ak['memory']['mainram_after_sha256'] and sha(dt)==ak['memory']['dtcm_after_sha256'] and dt==de
changes=[dict(address=f'0x{0x02000000+i:08X}',before=x,after=y) for i,(x,y) in enumerate(zip(b,e)) if x!=y]
assert changes==[dict(address='0x020EA1C0',before=0x18,after=0x50),dict(address='0x020EA1C1',before=0x3a,after=0x27)]
assert struct.unpack_from('<I',b,0xea1c0)[0]==0x02133a18 and struct.unpack_from('<I',e,0xea1c0)[0]==0x02132750
fields=[]
for f in ak['memory']['mapped_fields']:
 off=int(f['address'],16)-0x02000000;n=f['width'];before=int.from_bytes(b[off:off+n],'little');after=int.from_bytes(e[off:off+n],'little')
 assert before==f['after'] and after==(0x02132750 if off==0xea1c0 else before)
 fields.append(dict(offset=f['offset'],address=f['address'],width=n,before=before,after=after))
save=(out/'ao-before.sav').read_bytes();assert sha(save)==ak['save']['after_sha256']
for path in (out,disabled):
 for name in ('initial.sav','session.sav','final.sav'):assert (path/name).read_bytes()==save
 assert not (path/'requests.jsonl').stat().st_size and not (path/'flash.jsonl').stat().st_size
assert (out/'decision-after.sav').read_bytes()==save
assert [x['event'] for x in rows(disabled/'audit.jsonl')]==['entry','disabled_control','disposable_exit']
assert (disabled/'disabled-entry-mainram.bin').read_bytes()==(disabled/'disabled-stop-mainram.bin').read_bytes() and not ds['input_events']
x=event('ao_before_sample');y=event('decision_stop_sample')
for k in ['insn7','guest_deliveries','owner','down','video_sha1','flash_sha1','current','requested','selected','presents']:assert x[k]==y[k]
assert x['insn9']==281097944 and x['cycle9']==3416875550 and x['insn7']==96026779 and x['cycle7']==1708437767
account={k:{'before':x[k],'after':y[k],'delta':y[k]-x[k]} for k in ['insn9','cycle9','insn7','cycle7']};assert account['insn9']['delta']==1
assert event('decision_stopped')==dict(event='decision_stopped',ao_instructions=1,ao_writes=1,successor_dispatched=False)
assert not event('disposable_exit')['save_dirty']
assert len(s['input_events'])==10
installed={}
for src,dst in [('diagnostic.h','brainage_task_ao.h'),('guard.h','task_ao_guard.h'),('task_ao_decision.inc','task_ao_decision.inc')]:
 text=(ROOT/'tools/task_ao'/src).read_text();assert text==(ROOT/'local/ndsrecomp/runner/src'/dst).read_text();installed[src]=sha(text.encode())
result=dict(task='AO - single second value-changing object store',classification='FULL PASS',authoritative_an_commit='0f3d697861a8d52f569ec051915258e02915d878',authoritative_am_commit='cb2126cfa0c2e75714b993cdc0124c49c8e1b680',authoritative_al_commit='7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70',branch='codex/brainage',rom_sha1=ak['rom_sha1'],framework_baseline=ak['framework_baseline'],evidence_tier=ak['evidence_tier'],authoritative_path=out.relative_to(ROOT).as_posix(),disabled_path=disabled.relative_to(ROOT).as_posix(),complete_AN_prefix_exact=True,an_cpu_images_save_ordinals_revalidated=True,ao_start=start,ao_stop=stop,executed_pcs=['0x02067C44'],terminal_pc='0x02067C48',terminal_dispatched=False,store_event=w,register_deltas=[dict(register='PC',before='0x02067C44',after='0x02067C48')],flags_before=[0,0,1,0],flags_after=[0,0,1,0],memory=dict(mainram_changed_bytes=2,dtcm_changed_bytes=0,write_events=1,byte_changes=changes,mapped_fields=fields,mainram_before_sha256=sha(b),mainram_after_sha256=sha(e),dtcm_before_sha256=sha(dt),dtcm_after_sha256=sha(de)),save=dict(before_sha256=sha(save),after_sha256=sha(save),changed_bytes=0,logical_requests=0,flash_commits=0,dirty=False),state_effects=dict(MMIO_accesses=0,unexpected_writes=0,video_touch_scene_unchanged=True,gameplay_resumed=False,additional_effect_beyond_isolated_store=False),accounting=account,focused_tests=read(ROOT/'local/task-ao/focused-tests.json'),disabled_control_pass=True,runner_sha256=s['runner_sha256'],installed_source_sha256=installed,limitations=['Forced Tier-3 frozen context; no compiled parity','Semantic role of exercise +0x7C0 unproven','No successor dispatch or helper return'],next_smallest_task='Read-only audit of successor at 0x02067C48 and its smallest safe boundary; AP not started')
args.export.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':'FULL PASS','accounting':account,'RAM_diff':2,'DTCM_diff':0,'write_events':1}))
