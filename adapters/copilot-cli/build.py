#!/usr/bin/env python3
"""build.py — Assemble the Copilot CLI adapter distribution package.

Run from the repository root:
    python adapters/copilot-cli/build.py

Copies core/, skills/, designs/, and templates/ into
adapters/copilot-cli/_dist/ in the layout expected by the Copilot CLI plugin
loader (self-contained directory; well-known files = manifest).

Layout produced:

    _dist/
      core/                         # paperboard python package (incl. hooks)
      skills/                       # SKILL.md per skill — auto-loaded by Copilot CLI
      designs/                      # starter DESIGN.md files
      templates/                    # Jinja templates
      agents/
        artifact-reviewer.agent.md
      hooks.json                    # postToolUse → paperboard copilot-post-tool-use
      pyproject.toml                # so the dir is `pip install -e .`-able
      INSTALL.md
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

# Repo-root files to include verbatim (relative to REPO_ROOT). Impeccable
# attribution must reach every adapter dist so downstream installs carry the
# Apache 2.0 notice alongside the vendored reference files.
INCLUDE_FILES = ["NOTICE.md"]

# Adapter-local files/dirs to include (relative to ADAPTER_DIR).
# hooks.json lives at the plugin root (not under hooks/) per Copilot CLI's
# documented layout — the hooks/ subdir form is also accepted but the root
# file is the canonical case in the docs.
ADAPTER_INCLUDES = [
    "plugin.json",
    "hooks.json",
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
    print(f"  [copy] {src.relative_to(REPO_ROOT)} -> {dst.relative_to(DIST_DIR)}")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [copy] {src.relative_to(ADAPTER_DIR)} -> {dst.relative_to(DIST_DIR)}")


def copy_repo_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [copy] {src.relative_to(REPO_ROOT)} -> {dst.relative_to(DIST_DIR)}")


def main() -> int:
    print(f"Building Copilot CLI adapter dist -> {DIST_DIR}")
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

    # 3. Copy pyproject.toml so the dist dir is `pip install -e .`-able
    (DIST_DIR / "pyproject.toml").write_text(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print("  [copy] pyproject.toml -> pyproject.toml")

    print(f"\nDone. Dist at: {DIST_DIR}")
    print(
        "\nLocal smoke test (no install):\n"
        f"  copilot --plugin-dir={DIST_DIR}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
