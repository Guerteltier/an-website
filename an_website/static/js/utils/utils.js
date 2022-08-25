"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
const elById=t=>document.getElementById(t);let lastLocation=String(window.location);function getLastLocation(){return lastLocation}function setLastLocation(t){lastLocation=t}function post(t,o={},n=console.log,e=console.error){fetch(t,{method:"POST",body:JSON.stringify(o),headers:{Accept:"application/json","Content-Type":"application/json"}}).then(a=>a.json()).catch(e).then(n).catch(e)}function get(t,o={},n=console.log,e=console.error){o&&(t+="?"+new URLSearchParams(o).toString()),fetch(t,{method:"GET",headers:{Accept:"application/json"}}).then(a=>a.json()).catch(e).then(n).catch(e)}const PopStateHandlers={replaceURL:t=>{lastLocation===t.origin||window.location.reload()},URLParamChange:()=>window.location.reload()};function setURLParam(t,o,n,e="URLParamChange",a=!0){const c=new URLSearchParams(window.location.search);c.set(t,o);const i=`${window.location.origin}${window.location.pathname}?${c.toString()}`;return n.stateType=e,a&&i!==window.location.href?history.pushState(n,i,i):history.replaceState(n,i,i),lastLocation=window.location.href,i}function scrollToId(){if(window.location.hash==="")return;const t=elById("header");if(!t)return;const o=document.querySelector(window.location.hash);!o||window.scrollBy(0,o.getBoundingClientRect().top-Math.floor(parseFloat(getComputedStyle(t).height)))}setTimeout(scrollToId,4),window.onhashchange=scrollToId,window.onpopstate=t=>{if(lastLocation.split("#")[0]===window.location.href.split("#")[0]){lastLocation=window.location.href,scrollToId();return}if(t.state&&t.state.stateType&&PopStateHandlers[t.state.stateType]){PopStateHandlers[t.state.stateType](t),lastLocation=window.location.href,t.preventDefault(),scrollToId();return}console.error("Couldn't handle state. ",t.state),lastLocation=window.location.href,window.location.reload()};// @license-end
//# sourceMappingURL=utils.js.map
