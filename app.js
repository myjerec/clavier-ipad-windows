'use strict';
const $=id=>document.getElementById(id), selected=new Set();
let chain=Promise.resolve(), generation=0, pending=0;
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function clearMods(){selected.clear();document.querySelectorAll('#mods [aria-pressed]').forEach(b=>b.setAttribute('aria-pressed','false'));}
function connected(){ $('keyboard').disabled=false;$('connection').hidden=true;$('connection-toggle').setAttribute('aria-expanded','false'); }
async function post(path,data){
 const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),5000);
 try{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Keyboard':'1'},body:JSON.stringify(data),signal:controller.signal});
 const result=await r.json();if(!r.ok){if(r.status===401)$('keyboard').disabled=true;throw Error(result.error||'Connexion refusée');}return result;
 }finally{clearTimeout(timer);}
}
function send(data){
 if(data.type!=='media'&&(sentText||nativeBusy))nativeProblem('Commande utilisée : touche « Reprendre ici » avant de reprendre la saisie directe.');
 if(pending>=20){status('Trop de touches en attente. Patiente un instant.',true);return;}
 const current=generation;pending++;
 chain=chain.then(async()=>{if(current!==generation)return;await post('/command',data);status('Connecté · commande envoyée au PC');}).catch(e=>{generation++;clearMods();status(e.name==='AbortError'?'Connexion interrompue : vérifie le PC avant de réessayer.':e.message,true);}).finally(()=>pending--);
}
function button(parent,label,action,caption){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=action;if(caption){const small=document.createElement('small');small.textContent=caption;b.append(small);}parent.append(b);return b;}
for(const mod of ['Ctrl','Alt','Shift','Win','AltGr']){
 const b=button($('mods'),mod==='Shift'?'Maj ⇧':mod,()=>{selected.has(mod)?selected.delete(mod):selected.add(mod);b.setAttribute('aria-pressed',String(selected.has(mod)));});b.setAttribute('aria-pressed','false');
}
function key(key){const mods=[...selected];clearMods();send({type:'key',key,mods});}
for(const row of ['1234567890','AZERTYUIOP','QSDFGHJKLM','WXCVBN']){
 const div=document.createElement('div');div.className='keyrow';$('letters').append(div);
 for(const c of row)button(div,c,()=>{
  if(selected.size)key(c);else send({type:'text',text:c.toLowerCase()});
 });
}
const symbols=document.createElement('div');symbols.className='row';$('letters').append(symbols);
for(const c of ['é','è','à','ç','ù','@','€','!','?',',','.',';',':',"'",'"','-','_','(',')','/','\\','+','=','[',']','{','}'])button(symbols,c,()=>{clearMods();send({type:'text',text:c});});
for(const [label,k] of [['Échap','Esc'],['Tab ↹','Tab'],['Entrée ↵','Enter'],['Effacer ⌫','Backspace'],['Suppr','Delete'],['Espace','Space'],['Début','Home'],['Fin','End'],['Page ↑','PageUp'],['Page ↓','PageDown'],['Insérer','Insert'],['Verr. Maj','CapsLock'],['Capture','PrintScreen'],['←','Left'],['↑','Up'],['↓','Down'],['→','Right']])button($('navigation'),label,()=>key(k));
for(let i=1;i<=12;i++)button($('functions'),'F'+i,()=>key('F'+i));
for(const [label,k,mods] of [['Copier','C',['Ctrl']],['Coller','V',['Ctrl']],['Couper','X',['Ctrl']],['Annuler','Z',['Ctrl']],['Rétablir','Y',['Ctrl']],['Tout sélectionner','A',['Ctrl']],['Changer de fenêtre','Tab',['Alt']],['Exécuter','R',['Win']],['Afficher le bureau','D',['Win']],['Enregistrer','S',['Ctrl']],['Rechercher','F',['Ctrl']],['Menu Démarrer','Esc',['Ctrl']]])button($('shortcuts'),label,()=>{clearMods();send({type:'key',key:k,mods});},mods.join(' + ')+' + '+k);
$('pair').onclick=async()=>{try{await post('/pair',{code:$('code').value.trim()});$('code').value='';connected();status('Connecté · sélectionne une fenêtre sur ton PC.');}catch(e){status(e.message,true);}};
$('reset').onclick=clearMods;
let sentText='', nativeBusy=false, nativeBlocked=false, composing=false, draftTimer;
function newDraftId(){return Array.from(crypto.getRandomValues(new Uint32Array(4))).join('-');}
let draftId=newDraftId();
function nativeProblem(message){nativeBlocked=true;$('live').checked=false;$('native-status').textContent=message;}
function scheduleDraft(){
 clearTimeout(draftTimer);
 if(selected.size){$('native-status').textContent='Combinaison active · choisis une lettre (ou utilise « Lettres PC »).';return;}
 if($('live').checked&&!nativeBlocked&&!composing&&!document.hidden)flushDraft(false);
}
function flushDraft(all){
 clearTimeout(draftTimer);
 if(nativeBusy||nativeBlocked||composing||$('keyboard').disabled||document.hidden)return;
 let draft;
 try{draft=nextDraft($('text').value,sentText,all);}catch(e){nativeProblem(e.message);return;}
 if(!draft.changed)return;
 nativeBusy=true;$('send').disabled=true;$('new-text').disabled=true;
 const current=generation;
 chain=chain.then(async()=>{
  if(current!==generation||document.hidden||nativeBlocked) return;
  // Re-read after queued shortcuts, so a replaced prediction is not sent stale.
  if(composing)return;
  draft=nextDraft($('text').value,sentText,all);
  if(!draft.changed)return;
  await post('/command',{type:'direct',draft:draftId,base:sentText,text:draft.text});
  sentText=draft.snapshot;
  $('native-status').textContent='Saisie en direct · lettres et corrections transmises au PC.';
 }).catch(e=>{
  generation++;nativeProblem('Envoi arrêté : vérifie le texte sur le PC avant de créer une nouvelle zone. '+(e.name==='AbortError'?'Connexion interrompue.':e.message));
 }).finally(()=>{nativeBusy=false;$('send').disabled=false;$('new-text').disabled=false;scheduleDraft();});
}
$('text').addEventListener('compositionstart',()=>{composing=true;clearTimeout(draftTimer);});
$('text').addEventListener('compositionend',()=>{composing=false;scheduleDraft();});
$('text').addEventListener('input',e=>{if(!e.isComposing)scheduleDraft();});
// Convert a native iPad letter into a Windows chord when modifiers are selected.
// Unsupported/non-cancellable composition stays in the draft, never sent as a chord.
$('text').addEventListener('beforeinput',e=>{
 if(!selected.size||e.isComposing)return;
 if(e.inputType==='insertText'&&e.data&&/^[a-z0-9]$/i.test(e.data)&&e.cancelable){
  e.preventDefault();key(e.data.toUpperCase());
 }else if(e.cancelable){e.preventDefault();status('Choisis une lettre dans « Lettres PC » pour cette combinaison.',true);}
});
$('live').onchange=scheduleDraft;
$('send').onclick=()=>{clearMods();flushDraft(true);};
$('new-text').onclick=()=>{
 if(nativeBusy)return;
 clearTimeout(draftTimer);sentText='';draftId=newDraftId();nativeBlocked=false;$('text').value='';$('live').checked=true;
 $('native-status').textContent='Nouvelle zone · le texte du PC reste inchangé.';$('text').focus();
};
document.addEventListener('visibilitychange',()=>{if(document.hidden){clearMods();generation++;clearTimeout(draftTimer);$('live').checked=false;}});
let checkingConnection=false,wasConnected=false;
async function reconnect(){
 if(checkingConnection||document.hidden)return;
 checkingConnection=true;
 try{await post('/command',{type:'status'});connected();if(!wasConnected)status('Connecté automatiquement · iPad mémorisé');wasConnected=true;}
 catch(e){
  wasConnected=false;
  status($('keyboard').disabled?'Appaire cet iPad une fois avec le code du PC.':'PC indisponible · reconnexion automatique en attente.',true);
 }finally{checkingConnection=false;}
}
reconnect();
window.setInterval(reconnect,15000);
window.addEventListener('online',reconnect);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)reconnect();});
$('open-keyboard').onclick=()=>{$('text').focus({preventScroll:true});};
$('connection-toggle').onclick=()=>{const visible=$('connection').hidden;$('connection').hidden=!visible;$('connection-toggle').setAttribute('aria-expanded',String(visible));};
document.querySelectorAll('[data-panel]').forEach(tab=>{
 tab.onclick=()=>{
  document.querySelectorAll('[data-panel]').forEach(other=>other.setAttribute('aria-pressed',String(other===tab)));
  document.querySelectorAll('.panel').forEach(panel=>{panel.hidden=panel.id!==tab.dataset.panel;});
 };
});
document.querySelectorAll('button').forEach(b=>b.addEventListener('pointerdown',e=>{
 if(document.activeElement===$('text'))e.preventDefault();
}));
function fitViewport(){
 const viewport=window.visualViewport;
 document.documentElement.style.setProperty('--app-height',(viewport?viewport.height:window.innerHeight)+'px');
 document.documentElement.style.setProperty('--app-top',(viewport?viewport.offsetTop:0)+'px');
}
window.addEventListener('resize',fitViewport);
if(window.visualViewport){window.visualViewport.addEventListener('resize',fitViewport);window.visualViewport.addEventListener('scroll',fitViewport);}
fitViewport();
