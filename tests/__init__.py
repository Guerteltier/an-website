# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Utilities used by the tests of an-website."""

from __future__ import annotations

import configparser
import os
import socket
import sys
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any, cast

import orjson as json
import pytest
import tornado.httpclient
import tornado.web
from blake3 import blake3  # type: ignore[import]
from lxml import etree  # type: ignore[import]
from lxml.html import document_fromstring  # type: ignore[import]
from lxml.html.html5parser import HTMLParser  # type: ignore[import]

DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(DIR)

WRONG_QUOTE_DATA = {
    # https://zitate.prapsschnalinen.de/api/wrongquotes/1
    "id": 1,
    "author": {
        "id": 2,
        "author": "Kim Jong-il",
    },
    "quote": {
        "id": 1,
        "author": {
            "id": 1,
            "author": "Abraham Lincoln",
        },
        "quote": (
            "Frage nicht, was dein Land für dich tun kann, "
            "frage, was du für dein Land tun kannst."
        ),
    },
    "rating": 4,
    "showed": 216,
    "voted": 129,
}

# add parent dir to sys.path
# this makes importing an_website possible
sys.path.append(PARENT_DIR)

from an_website import main  # noqa  # pylint: disable=wrong-import-position
from an_website import quotes  # noqa  # pylint: disable=wrong-import-position
from an_website.patches import (  # noqa  # pylint: disable=wrong-import-position
    apply,
)
from an_website.utils.utils import (  # noqa  # pylint: disable=wrong-import-position
    ModuleInfo,
)

apply()

FetchCallable = Callable[..., Awaitable[tornado.httpclient.HTTPResponse]]


def get_module_infos() -> tuple[ModuleInfo, ...]:
    """Get module infos and fail if they are a string."""
    module_infos = main.get_module_infos()
    assert not isinstance(module_infos, str)
    assert isinstance(module_infos, tuple)
    return module_infos


@pytest.fixture
def app() -> tornado.web.Application:
    """Create the application."""
    app = main.make_app()  # pylint: disable=redefined-outer-name

    assert isinstance(app, tornado.web.Application)

    app.settings["debug"] = True

    config = configparser.ConfigParser(interpolation=None)
    config.read(os.path.join(DIR, "config.ini"))
    main.apply_config_to_app(app, config)

    return app


async def make_effective_url_relative(
    response: Awaitable[tornado.httpclient.HTTPResponse],
    host: str,
) -> tornado.httpclient.HTTPResponse:
    """Add effective_url_path to response."""
    _response = await response
    _response.effective_url_path = (  # type: ignore[attr-defined]
        _response.effective_url.removeprefix(host)
    )
    return _response


@pytest.fixture
def fetch(
    http_client: tornado.httpclient.AsyncHTTPClient,
    http_server_port: tuple[socket.socket, int],
) -> FetchCallable:
    """Fetch a URL."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)
    host = f"http://127.0.0.1:{http_server_port[1]}"
    return lambda url, **kwargs: make_effective_url_relative(
        http_client.fetch(
            url
            if url.startswith("http://") or url.startswith("https://")
            else f"{host}/{url.removeprefix('/')}",
            **{"raise_error": False, **kwargs},
        ),
        host,
    )


def assert_valid_redirect(
    response: tornado.httpclient.HTTPResponse,
    new_url: str,
) -> tornado.httpclient.HTTPResponse:
    """Assert a valid redirect to a new url."""
    effective_url_path = getattr(response, "effective_url_path", None)
    if effective_url_path:
        assert effective_url_path == new_url
    else:
        print("Effective URL path missing for", response.effective_url)
    assert response.effective_url.endswith(new_url)
    return response


def assert_valid_response(
    response: tornado.httpclient.HTTPResponse,
    content_type: None | str,
    code: int = 200,
    headers: None | dict[str, Any] = None,
) -> tornado.httpclient.HTTPResponse:
    """Assert a valid response with the given code and content type header."""
    url = response.effective_url
    assert response.code == code or print(url)

    headers = headers or {}
    if content_type is not None:
        headers["Content-Type"] = content_type

    for header, value in headers.items():
        assert response.headers[header] == value or print(
            url, response.headers, header, value
        )
    return response


async def check_html_page(
    _fetch: FetchCallable,
    url: str,
    code: int = 200,
    # pylint: disable=dangerous-default-value
    checked_urls: set[str] = set(),  # noqa: B006
) -> tornado.httpclient.HTTPResponse:
    """Check an html page."""
    response = await _fetch(url)
    assert_valid_html_response(response, code)
    html = document_fromstring(
        response.body.decode("utf-8"), base_url=response.effective_url
    )
    assert html.find("head") is not None or print("no head found", url)
    assert html.find("body") is not None or print("no body found", url)
    html.make_links_absolute(response.effective_url)
    eff_url = urllib.parse.urlsplit(response.effective_url)
    prot_and_host = f"{eff_url.scheme}://{eff_url.netloc}"
    found_ref_to_body = False
    for link_tuple in html.iterlinks():
        if link_tuple[2] == response.effective_url + "#body":
            found_ref_to_body = True
        link: str = link_tuple[2].removesuffix("#body")
        if (
            link.startswith(prot_and_host)
            and link not in checked_urls
            and not link.startswith(f"{prot_and_host}/LOLWUT")
            and response.effective_url != link
        ):
            checked_urls.add(link)
            _response = assert_valid_response(
                await _fetch(link), content_type=None
            )
            if link.startswith(f"{prot_and_host}/static/") or link.startswith(
                f"{prot_and_host}/soundboard/files/"
            ):
                assert "v=" in link
                file_hash = cast(str, blake3(_response.body).hexdigest(8))
                assert f"v={file_hash}" in link
    assert found_ref_to_body or print(url)
    return response


def assert_valid_html_response(
    response: tornado.httpclient.HTTPResponse,
    code: int = 200,
    effective_url: None | str = None,
) -> etree.ElementTree:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "text/html; charset=UTF-8", code)
    body = response.body.decode("utf-8")
    root: etree.ElementTree = HTMLParser(
        strict=True, namespaceHTMLElements=False
    ).parse(body)

    assert root.find("./head/link[@rel='canonical']").get("href").rstrip(
        "/"
    ) == (effective_url or response.effective_url).split("?")[0].rstrip("/")

    return root


def assert_valid_rss_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> etree.ElementTree:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "application/rss+xml", code)
    body = response.body
    parsed_xml: etree.ElementTree = etree.fromstring(
        body,
        parser=etree.XMLParser(recover=False, resolve_entities=False),
        base_url=response.request.url,
    )
    return parsed_xml


def assert_valid_json_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> Any:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "application/json; charset=UTF-8", code)
    parsed_json = json.loads(response.body)
    assert parsed_json is not None and len(parsed_json)
    return parsed_json
