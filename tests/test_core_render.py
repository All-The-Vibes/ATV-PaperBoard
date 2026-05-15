"""tests/test_core_render.py — RENDER pillar unit tests.

Renders a minimal fixture, asserts the triple exists, HTML parses, meta.yaml has expected keys.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest
import yaml


# ── Fixtures ──────────────────────────────────────────────────────────────────

MINIMAL_DESIGN = Path(__file__).parent / "fixtures" / "compliant" / "minimal.DESIGN.md"

MINIMAL_INPUT = {
    "title": "Test Artifact",
    "body_html": "<p>Hello from the test suite.</p>",
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _render_to_tmpdir(tier: str = "pico") -> tuple[dict, Path]:
    """Render MINIMAL_INPUT to a fresh temp directory and return (triple, tmpdir)."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            tier=tier,
            output_dir=tmp_path,
        )
        # Copy result data before tempdir cleanup
        # (we need to inspect files; read them now)
        html_content = triple["html_path"].read_text(encoding="utf-8")
        design_content = triple["design_path"].read_text(encoding="utf-8")
        meta_content = triple["meta_path"].read_text(encoding="utf-8")
        return (
            {
                "slug": triple["slug"],
                "html": html_content,
                "design": design_content,
                "meta_raw": meta_content,
            },
            tmp_path,
        )


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_render_returns_triple_keys():
    """render_artifact must return dict with html_path, design_path, meta_path, slug."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
    assert "html_path" in triple
    assert "design_path" in triple
    assert "meta_path" in triple
    assert "slug" in triple


def test_render_files_exist():
    """All three files of the triple must exist on disk."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=tmp_path,
        )
        assert triple["html_path"].exists(), "HTML file not written"
        assert triple["design_path"].exists(), "DESIGN.md not written"
        assert triple["meta_path"].exists(), "meta.yaml not written"


def test_render_html_contains_title():
    """Rendered HTML must include the artifact title."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert "Test Artifact" in html


def test_render_html_contains_body():
    """Rendered HTML must include the body_html content."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert "Hello from the test suite." in html


def test_render_html_has_doctype():
    """Rendered HTML must start with <!DOCTYPE html>."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert html.strip().lower().startswith("<!doctype html>")


def test_render_meta_yaml_keys():
    """meta.yaml must contain all required keys."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
        meta = yaml.safe_load(triple["meta_path"].read_text(encoding="utf-8"))

    required_keys = {"created_at", "harness", "design", "tier", "slug", "lint_passed"}
    assert required_keys <= set(meta.keys()), f"Missing keys: {required_keys - set(meta.keys())}"


def test_render_meta_tier_matches():
    """meta.yaml tier must match the requested tier."""
    from core.render import render_artifact

    for tier in ("pico", "daisy"):
        with tempfile.TemporaryDirectory() as tmp:
            triple = render_artifact(
                input_data=MINIMAL_INPUT,
                design_path=MINIMAL_DESIGN,
                tier=tier,
                output_dir=Path(tmp),
            )
            meta = yaml.safe_load(triple["meta_path"].read_text(encoding="utf-8"))
        assert meta["tier"] == tier


def test_render_slug_is_filesystem_safe():
    """Slug must only contain lowercase alphanumerics and hyphens."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data={"title": "Hello World! This is a Test 123"},
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
    slug = triple["slug"]
    assert re.match(r"^[a-z0-9][a-z0-9\-]*$", slug), f"Unsafe slug: {slug!r}"


def test_render_daisy_tier():
    """Daisy tier must produce HTML that references daisyUI CDN."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            tier="daisy",
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert "daisyui" in html.lower()


def test_render_pico_tier_references_pico():
    """Pico tier must reference Pico CSS CDN."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            tier="pico",
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert "picocss" in html.lower() or "pico" in html.lower()


def test_render_footer_present():
    """Rendered HTML must include the atv-paperboard footer."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=MINIMAL_DESIGN,
            output_dir=Path(tmp),
        )
        html = triple["html_path"].read_text(encoding="utf-8")

    assert "atv-paperboard" in html
    assert "DESIGN.md" in html


def test_tokens_from_export_pico():
    """tokens_from_export must map Tailwind color tokens to Pico CSS vars."""
    from core.render import tokens_from_export

    export = {
        "colors": {
            "primary": {"500": "#3B82F6", "DEFAULT": "#3B82F6"},
            "background": "#FFFFFF",
        }
    }
    tokens = tokens_from_export(export, tier="pico")
    assert "--pico-primary" in tokens
    assert tokens["--pico-primary"] == "#3B82F6"


def test_tokens_from_export_daisy():
    """tokens_from_export must map primary color to daisyUI --p var."""
    from core.render import tokens_from_export

    export = {
        "colors": {
            "primary": {"500": "#3B82F6"},
        }
    }
    tokens = tokens_from_export(export, tier="daisy")
    assert "--p" in tokens


def test_render_invalid_tier_raises():
    """render_artifact must raise ValueError for unknown tier."""
    from core.render import render_artifact

    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError, match="Unknown tier"):
            render_artifact(
                input_data=MINIMAL_INPUT,
                design_path=MINIMAL_DESIGN,
                tier="bootstrap",
                output_dir=Path(tmp),
            )
