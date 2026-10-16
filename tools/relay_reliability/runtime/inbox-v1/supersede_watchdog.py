"""Explicit one-item local administrator supersession; never sends or recovers seq94."""
import argparse,json,sys,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from inbox_supersession import WATCHDOG
from reliability import assert_capability, BUILD_ID
p=argparse.ArgumentParser();p.add_argument('--supersede',action='store_true');p.add_argument('--expected-fingerprint');p.add_argument('--expected-proof-sha256');a=p.parse_args()
if a.supersede and not (a.expected_fingerprint and a.expected_proof_sha256):p.error('explicit supersession requires both reviewed hashes')
if not a.supersede and (a.expected_fingerprint or a.expected_proof_sha256):p.error('hashes only apply to explicit supersession')
key=ROOT/'.runtime/inbox_recovery_admin.token'
probe=urllib.request.Request('http://127.0.0.1:18741/local/inbox/capabilities',headers={'X-Jarvis-Local':'1'})
try:
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(probe,timeout=10) as response:
  assert_capability(json.load(response),'/local/inbox/admin/supersede-watchdog',expected_build=BUILD_ID)
except (OSError,ValueError):raise SystemExit('Capability unavailable/stale; idle managed restart required before admin invocation. No cancellation attempted.')
if not key.exists():raise SystemExit('Local administrator route not initialized; managed bridge restart required. No cancellation performed.')
body=json.dumps({'delivery_id':WATCHDOG,'expected_fingerprint':a.expected_fingerprint,'expected_proof_sha256':a.expected_proof_sha256}).encode() if a.supersede else None
req=urllib.request.Request('http://127.0.0.1:18741/local/inbox/admin/supersede-watchdog',data=body,headers={'X-Jarvis-Local':'1','X-Jarvis-Admin':key.read_text().strip(),'Content-Type':'application/json'})
try:
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=60) as r:print(r.read(65537).decode('utf-8'))
except urllib.error.HTTPError as e:
 if e.code==404:raise SystemExit('Supersession operation not loaded; managed bridge restart required. No cancellation performed.')
 print(e.read(65537).decode('utf-8'));raise SystemExit(1)
except (OSError,TimeoutError):raise SystemExit('Local request failed; inspect status, never blindly repeat an authorization.')
