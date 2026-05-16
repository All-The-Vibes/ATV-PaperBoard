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
