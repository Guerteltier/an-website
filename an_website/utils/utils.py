from __future__ import annotations, barry_as_FLUFL

import asyncio
import asyncio.subprocess
import logging
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado.web import HTTPError, RequestHandler

Handler = Union[
    Tuple[str, Any],
    Tuple[str, Any, Dict[str, Any]],
    Tuple[str, Any, Dict[str, Any], str],
]
HandlerTuple = Tuple[Handler, ...]


# sortable so the pages can be linked in a order
# frozen so it's immutable
@dataclass(order=True, frozen=True)
class PageInfo:
    name: str
    description: str
    path: Optional[str] = None


@dataclass(order=True, frozen=True)
class ModuleInfo(PageInfo):
    handlers: HandlerTuple = field(default_factory=HandlerTuple)
    sub_pages: Optional[Tuple[PageInfo, ...]] = None


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        "Utilitys",
        "Nütliche Werkzeuge für alle möglichen Sachen.",
        handlers=((r"/error/?", ZeroDivision),),
    )


def length_of_match(_m: re.Match):
    span = _m.span()
    return span[1] - span[0]


def n_from_set(_set: set, _n: int) -> set:
    i = 0
    new_set = set()
    for _el in _set:
        if i < _n:
            i += 1
            new_set.add(_el)
        else:
            break
    return new_set


def strtobool(val):
    """Convert a string representation of truth to True or False."""
    val = val.lower()
    if val in ("sure", "y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("nope", "n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError("invalid truth value %r" % (val,))


async def run(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=stdin,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    com = proc.communicate()
    if "ps -p" not in cmd:
        with open(f"/proc/{proc.pid}/stat") as file:
            print(file.read())
        await (run(f"ps -p {proc.pid} all | grep -E 'PID|{proc.pid}'"))

    stdout, stderr = await com

    if "ps -p" in cmd:
        logger = logging.getLogger(__name__)
        logger.error(
            str(
                {
                    "code": proc.returncode,
                    "stdout": stdout.decode("utf-8"),
                    "stderr": stderr.decode("utf-8"),
                }
            )
        )

    return proc.returncode, stdout, stderr


class BaseRequestHandler(RequestHandler):
    RATELIMIT_TOKENS = 1  # can be overridden in subclasses
    title = "Das Asoziale Netzwerk"
    description = "Die tolle Webseite des Asozialen Netzwerkes"

    def initialize(self, **kwargs):
        self.title = kwargs.get("title", self.title)
        self.description = kwargs.get("description", self.description)

    def data_received(self, chunk):
        pass

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        if not sys.flags.dev_mode and not self.request.method == "OPTIONS":
            now = datetime.utcnow()
            redis = self.settings.get("REDIS")
            prefix = self.settings.get("REDIS_PREFIX")
            tokens = getattr(
                self, "RATELIMIT_TOKENS_" + self.request.method, None
            )
            if tokens is None:
                tokens = self.RATELIMIT_TOKENS
            result = await redis.execute_command(
                "CL.THROTTLE",
                prefix + "ratelimit:" + self.request.remote_ip,
                15,  # max burst
                30,  # count per period
                60,  # period
                tokens,
            )
            self.set_header("X-RateLimit-Limit", result[1])
            self.set_header("X-RateLimit-Remaining", result[2])
            self.set_header("Retry-After", result[3])
            self.set_header("X-RateLimit-Reset", result[4])
            if result[0]:
                if now.month == 4 and now.day == 20:
                    self.set_status(420, "Enhance Your Calm")
                    self.write_error(420)
                else:
                    self.set_status(429)
                    self.write_error(429)

    def write_error(self, status_code, **kwargs):
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
        )

    def get_error_message(self, **kwargs):
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][:2])[-1]
        return self._reason

    def get_no_3rd_party(self) -> bool:
        return self.get_query_argument_as_bool("no_3rd_party", False)

    def get_template_namespace(self):
        namespace = super().get_template_namespace()
        no_3rd_party: bool = self.get_no_3rd_party()
        form_appendix: str = (
            "<input name='no_3rd_party' style='display: none;"
            + "width: 0; height: 0; opacity: 0' value='sure'>"
            if no_3rd_party
            else ""
        )
        namespace.update(
            {
                "ansi2html": Ansi2HTMLConverter(inline=True, scheme="xterm"),
                "title": self.title,
                "description": self.description,
                "no_3rd_party": no_3rd_party,
                "lang": "de",
                "url_appendix": "?no_3rd_party=sure" if no_3rd_party else "",
                "form_appendix": form_appendix,
                # this is not important because we don't need the templates
                # in a context without the request for soundboard and wiki
                "url": self.request.full_url(),
                "settings": self.settings,
            }
        )
        return namespace

    def get_query_argument_as_bool(self, name: str, default: bool = False):
        try:
            return strtobool(
                str(self.get_query_argument(name, default=str(default)))
            )
        except ValueError:
            return default


class APIRequestHandler(BaseRequestHandler):
    def write_error(self, status_code, **kwargs):
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    RATELIMIT_TOKENS = 0

    async def prepare(self):
        raise HTTPError(404)


class ZeroDivision(BaseRequestHandler):
    RATELIMIT_TOKENS = 10

    async def prepare(self):
        if not self.request.method == "OPTIONS":
            await super().prepare()
            self.finish(str(0 / 0))
