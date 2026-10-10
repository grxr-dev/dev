"""Frozen source corpus; labels never enter production exercise or recognizer."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED=(ROOT/'corpus.sha256').read_text().strip()
def load():
    c=json.loads((ROOT/'corpus.json').read_text());actual=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert actual==EXPECTED,'frozen corpus changed'
    assert [s['label'] for s in c['samples']]==list(range(10))
    for sample in c['samples']:
        assert sample['strokes'] and all(s for s in sample['strokes'])
        assert all(24<=x<=232 and 32<=y<=136 for s in sample['strokes'] for x,y in s)
    return c
