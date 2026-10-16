"""Explicit local administrator CLI. Default is read-only status; no automatic retry."""
import argparse,json,os,secrets,sys,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from inbox_recovery import TARGET
p=argparse.ArgumentParser();p.add_argument('--refresh-readiness',action='store_true');p.add_argument('--recover-once',action='store_true');p.add_argument('--expected-fingerprint');a=p.parse_args()
r=ROOT/'.runtime'
if a.refresh_readiness:
 if a.recover_once or a.expected_fingerprint:p.error('refresh and authorization are separate operations')
 from sys import path
 path.insert(0,str(ROOT/'inbox-v1/native-host'))
 from readiness_diagnostic import atomic
 atomic(r/'inbox_readiness_request.json',{'probe_id':secrets.token_hex(16)})
 print('Fresh no-send readiness requested. Run readiness_probe.py until its exact new probe reports, then query recovery status. No recovery authorized.');raise SystemExit(0)
if a.recover_once and not a.expected_fingerprint:p.error('--recover-once requires reviewed --expected-fingerprint')
if a.expected_fingerprint and not a.recover_once:p.error('fingerprint is only used for explicit recovery')
key=r/'inbox_recovery_admin.token'
if not key.exists():raise SystemExit('Recovery code is not loaded: Restart Bridge is required once to load the new queue/listener. No recovery attempted.')
headers={'X-Jarvis-Local':'1','X-Jarvis-Admin':key.read_text().strip(),'Content-Type':'application/json'}
body=json.dumps({'delivery_id':TARGET,'expected_fingerprint':a.expected_fingerprint}).encode() if a.recover_once else None
req=urllib.request.Request('http://127.0.0.1:18741/local/inbox/admin/recovery-once',data=body,headers=headers)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 with opener.open(req,timeout=10) as response:print(response.read(65537).decode('utf-8'))
except urllib.error.HTTPError as e:
 print(e.read(65537).decode('utf-8'));raise SystemExit(1)
except (OSError,TimeoutError):raise SystemExit('Local admin request failed. Do not retry authorization blindly; inspect status before any action.')
