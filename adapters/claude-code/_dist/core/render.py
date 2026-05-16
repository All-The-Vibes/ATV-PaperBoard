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

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_DEFAULT_DESIGN = Path(__file__).parent / "designs" / "paperboard.DESIGN.md"
_TIER_TEMPLATES = {
    "pico": "pico-tier.html.j2",
    "daisy": "daisy-tier.html.j2",
    "atv": "atv-tier.html.j2",
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
    "--color-border-500": "--pico-border-color",
    # Pico also reads `--pico-muted-border-color` for the footer divider and other
    # subtle separators; map our `colors.border` token to it as well.
    "--font-family": "--pico-font-family",
    "--font-size": "--pico-font-size",
    # Heading family/size aliases: DESIGN.md `typography.body` is emitted as
    # `--font-family-body` by the flattener (typography uses body/heading/mono
    # role names, not sans/DEFAULT), so a generic `--font-family` alias never
    # fires through the flattener's `sans`/`DEFAULT` early-return. Map the
    # role-specific keys directly so Pico's font stack actually changes.
    "--font-family-body": "--pico-font-family",
    "--font-size-body": "--pico-font-size",
    "--color-accent": "--pico-contrast",
    "--color-accent-500": "--pico-contrast",
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
    "--font-family-body": "--font-family",
    "--font-size-body": "--font-size",
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
    template_ctx: dict[str, Any] = {
        "title": title,
        "tokens": tokens,
        "body_html": body_html,
        "design_md_path": dest_design_path.name,
    }
    # The atv tier supports a topbar with brand / breadcrumb / status pill.
    if tier == "atv":
        template_ctx["brand"] = input_data.get("brand", "atv-paperboard")
        template_ctx["breadcrumb"] = input_data.get("breadcrumb", "")
        template_ctx["status_tag"] = input_data.get("status_tag", "rendered")
    html_content = template.render(**template_ctx)
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
      1. sections   — rich atv-tier section graph (hero / sec / stack-list / dep-list / q-list / steps / code-shell / color-strip / fit-row / anti / checklist / callout / props-table / file-path / subhead)
      2. body_html  — returned as-is.
      3. body_md    — converted via tiny built-in markdown converter.
      4. rows       — rendered as an HTML <table>.
      5. fallback   — <pre><code> with JSON dump.

    A header section (h1 title + h2 subtitle) is always prepended UNLESS
    `sections` is supplied (those sections own their own headers via the hero kind).
    """
    parts: list[str] = []

    # Rich section graph (atv tier)
    sections = input_data.get("sections")
    if sections and isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            kind = section.get("kind", "")
            emitter = _SECTION_EMITTERS.get(kind)
            if emitter:
                parts.append(emitter(section))
        return "\n".join(parts)

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


# ── Section emitters for the atv tier ─────��──────────────────────────────────


def _e(s: Any) -> str:
    """Shorthand for HTML-escape with str-coercion."""
    return _html_lib.escape(str(s)) if s is not None else ""


def _classes(*xs: str) -> str:
    return " ".join(x for x in xs if x)


def _emit_hero(s: dict[str, Any]) -> str:
    """`hero` section: eyebrow + h1 + sub + meta strip."""
    eyebrow = s.get("eyebrow", "")
    title = s.get("title", "")
    title_into = s.get("title_into", "")  # optional grayed-out continuation
    sub = s.get("sub", "")
    meta = s.get("meta", [])  # list of {label, value}

    title_html = _e(title)
    if title_into:
        title_html = f'{title_html} <span class="into">{_e(title_into)}</span>'

    meta_html = ""
    if meta:
        items = "".join(
            f'<div class="item">{_e(m.get("label", ""))} <span class="v">{_e(m.get("value", ""))}</span></div>'
            for m in meta if isinstance(m, dict)
        )
        meta_html = f'<div class="hero-meta">{items}</div>'

    eyebrow_html = (
        f'<div class="eyebrow"><span class="bar"></span>{_e(eyebrow)}</div>'
        if eyebrow else ""
    )
    sub_html = f'<p class="sub">{_e(sub)}</p>' if sub else ""

    return (
        f'<section class="hero">'
        f'{eyebrow_html}'
        f'<h1>{title_html}</h1>'
        f'{sub_html}'
        f'{meta_html}'
        f'</section>'
    )


def _emit_section(s: dict[str, Any]) -> str:
    """`sec` wrapper: numbered section head with eyebrow + h2 + lede + inner content."""
    num = s.get("num", "")
    eyebrow = s.get("eyebrow", "")
    title = s.get("title", "")
    aside = s.get("aside", "")
    lede = s.get("lede", "")
    zebra = s.get("zebra", False)
    tight = s.get("tight", False)
    inner_sections = s.get("body", [])  # list of nested sub-kinds

    sec_classes = _classes("sec", "zebra" if zebra else "", "tight" if tight else "")

    head_parts = []
    if num:     head_parts.append(f'<span class="num mono">{_e(num)}</span>')
    if eyebrow: head_parts.append(f'<span class="eyebrow">{_e(eyebrow)}</span>')
    if title:   head_parts.append(f'<h2>{_e(title)}</h2>')
    if aside:   head_parts.append(f'<span class="aside">{_e(aside)}</span>')

    head_html = f'<div class="sec-head">{"".join(head_parts)}</div>' if head_parts else ""
    lede_html = f'<p class="sec-lede">{_e(lede)}</p>' if lede else ""

    inner_html = ""
    if isinstance(inner_sections, list):
        for child in inner_sections:
            if not isinstance(child, dict):
                continue
            emitter = _SECTION_EMITTERS.get(child.get("kind", ""))
            if emitter:
                inner_html += emitter(child)

    return f'<section class="{sec_classes}">{head_html}{lede_html}{inner_html}</section>'


def _emit_stack_list(s: dict[str, Any]) -> str:
    """`stack-list`: three-column list (name+tag / why / fix). Rows: [{name, tag, tag_kind, why, fix}]."""
    rows = s.get("rows", [])
    row_html = []
    tag_class_map = {"shadcn": "stack-tag-shadcn", "tailwind": "stack-tag-tailwind", "typescript": "stack-tag-typescript"}
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = r.get("name", "")
        tag = r.get("tag", "")
        tag_kind = r.get("tag_kind", "")
        why = r.get("why", "")
        fix = r.get("fix", "")
        tag_html = ""
        if tag:
            extra = tag_class_map.get(tag_kind, "")
            tag_html = f'<span class="stack-tag {extra}">{_e(tag)}</span>'
        row_html.append(
            f'<div class="stack-row">'
            f'<div class="stack-name"><span class="mono">{_e(name)}</span>{tag_html}</div>'
            f'<div class="stack-why">{why}</div>'  # allow inline html
            f'<div class="stack-fix muted">{fix}</div>'
            f'</div>'
        )
    return f'<div class="stack-list">{"".join(row_html)}</div>'


def _emit_dep_list(s: dict[str, Any]) -> str:
    """`dep-list`: four-column list (name+tag / role / why / version)."""
    rows = s.get("rows", [])
    row_html = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = r.get("name", "")
        tag = r.get("tag", "")  # required | transitive | (any)
        role = r.get("role", "")
        why = r.get("why", "")
        version = r.get("version", "")
        tag_class = "dep-tag-required" if tag == "required" else ("dep-tag-transitive" if tag == "transitive" else "")
        tag_html = f'<span class="dep-tag {tag_class}">{_e(tag)}</span>' if tag else ""
        row_html.append(
            f'<div class="dep-row">'
            f'<div class="dep-col-name"><span class="mono dep-name">{_e(name)}</span>{tag_html}</div>'
            f'<div class="dep-col-role">{_e(role)}</div>'
            f'<div class="dep-col-why">{why}</div>'
            f'<div class="dep-col-ver mono">{_e(version)}</div>'
            f'</div>'
        )
    return f'<div class="dep-list">{"".join(row_html)}</div>'


def _emit_q_list(s: dict[str, Any]) -> str:
    """`q-list`: numbered Q&A list. Rows: [{num, title, body}]."""
    rows = s.get("rows", [])
    row_html = []
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            continue
        num = r.get("num", f"{i:02d}")
        title = r.get("title", "")
        body = r.get("body", "")
        row_html.append(
            f'<div class="q-row">'
            f'<span class="q-num mono">{_e(num)}</span>'
            f'<div class="q-body"><h4>{_e(title)}</h4><p>{body}</p></div>'
            f'</div>'
        )
    return f'<div class="q-list">{"".join(row_html)}</div>'


def _emit_steps(s: dict[str, Any]) -> str:
    """`steps`: timeline of numbered steps. Rows: [{num, title, desc}]."""
    rows = s.get("rows", [])
    row_html = []
    for i, r in enumerate(rows, start=0):
        if not isinstance(r, dict):
            continue
        num = r.get("num", f"{i:02d}")
        title = r.get("title", "")
        desc = r.get("desc", "")
        row_html.append(
            f'<div class="step-row">'
            f'<span class="step-num mono">{_e(num)}</span>'
            f'<div class="step-body"><div class="step-title">{_e(title)}</div><div class="step-desc">{desc}</div></div>'
            f'</div>'
        )
    return f'<div class="steps">{"".join(row_html)}</div>'


def _emit_code_shell(s: dict[str, Any]) -> str:
    """`code-shell`: macOS-style code block with traffic dots + language tag."""
    lang = s.get("lang", "")
    code = s.get("code", "")
    path = s.get("path", "")
    path_html = f'<div class="file-path">{_e(path)}</div>' if path else ""
    return (
        f'{path_html}'
        f'<div class="code-shell">'
        f'<div class="code-bar">'
        f'<span class="code-dots"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></span>'
        f'<span class="code-lang">{_e(lang)}</span>'
        f'</div>'
        f'<pre class="code"><code>{_e(code)}</code></pre>'
        f'</div>'
    )


def _emit_color_strip(s: dict[str, Any]) -> str:
    """`color-strip`: grid of color swatches. Colors: [{hex, name, role}]."""
    colors = s.get("colors", [])
    cells = []
    for c in colors:
        if not isinstance(c, dict):
            continue
        hex_value = c.get("hex", "#000000")
        name = c.get("name", "")
        role = c.get("role", "")
        cells.append(
            f'<div class="color-cell">'
            f'<div class="color-swatch" style="background:{_e(hex_value)};"></div>'
            f'<div class="color-meta">'
            f'<span class="color-hex mono">{_e(hex_value)}</span>'
            f'<span class="color-name">{_e(name)}</span>'
            f'<span class="color-role">{_e(role)}</span>'
            f'</div>'
            f'</div>'
        )
    return f'<div class="color-strip">{"".join(cells)}</div>'


def _emit_fit_row(s: dict[str, Any]) -> str:
    """`fit-row`: pill list with leading status dots. Items: [{label, avoid?}]."""
    items = s.get("items", [])
    chip_html = []
    for it in items:
        if isinstance(it, dict):
            label = it.get("label", "")
            avoid = bool(it.get("avoid", False))
        else:
            label = str(it)
            avoid = False
        cls = "fit avoid" if avoid else "fit"
        chip_html.append(f'<span class="{cls}">{_e(label)}</span>')
    return f'<div class="fit-row">{"".join(chip_html)}</div>'


def _emit_anti(s: dict[str, Any]) -> str:
    """`anti`: anti-pattern block with DO NOT label and bullet list."""
    items = s.get("items", [])
    li = "".join(f'<li>{x}</li>' for x in items)
    return f'<div class="anti"><ul>{li}</ul></div>'


def _emit_checklist(s: dict[str, Any]) -> str:
    """`checklist`: single-column list with mono `·` markers."""
    items = s.get("items", [])
    rows = "".join(
        f'<div class="chk"><span class="chk-mark">·</span><span>{x}</span></div>'
        for x in items
    )
    return f'<div class="check-list">{rows}</div>'


def _emit_callout(s: dict[str, Any]) -> str:
    """`callout`: accent-tinted advisory block. Items: [...] (li bullets)."""
    title = s.get("title", "")
    items = s.get("items", [])
    body = s.get("body", "")
    title_html = f'<h4>{_e(title)}</h4>' if title else ""
    list_html = ""
    if items:
        list_html = "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    body_html = f"<p>{body}</p>" if body else ""
    return f'<div class="callout">{title_html}{list_html}{body_html}</div>'


def _emit_subhead(s: dict[str, Any]) -> str:
    return f'<div class="subhead">{_e(s.get("text", ""))}</div>'


def _emit_props_table(s: dict[str, Any]) -> str:
    """`props-table`: classic prop/type/default/notes table."""
    headers = s.get("headers", ["Prop", "Type", "Default", "Notes"])
    rows = s.get("rows", [])
    th = "".join(f"<th>{_e(h)}</th>" for h in headers)
    tr = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = r.get("name", "")
        type_ = r.get("type", "")
        default = r.get("default", "")
        notes = r.get("notes", "")
        tr.append(
            f'<tr>'
            f'<td class="mono prop-name">{_e(name)}</td>'
            f'<td><span class="type-pill mono">{_e(type_)}</span></td>'
            f'<td class="mono small muted">{_e(default)}</td>'
            f'<td class="muted">{notes}</td>'
            f'</tr>'
        )
    return f'<table class="props"><thead><tr>{th}</tr></thead><tbody>{"".join(tr)}</tbody></table>'


def _emit_status_table(s: dict[str, Any]) -> str:
    """`status-table`: typed table where the status column becomes a colored badge.

    Auto-detects a status column from headers matching status|state|result.
    Values like DONE / PASS get green badges, FAIL / ERROR red, IN_PROGRESS indigo, etc.
    Rows: list of dicts (column-name -> value).
    """
    rows = s.get("rows", [])
    if not rows or not isinstance(rows[0], dict):
        return ""
    headers = list(rows[0].keys())
    status_col = None
    for h in headers:
        if h.lower() in ("status", "state", "result"):
            status_col = h
            break

    th = "".join(f"<th>{_e(h)}</th>" for h in headers)
    tr = []
    for r in rows:
        cells = []
        for h in headers:
            v = str(r.get(h, ""))
            if h == status_col:
                badge_class = v.lower().replace("_", "-").replace(" ", "-")
                cells.append(f'<td><span class="badge {badge_class}">{_e(v)}</span></td>')
            else:
                cells.append(f'<td>{_e(v)}</td>')
        tr.append(f'<tr>{"".join(cells)}</tr>')
    return f'<table class="props"><thead><tr>{th}</tr></thead><tbody>{"".join(tr)}</tbody></table>'


# Registry of section kinds → emitter functions
_SECTION_EMITTERS: dict[str, Any] = {
    "hero": _emit_hero,
    "sec": _emit_section,
    "stack-list": _emit_stack_list,
    "dep-list": _emit_dep_list,
    "q-list": _emit_q_list,
    "steps": _emit_steps,
    "code-shell": _emit_code_shell,
    "color-strip": _emit_color_strip,
    "fit-row": _emit_fit_row,
    "anti": _emit_anti,
    "checklist": _emit_checklist,
    "callout": _emit_callout,
    "subhead": _emit_subhead,
    "props-table": _emit_props_table,
    "status-table": _emit_status_table,
}


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
