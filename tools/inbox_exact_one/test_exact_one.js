'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const base=__dirname+'/production/inbox-v1/extension/';
const target='6ae5615a-0720-83ea-a43b-82386ce031e5',old='6acab580-d218-83ea-9598-0ff64dc33aa7';
const build='inbox-exact-one-20261101-01',extensionId='jarvis-inbox-v1@grxr.ca';
const binding={schema:'middleman-inbox-binding/1',build:'inbox-binding-20261101-01',conversation_id:target,generation:1,epoch:'b2108916e5fb44098859a58e0252a2ad',delivery_policy:'HOLD',identity:'2'.repeat(64)};
const text='[CODEX → CHATGPT]\n\n[CODEX → CHATGPT] RELAY_SYNTHETIC_A\ntest_id: middleman-smoke-20261101-71c4fb280c\nsenior_nonce: CHALLENGE-151b6c2d2b379fdd4253c074\ncodex_reply: RECEIVED_SENIOR_CHALLENGE';
const hash=crypto.createHash('sha256').update(text).digest('hex');
const delivery={cmd:'delivery',delivery_id:'middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878',text,text_sha256:hash,attempt_count:1,claim_token:'4'.repeat(64)};
delivery.authorization={schema:'inbox-exact-one/1',build,authorization_id:'3'.repeat(32),delivery_id:delivery.delivery_id,text_sha256:hash,binding,created_at:100,expires_at:220};
const uuid='12345678-1234-1234-1234-123456789abc';
let tests=0;
async function test(name,fn){await fn();tests++;console.log('PASS '+name);}
function scripts(context,names){vm.createContext(context);for(const name of names)vm.runInContext(fs.readFileSync(base+name,'utf8'),context,{filename:name});}
function content(options={}){
 let listener;
 const state={now:101000,draft:options.draft||'',sends:0,inserts:0,permits:0,users:[{id:'11111111-1111-1111-1111-111111111111',text:'old'}]};
 const context={state,URL,TextEncoder,crypto:crypto.webcrypto,console,location:{origin:'https://chatgpt.com',pathname:'/c/'+target,search:'',hash:''},
  Date:{now:()=>state.now},setTimeout:fn=>{state.now+=250;queueMicrotask(fn);},document:{querySelector:()=>null},
  browser:{runtime:{id:extensionId,onMessage:{addListener:fn=>listener=fn},sendMessage:async msg=>{
   if(msg.cmd!=='exact_one_send_permit')return;
   state.permits++;
   if(options.permitHook)options.permitHook(state,context);
   return options.denyPermit?{ok:false}:{ok:true,build,authorization_id:delivery.authorization.authorization_id,expires_at:delivery.authorization.expires_at};
  }}}};
 scripts(context,['binding_contract.js','one_contract.js','candidate_analysis.js','chatgpt_content.js']);
 context.actualMessages=vm.runInContext('userMessages',context);
 context.actualIds=vm.runInContext('userMessageIds',context);
 vm.runInContext(`composer=()=>state;composerText=()=>state.draft;userMessages=()=>state.users;userMessageIds=()=>new Set(state.users.map(value=>value.id));insert=(editor,text)=>{state.draft=text;state.inserts++;};sendButton=()=>({click:()=>{state.sends++;if(!state.noTurn)state.users.push({id:'${uuid}',text:state.observed===undefined?state.draft:state.observed});if(!state.keepDraft)state.draft='';}});`,context);
 const call=(msg,sender={id:extensionId})=>listener(msg,sender);
 return {state,context,call,ready:()=>call({cmd:'readiness',binding}),send:(value=delivery)=>call({...structuredClone(value),cmd:'deliver'})};
}
function background(options={}){
 let nativeListener,internalListener,disconnect;
 const native=[],tabMessages=[];
 const port={onMessage:{addListener:fn=>nativeListener=fn},onDisconnect:{addListener:fn=>disconnect=fn},postMessage:msg=>native.push(msg)};
 const context={URL,console,Date:{now:()=>101000},setTimeout:()=>1,clearTimeout:()=>{},browser:{runtime:{id:extensionId,connectNative:()=>port,onMessage:{addListener:fn=>internalListener=fn}},tabs:{query:async()=>[{id:1,windowId:2,url:'https://chatgpt.com/c/'+target,hidden:false,discarded:false,incognito:false}],sendMessage:async(id,msg)=>{
   tabMessages.push({id,msg});
   if(msg.cmd==='readiness')return {reachable:true,bound:true,composer_present:true,composer_empty:true,generation_active:false,busy:false,ready:true,reason:'ready',binding_identity:binding.identity,one_build:build};
   return options.onDeliver?options.onDeliver(msg):{delivery_id:msg.delivery_id,state:'NEEDS_REVIEW'};
 }}}};
 scripts(context,['binding_contract.js','one_contract.js','background.js']);
 return {context,native,tabMessages,call:msg=>nativeListener(msg,port),internal:(msg,sender)=>internalListener(msg,sender),disconnect:()=>disconnect()};
}
(async()=>{
 await test('content no grant and historical entries never insert',async()=>{const h=content();await h.ready();for(const value of [{cmd:'deliver',delivery_id:'seq94'}, {...delivery,authorization:undefined}]){assert.equal((await h.send(value)).state,'FAILED_PERMANENT');}assert.equal(h.state.inserts,0);assert.equal(h.state.sends,0);});
 await test('exact envelope preserves payload one Send new UUID empty composer',async()=>{const h=content();assert.equal((await h.ready()).one_build,build);const r=await h.send();assert.equal(r.state,'DELIVERED');assert.equal(r.user_turn_uuid,uuid);assert.equal(r.observed_sha256,hash);assert.equal(h.state.users[1].text,text);assert.equal(h.state.draft,'');assert.equal(h.state.sends,1);assert.equal(h.state.permits,1);await h.send();assert.equal(h.state.sends,1);assert.equal(h.state.permits,1);});
 await test('wrong ID/hash/target/epoch/expiry/malformed grant never inserts',async()=>{for(const mutation of [d=>d.delivery_id='seq94',d=>d.text_sha256='0'.repeat(64),d=>d.authorization.binding.epoch='0'.repeat(32),d=>d.authorization.binding.conversation_id=old,d=>d.authorization.expires_at=101,d=>d.authorization.synthetic=true]){const h=content();await h.ready();const d=structuredClone(delivery);mutation(d);assert.equal((await h.send(d)).state,'FAILED_PERMANENT');assert.equal(h.state.inserts,0);assert.equal(h.state.sends,0);}});
 await test('wrong text is not replaced with an expected synthetic payload',async()=>{const h=content();await h.ready();assert.equal((await h.send({...delivery,text:'different'})).state,'FAILED_PERMANENT');assert.equal(h.state.inserts,0);});
 await test('human draft remains untouched',async()=>{const h=content({draft:' human draft '});await h.ready();assert.equal((await h.send()).pre_send,true);assert.equal(h.state.inserts,0);assert.equal(h.state.sends,0);assert.equal(h.state.draft,' human draft ');});
 await test('durable permit denied never clicks Send',async()=>{const h=content({denyPermit:true});await h.ready();assert.equal((await h.send()).state,'NEEDS_REVIEW');assert.equal(h.state.sends,0);assert.equal(h.state.permits,1);});
 await test('expiry or navigation while awaiting permit never clicks',async()=>{for(const permitHook of [(state)=>state.now=221000,(_,context)=>context.location.pathname='/c/'+old]){const h=content({permitHook});await h.ready();assert.notEqual((await h.send()).state,'DELIVERED');assert.equal(h.state.sends,0);}});
 await test('ambiguous Send no duplicate across repeated delivery',async()=>{const h=content();await h.ready();h.state.noTurn=true;assert.equal((await h.send()).state,'NEEDS_REVIEW');await h.send();assert.equal(h.state.sends,1);assert.equal(h.state.permits,1);});
 await test('nonempty post-Send composer never certifies delivered',async()=>{const h=content();await h.ready();h.state.keepDraft=true;assert.equal((await h.send()).state,'NEEDS_REVIEW');assert.equal(h.state.sends,1);});
 await test('later unrelated human USER turn does not hide exact UUID',async()=>{const h=content();await h.ready();vm.runInContext(`const previous=sendButton;sendButton=()=>({click:()=>{previous().click();state.users.push({id:'22222222-2222-2222-2222-222222222222',text:'later human'});}})`,h.context);assert.equal((await h.send()).user_turn_uuid,uuid);assert.equal(h.state.sends,1);});
 await test('existing same-text UUID not new proof',async()=>{const h=content();await h.ready();h.state.users.push({id:uuid,text});h.state.noTurn=true;assert.equal((await h.send()).state,'NEEDS_REVIEW');assert.equal(h.state.sends,1);});
 await test('two new identical turns fail closed',async()=>{const h=content();await h.ready();vm.runInContext(`const previous=sendButton;sendButton=()=>({click:()=>{previous().click();state.users.push({id:'22222222-2222-2222-2222-222222222222',text:state.users.at(-1).text});}})`,h.context);assert.equal((await h.send()).state,'NEEDS_REVIEW');});
 await test('content rejects non-extension sender before readiness or Send',async()=>{const h=content();assert.equal(await h.call({cmd:'readiness',binding},{id:'other'}),undefined);assert.equal(await h.call(delivery,{}),undefined);assert.equal(h.state.inserts,0);});
 await test('current production DOM selectors retain exact UUID',async()=>{const h=content(),owner={getAttribute:key=>key==='data-chatgpt-search-message-ids'?uuid:null};const element={isConnected:true,innerText:text,getAttribute:key=>key==='data-user-message-bubble'?'true':null,closest:selector=>selector==='[data-chatgpt-search-message-ids]'?owner:null,querySelectorAll:()=>[]};h.context.getComputedStyle=()=>({display:'block',visibility:'visible'});const doc={querySelectorAll:selector=>selector.includes('data-user-message-bubble')?[element]:[]};const turns=h.context.actualMessages(doc,{historical:true});assert.equal(turns.length,1);assert.equal(turns[0].id,uuid);assert.equal(turns[0].text,text);});
 await test('background obtains binding before tab lookup and advertises capability',async()=>{const h=background();await h.call({cmd:'binding_config',binding});await h.call({cmd:'readiness_probe',binding_identity:binding.identity,probe_id:'1'.repeat(32)});assert.equal(h.native.at(-1).one_build,build);assert.equal(h.native.at(-1).content.one_build,build);assert.equal(h.native.at(-1).ready,true);});
 await test('background refuses all old or wrong grant entries',async()=>{const h=background();await h.call({cmd:'binding_config',binding});await h.call({...delivery,delivery_id:'seq94'});await h.call({...delivery,authorization:undefined});assert.equal(h.tabMessages.length,0);});
 await test('background forwards exact item and authorization once',async()=>{const h=background();await h.call({cmd:'binding_config',binding});await h.call(structuredClone(delivery));assert.equal(h.tabMessages.length,1);assert.equal(h.tabMessages[0].msg.authorization.authorization_id,delivery.authorization.authorization_id);assert.equal(h.native.at(-1).cmd,'result');await h.call(delivery);assert.equal(h.tabMessages.length,1);});
 await test('background permit requires active exact tab and native approval',async()=>{let finish;const h=background({onDeliver:()=>new Promise(resolve=>finish=resolve)});await h.call({cmd:'binding_config',binding});const running=h.call(structuredClone(delivery));await new Promise(setImmediate);const msg={cmd:'exact_one_send_permit',delivery_id:delivery.delivery_id,authorization_id:delivery.authorization.authorization_id};assert.equal((await h.internal(msg,{id:'other',tab:{id:1,url:'https://chatgpt.com/c/'+target}})).ok,false);assert.equal((await h.internal(msg,{id:extensionId,tab:{id:99,url:'https://chatgpt.com/c/'+target}})).ok,false);const waiting=h.internal(msg,{id:extensionId,tab:{id:1,url:'https://chatgpt.com/c/'+target}});assert.equal(h.native.at(-1).cmd,'send_permit');await h.call({cmd:'permit_result',ok:true,build,authorization_id:msg.authorization_id,expires_at:220});assert.equal((await waiting).ok,true);finish({delivery_id:delivery.delivery_id,state:'NEEDS_REVIEW'});await running;});
 await test('disconnect while permit is pending rejects without another forward',async()=>{let finish;const h=background({onDeliver:()=>new Promise(resolve=>finish=resolve)});await h.call({cmd:'binding_config',binding});const running=h.call(delivery);await new Promise(setImmediate);const waiting=h.internal({cmd:'exact_one_send_permit',delivery_id:delivery.delivery_id,authorization_id:delivery.authorization.authorization_id},{id:extensionId,tab:{id:1,url:'https://chatgpt.com/c/'+target}});h.disconnect();assert.equal((await waiting).ok,false);finish({delivery_id:delivery.delivery_id,state:'NEEDS_REVIEW'});await running;assert.equal(h.tabMessages.length,1);});
 await test('source keeps one Send site and unchanged extension permissions',async()=>{const source=fs.readFileSync(base+'chatgpt_content.js','utf8');assert.equal((source.match(/button\.click\(\)/g)||[]).length,1);assert.deepEqual(JSON.parse(fs.readFileSync(base+'manifest.json','utf8')).permissions,['nativeMessaging','tabs']);assert.equal(binding.delivery_policy,'HOLD');});
 console.log(tests+' isolated JS tests passed; not live Firefox delivery');
})().catch(error=>{console.error(error);process.exitCode=1;});
