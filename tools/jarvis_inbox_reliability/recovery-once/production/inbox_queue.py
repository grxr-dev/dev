"""Durable title-independent inbox; no browser or relay credentials here.
Only an explicit pre_send outcome is retryable. Uncertainty is terminal/manual.
The managed bridge instance lock owns this file; all in-process access is locked.
"""
import hashlib
import copy
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from inbox_wire import validate_text, sha256_text, unique_json
QUEUED='QUEUED'; DELIVERING='DELIVERING'; DELIVERED='DELIVERED'
FAILED_RETRYABLE='FAILED_RETRYABLE'; FAILED_PERMANENT='FAILED_PERMANENT'; NEEDS_REVIEW='NEEDS_REVIEW'
VALID_STATES={QUEUED,DELIVERING,DELIVERED,FAILED_RETRYABLE,FAILED_PERMANENT,NEEDS_REVIEW}
TERMINAL_STATES={DELIVERED,FAILED_PERMANENT,NEEDS_REVIEW}
MAX_ATTEMPTS=3
LEASE_SECONDS=300
_KEEP=object()
class Conflict(ValueError): pass

class InboxQueue:
    def __init__(self,path,clock=time.time):
        self.path=Path(path); self.clock=clock; self.lock=threading.RLock(); self._entries={}; self._recovery=None; self._recovery_check=None
        if self.path.exists():
            data=unique_json(self.path.read_text(encoding='utf-8-sig'))
            if not isinstance(data,dict) or set(data) not in ({'version','entries'},{'version','entries','recovery_once'}) or data['version']!=2 or not isinstance(data['entries'],dict):
                raise ValueError('malformed inbox queue; preserve for manual review')
            self._recovery=data.get('recovery_once')
            if self._recovery is not None:self._validate_recovery(self._recovery,data['entries'])
            for did,e in data['entries'].items():
                self._validate_entry(did,e)
            self._entries=data['entries']
            # Crash recovery is never a resend, even if the last process died before Send.
            changed=copy.deepcopy(self._entries)
            for e in changed.values():
                if e['state']==DELIVERING:
                    e['state']=NEEDS_REVIEW; e['last_error']='bridge restarted with unresolved delivery; never auto-resend'
            recovery=copy.deepcopy(self._recovery)
            if recovery and recovery['status'] in ('PREPARED','ARMED','CLAIMED'):
                e=changed[recovery['delivery_id']]
                if recovery['status'] in ('PREPARED','ARMED'):
                    e['state']=FAILED_PERMANENT;e['last_error']='administrative recovery interrupted before claim; no auto-resend'
                recovery['status']='CANCELLED' if e['state']!=NEEDS_REVIEW else 'NEEDS_REVIEW'
                recovery['events'].append({'event':'startup_interrupted','at':self.clock(),'state':e['state']})
            if changed!=self._entries or recovery!=self._recovery:self._commit(changed,recovery)
    def _validate_entry(self,did,e):
        required={'delivery_id','text','text_sha256','created_at','state','attempt_count','last_attempt_at',
                  'delivered_at','last_error','next_attempt_at','claim_token','outcome'}
        if not isinstance(e,dict) or set(e)!=required:raise ValueError('malformed inbox entry')
        text=validate_text(did,e['text'])
        if e['delivery_id']!=did or text!=e['text'] or sha256_text(text)!=e['text_sha256'] or e['state'] not in VALID_STATES:
            raise ValueError('corrupt inbox identity/hash/state')
        if type(e['attempt_count']) is not int or not 0<=e['attempt_count']<=(MAX_ATTEMPTS+1 if self._recovery and did==self._recovery['delivery_id'] else MAX_ATTEMPTS):raise ValueError('corrupt attempt count')
        for k in ('created_at','last_attempt_at','delivered_at','next_attempt_at'):
            v=e[k]
            if v is not None and (type(v) not in (int,float) or not 0<=v<1e12):raise ValueError('invalid timestamp')
        if e['created_at'] is None:raise ValueError('missing creation time')
        if e['last_error'] is not None and (not isinstance(e['last_error'],str) or len(e['last_error'])>2000):raise ValueError('invalid error')
        if e['claim_token'] is not None and (not isinstance(e['claim_token'],str) or len(e['claim_token'])!=64):raise ValueError('invalid claim token')
        if e['attempt_count'] and (e['claim_token'] is None or e['last_attempt_at'] is None):raise ValueError('incomplete claim')
        if e['state']==FAILED_RETRYABLE and (e['next_attempt_at'] is None or not isinstance(e['outcome'],dict) or e['outcome'].get('pre_send') is not True):raise ValueError('unproven retry')
        if e['state']==DELIVERED and (not isinstance(e['outcome'],dict) or e['outcome'].get('observed_sha256')!=e['text_sha256'] or e['delivered_at'] is None):raise ValueError('unproven delivery')
    def _validate_recovery(self,r,entries):
        from inbox_recovery import TARGET, TEXT_SHA256
        keys={'delivery_id','authorization_id','authorized_at','expected_fingerprint','entry_before','readiness','status','events','armed_entries_sha256','prior_evidence'}
        if not isinstance(r,dict) or set(r)!=keys or r['delivery_id']!=TARGET or TARGET not in entries:raise ValueError('corrupt recovery identity')
        if r['status'] not in ('PREPARED','ARMED','CLAIMED','FINISHED','CANCELLED','NEEDS_REVIEW'):raise ValueError('corrupt recovery status')
        b=r['entry_before'];e=entries[TARGET]
        if not isinstance(b,dict) or b.get('delivery_id')!=TARGET or b.get('state')!=FAILED_PERMANENT or b.get('attempt_count')!=MAX_ATTEMPTS or b.get('text_sha256')!=TEXT_SHA256 or e['text']!=b['text'] or sha256_text(e['text'])!=TEXT_SHA256:raise ValueError('corrupt recovery history')
        self._validate_entry(TARGET,b)
        status=r['status']
        if status in ('PREPARED','ARMED'):
            wanted=copy.deepcopy(b);wanted.update(state=QUEUED,last_error=None,next_attempt_at=None)
            if e!=wanted:raise ValueError('armed recovery entry changed unexpectedly')
        elif status=='CLAIMED':
            if e['state']!=DELIVERING or e['attempt_count']!=MAX_ATTEMPTS+1 or e['outcome'] is not None:raise ValueError('corrupt claimed recovery state')
        elif status=='FINISHED':
            if e['state'] not in TERMINAL_STATES or e['attempt_count']!=MAX_ATTEMPTS+1:raise ValueError('corrupt finished recovery state')
        elif status=='CANCELLED':
            if e['state']!=FAILED_PERMANENT or e['attempt_count']!=MAX_ATTEMPTS:raise ValueError('corrupt cancelled recovery state')
        elif status=='NEEDS_REVIEW':
            if e['state']!=NEEDS_REVIEW or e['attempt_count']!=MAX_ATTEMPTS+1:raise ValueError('corrupt review recovery state')
        if not isinstance(r['authorization_id'],str) or len(r['authorization_id'])!=32 or not isinstance(r['expected_fingerprint'],str) or len(r['expected_fingerprint'])!=64:raise ValueError('corrupt recovery authorization')
        if not isinstance(r['readiness'],dict) or not isinstance(r['events'],list) or not 1<=len(r['events'])<=16:raise ValueError('corrupt recovery audit')
    def fingerprint(self):
        with self.lock:return hashlib.sha256(json.dumps({'entries':self._entries,'recovery_once':self._recovery},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
    def recover_once(self,did,expected_fingerprint,readiness,release_hold,evidence=None):
        from inbox_recovery import TARGET,TEXT_SHA256
        with self.lock:
            if did!=TARGET:raise Conflict('recovery target mismatch')
            if self._recovery is not None:raise Conflict('one-use recovery authorization already exists')
            if expected_fingerprint!=self.fingerprint():raise Conflict('stale queue fingerprint')
            old=self._entries.get(did)
            if not old or old['state']!=FAILED_PERMANENT or old['attempt_count']!=MAX_ATTEMPTS or old['text_sha256']!=TEXT_SHA256 or sha256_text(old['text'])!=TEXT_SHA256:raise Conflict('unexpected terminal identity/state')
            if old['last_error']!='pre-Send retry limit exhausted' or not isinstance(old['outcome'],dict) or old['outcome'].get('state')!=FAILED_RETRYABLE or old['outcome'].get('pre_send') is not True:raise Conflict('not a proven pre-Send exhausted failure')
            if any(e['state'] in (QUEUED,FAILED_RETRYABLE,DELIVERING) for e in self._entries.values()):raise Conflict('other delivery or eligible work exists')
            ready=readiness()
            recovery={'delivery_id':did,'authorization_id':secrets.token_hex(16),'authorized_at':self.clock(),'expected_fingerprint':expected_fingerprint,'entry_before':copy.deepcopy(old),'readiness':ready,'status':'PREPARED','prior_evidence':evidence() if evidence else {},'events':[{'event':'authorized','at':self.clock(),'previous_attempt_count':old['attempt_count'],'additional_attempts':1}]}
            entries=copy.deepcopy(self._entries);entries[did].update(state=QUEUED,last_error=None,next_attempt_at=None)
            recovery['armed_entries_sha256']=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            self._commit(entries,recovery)
            try:
                release_hold(ready)
                armed=copy.deepcopy(recovery);armed['status']='ARMED';armed['events'].append({'event':'armed','at':self.clock()})
                self._commit(entries,armed)
            except Exception:
                cancelled=copy.deepcopy(recovery);cancelled['status']='CANCELLED';cancelled['events'].append({'event':'arm_failed','at':self.clock()})
                restored=copy.deepcopy(self._entries);restored[did]=copy.deepcopy(old)
                self._commit(restored,cancelled)
                raise
            return {'authorization_id':armed['authorization_id'],'delivery_id':did,'state':QUEUED,'previous_attempt_count':old['attempt_count'],'max_total_attempts':MAX_ATTEMPTS+1}
    def _commit(self,entries,recovery=_KEEP):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.path.parent,prefix='.inbox.',suffix='.tmp')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                value={'version':2,'entries':entries};r=self._recovery if recovery is _KEEP else recovery
                if r is not None:value['recovery_once']=r
                json.dump(value,f,ensure_ascii=False,allow_nan=False,indent=1)
                f.flush(); os.fsync(f.fileno())
            os.replace(tmp,self.path)
            self._entries=entries  # publish only after durable write succeeds
            self._recovery=r
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    def enqueue(self,did,text):
        text=validate_text(did,text)
        with self.lock:
            old=self._entries.get(did)
            if old:
                if old['text']!=text or old['text_sha256']!=sha256_text(text):raise Conflict('delivery_id has different canonical text')
                return copy.deepcopy(old),False
            e={'delivery_id':did,'text':text,'text_sha256':sha256_text(text),'created_at':self.clock(),
               'state':QUEUED,'attempt_count':0,'last_attempt_at':None,'delivered_at':None,'last_error':None,
               'next_attempt_at':None,'claim_token':None,'outcome':None}
            entries=copy.deepcopy(self._entries); entries[did]=e; self._commit(entries)
            return copy.deepcopy(e),True
    def reap_stale(self):
        with self.lock:
            entries=copy.deepcopy(self._entries);changed=False
            for e in entries.values():
                if e['state']==DELIVERING and self.clock()-e['last_attempt_at']>=LEASE_SECONDS:
                    e['state']=NEEDS_REVIEW;e['last_error']='delivery lease expired; Send outcome unknown';changed=True
            if changed:
                recovery=copy.deepcopy(self._recovery)
                if recovery and recovery['status']=='CLAIMED' and entries[recovery['delivery_id']]['state']==NEEDS_REVIEW:
                    recovery['status']='NEEDS_REVIEW';recovery['events'].append({'event':'lease_expired','at':self.clock(),'state':NEEDS_REVIEW})
                self._commit(entries,recovery)
    def get(self,did):
        with self.lock:
            self.reap_stale()
            return copy.deepcopy(self._entries.get(did))
    def claim_next(self):
        with self.lock:
            entries=copy.deepcopy(self._entries); now=self.clock(); changed=False
            for e in entries.values():
                if e['state']==DELIVERING and now-e['last_attempt_at']>=LEASE_SECONDS:
                    e['state']=NEEDS_REVIEW;e['last_error']='delivery lease expired; send outcome unknown'; changed=True
            if any(e['state']==DELIVERING for e in entries.values()):return None
            recovery=copy.deepcopy(self._recovery)
            if recovery and recovery['status']=='PREPARED':return None
            eligible=[e for e in entries.values() if e['state']==QUEUED or
                      (e['state']==FAILED_RETRYABLE and e['next_attempt_at']<=now and e['attempt_count']<MAX_ATTEMPTS)]
            if not eligible:
                if changed:self._commit(entries)
                return None
            if recovery and recovery['status']=='ARMED':
                if not self._recovery_check:raise Conflict('recovery readiness validator unavailable')
                if hashlib.sha256(json.dumps(self._entries,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()!=recovery['armed_entries_sha256']:raise Conflict('queue changed after recovery authorization')
                self._recovery_check(recovery['readiness']['probe_id'])
                eligible=[e for e in eligible if e['delivery_id']==recovery['delivery_id'] and e['attempt_count']==MAX_ATTEMPTS]
                if len(eligible)!=1:raise Conflict('armed recovery state changed')
            else:eligible=[e for e in eligible if e['attempt_count']<MAX_ATTEMPTS]
            if not eligible:return None
            e=min(eligible,key=lambda e:(e['created_at'],e['delivery_id']))
            e.update(state=DELIVERING,attempt_count=e['attempt_count']+1,last_attempt_at=now,
                     next_attempt_at=None,claim_token=secrets.token_hex(32),outcome=None)
            if recovery and recovery['status']=='ARMED':
                recovery['status']='CLAIMED';recovery['events'].append({'event':'claimed','at':now,'attempt_count':e['attempt_count'],'claim_token_sha256':hashlib.sha256(e['claim_token'].encode()).hexdigest()})
            self._commit(entries,recovery);return copy.deepcopy(e)
    def ack(self,did,state,error=None,*,claim_token=None,pre_send=False,observed_sha256=None,
            send_count=None,new_user_turns=None,composer_empty=None):
        with self.lock:
            old=self._entries.get(did)
            if old is None:return None
            if not claim_token or claim_token!=old['claim_token']:raise Conflict('claim token mismatch')
            if state not in (DELIVERED,FAILED_RETRYABLE,FAILED_PERMANENT,NEEDS_REVIEW):raise ValueError('invalid outcome')
            if error is not None and (not isinstance(error,str) or len(error)>2000):raise ValueError('invalid error')
            if type(pre_send) is not bool:raise ValueError('invalid pre_send')
            if state==FAILED_RETRYABLE and pre_send is not True:raise ValueError('retry requires proven pre-Send failure')
            if state==DELIVERED and (observed_sha256!=old['text_sha256'] or type(send_count) is not int or send_count!=1 or type(new_user_turns) is not int or new_user_turns!=1 or composer_empty is not True):
                raise ValueError('delivery requires exact hash and one-Send/one-new-user-turn proof')
            outcome={'state':state,'error':error,'pre_send':pre_send,'observed_sha256':observed_sha256,
                     'send_count':send_count,'new_user_turns':new_user_turns,'composer_empty':composer_empty}
            if old['outcome']==outcome:return copy.deepcopy(old) # idempotent ACK, including exhausted retry
            if old['state'] not in (DELIVERING,NEEDS_REVIEW) or (old['state']==NEEDS_REVIEW and old['outcome'] is not None):
                raise Conflict('refusing to change completed outcome')
            # A late matching durable outcome can resolve crash/lease review; never re-execute it.
            entries=copy.deepcopy(self._entries);e=entries[did];e.update(state=state,last_error=error,outcome=outcome)
            if state==DELIVERED:e.update(delivered_at=self.clock(),last_error=None)
            if state==FAILED_RETRYABLE:
                if e['attempt_count']>=MAX_ATTEMPTS:e.update(state=FAILED_PERMANENT,last_error='pre-Send retry limit exhausted')
                else:e['next_attempt_at']=self.clock()+30*(2**(e['attempt_count']-1))
            recovery=copy.deepcopy(self._recovery)
            if recovery and recovery['delivery_id']==did and recovery['status'] in ('CLAIMED','NEEDS_REVIEW'):
                recovery['status']='FINISHED';recovery['events'].append({'event':'outcome','at':self.clock(),'attempt_count':e['attempt_count'],'state':e['state'],'outcome':copy.deepcopy(outcome)})
            self._commit(entries,recovery);return copy.deepcopy(e)
    def counts(self):
        with self.lock:
            self.reap_stale()
            return {s:sum(e['state']==s for e in self._entries.values()) for s in sorted(VALID_STATES)}
