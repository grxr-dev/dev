"use strict";
const BINDING_BUILD='inbox-binding-20261101-01';
function checkedBinding(value){
 const keys=['schema','build','conversation_id','generation','epoch','delivery_policy','identity'];
 if(!value||Object.keys(value).sort().join('|')!==keys.sort().join('|')||value.schema!=='middleman-inbox-binding/1'||value.build!==BINDING_BUILD||value.delivery_policy!=='HOLD'||!Number.isInteger(value.generation)||value.generation<1||value.generation>1000000||!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value.conversation_id)||!/^[0-9a-f]{32}$/.test(value.epoch)||!/^[0-9a-f]{64}$/.test(value.identity))throw Error('binding unavailable or inconsistent');
 return Object.freeze({...value});
}
