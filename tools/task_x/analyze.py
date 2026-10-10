"""Audit Task X real SDL observations and apply proven consumer policy offline."""
import argparse,hashlib,importlib.util,json,subprocess
from pathlib import Path
from corpus import load,EXPECTED
from consumer import Consumer
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('w_audit',R/'tools/task_w/analyze.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
w.EXPECTED=EXPECTED
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--export',type=Path,required=True);p.add_argument('--static-out',type=Path,default=R/'local/task-x/static-001');a=p.parse_args();root=a.out.resolve();assert root.is_relative_to(R/'local/task-x')
c=load();assert json.loads((root/'freeze.json').read_text())=={'sha256':EXPECTED,'corpus':c}
sessions=[]
for sample in c['samples']:
 path=root/sample['id'];s=w.audit_session(R,path,sample['strokes']);raw=json.loads((path/'result.json').read_text());consumer=Consumer()
 s['id']=sample['id'];s['description']=sample['description']
 for v,m in zip(s['observations'],raw['stroke_results']):
  groups=[]
  for g in range(2):
   prefix=f'group{g}_';n=m[prefix+'code_count'];assert 0<=n<16
   groups.append({'returned_count':m[prefix+'count'],'codes':[m[prefix+f'code_{i}'] for i in range(n)],'accessor_codes':[m[prefix+f'accessor_{i}'] for i in range(n)]})
  v['groups']=groups;v['consumer']=consumer.consume(groups,sample['label']);v['private_instructions_including_accessors']=v.pop('private_instructions_including_metric')
  assert v['candidate_code']==(groups[1]['codes'][0] if groups[1]['returned_count'] else None)
 s['final_consumer']=s['observations'][-1]['consumer'];s['offline_target_match']=s['final_consumer']['offline_target_match'];sessions.append(s)
legacy=w.audit_session(R,root/'legacy-v-4',c['samples'][9]['strokes'],legacy=True)
assert [v['candidate'] for v in legacy['observations']]==['2','4']
assert [v['candidate'] for v in sessions[9]['observations']]==['2','4']
assert [v['metric'] for v in sessions[9]['observations']]==[500,249]
# Core gates/ownership/input and old exercises stay byte-for-byte unchanged.
for name in ('bc_host.h','bc_rom_resource.h','bc_decuma_adapter.h','bc_digit_probe.h','bc_quiz.h','bc_freehand.h'):
 old=subprocess.check_output(['git','show','5ff5685806003dabd6d7a6d82265316466dc03fc:tools/brainage_custom/'+name],cwd=R).decode().replace('\r\n','\n');assert (R/'tools/brainage_custom'/name).read_text()==old
result={'classification':'FULL PASS','task_w_commit':'5ff5685806003dabd6d7a6d82265316466dc03fc','freeze_commit':'76e3d26','corpus_sha256':EXPECTED,'freeze':json.loads((R/'tools/task_x/freeze.json').read_text()),'sessions':sessions,'legacy_v':legacy,'runtime_sha256':hashlib.sha256((R/'build/task-o-sdl-runner/nds_runner.exe').read_bytes()).hexdigest(),'no_runtime_expected_label':True,'no_original_answer_submission':True,'consumer_policy':'offline mode 0, +31C=2 as configured by Calculations; not a claim of live submission or timing equivalence'}
result['semantics']=json.loads((R/'tools/task_x/semantics.json').read_text())
result['static_ranges']=json.loads((a.static_out/'ranges.json').read_text())
result['focused_tests']=json.loads((R/'local/task-x/focused-tests.json').read_text());assert result['focused_tests']['pass']
result['freeze_commit']=subprocess.check_output(['git','rev-parse','76e3d26'],cwd=R,text=True).strip()
result['final_matches']=sum(s['offline_target_match'] for s in sessions)
for s in sessions:
 matches=[v['stroke'] for v in s['observations'] if v['consumer']['offline_target_match']]
 s['first_matching_release_zero_based']=matches[0] if matches else None
 s['later_releases_counterfactual_after_first_match']=bool(matches and matches[0]<s['stroke_count']-1)
result['release_timing_limit']='Original 7/9 would publish on first expected-matching release; all later probe releases remain valid recognition characterization but are counterfactual after original publication.'
a.export.write_text(json.dumps(result,indent=2)+'\n')
for s in sessions:
 print(s['id'], 'scalar', ' -> '.join(v['candidate'] or '-' for v in s['observations']), 'consumer',' -> '.join(str(v['consumer']['original_consumer_numeric']) for v in s['observations']), 'groups',[(v['groups'][0]['returned_count'],v['groups'][1]['returned_count']) for v in s['observations']])
