# atv-paperboard

> **Cross-harness HTML artifact toolkit for AI coding agents.** One spec. Three native adapters. Zero lock-in.
>
> Drop it into **Claude Code**, **Codex CLI**, or **GitHub Copilot CLI** and your agent stops dumping markdown into the chat — it emits paired `.html` + `.DESIGN.md` artifacts governed by Google's [DESIGN.md spec](https://github.com/google-labs-code/design.md), persisted to disk, and rolled into a compounding gallery you can actually share.

<p align="center">
  <a href="assets/paperboard-teaser.mp4">
    <img src="assets/paperboard-teaser-poster.jpg" alt="paperboard teaser — click to play" width="720" />
  </a>
  <br/>
  <sub><strong><a href="assets/paperboard-teaser.mp4">▶ Watch the 60-second teaser</a></strong></sub>
</p>

<!-- GitHub renders an inline player when the .mp4 is referenced via raw URL; the link above is the universal fallback. -->

https://github.com/All-The-Vibes/ATV-PaperBoard/raw/main/assets/paperboard-teaser.mp4

---

## Why this exists

Every coding agent today renders status updates the same way: a wall of monospace markdown in a chat window. That output is **ephemeral, ugly, and impossible to share with stakeholders.** Paperboard intercepts the moment an agent emits structured data (a status table, a triage list, a comparison matrix) and turns it into a **lint-clean HTML artifact** that lives on disk, links into a gallery, and renders identically across harnesses.

It's the same toolkit, the same spec, the same `core/` Python package — wired into **three different agent runtimes** via thin native adapters, plus a GitHub Actions recipe for the Copilot Coding Agent.

## Where it runs (today)

| Harness | Type | Status |
|---|---|---|
| **Claude Code** | Native plugin (`adapters/claude-code/`) | ✅ Shipping |
| **Codex CLI** | Native plugin (`adapters/codex/`) | ✅ Shipping |
| **GitHub Copilot CLI** | Native plugin (`adapters/copilot-cli/`) | ✅ Shipping — **validated end-to-end against `copilot.exe v1.0.49`** ([receipts](_release-proof/)) |
| **GitHub Copilot Coding Agent** | GitHub Actions recipe (`recipes/github-actions/`) | ✅ Shipping |
| OpenCode | Native plugin | 🚧 Deferred to v0.1.1 (SPEC v4 TS plugin has 5 breaking upstream defects) |

> The Copilot CLI integration was validated against the real binary inside a fully isolated sandbox (`USERPROFILE`/`HOME`/`COPILOT_HOME` pinned). Hook fires, payload parses, suggestion injects, file lands, `exit=0`. Full ground-truth jsonl traces live in [`_release-proof/`](_release-proof/).

## The four pillars

| Pillar | What it does | How you'd break it |
|---|---|---|
| **Enforce** | Validates the paired DESIGN.md via the upstream Google CLI **and** an HTML-side color-token trace | Reference `{colors.nonexistent}` in DESIGN.md → lint rejects |
| **Render** | Single-file HTML → loopback HTTP server → auto-opens a browser tab (skipped in headless/remote) | `paperboard render --input data.json` → triple on disk + tab in <2s |
| **Persist** | Writes `{name}.html` + `{name}.DESIGN.md` + `{name}.meta.yaml` to the harness-resolved persistence path | After 3 emissions → 3 triples at the right path for that harness |
| **Compound** | Auto-regenerates a `gallery.html` that reflects every prior artifact, governed by its own DESIGN.md | Add a new artifact → gallery reflects it within 1s, gallery's own lint passes |

## Install — pick your harness

### GitHub Copilot CLI (native plugin)

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard
cd ATV-PaperBoard
pip install -e .
python adapters/copilot-cli/build.py
copilot --plugin-dir="$(pwd)/adapters/copilot-cli/_dist"
# Or, inside copilot:  /plugin marketplace add All-The-Vibes/ATV-PaperBoard
```

Full instructions: [`adapters/copilot-cli/INSTALL.md`](adapters/copilot-cli/INSTALL.md)

### Claude Code (native plugin)

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard
# Then inside Claude Code:
/plugin marketplace add All-The-Vibes/ATV-PaperBoard
/plugin install atv-paperboard@<marketplace>
```

Full instructions: [`adapters/claude-code/INSTALL.md`](adapters/claude-code/INSTALL.md)

### Codex CLI (native plugin)

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard ~/.agents/skills/atv-paperboard
# Optional: add the hook to ~/.codex/config.toml (see INSTALL.md)
```

Full instructions: [`adapters/codex/INSTALL.md`](adapters/codex/INSTALL.md)

### GitHub Copilot Coding Agent (Actions recipe)

```bash
pip install atv-paperboard
cp recipes/github-actions/*.template .github/
# Rename the .template extensions and fill in repo-specific values
```

Full instructions: [`recipes/github-actions/INSTALL.md`](recipes/github-actions/INSTALL.md)

## Quick start (standalone — no harness needed)

Requires Node.js + Python 3.10+.

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard
cd ATV-PaperBoard
npm install
pip install -e .
python -m core.cli render --input examples/inputs/build-status.json --output-dir ./out
python -m core.cli gallery --output-dir ./out
```

`render` auto-triggers gallery regeneration. `--output-dir` overrides the harness-resolved persistence path for every subcommand.

## What you get

Three real example artifacts ship in `examples/output/`:

- [`build-status.html`](examples/output/build-status.html) — CI dashboard
- [`harness-comparison.html`](examples/output/harness-comparison.html) — side-by-side adapter feature matrix
- [`bug-hunt.html`](examples/output/bug-hunt.html) — triage snapshot
- [`gallery.html`](examples/output/gallery.html) — the compounding index, auto-regenerated on every render

Each artifact is a paired `.html` + `.DESIGN.md` + `.meta.yaml` triple. The HTML uses only design tokens declared in the DESIGN.md. The lint trace will reject any drift.

## Architecture

A shared `core/` Python package (harness-agnostic) implements all four pillars. Thin per-harness adapters (`adapters/claude-code/`, `adapters/codex/`, `adapters/copilot-cli/`) provide the manifest, hook config, and install glue; `recipes/github-actions/` covers the Copilot Coding Agent via GitHub Actions templates. Every adapter and recipe invokes the same `core/cli.py` entry point via subprocess.

Token export uses `@google/design.md` (`tailwind | dtcg` formats); a rename layer in `core/render.py` bridges to Pico/daisyUI CSS variables.

See [SPEC.md](SPEC.md) for the full specification and [SPEC-addendum-2026-05-16-copilot-cli.md](SPEC-addendum-2026-05-16-copilot-cli.md) for the Copilot CLI addendum.

## Development

```bash
pytest tests/ -q
# Expected: 130 passed, 2 skipped
```

The 2 skipped tests are real-session gates (V3, V4) that require a live harness session — not run in CI.

| Marker | Scope |
|---|---|
| `phase0` | Cross-harness empirical verification (V1–V6) |
| `harness_claude_code` | Claude Code adapter |
| `harness_codex` | Codex CLI adapter |

## Roadmap & lineage

- [CHANGELOG.md](CHANGELOG.md) — version history
- [SPEC.md](SPEC.md) — full v4.2 specification
- [SPEC-review-2026-05-14.md](SPEC-review-2026-05-14.md) — adversarial review record
- [SPEC-addendum-2026-05-16-copilot-cli.md](SPEC-addendum-2026-05-16-copilot-cli.md) — Copilot CLI addendum

## License

Apache-2.0. See [LICENSE](LICENSE).

`@google/design.md@0.1.1` is pinned as a dev dependency (Apache-2.0). Starter designs in `designs/starters/` carry per-file `attribution:` frontmatter per SPEC §17.

