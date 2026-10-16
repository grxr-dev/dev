"""Stage reviewed watchdog supersession source only; never restarts, rearms, reads or edits a queue."""
import argparse,datetime,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--bridge',type=Path,default=HERE.parents[3]/'bridge');a=p.parse_args();root=a.bridge.resolve()
assert root.is_dir() and (root/'inbox_queue.py').is_file(),'existing bridge required'
manifest=json.loads((HERE/'manifest.json').read_text());changes=[]
for name,m in manifest.items():
 source=HERE/'production'/name;target=(root/name).resolve();assert target.is_relative_to(root)
 text=source.read_text(encoding='utf-8-sig');assert hashlib.sha256(text.encode()).hexdigest()==m['new_sha256']
 if target.exists():
  digest=hashlib.sha256(target.read_text(encoding='utf-8-sig').encode()).hexdigest()
  assert digest in [m['new_sha256'],m['baseline_sha256']],name+': unknown production baseline'
  if digest==m['new_sha256']:continue
 else:assert m['baseline_sha256'] is None,name+': expected existing baseline'
 changes.append((source,target))
if changes:
 backup=root/'backups'/('supersede-watchdog-deploy-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S%f'));backup.mkdir(parents=True,exist_ok=False)
 for source,target in changes:
  if target.exists():
   saved=backup/target.relative_to(root);saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
  target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source.read_text(encoding='utf-8-sig'),encoding='utf-8')
 print('Staged source backup:',backup)
print('Files staged. One tray Restart Bridge is required to load new queue/listener. No cancellation, recovery or delivery performed.')
