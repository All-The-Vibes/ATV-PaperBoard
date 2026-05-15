# atv-paperboard

Cross-harness HTML artifact toolkit for agentic coding workflows. Emits paired `.html` + `.DESIGN.md` artifacts governed by Google's [DESIGN.md spec](https://github.com/google-labs-code/design.md), persists them with metadata, and gathers them into a compounding gallery.

## Status

**v0.1.0-preview** (private/limited release, 2026-05-15).

Shipping:
- Native adapter: **Claude Code** (`adapters/claude-code/`)
- Native adapter: **Codex CLI** (`adapters/codex/`)
- Recipe: **GitHub Copilot Coding Agent** (`recipes/github-actions/`)

Deferred to v0.1.1: OpenCode (5 breaking defects in the SPEC v4 TS plugin required an empirical-verification cycle the schedule didn't accommodate).

## The four pillars

| Pillar | What | Success test |
|---|---|---|
| **Enforce** | Validates the paired DESIGN.md via the upstream Google CLI + an HTML-side color-token trace | Lint rejects an artifact whose DESIGN.md has `{colors.nonexistent}` |
| **Render** | Single-file HTML → loopback HTTP server → auto-open browser tab (skip-open in headless/remote) | `paperboard render` writes the triple and opens a tab in <2s |
| **Persist** | Writes the triple to the harness-resolved persistence path with YAML metadata sidecar | After 3 emissions, 3 triples exist at the harness's correct path |
| **Compound** | Auto-regenerates a gallery HTML that reflects all prior artifacts; gallery uses `paperboard.DESIGN.md` as its design source | Gallery reflects new artifact within 1s; gallery's own lint passes |

## Install

### Claude Code (native adapter)

```bash
git clone https://github.com/<owner>/atv-paperboard
# Then inside Claude Code:
/plugin marketplace add <owner>/atv-paperboard
/plugin install atv-paperboard@<marketplace>
```

Full instructions: [`adapters/claude-code/INSTALL.md`](adapters/claude-code/INSTALL.md)

### Codex CLI (native adapter)

```bash
git clone https://github.com/<owner>/atv-paperboard ~/.agents/skills/atv-paperboard
# Optional: add the hook to ~/.codex/config.toml (see INSTALL.md)
```

Full instructions: [`adapters/codex/INSTALL.md`](adapters/codex/INSTALL.md)

### GitHub Copilot Coding Agent (recipe)

```bash
pip install atv-paperboard
cp recipes/github-actions/*.template .github/
# Rename the .template extensions and fill in repo-specific values
```

Full instructions: [`recipes/github-actions/INSTALL.md`](recipes/github-actions/INSTALL.md)

## Quick start (standalone)

Works without any harness install. Requires Node.js and Python 3.10+.

```bash
npm install
pip install -e .
python -m core.cli render --input examples/inputs/build-status.json --output-dir ./out
python -m core.cli gallery --output-dir ./out
```

`render` auto-triggers gallery regeneration after writing the artifact triple. The `--output-dir` flag overrides the harness-resolved persistence path for all subcommands.

## Real-world example output

Three example artifacts are included in `examples/output/`:

- `build-status.html` — CI build status dashboard
- `harness-comparison.html` — side-by-side harness feature comparison table
- `bug-hunt.html` — bug triage snapshot

Gallery: [`examples/output/gallery.html`](examples/output/gallery.html)

## Architecture

A shared `core/` Python package (harness-agnostic) handles all four pillars. Thin per-harness adapters (`adapters/claude-code/`, `adapters/codex/`) provide manifest files, hook config, and install instructions; `recipes/github-actions/` covers Copilot via GitHub Actions templates. All adapters and recipes invoke the same `core/cli.py` entry point via subprocess. Token export from `@google/design.md` uses `tailwind | dtcg` formats; a rename layer in `core/render.py` bridges to Pico/daisyUI CSS variables.

See [SPEC.md](SPEC.md) for the full specification.

## Development

```bash
pytest tests/ -q
# Expected: 93 passed, 2 skipped
```

Test markers:

| Marker | Scope |
|---|---|
| `phase0` | Cross-harness empirical verification (V1–V6) |
| `harness_claude_code` | Claude Code adapter |
| `harness_codex` | Codex CLI adapter |

The 2 skipped tests are real-session gates (V3 and V4) that require a live harness session — they are not run in CI.

## Roadmap & lineage

- [CHANGELOG.md](CHANGELOG.md) — version history
- [SPEC.md](SPEC.md) — full v4.2 specification
- [SPEC-review-2026-05-14.md](SPEC-review-2026-05-14.md) — adversarial review record
- [.omc/research/research-20260514-spec-v4-deep/report.md](.omc/research/research-20260514-spec-v4-deep/report.md) — deep-research record

## License

Apache-2.0. See [LICENSE](LICENSE).

`@google/design.md@0.1.1` is pinned as a dev dependency (Apache-2.0). Starter designs in `designs/starters/` carry per-file `attribution:` frontmatter per SPEC §17; public release is pending counsel review and USPTO TESS clearance.
