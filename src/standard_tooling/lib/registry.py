"""Package registry HTTP lookups (PyPI, Go proxy, crates.io)."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass
class RegistryVersion:
    """Latest version information from a package registry."""

    name: str
    version: str
    registry: str


def pypi_latest(package: str) -> RegistryVersion | None:
    """Return the latest PyPI version for *package*, or ``None`` on failure."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read())
        version: str = data["info"]["version"]
        return RegistryVersion(name=package, version=version, registry="PyPI")
    except Exception:  # noqa: BLE001
        return None


def go_proxy_latest(module: str) -> RegistryVersion | None:
    """Return the latest Go module version from the Go proxy, or ``None``."""
    url = f"https://proxy.golang.org/{module}/@latest"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read())
        version: str = data["Version"]
        return RegistryVersion(name=module, version=version, registry="Go proxy")
    except Exception:  # noqa: BLE001
        return None


def crates_latest(crate: str) -> RegistryVersion | None:
    """Return the latest crates.io version for *crate*, or ``None`` on failure."""
    url = f"https://crates.io/api/v1/crates/{crate}"
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "User-Agent": "standard-tooling (https://github.com/wphillipmoore/standard-tooling)"
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read())
        version: str = data["crate"]["max_stable_version"]
        return RegistryVersion(name=crate, version=version, registry="crates.io")
    except Exception:  # noqa: BLE001
        return None


def maven_latest(_artifact: str) -> RegistryVersion | None:
    """Maven Central lookup — deferred (needs group:artifact, can't infer)."""
    return None


def lookup(language: str, owner: str, repo: str) -> RegistryVersion | None:
    """Infer the registry from *language* and look up the latest version."""
    lang = language.lower() if language else ""
    if lang == "python":
        return pypi_latest(repo)
    if lang == "go":
        return go_proxy_latest(f"github.com/{owner}/{repo}")
    if lang == "rust":
        return crates_latest(repo)
    if lang == "java":
        return maven_latest(repo)
    return None
