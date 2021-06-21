from __future__ import barry_as_FLUFL

import asyncio
import asyncio.subprocess
import re
import traceback

from tornado.web import HTTPError, RequestHandler


def get_handlers():
    return ((r"/error/?", ZeroDivision),)


async def run_shell(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdin=stdin, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


async def run_exec(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_exec(
        cmd, stdin=stdin, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


def length_of_match(m: re.Match):  # pylint: disable=invalid-name
    span = m.span()
    return span[1] - span[0]


class BaseRequestHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def render_string(self, template_name, **kwargs):
        return super().render_string(
            template_name, **kwargs, url=self.get_url(), rum=self.get_rum()
        )

    def write_error(self, status_code, **kwargs):
        self.render(
            "error.html", code=status_code, message=self.get_error_message(**kwargs)
        )

    def get_error_message(self, **kwargs):
        if "exc_info" in kwargs and not issubclass(kwargs["exc_info"][0], HTTPError):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][0:2])[-1]
        return self._reason

    def get_url(self):
        """Dirty fix to force https"""
        return self.request.full_url().replace("http://joshix", "https://joshix")

    def get_rum(self):
        return f"""
        <script src="https://unpkg.com/@elastic/apm-rum@^5/dist/bundles/elastic-apm-rum.umd.min.js" crossorigin></script>
        <script>
          elasticApm.init({{
            active: {"true" if self.settings.get("ELASTIC_APM")["ENABLED"] else "false"},
            serverUrl: '{self.settings.get("ELASTIC_APM")["SERVER_URL"]}',
            serviceName: '{self.settings.get("ELASTIC_APM")["SERVICE_NAME"]}',
            serviceVersion: '{self.settings.get("ELASTIC_APM")["SERVICE_VERSION"]}',
            environment: '{self.settings.get("ELASTIC_APM")["ENVIRONMENT"]}',
          }})
        </script>
        """


class APIRequestHandler(BaseRequestHandler):
    def write_error(self, status_code, **kwargs):
        self.write({"status": status_code, "message": self.get_error_message(**kwargs)})


class NotFound(BaseRequestHandler):
    def prepare(self):
        raise HTTPError(404)


class ZeroDivision(BaseRequestHandler):
    def get(self):
        self.finish(0 / 0)
