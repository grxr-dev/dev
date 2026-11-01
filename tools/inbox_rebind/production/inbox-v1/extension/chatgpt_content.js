"use strict";
let BOUND_CONVERSATION_ID=null, configuredBinding=null;
const VERIFIER_BUILD='inbox-v1-trace2-20261011-01';

// Tracing-only identity observations; never used as delivery gates.
function conversationIdFromUrl(doc=document){
 const m=(doc.location||location).pathname.match(/^(?:\/g\/g-p-[a-z0-9-]+)?\/c\/([0-9a-f-]{36})(?:\/|$)/i);
 return m?m[1].toLowerCase():null;
}
function detectBranch(doc=document){
 try{return doc.querySelector('[data-testid*="branch"],[aria-label*="version"],[aria-label*="branch"],[data-testid*="version"]')?true:null;}catch(_){return null;}
}
function conversationTrace(initialId){
 try{return conversationSignals(BOUND_CONVERSATION_ID,conversationIdFromUrl(document),initialId,detectBranch(document));}catch(_){return {};}
}

function verifierTrace(d,event,fields={}){
 try{
  const pending=browser.runtime.sendMessage({cmd:'verifier_trace',event:{build:VERIFIER_BUILD,delivery_id:d.delivery_id,event,ts_ms:Date.now(),...fields}});
  if(pending&&pending.catch)pending.catch(()=>{});
 }catch(_){} // Diagnostics must never affect delivery or add a wait.
}
const canonicalText=s=>s.replace(/\r\n/g,'\n').replace(/\r/g,'\n');
// Narrow observed rendering variant: simple, single-line, single-backtick spans.
// Leave fenced/multi-backtick documents untouched; preserve every content byte.
function inlineCodeBubbleText(text){
 text=canonicalText(text);
 if(text.includes(String.fromCharCode(92))||text.includes('``')||/^ {0,3}~{3,}/m.test(text))return text;
 return text.replace(/(^|[^`])`([^`\n]+)`(?!`)/g,(_,prefix,content)=>prefix+content);
}
function bound(){return !!configuredBinding&&location.origin==='https://chatgpt.com'&&!location.search&&!location.hash&&new RegExp('^(?:/g/g-p-[a-z0-9-]+)?/c/'+BOUND_CONVERSATION_ID+'/?$','i').test(location.pathname);}
async function hash(text){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonicalText(text))))).map(b=>b.toString(16).padStart(2,'0')).join('');}
function visible(el){return el.isConnected&&!el.closest('[hidden],[inert],[aria-hidden="true"]')&&el.getClientRects().length>0&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden';}
function composer(){const els=Array.from(document.querySelectorAll('#prompt-textarea,.ProseMirror[data-composer-markdown][role="textbox"]')).filter(el=>visible(el)&&(el.tagName==='TEXTAREA'||el.isContentEditable));return els.length===1?els[0]:null;}
const insertionDiagnostics=new WeakMap();
function decorativeAutolinkIcon(node){
 if(node.nodeType!==1||node.textContent!==""||!(node.getAttribute('aria-hidden')==="true"||node.getAttribute('contenteditable')==="false"))return false;
 const link=node.closest('span[text-link-href],a[href]');
 const url=link&&(link.getAttribute('text-link-href')||link.getAttribute('href'));
 return !!(link&&/^https?:\/\//.test(url||"")&&['SPAN','SVG'].includes(node.tagName.toUpperCase())&&Array.from(node.querySelectorAll('*')).every(child=>['span','svg','path'].includes(child.localName)));
}
function logicalText(el,{editor=false}={}){
 // Read structure, never CSS layout or whole-element textContent. Only known
 // paragraphs, inline text/wrappers, hard breaks and URL decoration are valid.
 function inline(parent){
  let result="";
  for(const node of parent.childNodes){
   if(node.nodeType===3){result+=node.nodeValue;continue;}
   if(decorativeAutolinkIcon(node))continue;
   if(node.nodeType!==1||node.getAttribute('contenteditable')==='false'||node.getAttribute('aria-hidden')==='true')return null;
   if(node.tagName==="BR"){
    if(editor&&node.classList.contains('ProseMirror-trailingBreak')){if(node!==parent.lastChild)return null;}else result+='\n';
   }else if(node.tagName==="SPAN"||node.tagName==="A"){
    const part=inline(node);if(part===null)return null;
    const generated=node.hasAttribute('text-link-href')||node.hasAttribute('data-rich-text-generated-autolink')||node.tagName==="A";
    if(generated){const url=node.getAttribute('text-link-href')||node.getAttribute('href');if(!/^https?:\/\//.test(url||"")||part!==url)return null;}
    result+=part;
   }else return null;
  }
  return result;
 }
 const nodes=Array.from(el.childNodes);
 if(nodes.every(n=>n.nodeType===1&&n.tagName==="P")){
  if(editor&&nodes.length===1&&nodes[0].textContent===""&&nodes[0].childNodes.length<=1&&(nodes[0].childNodes.length===0||nodes[0].firstChild.nodeName==="BR"))return "";
  const paragraphs=nodes.map(inline);return paragraphs.some(p=>p===null)?null:paragraphs.join('\n');
 }
 return inline(el);
}
function composerText(el){return el.tagName==="TEXTAREA"?el.value:logicalText(el,{editor:true});}
// Snapshot identities even when an existing turn is offscreen or its text is
// temporarily unparseable. Never accept an old turn merely because it renders later.
function userMessageIds(doc=document){
 const ids=new Set();
 for(const el of doc.querySelectorAll('[data-user-message-bubble="true"],[data-markdown-text-tone="user-message"]')){
  const id=currentUserIdentity(el);if(id)ids.add(id);
 }
 for(const el of doc.querySelectorAll('[data-chatgpt-search-unit-key$=":user"][data-chatgpt-search-message-ids],[data-message-author-role="user"][data-message-id]')){
  const id=el.getAttribute('data-chatgpt-search-message-ids')||el.getAttribute('data-message-id');
  if(id)ids.add(id);
 }
 return ids;
}
const CURRENT_USER_SELECTOR='[data-user-message-bubble="true"],[data-markdown-text-tone="user-message"]';
function currentUserIdentity(el){
 const owner=el.closest('[data-chatgpt-search-message-ids]');
 const id=owner&&owner.getAttribute('data-chatgpt-search-message-ids');
 return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id||'')?id:null;
}
function userMessages(doc=document,{historical=false}={}){
 const messages=new Map(),bubbleOnlyIds=new Set(),markdownIds=new Set(),legacyIds=new Set();
 function visible(el){if(!el.isConnected||el.closest('[hidden],[inert],[aria-hidden="true"]'))return false;if(historical)return true;const style=doc.defaultView.getComputedStyle(el);return el.getClientRects().length>0&&style.display!=="none"&&style.visibility!=="hidden"&&style.opacity!=="0";}
 for(const el of doc.querySelectorAll(CURRENT_USER_SELECTOR)){
  const id=currentUserIdentity(el);
  if(!id||!visible(el))continue;
  let body=el;
  if(el.getAttribute('data-user-message-bubble')==='true'){
   const texts=el.querySelectorAll('[data-markdown-text-tone="user-message"]');
   if(texts.length>1)continue;
   // Bubble-only turns expose exact payload innerText; no content class required.
   body=texts.length===1?texts[0]:el;
  }
  if(!body||currentUserIdentity(body)!==id||!visible(body)||typeof body.innerText!=='string')continue;
  if(body.getAttribute('data-markdown-text-tone')==='user-message')markdownIds.add(id);
  else if(body.getAttribute('data-user-message-bubble')==='true')bubbleOnlyIds.add(id);
  const text=canonicalText(body.innerText);
  // Conflicting representations of one UUID cannot establish exact proof.
  if(messages.has(id)&&messages.get(id)!==text)messages.set(id,null);
  else if(!messages.has(id))messages.set(id,text);
 }
 for(const el of doc.querySelectorAll('[data-message-author-role="user"][data-message-id]')){
  if(!visible(el))continue;
  const id=el.getAttribute('data-message-id');
  if(!id||messages.has(id))continue;
  const body=el.querySelector('.whitespace-pre-wrap')||el,text=logicalText(body);
  if(text!==null){messages.set(id,text);legacyIds.add(id);}
 }
 return Array.from(messages,([id,text])=>({id,text,bubbleOnly:bubbleOnlyIds.has(id)&&!markdownIds.has(id),source:markdownIds.has(id)?'markdown-tone':legacyIds.has(id)?'legacy':'bubble'})).filter(turn=>turn.text!==null);
}
function sendButton(doc=document){
 const selectors='button[type="submit"][aria-label="Send"],button[data-testid="send-button"],button[aria-label="Send prompt"],button[aria-label="Send message"]';
 const candidates=Array.from(doc.querySelectorAll(selectors)).filter(el=>{
  if(el.disabled||el.getAttribute('aria-disabled')==='true'||el.closest('[hidden],[inert],[aria-hidden="true"]'))return false;
  const style=doc.defaultView.getComputedStyle(el);
  return el.getClientRects().length>0&&style.display!=="none"&&style.visibility!=="hidden"&&style.visibility!=="collapse"&&style.opacity!=="0";
 });
 return candidates.length===1?candidates[0]:null;
}
function insert(el,text){
 // Do not give insertText a multiline string: Firefox/ProseMirror can parse
 // its literal LF text nodes as collapsible whitespace. Encode LF as hard
 // breaks in a text-only HTML slice, so the editable document contains LF.
 if(composerText(el)!=="")throw Error("Non-empty composer; insertion refused");
 el.focus();
 if(el.tagName==="TEXTAREA"){
  Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value").set.call(el,text);
  insertionDiagnostics.set(el,{path:"textarea"});el.dispatchEvent(new InputEvent("input",{bubbles:true,inputType:"insertText",data:text}));return;
 }
 const doc=el.ownerDocument,view=doc.defaultView,p=doc.createElement('p');
 p.style.whiteSpace='pre-wrap';
 const lines=text.split('\n');
 lines.forEach((line,index)=>{if(index)p.append(doc.createElement('br'));p.append(doc.createTextNode(line));});
 // Preserve a final real hard break plus the editor's empty final caret line.
 if(text.endsWith('\n')){const caret=doc.createElement('br');caret.className='ProseMirror-trailingBreak';p.append(caret);}
 const selection=view.getSelection(),range=doc.createRange();range.selectNodeContents(el);selection.removeAllRanges();selection.addRange(range);
 // The current ChatGPT editor cancels untrusted synthetic paste without
 // inserting anything. Use native editing directly: it produces the input/
 // mutation events ProseMirror observes, while BR nodes preserve literal LF.
 // Payload characters are escaped text nodes, never interpreted markup.
 if(composerText(el)!=="")throw Error("Composer changed before insertion; not overwritten");
 insertionDiagnostics.set(el,{path:"native-insertHTML"});
 if(!doc.execCommand('insertHTML',false,p.outerHTML))throw Error("Multiline composer insertion unsupported");
}

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let busy=false;
const seen=new Map();
async function deliver(d){
  if(!configuredBinding||configuredBinding.delivery_policy==='HOLD')return {state:'FAILED_PERMANENT',pre_send:true,delivery_id:d.delivery_id,error:'recipient binding held; no insertion or Send authorized'};
  verifierTrace(d,'start',{bound:bound(),payload_sha256:d.text_sha256});
  if(seen.has(d.delivery_id)){verifierTrace(d,'terminal',{reason:'cached_idempotent_outcome',bound:bound()});const old=seen.get(d.delivery_id);return old.payload_sha256===d.text_sha256?Object.fromEntries(Object.entries(old).filter(([k])=>k!=='payload_sha256')):{state:'NEEDS_REVIEW',delivery_id:d.delivery_id,error:'duplicate ID/hash conflict'};}
  const fail=(state,error,pre_send=false)=>{verifierTrace(d,'outcome',{state,reason:error,pre_send,bound:bound()});return {state,error,pre_send,delivery_id:d.delivery_id};};
  if(busy)return fail('FAILED_RETRYABLE','another delivery active',true);
  if(!bound())return fail('FAILED_RETRYABLE','bound conversation not open',true);
  if(typeof d.text!=='string'||d.text!==canonicalText(d.text)||await hash(d.text)!==d.text_sha256)return fail('FAILED_PERMANENT','canonical text/hash mismatch',true);
  busy=true;let mayHaveSent=false;
  try {
    const editor=composer();
    if(!editor)return fail('FAILED_RETRYABLE','composer missing or unsupported',true);
    // Whitespace and unsupported rich DOM count as a draft. Never overwrite them.
    if(composerText(editor)!=='')return fail('FAILED_RETRYABLE','composer contains a draft',true);
    if(document.querySelector('button[data-testid="stop-button"],button[aria-label="Stop streaming"]'))return fail('FAILED_RETRYABLE','generation active',true);
    const ids=userMessageIds(document);
    let initialConvId=null;try{initialConvId=conversationIdFromUrl(document);}catch(_){}
    verifierTrace(d,'baseline',{baseline_ids:Array.from(ids).slice(0,256),baseline_count:ids.size,baseline_truncated:ids.size>256,bound:bound(),...conversationTrace(initialConvId)});
    if(!bound()||composer()!==editor||composerText(editor)!=='')return fail('FAILED_RETRYABLE','composer changed before insertion',true);
    insert(editor,d.text);
    let exact=false;
    for(let i=0;i<80;i++){if(!bound()||composer()!==editor)break;if(composerText(editor)===d.text){await sleep(100);exact=composerText(editor)===d.text;break;}await sleep(25);}
    if(!exact)return fail('FAILED_PERMANENT','inserted composer text differs; no Send',true);
    const button=sendButton();
    if(!button)return fail('FAILED_PERMANENT','Send unavailable after insertion; draft left untouched',true);
    if(!bound()||composer()!==editor||composerText(editor)!==d.text||await hash(composerText(editor))!==d.text_sha256)return fail('FAILED_PERMANENT','composer changed before Send',true);
    // Recheck synchronously after the asynchronous hash operation.
    if(!bound()||composer()!==editor||composerText(editor)!==d.text)return fail('FAILED_PERMANENT','composer changed during final hash; no Send',true);
    // Mark BEFORE click: even a thrown click or lost page is ambiguous.
    mayHaveSent=true;
    const pending=fail('NEEDS_REVIEW','Send initiated; outcome pending');seen.set(d.delivery_id,{...pending,payload_sha256:d.text_sha256});
    verifierTrace(d,'send',{bound:bound()});
    button.click(); // the sole Send site
    // Exact payload identity, not viewport visibility or the first new turn.
    // Stay within the background's 120 s deadline and never click again.
    const end=Date.now()+90000;let matchingId=null,exitReason='deadline_expired',sample=0;
    verifierTrace(d,'deadline',{deadline_ms:end,bound:bound()});
    while(Date.now()<end){
      if(!bound()){exitReason='page_unbound_before_sample';break;}
      const matches=new Map(),candidates=[];let candidateCount=0;sample++;
      for(const turn of userMessages(document,{historical:true})){
        const inBaseline=ids.has(turn.id);
        const observed=canonicalText(turn.text);
        const expected=observed===d.text?d.text:turn.bubbleOnly?inlineCodeBubbleText(d.text):d.text;
        const candidate={uuid:turn.id,in_baseline:inBaseline,canonical_match:observed===expected,hash_match:null,source:turn.source||'synthetic'};
        candidateCount++;if(candidates.length<64)candidates.push(candidate);
        // Preserve the original delivery gates and required-match hash operation.
        let observedHash,expectedHash;
        if(!inBaseline&&observed===expected){
          observedHash=await hash(observed);expectedHash=await hash(expected);
          candidate.hash_match=observedHash===expectedHash;candidate.observed_sha256=observedHash;candidate.expected_sha256=expectedHash;
          if(candidate.hash_match)matches.set(turn.id,turn);
        }
        // Diagnostics are best-effort, including hashing/helper failures.
        // Never use analysis output to decide delivery or overwrite match gates.
        try{
          const normalization=turn.source==='markdown-tone'?'markdown':(observed!==d.text&&turn.bubbleOnly)?'bubble':'none';
          const analysis=analyzeCandidate(turn.text,observed,expected,normalization,observedHash===undefined?await hash(observed):observedHash,expectedHash===undefined?await hash(expected):expectedHash);
          const {canonical_match,...details}=analysis;Object.assign(candidate,details);
        }catch(_){}

      }
      verifierTrace(d,'sample',{sample,bound:bound(),...conversationTrace(initialConvId),candidates,candidate_count:candidateCount,candidates_truncated:candidateCount>64,match_count:matches.size});
      if(!bound()){exitReason='page_unbound_after_sample';break;}
      if(matches.size>1){verifierTrace(d,'terminal',{reason:'multiple_exact_new_identities',state:'NEEDS_REVIEW',bound:bound()});const r=fail('NEEDS_REVIEW','multiple new USER identities match this exact payload');seen.set(d.delivery_id,{...r,payload_sha256:d.text_sha256});return r;}
      const id=matches.size===1?matches.keys().next().value:null;
      // Require the same new message identity and exact canonical text/hash on
      // consecutive samples; transient partial/replaced DOM is not terminal.
      if(id&&id===matchingId){
        verifierTrace(d,'terminal',{reason:'stable_exact_match',uuid:id,bound:bound(),state:'DELIVERED'});
        const r={state:'DELIVERED',delivery_id:d.delivery_id,observed_sha256:d.text_sha256,send_count:1,new_user_turns:1,composer_empty:true};seen.set(d.delivery_id,{...r,payload_sha256:d.text_sha256});return r;
      }
      matchingId=id;
      await sleep(250);
    }
    verifierTrace(d,'terminal',{reason:exitReason,bound:bound(),...conversationTrace(initialConvId),deadline_ms:end,state:'NEEDS_REVIEW'});
    const r=fail('NEEDS_REVIEW','Send may have occurred; no stable exact-payload new USER identity within verification deadline');seen.set(d.delivery_id,{...r,payload_sha256:d.text_sha256});return r;
  }catch(_){
    verifierTrace(d,'terminal',{reason:mayHaveSent?'exception_after_send':'exception_before_send',bound:bound()});
    const r=fail(mayHaveSent?'NEEDS_REVIEW':'FAILED_PERMANENT',mayHaveSent?'exception after Send intent; manual review':'pre-Send insertion exception; draft retained',!mayHaveSent);
    if(mayHaveSent)seen.set(d.delivery_id,{...r,payload_sha256:d.text_sha256});return r;
  }finally{busy=false;}
}
// Read-only: never invokes insert(), Send, deliver(), tracing or seen-ID state.
function readiness(){
 const r={reachable:true,binding_identity:configuredBinding?configuredBinding.identity:null,bound:bound(),composer_present:false,composer_empty:false,generation_active:false,busy:busy,ready:false,reason:'page_unbound'};
 if(!r.bound)return r;
 try{
  const editor=composer();r.composer_present=!!editor;
  if(!editor){r.reason='composer_missing_or_unsupported';return r;}
  r.composer_empty=composerText(editor)==='';
  r.generation_active=!!document.querySelector('button[data-testid="stop-button"],button[aria-label="Stop streaming"]');
  r.ready=r.composer_empty&&!r.generation_active&&!r.busy;
  r.reason=r.ready?'ready':r.busy?'delivery_active':!r.composer_empty?'draft_present':'generation_active';
 }catch(_){r.reason='readiness_inspection_failed';}
 return r;
}
if(typeof browser!=='undefined')browser.runtime.onMessage.addListener(msg=>{
  if(msg&&msg.cmd==='readiness'){
    try{configuredBinding=checkedBinding(msg.binding);BOUND_CONVERSATION_ID=configuredBinding.conversation_id;return Promise.resolve(readiness());}
    catch(_){configuredBinding=null;BOUND_CONVERSATION_ID=null;return Promise.resolve(readiness());}
  }
  if(!msg||msg.cmd!=='deliver'||!bound())return undefined;
  return deliver(msg);
});
