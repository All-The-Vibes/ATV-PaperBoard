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


def validate_all(directory: Path) -> list[ValidationResult]:
    """Validate every artifact triple found in *directory*.

    Iterates over ``*.meta.yaml`` files, derives the slug, and calls
    :func:`validate_artifact` for each one.  The harness is read from the
    meta file when available; falls back to ``"standalone"``.

    Args:
        directory: Path to the artifact directory to scan.

    Returns:
        List of :class:`ValidationResult` instances (one per artifact found).
    """
    directory = Path(directory)
    results: list[ValidationResult] = []
    for meta_file in sorted(directory.glob("*.meta.yaml")):
        try:
            import yaml as _yaml  # noqa: PLC0415
            meta = _yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            meta = {}
        slug = meta.get("slug") or meta_file.stem.replace(".meta", "")
        meta.get("harness", "standalone")
        # Validate using the directory directly (bypass harness path resolution).
        html_path = directory / f"{slug}.html"
        design_path = directory / f"{slug}.DESIGN.md"
        result = _validate_paths(slug, html_path, design_path)
        results.append(result)
    return results


def _validate_paths(slug: str, html_path: Path, design_path: Path) -> ValidationResult:
    """Core validation logic given explicit paths (used by both public functions)."""
    if not html_path.exists() or not design_path.exists():
        return ValidationResult(
            passed=False,
            fail_class="environment",
            lint_findings=[{"message": f"Triple not found for slug {slug!r}"}],
        )

    lint_findings: list[dict[str, Any]] = []
    try:
        from core import bridge as _bridge  # noqa: PLC0415
        lint_result = _bridge.lint(design_path)
        lint_findings = lint_result.get("findings", [])
    except ImportError:
        lint_findings = []

    # Only error/warning severities block validation. Info findings (e.g. the
    # token-count summary @google/design.md emits) are non-blocking.
    # Discovered via Phase 7a real-world run.
    blocking = [
        f for f in lint_findings
        if isinstance(f, dict) and f.get("severity") in ("error", "warning")
    ]
    if blocking:
        return ValidationResult(passed=False, lint_findings=blocking, fail_class="lint")

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
    return ValidationResult(passed=True, lint_findings=lint_findings, color_violations=[], fail_class="none")


def validate_artifact(
    slug: str, harness: str, artifact_dir: Path | None = None
) -> ValidationResult:
    """Run ENFORCE checks for a persisted artifact triple.

    Resolves the triple paths from ``persist.artifact_dir(harness) / slug.*``.
    Falls back to ``CWD/paperboard-artifacts/<slug>.*`` if persist unavailable.

    Args:
        slug: Artifact slug (filename stem).
        harness: Harness name (used for path resolution).
        artifact_dir: If provided, use this directory instead of the harness default.

    Returns:
        :class:`ValidationResult`.
    """
    resolved_dir = artifact_dir if artifact_dir is not None else _resolve_artifact_dir(harness)
    html_path = resolved_dir / f"{slug}.html"
    design_path = resolved_dir / f"{slug}.DESIGN.md"

    return _validate_paths(slug, html_path, design_path)


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
