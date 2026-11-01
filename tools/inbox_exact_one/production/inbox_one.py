"""One local-owner grant for the existing issue-95 entry. HOLD is never lifted."""
import copy
import hashlib
import re
import secrets
from pathlib import Path
from inbox_binding import load, public, digest
from inbox_binding import COMPONENTS
from inbox_queue import Conflict

BUILD = 'inbox-exact-one-20261101-01'
TARGET = 'middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878'
TEXT_SHA256 = '1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651'
DESTINATION = '6ae5615a-0720-83ea-a43b-82386ce031e5'
KEYS = {'schema','build','authorization_id','delivery_id','text_sha256','binding',
        'created_at','expires_at','queue_before_sha256','history_sha256','state',
        'claim_token_sha256','send_intent_at','events','seal'}
STATES = {'ARMED','CLAIMED','SEND_INTENT','FINISHED','REVOKED','EXPIRED'}
LOADED_SOURCES = {name:hashlib.sha256((Path(__file__).resolve().parent/name).read_bytes()).hexdigest() for name in COMPONENTS}


def sealed(value):
    result = copy.deepcopy(value)
    result['seal'] = digest({key:item for key,item in result.items() if key != 'seal'})
    return result


def validate(value):
    if not isinstance(value,dict) or set(value) != KEYS:
        raise Conflict('malformed exact-one grant')
    if value['schema'] != 'inbox-exact-one/1' or value['build'] != BUILD:
        raise Conflict('exact-one schema/build mismatch')
    if value['delivery_id'] != TARGET or value['text_sha256'] != TEXT_SHA256 or value['state'] not in STATES:
        raise Conflict('exact-one target/state mismatch')
    if not isinstance(value['authorization_id'],str) or not re.fullmatch('[0-9a-f]{32}',value['authorization_id']):
        raise Conflict('exact-one authorization identity invalid')
    for key in ('created_at','expires_at'):
        if type(value[key]) not in (int,float) or not 0 < value[key] < 1e12:
            raise Conflict('invalid grant time')
    if not 1 <= value['expires_at']-value['created_at'] <= 300:
        raise Conflict('invalid grant lifetime')
    if not isinstance(value['events'],list) or not 1 <= len(value['events']) <= 8:
        raise Conflict('invalid grant audit')
    for key in ('queue_before_sha256','history_sha256','seal'):
        if not isinstance(value[key],str) or not re.fullmatch('[0-9a-f]{64}',value[key]):
            raise Conflict('invalid grant digest')
    if value != sealed(value):
        raise Conflict('exact-one seal mismatch')
    binding = value['binding']
    if not isinstance(binding,dict) or set(binding) != {'schema','build','conversation_id','generation','epoch','delivery_policy','identity'}:
        raise Conflict('invalid grant binding')
    if binding['conversation_id'] != DESTINATION or binding['generation'] != 1 or binding['delivery_policy'] != 'HOLD':
        raise Conflict('grant cannot rebind or release HOLD')
    token = value['claim_token_sha256']
    if token is not None and (not isinstance(token,str) or not re.fullmatch('[0-9a-f]{64}',token)):
        raise Conflict('invalid grant claim')
    if value['state'] in ('ARMED','EXPIRED','REVOKED'):
        if token is not None or value['send_intent_at'] is not None:
            raise Conflict('unclaimed grant has attempt evidence')
    elif token is None:
        raise Conflict('claimed grant lacks attempt evidence')
    if value['state'] == 'SEND_INTENT' and type(value['send_intent_at']) not in (float,int):
        raise Conflict('missing durable Send intent')
    return value


def protected_history(queue):
    return digest({'entries':{key:value for key,value in queue._entries.items() if key != TARGET},
                   'recovery_once':queue._recovery,'superseded_watchdog':queue._supersession})


def binding(queue):
    try:
        config = load(queue.path.parent)
        if config['components'] != LOADED_SOURCES:
            raise ValueError('loaded source differs from sealed source; restart while idle')
        result = public(config)
    except (ValueError,OSError,KeyError,TypeError):
        raise Conflict('binding unavailable; all Inbox work held') from None
    if result['conversation_id'] != DESTINATION or result['generation'] != 1 or result['delivery_policy'] != 'HOLD':
        raise Conflict('exact-one requires the authorized generation-1 held recipient')
    return result


def ready(queue):
    if not queue._recovery_check:
        raise Conflict('loaded readiness validator unavailable')
    proof = queue._recovery_check()
    if proof['content'].get('one_build') != BUILD:
        raise Conflict('fresh exact-one content capability required')
    return proof


def checked(queue, allow_expired=False):
    value = validate(queue._one)
    if value['binding'] != binding(queue) or value['history_sha256'] != protected_history(queue):
        raise Conflict('grant binding/history changed; no action')
    if not allow_expired and not value['created_at'] <= queue.clock() < value['expires_at']:
        raise Conflict('grant expired or clock moved backwards')
    entry = queue._entries.get(TARGET)
    if not entry or entry['text_sha256'] != TEXT_SHA256 or hashlib.sha256(entry['text'].encode('utf-8')).hexdigest() != TEXT_SHA256:
        raise Conflict('exact queued text changed')
    return value,entry


def transition(value, state, now, **changes):
    result = copy.deepcopy(value)
    result.update(state=state,**changes)
    result['events'].append({'state':state,'at':now})
    return sealed(result)


def arm(queue, body):
    if not isinstance(body,dict) or set(body) != {'delivery_id','text_sha256','binding_identity','queue_fingerprint','expires_in'}:
        raise Conflict('exact explicit authorization fields required')
    with queue.lock:
        if queue._one is not None:
            raise Conflict('one-shot already issued; never rearm or retry')
        current = binding(queue)
        if body['delivery_id'] != TARGET or body['text_sha256'] != TEXT_SHA256 or body['binding_identity'] != current['identity']:
            raise Conflict('wrong exact authorization identity')
        if body['queue_fingerprint'] != queue.fingerprint():
            raise Conflict('queue changed before owner authorization')
        if type(body['expires_in']) is not int or not 1 <= body['expires_in'] <= 300:
            raise Conflict('expiry must be 1..300 seconds')
        entry = queue._entries.get(TARGET)
        if not entry or entry['text_sha256'] != TEXT_SHA256 or hashlib.sha256(entry['text'].encode()).hexdigest() != TEXT_SHA256:
            raise Conflict('exact queued payload required')
        if any(entry[key] is not None for key in ('claim_token','last_attempt_at','delivered_at','outcome','next_attempt_at','last_error')) or entry['state'] != 'QUEUED' or entry['attempt_count'] != 0:
            raise Conflict('only the existing unattempted queued entry may be granted')
        if any(item['state'] == 'DELIVERING' for item in queue._entries.values()):
            raise Conflict('another delivery is outstanding')
        if queue._recovery and queue._recovery['status'] in ('PREPARED','ARMED','CLAIMED'):
            raise Conflict('legacy recovery outstanding')
        from inbox_wire import unique_json
        if unique_json((queue.path.parent/'inbox_native_recovery.json').read_text()) is not None:
            raise Conflict('native outcome journal outstanding')
        ready(queue)
        now = queue.clock()
        value = sealed({'schema':'inbox-exact-one/1','build':BUILD,'authorization_id':secrets.token_hex(16),
                        'delivery_id':TARGET,'text_sha256':TEXT_SHA256,'binding':current,'created_at':now,
                        'expires_at':now+body['expires_in'],'queue_before_sha256':body['queue_fingerprint'],
                        'history_sha256':protected_history(queue),'state':'ARMED','claim_token_sha256':None,
                        'send_intent_at':None,'events':[{'state':'ARMED','at':now}]})
        queue._commit(copy.deepcopy(queue._entries),one=value)
        return status(queue)


def revoke(queue, authorization_id):
    with queue.lock:
        value,entry = checked(queue,allow_expired=True)
        if value['authorization_id'] != authorization_id or value['state'] != 'ARMED':
            raise Conflict('only an unclaimed exact grant can be revoked; after claim never resend')
        queue._commit(copy.deepcopy(queue._entries),one=transition(value,'REVOKED',queue.clock()))
        return status(queue)


def claim(queue):
    if queue._one is None:
        binding(queue)
        return None
    value,entry = checked(queue,allow_expired=True)
    if value['state'] != 'ARMED':
        return None
    now = queue.clock()
    if now >= value['expires_at']:
        queue._commit(copy.deepcopy(queue._entries),one=transition(value,'EXPIRED',now))
        return None
    if now < value['created_at']:
        raise Conflict('clock moved backwards')
    ready(queue)
    if entry['state'] != 'QUEUED' or entry['attempt_count'] != 0 or entry['claim_token'] is not None:
        raise Conflict('exact entry already attempted')
    entries = copy.deepcopy(queue._entries)
    entry = entries[TARGET]
    entry.update(state='DELIVERING',attempt_count=1,last_attempt_at=now,next_attempt_at=None,
                 claim_token=secrets.token_hex(32),outcome=None)
    value = transition(value,'CLAIMED',now,claim_token_sha256=hashlib.sha256(entry['claim_token'].encode()).hexdigest())
    queue._commit(entries,one=value)
    from inbox_wire import delivery_message
    result = delivery_message(entry)
    result['authorization'] = envelope(value)
    return result


def envelope(value):
    return {key:copy.deepcopy(value[key]) for key in ('schema','build','authorization_id','delivery_id','text_sha256','binding','created_at','expires_at')}


def verify_envelope(value, delivery, current, now, allow_expired=False):
    keys = {'schema','build','authorization_id','delivery_id','text_sha256','binding','created_at','expires_at'}
    if not isinstance(value,dict) or set(value) != keys or value['schema'] != 'inbox-exact-one/1' or value['build'] != BUILD:
        raise Conflict('invalid exact-one envelope')
    if value['delivery_id'] != TARGET or delivery['delivery_id'] != TARGET or value['text_sha256'] != TEXT_SHA256 or delivery['text_sha256'] != TEXT_SHA256:
        raise Conflict('wrong exact-one payload')
    if value['binding'] != current or current['conversation_id'] != DESTINATION or current['generation'] != 1 or current['delivery_policy'] != 'HOLD':
        raise Conflict('stale exact-one recipient')
    if not re.fullmatch('[0-9a-f]{32}',value['authorization_id']) or type(value['created_at']) not in (int,float) or type(value['expires_at']) not in (int,float) or not value['created_at'] <= now or not 1 <= value['expires_at']-value['created_at'] <= 300 or (not allow_expired and now >= value['expires_at']):
        raise Conflict('invalid/expired exact-one grant')
    return value


def require_claim(queue, body, allow_expired=False):
    value,entry = checked(queue,allow_expired=allow_expired)
    if body.get('delivery_id') != TARGET or body.get('authorization_id') != value['authorization_id'] or body.get('claim_token') != entry['claim_token'] or hashlib.sha256(str(body.get('claim_token')).encode()).hexdigest() != value['claim_token_sha256']:
        raise Conflict('exact-one claim mismatch')
    return value,entry


def send_permit(queue, body):
    with queue.lock:
        if not isinstance(body,dict) or set(body) != {'delivery_id','authorization_id','claim_token','text_sha256','binding_identity'}:
            raise Conflict('invalid Send permit request')
        value,entry = require_claim(queue,body)
        if value['state'] != 'CLAIMED' or entry['state'] != 'DELIVERING' or body['text_sha256'] != TEXT_SHA256 or body['binding_identity'] != value['binding']['identity']:
            raise Conflict('Send permit consumed or changed')
        now = queue.clock()
        queue._commit(copy.deepcopy(queue._entries),one=transition(value,'SEND_INTENT',now,send_intent_at=now))
        return {'ok':True,'authorization_id':value['authorization_id'],'expires_at':value['expires_at'],'build':BUILD}


def ack_guard(queue, did, authorization_id, claim_token, state, user_turn_uuid):
    value,entry = require_claim(queue,{'delivery_id':did,'authorization_id':authorization_id,'claim_token':claim_token},allow_expired=True)
    if value['state'] not in ('CLAIMED','SEND_INTENT','FINISHED'):
        raise Conflict('grant cannot ACK')
    if state == 'DELIVERED' and (value['send_intent_at'] is None or not isinstance(user_turn_uuid,str) or not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',user_turn_uuid)):
        raise Conflict('durable Send intent and exact new USER UUID required')
    return value


def finish(value, now):
    return value if value['state'] == 'FINISHED' else transition(value,'FINISHED',now)


def status(queue):
    with queue.lock:
        return {'ok':True,'build':BUILD,'binding':binding(queue),'queue_fingerprint':queue.fingerprint(),
                'grant':copy.deepcopy(queue._one),'delivery_authorized':bool(queue._one and queue._one['state'] == 'ARMED'),
                'loaded_source_identity':digest(LOADED_SOURCES),'history_held':True}
