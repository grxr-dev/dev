"""Promote allowed scalar fence metadata only, never a resumable state or permit."""
import hashlib
import json
import sys
from common import ROOT, ATTEMPT, AUTHORITY, TERMINAL, load, require, rows, sha, write_new


def main():
    analysis=load(ATTEMPT/'analysis.json')
    require(analysis['classification']=='FULL PASS' and analysis['exit_code']==73,'successful one-shot analysis required')
    sys.path.insert(0,str(ROOT/'tools/task_aw11'))
    import state
    baseline=state.load()
    audit=rows(ATTEMPT/'capture.jsonl')
    core=None
    for record in audit:
        if record['event']=='canonical_snapshot':
            core=record
        if record['event']=='pre_device_fence':
            break
    fields,identities=state.decode(bytes.fromhex(core['canonical_hex']))
    expected=[row[:] for row in baseline['fields']]
    changes=[{'name':'unwinding','width':1,'before':0,'after':1},
             {'name':'slot9.cycle','width':8,'before':3416875650,'after':3416875777}]
    for change in changes:
        target=next(row for row in expected if row[0]==change['name'])
        require(target[1:]==[change['width'],change['before']],'base delta mismatch')
        target[2]=change['after']
    require(fields==expected and identities==baseline['identities'],'lossless full core reconstruction')
    require(hashlib.sha256(state.encode(fields,identities)).hexdigest()==core['sha256']=='3528c2be122178850a3d3c78157cdd1adaf5409e5eb32f6d794e1c3f81d27d84','fence core identity')
    gpu=next(record for record in audit if record['event']=='gpu_snapshot')
    gpu_fields,gpu_identities=state.decode(bytes.fromhex(gpu['canonical_hex']))
    require(hashlib.sha256(state.encode(gpu_fields,gpu_identities)).hexdigest()==gpu['sha256']==analysis['GPU_sha256'],'GPU lossless identity')
    value={'schema':'AW14 lossless terminal-fence core reference and live GPU scalar metadata v1',
           'authority':{'AW13':AUTHORITY,'AW12':'b60203a9d30b3a8536395aaacdd15d126ee88399','AW9':'fb3e417aa48cc70cc4c05f796263c9cf87b791af'},
           'audit_sha256':sha(ATTEMPT/'capture.jsonl'),'analysis_sha256':sha(ATTEMPT/'analysis.json'),
           'core':{'base_authority':'b10e83d9f5e236930d7b2fd8e1b2b301e978decc','base_metadata':'tools/task_aw11/terminal.json',
                   'base_canonical_sha256':TERMINAL,'canonical_schema':'AW2S v1','scalar_count':411,'identity_count':5,
                   'changes':changes,'canonical_sha256':core['sha256'],'all_other_fields_and_identities':'exactly unchanged'},
           'GPU':{'schema':'AW2S v1 with gpu.schema=1','fields':gpu_fields,'identities':gpu_identities,'canonical_sha256':gpu['sha256'],
                  'source':'actual runtime-owned GPU getter; two identical passive samples; not the synthetic AW12 fixture'},
           'ownership':{'ticket':1,'frame':analysis['fence_chain_verification']['bound_frame'],'frame_depth_at_fence':0,
                        'saved_unwind_valid_at_fence':False,'outermost_entry_predicate_passed':True,
                        'transcript':[{'event':record['event'],'index':record['index'],'phase':record['phase'],
                                       'saved_valid':record['saved_valid'],'frame_depth':record['frame_depth'],'chain':record['chain']}
                                      for record in analysis['ownership_fence_transcript']]},
           'CPU':{'PC':'0x020019B4','cycle9':3416875777,'cap':3416875778,'ordinal9':281098019,'cycle7':1708437825,'ordinal7':96026779},
           'terminal':{'phase':'pre-device capture-only fence','exit':73,'guest_reentry':False,'new_slice_or_cap':False},
           'not_resumable_emulator_or_host_process_state':True,'additional_execution_authorized':False}
    write_new(ATTEMPT/'fence-metadata.json',value)
    print(json.dumps({'lossless_core_fields':len(fields),'GPU_fields':len(gpu_fields),'metadata_sha256':sha(ATTEMPT/'fence-metadata.json'),'additional_execution_authorized':False},indent=2))


if __name__=='__main__':
    main()
