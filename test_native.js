 'use strict';
const assert=require('node:assert/strict');
const {nextDraft}=require('./native-draft.js');
assert.equal(nextDraft('B','',false).changed,true);
assert.equal(nextDraft('Bonjour','Bonjor',false).text,'Bonjour');
assert.equal(nextDraft('','B',false).changed,true);
assert.equal(nextDraft('été','été',false).changed,false);
const vm=require('node:vm'),fs=require('node:fs');
const elements=new Map(),requests=[],replies=[];
function element(){return {value:'',checked:true,disabled:false,textContent:'',listeners:{},classList:{toggle(){}},append(){},setAttribute(){},addEventListener(k,fn){this.listeners[k]=fn;},focus(){}};}
const document={documentElement:{style:{setProperty(){}}},hidden:false,getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element,querySelectorAll(){return [];},addEventListener(){}};
const context=vm.createContext({window:{innerHeight:768,setInterval(){},addEventListener(){}},crypto:require('node:crypto').webcrypto,document,AbortController,setTimeout:()=>1,clearTimeout(){},nextDraft,fetch:(path,options)=>new Promise(resolve=>{
 const data=JSON.parse(options.body);
 if(data.type==='status'){resolve({ok:true,json:async()=>({ok:true})});return;}
 requests.push(data);replies.push(()=>resolve({ok:true,json:async()=>({ok:true})}));
})});
vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8'),context);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();const input=elements.get('text');
 input.value='B';input.listeners.input({isComposing:false});await tick();
 assert.equal(requests.length,1);assert.equal(requests[0].text,'B');assert.equal(requests[0].type,'direct');
 input.value='Bonjor';input.listeners.input({isComposing:false});await tick();assert.equal(requests.length,1);
 replies.shift()();await tick();assert.equal(requests[1].text,'Bonjor');assert.equal(requests[1].base,'B');
 input.value='Bonjour';input.listeners.input({isComposing:false});replies.shift()();await tick();
 assert.equal(requests[2].text,'Bonjour');assert.equal(requests[2].base,'Bonjor');
 replies.shift()();await tick();assert.equal(requests.length,3);
 input.listeners.compositionstart();input.value='Bonjour été';input.listeners.input({isComposing:true});await tick();assert.equal(requests.length,3);
 input.listeners.compositionend();await tick();assert.equal(requests[3].text,'Bonjour été');replies.shift()();await tick();
 input.value='';input.listeners.input({isComposing:false});await tick();assert.equal(requests[4].text,'');
 replies.shift()();await tick();
 vm.runInContext("selected.add('Ctrl')",context);
 let prevented=false;
 input.listeners.beforeinput({inputType:'insertText',data:'c',cancelable:true,isComposing:false,preventDefault(){prevented=true;}});
 await tick();assert.equal(prevented,true);assert.equal(requests[5].key,'C');assert.equal(requests[5].mods[0],'Ctrl');
 replies.shift()();await tick();
 console.log('PASS: immediate first letter, coalesced in-flight typing, autocorrection, composition, deletion and no duplicates.');
})().catch(e=>{console.error(e);process.exitCode=1;});
