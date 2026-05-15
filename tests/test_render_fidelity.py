"""tests/test_render_fidelity.py — Regression tests for the _flatten_tailwind unwrap fix.

These tests guard against re-introducing the bug where _flatten_tailwind() failed to
unwrap {"theme": {"extend": {...}}} output from @google/design.md, producing an empty
:root block in rendered HTML.

Sentinel color #ABCDEF is used throughout — it appears nowhere else in the repo, so
any test finding it in rendered HTML proves token injection actually worked.
"""
from __future__ import annotations

from pathlib import Path

# ── Fixtures ──────────────────────────────────────────────────────────────────

SENTINEL_DESIGN = Path(__file__).parent / "fixtures" / "sentinel.DESIGN.md"
SENTINEL_COLOR = "#ABCDEF"
SENTINEL_COLOR_LOWER = "#abcdef"


# ── Test A: nested theme.extend shape ────────────────────────────────────────


def test_flatten_tailwind_handles_nested_theme_extend_shape():
    """_flatten_tailwind must unwrap {"theme": {"extend": {...}}} and produce tokens.

    This is the exact shape @google/design.md export --format tailwind emits (Tailwind
    v3 config). Before the fix, _flatten_tailwind returned {} for this shape, leaving
    the :root block empty.
    """
    from core.render import _flatten_tailwind

    nested = {"theme": {"extend": {"colors": {"sentinel": SENTINEL_COLOR}}}}
    result = _flatten_tailwind(nested)

    assert result, "Expected non-empty result from nested theme.extend shape"
    assert "--color-sentinel" in result, (
        f"--color-sentinel not found in flattened keys: {list(result.keys())}"
    )
    assert result["--color-sentinel"] == SENTINEL_COLOR, (
        f"Expected {SENTINEL_COLOR!r}, got {result['--color-sentinel']!r}"
    )


# ── Test B: flat shape (backward compatibility) ───────────────────────────────


def test_flatten_tailwind_handles_flat_shape():
    """_flatten_tailwind must handle the flat {"colors": {...}} shape unchanged.

    Preserves backward compatibility with test-fixture–shaped dicts (no theme wrapper).
    """
    from core.render import _flatten_tailwind

    flat = {"colors": {"sentinel": SENTINEL_COLOR}}
    result = _flatten_tailwind(flat)

    assert result, "Expected non-empty result from flat shape"
    assert "--color-sentinel" in result, (
        f"--color-sentinel not found in flattened keys: {list(result.keys())}"
    )
    assert result["--color-sentinel"] == SENTINEL_COLOR, (
        f"Expected {SENTINEL_COLOR!r}, got {result['--color-sentinel']!r}"
    )


# ── Test C: end-to-end render injects tokens into :root block ─────────────────


def test_render_artifact_injects_tokens_into_root_block(tmp_path: Path):
    """render_artifact must inject sentinel color into the :root CSS block in HTML.

    Uses sentinel.DESIGN.md → render_artifact() → reads the produced .html file.
    Asserts the sentinel color appears and the :root block is non-empty.
    This is the end-to-end regression guard for the _flatten_tailwind unwrap fix.
    """
    from core.render import render_artifact

    input_data = {"title": "Sentinel Test", "rows": [{"col": "val"}]}

    triple = render_artifact(
        input_data=input_data,
        design_path=SENTINEL_DESIGN,
        tier="pico",
        output_dir=tmp_path,
    )

    html = triple["html_path"].read_text(encoding="utf-8")

    # Sentinel color must appear (case-insensitive — Tailwind may lowercase hex)
    assert SENTINEL_COLOR_LOWER in html.lower(), (
        f"Sentinel color {SENTINEL_COLOR!r} not found in rendered HTML. "
        "Token injection likely broken — check _flatten_tailwind unwrap logic."
    )

    # :root block must be non-empty (contain at least one --pico- CSS variable)
    assert ":root {" in html, ":root { block missing from rendered HTML"
    root_start = html.index(":root {")
    root_end = html.find("}", root_start)
    root_block = html[root_start:root_end]
    assert "--pico-" in root_block, (
        f":root block appears empty (no --pico- vars). Block content: {root_block!r}"
    )
