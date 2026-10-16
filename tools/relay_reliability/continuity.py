"""Transactional reference consumer. No inference, browser sends, or task creation."""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def atomic_status(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        handle.write(canonical(value))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class IntegrityError(ValueError):
    pass


def envelope(body, key):
    if not isinstance(body, str) or '\r' in body or not body.startswith('---\n'):
        raise IntegrityError('invalid_envelope')
    header, separator, text = body[4:].partition('\n---\n')
    fields = {}
    for line in header.splitlines():
        name, delimiter, value = line.partition(': ')
        if not delimiter or name in fields:
            raise IntegrityError('duplicate_or_invalid_header')
        fields[name] = value
    if not separator or fields.get(key) != '1':
        raise IntegrityError('invalid_version')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', fields.get('request_id', '')):
        raise IntegrityError('invalid_request_id')
    return fields, text


def reset_time(text):
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    error = payload.get('error') or {}
    if not isinstance(error, dict):
        return None
    for name in ('resetsAt', 'reset_at', 'resetAt'):
        value = error.get(name, payload.get(name))
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            return str(value)
    match = re.search(r'try again at ([^\n]+?)\.(?:\s|$)', str(error.get('message', '')), re.IGNORECASE)
    if match:
        return 'reported-local:' + match.group(1)
    return None


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(self.path, timeout=20)
            self.db.row_factory = sqlite3.Row
            if self.db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise IntegrityError('state_integrity_failure')
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.executescript('''
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests(repo TEXT,request_id TEXT,issue INTEGER,
              created TEXT,prompt TEXT,prompt_hash TEXT,PRIMARY KEY(repo,request_id));
            CREATE TABLE IF NOT EXISTS receipts(repo TEXT,comment INTEGER,request_id TEXT,
              body TEXT,body_hash TEXT,PRIMARY KEY(repo,comment));
            CREATE TABLE IF NOT EXISTS results(local_seq INTEGER PRIMARY KEY AUTOINCREMENT,
              repo TEXT,request_id TEXT,status TEXT,result_hash TEXT,text TEXT,comment INTEGER,
              bridge_sequence INTEGER,ingested_at REAL NOT NULL,UNIQUE(repo,request_id));
            CREATE TABLE IF NOT EXISTS retry_wait(repo TEXT,request_id TEXT,reset_at TEXT,
              state TEXT,PRIMARY KEY(repo,request_id));
            CREATE TABLE IF NOT EXISTS intents(repo TEXT,parent TEXT,kind TEXT,state TEXT,
              PRIMARY KEY(repo,parent,kind));
            CREATE TABLE IF NOT EXISTS signals(key TEXT PRIMARY KEY,body TEXT,state TEXT,comment INTEGER);
            CREATE TABLE IF NOT EXISTS health(worker TEXT PRIMARY KEY,value TEXT);
            CREATE TABLE IF NOT EXISTS quarantine(repo TEXT,issue INTEGER,observation_sha256 TEXT,
              reason TEXT,evidence_json TEXT,first_seen REAL,PRIMARY KEY(repo,issue,observation_sha256));
            ''')
            version = self.db.execute("SELECT value FROM metadata WHERE key='schema'").fetchone()
            if version and version[0] != 'relay-continuity/1':
                raise IntegrityError('unsupported_schema')
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES('schema','relay-continuity/1')")
            self.db.commit()
        except (sqlite3.DatabaseError, IntegrityError):
            if hasattr(self, 'db'):
                self.db.close()
            atomic_status(str(self.path) + '.error.json', {'state': 'ERROR', 'error': 'state_integrity_failure',
                          'recovery': 'preserve database; restore verified backup or reconcile GitHub; never reset cursor'})
            raise

    def close(self):
        self.db.close()

    def health(self, worker, **changes):
        row = self.db.execute('SELECT value FROM health WHERE worker=?', (worker,)).fetchone()
        value = json.loads(row[0]) if row else {'last_success': None, 'failures': 0}
        value.update(changes, observed_at=time.time())
        value.setdefault('dependencies', {'bridge': 'NOT_REQUIRED', 'inbox': 'NOT_REQUIRED'})
        value.setdefault('next_retry_seconds', 10)
        value.setdefault('continuity_healthy', None)
        value.setdefault('inbox_delivery_degraded', None)
        value['intentional_pause'] = value.get('state') == 'INTENTIONAL_PAUSE'
        value.update(schema='relay-worker-health/1', worker=worker, pid=os.getpid(),
                     build=digest(Path(__file__).read_text(encoding='utf-8')),
                     local_high_water=self.db.execute('SELECT coalesce(max(local_seq),0) FROM results').fetchone()[0],
                     backlog=self.db.execute('''SELECT count(*) FROM requests q LEFT JOIN results r USING(repo,request_id)
                         WHERE r.local_seq IS NULL''').fetchone()[0])
        self.db.execute('INSERT OR REPLACE INTO health VALUES(?,?)', (worker, canonical(value)))
        return value

    def snapshot(self):
        workers = {row['worker']: json.loads(row['value']) for row in self.db.execute('SELECT * FROM health')}
        return {'schema': 'relay-continuity/1', 'workers': workers,
                'result_count': self.db.execute('SELECT count(*) FROM results').fetchone()[0],
                'local_high_water': self.db.execute('SELECT coalesce(max(local_seq),0) FROM results').fetchone()[0],
                'pending_intents': [dict(row) for row in self.db.execute("SELECT * FROM intents WHERE state!='ACKED'")],
                'usage_retries': [dict(row) for row in self.db.execute('SELECT * FROM retry_wait')]}

    def request(self, repo, issue, synthetic=False):
        fields, prompt = envelope(issue['body'], 'codex_relay_version')
        prefix = '[RELAY RELIABILITY SMOKE] ' if synthetic else '[CODEX RELAY] '
        if issue['title'] != prefix + fields['request_id']:
            raise IntegrityError('request_title_mismatch')
        old = self.db.execute('SELECT * FROM requests WHERE repo=? AND request_id=?',
                              (repo, fields['request_id'])).fetchone()
        values = (repo, fields['request_id'], issue['number'], issue['created_at'], prompt, digest(issue['body']))
        if old and tuple(old) != values:
            raise IntegrityError('request_identity_changed')
        self.db.execute('INSERT OR IGNORE INTO requests VALUES(?,?,?,?,?,?)', values)
        return fields['request_id']

    def comment(self, repo, request_id, comment):
        fields, text = envelope(comment['body'], 'codex_relay_result_version')
        if fields['request_id'] != request_id or not re.fullmatch('[0-9a-f]{64}', fields.get('result_sha256', '')):
            raise IntegrityError('result_identity_mismatch')
        old = self.db.execute('SELECT body_hash FROM receipts WHERE repo=? AND comment=?',
                              (repo, comment['id'])).fetchone()
        if old and old[0] != digest(comment['body']):
            raise IntegrityError('terminal_comment_edited')
        self.db.execute('INSERT OR IGNORE INTO receipts VALUES(?,?,?,?,?)',
                        (repo, comment['id'], request_id, comment['body'], digest(comment['body'])))
        return fields, text

    def assemble(self, repo, request_id):
        rows = self.db.execute('SELECT * FROM receipts WHERE repo=? AND request_id=? ORDER BY comment',
                               (repo, request_id)).fetchall()
        completed = []
        for row in rows:
            fields, text = envelope(row['body'], 'codex_relay_result_version')
            if text.startswith('[CODEX \u2192 CHATGPT]\n'):
                completed.append((fields, text[len('[CODEX \u2192 CHATGPT]\n'):], row['comment']))
            elif text.startswith('manifest: '):
                manifest = json.loads(text[len('manifest: '):])
                chunks = {}
                total = len(manifest['chunks'])
                for candidate in rows:
                    chunk_fields, chunk_text = envelope(candidate['body'], 'codex_relay_result_version')
                    if not chunk_text.startswith('chunk: ') or chunk_fields != fields:
                        continue
                    lines = chunk_text.split('\n', 3)
                    position, count = map(int, lines[0][7:].split('/'))
                    if count != total or not 1 <= position <= total or lines[2] != '':
                        raise IntegrityError('invalid_chunk')
                    value = lines[3]
                    if lines[1] != 'chunk_sha256: ' + digest(value) or digest(value) != manifest['chunks'][position-1]:
                        raise IntegrityError('chunk_hash_mismatch')
                    if position in chunks and chunks[position] != value:
                        raise IntegrityError('conflicting_chunk')
                    chunks[position] = value
                if len(chunks) != total:
                    continue
                message = ''.join(chunks[position] for position in range(1, total+1))
                if digest(message) != manifest['message_sha256'] or not message.startswith('[CODEX \u2192 CHATGPT]\n'):
                    raise IntegrityError('manifest_mismatch')
                completed.append((fields, message[len('[CODEX \u2192 CHATGPT]\n'):], row['comment']))
            elif not text.startswith('chunk: '):
                raise IntegrityError('unknown_result_format')
        for fields, text, comment_id in completed:
            if digest(text) != fields['result_sha256']:
                raise IntegrityError('result_hash_mismatch')
            status = fields.get('status')
            if status not in ('COMPLETED', 'FAILED', 'INTERRUPTED', 'USAGE_EXHAUSTED', 'RATE_LIMITED',
                              'APP_SERVER_LOST', 'TRANSPORT_LOST'):
                raise IntegrityError('unknown_terminal_state')
            old = self.db.execute('SELECT * FROM results WHERE repo=? AND request_id=?', (repo, request_id)).fetchone()
            if old and (old['result_hash'], old['status']) != (digest(text), status):
                raise IntegrityError('conflicting_terminal_result')
            if not old:
                self.db.execute('INSERT INTO results(repo,request_id,status,result_hash,text,comment,ingested_at) VALUES(?,?,?,?,?,?,?)',
                                (repo, request_id, status, digest(text), text, comment_id, time.time()))
            if status in ('USAGE_EXHAUSTED', 'RATE_LIMITED'):
                reset = reset_time(text)
                retry_state = ('RESET_ZONE_REQUIRED' if reset and reset.startswith('reported-local:')
                               else 'RETRY_WAIT' if reset else 'RESET_TIME_REQUIRED')
                self.db.execute('INSERT OR IGNORE INTO retry_wait VALUES(?,?,?,?)',
                                (repo, request_id, reset, retry_state))
                if reset:
                    self.db.execute('UPDATE retry_wait SET reset_at=?,state=? WHERE repo=? AND request_id=? AND reset_at IS NULL',
                                    (reset, retry_state, repo, request_id))
        return bool(completed)

    def enrich(self, repo, request_id, bridge_sequence):
        if type(bridge_sequence) is not int or bridge_sequence <= 0:
            raise IntegrityError('invalid_bridge_sequence')
        row = self.db.execute('SELECT bridge_sequence FROM results WHERE repo=? AND request_id=?',
                              (repo, request_id)).fetchone()
        if row is None or row[0] is not None and row[0] != bridge_sequence:
            raise IntegrityError('bridge_enrichment_conflict')
        self.db.execute('UPDATE results SET bridge_sequence=? WHERE repo=? AND request_id=?',
                        (bridge_sequence, repo, request_id))

    def scan(self, repo, project_prefix, paused=True, grace=900, now=None):
        now = time.time() if now is None else now
        if paused:
            return {'state': 'INTENTIONAL_PAUSE', 'after': 'AW16', 'successor_permitted': False}
        rows = self.db.execute('''SELECT r.*,q.created FROM results r JOIN requests q USING(repo,request_id)
            WHERE r.repo=? AND substr(r.request_id,1,?)=? ORDER BY q.created DESC,q.issue DESC''',
            (repo, len(project_prefix), project_prefix)).fetchall()
        if not rows:
            return {'state': 'NO_VERIFIED_RESULT', 'successor_permitted': False}
        latest = rows[0]
        if self.db.execute('SELECT 1 FROM retry_wait WHERE repo=? AND request_id=?',
                           (repo, latest['request_id'])).fetchone():
            return {'state': 'RETRY_PENDING', 'successor_permitted': False}
        pending = self.db.execute('''SELECT 1 FROM requests WHERE repo=? AND created>? AND
            substr(request_id,1,?)=?''', (repo, latest['created'], len(project_prefix), project_prefix)).fetchone()
        if pending:
            return {'state': 'SUCCESSOR_OR_RETRY_PRESENT', 'successor_permitted': False}
        if now - latest['ingested_at'] < grace:
            return {'state': 'GRACE', 'successor_permitted': False}
        self.db.execute("INSERT OR IGNORE INTO intents VALUES(?,?, 'SENIOR_REVIEW','PENDING')", (repo, latest['request_id']))
        return {'state': 'SENIOR_REVIEW_REQUIRED', 'parent': latest['request_id'], 'successor_permitted': False}


class Poller:
    def __init__(self, store, client, repo, author, synthetic=False):
        self.store, self.client, self.repo, self.author = store, client, repo, author
        self.synthetic = synthetic

    def tick(self, after_fetch=None, bridge=None, inbox=None):
        try:
            self.client.private()
            if self.client.call('user')['login'] != self.author:
                raise IntegrityError('credential_actor_mismatch')
            issues = self.client.pages('issues?state=all&sort=created&direction=asc')
            fetched = []
            prefix = '[RELAY RELIABILITY SMOKE] ' if self.synthetic else '[CODEX RELAY] '
            for issue in issues:
                if issue.get('pull_request') or not issue.get('title', '').startswith(prefix):
                    continue
                if isinstance(self.synthetic, str) and issue['title'] != prefix + self.synthetic:
                    continue
                if issue.get('user', {}).get('login') != self.author:
                    raise IntegrityError('request_author_mismatch')
                comments = self.client.pages('issues/' + str(issue['number']) + '/comments')
                fetched.append((issue, [comment for comment in comments if comment.get('body', '').startswith(
                    '---\ncodex_relay_result_version: ') and comment.get('user', {}).get('login') == self.author]))
            if after_fetch:
                after_fetch()
            with self.store.db:
                self.store.db.execute('BEGIN IMMEDIATE')
                incomplete = 0
                quarantined = []
                for issue, comments in fetched:
                    self.store.db.execute('SAVEPOINT issue_ingestion')
                    try:
                        request_id = self.store.request(self.repo, issue, self.synthetic)
                        for comment in comments:
                            self.store.comment(self.repo, request_id, comment)
                        if comments and not self.store.assemble(self.repo, request_id):
                            incomplete += 1
                    except IntegrityError as error:
                        self.store.db.execute('ROLLBACK TO issue_ingestion')
                        evidence = canonical({'issue': issue, 'comments': comments})
                        self.store.db.execute('INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?,?,?)',
                            (self.repo, issue['number'], digest(evidence), str(error), evidence, time.time()))
                        quarantined.append({'issue': issue['number'], 'reason': str(error), 'evidence_sha256': digest(evidence)})
                    finally:
                        self.store.db.execute('RELEASE issue_ingestion')
                dependency_degraded = bridge not in (None, 'HEALTHY', 'NOT_REQUIRED') or inbox != 'HEALTHY'
                self.store.health('github_poller', state='DEGRADED' if incomplete or quarantined or dependency_degraded else 'HEALTHY',
                    ingestion_state='DEGRADED' if incomplete or quarantined else 'HEALTHY', quarantined=quarantined,
                    last_success=time.time(), failures=0,
                    last_error=quarantined[0]['reason'] if quarantined else 'incomplete_multipart' if incomplete else None,
                    incomplete_results=incomplete, continuity_healthy=not incomplete and not quarantined, inbox_delivery_degraded=inbox != 'HEALTHY',
                    dependencies={'bridge': bridge or 'NOT_REQUIRED', 'inbox': inbox or 'UNKNOWN',
                                  'vm_to_host': 'NOT_REQUIRED'}, next_retry_seconds=10)
            return self.store.snapshot()
        except Exception as error:
            self.store.db.rollback()
            with self.store.db:
                prior = self.store.snapshot()['workers'].get('github_poller', {})
                failures = prior.get('failures', 0) + 1
                self.store.health('github_poller', state='ERROR', continuity_healthy=False,
                    last_error=str(error) if isinstance(error, IntegrityError) else type(error).__name__,
                    failures=failures, next_retry_seconds=min(300, 10 * 2**min(failures, 5)))
            raise


def _signal(store, client, repo, key, body):
    """Durable exact-comment reconciliation; uncertain POST is never blindly repeated."""
    marker = '[RELAY-CONTINUITY/1 ' + key + ']\n' + body
    with store.db:
        old = store.db.execute('SELECT * FROM signals WHERE key=?', (key,)).fetchone()
        if old and old['body'] != marker:
            raise IntegrityError('signal_identity_conflict')
        store.db.execute("INSERT OR IGNORE INTO signals VALUES(?,?,'PENDING',NULL)", (key, marker))
    matches = [comment for comment in client.pages('issues/45/comments') if comment.get('body') == marker
               and comment.get('user', {}).get('login') == 'grxr-dev']
    if len(matches) > 1:
        raise IntegrityError('duplicate_direct_signal')
    row = store.db.execute('SELECT * FROM signals WHERE key=?', (key,)).fetchone()
    if matches:
        with store.db:
            store.db.execute("UPDATE signals SET state='VERIFIED',comment=? WHERE key=?", (matches[0]['id'], key))
        return matches[0]['id']
    if row['state'] != 'PENDING':
        raise IntegrityError('uncertain_signal_requires_readback_no_resend')
    with store.db:
        store.db.execute("UPDATE signals SET state='POSTING' WHERE key=?", (key,))
    result = client.call('repos/' + repo + '/issues/45/comments', 'POST', {'body': marker})
    if result.get('body') != marker or result.get('user', {}).get('login') != 'grxr-dev':
        raise IntegrityError('signal_readback_mismatch')
    with store.db:
        store.db.execute("UPDATE signals SET state='VERIFIED',comment=? WHERE key=?", (result['id'], key))
    return result['id']


def signal(store, client, repo, key, body):
    try:
        result = _signal(store, client, repo, key, body)
        with store.db:
            store.health('direct45', state='HEALTHY', last_success=time.time(), last_error=None, comment_id=result)
        return result
    except Exception as error:
        with store.db:
            store.health('direct45', state='ERROR', last_error=type(error).__name__,
                         recovery='exact GitHub readback only; uncertain POST must never auto-resend')
        raise
