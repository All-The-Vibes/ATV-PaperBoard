"""tests/test_core_regenerate.py — 3-step retry unit tests.

Mocks a failing validation and asserts each retry step actually changes a parameter:
  Step 1: tier swap (pico → daisy or vice versa)
  Step 2: optional components dropped from input
  Step 3: design falls back to paperboard.DESIGN.md default
"""
from __future__ import annotations

import tempfile
import unittest.mock as mock
from pathlib import Path

import pytest
import yaml

from core.validate import ValidationResult


MINIMAL_DESIGN = Path(__file__).parent / "fixtures" / "compliant" / "minimal.DESIGN.md"
DEFAULT_DESIGN = Path(__file__).parent.parent / "core" / "designs" / "paperboard.DESIGN.md"

_FAILING_VALIDATION = ValidationResult(
    passed=False,
    lint_findings=[],
    color_violations=["#FF0000"],
    fail_class="color-trace",
)

_PASSING_VALIDATION = ValidationResult(
    passed=True,
    lint_findings=[],
    color_violations=[],
    fail_class="none",
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_meta(tmp: Path, slug: str, tier: str, input_data: dict) -> None:
    """Write a synthetic meta.yaml so regenerate can load it."""
    meta = {
        "created_at": "2026-05-14T00:00:00Z",
        "harness": "standalone",
        "design": str(MINIMAL_DESIGN),
        "tier": tier,
        "slug": slug,
        "lint_passed": False,
        "_input_data": input_data,
    }
    (tmp / f"{slug}.meta.yaml").write_text(yaml.dump(meta), encoding="utf-8")


def _write_stub_triple(tmp: Path, slug: str) -> None:
    """Write minimal stub HTML + DESIGN.md so render/validate can read them."""
    (tmp / f"{slug}.html").write_text(
        "<!DOCTYPE html><html><body><p>stub</p></body></html>", encoding="utf-8"
    )
    (tmp / f"{slug}.DESIGN.md").write_text(
        MINIMAL_DESIGN.read_text(encoding="utf-8"), encoding="utf-8"
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_regenerate_step1_switches_tier():
    """Step 1 must switch the tier from the original."""
    from core import regenerate as _regen

    original_input = {"title": "Regen Step1 Test", "body_html": "<p>test</p>"}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        slug = "regen-step1-test"
        _write_stub_triple(tmp_path, slug)
        _write_meta(tmp_path, slug, tier="pico", input_data=original_input)

        rendered_slugs: list[str] = []
        rendered_tiers: list[str] = []

        original_render = __import__("core.render", fromlist=["render_artifact"]).render_artifact

        def mock_render(input_data, design_path, tier, output_dir):
            rendered_tiers.append(tier)
            new_slug = f"new-{tier}-{len(rendered_slugs)}"
            rendered_slugs.append(new_slug)
            # Write stub triple for validation
            _write_stub_triple(output_dir, new_slug)
            _write_meta(output_dir, new_slug, tier=tier, input_data=input_data)
            return {
                "html_path": output_dir / f"{new_slug}.html",
                "design_path": output_dir / f"{new_slug}.DESIGN.md",
                "meta_path": output_dir / f"{new_slug}.meta.yaml",
                "slug": new_slug,
            }

        with (
            mock.patch("core.regenerate._resolve_artifact_dir", return_value=tmp_path),
            mock.patch("core.regenerate._candidate_dirs", return_value=[tmp_path]),
            mock.patch("core.render.render_artifact", side_effect=mock_render),
            mock.patch("core.validate.validate_artifact", return_value=_PASSING_VALIDATION),
            mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path),
        ):
            result = _regen.regenerate(slug, _FAILING_VALIDATION)

    assert result["retry_step"] == 1
    assert len(rendered_tiers) >= 1
    # Step 1 must use a different tier than the original "pico"
    assert rendered_tiers[0] == "daisy"


def test_regenerate_step2_drops_optional_components():
    """Step 2 must produce an input dict without optional component keys."""
    from core import regenerate as _regen

    original_input = {
        "title": "Regen Step2 Test",
        "body_html": "<p>main content</p>",
        "components": ["table", "chart"],
        "extras": {"footer": True},
    }

    captured_inputs: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        slug = "regen-step2-test"
        _write_stub_triple(tmp_path, slug)
        _write_meta(tmp_path, slug, tier="pico", input_data=original_input)

        call_count = [0]

        def mock_render(input_data, design_path, tier, output_dir):
            call_count[0] += 1
            captured_inputs.append(dict(input_data))
            new_slug = f"new-step-{call_count[0]}"
            _write_stub_triple(output_dir, new_slug)
            _write_meta(output_dir, new_slug, tier=tier, input_data=input_data)
            return {
                "html_path": output_dir / f"{new_slug}.html",
                "design_path": output_dir / f"{new_slug}.DESIGN.md",
                "meta_path": output_dir / f"{new_slug}.meta.yaml",
                "slug": new_slug,
            }

        # Step 1 fails, Step 2 passes
        validate_results = [_FAILING_VALIDATION, _PASSING_VALIDATION]
        validate_call = [0]

        def mock_validate(s, h, **kwargs):
            idx = validate_call[0]
            validate_call[0] += 1
            return validate_results[min(idx, len(validate_results) - 1)]

        with (
            mock.patch("core.regenerate._resolve_artifact_dir", return_value=tmp_path),
            mock.patch("core.regenerate._candidate_dirs", return_value=[tmp_path]),
            mock.patch("core.render.render_artifact", side_effect=mock_render),
            mock.patch("core.validate.validate_artifact", side_effect=mock_validate),
            mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path),
        ):
            result = _regen.regenerate(slug, _FAILING_VALIDATION)

    assert result["retry_step"] == 2
    # Step 2 input must NOT have optional keys
    step2_input = captured_inputs[1]  # second render call = step 2
    assert "components" not in step2_input
    assert "extras" not in step2_input
    # But title must still be present
    assert "title" in step2_input


def test_regenerate_step3_uses_default_design():
    """Step 3 must use paperboard.DESIGN.md as the design source."""
    from core import regenerate as _regen

    original_input = {"title": "Regen Step3 Test", "body_html": "<p>test</p>"}

    captured_designs: list[Path] = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        slug = "regen-step3-test"
        _write_stub_triple(tmp_path, slug)
        _write_meta(tmp_path, slug, tier="pico", input_data=original_input)

        call_count = [0]

        def mock_render(input_data, design_path, tier, output_dir):
            call_count[0] += 1
            captured_designs.append(Path(design_path))
            new_slug = f"new-step-{call_count[0]}"
            _write_stub_triple(output_dir, new_slug)
            _write_meta(output_dir, new_slug, tier=tier, input_data=input_data)
            return {
                "html_path": output_dir / f"{new_slug}.html",
                "design_path": output_dir / f"{new_slug}.DESIGN.md",
                "meta_path": output_dir / f"{new_slug}.meta.yaml",
                "slug": new_slug,
            }

        # All 3 steps fail then pass on step 3
        validate_results = [_FAILING_VALIDATION, _FAILING_VALIDATION, _PASSING_VALIDATION]
        validate_call = [0]

        def mock_validate(s, h, **kwargs):
            idx = validate_call[0]
            validate_call[0] += 1
            return validate_results[min(idx, len(validate_results) - 1)]

        with (
            mock.patch("core.regenerate._resolve_artifact_dir", return_value=tmp_path),
            mock.patch("core.regenerate._candidate_dirs", return_value=[tmp_path]),
            mock.patch("core.render.render_artifact", side_effect=mock_render),
            mock.patch("core.validate.validate_artifact", side_effect=mock_validate),
            mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path),
        ):
            result = _regen.regenerate(slug, _FAILING_VALIDATION)

    assert result["retry_step"] == 3
    # Step 3 design must differ from original (MINIMAL_DESIGN)
    # It should be the default paperboard.DESIGN.md
    assert len(captured_designs) == 3
    step3_design = captured_designs[2]
    assert step3_design.name == "paperboard.DESIGN.md" or str(step3_design).endswith(
        "paperboard.DESIGN.md"
    )


def test_regenerate_returns_result_dict_shape():
    """regenerate must always return dict with retry_step, new_slug, validation keys."""
    from core import regenerate as _regen

    original_input = {"title": "Shape Test", "body_html": "<p>shape</p>"}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        slug = "shape-test"
        _write_stub_triple(tmp_path, slug)
        _write_meta(tmp_path, slug, tier="pico", input_data=original_input)

        call_count = [0]

        def mock_render(input_data, design_path, tier, output_dir):
            call_count[0] += 1
            new_slug = f"new-{call_count[0]}"
            _write_stub_triple(output_dir, new_slug)
            _write_meta(output_dir, new_slug, tier=tier, input_data=input_data)
            return {
                "html_path": output_dir / f"{new_slug}.html",
                "design_path": output_dir / f"{new_slug}.DESIGN.md",
                "meta_path": output_dir / f"{new_slug}.meta.yaml",
                "slug": new_slug,
            }

        with (
            mock.patch("core.regenerate._resolve_artifact_dir", return_value=tmp_path),
            mock.patch("core.regenerate._candidate_dirs", return_value=[tmp_path]),
            mock.patch("core.render.render_artifact", side_effect=mock_render),
            mock.patch("core.validate.validate_artifact", return_value=_PASSING_VALIDATION),
            mock.patch("core.validate._resolve_artifact_dir", return_value=tmp_path),
        ):
            result = _regen.regenerate(slug, _FAILING_VALIDATION)

    assert "retry_step" in result
    assert "new_slug" in result
    assert "validation" in result
    assert isinstance(result["retry_step"], int)
    assert 1 <= result["retry_step"] <= 3
