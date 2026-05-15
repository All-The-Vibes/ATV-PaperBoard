"""core/render.py — RENDER pillar for atv-paperboard.

Converts input data + a DESIGN.md path into a paired HTML + DESIGN.md + meta.yaml triple.

API surface used from the parallel agent:
  bridge.export(design_path: Path, format: str) -> dict   (format='tailwind')
  bridge.lint(design_path: Path) -> list[dict]

If bridge.py doesn't exist yet, render_artifact will note the absence and proceed with
an empty token dict (graceful degradation).

TODO: Remove the graceful-degradation branch once bridge.py is delivered.
"""
from __future__ import annotations

import datetime
import hashlib
import http.server
import os
import re
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

# ── Constants ────────────────────────────────────────────────────────────────

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_DEFAULT_DESIGN = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"
_TIER_TEMPLATES = {
    "pico": "pico-tier.html.j2",
    "daisy": "daisy-tier.html.j2",
}
_HARNESS = "atv-paperboard/0.1.0"

# daisyUI uses short HSL-component CSS vars; Pico uses longer semantic names.
_PICO_TOKEN_MAP: dict[str, str] = {
    "--color-primary": "--pico-primary",
    "--color-primary-500": "--pico-primary",
    "--color-secondary": "--pico-secondary",
    "--color-secondary-500": "--pico-secondary",
    "--color-background": "--pico-background-color",
    "--color-foreground": "--pico-color",
    "--color-muted": "--pico-muted-color",
    "--color-border": "--pico-border-color",
    "--color-accent": "--pico-contrast",
    "--color-accent-500": "--pico-contrast",
    "--font-family": "--pico-font-family",
    "--font-size": "--pico-font-size",
}

_DAISY_TOKEN_MAP: dict[str, str] = {
    "--color-primary": "--p",
    "--color-primary-500": "--p",
    "--color-secondary": "--s",
    "--color-secondary-500": "--s",
    "--color-accent": "--a",
    "--color-accent-500": "--a",
    "--color-background": "--b1",
    "--color-foreground": "--bc",
    "--color-muted": "--b3",
    "--color-border": "--b2",
    "--font-family": "--font-family",
    "--font-size": "--font-size",
}


# ── Public API ────────────────────────────────────────────────────────────────


def render_artifact(
    input_data: dict[str, Any],
    design_path: Path,
    tier: str = "pico",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Render a paired HTML + DESIGN.md + meta.yaml triple.

    Args:
        input_data: Arbitrary dict (title, body_html, components, etc.).
        design_path: Path to the DESIGN.md sidecar to use.
        tier: CSS framework tier — ``'pico'`` or ``'daisy'``.
        output_dir: Where to write the triple; defaults to CWD/paperboard-artifacts.

    Returns:
        dict with keys: html_path, design_path, meta_path, slug.
    """
    if tier not in _TIER_TEMPLATES:
        raise ValueError(f"Unknown tier {tier!r}. Choose from: {list(_TIER_TEMPLATES)}")

    # Resolve output directory
    if output_dir is None:
        output_dir = Path.cwd() / "paperboard-artifacts"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    title = str(input_data.get("title", "Untitled Artifact"))
    slug = _slugify(title)

    # Ensure slug uniqueness within output_dir
    slug = _unique_slug(slug, output_dir)

    # Export tokens from DESIGN.md via bridge (graceful degradation if missing)
    tokens: dict[str, str] = {}
    lint_passed = False
    try:
        from core import bridge as _bridge  # noqa: PLC0415

        export_dict = _bridge.export(design_path, fmt="tailwind")
        tokens = tokens_from_export(export_dict, tier=tier)
        lint_result = _bridge.lint(design_path)
        # lint() returns {"findings": [...], "summary": {...}}
        lint_passed = len(lint_result.get("findings", [])) == 0
    except ImportError:
        # TODO: Remove once bridge.py is delivered by the parallel agent.
        tokens = {}
        lint_passed = False

    # Resolve destination paths
    html_path = output_dir / f"{slug}.html"
    dest_design_path = output_dir / f"{slug}.DESIGN.md"
    meta_path = output_dir / f"{slug}.meta.yaml"

    # Copy DESIGN.md sidecar
    design_content = Path(design_path).read_text(encoding="utf-8")
    dest_design_path.write_text(design_content, encoding="utf-8")

    # Render HTML via Jinja2
    body_html = str(input_data.get("body_html", ""))
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)
    template = env.get_template(_TIER_TEMPLATES[tier])
    html_content = template.render(
        title=title,
        tokens=tokens,
        body_html=body_html,
        design_md_path=dest_design_path.name,
    )
    html_path.write_text(html_content, encoding="utf-8")

    # Write meta.yaml sidecar
    meta: dict[str, Any] = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "harness": _HARNESS,
        "design": str(design_path),
        "tier": tier,
        "slug": slug,
        "lint_passed": lint_passed,
    }
    meta_path.write_text(yaml.dump(meta, sort_keys=True), encoding="utf-8")

    return {
        "html_path": html_path,
        "design_path": dest_design_path,
        "meta_path": meta_path,
        "slug": slug,
    }


def tokens_from_export(export_dict: dict[str, Any], tier: str = "pico") -> dict[str, str]:
    """Token-rename layer: Tailwind export → CSS vars for the active tier.

    The ``@google/design.md export --format tailwind`` output is a dict like::

        {
          "colors": {"primary": {"500": "#3B82F6"}, ...},
          "fontFamily": {"sans": ["system-ui", ...]},
          ...
        }

    This function flattens that into ``--color-primary-500``-style keys first,
    then maps them through the tier-specific rename map.

    Args:
        export_dict: Raw dict from ``bridge.export(format='tailwind')``.
        tier: ``'pico'`` or ``'daisy'``.

    Returns:
        Flat dict of CSS variable name → value (e.g. ``{'--pico-primary': '#3B82F6'}``).
    """
    rename_map = _PICO_TOKEN_MAP if tier == "pico" else _DAISY_TOKEN_MAP
    flat = _flatten_tailwind(export_dict)
    result: dict[str, str] = {}
    for tw_var, value in flat.items():
        dest = rename_map.get(tw_var)
        if dest:
            result[dest] = value
        else:
            # Pass through unknown vars with the tier prefix stripped
            result[tw_var] = value
    return result


# ── Internal helpers ──────────────────────────────────────────────────────────


def _flatten_tailwind(export_dict: dict[str, Any]) -> dict[str, str]:
    """Flatten a Tailwind config dict into ``--color-primary-500`` style keys."""
    flat: dict[str, str] = {}

    colors = export_dict.get("colors", {})
    for color_name, shades in colors.items():
        if isinstance(shades, dict):
            for shade, value in shades.items():
                if isinstance(value, str):
                    flat[f"--color-{color_name}-{shade}"] = value
                    # Also register without shade for direct references
                    if shade in ("DEFAULT", "500"):
                        flat[f"--color-{color_name}"] = value
        elif isinstance(shades, str):
            flat[f"--color-{color_name}"] = shades

    font_family = export_dict.get("fontFamily", {})
    for name, families in font_family.items():
        if isinstance(families, list):
            flat[f"--font-family-{name}"] = ", ".join(str(f) for f in families)
            if name in ("sans", "DEFAULT"):
                flat["--font-family"] = flat[f"--font-family-{name}"]
        elif isinstance(families, str):
            flat[f"--font-family-{name}"] = families

    font_size = export_dict.get("fontSize", {})
    for name, size in font_size.items():
        value = size[0] if isinstance(size, (list, tuple)) else size
        flat[f"--font-size-{name}"] = str(value)
        if name in ("base", "DEFAULT"):
            flat["--font-size"] = str(value)

    return flat


def _slugify(title: str) -> str:
    """Convert a title string to a URL/filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "artifact"


def _unique_slug(base: str, output_dir: Path) -> str:
    """Append a short hash suffix if ``base.html`` already exists."""
    candidate = base
    if not (output_dir / f"{candidate}.html").exists():
        return candidate
    suffix = hashlib.sha1(
        datetime.datetime.utcnow().isoformat().encode()
    ).hexdigest()[:6]
    return f"{base}-{suffix}"


def _serve_and_open(html_path: Path) -> None:
    """Start a loopback HTTP server and open the artifact in the browser.

    Skips opening if any of the following are true:
    - ``CLAUDE_CODE_REMOTE=true`` (remote Claude Code session)
    - ``GITHUB_ACTIONS=true`` (CI environment)
    - On Linux and neither ``DISPLAY`` nor ``WAYLAND_DISPLAY`` is set (headless)
    """
    env = os.environ
    if env.get("CLAUDE_CODE_REMOTE", "").lower() == "true":
        return
    if env.get("GITHUB_ACTIONS", "").lower() == "true":
        return
    if sys.platform.startswith("linux"):
        if not env.get("DISPLAY") and not env.get("WAYLAND_DISPLAY"):
            return

    html_path = html_path.resolve()
    serve_dir = html_path.parent

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(serve_dir), **kwargs)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            pass  # silence access log in interactive use

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/{html_path.name}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    webbrowser.open_new_tab(url)
