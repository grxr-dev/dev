"""Compare audited trials; export compact ROM-free metadata, not raw dumps."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--a',type=Path,required=True);p.add_argument('--b',type=Path,required=True);p.add_argument('--out',type=Path,required=True);x=p.parse_args()
a=json.loads((x.a/'audit.json').read_text());b=json.loads((x.b/'audit.json').read_text());assert a['validated'] and b['validated'] and a['variant']=='A' and b['variant']=='B'
assert a['objects']==b['objects']
identical=True
for region in ['context','slot']:
 for tag in ['initial','call-0-0-before','call-0-0-after','call-0-1-after','call-1-0-after','call-1-1-after']:
  identical &= (x.a/f'{tag}-{region}.bin').read_bytes()==(x.b/f'{tag}-{region}.bin').read_bytes()
source_a=json.loads((x.a/'session.json').read_text());source_b=json.loads((x.b/'session.json').read_text());assert source_a['state_sha256']==source_b['state_sha256']
data=dict(classification='FULL PASS' if b['calls'][-1]['candidate_code']==52 else 'PARTIAL PASS',mechanism='fixed-target interpreter redirect; original worker callsite not executed',checkpoint_sha256=source_a['state_sha256'],target='0x020A41A0',synthetic_return_gate='0x02051AF8',context_and_output_snapshots_identical=identical,baseline=dict(counts=[9,5],candidates=[50,52],returns=[0,0],metrics=[500,249]),trials=[a,b])
x.out.write_text(json.dumps(data,indent=2)+'\n');print(data['classification'])
