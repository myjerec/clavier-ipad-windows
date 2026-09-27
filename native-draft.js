/* Pure draft rules shared by Safari and the regression tests. */
(function(root){
 'use strict';
 function nextDraft(value,sent,all){
  return {text:value,snapshot:value,changed:value!==sent};
 }
 if(typeof module!=='undefined')module.exports={nextDraft};
 else root.nextDraft=nextDraft;
})(globalThis);
