"""Narrow Firefox transport. No remote bearer, URLs, commands, or general RPC.
Recovery journal is written BEFORE forwarding and BEFORE ACK. Recovery only
replays an outcome ACK; it NEVER forwards an uncertain delivery again.
"""
import json
import os
from pathlib import Path
import struct
import sys
import urllib.request
import time
import re
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from inbox_wire import encoded,unique_json,MAX_NATIVE_BYTES,delivery_message,validate_text,sha256_text
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from incident_retention import retain, VERSION as INCIDENT_RETENTION_BUILD
from readiness_diagnostic import ReadinessDiagnostic
from inbox_binding import load as load_binding, public as public_binding
from inbox_one import verify_envelope, BUILD as ONE_BUILD
from inbox_future import config as future_config,lane_public,BUILD as FUTURE_BUILD
import uuid

def read_message(stream):
    raw=stream.read(4)
    if not raw:return None
    if len(raw)!=4:raise ValueError('truncated length')
    n=struct.unpack('<I',raw)[0]
    if not 0<n<=MAX_NATIVE_BYTES:raise ValueError('invalid frame size')
    raw=stream.read(n)
    if len(raw)!=n:raise ValueError('truncated frame')
    msg=unique_json(raw.decode('utf-8'))
    if not isinstance(msg,dict):raise ValueError('expected object')
    return msg

def write_message(stream,msg):
    raw=encoded(msg)
    if len(raw)>MAX_NATIVE_BYTES:raise ValueError('oversized frame')
    stream.write(struct.pack('<I',len(raw))+raw);stream.flush()

def request(base,path,payload=None):
    # No environment proxy: this process may contact only the fixed loopback listener.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request(base+path,data=None if payload is None else encoded(payload),
          headers={'X-Jarvis-Local':'1','Content-Type':'application/json'})
    with opener.open(req,timeout=10) as resp:
        if resp.status==204:return 204,None
        raw=resp.read(MAX_NATIVE_BYTES+1025)
        if len(raw)>MAX_NATIVE_BYTES+1024:raise ValueError('oversized bridge response')
        return resp.status,unique_json(raw.decode('utf-8'))

def journal_write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,allow_nan=False);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

TRACE_MAX_BYTES=262144
TRACE_FILES=4
TRACE_FIELDS={'build','delivery_id','event','ts_ms','payload_sha256','bound','state','reason','pre_send','deadline_ms','baseline_ids','baseline_count','baseline_truncated','sample','candidates','candidate_count','candidates_truncated','match_count','uuid','conv_id','conv_changed','is_branch'}
CANDIDATE_FIELDS={'uuid','in_baseline','canonical_match','hash_match','source','observed_sha256','expected_sha256','expected_len','observed_len','raw_len','mismatch_index','mismatch_window','normalization'}
def trace_event(path,event):
    """Bounded metadata-only sink. All failures are observational and swallowed."""
    try:
        if not isinstance(event,dict) or not set(event)<=TRACE_FIELDS:return
        clean={}
        for k,v in event.items():
            if k=='baseline_ids':
                if not isinstance(v,list):return
                clean[k]=[x for x in v[:256] if isinstance(x,str) and re.fullmatch(r'[0-9a-fA-F-]{36}',x)]
            elif k=='candidates':
                if not isinstance(v,list):return
                clean[k]=[]
                for c in v[:64]:
                    if not isinstance(c,dict) or not set(c)<=CANDIDATE_FIELDS:return
                    if any(not (x is None or isinstance(x,(bool,int,float)) or isinstance(x,str) and len(x)<=80) for x in c.values()):return
                    clean[k].append(c)
            elif k=='conv_id':
                if v is not None and not (isinstance(v,str) and re.fullmatch(r'[0-9a-f-]{36}',v)):return
                clean[k]=v
            elif k in ('conv_changed','is_branch'):
                if not (v is None or isinstance(v,bool)):return
                clean[k]=v
            elif v is None or isinstance(v,(bool,int,float)):clean[k]=v
            elif isinstance(v,str) and len(v)<=256:clean[k]=v
            else:return
        clean['native_received_ms']=int(time.time()*1000)
        did=clean.get('delivery_id','')
        clean['request_id']=did.rsplit(':',1)[0] if re.search(r':[0-9a-f]{64}$',did) else did
        data=(json.dumps(clean,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
        if len(data)>TRACE_MAX_BYTES:return
        retain(path,clean)
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.stat().st_size+len(data)>TRACE_MAX_BYTES:
            for n in range(TRACE_FILES-1,0,-1):
                src=path if n==1 else Path(str(path)+'.'+str(n-1))
                dst=Path(str(path)+'.'+str(n))
                if src.exists():os.replace(src,dst)
        with path.open('ab') as f:f.write(data);f.flush()
    except Exception:pass

class Transport:
    def __init__(self,base,journal,http=request):
        if base!='http://127.0.0.1:18741':raise ValueError('fixed local transport required')
        self.readiness=ReadinessDiagnostic(Path(journal).parent);self.base=base;self.path=Path(journal);self.trace_path=self.path.parent/'inbox_verifier_trace.jsonl';self.http=http;self.pending=None
        if self.path.exists():
            self.pending=unique_json(self.path.read_text(encoding='utf-8'))
            if self.pending is not None:
                if not isinstance(self.pending,dict) or set(self.pending)!={'delivery','outcome'}:raise ValueError('corrupt recovery journal')
                d=self.pending['delivery']
                if not isinstance(d,dict) or set(d) not in ({'cmd','delivery_id','text','text_sha256','claim_token','attempt_count'},{'cmd','delivery_id','text','text_sha256','claim_token','attempt_count','authorization'}):raise ValueError('corrupt journal delivery')
                if validate_text(d['delivery_id'],d['text'])!=d['text'] or sha256_text(d['text'])!=d['text_sha256']:raise ValueError('corrupt journal hash')
                try:held=load_binding(self.path.parent)['delivery_policy']=='HOLD'
                except (OSError,ValueError):held=True
                if 'authorization' in d:
                    self.authorized_pending()
                    held=False
                if self.pending['outcome'] is None and not held:self.set_outcome({'state':'NEEDS_REVIEW','error':'native host restarted with unknown Send outcome'})
    def authorized_pending(self):
        if not self.pending or 'authorization' not in self.pending['delivery']:return False
        delivery=self.pending['delivery']
        verify_envelope(delivery['authorization'],delivery,public_binding(load_binding(self.path.parent)),time.time(),allow_expired=True,runtime=self.path.parent)
        if delivery['attempt_count']!=1:raise ValueError('exact-one never retries')
        return True
    def set_outcome(self,outcome):
        pending={'delivery':self.pending['delivery'],'outcome':outcome}
        journal_write(self.path,pending);self.pending=pending
        if outcome.get('state')=='NEEDS_REVIEW':
            trace_event(self.trace_path,{'event':'native_outcome','delivery_id':pending['delivery']['delivery_id'],'state':'NEEDS_REVIEW','reason':str(outcome.get('error',''))[:256],'ts_ms':int(time.time()*1000)})
    def recover_ack(self):
        try:
            if load_binding(self.path.parent)['delivery_policy']=='HOLD' and not self.authorized_pending():return {'cmd':'idle','readiness_hold':True,'reason':'historical_ACK_held_across_rebind'}
        except (OSError,ValueError):return {'cmd':'error','error':'binding unknown; no ACK'}
        if self.pending is None:return {'cmd':'idle'}
        outcome=self.pending['outcome']
        if outcome is None:return {'cmd':'error','error':'delivery outstanding; no additional claim'}
        d=self.pending['delivery'];ack={'delivery_id':d['delivery_id'],'claim_token':d['claim_token']}|outcome
        if self.authorized_pending():ack['authorization_id']=d['authorization']['authorization_id']
        try:
            status,body=self.http(self.base,'/local/inbox/ack',ack)
            if status!=200 or not body.get('ok'):raise ValueError('durable ACK rejected')
        except Exception:
            trace_event(self.trace_path,{'event':'ack_pending','delivery_id':d['delivery_id'],'ts_ms':int(time.time()*1000)})
            return {'cmd':'ack_pending','delivery_id':d['delivery_id'],'error':'durable ACK pending; no resend'}
        trace_event(self.trace_path,{'event':'ack_committed','delivery_id':d['delivery_id'],'state':body['state'],'ts_ms':int(time.time()*1000)})
        # If clearing fails, a duplicate idempotent ACK after restart is safe.
        journal_write(self.path,None);self.pending=None
        return {'cmd':'acked','delivery_id':d['delivery_id'],'state':body['state']}
    def handle(self,msg):
        try:binding=load_binding(self.path.parent)
        except (OSError,ValueError,KeyError,TypeError):return {'cmd':'error','error':'production recipient binding unavailable; HOLD; no claim or ACK'}
        if msg=={'cmd':'binding'} or msg=={'cmd':'poll'}:
            return {'cmd':'binding_config','binding':public_binding(binding),'future_lane':lane_public(future_config(self.path.parent)) if future_config(self.path.parent) else None}
        if msg.get('cmd')=='readiness_result':return self.readiness.accept(msg)
        if msg.get('cmd')=='verifier_trace':
            trace_event(self.trace_path,msg.get('event'))
            return {'cmd':'trace_recorded'}

        if msg.get('cmd')=='send_permit':
            if not self.authorized_pending() or self.pending['outcome'] is not None:return {'cmd':'permit_result','ok':False}
            delivery=self.pending['delivery']
            if msg!={'cmd':'send_permit','delivery_id':delivery['delivery_id'],'authorization_id':delivery['authorization']['authorization_id']}:return {'cmd':'permit_result','ok':False}
            try:
                verify_envelope(delivery['authorization'],delivery,public_binding(binding),time.time(),runtime=self.path.parent)
                payload={key:delivery[key] for key in ('delivery_id','text_sha256','claim_token')}
                payload.update(authorization_id=msg['authorization_id'],binding_identity=binding['identity'])
                status,body=self.http(self.base,'/local/inbox/exact-one/send-permit',payload)
                return {'cmd':'permit_result',**body} if status==200 else {'cmd':'permit_result','ok':False}
            except Exception:return {'cmd':'permit_result','ok':False}
        if msg=={'cmd':'poll','binding_identity':binding['identity']}:
            if self.authorized_pending():return self.recover_ack()
            if self.pending is not None:return {'cmd':'idle','readiness_hold':True}
            from inbox_binding import status as probe_status,atomic
            if future_config(self.path.parent):
                snapshot=probe_status(self.path.parent)
                if not snapshot['no_send_ready'] or snapshot['readiness']['content'].get('future_build')!=FUTURE_BUILD or snapshot['readiness']['content'].get('future_lane_seal')!=future_config(self.path.parent)['seal']:
                    # An owner no-send provenance probe must reach the content
                    # script once. After its result is recorded normal freshness
                    # probes resume, so this cannot strand routine delivery.
                    owner_probe={};recorded={}
                    try:owner_probe=unique_json(self.readiness.request.read_text(encoding='utf-8'))
                    except (OSError,ValueError):pass
                    try:recorded=unique_json(self.readiness.result.read_text(encoding='utf-8'))
                    except (OSError,ValueError):pass
                    pending_probe=owner_probe.get('binding_identity')==binding['identity'] and bool(owner_probe.get('diagnostic_targets')) and owner_probe.get('probe_id')!=recorded.get('probe_id')
                    if not pending_probe:atomic(self.readiness.request,{'probe_id':uuid.uuid4().hex,'binding_identity':binding['identity']})
            probe=self.readiness.poll()
            if probe.get('cmd')=='readiness_probe':return probe
            from inbox_binding import status as binding_status
            current=binding_status(self.path.parent)
            if not current['no_send_ready'] or current['readiness']['content'].get('one_build')!=ONE_BUILD:return probe
            try:status,body=self.http(self.base,'/local/inbox/next')
            except Exception:return {'cmd':'idle','bridge_unreachable':True}
            if status==204:return {'cmd':'idle','readiness_hold':True}
            if status!=200 or not isinstance(body,dict) or body.get('ok') is not True:raise ValueError('invalid exact claim response')
            delivery={key:value for key,value in body.items() if key!='ok'}
            verify_envelope(delivery.get('authorization'),delivery,public_binding(binding),time.time(),runtime=self.path.parent)
            if delivery.get('cmd')!='delivery' or delivery.get('attempt_count')!=1 or validate_text(delivery['delivery_id'],delivery['text'])!=delivery['text'] or sha256_text(delivery['text'])!=delivery['text_sha256']:raise ValueError('invalid exact claim')
            journal_write(self.path,{'delivery':delivery,'outcome':None});self.pending={'delivery':delivery,'outcome':None}
            return delivery
        if msg.get('cmd')=='result' and self.authorized_pending():
            delivery=self.pending['delivery']
            allowed={'cmd','delivery_id','state','error','pre_send','observed_sha256','send_count','new_user_turns','composer_empty','user_turn_uuid','verification_method','composer_sha256'}
            if self.pending['outcome'] is not None or msg.get('delivery_id')!=delivery['delivery_id'] or not set(msg)<=allowed or msg.get('state') not in ('DELIVERED','FAILED_RETRYABLE','FAILED_PERMANENT','NEEDS_REVIEW'):raise ValueError('invalid exact outcome')
            self.set_outcome({key:value for key,value in msg.items() if key not in ('cmd','delivery_id')})
            return self.recover_ack()
        if binding['delivery_policy']=='HOLD':return {'cmd':'idle','readiness_hold':True,'binding_identity':binding['identity'],'reason':'recipient_rebind_requires_separate_delivery_authorization'}

        if msg=={'cmd':'poll'}:
            if self.pending is not None:return self.recover_ack()
            probe=self.readiness.poll()
            if probe is not None:return probe
            try:status,body=self.http(self.base,'/local/inbox/next')
            except Exception:return {'cmd':'idle','bridge_unreachable':True}
            if status==204:return {'cmd':'idle'}
            if status!=200 or not isinstance(body,dict) or not body.get('ok'):raise ValueError('invalid claim response')
            d=delivery_message(body)
            if validate_text(d['delivery_id'],d['text'])!=d['text'] or sha256_text(d['text'])!=d['text_sha256']:raise ValueError('invalid claim hash')
            journal_write(self.path,{'delivery':d,'outcome':None});self.pending={'delivery':d,'outcome':None}
            return d
        if msg.get('cmd')=='result':
            if not self.pending or self.pending['outcome'] is not None or msg.get('delivery_id')!=self.pending['delivery']['delivery_id']:
                return {'cmd':'error','error':'unexpected outcome'}
            allowed={'cmd','delivery_id','state','error','pre_send','observed_sha256','send_count','new_user_turns','composer_empty'}
            if not set(msg)<=allowed or msg.get('state') not in ('DELIVERED','FAILED_RETRYABLE','FAILED_PERMANENT','NEEDS_REVIEW'):
                raise ValueError('invalid outcome schema')
            if msg.get('state')=='FAILED_RETRYABLE' and msg.get('pre_send') is not True:raise ValueError('unproven retry')
            outcome={k:v for k,v in msg.items() if k not in ('cmd','delivery_id')}
            if outcome['state']!='NEEDS_REVIEW':
                trace_event(self.trace_path,{'event':'native_outcome','delivery_id':msg['delivery_id'],'state':outcome['state'],'ts_ms':int(time.time()*1000)})
            self.set_outcome(outcome)
            return self.recover_ack()
        return {'cmd':'error','error':'only poll and delivery outcome are supported'}
    def disconnect(self):
        try:
            if load_binding(self.path.parent)['delivery_policy']=='HOLD' and not self.authorized_pending():return
        except (OSError,ValueError):return
        if self.pending and self.pending['outcome'] is None:
            self.set_outcome({'state':'NEEDS_REVIEW','error':'native port closed; Send outcome unknown'})
        if self.pending:self.recover_ack()

def main():
    if os.name=='nt':
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(),os.O_BINARY);msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)
    cfg=unique_json((HERE/'config.json').read_text(encoding='utf-8-sig'))
    if cfg!={'local_port':18741}:raise ValueError('invalid native configuration')
    journal=HERE.parents[1]/'.runtime'/'inbox_native_recovery.json'
    journal.parent.mkdir(parents=True,exist_ok=True)
    lock=(journal.with_suffix('.lock')).open('a+b');lock.seek(0)
    if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    transport=Transport('http://127.0.0.1:18741',journal)
    trace_event(transport.trace_path,{'event':'native_retention_ready','build':INCIDENT_RETENTION_BUILD,'ts_ms':int(time.time()*1000)})
    try:
        while True:
            msg=read_message(sys.stdin.buffer)
            if msg is None:break
            write_message(sys.stdout.buffer,transport.handle(msg))
    finally:
        transport.disconnect();lock.close()
if __name__=='__main__':main()
