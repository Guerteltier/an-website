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

"""The tests for the token module."""

import binascii
from datetime import datetime

import pytest
import time_machine

from an_website.utils.token import (  # pylint: disable=import-private-name
    InvalidTokenError,
    InvalidTokenVersionError,
    _create_token_body_v0,
    _parse_token_v0,
    bytes_to_int,
    create_token,
    int_to_bytes,
    parse_token,
)
from an_website.utils.utils import Permission


@time_machine.travel(67, tick=False)
def test_token() -> None:
    """Test the token creation."""
    token = create_token(Permission(1), secret=b"xyzzy", duration=2)
    assert token.permissions == Permission(1)
    assert token.valid_until == datetime.fromtimestamp(69)  # nice
    assert token.permissions == Permission.RATELIMITS

    with time_machine.travel(70, tick=False), pytest.raises(InvalidTokenError):
        parse_token(token.token, secret=b"xyzzy")  # expired

    parsed = parse_token(token.token, secret="xyzzy")  # nosec: B106
    assert parsed.token == token.token
    assert parsed == token
    assert parsed == parse_token(token.token, secret=b"xyzzy")

    with pytest.raises(InvalidTokenError):
        parse_token(token.token, secret=b"abc", verify_time=False)

    with pytest.raises(InvalidTokenError):
        parse_token(token.token, secret=b"xyzzy ", verify_time=False)

    with pytest.raises(InvalidTokenError):
        parse_token(token.token[:50], secret=b"xyzzy", verify_time=False)

    with pytest.raises(InvalidTokenError):
        parse_token("", secret=b"a", verify_time=False)

    with pytest.raises(InvalidTokenError):
        parse_token("0", secret=b"b", verify_time=False)

    with pytest.raises(InvalidTokenError):
        parse_token("0👐", secret=b"c", verify_time=False)

    with pytest.raises(InvalidTokenVersionError):
        parse_token("1", secret=b"d", verify_time=False)


def test_token_v0() -> None:
    """Test the token creation."""
    result = create_token(
        Permission(1), secret=b"xyzzy", duration=9999, version="0"
    )
    assert result.permissions == Permission(1)
    token = _create_token_body_v0(
        Permission(20),
        b"xyzzy",
        100,
        datetime.fromtimestamp(0),
        b"\x00\x00\x00\x00\x00*",  # 42
    )
    assert (
        token == "ABQAAAAAACoAAAAAZAAAAAAAVuGjEJjux2P8zah"  # nosec: B105
        "9SjQGkxCWn9Iaszr/qJJHJSMWoRPoVjQKa6/jKFWPdBehSL0K"
    )

    parsed = _parse_token_v0(token, b"xyzzy", verify_time=False)
    assert parsed.salt == b"\x00\x00\x00\x00\x00*"
    assert parsed.permissions == Permission(20)
    assert parsed.valid_until == datetime.fromtimestamp(100)
    assert parsed.token == f"0{token}"
    parsed2 = parse_token(parsed.token, secret=b"xyzzy", verify_time=False)
    assert parsed == parsed2

    with pytest.raises(InvalidTokenError):
        _parse_token_v0(token, b"xyzzy")  # expired

    with pytest.raises(InvalidTokenError):
        parse_token("0" + token, secret=b"xyzzy")

    with time_machine.travel(67, tick=False):
        _parse_token_v0(token, b"xyzzy")
        parse_token("0" + token, secret=b"xyzzy")
        result = create_token(
            Permission(4), secret=b"xyzzy", duration=2, version="0"
        )
        assert result.valid_until == datetime.fromtimestamp(69)
        parsed = parse_token(result.token, secret=b"xyzzy")
        assert parsed.token == result.token
        assert parsed.token[0] == "0"

    with pytest.raises(InvalidTokenError):
        _parse_token_v0(token, b"hunter2", verify_time=False)

    with pytest.raises(
        InvalidTokenError,
        check=lambda exc: isinstance(exc.__cause__, ValueError),
    ):
        _parse_token_v0("🏳‍⚧", secret=b"e")

    with pytest.raises(
        InvalidTokenError,
        check=lambda exc: isinstance(exc.__cause__, binascii.Error),
    ):
        _parse_token_v0(" ", secret=b"empty")


def test_int_to_bytes() -> None:
    """Test the int to bytes conversion."""
    assert int_to_bytes(0, 2) == b"\0" * 2
    assert int_to_bytes(0x20, 2) == b"\0 "
    assert int_to_bytes(0x2000, 2) == b" \0"


def test_bytes_to_int() -> None:
    """Test the bytes to int conversion."""
    assert bytes_to_int(b"\0") == 0  # pylint: disable=compare-to-zero
    assert bytes_to_int(b" ") == 0x20
    assert bytes_to_int(b"  ") == 0x2020
    assert bytes_to_int(b" \0") == 0x2000

    with pytest.raises(ValueError):
        bytes_to_int(b"")
