"""core/gallery.py — COMPOUND pillar for atv-paperboard.

Scans the artifact directory for all *.meta.yaml sidecars, sorts by created_at
descending, and renders a gallery.html index using the gallery.html.j2 template.

Performance target: < 1 second for up to 50 artifacts (file-system listing only;
no per-artifact HTML parsing).
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_DEFAULT_DESIGN = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"


def regenerate_gallery(harness: str | None = None, artifact_dir: Path | None = None) -> Path:
    """Scan the artifact directory and (re-)write gallery.html.

    Args:
        harness: Harness name used to resolve the artifact directory.
                 ``None`` defaults to ``"standalone"``.
        artifact_dir: If provided, use this directory instead of the harness default.

    Returns:
        Path to the written ``gallery.html``.
    """
    if artifact_dir is not None:
        art_dir = artifact_dir
    else:
        resolved = harness or "standalone"
        art_dir = _resolve_artifact_dir(resolved)
    art_dir.mkdir(parents=True, exist_ok=True)

    # Collect all meta.yaml files — file-system listing only, no HTML parsing.
    meta_files = sorted(
        art_dir.glob("*.meta.yaml"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    artifacts: list[dict[str, Any]] = []
    for meta_file in meta_files:
        try:
            meta = _fast_meta_load(meta_file)
        except Exception:  # noqa: BLE001
            continue

        slug = meta.get("slug") or meta_file.stem.replace(".meta", "")
        html_name = f"{slug}.html"
        artifacts.append(
            {
                "slug": slug,
                "title": meta.get("title") or slug.replace("-", " ").title(),
                "harness": meta.get("harness", "unknown"),
                "design": meta.get("design", ""),
                "tier": meta.get("tier", "pico"),
                "created_at": meta.get("created_at", ""),
                "html_name": html_name,
                "html_exists": (art_dir / html_name).exists(),
            }
        )

    # Export tokens from the project default DESIGN.md.
    # Strategy mirrors core/render.py: try the Node bridge first; on ANY failure
    # fall back to the pure-Python YAML reader so the gallery still themes
    # correctly when @google/design.md is not installed.
    tokens: dict[str, str] = {}
    try:
        from core import bridge as _bridge  # noqa: PLC0415
        from core.render import tokens_from_export  # noqa: PLC0415

        export_dict = _bridge.export(_DEFAULT_DESIGN, fmt="tailwind")
        tokens = tokens_from_export(export_dict, tier="pico")
    except Exception:  # noqa: BLE001
        try:
            from core.render import (  # noqa: PLC0415
                _export_from_design_yaml,
                tokens_from_export,
            )

            synthetic_export = _export_from_design_yaml(_DEFAULT_DESIGN)
            tokens = tokens_from_export(synthetic_export, tier="pico")
        except Exception:  # noqa: BLE001
            tokens = {}

    # Render gallery template.
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("gallery.html.j2")
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )
    html_content = template.render(
        artifacts=artifacts,
        tokens=tokens,
        generated_at=generated_at,
        total=len(artifacts),
    )

    gallery_path = art_dir / "gallery.html"
    gallery_path.write_text(html_content, encoding="utf-8")
    return gallery_path


# ── Internal helpers ──────────────────────────────��───────────────────────────


def _resolve_artifact_dir(harness: str) -> Path:
    try:
        from core import persist as _persist  # noqa: PLC0415

        return _persist.artifact_dir(harness)
    except (ImportError, RuntimeError):
        return Path.cwd() / "paperboard-artifacts"


# Regex: matches ``key: value`` lines in the flat top-level of a meta.yaml.
_META_LINE_RE = re.compile(r'^([a-z_]+):\s*["\']?([^"\'#\n]*?)["\']?\s*$', re.MULTILINE)


def _fast_meta_load(meta_file: Path) -> dict[str, Any]:
    """Read a meta.yaml using a fast regex scan (no YAML parser overhead).

    Falls back to an empty dict on any error.  Only extracts scalar top-level
    keys — sufficient for gallery card rendering.
    """
    try:
        text = meta_file.read_text(encoding="utf-8")
    except OSError:
        return {}
    result: dict[str, Any] = {}
    for m in _META_LINE_RE.finditer(text):
        result[m.group(1)] = m.group(2).strip()
    return result
