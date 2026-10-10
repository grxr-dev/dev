"""Focused ROM-free policy/contracts and existing private-service regressions; no gameplay."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--code-snapshot',type=Path,required=True);args=parser.parse_args()
root=Path(__file__).resolve().parents[2];build=root/'build/task-y-tests';local=root/'local/task-y';build.mkdir(exist_ok=True,parents=True);local.mkdir(exist_ok=True,parents=True)
assert hashlib.sha1(args.rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
core=root/'local/ndsrecomp/external/arm-recomp-core/common';compiler=root/'local/toolchain/w64devkit/bin/g++.exe'
results={}
for name,source,service in [('policy','tools/task_y/policy_test.cpp',False),('legacy_v_contract','tools/task_v/contract_test.cpp',False),('generic_w_contract','tools/task_w/contract_test.cpp',False),('arithmetic','tools/task_p/contract_test.cpp',False),('freehand','tools/task_q/freehand_test.cpp',False),('legacy_v_service','tools/task_v/service_test.cpp',True),('groups_secondary','tools/task_x/service_test.cpp',True)]:
    command=[compiler,'-O2','-std=c++17','-Wall','-Wextra','-I',root/'tools/brainage_custom','-I',root/'tools/task_l','-I',core,root/source]
    if service:command+=[core/filename for filename in ('interpreter.cpp','arm_decode.cpp','thumb_decode.cpp','arm_ir.cpp')]
    binary=build/(name+'.exe');command+=['-o',binary,'-static-libgcc','-static-libstdc++'];subprocess.run(list(map(str,command)),cwd=root,check=True)
    arguments=[args.rom.resolve(),args.code_snapshot.resolve()] if service else [local/'no-candidate.ppm'] if name=='generic_w_contract' else []
    reply=subprocess.run(list(map(str,[binary,*arguments])),cwd=root,check=True,capture_output=True,text=True)
    results[name]={'pass':True,'output':reply.stdout.strip()}
for identity in ('arithmetic-2plus2','freehand-canvas','digit-recognition-probe','digit-entry-probe'):
    env={key:value for key,value in os.environ.items() if not key.startswith(('NDS_TASK_','NDS_BRAINAGE_'))};env['NDS_BRAINAGE_CUSTOM_EXERCISE_ID']=identity
    reply=subprocess.run([str(build/'freehand.exe'),'--selection'],cwd=root,env=env,capture_output=True,text=True,check=True);assert reply.stdout.strip()==identity
results['selectors']={'pass':True,'ids':['arithmetic-2plus2','freehand-canvas','digit-recognition-probe','digit-entry-probe']}
for filename in ('bc_host.h','bc_private_digit_recognizer.h','bc_digit_entry.h','bc_catalog.h','bc_quiz.h','bc_freehand.h'):
    previous=subprocess.check_output(['git','show','b08cb211687368e4ca9f089f7dfb3f71a5c8b1d6:tools/brainage_custom/'+filename],cwd=root)
    assert previous.decode().splitlines()==(root/'tools/brainage_custom'/filename).read_text().splitlines(),filename
results['unchanged_host_service_exercises']={'pass':True}
(local/'focused-tests.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: Task Y policy, V/W/X service/contracts and arithmetic/freehand selectors; no historical evidence overwritten')
