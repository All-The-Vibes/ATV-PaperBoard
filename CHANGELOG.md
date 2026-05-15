# Changelog

All notable changes to atv-paperboard are documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/) starting at v0.1.0.

## [Unreleased]

### Planned for v0.1.1
- OpenCode adapter (deferred from v0.1.0; 5 breaking defects in SPEC v4 TS plugin require empirical-verification cycle).
- USPTO TESS clearance on "paperboard" / "atv" IC 009/042.
- Public release (PyPI + GitHub + Claude Code marketplace PR).
- Cross-harness artifact aggregation (one gallery showing artifacts from multiple harnesses on one machine).

### Planned for v0.2
- VS Code Chat Participant extension (Copilot in-IDE path).
- MCP server integration.
- Full HTML-side token trace (spacing/typography/shadow). v0.1.0 is color-only.

## [0.1.0-preview] — 2026-05-15

Initial private/limited release. Delivered in a single session.

### Adapters
- **Claude Code** (native, §2.1 corrected): `.claude-plugin/plugin.json` manifest + `hooks/hooks.json` with corrected outer `"hooks"` wrapper key and timeout unit (seconds, not ms). Regression test covers the SPEC v4 syntax bugs.
- **Codex CLI** (native, §2.2 corrected): `agents/openai.yaml` with corrected schema (removed non-existent `allowed_tools` field); `~/.codex/config.toml` TOML hook with corrected array-of-tables syntax and `matcher` key. Regression test covers the SPEC v4 TOML bugs.

### Recipe
- **GitHub Copilot Coding Agent** via `recipes/github-actions/`: `copilot-instructions.md.template` + `workflow.yml.template` + `INSTALL.md`. Copilot has no local plugin path; recipe ships as GitHub Actions templates rather than a 4th adapter.

### Pillars
- **ENFORCE**: `core/validate.py` — Google CLI lint (`node <bin>/dist/index.js lint --format json`) + HTML-side color-token trace. Severity-aware: lint failures surface `fail-class`. Regeneration retries: same tier → switch tier → fall back to paperboard default.
- **RENDER**: `core/render.py` — `rows/body_md/body_html` input contract; Pico (cheap) and daisyUI (rich) tier templates via Jinja2; Tailwind token-rename layer bridges `@google/design.md export tailwind` output to Pico's `--pico-*` / daisyUI's `--p` CSS variables.
- **PERSIST**: `core/persist.py` — harness-aware path resolution; `--output-dir` override propagated across all subcommands (`render`, `validate`, `gallery`, `detect-artifact-candidate`).
- **COMPOUND**: `core/gallery.py` — auto-gallery-regen triggered after every `render` call; gallery reuses `designs/paperboard.DESIGN.md`; gallery lint passes.

### Designs
- `designs/paperboard.DESIGN.md` — default (dialed-back neubrutalism).
- `designs/starters/stripi-inspired.DESIGN.md`, `lin-ear-inspired.DESIGN.md`, `vercel-inspired.DESIGN.md` — 3 brand-inspired starters, all carrying §17 attribution frontmatter (`inspired_by`, `not_affiliated_with`, `source_repo`, `source_commit`, `source_license`, `redistributed_under`). Public-release blocker resolved (`test_starter_attribution.py` passing).
- `designs/glass.DESIGN.md` — premium opt-in tier.

### Empirical SPEC corrections
- **V2 export format**: `@google/design.md` export emits only `tailwind | dtcg` formats; `css-tailwind` flag does not exist. Token-rename layer in `core/render.py` bridges to Pico/daisyUI CSS variables.
- **RW-1 to RW-10**: 10 real-world bugs surfaced during Phase 7a by driving the CLI on 3 real-world fixtures (build-status, harness-comparison, bug-hunt) and patched same-session.

### Tests
- 93 passing, 2 skipped (real-session V3/V4 gates that require a live harness).
- Markers: `phase0`, `harness_claude_code`, `harness_codex`.

### Dependencies
- `@google/design.md@0.1.1` (Apache-2.0) exact-pinned; committed `package-lock.json`.

### Migration plan when `@google/design.md` 0.2 ships
- `tests/test_core_bridge.py` is the schema-drift guard; if it fails post-bump, do not auto-upgrade.
- Inspect the 0.2 release notes for new mandatory sections; update `designs/paperboard.DESIGN.md` accordingly.
- Bump the dep, regenerate the lockfile, re-run the Phase 0 verification matrix (SPEC §15) before tagging the patch release.
