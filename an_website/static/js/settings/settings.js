"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
function createBumpscositySlider(){const n=elById("bumpscosity-select");if(!n)return;n.classList.add("hidden");const o=[];for(const e of n.options)o.push(parseInt(e.value));const l=parseInt(n.value),s=document.createElement("div");s.setAttribute("tooltip",l.toString()),s.style.position="absolute",s.style.transform="translateX(-50%)";const t=document.createElement("input");t.setAttribute("type","range"),t.setAttribute("min","0"),t.setAttribute("value",o.indexOf(l).toString()),t.setAttribute("max",(n.options.length-1).toString()),t.onpointermove=()=>{const e=o[parseInt(t.value)].toString();n.value=e,s.setAttribute("tooltip",e),s.classList.add("show-tooltip"),s.style.left=(1+98*parseInt(t.value)/(n.options.length-1)).toString()+"%"},t.onpointerleave=()=>s.classList.remove("show-tooltip"),t.onchange=()=>{let e=parseInt(t.value);const r=`Willst du die Bumpscosity wirklich auf ${o[e]} setzen? `;if(e===n.options.length-1)confirm(r+"Ein so hoher Wert kann katastrophale Folgen haben.")||e--;else if(e===0)confirm(r+"Fehlende Bumpscosity kann großes Unbehagen verursachen.")||e++;else return;e!==parseInt(t.value)&&(t.value=e.toString(),n.value=o[parseInt(t.value)].toString())};const i=n.parentElement;i.style.position="relative",i.append(s),i.append(t)}createBumpscositySlider();// @license-end
//# sourceMappingURL=settings.js.map
