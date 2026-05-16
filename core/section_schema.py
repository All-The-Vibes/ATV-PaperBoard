"""core/section_schema.py — Canonical schema for the atv-tier sections graph.

This module documents the input shape every agent (Claude Code, Copilot CLI,
Codex CLI) should construct when piping JSON to ``paperboard render --tier atv``.
It is the single source of truth consumed by:

  * ``paperboard schema`` subcommand (CLI discovery)
  * ``skills/render-artifact/SKILL.md`` documentation block

Every entry corresponds to an emitter registered in ``core/render._SECTION_EMITTERS``.
Keeping the description / fields / example here (rather than re-deriving from the
emitter source) preserves human-readable usage hints and round-trippable example
JSON while staying close enough to the emitters that drift is easy to catch in
review.

When adding a new section kind, update both this dict AND
``core/render._SECTION_EMITTERS`` together.
"""
from __future__ import annotations

from typing import Any

SECTION_SCHEMA: dict[str, dict[str, Any]] = {
    "hero": {
        "description": (
            "Top-of-page eyebrow + headline + sub + meta strip. "
            "Use exactly one per artifact, as the first section."
        ),
        "fields": {
            "eyebrow": "Small uppercase label above the headline. Optional.",
            "title": "Main H1 headline.",
            "title_into": "Optional grayed-out continuation rendered after the title.",
            "sub": "Lede paragraph below the headline. Optional.",
            "meta": "List of {label, value} pairs rendered as a horizontal strip below the sub. Optional.",
        },
        "example": {
            "kind": "hero",
            "eyebrow": "Release report",
            "title": "ATV tier renders artifacts as designed documents.",
            "title_into": "not colored tables.",
            "sub": "Six section kinds, one opinionated dark template, zero CDN dependencies.",
            "meta": [
                {"label": "Version", "value": "v0.2.0"},
                {"label": "Tier", "value": "atv"},
            ],
        },
    },
    "sec": {
        "description": (
            "Numbered section wrapper with eyebrow + h2 + lede + nested body. "
            "Contains other section kinds as children via the body array."
        ),
        "fields": {
            "num": "Section number, monospaced. Optional. Convention: '01', '02', ...",
            "eyebrow": "Small label above the h2. Optional.",
            "title": "Section h2 headline.",
            "aside": "Right-aligned pill in the section head. Optional.",
            "lede": "Lede paragraph below the head. Optional.",
            "zebra": "Boolean; if true, alternates background tint. Optional.",
            "tight": "Boolean; if true, reduces vertical padding. Optional.",
            "body": "List of child sections (kinds: stack-list, dep-list, q-list, steps, etc.).",
        },
        "example": {
            "kind": "sec",
            "num": "01",
            "eyebrow": "Status",
            "title": "Pipeline health.",
            "lede": "Build, lint, and tests after the v0.2.0 changes.",
            "body": [
                {"kind": "status-table", "rows": [{"check": "build", "status": "PASS"}]},
            ],
        },
    },
    "stack-list": {
        "description": (
            "Three-column hairline list: name + tag on the left, why in the middle, "
            "fix/recommendation on the right. Best for item/why/fix tables."
        ),
        "fields": {
            "rows": (
                "List of {name, tag, tag_kind, why, fix}. "
                "tag_kind ∈ {shadcn, tailwind, typescript} controls the tag color. "
                "why and fix may contain inline HTML (e.g. <code>...</code>)."
            ),
        },
        "example": {
            "kind": "stack-list",
            "rows": [
                {
                    "name": "hero",
                    "tag": "layout",
                    "tag_kind": "shadcn",
                    "why": "Top-of-page eyebrow, headline, sub, meta strip.",
                    "fix": "<code>{kind: hero, title, sub, meta}</code>",
                },
            ],
        },
    },
    "dep-list": {
        "description": (
            "Four-column list (name+tag / role / why / version). "
            "Best for dependency audits and package inventories."
        ),
        "fields": {
            "rows": (
                "List of {name, tag, role, why, version}. "
                "tag ∈ {required, transitive} controls the tag color."
            ),
        },
        "example": {
            "kind": "dep-list",
            "rows": [
                {
                    "name": "jinja2",
                    "tag": "required",
                    "role": "templating",
                    "why": "Renders the atv-tier template.",
                    "version": ">=3.1.0",
                },
            ],
        },
    },
    "q-list": {
        "description": (
            "Numbered Q&A list. Renders each row with a left-side number gutter "
            "and an h4 question + paragraph body. Best for intake checklists."
        ),
        "fields": {
            "rows": (
                "List of {num, title, body}. "
                "num is optional and auto-derived from row index (zero-padded). "
                "body may contain inline HTML."
            ),
        },
        "example": {
            "kind": "q-list",
            "rows": [
                {"num": "01", "title": "What is the target tier?", "body": "Default is <code>atv</code>."},
                {"num": "02", "title": "Where does input come from?", "body": "Agent-constructed JSON via stdin."},
            ],
        },
    },
    "steps": {
        "description": (
            "Vertical timeline with monospaced number markers. "
            "Best for sequential procedures or onboarding flows."
        ),
        "fields": {
            "rows": (
                "List of {num, title, desc}. "
                "num is optional and auto-derived (zero-padded, starts at 00). "
                "desc may contain inline HTML."
            ),
        },
        "example": {
            "kind": "steps",
            "rows": [
                {"num": "01", "title": "Install", "desc": "<code>pip install atv-paperboard</code>"},
                {"num": "02", "title": "Render", "desc": "<code>paperboard render --input report.json</code>"},
            ],
        },
    },
    "code-shell": {
        "description": (
            "macOS-style code block with traffic-light dots and a language tag. "
            "Best for code samples in documentation."
        ),
        "fields": {
            "lang": "Language label shown in the title bar (e.g. 'json', 'python').",
            "code": "Raw code body. Newlines preserved; HTML-escaped on render.",
            "path": "Optional file-path label rendered above the code block.",
        },
        "example": {
            "kind": "code-shell",
            "lang": "json",
            "path": "report.json",
            "code": '{\n  "title": "Pipeline Report",\n  "sections": []\n}',
        },
    },
    "color-strip": {
        "description": (
            "Grid of color swatch cards (hex / name / role). "
            "Best for palette documentation."
        ),
        "fields": {
            "colors": "List of {hex, name, role}. hex is the swatch fill (e.g. '#f59e0b').",
        },
        "example": {
            "kind": "color-strip",
            "colors": [
                {"hex": "#f59e0b", "name": "amber", "role": "accent"},
                {"hex": "#0a0a0a", "name": "ink", "role": "background"},
            ],
        },
    },
    "fit-row": {
        "description": (
            "Pill row with leading green/rose dots. "
            "Best for fit / avoid signal pairs ('Use for X', 'Avoid for Y')."
        ),
        "fields": {
            "items": (
                "List of {label, avoid?} dicts OR plain strings. "
                "avoid=true renders a rose dot; default is green."
            ),
        },
        "example": {
            "kind": "fit-row",
            "items": [
                {"label": "Dashboards"},
                {"label": "Single-page reports"},
                {"label": "Marketing pages", "avoid": True},
            ],
        },
    },
    "anti": {
        "description": (
            "Anti-pattern block with implicit 'DO NOT' label and bulleted list. "
            "Best for don'ts lists in design-system docs."
        ),
        "fields": {
            "items": "List of strings (may contain inline HTML). Rendered as <li> bullets.",
        },
        "example": {
            "kind": "anti",
            "items": [
                "Use drop shadows instead of borders.",
                "Hard-code colors outside the token system.",
            ],
        },
    },
    "checklist": {
        "description": (
            "Single-column list with mono '·' markers. "
            "Best for verification checklists and acceptance criteria."
        ),
        "fields": {
            "items": "List of strings (may contain inline HTML).",
        },
        "example": {
            "kind": "checklist",
            "items": [
                "All tests pass.",
                "ruff clean.",
                "CHANGELOG updated.",
            ],
        },
    },
    "callout": {
        "description": (
            "Accent-tinted advisory block with optional title and bullet list. "
            "Use sparingly — at most one or two per artifact."
        ),
        "fields": {
            "title": "Optional h4 title.",
            "items": "Optional list of strings rendered as <li> bullets.",
            "body": "Optional paragraph body (may contain inline HTML).",
        },
        "example": {
            "kind": "callout",
            "title": "Heads up",
            "items": [
                "The sections array bypasses rows/body_md when present.",
                "Pick one input mode per artifact.",
            ],
        },
    },
    "subhead": {
        "description": (
            "Mono uppercase label inside a section. Use for sub-grouping inside a sec body."
        ),
        "fields": {
            "text": "Label text. Rendered uppercase via CSS.",
        },
        "example": {"kind": "subhead", "text": "Inputs"},
    },
    "props-table": {
        "description": (
            "Classic prop/type/default/notes table. "
            "Best for API surfaces and configuration references."
        ),
        "fields": {
            "headers": "Optional list of column headers. Defaults to ['Prop', 'Type', 'Default', 'Notes'].",
            "rows": "List of {name, type, default, notes}. notes may contain inline HTML.",
        },
        "example": {
            "kind": "props-table",
            "rows": [
                {
                    "name": "tier",
                    "type": "string",
                    "default": "atv",
                    "notes": "One of <code>atv</code>, <code>pico</code>, <code>daisy</code>.",
                },
            ],
        },
    },
    "status-table": {
        "description": (
            "Typed table where the status / state / result column auto-renders as a colored badge. "
            "DONE/PASS green, FAIL/ERROR red, IN_PROGRESS indigo. "
            "Best for build matrices and CI dashboards."
        ),
        "fields": {
            "rows": (
                "List of dicts. Column headers are inferred from the first row's keys. "
                "Any column named status / state / result is rendered as a badge."
            ),
        },
        "example": {
            "kind": "status-table",
            "rows": [
                {"check": "build", "status": "PASS"},
                {"check": "lint", "status": "PASS"},
                {"check": "tests", "status": "FAIL"},
            ],
        },
    },
}


def list_kinds() -> list[str]:
    """Return the section kinds in registration order."""
    return list(SECTION_SCHEMA.keys())


def get_kind(name: str) -> dict[str, Any] | None:
    """Return the schema entry for a single kind, or None if unknown."""
    return SECTION_SCHEMA.get(name)
