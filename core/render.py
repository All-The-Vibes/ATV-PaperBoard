"""core/render.py — RENDER pillar for atv-paperboard.

Converts input data + a DESIGN.md path into a paired HTML + DESIGN.md + meta.yaml triple.

Input contract:
  input_data['title']     — required, string used for slug + <title>
  input_data['subtitle']  — optional, rendered as <h2> below title
  input_data['body_html'] — already-rendered HTML; takes precedence if present
  input_data['body_md']   — markdown; converted via a tiny built-in converter
  input_data['rows']      — list of dicts; rendered as a table (column order = first-row keys)

If none of body_html/body_md/rows is present, the body falls back to a
formatted JSON dump so the artifact is still self-explanatory.

API surface used:
  bridge.export(design_path: Path, fmt: str) -> dict
  bridge.lint(design_path: Path) -> dict   ({findings: [...], summary: {...}})
  detect.detect_harness() -> str
"""
from __future__ import annotations

import datetime
import hashlib
import html as _html_lib
import http.server
import json
import os
import re
import sys
import threading
import warnings
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
_GENERATOR = "atv-paperboard/0.1.0"

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

    # Export tokens from DESIGN.md.
    #
    # Strategy: try the Node bridge first (authoritative — full Tailwind export
    # semantics from @google/design.md). If the bridge is unavailable for ANY
    # reason (module missing, node missing, node_modules not installed, lint
    # findings, JSON parse error), fall back to a pure-Python YAML reader so the
    # render still applies design tokens. The bridge governs lint_passed; the
    # YAML fallback assumes lint_passed=False since it can't run the upstream
    # lint rules.
    tokens: dict[str, str] = {}
    lint_passed = False
    bridge_ok = False
    try:
        from core import bridge as _bridge  # noqa: PLC0415

        export_dict = _bridge.export(design_path, fmt="tailwind")
        tokens = tokens_from_export(export_dict, tier=tier)
        lint_result = _bridge.lint(design_path)
        findings = lint_result.get("findings", [])
        blocking = [f for f in findings if isinstance(f, dict) and f.get("severity") in ("error", "warning")]
        lint_passed = len(blocking) == 0
        bridge_ok = True
    except Exception:
        bridge_ok = False

    if not bridge_ok:
        # Pure-Python fallback: parse the DESIGN.md YAML frontmatter directly
        # and synthesize a Tailwind-shaped dict so tokens_from_export() still
        # produces the right CSS variables for the active tier.
        try:
            synthetic_export = _export_from_design_yaml(design_path)
            tokens = tokens_from_export(synthetic_export, tier=tier)
        except Exception:
            tokens = {}

    # Resolve destination paths
    html_path = output_dir / f"{slug}.html"
    dest_design_path = output_dir / f"{slug}.DESIGN.md"
    meta_path = output_dir / f"{slug}.meta.yaml"

    # Copy DESIGN.md sidecar
    design_content = Path(design_path).read_text(encoding="utf-8")
    dest_design_path.write_text(design_content, encoding="utf-8")

    # Render HTML via Jinja2
    body_html = _default_body_html(input_data)
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
        "generator": _GENERATOR,
        "harness": _detect_harness_safe(),
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


def _export_from_design_yaml(design_path: Path) -> dict[str, Any]:
    """Pure-Python fallback that reads DESIGN.md YAML frontmatter and synthesizes
    a Tailwind-shaped export dict compatible with ``_flatten_tailwind()``.

    Used when the @google/design.md Node bridge is unavailable (node missing,
    node_modules not installed, etc.). The fallback supports color and typography
    tokens — the same subset v0.1.0 promises to render. Spacing/rounded tokens
    are read but not currently consumed by the Pico/Daisy CSS-var maps.

    Frontmatter shape expected (matches designs/*.DESIGN.md)::

        colors:
          primary: "#1A1A1A"
          secondary: "#3B82F6"
          ...
        typography:
          body: {fontFamily: "system-ui, ...", fontSize: 16px, ...}
          heading: {...}
          mono: {...}

    Returns the same shape ``bridge.export(fmt='tailwind')`` returns so the
    downstream ``tokens_from_export()`` codepath stays identical.
    """
    text = Path(design_path).read_text(encoding="utf-8")
    # Frontmatter is the block between the first two '---' lines.
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter_yaml = text[3:end]
    try:
        fm = yaml.safe_load(frontmatter_yaml) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(fm, dict):
        return {}

    export: dict[str, Any] = {"colors": {}, "fontFamily": {}, "fontSize": {}}

    # Colors: scalar hex → {"DEFAULT": "#...", "500": "#..."} so both shaded
    # and unshaded forms flatten correctly.
    colors = fm.get("colors") or {}
    if isinstance(colors, dict):
        for name, value in colors.items():
            if isinstance(value, str):
                export["colors"][name] = {"DEFAULT": value, "500": value}
            elif isinstance(value, dict):
                export["colors"][name] = value

    # Typography: pull fontFamily and fontSize from the body/heading/mono blocks.
    typography = fm.get("typography") or {}
    if isinstance(typography, dict):
        for role_name, role_key in (("sans", "body"), ("heading", "heading"), ("mono", "mono")):
            block = typography.get(role_key)
            if not isinstance(block, dict):
                continue
            ff = block.get("fontFamily")
            if isinstance(ff, str):
                # Split comma-separated list into the array form _flatten_tailwind expects.
                export["fontFamily"][role_name] = [s.strip().strip('"') for s in ff.split(",")]
            fs = block.get("fontSize")
            if isinstance(fs, (str, int, float)):
                size_key = "base" if role_key == "body" else role_key
                export["fontSize"][size_key] = str(fs)

    return export


def _detect_harness_safe() -> str:
    """Return the detected harness string, or 'standalone' on ImportError."""
    try:
        from core.detect import detect_harness  # noqa: PLC0415
        return detect_harness()
    except (ImportError, Exception):
        return "standalone"


def _default_body_html(input_data: dict[str, Any]) -> str:
    """Convert input_data to an HTML body string.

    Priority:
      1. body_html — returned as-is.
      2. body_md   — converted via tiny built-in markdown converter.
      3. rows      — rendered as an HTML <table>.
      4. fallback  — <pre><code> with JSON dump.

    A header section (h1 title + h2 subtitle) is always prepended.
    """
    parts: list[str] = []

    title = input_data.get("title")
    subtitle = input_data.get("subtitle")
    if title:
        parts.append(f"<h1>{_html_lib.escape(str(title))}</h1>")
    if subtitle:
        parts.append(f"<h2>{_html_lib.escape(str(subtitle))}</h2>")

    if "body_html" in input_data:
        parts.append(str(input_data["body_html"]))
        return "\n".join(parts)

    if "body_md" in input_data:
        parts.append(_md_to_html(str(input_data["body_md"])))
        return "\n".join(parts)

    rows = input_data.get("rows")
    if rows and isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict):
        parts.append(_rows_to_table(rows))
        return "\n".join(parts)

    # Fallback: JSON dump
    parts.append(f"<pre><code>{_html_lib.escape(json.dumps(input_data, indent=2))}</code></pre>")
    return "\n".join(parts)


def _md_to_html(md: str) -> str:
    """Tiny markdown -> HTML converter using re only.

    Supports: headings (#/##/###), **bold**, *italic*, `code`,
    [links](url), unordered bullet lists (- / *), and paragraphs.
    """
    lines = md.split("\n")
    html_lines: list[str] = []
    in_ul = False
    in_p = False

    def close_p():
        nonlocal in_p
        if in_p:
            html_lines.append("</p>")
            in_p = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False

    def inline(text: str) -> str:
        text = _html_lib.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        return text

    for line in lines:
        h3 = re.match(r"^### (.+)$", line)
        h2 = re.match(r"^## (.+)$", line)
        h1 = re.match(r"^# (.+)$", line)
        li = re.match(r"^[-*] (.+)$", line)

        if h3:
            close_p(); close_ul()
            html_lines.append(f"<h3>{inline(h3.group(1))}</h3>")
        elif h2:
            close_p(); close_ul()
            html_lines.append(f"<h2>{inline(h2.group(1))}</h2>")
        elif h1:
            close_p(); close_ul()
            html_lines.append(f"<h1>{inline(h1.group(1))}</h1>")
        elif li:
            close_p()
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{inline(li.group(1))}</li>")
        elif line.strip() == "":
            close_p(); close_ul()
        else:
            close_ul()
            if not in_p:
                html_lines.append("<p>")
                in_p = True
            html_lines.append(inline(line))

    close_p()
    close_ul()
    return "\n".join(html_lines)


def _rows_to_table(rows: list[dict]) -> str:
    """Render a list of dicts as an HTML table with thead/tbody."""
    headers = list(rows[0].keys())
    th_cells = "".join(f"<th>{_html_lib.escape(str(h))}</th>" for h in headers)
    thead = f"<thead><tr>{th_cells}</tr></thead>"
    tbody_rows: list[str] = []
    for row in rows:
        td_cells = "".join(
            f"<td>{_html_lib.escape(str(row.get(h, '')))}</td>" for h in headers
        )
        tbody_rows.append(f"<tr>{td_cells}</tr>")
    tbody = f"<tbody>{''.join(tbody_rows)}</tbody>"
    return f"<table>{thead}{tbody}</table>"


def _flatten_tailwind(export_dict: dict[str, Any]) -> dict[str, str]:
    """Flatten a Tailwind config dict into ``--color-primary-500`` style keys.

    Accepts both shapes the @google/design.md CLI may emit:
      1. Flat:   {"colors": {...}, "fontFamily": {...}, ...}
      2. Nested: {"theme": {"extend": {"colors": {...}, ...}}}   ← Tailwind v3 config

    The nested form is what `design.md export --format tailwind` produces today;
    the flat form is preserved for forward compatibility and unit-test fixtures.
    """
    # Unwrap theme.extend wrapper if present (Tailwind v3 config shape).
    theme = export_dict.get("theme")
    if isinstance(theme, dict):
        extend = theme.get("extend")
        if isinstance(extend, dict):
            export_dict = extend

    # ── Unknown-shape guard ───────────────────────────────────────────────────
    # Fire if neither the theme.extend wrapper was found nor a top-level
    # "colors" key is present — likely a future @google/design.md schema change.
    if theme is None and "colors" not in export_dict:
        warnings.warn(
            "atv-paperboard: _flatten_tailwind received unrecognized export shape"
            " (no 'theme.extend' wrapper and no top-level 'colors' key)."
            f" Got top-level keys: {list(export_dict.keys())}."
            " Token injection will fall back to empty."
            " This may indicate a @google/design.md schema change.",
            UserWarning,
            stacklevel=2,
        )

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
