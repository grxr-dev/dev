"""Two remote routes and two loopback-only routes; no general RPC."""
from urllib.parse import unquote
from inbox_queue import Conflict
from inbox_wire import validate_text,delivery_message
PUBLIC=('delivery_id','text_sha256','created_at','state','attempt_count','last_attempt_at','delivered_at','last_error','next_attempt_at')
class InboxApi:
    def __init__(self,queue):self.queue=queue
    def post_inbox(self,body,authorized):
        if not authorized:return 401,{'ok':False,'error':'unauthorized'}
        try:
            if not isinstance(body,dict) or set(body)!={'delivery_id','text'}:raise ValueError('only delivery_id and text are accepted')
            text=validate_text(body['delivery_id'],body['text'])
            e,created=self.queue.enqueue(body['delivery_id'],text)
            return (201 if created else 200),{'ok':True,'delivery_id':e['delivery_id'],'state':e['state'],'duplicate':not created,'text_sha256':e['text_sha256']}
        except Conflict as exc:return 409,{'ok':False,'error':str(exc)}
        except (ValueError,UnicodeError) as exc:return 400,{'ok':False,'error':str(exc)}
    def get_inbox(self,did,authorized):
        if not authorized:return 401,{'ok':False,'error':'unauthorized'}
        try:did=unquote(did,errors='strict')
        except UnicodeError:return 400,{'ok':False,'error':'invalid delivery_id'}
        e=self.queue.get(did)
        return (200,{'ok':True,'entry':{k:e[k] for k in PUBLIC}|{'text_chars':len(e['text'])}}) if e else (404,{'ok':False,'error':'not_found'})
    def local_next(self):
        from inbox_one import claim
        with self.queue.lock:e=claim(self.queue)
        return (200,(e if e.get('cmd')=='delivery' else delivery_message(e))|{'ok':True}) if e else (204,None)
    def local_ack(self,body):
        allowed={'delivery_id','state','error','claim_token','pre_send','observed_sha256','send_count','new_user_turns','composer_empty','authorization_id','user_turn_uuid'}
        try:
            from inbox_one import binding
            binding(self.queue)
            if self.queue._one is None:raise Conflict('all historical ACKs remain held')
            if not isinstance(body,dict) or not {'delivery_id','state','claim_token'}<=set(body) or not set(body)<=allowed:raise ValueError('invalid ACK schema')
            e=self.queue.ack(body['delivery_id'],body['state'],body.get('error'),**{k:v for k,v in body.items() if k not in ('delivery_id','state','error')})
            return (200,{'ok':True,'state':e['state']}) if e else (404,{'ok':False,'error':'not_found'})
        except Conflict as exc:return 409,{'ok':False,'error':str(exc)}
        except (ValueError,TypeError) as exc:return 400,{'ok':False,'error':str(exc)}
