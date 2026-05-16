---
name: paperboard
description: >
  Agent-first PaperBoard command. Use when the user asks to render a file,
  create/open/share an HTML artifact, pick a PaperBoard style, list styles, or
  rebuild the gallery. The agent invokes the `paperboard` CLI internally so the
  human can stay in their preferred agent workflow.
---

# paperboard

Agent-first wrapper for PaperBoard HTML artifacts.

The human-facing command is `/paperboard`. The implementation detail is the
`paperboard` CLI. Do not ask the human to leave their agent and run the CLI
unless they explicitly want standalone/scripting usage.

## Agent command surface

```text
/paperboard <path> [--style paperboard|meridian|atv]
/paperboard path/to/file.md
/paperboard path/to/proposal.md --style meridian
/paperboard path/to/report.json --style atv
/paperboard styles
/paperboard gallery
```

## Style flags

- `paperboard` is the default. Use it for general reports, simple docs, and tables.
- `meridian` is for proposals, decision memos, plans, and reviews.
- `atv` is for dense technical reports, debugging notes, architecture docs, and comparisons.

If the user omits `--style`, use `paperboard`.

## How to execute

Map the agent command to the CLI:

```bash
paperboard render --input <path> --style <style>
```

Examples:

```bash
paperboard render --input path/to/file.md --style paperboard
paperboard render --input path/to/proposal.md --style meridian
paperboard render --input path/to/report.json --style atv
paperboard styles list
paperboard gallery
```

`--design <name|path|url>` is advanced. Use it only if the user explicitly asks
for a raw DESIGN.md override. `--design` wins over `--style`.

## Workflow

1. Parse the requested file path and optional `--style` flag.
2. If the request is `/paperboard styles`, run `paperboard styles list`.
3. If the request is `/paperboard gallery`, run `paperboard gallery`.
4. Otherwise run `paperboard render --input <path> --style <style>`.
5. Report the generated `.html`, `.DESIGN.md`, `.meta.yaml`, and slug from stdout.
6. If the browser opens automatically, say so. If it does not, give the HTML path.

## Guardrails

- Never silently choose `meridian` or `atv`; they are opt-in styles.
- Do not expose tier selection unless the user asks for advanced rendering behavior.
- Do not auto-render README, CHANGELOG, `.github/`, or docs prose unless the user
  explicitly asks.
- If the file path is missing or does not exist, ask for the path instead of guessing.
