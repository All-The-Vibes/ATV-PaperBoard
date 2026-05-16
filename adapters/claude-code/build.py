#!/usr/bin/env python3
"""build.py — Assemble the Claude Code adapter distribution package.

Run from the repository root:
    python adapters/claude-code/build.py

Copies core/, skills/, designs/, and templates/ into
adapters/claude-code/_dist/ in the layout expected by the Claude Code
plugin marketplace (self-contained directory).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
ADAPTER_DIR = Path(__file__).parent.resolve()
DIST_DIR = ADAPTER_DIR / "_dist"

# Directories from repo root to include verbatim. `core` now contains
# templates/ and designs/ as package-data, so they ride along.
INCLUDE_DIRS = ["core", "skills"]

# Adapter-local files/dirs to include (relative to ADAPTER_DIR)
ADAPTER_INCLUDES = [
    ".claude-plugin",
    "hooks",
    "agents",
    "INSTALL.md",
]


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)


def copy_dir(src: Path, dst: Path) -> None:
    """Copy src directory tree into dst, creating dst."""
    if not src.exists():
        print(f"  [skip] {src} — not found", file=sys.stderr)
        return
    shutil.copytree(src, dst)
    print(f"  [copy] {src.relative_to(REPO_ROOT)} → {dst.relative_to(DIST_DIR)}")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [copy] {src.relative_to(ADAPTER_DIR)} → {dst.relative_to(DIST_DIR)}")


def main() -> int:
    print(f"Building Claude Code adapter dist → {DIST_DIR}")
    clean_dist()

    # 1. Repo-level directories
    for name in INCLUDE_DIRS:
        src = REPO_ROOT / name
        dst = DIST_DIR / name
        copy_dir(src, dst)

    # 2. Adapter-local files/dirs
    for name in ADAPTER_INCLUDES:
        src = ADAPTER_DIR / name
        dst = DIST_DIR / name
        if src.is_dir():
            copy_dir(src, dst)
        elif src.is_file():
            copy_file(src, dst)
        else:
            print(f"  [skip] {name} — not found", file=sys.stderr)

    # 3. Write a minimal pyproject snippet so pip can install the dist in place
    (DIST_DIR / "pyproject.toml").write_text(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print("  [copy] pyproject.toml → pyproject.toml")

    print(f"\nDone. Dist at: {DIST_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
