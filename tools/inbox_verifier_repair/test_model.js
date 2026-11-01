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
 const cases=[
  ['seq132-shaped rendered suffix','[CODEX → CHATGPT]\n\n**Gate OPEN.** `0.8.0`\nNot started.','rendered text plus UI, not the payload'],
  ['seq133-shaped triple fence','[CODEX → CHATGPT]\n\nPinned `0.8.0`.\n\n```text\n`literal`  two spaces\n```\nNot started.','Markdown rendering with code widgets'],
  ['autolink/newlines','https://example.com\n\nUnicode → café\n','https://example.com external-link UI'],
 ];
 for(const [label,raw,rendered] of cases)await test(label+' verifies exact model SHA despite rendered variation',async()=>{
  const f=doc(raw,rendered,{wrapper:true}),h=harness(f),r=await h.send(raw);
  assert.equal(r.state,'DELIVERED');assert.equal(r.observed_sha256,sha(raw));assert.equal(r.user_turn_uuid,UUID);
  await h.send(raw);assert.equal(h.state.sends,1);assert.ok(h.traces.some(x=>x.event==='sample'&&x.candidates.some(c=>c.source==='raw-user-model'&&c.hash_match)));
 });
 await test('altered raw payload cannot be hidden by a matching rendered string',async()=>{const h=harness(doc('altered','expected'));assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');await h.send('expected');assert.equal(h.state.sends,1);});
 await test('wrong author model cannot establish user delivery',async()=>{const h=harness(doc('expected','expected',{role:'assistant'}));assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');});
 await test('pre-existing identical UUID is never new evidence',async()=>{const f=doc('expected','ui');const h=harness(f,{old:true});assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');});
 await test('wrong conversation cannot Send or verify',async()=>{const h=harness(doc('expected','expected'),{path:'/c/unrelated'});assert.notEqual((await h.send('expected')).state,'DELIVERED');assert.equal(h.state.sends,0);});
 await test('model conversation mismatch fails closed',async()=>{const f=doc('expected','expected');f.modelObject.conversation_id='other';const h=harness(f);assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');});
 await test('conflicting model representations of one UUID fail closed',async()=>{const f=doc('expected','expected');f.el.__reactProps$fixture={message:{...f.modelObject,content:{content_type:'text',parts:['altered']}}};const h=harness(f);assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');});
 await test('page getters are not executed during model discovery',async()=>{const f=doc('expected','expected');let called=false;Object.defineProperty(f.el,'__reactProps$evil',{get(){called=true;throw Error('getter');}});const h=harness(f);assert.equal((await h.send('expected')).state,'DELIVERED');assert.equal(called,false);});
 await test('unavailable model does not fabricate a raw-model proof',async()=>{const h=harness(doc('expected','altered',{model:false}));assert.equal((await h.send('expected')).state,'NEEDS_REVIEW');});
 await test('no-send provenance is bounded structure and hashes, never message bodies',async()=>{
  const secret='PRIVATE_FIXTURE_TEXT_must_not_be_logged',f=doc(secret,'UI_PRIVATE_TEXT'),h=harness(f,{old:true});
  h.ctx.targets=[{delivery_id:'fixture',user_turn_uuid:UUID,text_sha256:sha(secret)}];
  const result=await vm.runInContext('receiptDiagnostics(targets)',h.ctx);assert.equal(result[0].exact,true);
  const json=JSON.stringify(result);assert.ok(!json.includes(secret));assert.ok(!json.includes('UI_PRIVATE_TEXT'));assert.equal(h.state.sends,0);
 });
 console.log(`${count} focused synthetic model/DOM tests passed; live Firefox model availability not claimed.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
