"""tests/test_design_swap.py — design-swap fidelity contract.

Audit failure (2026-05-16): ``--design paperboard`` and ``--design atv`` silently
fell back to the default DESIGN.md because ``core.cli._resolve_design()`` only
checked ``core/designs/starters/<name>.DESIGN.md`` and never the top-level
``core/designs/<name>.DESIGN.md`` location where ``paperboard`` and ``atv``
live. The bug was invisible because:

  * No exception was raised.
  * Meta sidecar reported the *default* design path, not the requested one.
  * SHA-256 of the rendered HTML for ``--design paperboard`` and ``--design
    atv`` was *identical* (both fell back to the same default), which the
    schema-only lint cannot detect.

This test prevents regression by rendering the *same* input under two distinct
designs at each tier and asserting:

  1. The two HTMLs are not byte-identical (hash mismatch).
  2. The CSS token values for ``--color-primary`` differ between the two
     renders (substring check). This is the load-bearing signal — if the
     token swap is real, this primary-color variable must differ.
"""
from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path

import pytest

from core.render import render_artifact

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = REPO_ROOT / "core" / "designs"

# Two designs known to declare distinct ``colors.primary`` values. We pick
# from the top-level (paperboard) AND from starters/ (vercel-inspired) so that
# this test would have failed under the pre-fix resolver — ``paperboard`` would
# have silently fallen back to the default and produced identical output to
# any other top-level design.
DESIGN_A = DESIGNS_DIR / "paperboard.DESIGN.md"
DESIGN_B = DESIGNS_DIR / "starters" / "vercel-inspired.DESIGN.md"

MINIMAL_INPUT = {
    "title": "Design swap probe",
    "body_html": "<p>Body content for swap test.</p>",
}


def _render(tier: str, design_path: Path) -> str:
    """Render MINIMAL_INPUT at the given tier and design; return HTML content."""
    with tempfile.TemporaryDirectory() as tmp:
        triple = render_artifact(
            input_data=MINIMAL_INPUT,
            design_path=design_path,
            tier=tier,
            output_dir=Path(tmp),
        )
        return triple["html_path"].read_text(encoding="utf-8")


def _extract_primary(html: str, tier: str) -> str | None:
    """Pull the tier-specific primary color value from the rendered HTML.

    Each tier emits its tokens under a different namespace:

    * pico  → ``--pico-primary``
    * daisy → ``--p`` (daisyUI shortname for ``primary``)
    * atv   → ``--accent``

    Returning the raw value (e.g. ``#7170ff``) lets callers assert that swapping
    designs propagates through to the final token in the rendered HTML.
    """
    var_by_tier = {
        "pico": "--pico-primary",
        "daisy": "--p",
        "atv": "--accent",
    }
    var = var_by_tier.get(tier)
    if var is None:
        return None
    m = re.search(rf"{re.escape(var)}\s*:\s*([^;!]+)", html)
    return m.group(1).strip() if m else None


@pytest.mark.parametrize("tier", ["pico", "daisy", "atv"])
def test_design_swap_changes_output(tier: str) -> None:
    """Rendering the same input under two designs must produce distinct HTML
    AND distinct primary-color token values."""
    assert DESIGN_A.exists(), f"DESIGN_A missing: {DESIGN_A}"
    assert DESIGN_B.exists(), f"DESIGN_B missing: {DESIGN_B}"

    html_a = _render(tier, DESIGN_A)
    html_b = _render(tier, DESIGN_B)

    sha_a = hashlib.sha256(html_a.encode("utf-8")).hexdigest()
    sha_b = hashlib.sha256(html_b.encode("utf-8")).hexdigest()
    assert sha_a != sha_b, (
        f"[{tier}] same input rendered under {DESIGN_A.name} and {DESIGN_B.name} "
        f"produced byte-identical HTML — design swap is broken."
    )

    primary_a = _extract_primary(html_a, tier)
    primary_b = _extract_primary(html_b, tier)
    assert primary_a is not None, f"[{tier}] could not find primary-color var in {DESIGN_A.name} render"
    assert primary_b is not None, f"[{tier}] could not find primary-color var in {DESIGN_B.name} render"
    assert primary_a.lower() != primary_b.lower(), (
        f"[{tier}] primary-color token did not change across design swap "
        f"({DESIGN_A.name} → {primary_a!r}, {DESIGN_B.name} → {primary_b!r}). "
        f"This means tokens are not flowing from the DESIGN.md frontmatter."
    )
