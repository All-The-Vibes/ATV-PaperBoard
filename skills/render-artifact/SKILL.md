---
name: render-artifact
description: >
  Render a structured input (JSON or Markdown) into a paired HTML + DESIGN.md + meta.yaml
  artifact triple. Serves the result on loopback HTTP and opens a browser tab (unless
  running headless/remote). Invokes `paperboard render` via the atv-paperboard CLI.
---

# render-artifact

Converts structured LLM output into a beautiful, linted HTML artifact governed by a DESIGN.md.

## Usage

```
paperboard render --input <path-or-> [--design <name|path|url>] [--tier atv|pico|daisy] [--no-open]
```

## Tier selection

- **Default: `atv`** — the dark designed-document tier; use for dashboards, reports, and
  any rich multi-section output. This is the right answer in almost all cases.
- **`pico` / `daisy`** — light-document tiers; pick only when the target audience explicitly
  wants a lightweight, framework-styled page.

## When to invoke

- The user asks to "render" or "visualize" structured output (tables, dashboards, comparisons).
- A prior tool write produced a file that looks like a data artifact.

## Steps

1. Collect the input path (or pipe JSON/Markdown via stdin with `--input -`).
2. Optionally specify `--design` (starter name, path, or URL) and `--tier` (omit for `atv`).
3. Run the command; report the triple paths and slug from stdout.
4. If `--no-open` was NOT passed and the environment is non-headless, the browser opens automatically.

## Output

The command writes three files and prints their paths:
- `<slug>.html` — single-file artifact
- `<slug>.DESIGN.md` — design sidecar
- `<slug>.meta.yaml` — metadata (tier, harness, lint_passed, created_at)

## Input shape — pick the richest one that fits

The `atv` tier renders three distinct layouts depending on what `--input` receives.
**Prefer the richest layout the content supports** — most agent output is structured
enough to use the section graph, which is the only mode that exercises the
designed-document treatment (hero strip, numbered sections, accent typography).

### 1. Section graph — **use this for almost everything**

JSON with a top-level `sections: [...]` array. Each entry has a `kind` that maps
to one of 15 emitters. Run `paperboard schema` to see them all, or
`paperboard schema --kind <name>` for fields + an example payload.

```json
{
  "title": "Pipeline Report",
  "sections": [
    {"kind": "hero", "eyebrow": "Release", "title": "v0.2.0 pipeline.", "sub": "All checks green."},
    {"kind": "sec", "num": "01", "title": "Build matrix.",
     "body": [{"kind": "status-table", "rows": [{"check": "build", "status": "PASS"}]}]}
  ]
}
```

Available kinds (see `paperboard schema` for full input shape per kind):
`hero`, `sec`, `stack-list`, `dep-list`, `q-list`, `steps`, `code-shell`,
`color-strip`, `fit-row`, `anti`, `checklist`, `callout`, `subhead`,
`props-table`, `status-table`.

### 2. Simple table — `{title, subtitle, rows}`

Use when the content is genuinely just a table and a heading. Renders as
`<h1>` + `<h2>` + `<table>`; no hero strip, no card sections.

```json
{"title": "Bug Hunt", "subtitle": "Phase 7 triage", "rows": [{"id": "RW-1", "status": "FIXED"}]}
```

### 3. Markdown prose — `paperboard render --input report.md`

Use only when the content is genuinely prose (long-form writing, narrative
documentation). Renders the dark editorial typography in `.prose` mode.
No hero, no sections.

## Discover the schema before constructing JSON

```
paperboard schema                       # list all 15 kinds
paperboard schema --kind hero           # detail + example for one kind
paperboard schema --format json         # full machine-readable dump
```
