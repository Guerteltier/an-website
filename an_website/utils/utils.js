// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
const w = window;
const d = document;
const elById = (id) => d.getElementById(id);
const log = console.log;
const error = console.error;

w.lastLocation = String(w.location);

function post(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    fetch(url, {
        method: "POST",
        body: JSON.stringify(params),
        headers: {"Accept": "application/json"}
    }).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

function get(
    url,
    params = {},
    ondata = log,
    onerror = error
) {
    // log("GET", url, params);
    fetch(
        url + (!params ? "" : "?" + (new URLSearchParams(params)).toString()),
        {
            method: "GET",
            headers: {"Accept": "application/json"}
        }
    ).then(response => response.json()).catch(onerror)
        .then(ondata).catch(onerror);
}

w.PopStateHandlers = {
    "replaceURL": (state) => {
        // reload if the last location was not the one that got replaced
        w.lastLocation === state["origin"] || w.location.reload();
    },
    // always reload the location if URLParamChange
    "URLParamChange": (s) => w.location.reload()
};

function setURLParam(
    param,
    value,
    state,
    stateType = "URLParamChange",
    push = true
) {
    //log("setURLParam", param, value, state, onpopstate);
    const urlParams = new URLSearchParams(w.location.search);
    urlParams.set(param, value);
    const newUrl = `${w.location.origin}${w.location.pathname}?${urlParams.toString()}`;
    //log("newUrl", newUrl);
    state["stateType"] = stateType;
    if (push && newUrl !== w.location) {
        history.pushState(state, newUrl, newUrl);
    } else {
        history.replaceState(state, newUrl, newUrl)
    }
    w.lastLocation = String(w.location);
    return newUrl;
}

w.yOffset = Math.floor(parseFloat(getComputedStyle(elById("header")).height));
function scrollToAnchor() {
    if (w.location.hash === "") return;
    const anchor = d.querySelector(w.location.hash);
    if (!anchor) return;
    w.scrollBy(0, anchor.getBoundingClientRect().top - w.yOffset);
}
// scroll after few ms so the scroll is right on page load
setTimeout(scrollToAnchor, 4);
w.onhashchange = scrollToAnchor;

w.onpopstate = (event) => {
    if (
        String(w.lastLocation).split("#")[0]
        === String(w.location).split("#")[0]
    ) {
        // Only hash changed
        w.lastLocation = String(w.location);
        scrollToAnchor();
        return;
    }
    if (
        event.state
        && event.state["stateType"]
        && w.PopStateHandlers[event.state["stateType"]]
    ) {
        w.PopStateHandlers[event.state["stateType"]](event);
        w.lastLocation = String(w.location);
        event.preventDefault();
        scrollToAnchor();
        return;
    }
    error("Couldn't handle state. ", event.state);
    w.lastLocation = String(w.location);
    w.location.reload();
}

function fixHref(href) {
    if (w.dynLoadGetFixedHref)
        return w.dynLoadGetFixedHref(href);
    // if the function doesn't exist don't change anything
    return href;
}

function showSitePane(show) {
    elById("site-pane").style.right = show ? "0" : "-70%";
}
// @license-end
