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

"""The tests for the backdoor."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Callable
from io import StringIO
from multiprocessing import Pipe, Process, connection
from typing import Any

import tornado.httpclient

import an_website.backdoor.backdoor_client as bc
from an_website.backdoor.backdoor import PrintWrapper

from . import app

assert app


def _run_and_get_output(
    conn: connection.Connection,
    fun: Callable[[Any], Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Run a function with the arguments and get the printed output."""
    output = StringIO()
    fun_out = fun(*args, print=PrintWrapper(output), **kwargs)  # type: ignore
    conn.send((fun_out, output.getvalue()))
    conn.close()


async def run_and_get_output(
    fun: Callable[..., Any], *args: Any, **kwargs: Any
) -> tuple[Any, str]:
    """Run a function with the arguments and get the printed output."""
    parent_conn, child_conn = Pipe()
    process = Process(
        target=_run_and_get_output,
        args=(child_conn, fun, *args),
        kwargs=kwargs,
    )
    process.start()
    await asyncio.sleep(1)
    text = parent_conn.recv()
    process.join()
    return text  # type: ignore


# pylint: disable=too-many-arguments
async def assert_run_and_print(
    url: str,
    command: str,
    *output: str,
    lisp: bool = False,
    session: str = "69",
    assertion: None | Callable[[str], bool] = None,
) -> None:
    """Test the run_and_print function."""
    real_output = await run_and_get_output(
        bc.run_and_print,
        url,
        "xyzzy",
        command,
        lisp,
        session,
    )
    assert len(real_output) == 2
    assert real_output[0] is None
    assert isinstance(real_output[1], str)
    assert real_output[1].endswith("\n")
    if assertion:
        assert assertion(real_output[1])
    elif output:
        output_str = "\n".join(output + ("",))
        assert real_output[1] == output_str


def get_error_assertion(error_line: str) -> Callable[[str], bool]:
    """Get the assertion lambda needed for asserting errors with the client."""
    return lambda spam: (
        spam.startswith(
            "Success: False\n" "Traceback (most recent call last):\n"
        )
        and spam.endswith(error_line + "\n")
    )


async def test_backdoor(  # pylint: disable=unused-argument
    http_client: tornado.httpclient.AsyncHTTPClient,
    http_server: Any,
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test the backdoor client."""
    assert bc.E == ...
    assert bc.lisp_always_active() in {True, False}

    url = f"http://127.0.0.1:{http_server_port[1]}"

    await assert_run_and_print(
        url,
        "1 1",
        'File "<unknown>", line 1',
        "    1 1",
        "      ^",
        "SyntaxError: invalid syntax",
    )
    await assert_run_and_print(
        url,
        "return 42",
        assertion=get_error_assertion("SyntaxError: 'return' outside function"),
    )
    await assert_run_and_print(
        url,
        "LOLWUT",
        assertion=get_error_assertion(
            "NameError: name 'LOLWUT' is not defined"
        ),
    )
    await assert_run_and_print(
        url,
        "0 / 0",
        assertion=get_error_assertion("ZeroDivisionError: division by zero"),
    )
    await assert_run_and_print(
        url,
        "1 + 1",
        "Success: True",
        "Result:",
        "2",
    )
    await assert_run_and_print(
        url,
        "(+ 1 1)",
        "Success: True",
        "Result:",
        "2",
        lisp=True,
    )
    await assert_run_and_print(
        url,
        "_",
        "Success: True",
        "Result:",
        "2",
    )
    await assert_run_and_print(
        url,
        "app.settings['TRUSTED_API_SECRETS']['xyzzy']",
        "Success: True",
        "Result:",
        "<Permissions.UPDATE|BACKDOOR|TRACEBACK|RATELIMITS: 15>",
    )
    await assert_run_and_print(
        url,
        "app.settings['TRUSTED_API_SECRETS'].get('')",
        "Success: True",
    )
    await assert_run_and_print(
        url,
        "print('42')",
        "Success: True",
        "Output:",
        "42",
    )
    await assert_run_and_print(
        url,
        "help",
        "Success: True",
        "Result:",
        "Type help() for interactive help, or help(object) for help about object.",
    )
    await assert_run_and_print(
        url,
        "print",
        "Success: True",
        "Result:",
        "<built-in function print>",
    )
    await assert_run_and_print(
        "https://example.org",
        "1 + 1",
        "\x1b[91m404 Not Found\x1b[0m",
    )
