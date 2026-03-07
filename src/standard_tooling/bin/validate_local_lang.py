"""Language-specific local validation.

Delegates to the repository's ``scripts/dev/{lint,typecheck,test,audit}.sh``
scripts.  A single module serves all four language variants — the language
is determined from the entry point name or the ``--language`` argument.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from standard_tooling.lib import git

_SCRIPTS = ("lint.sh", "typecheck.sh", "test.sh", "audit.sh")

_ENTRY_POINT_LANGUAGES = {
    "st-validate-local-python": "python",
    "st-validate-local-rust": "rust",
    "st-validate-local-go": "go",
    "st-validate-local-java": "java",
}


def _detect_language(argv: list[str] | None) -> str:
    """Determine the target language from the entry point name or ``--language``."""
    if argv is not None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--language", default="")
        known, _ = parser.parse_known_args(argv)
        lang: str = known.language
        if lang:
            return lang

    prog = Path(sys.argv[0]).name
    return str(_ENTRY_POINT_LANGUAGES.get(prog, ""))


def main(argv: list[str] | None = None) -> int:
    language = _detect_language(argv)
    if not language:
        print(
            "ERROR: could not determine language from entry point or --language.",
            file=sys.stderr,
        )
        return 1

    repo_root = git.repo_root()
    failed = 0

    for script in _SCRIPTS:
        target = repo_root / "scripts" / "dev" / script
        if target.is_file() and os.access(target, os.X_OK):
            print(f"Running: scripts/dev/{script}")
            result = subprocess.run((str(target),), check=False)  # noqa: S603
            if result.returncode != 0:
                failed = 1

    return failed


if __name__ == "__main__":
    sys.exit(main())
