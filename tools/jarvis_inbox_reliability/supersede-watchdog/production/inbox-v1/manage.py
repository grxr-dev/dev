"""Local administrative enable/rollback; never invoked by browser/native messages."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import sys
import winreg
ROOT=Path(__file__).resolve().parents[1]
KEY=r'Software\Mozilla\NativeMessagingHosts\jarvis_inbox_host'

def checked(root,path):
    root=Path(root).resolve();path=Path(path).resolve()
    if not path.is_relative_to(root) or path==root:raise ValueError('path must stay inside the bridge workspace')
    return path

def atomic_config(root,enabled):
    cfg=checked(root,Path(root)/'.runtime/inbox-v1.json');cfg.parent.mkdir(parents=True,exist_ok=True)
    tmp=cfg.with_suffix('.tmp');tmp.write_text(json.dumps({'enabled':enabled,'local_port':18741}),encoding='utf-8');tmp.replace(cfg)

def current_registration():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,KEY) as key:return winreg.QueryValueEx(key,'')[0]
    except FileNotFoundError:return None

def unregister(root):
    expected=str(checked(root,Path(root)/'inbox-v1/native-host/jarvis_inbox_host.json'))
    current=current_registration()
    if current and Path(current).resolve()!=Path(expected).resolve():raise ValueError('refusing to remove unrelated native registration')
    if current:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,KEY)

def rollback_files(root,backup):
    root=Path(root).resolve();backup=checked(root,backup);backup.mkdir(parents=True,exist_ok=False)
    atomic_config(root,False)
    for name in ('inbox_queue.json','inbox_native_recovery.json'):
        src=checked(root,root/'.runtime'/name)
        if src.exists():shutil.copy2(src,backup/name) # preserve originals and export, never drop uncertainty
    host=checked(root,root/'inbox-v1/native-host')
    if host.exists():
        target=checked(root,backup/'native-host')
        if target.exists():raise ValueError('rollback destination already exists')
        shutil.move(str(host),str(target)) # resolved paths checked before recursive move
    return backup

def rollback(root=ROOT):
    unregister(root)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=rollback_files(root,Path(root)/'.runtime'/('inbox-rollback-'+stamp))
    print('Inbox disabled; native registration/files removed; queue preserved/exported:',backup)
    print('Remove the temporary Firefox add-on, then Restart Bridge when idle. No active task is stopped.')
    return backup

def enable():
    sys.path.insert(0,str(ROOT));from inbox_queue import InboxQueue
    # Administrative validation is read-only: never recover/mutate a live queue
    # from a second process. Only managed startup owns crash recovery.
    queue=ROOT/'.runtime/inbox_queue.json'
    if queue.exists():
        from inbox_wire import unique_json
        data=unique_json(queue.read_text(encoding='utf-8-sig'))
        if not isinstance(data,dict) or not ({'version','entries'}<=set(data)<={'version','entries','recovery_once','superseded_watchdog'}) or data['version']!=2 or not isinstance(data['entries'],dict):raise ValueError('malformed queue')
        validator=InboxQueue.__new__(InboxQueue);validator._recovery=data.get('recovery_once');validator._supersession=data.get('superseded_watchdog')
        if validator._supersession is not None:validator._validate_supersession(validator._supersession,data['entries'])
        if validator._recovery is not None:validator._validate_recovery(validator._recovery,data['entries'])
        for did,entry in data['entries'].items():validator._validate_entry(did,entry)
    if not (ROOT/'inbox-v1/native-host/jarvis_inbox_host.exe').is_file():raise ValueError('native executable missing')
    atomic_config(ROOT,True)
    print('Inbox enabled for NEXT managed start; Restart Bridge only when idle.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['enable','rollback']);args=parser.parse_args()
    enable() if args.action=='enable' else rollback()
