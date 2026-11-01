"""Foreground owner command; never scheduled, never called inside a Codex turn."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BRIDGE = ROOT / 'bridge'
RUNTIME = BRIDGE / '.runtime'
AREA = RUNTIME / 'inbox-receipt-132'
sys.path.insert(0, str(HERE.parent / 'inbox_exact_one'))
import seal_migration as m
import finish_once as managed
import receipt

PROTECTED = ('inbox_queue.json', 'inbox_native_recovery.json', 'inbox_readiness_request.json',
             'inbox_binding.json', 'inbox_future.json')


def operator_record():
    p = subprocess.run(['gh', 'api', 'repos/grxr-dev/codex-relay/issues/comments/' + str(receipt.COMMENT)],
                       capture_output=True, text=True, timeout=20)
    if p.returncode:
        raise ValueError('operator authority cannot be re-read; no mutation')
    value = json.loads(p.stdout)
    receipt.authority(value)
    return value


def incident():
    return RUNTIME / 'inbox_verifier_incidents' / (receipt.sha(receipt.TARGET.encode()) + '.jsonl')


def state():
    """Read raw first: never instantiate a queue with unresolved DELIVERING work."""
    raw = (RUNTIME / 'inbox_future_queue.json').read_bytes()
    value = json.loads(raw)
    if set(value) != {'version', 'entries'} or any(e['state'] == 'DELIVERING' for e in value['entries'].values()):
        raise ValueError('unexpected future schema/active delivery; stop')
    if json.loads((RUNTIME / 'inbox_native_recovery.json').read_text()) is not None:
        raise ValueError('native ACK pending; stop')
    b = m.checked_binding(BRIDGE)
    sys.path.insert(0, str(BRIDGE))
    from inbox_binding import public
    from inbox_future import config, lane_public, source
    from inbox_queue import InboxQueue
    lane = lane_public(config(RUNTIME))
    receipt.scope(public(b), lane)
    q = InboxQueue(RUNTIME / 'inbox_future_queue.json')
    if q.fingerprint() != receipt.FINGERPRINT:
        raise ValueError('pinned queue changed/already reconciled; no mutation')
    e = value['entries'].get(receipt.TARGET)
    if not e or e['state'] != 'NEEDS_REVIEW' or e['attempt_count'] != 1:
        raise ValueError('target no longer the authorized terminal receipt')
    trusted = source(RUNTIME, config(RUNTIME), receipt.TARGET, e['text'])
    return b, lane, q, trusted, receipt.sha(raw)


def prepare():
    if (AREA / 'plan.json').exists():
        raise ValueError('prepared plan already exists; never overwrite it')
    b, lane, q, trusted, raw_sha = state()
    receipt.trace_proof(incident().read_bytes())
    operator_record()
    h = managed.http()
    active = h.get('active_async_request') or {}
    if h.get('turn_active') is not True or not active.get('codex_turn_id'):
        raise ValueError('current task identity required for inert post-turn gate')
    life = managed.lifecycle()
    old = life.process(h['bridge_pid'])
    tray = life.process(json.loads((RUNTIME / 'tray.json').read_text())['pid'])
    if old['parent'] != tray['pid']:
        raise ValueError('existing managed tray ownership required')
    files = {str(BRIDGE / name): want for name, want in b['components'].items()}
    for p in (Path(__file__), HERE / 'receipt.py', Path(managed.__file__), Path(m.__file__),
              managed.LIFECYCLE, managed.PIPE):
        files[str(p.resolve())] = m.sha(p)
    if any(m.sha(Path(p)) != want for p, want in files.items()):
        raise ValueError('pinned source changed')
    protected = {n: m.sha(RUNTIME / n) for n in PROTECTED}
    plan = {'schema': 'inbox-pinned-owner-receipt/1', 'delivery_id': receipt.TARGET,
            'queue_fingerprint': q.fingerprint(), 'future_queue_file_sha256': raw_sha,
            'protected': protected, 'lane': lane, 'binding_identity': b['identity'],
            'trusted_source': trusted, 'incident_sha256': receipt.INCIDENT_SHA,
            'authority_comment': receipt.COMMENT, 'production_source_changes': False,
            'send_authorization': False}
    AREA.mkdir(parents=True, exist_ok=True)
    # Preserve the bounded incident against its normal retention cleanup. This
    # is diagnostic evidence, never a queue/result or a new browser observation.
    m.atomic(AREA / 'retained-incident.jsonl', incident().read_bytes())
    m.save(AREA / 'plan.json', m.sealed(plan))
    a = {'request_id': active['request_id'], 'turn_id': active['codex_turn_id'], 'old': old, 'tray': tray,
         'tools': files, 'migration_plan_sha256': m.sha(AREA / 'plan.json')}
    m.save(AREA / 'activation.json', m.sealed(a))
    print('Prepared INERT owner receipt. No source/seal/queue/cursor changes, shutdown, permit or Send.')


def unchanged(plan):
    if {n: m.sha(RUNTIME / n) for n in PROTECTED} != plan['protected']:
        raise ValueError('protected historical state/binding/lane changed; stop')


def publish(result):
    body = ('[CODEX → JARVIS / CHATGPT] #106 pinned seq132 operator receipt committed by the independent '
            'owner maintenance command. NOT an automatic exact-DOM ACK. No Send/rearm/cursor mutation.\n' +
            json.dumps(result, indent=2) +
            '\nLet the existing future worker proceed naturally; please provide read-only future cursor >135, '
            'historical hashes unchanged and one-turn evidence. Do not manually advance/reconcile later entries.')
    for issue in (45, 106):
        try:
            p = subprocess.run(['gh', 'api', f'repos/grxr-dev/codex-relay/issues/{issue}/comments',
                                '--method', 'POST', '--input', '-'], input=json.dumps({'body': body}),
                               capture_output=True, text=True, timeout=20)
            if p.returncode == 0:
                print('Posted #' + str(issue) + ': ' + str(json.loads(p.stdout)['id']))
            else:
                print('GitHub status unavailable; local result is durable. Do not repeat reconciliation.')
        except (OSError, subprocess.TimeoutExpired):
            print('GitHub status unavailable; local result is durable. Do not repeat reconciliation.')


def finish():
    managed.AREA = AREA
    a = m.read_sealed(AREA / 'activation.json')
    managed.verify_tools(a)
    life = managed.lifecycle()
    managed.independent(life)
    managed.task_finished(a)
    plan = m.read_sealed(AREA / 'plan.json')
    if (AREA / 'result.json').exists():
        raise ValueError('receipt command already finished; no second operation')
    # All fallible external evidence reads happen before requesting idle shutdown.
    unchanged(plan)
    operator = operator_record()
    raw_trace = (AREA / 'retained-incident.jsonl').read_bytes()
    receipt.trace_proof(raw_trace)
    state()
    with managed.exclusive_stopped(life, a):
        # Existing instance byte lock now prevents any other bridge queue owner.
        unchanged(plan)
        if m.sha(RUNTIME / 'inbox_future_queue.json') != plan['future_queue_file_sha256']:
            raise ValueError('future queue changed; no mutation')
        b, lane, q, trusted, _ = state()
        if lane != plan['lane'] or trusted != plan['trusted_source'] or (AREA / 'retained-incident.jsonl').read_bytes() != raw_trace:
            raise ValueError('pinned lane/completion/incident changed')
        # Backup is for forensics only. Never roll back a committed receipt after
        # worker progress; an old queue restore could duplicate later deliveries.
        m.atomic(AREA / 'future-queue.before.json', q.path.read_bytes())
        m.save(AREA / 'journal.json', m.sealed({'phase': 'PREPARED', 'plan_sha256': m.digest(plan)}))
        from inbox_binding import public
        result = receipt.reconcile(q, receipt.TARGET, plan['queue_fingerprint'], public(b), lane,
                                   trusted, raw_trace, operator, exclusive=True)
        unchanged(plan)
        result.update(historical_and_lane_files_unchanged=True, production_source_seal_unchanged=True,
                      cursor_modified=False, no_new_send=True)
        m.save(AREA / 'result.json', m.sealed(result))
        m.save(AREA / 'journal.json', m.sealed({'phase': 'COMMITTED', 'plan_sha256': m.digest(plan),
                                              'queue_fingerprint_after': result['queue_fingerprint_after']}))
    # The same managed tray normally restarts its bridge. Never force/start a
    # parallel bridge or repeat a commit if startup/status publication is delayed.
    print(json.dumps(result, indent=2))
    print('Existing managed tray owns restart. No source/extension reload or Send was requested.')
    publish(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'finish'])
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare()
        else:
            import msvcrt
            with (AREA / 'owner.lock').open('a+b') as f:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                try:
                    finish()
                finally:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception as error:
        print('STOP: ' + (str(error) if type(error) is ValueError else
                         type(error).__name__ + '; preserve state, no automatic retry'))
        sys.exit(1)
