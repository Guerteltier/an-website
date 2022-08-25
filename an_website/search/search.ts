// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt GNU-AGPL-3.0-or-later
"use strict";

(() => {
    const resultsList = elById("search-results") as HTMLElement;
    const searchForm = elById("search-form") as HTMLFormElement;
    const searchInput = elById("search-input") as HTMLInputElement;

    function displayResults(results: Iterable<any>) {
        resultsList.innerHTML = "";
        for (const result of results) {
            const resultElement = document.createElement("li");
            resultElement.setAttribute("score", String(result["score"]));
            resultElement.innerHTML = `<a href='${result.url}'>` +
                `${result.title}</a> ${result.description}`;
            resultsList.appendChild(resultElement);
        }
    }

    PopStateHandlers["search"] = (event: PopStateEvent) => {
        searchInput.value = event.state["query"];
        displayResults(event.state["results"]);
    };

    searchForm.onsubmit = (e: Event) => {
        e.preventDefault();
        get("/api/suche", "q=" + searchInput.value, (data) => {
            displayResults(data);
            setURLParam(
                "q",
                searchInput.value,
                { query: searchInput.value, results: data },
                "search",
                true,
            );
        });
    };
})();
// @license-end
