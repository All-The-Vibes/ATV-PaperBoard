# Changelog

All notable changes to **atv-paperboard** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The project is in `0.1.x` alpha — minor versions may introduce additive breaking changes, patch versions are bug-fix-only.

The current packaged version is in [`pyproject.toml`](pyproject.toml). The roadmap lives in [`README.md`](README.md#roadmap), not here.

---

## [Unreleased]

---

## [0.1.2] — 2026-05-16

First version published to **PyPI** (`pip install atv-paperboard`). Earlier
`0.1.0-preview` / `0.1.1` tags were repo-local only.

### Added
- **GitHub Copilot CLI adapter** (`adapters/copilot-cli/`) — native plugin (agents, skills, hook). Validated end-to-end against `copilot.exe v1.0.49` inside a fully isolated sandbox (`USERPROFILE` / `HOME` / `COPILOT_HOME` pinned). Hook fires, payload parses, suggestion injects, file lands, `exit=0`.
- Per-adapter `INSTALL.md` covering local-dev (`--plugin-dir`) and marketplace install flows.
- 60-second teaser video (`assets/paperboard-teaser.mp4`, 1.4 MB H.264) embedded inline at the top of the README via a `user-attachments` URL so it auto-plays on github.com.
- **PyPI Trusted Publishing workflow** (`.github/workflows/pypi-publish.yml`) — `v*` tag push → OIDC publish to PyPI via `environment: pypi`. Tag-vs-pyproject version consistency check prevents accidental drift.
- **Plugin marketplace manifests** at the canonical locations for each harness: `.claude-plugin/marketplace.json` (Claude Code) and `.github/plugin/marketplace.json` (Copilot CLI). One-command install:
  - Claude Code: `/plugin marketplace add All-The-Vibes/ATV-PaperBoard`
  - Copilot CLI: `copilot plugin install All-The-Vibes/ATV-PaperBoard`

### Changed
- **Package layout.** `templates/` and `designs/` moved inside `core/` and declared as `[tool.setuptools.package-data]` so a `pip install atv-paperboard` wheel actually ships the Jinja templates and DESIGN.md files (previously the wheel installed an unusable `paperboard` binary that crashed on first render).
- **Plugin hook commands** invoke the PyPI-installed `paperboard` binary directly instead of `python ${CLAUDE_PLUGIN_ROOT}/core/cli.py …`. Plugin downloads are smaller; the Python core is updated independently via `pip install -U atv-paperboard`.
- **README rewrite.** All public-facing technical content now lives in `README.md`: artifact triple, render tiers (Pico vs daisyUI), auto-detection precedence ladder, per-harness persistence paths, three integration patterns, hook heuristic, three Copilot surfaces disambiguation, Copilot CLI fail-open hook semantics + `additionalContext` channel, explicit non-goals, threat model, full CLI surface.
- **Plugin manifest versions synchronized** at `0.1.2` across `pyproject.toml`, `adapters/claude-code/.claude-plugin/plugin.json`, and `adapters/copilot-cli/plugin.json`. Copilot CLI manifest license corrected `MIT` → `Apache-2.0`.

### Fixed
- **Example sample slugs.** `examples/inputs/{build-status,harness-comparison,bug-hunt}.json` had long verbose titles producing 50-character slug filenames that didn't match the README links. Titles shortened; subtitles preserve context.
- Stale `<org>` placeholder in `adapters/claude-code/.claude-plugin/plugin.json` replaced with `All-The-Vibes`.

### Removed
- Internal spec documents (`SPEC.md`, `SPEC-review-*.md`, `SPEC-addendum-*.md`) are no longer published with the repo. They remain on contributors' local disks as reasoning records but are now gitignored (`SPEC*.md`). All user-facing material was lifted into the README.
- Local-only directories `_release-proof/` (validation harness output) and `.omc/` (session/research scratch) are gitignored.

### Internal
- Pinned PR review / repo automation: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer on relevant commits.

---

## [0.1.1] — 2026-05-15

### Fixed
- `core/render.py::_flatten_tailwind()` now unwraps the `{"theme": {"extend": {...}}}` envelope that `@google/design.md export tailwind` returns. Previously the nested structure was passed through verbatim, producing an empty `:root {}` block with no design tokens applied.
- Added a pure-Python YAML fallback path in `core/render.py` so token injection works when the Node bridge is unavailable (CI environments without `node`, offline use).

### Added
- **Render-fidelity test** — end-to-end sentinel-color check (`#ABCDEF`) verifies that a known token value survives the full export → flatten → CSS-variable injection → HTML render pipeline.
- **Bridge-shape mismatch warning** — `core/render.py` emits a structured warning when the export envelope shape does not match the expected `theme.extend` contract, making future `@google/design.md` schema changes immediately visible instead of silently producing empty tokens.

### Known limitations (still open)
- **Workflow glob is not monorepo-safe.** `paperboard-artifacts/**` does not match nested paths in monorepos; `**/paperboard-artifacts/**` is the correct pattern but needs validating against real multi-package repos before shipping as the default.
- **No merge-block enforcement.** `paperboard validate` failures are reported but do not block merges; enforcing this requires branch protection rules that vary by org policy.
- **`@google/design.md` installed globally without integrity check.** `npm install -g @google/design.md@0.1.1` pins by version only; a lockfile-based install path is deferred until the upstream package exposes stable SRI hashes.

---

## [0.1.0-preview] — 2026-05-15

Initial private/limited release. Three native adapters + one CI recipe, shared Python core, four pillars.

### Adapters
- **Claude Code** (native) — `.claude-plugin/plugin.json` manifest + `hooks/hooks.json` with the outer `"hooks"` wrapper key and timeout in **seconds**.
- **Codex CLI** (native) — `agents/openai.yaml` (no `allowed_tools` field — that key doesn't exist in the documented schema) + `~/.codex/config.toml` TOML hook using array-of-tables syntax and a `matcher` key.

### Recipe
- **GitHub Copilot Coding Agent** via `recipes/github-actions/`: `copilot-instructions.md.template` + `workflow.yml.template` + `INSTALL.md`. The Coding Agent has no local plugin path on this surface, so the integration ships as GitHub Actions templates rather than an adapter.

### Pillars
- **Enforce** (`core/validate.py`) — Google CLI lint (`node <bin>/dist/index.js lint --format json`) + HTML-side color-token trace. Severity-aware: lint failures surface a `fail-class`. Regeneration retries: same tier → switch tier → fall back to the default `paperboard` design.
- **Render** (`core/render.py`) — `rows / body_md / body_html` input contract; Pico (cheap) and daisyUI (rich) tier templates via Jinja2; Tailwind token-rename layer bridges `@google/design.md export tailwind` output to Pico's `--pico-*` / daisyUI's `--p` CSS variables.
- **Persist** (`core/persist.py`) — harness-aware path resolution; `--output-dir` override propagated across `render`, `validate`, `gallery`, `detect-artifact-candidate`.
- **Compound** (`core/gallery.py`) — auto gallery regeneration triggered after every `render` call; gallery reuses `designs/paperboard.DESIGN.md`; the gallery's own lint passes.

### Designs
- `designs/paperboard.DESIGN.md` — default (dialed-back neubrutalism).
- `designs/starters/{stripi,lin-ear,vercel}-inspired.DESIGN.md` — three brand-inspired starters, each carrying `attribution:` frontmatter (`inspired_by`, `not_affiliated_with`, `source_repo`, `source_commit`, `source_license`, `redistributed_under`). The starter-attribution lint blocks any starter missing required keys.
- `designs/glass.DESIGN.md` — premium opt-in tier.

### Empirical corrections discovered at build time
- `@google/design.md` `export` emits only `tailwind | dtcg` formats — the `css-tailwind` flag does not exist. The token-rename layer in `core/render.py` bridges to Pico/daisyUI.
- **10 real-world bugs** surfaced during the Phase 7a real-world test pass by driving the CLI on three real-world fixtures (build-status, harness-comparison, bug-hunt) and patched same-session.

### Tests
- 93 passing, 2 skipped (live-harness gates that require a real Claude Code or Codex CLI session — not run in CI).
- Markers: `phase0`, `harness_claude_code`, `harness_codex`.

### Dependencies
- `@google/design.md@0.1.1` (Apache-2.0) **exact-pinned**; committed `package-lock.json` is the integrity guard.

### Migration plan when `@google/design.md` 0.2 ships
- `tests/test_core_bridge.py` is the schema-drift guard. If it fails post-bump, do **not** auto-upgrade.
- Inspect the 0.2 release notes for new mandatory sections; update `designs/paperboard.DESIGN.md` accordingly.
- Bump the dep, regenerate the lockfile, re-run the Phase 0 verification matrix before tagging the patch release.

---

[Unreleased]: https://github.com/All-The-Vibes/ATV-PaperBoard/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/All-The-Vibes/ATV-PaperBoard/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/All-The-Vibes/ATV-PaperBoard/compare/v0.1.0-preview...v0.1.1
[0.1.0-preview]: https://github.com/All-The-Vibes/ATV-PaperBoard/releases/tag/v0.1.0-preview

