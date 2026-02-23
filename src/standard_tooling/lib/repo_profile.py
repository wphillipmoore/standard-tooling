"""Parse ``docs/repository-standards.md`` for repository profile data."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from pathlib import Path

PROFILE_FILENAME = "docs/repository-standards.md"

REQUIRED_FIELDS = (
    "repository_type",
    "versioning_scheme",
    "branching_model",
    "release_model",
    "supported_release_lines",
    "primary_language",
)

_FIELD_RE = re.compile(r"^[\s-]*(\w+):\s*(.+)$")
_COAUTHOR_RE = re.compile(r"^-\s*(Co-Authored-By:\s*.+)$", re.IGNORECASE)


@dataclass
class RepoProfile:
    """Parsed repository profile attributes."""

    repository_type: str = ""
    versioning_scheme: str = ""
    branching_model: str = ""
    release_model: str = ""
    supported_release_lines: str = ""
    primary_language: str = ""


def profile_path(root: Path | None = None) -> Path:
    """Return the profile file path relative to *root* (or cwd)."""
    base = root or Path.cwd()
    return base / PROFILE_FILENAME


def read_profile(root: Path | None = None) -> RepoProfile:
    """Read and return the repository profile from *root*."""
    path = profile_path(root)
    if not path.is_file():
        msg = f"Repository profile not found at {path}"
        raise FileNotFoundError(msg)

    profile = RepoProfile()
    valid_fields = {f.name for f in fields(profile)}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _FIELD_RE.match(line)
        if m and m.group(1) in valid_fields:
            setattr(profile, m.group(1), m.group(2).strip())
    return profile


def read_co_authors(root: Path | None = None) -> list[str]:
    """Return all ``Co-Authored-By`` identities from the profile."""
    path = profile_path(root)
    if not path.is_file():
        return []
    authors: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _COAUTHOR_RE.match(line)
        if m:
            authors.append(m.group(1))
    return authors


def resolve_co_author(agent: str, root: Path | None = None) -> str:
    """Return the ``Co-Authored-By`` line for *agent*.

    The agent name is matched against usernames containing ``-{agent}``
    (e.g. ``-claude``, ``-codex``).

    Raises ``SystemExit`` if no matching identity is found.
    """
    for identity in read_co_authors(root):
        if f"-{agent}" in identity.lower():
            return identity
    msg = (
        f"No approved identity found for agent '{agent}'. "
        f"Approved identities are listed under 'AI co-authors' in {PROFILE_FILENAME}."
    )
    raise SystemExit(msg)
