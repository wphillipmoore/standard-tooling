"""Tests for standard_tooling.lib.registry."""

from __future__ import annotations

import json
from unittest.mock import patch

from standard_tooling.lib.registry import (
    RegistryVersion,
    crates_latest,
    go_proxy_latest,
    lookup,
    maven_latest,
    pypi_latest,
)

_URLOPEN = "standard_tooling.lib.registry.urllib.request.urlopen"


class _FakeResponse:
    """Minimal file-like object for urllib responses."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass


def test_pypi_latest_success() -> None:
    body = json.dumps({"info": {"version": "2.1.0"}}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = pypi_latest("my-package")
    assert result == RegistryVersion(
        name="my-package",
        version="2.1.0",
        registry="PyPI",
    )


def test_pypi_latest_network_error() -> None:
    with patch(_URLOPEN, side_effect=OSError("timeout")):
        assert pypi_latest("bad-package") is None


def test_go_proxy_latest_success() -> None:
    body = json.dumps({"Version": "v1.5.3"}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = go_proxy_latest("github.com/acme/tool")
    assert result == RegistryVersion(
        name="github.com/acme/tool",
        version="v1.5.3",
        registry="Go proxy",
    )


def test_go_proxy_latest_network_error() -> None:
    with patch(_URLOPEN, side_effect=OSError("404")):
        assert go_proxy_latest("github.com/acme/missing") is None


def test_crates_latest_success() -> None:
    body = json.dumps({"crate": {"max_stable_version": "0.5.2"}}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = crates_latest("my-crate")
    assert result == RegistryVersion(
        name="my-crate",
        version="0.5.2",
        registry="crates.io",
    )


def test_crates_latest_network_error() -> None:
    with patch(_URLOPEN, side_effect=OSError("timeout")):
        assert crates_latest("bad-crate") is None


def test_maven_latest_returns_none() -> None:
    assert maven_latest("some-artifact") is None


def test_lookup_python() -> None:
    body = json.dumps({"info": {"version": "3.0.0"}}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = lookup("Python", "acme", "my-lib")
    assert result is not None
    assert result.registry == "PyPI"
    assert result.version == "3.0.0"


def test_lookup_go() -> None:
    body = json.dumps({"Version": "v0.2.1"}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = lookup("Go", "acme", "my-tool")
    assert result is not None
    assert result.registry == "Go proxy"


def test_lookup_java_deferred() -> None:
    assert lookup("Java", "acme", "my-app") is None


def test_lookup_rust() -> None:
    body = json.dumps({"crate": {"max_stable_version": "1.0.0"}}).encode()
    with patch(_URLOPEN, return_value=_FakeResponse(body)):
        result = lookup("Rust", "acme", "my-crate")
    assert result is not None
    assert result.registry == "crates.io"
    assert result.version == "1.0.0"


def test_lookup_unknown_language() -> None:
    assert lookup("Haskell", "acme", "my-lib") is None


def test_lookup_empty_language() -> None:
    assert lookup("", "acme", "repo") is None
