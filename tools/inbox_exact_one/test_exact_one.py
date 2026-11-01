"""Isolated stores and real queue/API/native contracts. No production HTTP or browser."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
import threading
import urllib.request
import urllib.error
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
STAGE=HERE/'production'
LIVE=HERE.parents[2]/'bridge'
sys.path[:0]=[str(STAGE),str(STAGE/'inbox-v1/native-host'),str(LIVE)]
import inbox_binding as binding
import inbox_one as one
from inbox_queue import InboxQueue,Conflict
from inbox_api import InboxApi
from inbox_recovery import RecoveryAdmin
from readiness_diagnostic import ReadinessDiagnostic
spec=importlib.util.spec_from_file_location('exact_native',STAGE/'inbox-v1/native-host/jarvis_inbox_host.py')
host=importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
TEXT='[CODEX → CHATGPT]\n\n[CODEX → CHATGPT] RELAY_SYNTHETIC_A\ntest_id: middleman-smoke-20261101-71c4fb280c\nsenior_nonce: CHALLENGE-151b6c2d2b379fdd4253c074\ncodex_reply: RECEIVED_SENIOR_CHALLENGE'
UUID='12345678-1234-1234-1234-123456789abc'


class ExactOneTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.runtime=Path(self.temp.name)
        self.now=time.time()
        (self.runtime/'inbox_native_recovery.json').write_text('null')
        (self.runtime/'inbox_readiness_request.json').write_text(json.dumps({'probe_id':'a'*32}))
        self.queue=InboxQueue(self.runtime/'inbox_queue.json',clock=lambda:self.now)
        self.queue.enqueue('historical-oldest','historical never eligible')
        self.queue.enqueue('historical-other','other history')
        self.queue.enqueue(one.TARGET,TEXT)
        self.value=binding.change(self.runtime,one.DESTINATION,binding.LEGACY,'LEGACY_UNCONFIGURED')[0]
        self.api=InboxApi(self.queue)
        self.admin=RecoveryAdmin(self.queue)
        self.native=host.Transport('http://127.0.0.1:18741',self.runtime/'inbox_native_recovery.json',self.http)
        self.before=copy.deepcopy({key:value for key,value in self.queue._entries.items() if key!=one.TARGET})
        self.binding_bytes=(self.runtime/'inbox_binding.json').read_bytes()
        self.hold_bytes=(self.runtime/'inbox_readiness_request.json').read_bytes()
        self.calls=[]
        self.probe()

    def tearDown(self):
        self.assertEqual(self.before,{key:value for key,value in self.queue._entries.items() if key!=one.TARGET})
        self.assertEqual(self.binding_bytes,(self.runtime/'inbox_binding.json').read_bytes())
        self.assertEqual(self.hold_bytes,(self.runtime/'inbox_readiness_request.json').read_bytes())
        self.temp.cleanup()

    def probe(self):
        nonce='b'*32
        binding.atomic(self.runtime/'inbox_binding_probe.json',{'probe_id':nonce,'binding_identity':self.value['identity']})
        diagnostic=self.native.readiness
        self.assertEqual(diagnostic.poll()['cmd'],'readiness_probe')
        result={'cmd':'readiness_result','probe_id':nonce,'build':binding.BUILD,'one_build':one.BUILD,
            'binding_identity':self.value['identity'],'match_count':1,'matches':[{'id':1,'windowId':2,
            'url':'https://chatgpt.com/c/'+one.DESTINATION,'hidden':False,'discarded':False,'incognito':False}],
            'truncated':False,'ready':True,'reason':'ready','content':{'binding_identity':self.value['identity'],
            'one_build':one.BUILD,'reason':'ready','reachable':True,'bound':True,'composer_present':True,
            'composer_empty':True,'generation_active':False,'busy':False,'ready':True}}
        self.assertEqual(diagnostic.accept(result)['cmd'],'readiness_recorded')
        self.proof=result

    def http(self,base,path,payload=None):
        self.assertEqual(base,'http://127.0.0.1:18741')
        self.calls.append(path)
        if path=='/local/inbox/next':return self.api.local_next()
        if path=='/local/inbox/ack':return self.api.local_ack(payload)
        if path=='/local/inbox/exact-one/send-permit':return 200,one.send_permit(self.queue,payload)
        self.fail('unsupported request')

    def arm_body(self):
        return {'delivery_id':one.TARGET,'text_sha256':one.TEXT_SHA256,'binding_identity':self.value['identity'],
                'queue_fingerprint':self.queue.fingerprint(),'expires_in':120}

    def arm(self):return one.arm(self.queue,self.arm_body())

    def poll(self):return self.native.handle({'cmd':'poll','binding_identity':self.value['identity']})

    def permit(self,delivery):
        return self.native.handle({'cmd':'send_permit','delivery_id':delivery['delivery_id'],
                                  'authorization_id':delivery['authorization']['authorization_id']})

    def outcome(self,delivery,**changes):
        result={'cmd':'result','delivery_id':delivery['delivery_id'],'state':'DELIVERED',
            'observed_sha256':one.TEXT_SHA256,'send_count':1,'new_user_turns':1,'composer_empty':True,'user_turn_uuid':UUID}
        result.update(changes)
        return self.native.handle(result)

    def test_exact_contract_end_to_end_no_historical_delivery(self):
        self.assertEqual(hashlib.sha256(TEXT.encode()).hexdigest(),one.TEXT_SHA256)
        self.assertIsNone(self.queue.claim_next())
        self.arm()
        delivery=self.poll()
        self.assertEqual(delivery['delivery_id'],one.TARGET)
        self.assertEqual(delivery['attempt_count'],1)
        self.assertTrue(self.permit(delivery)['ok'])
        self.assertEqual(self.outcome(delivery)['state'],'DELIVERED')
        self.assertEqual(self.queue._one['state'],'FINISHED')
        self.assertEqual(self.queue._entries[one.TARGET]['outcome']['user_turn_uuid'],UUID)
        self.assertIsNone(self.queue.claim_next())
        self.assertEqual(self.calls,['/local/inbox/next','/local/inbox/exact-one/send-permit','/local/inbox/ack'])

    def test_no_grant_holds_all_ids_on_restart(self):
        for count in range(3):
            self.assertIsNone(self.queue.claim_next())
            self.queue=InboxQueue(self.queue.path,clock=lambda:self.now)
            self.admin=RecoveryAdmin(self.queue)
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_wrong_id_hash_binding_or_fingerprint_never_arm(self):
        for key,bad in [('delivery_id','historical-oldest'),('text_sha256','0'*64),('binding_identity','0'*64),('queue_fingerprint','0'*64),('expires_in',301),('expires_in',True)]:
            body=self.arm_body();body[key]=bad
            with self.subTest(key=key),self.assertRaises(Conflict):one.arm(self.queue,body)
            self.assertIsNone(self.queue._one)
            self.assertIsNone(self.queue.claim_next())

    def test_arbitrary_flags_never_authorize(self):
        body=self.arm_body();body['synthetic']=True
        with self.assertRaises(Conflict):one.arm(self.queue,body)
        self.assertIsNone(self.queue.claim_next())

    def test_duplicate_grant_and_claim(self):
        self.arm()
        with self.assertRaises(Conflict):self.arm()
        self.assertIsNotNone(self.queue.claim_next())
        self.assertIsNone(self.queue.claim_next())

    def test_expiry_no_rearm(self):
        self.arm();self.now+=121
        self.assertIsNone(self.queue.claim_next())
        self.assertEqual(self.queue._one['state'],'EXPIRED')
        with self.assertRaises(Conflict):self.arm()
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_revoke_keeps_entry_unattempted(self):
        self.arm();one.revoke(self.queue,self.queue._one['authorization_id'])
        self.assertIsNone(self.queue.claim_next())
        self.assertEqual(self.queue._one['state'],'REVOKED')
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_revoke_after_claim_refused_not_retried(self):
        self.arm();self.queue.claim_next()
        with self.assertRaises(Conflict):one.revoke(self.queue,self.queue._one['authorization_id'])
        self.assertIsNone(self.queue.claim_next())

    def test_missing_or_stale_readiness_and_old_loaded_content(self):
        result_path=self.runtime/'inbox_binding_readiness.json'
        result_path.unlink()
        with self.assertRaises(Conflict):self.arm()
        result=copy.deepcopy(self.proof);result.update(native_pid=1,observed_ms=self.now*1000-61000)
        binding.atomic(result_path,result)
        with self.assertRaises(Conflict):self.arm()
        result['observed_ms']=self.now*1000;result['content'].pop('one_build')
        binding.atomic(result_path,result)
        with self.assertRaises(Conflict):self.arm()

    def test_readiness_expires_between_arm_and_claim(self):
        self.arm();self.now+=61
        with self.assertRaises(Conflict):self.queue.claim_next()
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_changed_history_rejects_claim(self):
        self.arm();self.queue._entries['historical-oldest']['last_error']='unexpected'
        with self.assertRaises(Conflict):self.queue.claim_next()
        self.queue._entries['historical-oldest']['last_error']=None
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_malformed_grant_restart_fails_closed(self):
        self.arm();path=self.queue.path;value=json.loads(path.read_text());value['exact_one']['expires_at']+=1;path.write_text(json.dumps(value))
        with self.assertRaises(Conflict):InboxQueue(path)

    def test_crash_before_atomic_claim_commit(self):
        self.arm();before=self.queue.path.read_bytes()
        with patch('inbox_queue.os.replace',side_effect=OSError('crash')):
            with self.assertRaises(OSError):self.queue.claim_next()
        self.assertEqual(self.queue.path.read_bytes(),before)
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)
        restarted=InboxQueue(self.queue.path,clock=lambda:self.now);RecoveryAdmin(restarted)
        self.assertIsNotNone(restarted.claim_next())

    def test_crash_after_claim_before_native_journal_no_resend(self):
        self.arm();self.queue.claim_next()
        restarted=InboxQueue(self.queue.path,clock=lambda:self.now);RecoveryAdmin(restarted)
        self.assertEqual(restarted._entries[one.TARGET]['state'],'NEEDS_REVIEW')
        self.assertIsNone(restarted.claim_next())

    def test_duplicate_send_permit_refused(self):
        self.arm();delivery=self.poll()
        self.assertTrue(self.permit(delivery)['ok'])
        self.assertFalse(self.permit(delivery)['ok'])
        self.assertIsNone(self.queue.claim_next())

    def test_ack_without_send_permit_or_uuid_rejected(self):
        self.arm();delivery=self.poll()
        self.assertEqual(self.outcome(delivery)['cmd'],'ack_pending')
        self.assertEqual(self.queue._entries[one.TARGET]['state'],'DELIVERING')

    def test_wrong_new_uuid_and_payload_proof(self):
        self.arm();delivery=self.poll();self.permit(delivery)
        for changes in [{'user_turn_uuid':None},{'observed_sha256':'0'*64},{'send_count':2},{'composer_empty':False}]:
            payload={'delivery_id':one.TARGET,'state':'DELIVERED','claim_token':delivery['claim_token'],
                'authorization_id':delivery['authorization']['authorization_id'],'user_turn_uuid':UUID,
                'observed_sha256':one.TEXT_SHA256,'send_count':1,'new_user_turns':1,'composer_empty':True}|changes
            self.assertNotEqual(self.api.local_ack(payload)[0],200)

    def test_presend_failure_terminal_never_retry(self):
        self.arm();delivery=self.poll()
        self.assertEqual(self.outcome(delivery,state='FAILED_RETRYABLE',pre_send=True,error='no composer')['state'],'FAILED_PERMANENT')
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],1)
        self.assertIsNone(self.queue.claim_next())

    def test_disconnect_unknown_outcome_needs_review_no_send(self):
        self.arm();self.poll();self.native.disconnect()
        self.assertEqual(self.queue._entries[one.TARGET]['state'],'NEEDS_REVIEW')
        self.assertIsNone(self.queue.claim_next())

    def test_restart_native_after_send_intent_needs_review(self):
        self.arm();delivery=self.poll();self.permit(delivery)
        native=host.Transport('http://127.0.0.1:18741',self.native.path,self.http)
        self.assertEqual(native.recover_ack()['state'],'NEEDS_REVIEW')
        self.assertIsNone(self.queue.claim_next())

    def test_ack_commit_then_native_clear_crash_idempotent(self):
        self.arm();delivery=self.poll();self.permit(delivery)
        original=host.journal_write
        def fail_clear(path,value):
            if value is None:raise OSError('crash after ACK')
            original(path,value)
        with patch.object(host,'journal_write',side_effect=fail_clear):
            with self.assertRaises(OSError):self.outcome(delivery)
        self.assertEqual(self.queue._entries[one.TARGET]['state'],'DELIVERED')
        native=host.Transport('http://127.0.0.1:18741',self.native.path,self.http)
        self.assertEqual(native.recover_ack()['state'],'DELIVERED')
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],1)
        self.assertIsNone(self.queue.claim_next())

    def test_duplicate_ack_same_proof_idempotent(self):
        self.arm();delivery=self.poll();self.permit(delivery)
        self.outcome(delivery)
        old=self.queue.path.read_bytes()
        entry=self.queue._entries[one.TARGET]
        payload={'delivery_id':one.TARGET,'claim_token':entry['claim_token']}|entry['outcome']
        self.assertEqual(self.api.local_ack(payload)[0],200)
        self.assertEqual(self.queue.path.read_bytes(),old)

    def test_old_ack_and_legacy_poll_remain_held(self):
        self.arm()
        self.assertEqual(self.native.handle({'cmd':'poll'})['cmd'],'binding_config')
        self.assertTrue(self.native.handle({'cmd':'result','delivery_id':'historical-oldest'})['readiness_hold'])
        self.assertNotEqual(self.api.local_ack({'delivery_id':'historical-oldest','state':'NEEDS_REVIEW','claim_token':'a'*64})[0],200)
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_reconnect_after_claim_no_reforward(self):
        self.arm();self.poll()
        result=self.poll()
        self.assertNotEqual(result['cmd'],'delivery')
        self.assertEqual(self.calls.count('/local/inbox/next'),1)

    def test_wrong_native_envelope_rejects(self):
        self.arm();delivery=self.poll();current=binding.public(self.value)
        for field,bad in [('delivery_id','historical-oldest'),('text_sha256','0'*64),('authorization_id','bad'),('expires_at',self.now-1)]:
            value=copy.deepcopy(delivery['authorization']);value[field]=bad
            with self.subTest(field=field),self.assertRaises(Conflict):one.verify_envelope(value,delivery,current,self.now)
        value=copy.deepcopy(delivery['authorization']);value['binding']['epoch']='0'*32
        with self.assertRaises(Conflict):one.verify_envelope(value,delivery,current,self.now)

    def test_local_admin_route_authentication_and_fixed_transport(self):
        from inbox_local import LocalInboxServer
        server=LocalInboxServer(0,self.api)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base='http://127.0.0.1:'+str(server.server_port)
        def query(path,payload=None,**headers):
            request=urllib.request.Request(base+path,data=None if payload is None else json.dumps(payload).encode(),
                headers={'X-Jarvis-Local':'1','Content-Type':'application/json'}|headers)
            with opener.open(request,timeout=3) as response:return response.status,json.loads(response.read())
        try:
            self.assertEqual(query('/local/inbox/capabilities')[1]['exact_one_build'],one.BUILD)
            for extra in [{},{'X-Jarvis-Admin':'wrong'},{'X-Jarvis-Admin':server.recovery.token,'Origin':'https://chatgpt.com'}]:
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    query('/local/inbox/admin/exact-one',self.arm_body(),**extra)
                self.assertEqual(caught.exception.code,403)
                self.assertIsNone(self.queue._one)
            self.assertEqual(query('/local/inbox/admin/exact-one',self.arm_body(),**{'X-Jarvis-Admin':server.recovery.token})[1]['grant']['state'],'ARMED')
            claimed=query('/local/inbox/next')[1]
            self.assertEqual(claimed['delivery_id'],one.TARGET)
            permit={key:claimed[key] for key in ('delivery_id','text_sha256','claim_token')}
            permit.update(authorization_id=claimed['authorization']['authorization_id'],binding_identity=self.value['identity'])
            self.assertTrue(query('/local/inbox/exact-one/send-permit',permit)[1]['ok'])
            with self.assertRaises(urllib.error.HTTPError) as caught:query('/local/inbox/exact-one/send-permit',permit)
            self.assertEqual(caught.exception.code,409)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

    def test_pinned_component_change_fails_closed(self):
        with patch.dict(one.LOADED_SOURCES,{'inbox_queue.py':'0'*64}):
            with self.assertRaises(Conflict):self.arm()
            with self.assertRaises(Conflict):self.queue.claim_next()
        self.assertIsNone(self.queue._one)

    def test_stale_destination_generation_epoch_identity_rejects_claim(self):
        self.arm()
        original=copy.deepcopy(self.value)
        for field,bad in [('conversation_id',binding.LEGACY),('generation',2),('epoch','0'*32),('delivery_policy','SEND')]:
            changed=copy.deepcopy(original);changed[field]=bad
            changed['identity']=binding.digest({key:value for key,value in changed.items() if key!='identity'})
            binding.atomic(self.runtime/'inbox_binding.json',changed)
            try:
                with self.subTest(field=field),self.assertRaises(Conflict):self.queue.claim_next()
            finally:(self.runtime/'inbox_binding.json').write_bytes(self.binding_bytes)
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_claim_token_wrong_authorization_or_expiry_cannot_get_permit(self):
        self.arm();delivery=self.poll()
        body={key:delivery[key] for key in ('delivery_id','text_sha256','claim_token')}
        body.update(authorization_id=delivery['authorization']['authorization_id'],binding_identity=self.value['identity'])
        for key,bad in [('delivery_id','historical-oldest'),('text_sha256','0'*64),('claim_token','0'*64),('authorization_id','0'*32),('binding_identity','0'*64)]:
            with self.subTest(key=key),self.assertRaises(Conflict):one.send_permit(self.queue,body|{key:bad})
        self.now+=121
        with self.assertRaises(Conflict):one.send_permit(self.queue,body)
        self.assertIsNone(self.queue.claim_next())

    def test_expired_grant_can_ack_exact_known_send_but_never_send_again(self):
        self.arm();delivery=self.poll();self.permit(delivery)
        self.now+=121
        self.assertEqual(self.outcome(delivery)['state'],'DELIVERED')
        self.assertIsNone(self.queue.claim_next())

    def test_armed_restart_preserves_exact_exclusion(self):
        self.arm()
        restarted=InboxQueue(self.queue.path,clock=lambda:self.now);RecoveryAdmin(restarted)
        self.assertEqual(restarted.claim_next()['delivery_id'],one.TARGET)
        self.assertIsNone(restarted.claim_next())

    def test_pending_historical_native_journal_does_not_ack_or_allow_grant(self):
        binding.atomic(self.runtime/'inbox_native_recovery.json',{'unresolved':'old'})
        with self.assertRaises(Conflict):self.arm()
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)

    def test_native_journal_failure_after_claim_no_reforward(self):
        self.arm()
        with patch.object(host,'journal_write',side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):self.poll()
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],1)
        self.assertIsNone(self.queue.claim_next())

    def test_corrupt_partial_queue_detected_without_claim(self):
        for raw in ['{','{"version":2,"entries":{},"version":2}']:
            with self.subTest(raw=raw):
                path=self.runtime/'broken.json';path.write_text(raw)
                with self.assertRaises(ValueError):InboxQueue(path)

    def test_missing_binding_never_falls_back_to_oldest_queue_entry(self):
        path=self.runtime/'inbox_binding.json';path.unlink()
        try:
            with self.assertRaises(Conflict):self.api.local_next()
            self.assertNotEqual(self.api.local_ack({'delivery_id':'historical-oldest','state':'NEEDS_REVIEW','claim_token':'0'*64})[0],200)
        finally:path.write_bytes(self.binding_bytes)
        self.assertEqual(self.queue._entries[one.TARGET]['attempt_count'],0)


if __name__=='__main__':unittest.main(verbosity=2)
