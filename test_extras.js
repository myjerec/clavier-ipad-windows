const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const storage=new Map();
function setup(){
 const elements=new Map(),commands=[];
 const element=()=>({children:[],value:'',checked:false,hidden:false,textContent:'',append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},addEventListener(){},setAttribute(){},focus(){},scrollIntoView(){}});
 const $=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
 const document={createElement:element,createTextNode:t=>({textContent:t}),querySelectorAll:q=>$('favorite-mods').children.map(l=>l.children[0]).filter(b=>!q.includes(':checked')||b.checked)};
 let next=0;
 const context=vm.createContext({$,document,localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},newDraftId:()=>String(++next),clearMods(){},send:c=>commands.push(c),button(parent,label,action){const b=element();b.textContent=label;b.onclick=action;parent.append(b);return b;}});
 vm.runInContext(fs.readFileSync(__dirname+'/extras.js','utf8'),context);
 return {$,context,commands};
}
let app=setup();
app.$('add-phrase').onclick();app.$('favorite-name').value='Bonjour';app.$('favorite-text').value='Bonjour été 😀';
app.$('favorite-editor').onsubmit({preventDefault(){}});
assert.equal(JSON.parse([...storage.values()][0])[0].text,'Bonjour été 😀');
app=setup();app.$('favorites-grid').children[0].children[0].onclick();assert.equal(app.commands[0].text,'Bonjour été 😀');
app.$('manage-favorites').onclick();app.$('favorites-grid').children[0].children[1].children[0].onclick();app.$('favorite-name').value='Salut';app.$('favorite-editor').onsubmit({preventDefault(){}});
assert.equal(JSON.parse([...storage.values()][0])[0].name,'Salut');
app.$('favorites-grid').children[0].children[1].children[1].onclick();assert.equal(JSON.parse([...storage.values()][0]).length,0);
app.$('favorites-grid').children.at(-1).onclick();assert.equal(JSON.parse([...storage.values()][0]).length,1);
app.$('add-shortcut').onclick();app.$('favorite-name').value='Sauver';app.$('favorite-key').value='S';app.$('favorite-mods').children[0].children[0].checked=true;app.$('favorite-editor').onsubmit({preventDefault(){}});
app.$('favorites-grid').children[1].children[0].onclick();assert.equal(app.commands.at(-1).key,'S');assert.equal(app.commands.at(-1).mods[0],'Ctrl');
app.$('apps-grid').children[1].onclick();assert.equal(app.commands.at(-1).app,'discord');
app.$('media-grid').children[0].onclick();assert.equal(app.commands.at(-1).action,'volume_down');
assert.equal(vm.runInContext("validFavorite({id:'x',kind:'shortcut',name:'bad',key:'Delete',mods:['Ctrl','Alt']})",app.context),false);
console.log('PASS: create/edit/delete/undo favorites, persistence/reload, text and shortcut dispatch, app/media buttons and forbidden chord validation.');
