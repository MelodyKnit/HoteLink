#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def find_command(command: str, windows_fallback: str | None = None) -> str:
    resolved = shutil.which(command)
    if resolved:
        return resolved
    if windows_fallback:
        resolved = shutil.which(windows_fallback)
        if resolved:
            return resolved
    raise FileNotFoundError(command)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    try:
        poetry = find_command("poetry", "poetry.exe")
    except FileNotFoundError:
        print(
            "poetry command not found. Install Poetry before running the pre-push hook.",
            file=sys.stderr,
        )
        return 1

    completed = subprocess.run(
        [poetry, "run", "python", "manage.py", "test", "apps.api.tests", "-v", "2"],
        cwd=backend_dir,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
