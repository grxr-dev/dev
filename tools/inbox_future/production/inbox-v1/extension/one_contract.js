"use strict";
const ONE_BUILD='inbox-exact-one-20261101-01';
const ONE_ID='middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878';
const ONE_HASH='1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651';
function checkedGrant(delivery,binding){
 if(delivery&&delivery.authorization&&delivery.authorization.schema==='inbox-future-grant/1')return checkedFutureGrant(delivery,binding,configuredFutureLane);
 const grant=delivery&&delivery.authorization;
 const keys=['schema','build','authorization_id','delivery_id','text_sha256','binding','created_at','expires_at'];
 if(!binding||binding.delivery_policy!=='HOLD'||binding.conversation_id!=='6ae5615a-0720-83ea-a43b-82386ce031e5'||binding.generation!==1||!grant||Object.keys(grant).sort().join('|')!==keys.sort().join('|')||grant.schema!=='inbox-exact-one/1'||grant.build!==ONE_BUILD||grant.delivery_id!==ONE_ID||delivery.delivery_id!==ONE_ID||grant.text_sha256!==ONE_HASH||delivery.text_sha256!==ONE_HASH||!/^[0-9a-f]{32}$/.test(grant.authorization_id))throw Error('exact-one grant required');
 const saved=checkedBinding(grant.binding);
 if(Object.keys(saved).some(key=>saved[key]!==binding[key])||!Number.isFinite(grant.created_at)||!Number.isFinite(grant.expires_at)||grant.expires_at-grant.created_at<1||grant.expires_at-grant.created_at>300||Date.now()/1000<grant.created_at||Date.now()/1000>=grant.expires_at)throw Error('stale exact-one grant');
 return grant;
}
