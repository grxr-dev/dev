"""Best-effort sanitized trace retention; never participates in delivery decisions."""
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

VERSION = 'inbox-v1-incidents-20261011-01'
MAX_INCIDENTS = 32
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_INCIDENT_BYTES = 16 * 1024 * 1024
MAX_ACTIVE = 8
MAX_AGE = 7 * 86400
MIN_AGE = 86400

def key(delivery_id):
    return hashlib.sha256(delivery_id.encode('utf-8')).hexdigest()

def atomic(path, data):
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with tmp.open('xb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()

def cleanup(root, now, reserve=0, new=False):
    files = sorted(root.glob('*.jsonl'), key=lambda p: p.stat().st_mtime)
    for p in list(files):
        if now - p.stat().st_mtime >= MAX_AGE:
            p.unlink(); files.remove(p)
    while len(files) + int(new) > MAX_INCIDENTS or sum(p.stat().st_size for p in files) + reserve > MAX_TOTAL_BYTES:
        eligible = [p for p in files if now - p.stat().st_mtime >= MIN_AGE]
        if not eligible: return False  # Never evict an incident younger than 24h.
        p = eligible[0]; p.unlink(); files.remove(p)
    return True

def retain(trace_path, clean, now=None):
    # Input is ONLY the native sink's allowlisted, bounded record, not browser payload.
    try:
        now = time.time() if now is None else now
        did = clean.get('delivery_id')
        if not isinstance(did, str) or not did: return
        root = Path(trace_path).parent / 'inbox_verifier_incidents'
        active = root / 'active'; active.mkdir(parents=True, exist_ok=True)
        for p in active.iterdir():
            if p.is_file() and now - p.stat().st_mtime >= MIN_AGE: p.unlink()
        for p in root.glob('*.tmp'):
            if now - p.stat().st_mtime >= MIN_AGE: p.unlink()
        cleanup(root, now)
        name = key(did)
        final = root / (name + '.jsonl')
        stage = active / (name + '.jsonl')
        data = (json.dumps(clean, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
        review = clean.get('state') == 'NEEDS_REVIEW'
        if final.exists():
            old = final.read_bytes()
            if len(old) + len(data) <= MAX_INCIDENT_BYTES and cleanup(root, now, len(data)):
                atomic(final, old + data)
            return
        if not stage.exists() and len(list(active.glob('*.jsonl'))) >= MAX_ACTIVE: return
        if stage.exists():
            previous = stage.read_bytes()
            if previous and not previous.endswith(b'\n'):
                atomic(stage, previous[:previous.rfind(b'\n') + 1])
        size = stage.stat().st_size if stage.exists() else 0
        # Reserve room for a bounded explicit overflow marker and terminal/ACK metadata.
        if size + len(data) <= MAX_INCIDENT_BYTES - 65536 or clean.get('event') in ('native_outcome', 'terminal', 'ack_committed', 'ack_pending'):
            if size + len(data) <= MAX_INCIDENT_BYTES:
                with stage.open('ab') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        else:
            marker = active / (name + '.overflow')
            if not marker.exists():
                marker.touch()
                with stage.open('ab') as f:
                    f.write((json.dumps({'event':'incident_truncated','delivery_id':did,'limit_bytes':MAX_INCIDENT_BYTES})+'\n').encode())
        if review and stage.exists():
            if cleanup(root, now, stage.stat().st_size, True):
                os.replace(stage, final)
                marker = active / (name + '.overflow')
                if marker.exists(): marker.unlink()
        elif clean.get('event') == 'ack_committed' and clean.get('state') != 'NEEDS_REVIEW':
            if stage.exists(): stage.unlink()
            marker = active / (name + '.overflow')
            if marker.exists(): marker.unlink()
    except Exception:
        pass
