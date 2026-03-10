"""Tests for standard_tooling.bin.finalize_repo."""

from __future__ import annotations

from subprocess import CompletedProcess
from typing import TYPE_CHECKING
from unittest.mock import patch

from standard_tooling.bin.finalize_repo import main, parse_args

_MOD = "standard_tooling.bin.finalize_repo"

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.target_branch == "develop"
    assert args.dry_run is False


def test_parse_args_custom() -> None:
    args = parse_args(["--target-branch", "main", "--dry-run"])
    assert args.target_branch == "main"
    assert args.dry_run is True


def _make_profile(tmp_path: Path, model: str) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "repository-standards.md").write_text(
        f"## Repository profile\n\n- branching_model: {model}\n"
    )


def _validation_ok() -> CompletedProcess[bytes]:
    return CompletedProcess(args=("st-validate-local",), returncode=0)


def _which_docker_only(name: str) -> str | None:
    """Simulate st-docker-run on PATH, st-validate-local not."""
    return "/usr/bin/st-docker-run" if name == "st-docker-run" else None


def _which_validator_only(name: str) -> str | None:
    """Simulate st-validate-local on PATH, st-docker-run not."""
    return "/usr/bin/st-validate-local" if name == "st-validate-local" else None


def test_main_library_release(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="feature/x"),
        patch(_MOD + ".git.run") as mock_run,
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["feature/x", "develop"],
        ),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0
    mock_run.assert_any_call("checkout", "develop")
    mock_run.assert_any_call("branch", "-d", "feature/x")


def test_main_already_on_target(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0


def test_main_dry_run(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="feature/x"),
        patch(_MOD + ".git.run") as mock_git_run,
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["feature/x"],
        ),
    ):
        result = main(["--dry-run"])
    assert result == 0
    mock_git_run.assert_not_called()


def test_main_no_profile(tmp_path: Path) -> None:
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0


def test_main_unrecognized_model(tmp_path: Path) -> None:
    _make_profile(tmp_path, "unknown-model")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
    ):
        result = main([])
    assert result == 1


def test_main_application_promotion(tmp_path: Path) -> None:
    _make_profile(tmp_path, "application-promotion")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(
            "standard_tooling.bin.finalize_repo.git.merged_branches",
            return_value=["develop", "release", "main", "feature/y"],
        ),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0


def test_main_docs_single_branch(tmp_path: Path) -> None:
    _make_profile(tmp_path, "docs-single-branch")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0


def test_main_no_deleted_branches(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=["develop"]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()),
    ):
        result = main([])
    assert result == 0


def test_main_validation_fails(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(
            "standard_tooling.bin.finalize_repo.subprocess.run",
            return_value=CompletedProcess(args=("st-validate-local",), returncode=1),
        ),
    ):
        result = main([])
    assert result == 1


def test_main_validator_not_found(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", return_value=None),
    ):
        result = main([])
    assert result == 1


def test_main_prefers_docker_run(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_docker_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()) as mock_sub,
    ):
        result = main([])
    assert result == 0
    cmd = mock_sub.call_args[0][0]
    assert cmd[0] == "/usr/bin/st-docker-run"
    assert cmd[1:] == ("--", "st-validate-local")


def test_main_falls_back_to_direct_validator(tmp_path: Path) -> None:
    _make_profile(tmp_path, "library-release")
    with (
        patch(_MOD + ".git.repo_root", return_value=tmp_path),
        patch(_MOD + ".git.current_branch", return_value="develop"),
        patch(_MOD + ".git.run"),
        patch(_MOD + ".git.merged_branches", return_value=[]),
        patch(_MOD + ".shutil.which", side_effect=_which_validator_only),
        patch(_MOD + ".subprocess.run", return_value=_validation_ok()) as mock_sub,
    ):
        result = main([])
    assert result == 0
    cmd = mock_sub.call_args[0][0]
    assert cmd == ("/usr/bin/st-validate-local",)
