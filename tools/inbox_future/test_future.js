'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=__dirname+'/production/inbox-v1/extension/';
const b={schema:'middleman-inbox-binding/1',build:'inbox-binding-20261101-01',conversation_id:'6ae5615a-0720-83ea-a43b-82386ce031e5',generation:1,epoch:'a'.repeat(32),delivery_policy:'HOLD',identity:'b'.repeat(64)};
const lane={schema:'inbox-future-only/1',build:'inbox-future-only-20261101-01',state:'ACTIVE',lane_id:'c'.repeat(32),binding:b,completion_cutoff:10,request_cutoff:20,seal:'d'.repeat(64)};
const source={sequence:11,event_id:'server-generated-event-identity',request_ordinal:21,request_id:'fresh',result_sha256:'e'.repeat(64)};
const grant={schema:'inbox-future-grant/1',build:'inbox-exact-one-20261101-01',authorization_id:'f'.repeat(32),delivery_id:'fresh:'+source.result_sha256,text_sha256:'1'.repeat(64),binding:b,created_at:Date.now()/1000-1,expires_at:Date.now()/1000+60,lane,source};
const ctx={Date,configuredFutureLane:lane};vm.createContext(ctx);for(const n of ['binding_contract.js','future_contract.js','one_contract.js'])vm.runInContext(fs.readFileSync(root+n,'utf8'),ctx);
const d={delivery_id:grant.delivery_id,text_sha256:grant.text_sha256,authorization:grant};
let count=0;
function test(name,f){f();count++;console.log('PASS '+name);}
function check(delivery=d,binding=b){ctx.d=delivery;ctx.b=binding;return vm.runInContext('checkedGrant(d,b)',ctx);}
test('new server grant with exact source/binding accepted',()=>assert.equal(check().authorization_id,grant.authorization_id));
test('old completion/request boundaries and arbitrary flag rejected',()=>{for(const change of [{source:{...source,sequence:10}},{source:{...source,request_ordinal:20}},{future:true}])assert.throws(()=>check({...d,authorization:{...grant,...change}}));});
test('wrong lane/binding/payload and expiry rejected',()=>{for(const change of [{lane:{...lane,lane_id:'0'.repeat(32)}},{binding:{...b,identity:'2'.repeat(64)}},{text_sha256:'3'.repeat(64)},{expires_at:Date.now()/1000-1}])assert.throws(()=>check({...d,authorization:{...grant,...change}}));});
test('JSON property order cannot cause false rejection',()=>{const reversed=Object.fromEntries(Object.entries(lane).reverse());assert.equal(check({...d,authorization:{...grant,lane:reversed}}).delivery_id,d.delivery_id);});
test('coherently PREPARED lane still cannot authorize Send',()=>{const prepared={...lane,state:'PREPARED'};ctx.configuredFutureLane=prepared;assert.throws(()=>check({...d,authorization:{...grant,lane:prepared}}));ctx.configuredFutureLane=lane;});
console.log(count+' future contract tests passed; no browser/Send');
