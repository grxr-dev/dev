"""Supported local-only recipient control; no send, queue claim, ACK or remote rebind."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inbox_binding import load, change, status, atomic, public


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('status')
    sub.add_parser('request-readiness')
    for action in ('rebind','rollback'):
        operation=sub.add_parser(action)
        operation.add_argument('--target',required=True)
        operation.add_argument('--expected-id',required=True)
        operation.add_argument('--expected-identity',required=True)
    args=parser.parse_args()
    runtime=Path(__file__).resolve().parents[1]/'.runtime'
    if args.action in ('rebind','rollback'):
        import msvcrt
        with (runtime/'inbox_binding.lock').open('a+b') as lock:
            lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            value,changed=change(runtime,args.target,args.expected_id,args.expected_identity,args.action=='rollback')
        print(json.dumps({'changed':changed,'binding':public(value),'delivery_authorized':False}))
    elif args.action=='request-readiness':
        value=load(runtime)
        atomic(runtime/'inbox_binding_probe.json',{'probe_id':uuid.uuid4().hex,'binding_identity':value['identity']})
        print(json.dumps({'status':'REQUESTED_NO_SEND','binding':public(value)}))
    else:
        print(json.dumps(status(runtime)))


if __name__=='__main__':
    main()
