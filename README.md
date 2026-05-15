# atv-paperboard

> Cross-harness HTML artifact toolkit. Enforce, render, persist, compound.

**Status:** v0.1.0-preview (private/limited release; see [SPEC.md](SPEC.md)).

atv-paperboard emits paired `.html` + `.DESIGN.md` artifacts governed by Google's [DESIGN.md spec](https://github.com/google-labs-code/design.md), serves them from loopback, persists them with metadata, and gathers them into a compounding gallery. It ships as native plugin adapters for **Claude Code** and **Codex CLI**, plus a `recipes/github-actions/` template for **GitHub Copilot Coding Agent**. (OpenCode is on the v0.1.1 roadmap.)

Part of the **ATV** family (Compound Engineering / gstack / Karpathy Guidelines lineage). Independent of `atv-starterkit` and `atv-design` — no shared packages, no required co-installation. Family-history only.

## What it does

Four pillars, all harness-invariant:

| Pillar | What | Success test |
|---|---|---|
| **Enforce** | Validates the paired DESIGN.md via the upstream Google CLI + an HTML-side color-token trace | Lint rejects an artifact whose DESIGN.md has `{colors.nonexistent}` |
| **Render** | Single-file HTML → loopback HTTP server → auto-open browser tab (skip-open in headless/remote) | `paperboard render` writes the triple and opens a tab in <2s |
| **Persist** | Writes the triple to the harness-resolved persistence path with YAML metadata sidecar | After 3 emissions, 3 triples exist at the harness's correct path |
| **Compound** | Auto-regenerates a gallery HTML that reflects all prior artifacts. Gallery uses `paperboard.DESIGN.md` as its design source | Gallery reflects new artifact within 1s; gallery's own lint passes |

## Install

See per-harness `INSTALL.md` files:
- [Claude Code](adapters/claude-code/INSTALL.md)
- [Codex CLI](adapters/codex/INSTALL.md)
- [GitHub Copilot Coding Agent (recipe)](recipes/github-actions/INSTALL.md)

## Status & roadmap

This is a `v0.1.0-preview` release. See [SPEC.md](SPEC.md) for the full specification, [SPEC-review-2026-05-14.md](SPEC-review-2026-05-14.md) for the adversarial review, and [.omc/research/research-20260514-spec-v4-deep/report.md](.omc/research/research-20260514-spec-v4-deep/report.md) for the deep-research record that informed v4.1.

License: Apache-2.0.
