'use strict';
// Favorites stay in this Safari origin; no clipboard or file upload is required.
const favoriteStorage='clavier-ipad-favorites-v1';
const favoriteKeys=[...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',...Array.from({length:12},(_,i)=>'F'+(i+1)),'Tab','Esc','Enter','Backspace','Delete','Space','Left','Up','Right','Down','Home','End','PageUp','PageDown','Insert','PrintScreen'];
const favoriteModifiers=['Ctrl','Alt','Shift','Win','AltGr'];
let favorites=[],editingFavorite=null,editorKind='shortcut',managingFavorites=false,removedFavorite=null;
function validFavorite(item){return item&&typeof item.id==='string'&&item.id.length<=80&&typeof item.name==='string'&&item.name.trim().length>0&&item.name.length<=40&&((item.kind==='text'&&typeof item.text==='string'&&item.text.length>0&&item.text.length<=2000)||(item.kind==='shortcut'&&favoriteKeys.includes(item.key)&&Array.isArray(item.mods)&&item.mods.length<=5&&new Set(item.mods).size===item.mods.length&&item.mods.every(m=>favoriteModifiers.includes(m))&&!(item.key==='Delete'&&item.mods.includes('Ctrl')&&item.mods.includes('Alt'))));}
try{const saved=JSON.parse(localStorage.getItem(favoriteStorage)||'[]');if(Array.isArray(saved))favorites=saved.filter(validFavorite).slice(0,40);}catch(e){$('favorites-status').textContent='Stockage indisponible ou illisible : tes nouveaux boutons resteront utilisables pendant cette session.';}
function persistFavorites(){try{localStorage.setItem(favoriteStorage,JSON.stringify(favorites));return true;}catch(e){$('favorites-status').textContent='Safari ne peut pas enregistrer ces boutons : ils restent disponibles pendant cette session seulement.';return false;}}
function keepNativeFocus(b){b.addEventListener('pointerdown',e=>{if(document.activeElement===$('text'))e.preventDefault();});return b;}
for(const [name,app,caption] of [['Navigateur','browser','Google · navigateur par défaut'],['Discord','discord','Discuter'],['Bloc-notes','notepad','Écrire'],['Explorateur','explorer','Mes fichiers'],['Calculatrice','calculator','Calculer'],['Paint','paint','Dessiner']])keepNativeFocus(button($('apps-grid'),name,()=>send({type:'app',app}),caption));
for(const [name,action,caption] of [['Volume −','volume_down','Baisser le son'],['Volume +','volume_up','Monter le son'],['Muet / son','mute','Activer ou couper'],['Lecture / Pause','play_pause','Lecteur actif'],['Précédent','previous','Piste précédente'],['Suivant','next','Piste suivante'],['Arrêter','stop','Stop lecture']])keepNativeFocus(button($('media-grid'),name,()=>send({type:'media',action}),caption));
for(const mod of favoriteModifiers){const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.value=mod;label.append(input,document.createTextNode(mod==='Shift'?'Maj':mod));$('favorite-mods').append(label);}
for(const key of favoriteKeys){const option=document.createElement('option');option.value=key;option.textContent=key;$('favorite-key').append(option);}
function showFavoriteEditor(kind,item){
 editorKind=kind;editingFavorite=item?item.id:null;
 $('favorite-editor').hidden=false;$('shortcut-fields').hidden=kind!=='shortcut';$('phrase-fields').hidden=kind!=='text';
 $('editor-title').textContent=(item?'Modifier':'Créer')+(kind==='text'?' un texte favori':' un raccourci');
 $('favorite-name').value=item?item.name:'';$('favorite-text').value=item&&kind==='text'?item.text:'';$('favorite-key').value=item&&kind==='shortcut'?item.key:'C';
 document.querySelectorAll('#favorite-mods input').forEach(box=>{box.checked=!!(item&&item.mods&&item.mods.includes(box.value));});
 $('favorite-name').focus();$('favorite-editor').scrollIntoView({block:'nearest'});
}
function renderFavorites(){
 $('favorites-grid').replaceChildren();
 if(!favorites.length){const p=document.createElement('p');p.textContent='Ajoute tes raccourcis et tes phrases habituelles avec les boutons ci-dessus.';$('favorites-grid').append(p);}
 for(const item of favorites){
  const card=document.createElement('div');card.className='favorite-card';
  const caption=item.kind==='text'?item.text.slice(0,65):(item.mods.length?item.mods.join(' + ')+' + ':'')+item.key;
  keepNativeFocus(button(card,item.name,()=>{clearMods();send(item.kind==='text'?{type:'text',text:item.text}:{type:'key',key:item.key,mods:[...item.mods]});},caption));
  if(managingFavorites){const actions=document.createElement('div');actions.className='favorite-actions';button(actions,'Modifier',()=>showFavoriteEditor(item.kind,item));button(actions,'Supprimer',()=>{removedFavorite={item,index:favorites.findIndex(f=>f.id===item.id)};favorites=favorites.filter(f=>f.id!==item.id);persistFavorites();renderFavorites();});card.append(actions);}
  $('favorites-grid').append(card);
 }
 if(removedFavorite){button($('favorites-grid'),'Annuler la suppression',()=>{if(favorites.length>=40){$('favorites-status').textContent='40 boutons maximum.';return;}favorites.splice(removedFavorite.index,0,removedFavorite.item);removedFavorite=null;persistFavorites();renderFavorites();});}
}
$('add-shortcut').onclick=()=>showFavoriteEditor('shortcut');$('add-phrase').onclick=()=>showFavoriteEditor('text');
$('manage-favorites').onclick=()=>{managingFavorites=!managingFavorites;$('manage-favorites').setAttribute('aria-pressed',String(managingFavorites));renderFavorites();};
$('cancel-favorite').onclick=()=>{$('favorite-editor').hidden=true;editingFavorite=null;};
$('favorite-editor').onsubmit=e=>{
 e.preventDefault();
 const item={id:editingFavorite||newDraftId(),name:$('favorite-name').value.trim(),kind:editorKind};
 if(editorKind==='text')item.text=$('favorite-text').value;
 else{item.key=$('favorite-key').value;item.mods=Array.from(document.querySelectorAll('#favorite-mods input:checked'),box=>box.value);}
 if(!validFavorite(item)){$('favorites-status').textContent='Vérifie le nom, le texte ou la combinaison. Ctrl+Alt+Suppr est réservé à Windows.';return;}
 if(!editingFavorite&&favorites.length>=40){$('favorites-status').textContent='40 boutons maximum. Supprime un bouton pour en ajouter un.';return;}
 if(editingFavorite)favorites=favorites.map(f=>f.id===editingFavorite?item:f);else favorites.push(item);
 const saved=persistFavorites();renderFavorites();$('favorite-editor').hidden=true;editingFavorite=null;
 if(saved)$('favorites-status').textContent='Bouton enregistré sur cet iPad.';
};
renderFavorites();

for(const row of [['7','8','9','÷'],['4','5','6','×'],['1','2','3','−'],['0',',','.','+'],['(',')','⌫','Entrée']]){
 for(const label of row)keepNativeFocus(button($('numeric-grid'),label,()=>{
  clearMods();
  if(label==='⌫'||label==='Entrée')send({type:'key',key:label==='⌫'?'Backspace':'Enter',mods:[]});
  else send({type:'text',text:({'÷':'/','×':'*','−':'-'})[label]||label});
 }));
}
for(const [label,key,mods] of [
 ['Nouvel onglet','T',['Ctrl']],['Rouvrir l’onglet','T',['Ctrl','Shift']],['Onglet suivant','Tab',['Ctrl']],['Onglet précédent','Tab',['Ctrl','Shift']],
 ['Actualiser','F5',[]],['Barre d’adresse','L',['Ctrl']],['Imprimer…','P',['Ctrl']],['Enregistrer sous…','S',['Ctrl','Shift']],
 ['Explorateur Windows','E',['Win']],['Paramètres Windows','I',['Win']],['Vue des tâches','Tab',['Win']],['Capture de zone','S',['Win','Shift']]
])keepNativeFocus(button($('shortcuts'),label,()=>{clearMods();send({type:'key',key,mods});},[...mods,key].join(' + ')));
