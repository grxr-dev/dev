"""Explicit publisher-verified local install; batch.py never downloads tools."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
TAG='v3.8.3'
COMMIT='9aeec9cbab1a056ade7dc1f1625aacc41b0f8511'
ASSET='objdiff-cli-windows-x86_64.exe'
SHA256='dd12dfb5e9e94a7f6c949a37e1815963cf2cffe4c87b4999b7ebc8c15b398a1f'
SIZE=7164416
URL='https://github.com/encounter/objdiff/releases/download/'+TAG+'/'+ASSET


def release_asset(release, tag):
    if release.get('tag_name')!=TAG or release.get('draft') is not False or tag.get('object')!={'sha':COMMIT,'type':'commit','url':'https://api.github.com/repos/encounter/objdiff/git/commits/'+COMMIT}:
        raise ValueError('official release/tag identity changed')
    assets=[asset for asset in release['assets'] if asset['name']==ASSET]
    if len(assets)!=1 or assets[0]['size']!=SIZE or assets[0]['digest']!='sha256:'+SHA256 or assets[0]['browser_download_url']!=URL:
        raise ValueError('publisher asset identity/digest changed')
    return assets[0]


def main():
    directory=ROOT/'local/matching_phase1/tools/objdiff-v3.8.3';directory.mkdir(parents=True,exist_ok=True)
    release=json.loads(subprocess.check_output(['gh','api','repos/encounter/objdiff/releases/tags/'+TAG],timeout=30))
    tag=json.loads(subprocess.check_output(['gh','api','repos/encounter/objdiff/git/ref/tags/'+TAG],timeout=30))
    asset=release_asset(release,tag)
    binary=directory/ASSET
    if not binary.exists():
        subprocess.run(['gh','release','download',TAG,'--repo','encounter/objdiff','--pattern',ASSET,'--dir',str(directory)],check=True,timeout=120)
    if binary.stat().st_size!=SIZE or hashlib.sha256(binary.read_bytes()).hexdigest()!=SHA256:
        raise ValueError('download checksum mismatch; do not execute; preserve for inspection')
    version=subprocess.check_output([str(binary),'--version'],timeout=15).decode().strip()
    if not version.endswith(' 3.8.3'):raise ValueError('version mismatch')
    evidence={'release_url':release['html_url'],'published_at':release['published_at'],'tag_commit':COMMIT,
        'asset':ASSET,'bytes':SIZE,'sha256':SHA256,'publisher_digest':asset['digest'],'version':version,
        'publisher_digest_verified':True,'independent_reproducible_source_build':False}
    (directory/'installation.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
