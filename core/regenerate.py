"""core/regenerate.py — 3-step differentiated retry strategy (SPEC §6 Phase 2, T4 fix).

Retry sequence per SPEC-review T4:
  Step 1 — same design, switch tier (pico ↔ daisy)
  Step 2 — drop optional components from the input
  Step 3 — fall back to designs/paperboard.DESIGN.md default

Each step re-renders and re-validates. Returns on the first passing step.
If all three steps fail, returns the Step 3 result regardless.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.validate import ValidationResult


_DEFAULT_DESIGN = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"

# Keys considered "optional" in input_data — dropped in Step 2
_OPTIONAL_COMPONENT_KEYS = ("body_html", "components", "extras", "sidebar", "footer_html")


# ── Public API ────────────────────────────────────────────────────────────────


def regenerate(slug: str, validation: ValidationResult) -> dict[str, Any]:
    """Run a 3-step differentiated retry for a failed artifact.

    Reads the original artifact's meta.yaml to recover input parameters,
    then re-renders with progressively more conservative settings.

    Args:
        slug: Slug of the failed artifact.
        validation: The failing :class:`~core.validate.ValidationResult`.

    Returns:
        dict with keys: ``retry_step`` (1–3), ``new_slug``, ``validation``.
    """
    # Lazy import to avoid circular dependency
    from core import render as _render  # noqa: PLC0415
    from core.validate import validate_artifact

    original_meta = _load_original_meta(slug)
    harness = original_meta.get("harness", "standalone").split("/")[0]
    # Normalise — "atv-paperboard" harness string from render.py vs detect harness name
    if harness == "atv-paperboard":
        harness = "standalone"

    original_input = original_meta.get("_input_data", {})
    original_design = Path(original_meta.get("design", str(_DEFAULT_DESIGN)))
    original_tier = original_meta.get("tier", "pico")
    output_dir = _resolve_artifact_dir(harness)

    # ── Step 1: switch tier ───────────────────────────────────────────────
    new_tier = "daisy" if original_tier == "pico" else "pico"
    triple = _render.render_artifact(
        input_data=original_input,
        design_path=original_design,
        tier=new_tier,
        output_dir=output_dir,
    )
    new_slug = triple["slug"]
    result = validate_artifact(new_slug, harness)
    if result.passed:
        return {"retry_step": 1, "new_slug": new_slug, "validation": result}

    # ── Step 2: drop optional components ─────────────────────────────────
    stripped_input = {
        k: v for k, v in original_input.items() if k not in _OPTIONAL_COMPONENT_KEYS
    }
    # Keep title so slug stays recognisable
    stripped_input.setdefault("title", original_input.get("title", "Artifact"))
    triple = _render.render_artifact(
        input_data=stripped_input,
        design_path=original_design,
        tier=new_tier,
        output_dir=output_dir,
    )
    new_slug = triple["slug"]
    result = validate_artifact(new_slug, harness)
    if result.passed:
        return {"retry_step": 2, "new_slug": new_slug, "validation": result}

    # ── Step 3: fall back to paperboard.DESIGN.md ─────────────────────────
    fallback_design = _DEFAULT_DESIGN
    triple = _render.render_artifact(
        input_data=stripped_input,
        design_path=fallback_design,
        tier=new_tier,
        output_dir=output_dir,
    )
    new_slug = triple["slug"]
    result = validate_artifact(new_slug, harness)
    return {"retry_step": 3, "new_slug": new_slug, "validation": result}


# ── Internal helpers ──────────────────────────────────────────────────────────


def _resolve_artifact_dir(harness: str) -> Path:
    """Resolve artifact directory via persist module or fallback."""
    try:
        from core import persist as _persist  # noqa: PLC0415

        return _persist.artifact_dir(harness)
    except ImportError:
        # TODO: Remove once persist.py is delivered by the parallel agent.
        return Path.cwd() / "paperboard-artifacts"


def _load_original_meta(slug: str) -> dict[str, Any]:
    """Load meta.yaml for the given slug from the default artifact dir.

    Searches CWD/paperboard-artifacts first, then tries persist module.
    """
    import yaml  # stdlib-adjacent; in dependencies

    for candidate_dir in _candidate_dirs():
        meta_path = candidate_dir / f"{slug}.meta.yaml"
        if meta_path.exists():
            return yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    return {}


def _candidate_dirs() -> list[Path]:
    dirs = [Path.cwd() / "paperboard-artifacts"]
    try:
        from core import persist as _persist  # noqa: PLC0415
        from core import detect as _detect  # noqa: PLC0415

        harness = _detect.detect_harness()
        dirs.append(_persist.artifact_dir(harness))
    except ImportError:
        pass
    return dirs
