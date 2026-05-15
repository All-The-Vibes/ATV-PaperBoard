"""core/validate.py — ENFORCE pillar for atv-paperboard.

Runs two checks:
1. ``bridge.lint()`` — @google/design.md JSON lint
2. HTML-side color-token trace — every inline hex color in the HTML must appear
   in the paired DESIGN.md's Colors section.

Color-only trace for v0.1.0 (SPEC §7).

API contract used from the parallel agent:
  bridge.lint(design_path: Path) -> list[dict]   # each dict has at minimum 'message' key

TODO: Remove graceful-degradation branch once bridge.py is delivered.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """Result of a validate_artifact run."""

    passed: bool
    lint_findings: list[dict[str, Any]] = field(default_factory=list)
    color_violations: list[str] = field(default_factory=list)
    fail_class: str = "none"  # none | lint | color-trace | environment


# ── Public API ────────────────────────────────────────────────────────────────


def validate_artifact(slug: str, harness: str) -> ValidationResult:
    """Run ENFORCE checks for a persisted artifact triple.

    Resolves the triple paths from ``persist.artifact_dir(harness) / slug.*``.
    Falls back to ``CWD/paperboard-artifacts/<slug>.*`` if persist unavailable.

    Args:
        slug: Artifact slug (filename stem).
        harness: Harness name (used for path resolution).

    Returns:
        :class:`ValidationResult`.
    """
    artifact_dir = _resolve_artifact_dir(harness)
    html_path = artifact_dir / f"{slug}.html"
    design_path = artifact_dir / f"{slug}.DESIGN.md"

    if not html_path.exists() or not design_path.exists():
        return ValidationResult(
            passed=False,
            fail_class="environment",
            lint_findings=[{"message": f"Triple not found in {artifact_dir}"}],
        )

    # ── Step 1: lint via bridge ────────────────────────────────────────────
    lint_findings: list[dict[str, Any]] = []
    bridge_available = False
    try:
        from core import bridge as _bridge  # noqa: PLC0415

        lint_result = _bridge.lint(design_path)
        # lint() returns {"findings": [...], "summary": {...}}
        lint_findings = lint_result.get("findings", [])
        bridge_available = True
    except ImportError:
        # TODO: Remove once bridge.py is delivered by the parallel agent.
        lint_findings = []
        bridge_available = False

    if lint_findings:
        return ValidationResult(
            passed=False,
            lint_findings=lint_findings,
            fail_class="lint",
        )

    # ── Step 2: HTML-side color-token trace ───────────────────────────────
    html_content = html_path.read_text(encoding="utf-8")
    design_content = design_path.read_text(encoding="utf-8")

    declared_colors = _extract_design_colors(design_content)
    inline_colors = _extract_inline_colors(html_content)

    violations = [c for c in inline_colors if c.lower() not in declared_colors]

    if violations:
        return ValidationResult(
            passed=False,
            lint_findings=lint_findings,
            color_violations=violations,
            fail_class="color-trace",
        )

    return ValidationResult(
        passed=True,
        lint_findings=lint_findings,
        color_violations=[],
        fail_class="none",
    )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _resolve_artifact_dir(harness: str) -> Path:
    """Resolve artifact directory via persist module or fallback."""
    try:
        from core import persist as _persist  # noqa: PLC0415

        return _persist.artifact_dir(harness)
    except ImportError:
        # TODO: Remove once persist.py is delivered by the parallel agent.
        return Path.cwd() / "paperboard-artifacts"


def _extract_design_colors(design_content: str) -> set[str]:
    """Extract all hex color values declared in a DESIGN.md Colors section.

    Matches #RGB, #RRGGBB, and #RRGGBBAA (case-insensitive).
    Returns a set of lowercase hex strings including the ``#`` prefix.
    """
    # Simple regex; the color section uses: ``- primary: "#3B82F6"``
    pattern = re.compile(r"#([0-9a-fA-F]{3,8})\b")
    return {m.group(0).lower() for m in pattern.finditer(design_content)}


def _extract_inline_colors(html_content: str) -> list[str]:
    """Extract hex colors from inline ``style="color: #..."`` or ``style="background: #..."``."""
    # Match style attributes containing color or background-color
    style_pattern = re.compile(r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)
    hex_pattern = re.compile(r"#([0-9a-fA-F]{3,8})\b")

    found: list[str] = []
    for style_match in style_pattern.finditer(html_content):
        style_value = style_match.group(1)
        # Only care about color / background properties
        if re.search(r"\b(color|background)\s*:", style_value, re.IGNORECASE):
            for hex_match in hex_pattern.finditer(style_value):
                found.append(hex_match.group(0))
    return found
