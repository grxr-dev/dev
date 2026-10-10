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
out=args.out.resolve();disabled=args.disabled.resolve();assert out.is_relative_to(ROOT/'local/task-y') and disabled.is_relative_to(ROOT/'local/task-y')
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
tests=read(ROOT/'local/task-y/focused-tests.json');assert all(value['pass'] for value in tests.values())
result={'classification':'FULL PASS (bounded original publication only; forced Tier-3)','rom_sha1':'b8a105bacc3234dede8d4465df0869f2b922a0e2','framework_baseline':'3a57236bb23d25dcb4caad7d58d733311062ff5e','predecessor':'b08cb211687368e4ca9f089f7dfb3f71a5c8b1d6','problem':definition['problem'],'expected':4,'prior_correct_count':1,'phase_before_and_after':1,'input_sha256':freeze['sha256'],'freeze':freeze,'authoritative_path':str(out.relative_to(ROOT)),'disabled_path':str(disabled.relative_to(ROOT)),'input_source':'SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> native owner','custom_events':10,'custom_guest_deliveries':0,'recognition':recognitions,'publication':published,'staged_transient_writes':stages,'private_isolation':cleanup,'hold_samples':held,'terminal_sample':event('terminal_publication'),'objects':objects,'mainram':{'before_sha256':digest(before),'after_private_service_sha256':digest(clean),'at_block_sha256':digest(final),'changed_bytes_at_block':sum(first!=last for first,last in zip(before,final)),'changed_ranges_at_block':ranges(before,final,0x02000000)},'save':{'before_sha256':digest(save),'after_sha256':digest((out/'final.sav').read_bytes()),'changed_bytes':0,'logical_requests':0,'flash_commits':0,'dirty':event('disposable_exit')['save_dirty']},'focused_tests':tests,'exit_code':session['exit_code'],'source_unchanged':True,'no_counter_restoration':True,'no_rom_or_generated_code_edit':True,'limits':['Controlled problem uses forced Tier-3, not compiled answer-publication parity.','No correctness, progression, scoring, history or gameplay resume.','No emulation of elapsed answer-delay frames while host gesture is held. Countdown=1 is discharged by the original publication update.','Three-stroke two-digit 4/5 contributor-dependent timing is deliberately unsupported.','No physical pen/SendInput or unseen-handwriting accuracy claim.'],'recommended_next_task':'Separately authorize one guarded correctness-consumer invocation for this same published 4, stopping before count/phase/progression mutation; map its first store before allowing it.'}
args.export.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'classification':result['classification'],'published_integer':4,'mainram_changed_bytes':result['mainram']['changed_bytes_at_block'],'save_changed_bytes':0,'exit_code':session['exit_code']}))
