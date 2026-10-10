"""Focused no-candidate/capacity tests plus supplemental same-object session reset."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from corpus import load,EXPECTED
p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--code-snapshot',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[2];assert hashlib.sha1(a.rom.read_bytes()).hexdigest()=='b8a105bacc3234dede8d4465df0869f2b922a0e2'
local=r/'local/task-w';local.mkdir(exist_ok=True);build=r/'build/task-w-tests';build.mkdir(exist_ok=True,parents=True);compiler=r/'local/toolchain/w64devkit/bin/g++.exe';core=r/'local/ndsrecomp/external/arm-recomp-core/common'
def run(cmd,**kw):return subprocess.run(list(map(str,cmd)),cwd=r,check=True,**kw)
cmd=[compiler,'-O2','-std=c++17','-Wall','-Wextra','-I',r/'tools/brainage_custom','tools/task_w/contract_test.cpp','-o',build/'contract_test.exe','-static-libgcc','-static-libstdc++'];run(cmd);run([build/'contract_test.exe',local/'fake-no-candidate.ppm'])
sys.path.insert(0,str(r/'tools/task_a'));from probe_boot import write_frame
rgb=(local/'fake-no-candidate.ppm').read_bytes().split(b'\n',3)[3];write_frame(local/'fake-no-candidate.png',{'w':256,'h':192,'rgb':rgb.hex()})
samples=load()['samples'];fixture=local/'reset-input.txt';lines=[]
for label in (0,1,0):
    strokes=samples[label]['strokes'];lines.append(str(len(strokes)))
    for stroke in strokes:lines.append(str(len(stroke)));lines.extend(f'{x} {y}' for x,y in stroke)
fixture.write_text('\n'.join(lines)+'\n')
cmd=[compiler,'-O2','-std=c++17','-Wall','-Wextra','-I',r/'tools/brainage_custom','-I',core,'tools/task_w/reset_test.cpp']+[core/n for n in ('interpreter.cpp','arm_decode.cpp','thumb_decode.cpp','arm_ir.cpp')]+['-o',build/'reset_test.exe','-static-libgcc','-static-libstdc++'];run(cmd);run([build/'reset_test.exe',a.rom.resolve(),a.code_snapshot.resolve(),fixture])
run(['python','tools/task_v/check.py','--rom',a.rom.resolve(),'--code-snapshot',a.code_snapshot.resolve()])
result={'pass':True,'corpus_sha256':EXPECTED,'no_candidate_evidence':'fake contract only; not authoritative recognizer output','no_candidate_non_error_render_safe_exit_and_later_candidate':True,'candidate_replacement':True,'eight_strokes_512_points':True,'same_object_reset_0_1_0':True,'arithmetic_freehand_legacy_v':True}
(local/'focused-tests.json').write_text(json.dumps(result,indent=2)+'\n')
