"use strict";// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
const bodyDiv=elById("body");let urlData={};const lastLoaded=[];function dynLoadOnData(e,t){if(!e){console.error("No data received");return}if(e.redirect){window.location.href=e.redirect;return}const o=e.url;if(!o){console.error("No URL in data ",e);return}if(console.log("Handling data",e),!t){if(lastLoaded.length===1&&lastLoaded[0]===o){console.log("URL is the same as last loaded, ignoring");return}history.pushState({data:e,url:o,stateType:"dynLoad"},e.title,o),lastLocation=o}if(!e.body){window.location.reload();return}if(document.onkeydown=()=>{},bodyDiv.innerHTML=e.body,e.css){const n=document.createElement("style");n.innerHTML=e.css,bodyDiv.appendChild(n)}if(e.stylesheets)for(const n of e.stylesheets){const i=document.createElement("link");i.rel="stylesheet",i.type="text/css",i.href=n,bodyDiv.appendChild(i)}if(e.scripts)for(const n of e.scripts)if(n.src){const i=document.createElement("script");i.src=n.src,bodyDiv.appendChild(i)}else console.error("Script without src",n);window.hideSitePane&&hideSitePane(),document.title=e.title;const r=elById("title");return r&&(r.setAttribute("short_title",e.short_title||e.title),r.innerText=e.title),dynLoadReplaceAnchors(),urlData=e,!0}function dynLoadReplaceAnchors(){for(const e of document.getElementsByTagName("A"))dynLoadReplaceHrefOnAnchor(e)}function dynLoadReplaceHrefOnAnchor(e){e.hasAttribute("no-dynload")||dynLoadFixHref(e)}function dynLoadFixHref(e){if(e.target==="_blank")return;const t=(e.href.startsWith("/")?window.location.origin+e.href:e.href).trim(),o=t.split("?")[0];!t.startsWith(window.location.origin)||(o.split("/").pop()||"").includes(".")&&o!==window.location.origin+"/redirect"||o===window.location.origin+"/chat"||t.startsWith("#")||t.startsWith(window.location.href.split("#")[0]+"#")||(e.onclick=r=>{dynLoad(t),r.preventDefault()})}function dynLoad(e){console.log("Loading URL",e),history.replaceState({data:urlData,url:window.location.href,scrollPos:[document.documentElement.scrollLeft||document.body.scrollLeft,document.documentElement.scrollTop||document.body.scrollTop],stateType:"dynLoad"},document.title,window.location.href),dynLoadSwitchToURL(e)}function dynLoadSwitchToURL(e,t=!1){if(!t&&e===window.location.href){console.log("URL is the same as current, just hide site pane"),window.hideSitePane&&hideSitePane();return}bodyDiv.prepend("Laden... Wenn dies zu lange (über ein paar Sekunden) dauert, lade bitte die Seite neu."),get(e,"",o=>dynLoadOnData(o,!1),o=>{console.log(o),e===window.location.href?window.location.reload():window.location.href=e},"application/vnd.asozial.dynload+json")}function dynLoadOnPopState(e){if(e.state){const t=e.state;if(console.log("Popstate",t),e.state.data&&dynLoadOnData(t,!0)||dynLoadSwitchToURL(t.url||window.location.href,!0),t.scrollPos){window.scrollTo(t.scrollPos[0],t.scrollPos[1]);return}}console.error("Couldn't handle state. ",e.state),window.location.reload()}PopStateHandlers.dynLoad=dynLoadOnPopState,dynLoadReplaceAnchors();// @license-end
//# sourceMappingURL=dynload.js.map
