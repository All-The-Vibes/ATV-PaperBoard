"""tests/test_render_real_world.py — Phase 7a real-world render tests.

Covers the three bugs fixed in RW-4/7, RW-5, and RW-6:
  - _default_body_html() for rows / body_md / body_html / fallback
  - lint_passed filters info-only findings correctly
  - meta.yaml has both `harness` and `generator` fields
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

MINIMAL_DESIGN = Path(__file__).parent / "fixtures" / "compliant" / "minimal.DESIGN.md"
PAPERBOARD_DESIGN = Path(__file__).parent.parent / "core" / "designs" / "paperboard.DESIGN.md"


def _render(input_data: dict, design: Path = MINIMAL_DESIGN, tier: str = "pico") -> tuple[dict, Path]:
    from core.render import render_artifact
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        triple = render_artifact(input_data, design, tier=tier, output_dir=tmpdir)
        # Read files before tmp is deleted
        triple["_html"] = triple["html_path"].read_text(encoding="utf-8")
        triple["_meta"] = yaml.safe_load(triple["meta_path"].read_text(encoding="utf-8"))
    return triple


# ── RW-4/7: body dispatch ─────────────────────────────────────────────────────

def test_rows_input_renders_table():
    triple = _render({
        "title": "Table Test",
        "rows": [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
    })
    html = triple["_html"]
    assert "<table>" in html
    assert "<th>a</th>" in html
    assert "<td>1</td>" in html
    assert "<td>3</td>" in html
    assert "<td>4</td>" in html


def test_body_md_input_converted():
    triple = _render({
        "title": "MD Test",
        "body_md": "# Hello\n\nWorld",
    })
    html = triple["_html"]
    assert "<h1>Hello</h1>" in html
    assert "<p>" in html
    assert "World" in html


def test_body_html_passthrough():
    triple = _render({
        "title": "HTML Passthrough",
        "body_html": "<p>raw</p>",
    })
    assert "<p>raw</p>" in triple["_html"]


def test_fallback_dumps_json():
    triple = _render({
        "title": "Fallback Test",
        "some_key": "some_value",
    })
    html = triple["_html"]
    assert "<pre>" in html
    assert "some_key" in html


def test_html_escaping():
    triple = _render({
        "title": "XSS Test",
        "rows": [{"col": '<script>alert(1)</script>'}],
    })
    html = triple["_html"]
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ── RW-6: meta harness/generator fields ──────────────────────────────────────

def test_meta_harness_field():
    triple = _render({"title": "Meta Test", "body_html": "<p>hi</p>"})
    meta = triple["_meta"]
    assert "generator" in meta
    assert meta["generator"] == "atv-paperboard/0.1.0"
    assert "harness" in meta
    # harness must be a known value or at least a non-empty string
    assert isinstance(meta["harness"], str)
    assert len(meta["harness"]) > 0


# ── RW-5: info-only findings don't block lint_passed ─────────────────────────

def test_meta_lint_passed_with_info_only():
    """Render against paperboard.DESIGN.md; info-level token-count findings must not block."""
    if not PAPERBOARD_DESIGN.exists():
        pytest.skip("designs/paperboard.DESIGN.md not found")
    triple = _render(
        {"title": "Lint Info Test", "body_html": "<p>test</p>"},
        design=PAPERBOARD_DESIGN,
    )
    meta = triple["_meta"]
    # If bridge is available, lint_passed should be True (info findings are non-blocking).
    # If bridge is not available, lint_passed is False by design — skip assertion.
    try:
        from core import (
            bridge as _bridge,  # noqa: F401  (import-only probe for bridge availability)
        )

        assert _bridge is not None
        assert meta["lint_passed"] is True, f"lint_passed was False; meta={meta}"
    except ImportError:
        pytest.skip("core.bridge not available; skipping lint_passed assertion")
