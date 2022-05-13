// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
(() => {
    const openPane = elById("open-pane");
    const body = elById("body");
    const sitePane = elById("site-pane");

    window.onscroll = () => {
        elById("header")
    }

    openPane.onclick = () => showSitePane(true);
    openPane.onmouseover = () => showSitePane(true);
    body.onmouseover = () => showSitePane(false);
    body.onclick = () => showSitePane(false);


    body.ontouchstart = startTouch;
    body.ontouchmove = (e) => moveTouch(
        e,
        () => showSitePane(true),
        () => showSitePane(false)
    );
    sitePane.ontouchstart = startTouch;
    sitePane.ontouchmove = (e) => moveTouch(
        e,
        null,
        () => showSitePane(false)
    );

    const startSwipePos = {x: null, y: null};

    function startTouch(e) {
        startSwipePos.x = e.touches[0].clientX;
        startSwipePos.y = e.touches[0].clientY;
    }

    function moveTouch(
        e,
        onSwipedLeft = null,
        onSwipedRight = null,
    ) {
        if (startSwipePos.x === null) return;
        if (startSwipePos.y === null) return;

        let currentX = e.touches[0].clientX;
        let currentY = e.touches[0].clientY;
        let diffX = startSwipePos.x - currentX;
        let diffY = startSwipePos.y - currentY;

        startSwipePos.x = null;
        startSwipePos.y = null;


        if (diffX === 0 && diffY === 0) return;

        if (Math.abs(diffX) > Math.abs(diffY)) {
            // sliding horizontally
            if (diffX > 0) {
                if (onSwipedLeft !== null) onSwipedLeft(diffX);
            } else {
                if (onSwipedRight !== null) onSwipedRight(diffX);
            }
            e.preventDefault();
        }
    }
})()
// @license-end
