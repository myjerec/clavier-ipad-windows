'use strict';
const $=id=>document.getElementById(id), selected=new Set();
let chain=Promise.resolve(), generation=0, pending=0;
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function clearMods(){selected.clear();document.querySelectorAll('#mods [aria-pressed]').forEach(b=>b.setAttribute('aria-pressed','false'));}
function connected(){ const first=$('keyboard').disabled;$('keyboard').disabled=false;if(first)$('text').focus({preventScroll:true});$('connection').hidden=true;$('connection-toggle').setAttribute('aria-expanded','false'); }
async function post(path,data){
 const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),5000);
 try{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Keyboard':'1'},body:JSON.stringify(data),signal:controller.signal});
 const result=await r.json();if(!r.ok){if(r.status===401)$('keyboard').disabled=true;throw Error(result.error||'Connexion refusée');}return result;
 }finally{clearTimeout(timer);}
}
function send(data){
 const beforeCommand=$('text').value;
 if(pending>=20){status('Trop de touches en attente. Patiente un instant.',true);return;}
 const current=generation;pending++;
 chain=chain.then(async()=>{if(current!==generation)return;await post('/command',data);if(data.type!=='media')resetDraft(beforeCommand);status('Connecté · commande envoyée au PC');}).catch(e=>{generation++;clearMods();status(e.name==='AbortError'?'Connexion interrompue : vérifie le PC avant de réessayer.':e.message,true);}).finally(()=>pending--);
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
function resetDraft(snapshot=$('text').value){
 const current=$('text').value;
 $('text').value=current.startsWith(snapshot)?current.slice(snapshot.length):'';
 sentText='';draftId=newDraftId();nativeBlocked=false;
}
function nativeProblem(message){resetDraft();$('native-status').textContent=message;}

function scheduleDraft(){
 clearTimeout(draftTimer);
 if(selected.size){$('native-status').textContent='Combinaison active · choisis une lettre (ou utilise « Lettres PC »).';return;}
 if(!nativeBlocked&&!composing&&!document.hidden)flushDraft(false);
}
function flushDraft(all){
 clearTimeout(draftTimer);
 if(nativeBusy||nativeBlocked||composing||$('keyboard').disabled||document.hidden)return;
 let draft;
 try{draft=nextDraft($('text').value,sentText,all);}catch(e){nativeProblem(e.message);return;}
 if(!draft.changed)return;
 nativeBusy=true;
 const current=generation;
 chain=chain.then(async()=>{
  if(current!==generation||document.hidden||nativeBlocked) return;
  // Re-read after queued shortcuts, so a replaced prediction is not sent stale.
  if(composing)return;
  draft=nextDraft($('text').value,sentText,all);
  if(!draft.changed)return;
  const result=await post('/command',{type:'direct',draft:draftId,base:sentText,text:draft.text,auto:true});
  if(current!==generation)return;
  if(result.reset||draft.snapshot.length>=1800){resetDraft(draft.snapshot);}else{sentText=draft.snapshot;}
  $('native-status').textContent=result.discardedCorrection?'Le curseur a changé : ancienne correction ignorée. Continue à écrire.':'Saisie automatique · lettres et corrections transmises au PC.';
 }).catch(e=>{
  generation++;nativeProblem('Vérifie le texte sur le PC ; la prochaine saisie repartira automatiquement. '+(e.name==='AbortError'?'Connexion interrompue.':e.message));
 }).finally(()=>{nativeBusy=false;scheduleDraft();});
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
document.addEventListener('visibilitychange',()=>{if(document.hidden){clearMods();generation++;clearTimeout(draftTimer);resetDraft();}});
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
 if(document.activeElement===$('text')&&!b.closest?.('#clipboard-panel'))e.preventDefault();
}));
function fitViewport(){
 const viewport=window.visualViewport;
 document.documentElement.style.setProperty('--app-height',(viewport?viewport.height:window.innerHeight)+'px');
 document.documentElement.style.setProperty('--app-top',(viewport?viewport.offsetTop:0)+'px');
}
window.addEventListener('resize',fitViewport);
if(window.visualViewport){window.visualViewport.addEventListener('resize',fitViewport);window.visualViewport.addEventListener('scroll',fitViewport);}
fitViewport();

// Clipboard access is explicit; never poll or persist clipboard contents.
function clipStatus(message){$('clipboard-status').textContent=message;}
function clipCheck(text){if(typeof text!=='string'||text.length>2000||text.includes('\0'))throw Error('Texte de 2 000 caractères maximum, sans caractère nul.');return text;}
$('clip-to-pc').onclick=async()=>{
 try{
  const text=clipCheck(await navigator.clipboard.readText());
  await post('/command',{type:'clipboard',action:'write',text});
  clipStatus('Copié sur le PC. Utilise Coller dans ton application Windows.');
 }catch(e){clipStatus('Transfert non effectué : '+e.message+' Tu peux coller le texte dans la zone ci-dessous.');}
};
$('clip-from-pc').onclick=async()=>{
 try{
  // Start the write during the tap: Safari accepts a promised ClipboardItem.
  $('clipboard-text').value='';
  const transfer=post('/command',{type:'clipboard',action:'read'}).then(r=>{
   const text=clipCheck(r.text);$('clipboard-text').value=text;return text;
  });
  transfer.catch(()=>{}); // A denied browser write must not leave a rejected fetch unhandled.
  if(typeof ClipboardItem!=='undefined'&&navigator.clipboard?.write){
   await navigator.clipboard.write([new ClipboardItem({'text/plain':transfer.then(text=>new Blob([text],{type:'text/plain'}))})]);
   clipStatus('Texte du PC copié sur l’iPad.');
  }else{await transfer;clipStatus('Texte reçu. Touche « Copier ce texte sur l’iPad ».');}
 }catch(e){clipStatus('Copie non terminée : '+e.message+' Si le texte est affiché, utilise le bouton de copie ci-dessous.');}
};
$('clip-send-text').onclick=async()=>{
 try{await post('/command',{type:'clipboard',action:'write',text:clipCheck($('clipboard-text').value)});clipStatus('Texte copié dans le presse-papiers du PC.');}
 catch(e){clipStatus(e.message);}
};
$('clip-copy-text').onclick=async()=>{
 try{await navigator.clipboard.writeText(clipCheck($('clipboard-text').value));clipStatus('Texte copié dans le presse-papiers de l’iPad.');}
 catch(e){clipStatus('Utilise un appui long dans la zone de texte, puis Sélectionner et Copier.');}
};
