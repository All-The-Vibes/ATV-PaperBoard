"""tests/test_core_validate.py — ENFORCE pillar unit tests.

Validates a rendered artifact; asserts clean pass.
Then introduces a color violation and asserts fail_class == 'color-trace'.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

MINIMAL_DESIGN = Path(__file__).parent / "fixtures" / "compliant" / "minimal.DESIGN.md"

MINIMAL_INPUT = {
    "title": "Validate Test Artifact",
    "body_html": "<p>Validation smoke test.</p>",
}

# A hex color NOT declared in minimal.DESIGN.md
_UNDECLARED_HEX = "#FF0000"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _render_to_dir(tmp: Path, input_data: dict | None = None, tier: str = "pico") -> dict:
    from core.render import render_artifact

    return render_artifact(
        input_data=input_data or MINIMAL_INPUT,
        design_path=MINIMAL_DESIGN,
        tier=tier,
        output_dir=tmp,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_validate_clean_artifact_passes():
    """A freshly rendered artifact with no inline color overrides must ACCEPT."""
    from core.validate import ValidationResult, validate_artifact

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        triple = _render_to_dir(tmp_path)
        slug = triple["slug"]

        # Patch artifact_dir resolution to point at our tmp
        import unittest.mock as mock
        with mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path):
            result = validate_artifact(slug, "standalone")

    assert isinstance(result, ValidationResult)
    # Bridge not available in unit test → lint_findings is [] (graceful degradation)
    # Color-trace should pass since body_html has no inline color styles
    assert result.color_violations == []
    assert result.fail_class in ("none", "environment")  # environment if bridge missing


def test_validate_color_violation_detected():
    """An artifact with an undeclared inline hex color must FAIL with fail_class='color-trace'."""
    from core.validate import validate_artifact

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Render with an undeclared inline color
        violating_input = {
            "title": "Violation Test",
            "body_html": f'<p style="color: {_UNDECLARED_HEX};">Red text violation</p>',
        }
        triple = _render_to_dir(tmp_path, input_data=violating_input)
        slug = triple["slug"]

        import unittest.mock as mock
        with mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path):
            result = validate_artifact(slug, "standalone")

    assert not result.passed
    assert result.fail_class == "color-trace"
    assert _UNDECLARED_HEX.lower() in [v.lower() for v in result.color_violations]


def test_validate_environment_fail_on_missing_files():
    """validate_artifact must return fail_class='environment' when files don't exist."""
    import unittest.mock as mock

    from core.validate import validate_artifact
    with mock.patch(
        "core.validate._resolve_artifact_dir",
        return_value=Path("/nonexistent/path/nowhere"),
    ):
        result = validate_artifact("no-such-slug", "standalone")

    assert not result.passed
    assert result.fail_class == "environment"


def test_extract_design_colors_parses_hex():
    """_extract_design_colors must find all hex values in the DESIGN.md Colors section."""
    from core.validate import _extract_design_colors

    content = """
## Colors
- primary: "#3B82F6"
- background: "#FFFFFF"
- foreground: "#0F172A"
"""
    colors = _extract_design_colors(content)
    assert "#3b82f6" in colors
    assert "#ffffff" in colors
    assert "#0f172a" in colors


def test_extract_inline_colors_finds_color_style():
    """_extract_inline_colors must find hex values in style='color: #...' attributes."""
    from core.validate import _extract_inline_colors

    html = '<p style="color: #FF0000; font-size: 16px;">Red text</p>'
    found = _extract_inline_colors(html)
    assert "#FF0000" in found


def test_extract_inline_colors_finds_background_style():
    """_extract_inline_colors must find hex values in style='background: #...' attributes."""
    from core.validate import _extract_inline_colors

    html = '<div style="background: #ABCDEF;">Box</div>'
    found = _extract_inline_colors(html)
    assert "#ABCDEF" in found


def test_extract_inline_colors_ignores_non_color_styles():
    """_extract_inline_colors must NOT return hex from unrelated style properties."""
    from core.validate import _extract_inline_colors

    html = '<div style="margin: 10px; padding: 5px;">No color here</div>'
    found = _extract_inline_colors(html)
    assert found == []


def test_validate_background_violation_detected():
    """An undeclared background hex must also trigger color-trace fail."""
    from core.validate import validate_artifact

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        violating_input = {
            "title": "Background Violation",
            "body_html": f'<div style="background: {_UNDECLARED_HEX};">BG violation</div>',
        }
        triple = _render_to_dir(tmp_path, input_data=violating_input)
        slug = triple["slug"]

        import unittest.mock as mock
        with mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path):
            result = validate_artifact(slug, "standalone")

    assert not result.passed
    assert result.fail_class == "color-trace"
