"""Reserve one fresh AW14 attempt; verify inherited certificates and frozen inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from common import ROOT, ATTEMPT, AUTHORITY, ENTRY, TERMINAL, digest, load, module, preserved, require, sha, write_new


def main():
    ATTEMPT.parent.mkdir(exist_ok=True)
    with (ATTEMPT.parent / 'one-shot.lock').open('x') as lock:
        lock.write(str(ATTEMPT) + '\n')
    ATTEMPT.mkdir()
    result={'task':'AW14','artifact_preflight_passed':False,'runner_launches':0,'retry_authorized':False}
    try:
        require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==AUTHORITY,'checkout differs from AW13')
        require(subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='codex/brainage','branch mismatch')
        prefix=load(ROOT/'tools/task_aw8/certificate.json')
        require(digest(prefix['certificate'])==prefix['sha256']=='8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417','prefix certificate mismatch')
        require(prefix['certificate']['dynamic_execution_ready'] and prefix['certificate']['instruction_count']==11,'wrong prefix')
        fence=load(ROOT/'tools/task_aw12/certificate.json')
        verifier=module('aw14_aw12_verifier',ROOT/'tools/task_aw12/certify.py')
        repeated=verifier.certificate(ROOT/fence['evidence']['path'])
        require(repeated==fence and fence['static_zero_guest_handoff_certified'] and not fence['dynamic_execution_ready'],'AW12 certificate mismatch')
        write_new(ATTEMPT/'aw12-repeated.json',repeated)
        old_output=ROOT/'local/task-aw8/aw14-preflight-once.json'
        require(not old_output.exists(),'AW14 prefix preflight already used')
        command=[sys.executable,str(ROOT/'tools/task_aw8/certify.py'),'--evidence',str(ROOT/prefix['certificate']['local_evidence']),'--out',str(old_output)]
        child=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120)
        write_new(ATTEMPT/'aw8-preflight-command.json',{'command':command,'exit':child.returncode,'stdout':child.stdout,'stderr':child.stderr})
        require(child.returncode==0 and load(old_output)==prefix,'unchanged AW8 preflight failed')
        freeze=load(ROOT/'tools/task_y/freeze.json')
        source=ROOT/'local/task-g/session-001/11-answer-01-63'
        require(sha(source/'checkpoint.state')==freeze['checkpoint_sha256'],'source checkpoint mismatch')
        require(sha(source/'after.sav')==prefix['certificate']['unchanged_identities']['save'],'source save mismatch')
        require(digest(load(ROOT/'tools/task_y/input.json'))==freeze['sha256'],'frozen input mismatch')
        historical=load(ROOT/'local/task-aw9/attempt-001/session.json')
        command=historical['command']
        require(hashlib.sha1(Path(command[command.index('--rom')+1]).read_bytes()).hexdigest()==prefix['certificate']['unchanged_identities']['rom'],'ROM mismatch')
        prior=load(ROOT/'local/task-aw12/certification-014/summary.json')['original_source_hashes']
        protected=dict(prior)
        protected.update(load(ROOT/'local/task-aw8/certification-008/tests.json')['preserved_artifacts'])
        for path in [ROOT/'local/task-aw9/attempt-001/runtime.permit',ROOT/'local/task-aw9/attempt-001/session.json',
                     ROOT/'build/task-aw9-once/nds_runner.exe',source/'checkpoint.state',source/'after.sav']:
            protected[str(path.relative_to(ROOT))]=sha(path)
        preserved(protected)
        contract={'task':'AW14','authority':AUTHORITY,'prefix_certificate_sha256':prefix['sha256'],
                  'fence_certificate_sha256':digest(fence),'entry_sha256':ENTRY,'terminal_sha256':TERMINAL,
                  'prerequisite':'exact historical AU checkpoint/gesture plus 11 instructions/56 cycles/five divider writes',
                  'after_terminal':'AW12 unchanged zero-guest capture to pre-device fence then nonreturning disposal',
                  'B4_fetch_account_dispatch':False,'service_after_terminal':False,'retry_authorized':False}
        write_new(ATTEMPT/'contract.json',contract)
        result.update(artifact_preflight_passed=True,contract_sha256=digest(contract),protected_artifacts=protected,
                      checkpoint_sha256=freeze['checkpoint_sha256'],input_sha256=freeze['sha256'],
                      prefix_certificate_sha256=prefix['sha256'],fence_certificate_sha256=digest(fence),
                      live_preflight_still_required=True)
    except Exception as error:
        result['first_mismatch']=str(error)
    write_new(ATTEMPT/'preflight.json',result)
    print(json.dumps({key:result.get(key) for key in ['artifact_preflight_passed','first_mismatch','contract_sha256']},indent=2))
    if not result['artifact_preflight_passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
