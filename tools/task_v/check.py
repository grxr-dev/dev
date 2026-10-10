"""Build/run the focused V + unchanged P/Q tests. Raw ROM/state inputs remain local."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--code-snapshot',type=Path,required=True);args=p.parse_args()
assert hashlib.sha1(args.rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
r=Path(__file__).resolve().parents[2];out=r/'build/task-v-tests';out.mkdir(exist_ok=True,parents=True);compiler=r/'local/toolchain/w64devkit/bin/g++.exe';core=r/'local/ndsrecomp/external/arm-recomp-core/common'
def run(cmd,**kw):return subprocess.run(list(map(str,cmd)),cwd=r,check=True,**kw)
for name,src in [('contract_test','tools/task_v/contract_test.cpp'),('arithmetic_test','tools/task_p/contract_test.cpp'),('freehand_test','tools/task_q/freehand_test.cpp'),('service_test','tools/task_v/service_test.cpp')]:
    cmd=[compiler,'-O2','-std=c++17','-Wall','-Wextra','-I',r/'tools/brainage_custom','-I',r/'tools/task_l','-I',core,src]
    if name=='service_test':cmd += [core/n for n in ('interpreter.cpp','arm_decode.cpp','thumb_decode.cpp','arm_ir.cpp')]
    cmd+=['-o',out/(name+'.exe'),'-static-libgcc','-static-libstdc++'];run(cmd)
    run([out/(name+'.exe')]+([args.rom.resolve(),args.code_snapshot.resolve()] if name=='service_test' else []))
run(['python','tools/task_p/check_contract.py','--binary',out/'arithmetic_test.exe','--out','local/task-p/task-v-contract.json'])
run(['python','tools/task_q/check_selection.py','--binary',out/'freehand_test.exe','--out','local/task-q/task-v-selection.json'])
env={k:v for k,v in os.environ.items() if not k.startswith(('NDS_TASK_','NDS_BRAINAGE_'))};env['NDS_BRAINAGE_CUSTOM_EXERCISE_ID']='digit-recognition-probe'
result=run([out/'freehand_test.exe','--selection'],env=env,capture_output=True,text=True);assert result.stdout.strip()=='digit-recognition-probe'
(r/'local/task-v').mkdir(exist_ok=True);(r/'local/task-v/focused-tests.json').write_text(json.dumps({'pass':True,'adapter_parity':True,'production_service_two_sessions':True,'resource_hash_negative':True,'arithmetic':True,'freehand':True,'selectors':True,'probe_error_exit':True},indent=2)+'\n')
print('PASS: focused Task V service/contract and P/Q regression checks')
