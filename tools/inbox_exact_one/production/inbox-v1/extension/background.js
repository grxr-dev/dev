"use strict";
const NATIVE_HOST='jarvis_inbox_host';
let BOUND_CONVERSATION_ID=null, configuredBinding=null;
let port=null, timer=null, busy=false, awaitingAck=false;
let activeDelivery=null, permitWait=null;
function exactBoundUrl(url){
  if(!configuredBinding)return false;
  try {const u=new URL(url);return u.origin==='https://chatgpt.com'&&!u.search&&!u.hash&&new RegExp('^(?:/g/g-p-[a-z0-9-]+)?/c/'+BOUND_CONVERSATION_ID+'/?$','i').test(u.pathname);}
  catch(_){return false;}
}
function schedulePoll(ms=30000){clearTimeout(timer);timer=setTimeout(pollBridge,ms);}
function connectNative(){
  try {
    const connected=browser.runtime.connectNative(NATIVE_HOST);port=connected;
    connected.onMessage.addListener(msg=>onNativeMessage(msg,connected));
    connected.onDisconnect.addListener(()=>{if(port!==connected)return;if(permitWait){permitWait.resolve({ok:false});permitWait=null;}port=null;configuredBinding=null;BOUND_CONVERSATION_ID=null;awaitingAck=false;schedulePoll(15000);});
    schedulePoll(100); // every successful reconnect must schedule its first poll
  } catch(_){port=null;schedulePoll(15000);}
}
function pollBridge(){
  if(busy){schedulePoll();return;}
  if(!port){connectNative();return;}
  try{port.postMessage({cmd:'binding'});}catch(_){try{port.disconnect();}catch(_){}port=null;schedulePoll(15000);}
}
async function boundTabs(){
  return (await browser.tabs.query({url:'https://chatgpt.com/*'})).filter(t=>exactBoundUrl(t.url));
}
const READINESS_BUILD=BINDING_BUILD;
async function readinessProbe(probe_id){
  if(!configuredBinding)throw Error('binding required');
  const identity=configuredBinding.identity;
  const tabs=await boundTabs();
  const matches=tabs.slice(0,128).map(t=>{
    const u=new URL(t.url);const m={id:t.id,windowId:t.windowId,url:u.origin+u.pathname};
    for(const k of ['active','hidden','discarded','pinned','incognito'])if(typeof t[k]==='boolean')m[k]=t[k];
    return m;
  });
  const r={cmd:'readiness_result',probe_id,build:READINESS_BUILD,one_build:ONE_BUILD,binding_identity:identity,match_count:tabs.length,matches,truncated:tabs.length>128,ready:false,reason:'unique_bound_tab_required'};
  if(busy||awaitingAck){r.reason='delivery_or_ack_active';return r;}
  if(tabs.length!==1)return r;
  try{
    const c=await Promise.race([browser.tabs.sendMessage(tabs[0].id,{cmd:'readiness',binding:configuredBinding}),new Promise((_,reject)=>setTimeout(()=>reject(Error('readiness timeout')),5000))]);
    const keys=['reachable','bound','composer_present','composer_empty','generation_active','busy','ready'];
    if(!c||c.one_build!==ONE_BUILD||c.binding_identity!==identity||!configuredBinding||configuredBinding.identity!==identity||keys.some(k=>typeof c[k]!=='boolean')||typeof c.reason!=='string')throw Error('invalid readiness');
    r.content=Object.fromEntries(keys.map(k=>[k,c[k]]));r.content.reason=c.reason;r.content.binding_identity=identity;
    r.content.one_build=ONE_BUILD;
    r.ready=keys.slice(0,4).every(k=>c[k])&&!c.generation_active&&!c.busy&&c.ready;
    r.reason=r.ready?'ready':c.reason;
  }catch(_){r.reason='content_unreachable_or_timeout';}
  return r;
}
async function attemptDelivery(d){
  try{checkedGrant(d,configuredBinding);}catch(_){return {state:'FAILED_PERMANENT',pre_send:true,error:'exact owner grant required; historical HOLD remains'};}
  const tabs=await boundTabs();
  if(tabs.length!==1||['hidden','discarded','incognito'].some(key=>tabs[0][key]!==false))return {state:'FAILED_PERMANENT',pre_send:true,error:'exactly one ready already-open bound tab required'};
  // Once forwarded, a transport exception/timeout is ambiguous, never a retry.
  try {
    checkedGrant(d,configuredBinding);activeDelivery={delivery:d,tabId:tabs[0].id};
    const r=await Promise.race([browser.tabs.sendMessage(tabs[0].id,{cmd:'deliver',delivery_id:d.delivery_id,text:d.text,text_sha256:d.text_sha256,authorization:d.authorization}),
      new Promise((_,reject)=>setTimeout(()=>reject(Error('timeout')),120000))]);
    if(!r||r.delivery_id!==d.delivery_id||!['DELIVERED','FAILED_RETRYABLE','FAILED_PERMANENT','NEEDS_REVIEW'].includes(r.state))throw Error('invalid outcome');
    if(r.state==='FAILED_RETRYABLE'&&r.pre_send!==true)throw Error('unproven retry');
    return r;
  }catch(_){return {state:'NEEDS_REVIEW',error:'content outcome unknown after forwarding; never resend'};}
  finally{activeDelivery=null;}
}
async function onNativeMessage(msg,connected){
  if(connected!==port||!msg)return;
  if(msg.cmd==='permit_result'){
    if(permitWait){const pending=permitWait;permitWait=null;pending.resolve(msg.ok===true&&msg.build===ONE_BUILD&&msg.authorization_id===pending.authorization_id?msg:{ok:false});}
    return;
  }
  if(msg.cmd==='binding_config'){
    try{configuredBinding=checkedBinding(msg.binding);BOUND_CONVERSATION_ID=configuredBinding.conversation_id;connected.postMessage({cmd:'poll',binding_identity:configuredBinding.identity});}
    catch(_){configuredBinding=null;BOUND_CONVERSATION_ID=null;schedulePoll();}
    return;
  }
  if(msg.cmd==='readiness_probe'){
    try{if(!configuredBinding||msg.binding_identity!==configuredBinding.identity)throw Error('stale binding');const r=await readinessProbe(msg.probe_id);if(port===connected)connected.postMessage(r);}catch(_){schedulePoll();}
    schedulePoll();return;
  }
  if(msg.cmd==='readiness_recorded'){schedulePoll();return;}
  if(msg.cmd==='acked'){awaitingAck=false;schedulePoll();return;}
  if(msg.cmd==='ack_pending'){awaitingAck=true;schedulePoll(15000);return;}
  if(msg.cmd==='idle'||msg.cmd==='error'){schedulePoll();return;}
  if(msg.cmd!=='delivery'||busy||awaitingAck||!configuredBinding)return;
  try{checkedGrant(msg,configuredBinding);}catch(_){schedulePoll();return;}
  busy=true;
  let r;
  try{r=await attemptDelivery(msg);}catch(_){r={state:'NEEDS_REVIEW',error:'background outcome unknown'};}
  if(port===connected){
    try{awaitingAck=true;connected.postMessage({cmd:'result',delivery_id:msg.delivery_id,...r});}
    catch(_){try{connected.disconnect();}catch(_){}port=null;awaitingAck=false;}
  }
  // A disconnect never causes another call to attemptDelivery for this item.
  busy=false;schedulePoll(port?30000:15000);
}
connectNative();

// One-way observational events only; no reconnect, poll, claim or delivery here.
if(browser.runtime.onMessage)browser.runtime.onMessage.addListener((msg,sender)=>{
 if(msg&&msg.cmd==='exact_one_send_permit'){
   try{
     if(!sender||sender.id!==browser.runtime.id||!sender.tab||!activeDelivery||sender.tab.id!==activeDelivery.tabId||!exactBoundUrl(sender.tab.url)||!port||permitWait)throw Error('untrusted or duplicate permit request');
     const delivery=activeDelivery.delivery,grant=checkedGrant(delivery,configuredBinding);
     if(msg.delivery_id!==delivery.delivery_id||msg.authorization_id!==grant.authorization_id)throw Error('wrong permit identity');
     return new Promise(resolve=>{
       const pending={resolve,authorization_id:grant.authorization_id};permitWait=pending;
       setTimeout(()=>{if(permitWait===pending){permitWait=null;resolve({ok:false});}},5000);
       try{port.postMessage({cmd:'send_permit',delivery_id:delivery.delivery_id,authorization_id:grant.authorization_id});}
       catch(_){permitWait=null;resolve({ok:false});}
     });
   }catch(_){return Promise.resolve({ok:false});}
 }
 if(!msg||msg.cmd!=='verifier_trace'||!sender||!sender.tab||!port)return;
 try{port.postMessage({cmd:'verifier_trace',event:msg.event});}catch(_){}
});
