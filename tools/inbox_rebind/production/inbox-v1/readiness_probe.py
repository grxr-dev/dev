"""Compatibility entry for the supported persistent no-send binding probe."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inbox_binding import load, atomic, status

parser=argparse.ArgumentParser()
parser.add_argument('--request',action='store_true')
args=parser.parse_args()
runtime=Path(__file__).resolve().parents[1]/'.runtime'
binding=load(runtime)
if args.request:
 atomic(runtime/'inbox_binding_probe.json',{'probe_id':uuid.uuid4().hex,'binding_identity':binding['identity']})
print(json.dumps(status(runtime)))
