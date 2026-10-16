"""Real GitHub synthetic result/45 smoke; never opens a Codex relay request."""
import argparse
import json
from pathlib import Path
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.error
import urllib.request

from continuity import Store, Poller, IntegrityError, digest, signal, atomic_status

REPO = 'grxr-dev/codex-relay'
IDENTITY = 'relay-reliability-smoke-20261016-02'


class FaultEndpoint(BaseHTTPRequestHandler):
    status = 404

    def do_GET(self):
        self.send_response(type(self).status)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'{}')

    def log_message(self, *args):
        pass


def dependency_probe(port):
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                'http://127.0.0.1:' + str(port) + '/events/completions?after=0', timeout=3):
            return 'HEALTHY'
    except urllib.error.HTTPError as error:
        return 'HTTP_' + str(error.code)
    except OSError:
        return 'TRANSPORT_ERROR'


def post_once(store, client, key, path, payload, matches):
    with store.db:
        row = store.db.execute('SELECT * FROM signals WHERE key=?', (key,)).fetchone()
        if row and row['body'] != json.dumps(payload, sort_keys=True):
            raise IntegrityError('smoke_post_identity_conflict')
        if not row:
            store.db.execute("INSERT INTO signals VALUES(?,?,'PENDING',NULL)", (key, json.dumps(payload, sort_keys=True)))
    if len(matches) > 1:
        raise IntegrityError('duplicate_smoke_artifact')
    if matches:
        result = matches[0]
    else:
        row = store.db.execute('SELECT state FROM signals WHERE key=?', (key,)).fetchone()
        if row[0] != 'PENDING':
            raise IntegrityError('uncertain_smoke_post_no_resend')
        with store.db:
            store.db.execute("UPDATE signals SET state='POSTING' WHERE key=?", (key,))
        result = client.call(path, 'POST', payload)
    if result.get('body') != payload['body']:
        raise IntegrityError('smoke_post_verification_failed')
    with store.db:
        store.db.execute("UPDATE signals SET state='VERIFIED',comment=? WHERE key=?", (result['id'], key))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge-source', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--publish', action='store_true', required=True)
    args = parser.parse_args()
    args.evidence.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.bridge_source.resolve()))
    from github_bus import GHClient
    client = GHClient(REPO)
    client.private()
    if client.call('user')['login'] != 'grxr-dev':
        raise IntegrityError('wrong_github_actor')
    store = Store(args.evidence / 'smoke.sqlite3')
    endpoint = ThreadingHTTPServer(('127.0.0.1', 0), FaultEndpoint)
    thread = threading.Thread(target=endpoint.serve_forever, daemon=True)
    thread.start()
    try:
        title = '[RELAY RELIABILITY SMOKE] ' + IDENTITY
        body = ('---\ncodex_relay_version: 1\nrequest_id: ' + IDENTITY +
                '\nthread_key: main\nroute_id: sol-high\n---\nSYNTHETIC TRANSPORT ONLY. '
                'Never execute or plan any task. Not a Brain Age request. No inference authorized.')
        existing = [issue for issue in client.pages('issues?state=all') if issue.get('title') == title]
        issue = post_once(store, client, 'smoke-issue', 'repos/' + REPO + '/issues',
                          {'title': title, 'body': body}, existing)
        text = 'Synthetic relay reliability result. No inference, no Brain Age state, no successor.'
        result_body = ('---\ncodex_relay_result_version: 1\nrequest_id: ' + IDENTITY +
                       '\nroute_id: sol-high\nstatus: COMPLETED\nterminal_reason: synthetic\nresult_sha256: ' +
                       digest(text) + '\n---\n[CODEX \u2192 CHATGPT]\n' + text)
        comments_path = 'issues/' + str(issue['number']) + '/comments'
        matches = [comment for comment in client.pages(comments_path) if comment.get('body') == result_body]
        comment = post_once(store, client, 'smoke-result', 'repos/' + REPO + '/' + comments_path,
                            {'body': result_body}, matches)
        poller = Poller(store, client, REPO, 'grxr-dev', synthetic=IDENTITY)
        before = store.snapshot()
        degraded = poller.tick(bridge=dependency_probe(endpoint.server_port), inbox='UNAVAILABLE_INJECTED')
        propagation = [degraded]
        for attempt in range(5):
            if degraded['result_count'] == 1:
                break
            time.sleep(2)
            degraded = poller.tick(bridge=dependency_probe(endpoint.server_port), inbox='UNAVAILABLE_INJECTED')
            propagation.append(degraded)
        if degraded['result_count'] != 1:
            raise IntegrityError('expected_smoke_result_not_discovered')
        with store.db:
            detection = store.scan(REPO, 'relay-reliability-smoke-', paused=False, grace=0)
            pause = store.scan(REPO, 'brainage-task-', paused=True)
        store.close()
        store = Store(args.evidence / 'smoke.sqlite3')
        poller = Poller(store, client, REPO, 'grxr-dev', synthetic=IDENTITY)
        repeated = poller.tick(bridge=dependency_probe(endpoint.server_port), inbox='NEEDS_REVIEW_INJECTED')
        signal_id = signal(store, client, REPO, IDENTITY,
            '[CODEX \u2192 JARVIS] INFRASTRUCTURE SMOKE ONLY; no inference/task/successor authorized. '
            'Brain Age remains intentionally PAUSED after AW16. Real GitHub result issue #' + str(issue['number']) +
            ' comment ' + str(comment['id']) + ' ingested despite injected completions HTTP404 and Inbox outage; '
            'restart dedupe verified. ACK this exact comment ID through the independent #45 channel. '
            'Windows runtime source remains staged; active bridge cannot be safely restarted during this turn. '
            'Cross-side reliability gate remains CLOSED pending activation and Jarvis acceptance.')
        self_check = signal(store, client, REPO, IDENTITY,
            '[CODEX \u2192 JARVIS] INFRASTRUCTURE SMOKE ONLY; no inference/task/successor authorized. '
            'Brain Age remains intentionally PAUSED after AW16. Real GitHub result issue #' + str(issue['number']) +
            ' comment ' + str(comment['id']) + ' ingested despite injected completions HTTP404 and Inbox outage; '
            'restart dedupe verified. ACK this exact comment ID through the independent #45 channel. '
            'Windows runtime source remains staged; active bridge cannot be safely restarted during this turn. '
            'Cross-side reliability gate remains CLOSED pending activation and Jarvis acceptance.')
        FaultEndpoint.status = 200
        recovered = poller.tick(bridge=dependency_probe(endpoint.server_port), inbox='HEALTHY')
        evidence = {'schema': 'relay-reliability-smoke/1', 'issue': issue['number'], 'comment_id': comment['id'],
                    'result_sha256': digest(text), 'direct45_comment_id': signal_id, 'direct45_dedupe': self_check == signal_id,
                    'before': before, 'during': degraded, 'restart': repeated, 'after': recovered,
                    'propagation_polls': propagation,
                    'synthetic_continuity_detection': detection, 'brainage_pause': pause,
                    'dedupe': repeated['result_count'] == degraded['result_count'] == recovered['result_count'] == 1,
                    'fault_scope': 'ephemeral HTTP dependency endpoint + injected Inbox status; production services untouched',
                    'production_jarvis_poller_validated': False, 'gate': 'CLOSED', 'new_inference': False}
        atomic_status(args.evidence / 'smoke.json', evidence)
        print(json.dumps(evidence, sort_keys=True))
    finally:
        endpoint.shutdown()
        endpoint.server_close()
        store.close()


if __name__ == '__main__':
    main()
