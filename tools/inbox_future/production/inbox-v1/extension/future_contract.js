"use strict";
const FUTURE_BUILD='inbox-future-only-20261101-01';
function futureCanonical(v){return v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+futureCanonical(v[k])).join(',')+'}':JSON.stringify(v);}
function checkedFutureLane(v,binding){
 if(!v||Object.keys(v).sort().join('|')!==['schema','build','state','lane_id','binding','completion_cutoff','request_cutoff','seal'].sort().join('|')||v.schema!=='inbox-future-only/1'||v.build!==FUTURE_BUILD||!['PREPARED','ACTIVE'].includes(v.state)||!/^[0-9a-f]{32}$/.test(v.lane_id)||!/^[0-9a-f]{64}$/.test(v.seal)||!Number.isSafeInteger(v.completion_cutoff)||v.completion_cutoff<0||!Number.isSafeInteger(v.request_cutoff)||v.request_cutoff<0)throw Error('future checkpoint required');
 const b=checkedBinding(v.binding);
 if(Object.keys(b).some(k=>b[k]!==binding[k]))throw Error('future binding mismatch');
 return Object.freeze(v);
}
function checkedFutureGrant(d,binding,lane){
 const g=d&&d.authorization,v=checkedFutureLane(lane,binding),keys=['schema','build','authorization_id','delivery_id','text_sha256','binding','created_at','expires_at','lane','source'];
 if(v.state!=='ACTIVE'||!g||Object.keys(g).sort().join('|')!==keys.sort().join('|')||g.schema!=='inbox-future-grant/1'||g.build!=='inbox-exact-one-20261101-01'||futureCanonical(g.lane)!==futureCanonical(v)||!/^[0-9a-f]{32}$/.test(g.authorization_id)||g.delivery_id!==d.delivery_id||g.text_sha256!==d.text_sha256||!/^[0-9a-f]{64}$/.test(g.text_sha256))throw Error('exact future authorization required');
 const b=checkedBinding(g.binding),s=g.source;
 if(Object.keys(b).some(k=>b[k]!==binding[k])||!s||Object.keys(s).sort().join('|')!==['sequence','event_id','request_ordinal','request_id','result_sha256'].sort().join('|')||!Number.isSafeInteger(s.sequence)||s.sequence<=v.completion_cutoff||!Number.isSafeInteger(s.request_ordinal)||s.request_ordinal<=v.request_cutoff||typeof s.event_id!=='string'||s.event_id.length<16||g.delivery_id!==s.request_id+':'+s.result_sha256||!/^[0-9a-f]{64}$/.test(s.result_sha256)||!Number.isFinite(g.created_at)||!Number.isFinite(g.expires_at)||g.expires_at-g.created_at<1||g.expires_at-g.created_at>300||Date.now()/1000<g.created_at||Date.now()/1000>=g.expires_at)throw Error('stale future source/grant');
 return g;
}
