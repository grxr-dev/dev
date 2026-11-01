"""Local owner control. Never POSTs a result, releases HOLD, or retries a Send."""
import argparse
import json
from pathlib import Path
import sys
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inbox_one import BUILD,TARGET,TEXT_SHA256


def request(runtime, path, payload=None):
    token=(runtime/'inbox_recovery_admin.token').read_text(encoding='ascii').strip()
    data=None if payload is None else json.dumps(payload).encode()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    query=urllib.request.Request('http://127.0.0.1:18741'+path,data=data,
        headers={'X-Jarvis-Local':'1','X-Jarvis-Admin':token,'Content-Type':'application/json'})
    with opener.open(query,timeout=5) as response:
        raw=response.read(262145)
    if len(raw)>262144:raise ValueError('bounded response required')
    return json.loads(raw)


def main():
    parser=argparse.ArgumentParser()
    actions=parser.add_subparsers(dest='action',required=True)
    actions.add_parser('status')
    arm=actions.add_parser('arm')
    arm.add_argument('--delivery-id',required=True)
    arm.add_argument('--text-sha256',required=True)
    arm.add_argument('--binding-identity',required=True)
    arm.add_argument('--queue-fingerprint',required=True)
    arm.add_argument('--expires-in',type=int,required=True)
    revoke=actions.add_parser('revoke')
    revoke.add_argument('--authorization-id',required=True)
    args=parser.parse_args()
    runtime=Path(__file__).resolve().parents[1]/'.runtime'
    capability=request(runtime,'/local/inbox/capabilities')
    if capability.get('exact_one_build')!=BUILD or '/local/inbox/admin/exact-one' not in capability.get('admin_routes',[]):
        raise ValueError('intended exact-one bridge source is not loaded; no grant issued')
    route='/local/inbox/admin/exact-one'
    if args.action=='status':result=request(runtime,route)
    elif args.action=='revoke':result=request(runtime,route,{'revoke_authorization_id':args.authorization_id})
    else:
        if args.delivery_id!=TARGET or args.text_sha256!=TEXT_SHA256:
            raise ValueError('only the authorized pre-existing issue-95 item is supported')
        result=request(runtime,route,{'delivery_id':args.delivery_id,'text_sha256':args.text_sha256,
            'binding_identity':args.binding_identity,'queue_fingerprint':args.queue_fingerprint,'expires_in':args.expires_in})
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':main()
