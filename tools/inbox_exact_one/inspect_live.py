"""Read-only inspection. Does not instantiate the mutating queue or call next/ACK."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
BRIDGE=ROOT/'bridge'
sys.path.insert(0,str(BRIDGE))
from inbox_binding import load,public,status

TARGET='middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878'
TEXT_HASH='1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651'
BASELINE={'inbox_queue.json':'b8a13a70244767f58c9c220eefa52109a561594bb2af3fe754d661d037cc12f2',
          'inbox_binding.json':'bd87b29ef840b49f1ba4a5e063dfa3a7f91702d496f9a3160121d7b0a4de170c',
          'inbox_native_recovery.json':'74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b',
          'inbox_readiness_request.json':'7e4449fe2a92b87ccfa921cedd11c6efed62beb942a5a7f5b4a0fa30cf0c960e'}


def get(url):
    request=urllib.request.Request(url,headers={'X-Jarvis-Local':'1'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request,timeout=4) as response:
        raw=response.read(262145)
    if len(raw)>262144:raise ValueError('bounded response required')
    return json.loads(raw)


def inspect():
    runtime=BRIDGE/'.runtime'
    binding=load(runtime)
    queue=json.loads((runtime/'inbox_queue.json').read_text(encoding='utf-8-sig'))
    entry=queue['entries'][TARGET]
    result=entry['text'].removeprefix('[CODEX → CHATGPT]\n\n')
    result_sha=hashlib.sha256(result.encode()).hexdigest()
    exact=(entry['delivery_id']==TARGET and entry['text_sha256']==TEXT_HASH and
           hashlib.sha256(entry['text'].encode()).hexdigest()==TEXT_HASH and
           result_sha==TARGET.rsplit(':',1)[1] and entry['state']=='QUEUED' and entry['attempt_count']==0 and
           all(entry[key] is None for key in ('claim_token','last_attempt_at','delivered_at','outcome','next_attempt_at','last_error')))
    protected={name:hashlib.sha256((runtime/name).read_bytes()).hexdigest() for name in BASELINE}
    original_manifest=json.loads((ROOT/'dev/tools/inbox_rebind/source-manifest.json').read_text())['production_files_sha256']
    original_sources=all(hashlib.sha256((BRIDGE/name).read_bytes()).hexdigest()==expected for name,expected in original_manifest.items())
    capabilities=get('http://127.0.0.1:18741/local/inbox/capabilities')
    health=get('http://127.0.0.1:8766/health')
    return {'schema':'inbox-exact-one-inspection/1','binding':public(binding),'entry':{
        'delivery_id':TARGET,'text_sha256':entry['text_sha256'],'result_sha256':result_sha,
        'state':entry['state'],'attempt_count':entry['attempt_count'],'delivered_at':entry['delivered_at'],
        'exact_unattempted_result_verified':exact},'queue_entries':len(queue['entries']),
        'queue_counts':{state:sum(item['state']==state for item in queue['entries'].values()) for state in sorted({item['state'] for item in queue['entries'].values()})},
        'grant_exists':queue.get('exact_one') is not None,'protected_hashes':protected,
        'protected_unchanged':protected==BASELINE,'deployed_rebind_sources_unchanged':original_sources,
        'fresh_no_send_readiness':status(runtime)['no_send_ready'],'bridge_pid':health.get('bridge_pid'),
        'turn_active':health.get('turn_active'),'live_capabilities':capabilities,
        'new_exact_one_source_loaded':capabilities.get('exact_one_build')=='inbox-exact-one-20261101-01',
        'delivery_attempted_by_this_task':False,'brain_age_paused':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=inspect();rendered=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(rendered,encoding='utf-8')
    print(rendered)
