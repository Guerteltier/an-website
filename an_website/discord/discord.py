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

"""A permanent redirect to an invite of the Discord guild."""
from __future__ import annotations

import time
from typing import Union

import orjson as json
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo

GUILD_ID = 367648314184826880


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/discord/", ANDiscord),
            (f"/discord/({GUILD_ID})/", ANDiscord),
            (r"/discord/(\d+)/", Discord),
            (r"/discord/api/", ANDiscordAPI),
            (f"/discord/api/({GUILD_ID})/", ANDiscordAPI),
            (r"/discord/api/(\d+)/", DiscordAPI),
        ),
        name="Discord-Einladung",
        description="Eine permanente Einladung zu unserer Discord-Gilde",
        path="/discord/",
        keywords=(
            "Discord",
            "Server",
            "Gilde",
            "Invite",
            "Einladung",
        ),
    )


HTTP_CLIENT = AsyncHTTPClient()


async def url_returns_200(url: str) -> bool:
    """Check whether a url returns a status code of 200."""
    response = await HTTP_CLIENT.fetch(url, raise_error=False)
    return response.code == 200


async def get_invite(guild_id: int = GUILD_ID) -> tuple[str, str]:
    """
    Get the invite to a Discord guild and return it with the source.

    How to get the invite:
        - from the widget (has to be enabled in guild settings)
        - from disboard (the guild needs to set it up first)
    If the invite couldn't be fetched a HTTPError is thrown.
    """
    reason = "Invite not found."

    # try getting the invite from the widget
    url = f"https://discord.com/api/guilds/{guild_id}/widget.json"
    response = await HTTP_CLIENT.fetch(url, raise_error=False)
    if response.code == 200:
        response_json = json.loads(response.body.decode("utf-8"))
        invite = response_json["instant_invite"]
        if invite is not None:
            return invite, url
        reason = f"No instant invite in widget ({url}) found."

    # try getting the invite from disboard
    url = f"https://disboard.org/site/get-invite/{guild_id}"
    response = await HTTP_CLIENT.fetch(url, raise_error=False)
    if response.code == 200:
        return (
            json.loads(response.body.decode("utf-8")),
            f"https://disboard.org/server/{guild_id}",
        )

    # check if top.gg lists the guild
    url = f"https://top.gg/servers/{guild_id}/join"
    if await url_returns_200(url):
        return url, f"https://top.gg/servers/{guild_id}/"

    # check if discords.com lists the guild
    if await url_returns_200(
        # API endpoint that only returns 200 if the guild exists
        f"https://discords.com/api-v2/server/{guild_id}/relevant"
    ):
        return (
            f"https://discords.com/servers/{guild_id}/join",
            f"https://discords.com/servers/{guild_id}/",
        )

    raise HTTPError(404, reason=reason)


invite_cache: dict[
    int,
    Union[
        tuple[float, str, str],
        tuple[float, HTTPError],
    ],
] = {}


async def get_invite_with_cache(
    guild_id: int = GUILD_ID,
) -> tuple[str, str]:
    """Get an invite from cache or from get_invite()."""
    if guild_id in invite_cache:
        _t = invite_cache[guild_id]
        if _t[0] > time.time() - 30 * 60:  # if in last 30 min
            if isinstance(_t[1], HTTPError):
                raise _t[1]
            if len(_t) == 3:
                return _t[1], _t[2]

    try:
        invite, source = await get_invite(guild_id)
    except HTTPError as _e:
        invite_cache.__setitem__(guild_id, (time.time(), _e))
        raise _e

    invite_cache.__setitem__(guild_id, (time.time(), invite, source))

    return invite, source


class Discord(BaseRequestHandler):
    """The request handler that gets the Discord invite and redirects to it."""

    RATELIMIT_NAME = "discord"
    RATELIMIT_TOKENS = 10

    async def get(self, guild_id=GUILD_ID):
        """Get the Discord invite."""
        return await self.render(
            "pages/ask_for_redirect.html",
            redirect_url=(await get_invite_with_cache(guild_id))[0],
            from_url=None,
        )


class ANDiscord(Discord):
    """The request handler only for the AN Discord guild."""

    RATELIMIT_NAME = "discord-an"
    RATELIMIT_TOKENS = 4


class DiscordAPI(APIRequestHandler):
    """The API request handler that gets the Discord invite and returns it."""

    RATELIMIT_NAME = "discord"
    RATELIMIT_TOKENS = 9

    async def get(self, guild_id=GUILD_ID):
        """Get the Discord invite and render it as JSON."""
        invite, source_url = await get_invite_with_cache(guild_id)
        await self.finish({"invite": invite, "source": source_url})


class ANDiscordAPI(DiscordAPI):
    """The API request handler only for the AN Discord guild."""

    RATELIMIT_NAME = "discord-an"
    RATELIMIT_TOKENS = 4
