'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(__dirname+'/../inbox_future/production/inbox-v1/extension/background.js','utf8');
const dest='6ae5615a-0720-83ea-a43b-82386ce031e5',build='inbox-raw-user-proof-20261101-01';
function harness(proofBuild){
 const sent=[];const c={reachable:true,bound:true,composer_present:true,composer_empty:true,generation_active:false,busy:false,ready:true,reason:'ready',one_build:'one',future_build:'future',future_lane_seal:'seal',proof_build:proofBuild,binding_identity:'id',diagnostics:[]};
 const ctx={URL,console,BINDING_BUILD:'binding',ONE_BUILD:'one',FUTURE_BUILD:'future',setTimeout:()=>1,clearTimeout:()=>{},browser:{
  runtime:{connectNative:()=>({onMessage:{addListener:()=>{}},onDisconnect:{addListener:()=>{}}}),onMessage:{addListener:()=>{}}},
  tabs:{query:async()=>[{id:7,windowId:2,url:'https://chatgpt.com/c/'+dest,hidden:false,discarded:false,incognito:false}],sendMessage:async(id,msg)=>{sent.push(msg);return c;}}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);vm.runInContext(`configuredBinding={identity:'id'};BOUND_CONVERSATION_ID='${dest}';configuredFutureLane={seal:'seal'};`,ctx);return {ctx,sent};
}
(async()=>{
 const h=harness(build);h.ctx.targets=[{delivery_id:'known',user_turn_uuid:'known-uuid',text_sha256:'known-hash'}];
 const result=await vm.runInContext("readinessProbe('probe',targets)",h.ctx);
 assert.equal(result.ready,true);assert.equal(h.sent[0].cmd,'readiness');assert.equal(h.sent[0].diagnostic_targets[0].delivery_id,'known');assert.equal(result.content.proof_build,build);
 console.log('PASS no-send target/proof capability traverses background readiness');
 const stale=harness('old-build');const rejected=await vm.runInContext("readinessProbe('probe',[])",stale.ctx);assert.equal(rejected.ready,false);assert.equal(rejected.reason,'content_unreachable_or_timeout');
 console.log('PASS stale loaded content cannot satisfy new proof capability');
})().catch(e=>{console.error(e);process.exitCode=1;});
