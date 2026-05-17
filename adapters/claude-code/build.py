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

# Force UTF-8 stdout on Windows so the unicode arrows in our progress prints
# (`→`) don't crash with UnicodeEncodeError under cp1252. Same pattern used in
# `core/cli.py` for the same root cause (Phase 7a RW-1).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
ADAPTER_DIR = Path(__file__).parent.resolve()
DIST_DIR = ADAPTER_DIR / "_dist"

# Directories from repo root to include verbatim. `core` now contains
# templates/ and designs/ as package-data, so they ride along.
INCLUDE_DIRS = ["core", "skills"]

# Repo-root files to include verbatim (relative to REPO_ROOT). Impeccable
# attribution must reach every adapter dist so downstream installs carry the
# Apache 2.0 notice alongside the vendored reference files.
INCLUDE_FILES = ["NOTICE.md"]

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


def copy_repo_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [copy] {src.relative_to(REPO_ROOT)} → {dst.relative_to(DIST_DIR)}")


def main() -> int:
    print(f"Building Claude Code adapter dist → {DIST_DIR}")
    clean_dist()

    # 1. Repo-level directories. `core/` already contains `designs/` (with the
    # vendored `impeccable-context/` and `DESIGN-AUTHORITY.md`), and `skills/`
    # already contains the `impeccable-design/` wrapper skill, so both ride
    # along via the existing INCLUDE_DIRS copy.
    for name in INCLUDE_DIRS:
        src = REPO_ROOT / name
        dst = DIST_DIR / name
        copy_dir(src, dst)

    # 1b. Repo-level files (NOTICE.md carries the impeccable Apache 2.0
    # attribution and must ship with every adapter dist).
    for name in INCLUDE_FILES:
        src = REPO_ROOT / name
        dst = DIST_DIR / name
        if src.is_file():
            copy_repo_file(src, dst)
        else:
            print(f"  [skip] {name} — not found at repo root", file=sys.stderr)

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
