"""Tests for standard_tooling.bin.markdown_standards."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.markdown_standards import (
    _classify_files,
    _run_markdownlint,
    _structural_check,
    main,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# -- _classify_files ---------------------------------------------------------


def test_classify_args_site_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    site = tmp_path / "docs" / "site"
    site.mkdir(parents=True)
    md = site / "index.md"
    md.write_text("# Hello\n")
    lint, struct = _classify_files(["docs/site/index.md"])
    assert lint == ["docs/site/index.md"]
    assert struct == []


def test_classify_args_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# Hello\n")
    lint, struct = _classify_files(["README.md"])
    assert lint == []
    assert struct == ["README.md"]


def test_classify_args_out_of_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    claude = tmp_path / "CLAUDE.md"
    claude.write_text("# Config\n")
    lint, struct = _classify_files(["CLAUDE.md"])
    assert lint == []
    assert struct == []


def test_classify_args_nonexistent() -> None:
    lint, struct = _classify_files(["/nonexistent/file.md"])
    assert lint == []
    assert struct == []


def test_classify_discovery_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    site = tmp_path / "docs" / "site"
    site.mkdir(parents=True)
    (site / "index.md").write_text("# Hello\n")
    (tmp_path / "README.md").write_text("# Project\n")
    lint, struct = _classify_files([])
    assert len(lint) == 1
    assert "index.md" in lint[0]
    assert struct == ["README.md"]


def test_classify_discovery_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    lint, struct = _classify_files([])
    assert lint == []
    assert struct == []


def test_classify_nested_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "sub" / "README.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("# Sub\n")
    lint, struct = _classify_files(["sub/README.md"])
    assert struct == ["sub/README.md"]


# -- _run_markdownlint -------------------------------------------------------


def test_run_markdownlint_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch(
        "standard_tooling.bin.markdown_standards.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0),
    ):
        assert _run_markdownlint(["file.md"]) is True


def test_run_markdownlint_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch(
        "standard_tooling.bin.markdown_standards.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1),
    ):
        assert _run_markdownlint(["file.md"]) is False


def test_run_markdownlint_with_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".markdownlint.yaml").write_text("default: true\n")
    captured_cmd: list[str] = []

    def capture_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_cmd.extend(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    with patch("standard_tooling.bin.markdown_standards.subprocess.run", side_effect=capture_run):
        _run_markdownlint(["file.md"])
    assert "--config" in captured_cmd
    assert ".markdownlint.yaml" in captured_cmd


# -- _structural_check -------------------------------------------------------


def test_structural_valid(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    assert _structural_check(str(doc)) is True


def test_structural_no_h1(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("## Section\n\n## Table of Contents\n")
    assert _structural_check(str(doc)) is False


def test_structural_multiple_h1(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n# Another\n\n## Table of Contents\n")
    assert _structural_check(str(doc)) is False


def test_structural_no_toc(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Section\n")
    assert _structural_check(str(doc)) is False


def test_structural_heading_skip(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n#### Skipped\n")
    assert _structural_check(str(doc)) is False


def test_structural_code_fence_ignored(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n```\n# Not a heading\n```\n\n## End\n")
    assert _structural_check(str(doc)) is True


def test_structural_tilde_fence_ignored(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n\n## Table of Contents\n\n~~~\n# Not a heading\n~~~\n\n## End\n")
    assert _structural_check(str(doc)) is True


# -- main --------------------------------------------------------------------


def test_main_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main([]) == 0


def test_main_markdownlint_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    site = tmp_path / "docs" / "site"
    site.mkdir(parents=True)
    (site / "index.md").write_text("# Hello\n")
    with patch("standard_tooling.bin.markdown_standards.shutil.which", return_value=None):
        assert main([]) == 2


def test_main_all_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    with (
        patch(
            "standard_tooling.bin.markdown_standards.shutil.which",
            return_value="/usr/bin/ml",
        ),
        patch(
            "standard_tooling.bin.markdown_standards._run_markdownlint",
            return_value=True,
        ),
    ):
        assert main(["README.md"]) == 0


def test_main_markdownlint_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n\n## Table of Contents\n\n## Section\n")
    with (
        patch(
            "standard_tooling.bin.markdown_standards.shutil.which",
            return_value="/usr/bin/ml",
        ),
        patch(
            "standard_tooling.bin.markdown_standards._run_markdownlint",
            return_value=False,
        ),
    ):
        assert main(["README.md"]) == 1


def test_main_structural_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("## No H1\n")
    with (
        patch(
            "standard_tooling.bin.markdown_standards.shutil.which",
            return_value="/usr/bin/ml",
        ),
        patch(
            "standard_tooling.bin.markdown_standards._run_markdownlint",
            return_value=True,
        ),
    ):
        assert main(["README.md"]) == 1


def test_main_lint_only_site_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    site = tmp_path / "docs" / "site"
    site.mkdir(parents=True)
    md = site / "page.md"
    md.write_text("## No H1 but that's fine for site pages\n")
    with (
        patch(
            "standard_tooling.bin.markdown_standards.shutil.which",
            return_value="/usr/bin/ml",
        ),
        patch(
            "standard_tooling.bin.markdown_standards._run_markdownlint",
            return_value=True,
        ),
    ):
        assert main(["docs/site/page.md"]) == 0
