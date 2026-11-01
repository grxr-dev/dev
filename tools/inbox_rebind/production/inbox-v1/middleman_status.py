"""Read-only local status. A saved recipient is never evidence of a loaded browser."""
import json
from pathlib import Path
import sys
import urllib.request
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inbox_binding

EXPECTED_VALIDATOR = 'inbox-recovery-binding-20261101-01'


def summarize(runtime, query_validator):
    state = inbox_binding.status(runtime)
    binding = state['binding']
    receipt = state['readiness']
    # A fresh native receipt carries the exact public binding identity all the
    # way through background and content. Missing/expired receipts prove nothing.
    loaded = bool(receipt and receipt.get('binding_identity') == binding['identity'])
    try:
        live_build = query_validator()
    except Exception:
        live_build = None
    return {
        'binding': binding, 'url': state['url'],
        'manifest': str(Path(__file__).resolve().parent/'extension/manifest.json'),
        'browser_native': 'READY' if state['no_send_ready'] else 'NOT VERIFIED',
        'loaded_binding': 'VERIFIED_NEW' if loaded else 'MISSING_OR_NOT_VERIFIED',
        'readiness_reason': receipt.get('reason') if receipt else 'no_fresh_exact_binding_receipt',
        'validator': 'LIVE' if live_build == EXPECTED_VALIDATOR else 'NEEDS_POST_TURN_ACTIVATION',
        'validator_build': live_build,
        'delivery_authorized': False,
    }


def validator_build(runtime):
    # Existing local-only authenticated GET. Token stays in process memory;
    # never put it in argv, stdout, an exception report or a launcher log.
    token = (runtime/'inbox_recovery_admin.token').read_text(encoding='ascii').strip()
    request = urllib.request.Request('http://127.0.0.1:18741/local/inbox/admin/recovery-once',
        headers={'X-Jarvis-Local': '1', 'X-Jarvis-Admin': token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=3) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError('bounded status required')
    return json.loads(raw).get('build')


if __name__ == '__main__':
    runtime = Path(__file__).resolve().parents[1]/'.runtime'
    try:
        print(json.dumps(summarize(runtime, lambda: validator_build(runtime))))
    except Exception:
        print(json.dumps({'error': 'binding_invalid_or_unavailable', 'delivery_authorized': False}))
        sys.exit(2)
