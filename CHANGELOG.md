# Changelog

All notable changes to atv-paperboard are documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/) starting at v0.1.0.

## [Unreleased]

### Planned for v0.1.1
- OpenCode adapter (deferred from v0.1.0 per deep-research stage 4 / 7).
- Cross-harness artifact aggregation (one gallery showing artifacts from multiple harnesses on one machine).

### Planned for v0.2
- VS Code Chat Participant extension (Copilot in-IDE path).
- MCP server integration.
- Full HTML-side token trace (spacing/typography/shadow). v0.1.0 is color-only.

## [0.1.0-preview] — TBD

Initial private/limited release.

- Harnesses: Claude Code, Codex CLI native adapters; GitHub Copilot Coding Agent via `recipes/github-actions/`.
- Pillars: Enforce, Render, Persist, Compound — all functional.
- Designs: `paperboard.DESIGN.md` default (dialed-back neubrutalism); 3 starters (`stripi-inspired`, `lin-ear-inspired`, `vercel-inspired`) with full §17 attribution.
- Tiers: Pico (cheap), daisyUI (rich) — via `@google/design.md export css-tailwind` + token-rename layer.
- Pin: `@google/design.md@0.1.1` (Apache-2.0), committed `package-lock.json`.

### Migration plan when `@google/design.md` 0.2 ships
- `tests/test_core_bridge.py` is the schema-drift guard; if it fails post-bump, do not auto-upgrade.
- Inspect the 0.2 release notes for new mandatory sections; update `designs/paperboard.DESIGN.md` accordingly.
- Bump the dep, regenerate the lockfile, re-run the Phase 0 verification matrix (SPEC §15) before tagging the patch release.
