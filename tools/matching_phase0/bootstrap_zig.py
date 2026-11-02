"""Pinned official open-source diagnostic compiler, installed only under local/.

TLS + official published digest; not an independent reproducible-build/signature
claim. Range sizes/content are verified and the complete archive is hashed before
any executable runs. No PATH/registry/system changes or proprietary downloads.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
VERSION='0.15.2'
URL='https://ziglang.org/download/0.15.2/zig-x86_64-windows-0.15.2.zip'
SHA256='3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c'
SIZE=92614574


def install():
    root=ROOT/'local/matching_phase0/toolchains';root.mkdir(parents=True,exist_ok=True)
    archive=root/'zig-x86_64-windows-0.15.2.zip'
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA256:
        parts=root/'zig-0.15.2-download-parts';parts.mkdir(exist_ok=True)
        step=1024*1024
        def download(i):
            start=i*step;end=min(start+step,SIZE)-1;path=parts/str(i)
            if path.exists() and path.stat().st_size==end-start+1:return path
            request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'})
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(request,timeout=15) as response:
                        if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{SIZE}':raise ValueError('release range mismatch')
                        data=response.read(end-start+2)
                        if len(data)!=end-start+1:raise ValueError('release chunk length mismatch')
                    path.write_bytes(data);return path
                except OSError:
                    if attempt:raise
        count=(SIZE+step-1)//step
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for n,_ in enumerate(pool.map(download,range(count)),1):
                if n%12==0:print(f'Downloaded/checked {n}/{count} chunks',flush=True)
        raw=b''.join((parts/str(i)).read_bytes() for i in range(count))
        if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('official archive checksum mismatch; never execute')
        archive.write_bytes(raw)
    destination=root/'zig-x86_64-windows-0.15.2'
    if not (destination/'zig.exe').exists():
        with zipfile.ZipFile(archive) as files:
            for entry in files.infolist():
                if not (root/entry.filename).resolve().is_relative_to(root.resolve()):raise ValueError('unsafe archive path')
            files.extractall(root)
    evidence={'source':URL,'official_index':'https://ziglang.org/download/index.json','version':VERSION,
              'archive_sha256':SHA256,'archive_bytes':archive.stat().st_size,
              'executable_sha256':hashlib.sha256((destination/'zig.exe').read_bytes()).hexdigest(),
              'license':str(destination/'LICENSE'),'installed_at':time.time()}
    (root/'zig-install.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence));return destination/'zig.exe'


if __name__=='__main__':install()
