'use strict';
// Synthetic framework/DOM contracts. NOT a capture of the live Firefox subtree.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const source=fs.readFileSync(__dirname+'/../inbox_future/production/inbox-v1/extension/chatgpt_content.js','utf8');
const DEST='6ae5615a-0720-83ea-a43b-82386ce031e5',UUID='41bfef82-0c00-4014-9f22-11adbf4345f5';
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
let count=0;
function doc(raw,rendered,{id=UUID,role='user',model=true,wrapper=false}={}){
 const owner={getAttribute:k=>k==='data-chatgpt-search-message-ids'?id:null};
 const modelObject={id,author:{role},content:{content_type:'text',parts:[raw]},conversation_id:DEST};
 const el={nodeType:1,tagName:'DIV',childNodes:[],isConnected:true,parentElement:null,
  innerText:rendered,getAttribute:k=>k==='data-user-message-bubble'?'true':null,
  closest:s=>s==='[data-chatgpt-search-message-ids]'?owner:null,querySelectorAll:()=>[],getClientRects:()=>[{}]};
 if(model){const page=wrapper?{}:el;page.__reactFiber$fixture={memoizedProps:{message:modelObject},return:null};if(wrapper)el.wrappedJSObject=page;}
 const document={querySelector:()=>null,querySelectorAll:s=>s.includes('data-user-message-bubble')?[el]:[],defaultView:{getComputedStyle:()=>({display:'block',visibility:'visible',opacity:'1'})}};
 return {document,el,modelObject};
}
function harness(fixture,{old=false,path='/c/'+DEST}={}){
 const state={draft:'',sends:0,now:0},traces=[];
 const ctx={console,URL,TextEncoder,crypto:crypto.webcrypto,location:{origin:'https://chatgpt.com',pathname:path,search:'',hash:''},
  document:old?fixture.document:doc('old','old',{id:'11111111-1111-1111-1111-111111111111'}).document,
  ONE_BUILD:'inbox-exact-one-20261101-01',FUTURE_BUILD:'inbox-future-only-20261101-01',Date:{now:()=>state.now},
  setTimeout:f=>{state.now+=250;queueMicrotask(f);},getComputedStyle:()=>({display:'block',visibility:'visible'}),
  browser:{runtime:{id:'test',onMessage:{addListener:()=>{}},sendMessage:m=>{
   if(m.cmd==='exact_one_send_permit')return Promise.resolve({ok:true,build:ctx.ONE_BUILD,authorization_id:'grant',expires_at:500});
   traces.push(m.event);return Promise.resolve();}}},state};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 vm.runInContext(`configuredBinding={conversation_id:'${DEST}',identity:'test'};BOUND_CONVERSATION_ID='${DEST}';
  checkedGrant=()=>({});composer=()=>state;composerText=()=>state.draft;
  insert=(el,text)=>{state.draft=text;};sendButton=()=>({click:()=>{state.sends++;document=fixture;state.draft='';}});`,ctx);
 ctx.fixture=fixture.document;
 return {ctx,state,traces,async send(text){ctx.delivery={delivery_id:'fixture:hash',text,text_sha256:sha(text),authorization:{authorization_id:'grant',expires_at:500}};return vm.runInContext('deliver(delivery)',ctx);}};
}
async function test(name,run){await run();count++;console.log('PASS '+name);}
(async()=>{
 for(const [name,raw,rendered] of [
  ['fence rendering','[CODEX → CHATGPT]\n\n```text\n`literal`\n```','literal rendered without fences'],
  ['bubble action UI','[CODEX → CHATGPT]\n\nGate `OPEN`.','Gate OPEN.\nUI control text']
 ])await test(name+' uses truthful composer proof, not DOM hash',async()=>{
  const h=harness(doc(raw,rendered,{model:false})),r=await h.send(raw);
  assert.equal(r.state,'DELIVERED');assert.equal(r.verification_method,'composer_hash_single_send_new_user_uuid_v1');assert.equal(r.composer_sha256,sha(raw));assert.equal(r.observed_sha256,null);assert.equal(r.user_turn_uuid,UUID);
  await h.send(raw);assert.equal(h.state.sends,1);
 });
 await test('changed inserted payload cannot Send',async()=>{const h=harness(doc('expected','ui',{model:false}));vm.runInContext("insert=()=>{state.draft='changed';}",h.ctx);assert.notEqual((await h.send('expected')).state,'DELIVERED');assert.equal(h.state.sends,0);});
 await test('incorrect inbound payload SHA cannot Send',async()=>{const h=harness(doc('expected','ui',{model:false}));h.ctx.d={delivery_id:'wrong:hash',text:'expected',text_sha256:sha('other')};const r=await vm.runInContext('deliver(d)',h.ctx);assert.notEqual(r.state,'DELIVERED');assert.equal(h.state.sends,0);});
 await test('pre-existing identical stable UUID never proves new delivery',async()=>{const h=harness(doc('expected','ui',{model:false}),{old:true});assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');assert.equal(h.state.sends,1);});
 await test('wrong bound conversation cannot Send',async()=>{const h=harness(doc('expected','ui',{model:false}),{path:'/c/wrong'});assert.notEqual((await h.send('expected')).state,'DELIVERED');assert.equal(h.state.sends,0);});
 await test('two distinct fresh USER UUIDs are ambiguous',async()=>{const a=doc('a','a',{model:false}),b=doc('b','b',{model:false,id:'22222222-2222-2222-2222-222222222222'});a.document.querySelectorAll=s=>s.includes('data-user-message-bubble')?[a.el,b.el]:[];const h=harness(a);assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');await h.send('expected');assert.equal(h.state.sends,1);});
 await test('zero fresh visible USER UUIDs stays review/no resend',async()=>{const f=doc('expected','ui',{model:false});f.el.getClientRects=()=>[];const h=harness(f);assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');await h.send('expected');assert.equal(h.state.sends,1);});
 await test('missing durable Send permit cannot click',async()=>{const h=harness(doc('expected','ui',{model:false}));h.ctx.browser.runtime.sendMessage=()=>Promise.resolve({ok:false});assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');assert.equal(h.state.sends,0);});
 await test('post-Send concurrent draft cannot verify',async()=>{const h=harness(doc('expected','ui',{model:false}));vm.runInContext("sendButton=()=>({click:()=>{state.sends++;document=fixture;state.draft='human draft';}})",h.ctx);assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');assert.equal(h.state.sends,1);});
 await test('optional DOM/model diagnostic failure cannot veto valid identity',async()=>{const h=harness(doc('expected','ui',{model:false}));vm.runInContext("userMessages=()=>{throw Error('diagnostic only');}",h.ctx);assert.equal((await h.send('expected')).state,'DELIVERED');});
 await test('delayed visible bubble verifies without another click',async()=>{const f=doc('expected','ui',{model:false}),h=harness(f);f.el.getClientRects=()=>h.state.now>=1000?[{}]:[];assert.equal((await h.send('expected')).state,'DELIVERED');assert.equal(h.state.sends,1);});
 console.log(count+' composer/single-Send/stable-user-identity tests passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
