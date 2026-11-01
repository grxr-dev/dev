'use strict';
// Privacy-free reproduction of the observed DIV -> DIV -> (DIV, BUTTON)
// structure. Text here is synthetic: the live button's text was NOT captured.
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(__dirname+'/../inbox_future/production/inbox-v1/extension/chatgpt_content.js','utf8');
const ctx={browser:{runtime:{onMessage:{addListener:()=>{}}}}};
vm.createContext(ctx);vm.runInContext(source,ctx);
const id='acab8cd4-6871-49cd-b92a-93961f10a574';
const owner={getAttribute:()=>id};
function el(tag,text,children=[],attrs={}){
 const n={nodeType:1,tagName:tag,innerText:text,childNodes:children,isConnected:true,
  getAttribute:k=>attrs[k]||null,closest:s=>s.includes('data-chatgpt-search-message-ids')?owner:null,getClientRects:()=>[{}]};
 n.querySelectorAll=s=>{
  const all=[];function walk(p){for(const c of p.childNodes){if(c.nodeType===1){all.push(c);walk(c);}}}walk(n);
  return s.includes('button')?all.filter(c=>['BUTTON','INPUT','TEXTAREA','SELECT'].includes(c.tagName)||c.getAttribute('role')==='button'):
   all.filter(c=>c.getAttribute('data-markdown-text-tone')==='user-message');
 };return n;
}
function selected(n){ctx.n=n;return vm.runInContext('authoredBubbleBody(n)',ctx);}
function messages(n){ctx.doc={querySelectorAll:s=>s.includes('data-user-message-bubble')?[n]:[],defaultView:{getComputedStyle:()=>({display:'block',visibility:'visible',opacity:'1'})}};return vm.runInContext('userMessages(doc)',ctx);}
let count=0;function test(name,f){f();count++;console.log('PASS '+name);}
const payload='[CODEX → CHATGPT]\n\nGate OPEN. `metadata`';
const content=el('DIV',payload),button=el('BUTTON','Synthetic UI');
const bubble=el('DIV',payload+'\nSynthetic UI',[el('DIV',payload+'\nSynthetic UI',[content,button])],{'data-user-message-bubble':'true'});
test('live-observed wrapper shape selects content, not action button',()=>assert.equal(selected(bubble),content));
test('candidate retains exact authored text and stable UUID',()=>{const m=messages(bubble);assert.equal(m.length,1);assert.equal(m[0].id,id);assert.equal(m[0].text,payload);assert.equal(m[0].bubbleOnly,true);});
test('different authored content is never replaced with expected payload',()=>{content.innerText='altered';assert.equal(messages(bubble)[0].text,'altered');content.innerText=payload;});
test('ambiguous sibling content branches fail closed',()=>assert.equal(selected(el('DIV','',[content,el('DIV','other'),button])),null));
test('unclassified direct text beside control fails closed',()=>assert.equal(selected(el('DIV','',[{nodeType:3,nodeValue:'authored'},button])),null));
test('UI-free bubble remains byte-exact including trailing whitespace',()=>{const p=el('DIV','literal\n\n  ');assert.equal(selected(p).innerText,'literal\n\n  ');});
test('code fence content is not rewritten or fuzzy-normalized',()=>{const p=el('DIV','```text\n`literal`\n```');assert.equal(selected(el('DIV','',[p,button])),p);assert.equal(p.innerText,'```text\n`literal`\n```');});
test('a rendered fence omission is not fabricated into raw-model proof',()=>{content.innerText='rendered code without fences';const m=messages(bubble)[0];assert.equal(m.source,'bubble');assert.notEqual(m.text,'```text\nrendered code without fences\n```');});
console.log(count+' focused boundary tests passed; live post-exclusion hash is NOT claimed.');
