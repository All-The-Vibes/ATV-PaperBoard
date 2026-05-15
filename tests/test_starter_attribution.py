"""
tests/test_starter_attribution.py
----------------------------------
§17 compliance test — PUBLIC RELEASE BLOCKER.

Rules:
  1. Every designs/starters/*.DESIGN.md must have YAML frontmatter with a
     fully-populated `attribution:` block containing all required keys.
  2. Every designs/**/*.DESIGN.md must pass bridge.lint() (warnings/errors == 0).

Failure here means: DO NOT PUSH.
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
STARTERS_DIR = REPO_ROOT / "designs" / "starters"
DESIGNS_DIR = REPO_ROOT / "designs"

# ---------------------------------------------------------------------------
# §17 required attribution keys
# ---------------------------------------------------------------------------
REQUIRED_ATTRIBUTION_KEYS = [
    "inspired_by",
    "not_affiliated_with",
    "source_repo",
    "source_path",
    "source_commit",
    "source_license",
    "redistributed_under",
    "imported_at",
    "notes",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(path: Path) -> dict[str, Any]:
    """Extract and parse YAML frontmatter from a DESIGN.md file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        pytest.fail(f"{path.name}: no YAML frontmatter found (expected --- delimiters)")
    return yaml.safe_load(match.group(1)) or {}


def _run_lint(path: Path) -> dict[str, Any]:
    """
    Run @google/design.md lint on *path* and return the parsed JSON result.

    If core.bridge is available, uses bridge.lint(). Otherwise falls back to
    a direct subprocess call to node.
    TODO: replace subprocess fallback with bridge.lint() once core.bridge is implemented.
    """
    try:
        from core.bridge import lint  # type: ignore[import]
        return lint(str(path))
    except ImportError:
        import subprocess  # noqa: PLC0415

        bin_path = (
            REPO_ROOT / "node_modules" / "@google" / "design.md" / "dist" / "index.js"
        )
        result = subprocess.run(
            ["node", str(bin_path), "lint", str(path), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            pytest.fail(
                f"lint node invocation failed for {path.name}: {result.stderr}"
            )
        return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Parametrize starters
# ---------------------------------------------------------------------------

STARTER_FILES = sorted(STARTERS_DIR.glob("*.DESIGN.md"))
ALL_DESIGN_FILES = sorted(DESIGNS_DIR.rglob("*.DESIGN.md"))


# ---------------------------------------------------------------------------
# Test 1 — attribution schema (§17)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("design_file", STARTER_FILES, ids=lambda p: p.name)
def test_attribution_block_present(design_file: Path) -> None:
    """DESIGN.md must have a top-level `attribution:` key in frontmatter."""
    fm = _parse_frontmatter(design_file)
    assert "attribution" in fm, (
        f"{design_file.name}: missing `attribution:` block in YAML frontmatter"
    )


@pytest.mark.parametrize("design_file", STARTER_FILES, ids=lambda p: p.name)
def test_attribution_required_keys(design_file: Path) -> None:
    """Every required §17 key must be present and non-empty."""
    fm = _parse_frontmatter(design_file)
    attr = fm.get("attribution", {})
    missing = []
    empty = []
    for key in REQUIRED_ATTRIBUTION_KEYS:
        if key not in attr:
            missing.append(key)
        elif not str(attr[key]).strip():
            empty.append(key)
    assert not missing, (
        f"{design_file.name}: attribution missing keys: {missing}"
    )
    assert not empty, (
        f"{design_file.name}: attribution has empty values for: {empty}"
    )


# ---------------------------------------------------------------------------
# Test 2 — lint clean (no errors or warnings)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("design_file", ALL_DESIGN_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_lint_clean(design_file: Path) -> None:
    """
    Every DESIGN.md must pass @google/design.md lint with 0 errors and 0 warnings.

    TODO: replace subprocess-based lint fallback with bridge.lint() once
          core.bridge is implemented (Phase 2 work).
    """
    result = _run_lint(design_file)
    findings = result.get("findings", [])
    bad = [f for f in findings if f.get("severity") in ("error", "warning")]
    assert not bad, (
        f"{design_file.name}: lint found {len(bad)} error/warning(s):\n"
        + "\n".join(f"  [{f['severity']}] {f.get('path','')} — {f['message']}" for f in bad)
    )
