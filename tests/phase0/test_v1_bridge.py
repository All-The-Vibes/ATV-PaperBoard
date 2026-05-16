"""tests/phase0/test_v1_bridge.py

V1: lint of minimal fixture returns empty findings.
V2: export with format='tailwind' returns a dict containing color tokens.
V_spec: bridge.spec() returns parseable structure (drift guard).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow imports from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.bridge import export, lint, spec, version


MINIMAL_FIXTURE = (
    Path(__file__).parent.parent / "fixtures" / "compliant" / "minimal.DESIGN.md"
)
PAPERBOARD_DESIGN = (
    Path(__file__).parent.parent.parent / "core" / "designs" / "paperboard.DESIGN.md"
)


def test_v1_lint_minimal_empty_findings() -> None:
    """V1: lint of minimal fixture returns empty findings."""
    result = lint(MINIMAL_FIXTURE)
    assert isinstance(result, dict), "lint() must return a dict"
    assert "findings" in result, "result must contain 'findings' key"
    errors = [f for f in result["findings"] if f.get("severity") == "error"]
    assert errors == [], f"Expected no error findings, got: {errors}"
    summary = result.get("summary", {})
    assert summary.get("errors", 0) == 0, f"Expected 0 errors in summary, got: {summary}"


def test_v2_export_tailwind_contains_color_tokens() -> None:
    """V2: export with format='tailwind' returns a dict containing color tokens."""
    result = export(PAPERBOARD_DESIGN, fmt="tailwind")
    assert isinstance(result, dict), "export() must return a dict"
    # Tailwind output shape: {"theme": {"extend": {"colors": {...}, ...}}}
    colors = result.get("theme", {}).get("extend", {}).get("colors", {})
    assert len(colors) >= 1, (
        f"Expected at least 1 color token in tailwind export, got: {colors!r}"
    )


def test_v_spec_parseable_structure() -> None:
    """V_spec: bridge.spec() returns parseable structure (drift guard)."""
    result = spec()
    assert isinstance(result, dict), "spec() must return a dict"
    assert "content" in result, "spec() result must contain 'content' key"
    assert "version" in result, "spec() result must contain 'version' key"
    content = result["content"]
    assert isinstance(content, str) and len(content) > 100, (
        "spec content should be a non-trivial string"
    )
    ver = result["version"]
    assert isinstance(ver, str) and len(ver) > 0, "version must be a non-empty string"
