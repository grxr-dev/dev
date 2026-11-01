"""Inbox-only logical text and bounded Native Messaging wire contract."""
import hashlib
import json
import re
MAX_NATIVE_BYTES = 262144  # well below Firefox's 1 MiB application-message limit
MAX_TEXT_BYTES = 131072
MAX_HTTP_BYTES = 1048576
ID_RE = re.compile(r'[A-Za-z0-9:_.-]{1,200}\Z')

def canonical_text(text):
    if not isinstance(text, str):
        raise ValueError('text must be a string')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text.encode('utf-8', 'strict')
    if any(ord(c) < 32 and c not in '\n\t' for c in text):
        raise ValueError('unsupported control character')
    return text

def sha256_text(text):
    return hashlib.sha256(canonical_text(text).encode('utf-8')).hexdigest()

def encoded(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')

def delivery_message(entry):
    return {k: entry[k] for k in ('delivery_id','text','text_sha256','attempt_count','claim_token')} | {'cmd':'delivery'}

def validate_text(delivery_id, text):
    if not isinstance(delivery_id, str) or not ID_RE.fullmatch(delivery_id):
        raise ValueError('invalid delivery_id')
    text = canonical_text(text)
    if not text or len(text.encode('utf-8')) > MAX_TEXT_BYTES:
        raise ValueError('text must be nonempty and at most 131072 UTF-8 bytes')
    envelope = {'delivery_id':delivery_id, 'text':text, 'text_sha256':sha256_text(text),
                'attempt_count':3,'claim_token':'f'*64}
    if len(encoded(delivery_message(envelope))) > MAX_NATIVE_BYTES:
        raise ValueError('encoded delivery exceeds 262144 bytes')
    return text

def unique_json(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj: raise ValueError('duplicate JSON key')
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid constant')))
