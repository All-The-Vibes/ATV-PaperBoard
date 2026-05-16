# Changelog

All notable changes to **atv-paperboard** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The project is in `0.1.x` alpha — minor versions may introduce additive breaking changes, patch versions are bug-fix-only.

The current packaged version is in [`pyproject.toml`](pyproject.toml). The roadmap lives in [`README.md`](README.md#roadmap), not here.

---

## [Unreleased]

### Changed
- Tightened editorial spacing across `atv-tier.html.j2`:
  - Hero padding `112px/80px` → `56px/48px`; eyebrow margin `36px` → `20px`.
  - Section padding `88px` → `48px` (`.sec.tight` `64px` → `32px`).
  - Prose `<h2>` rhythm `88px/40px` → `48px/24px`; `<h3>` `44px` → `32px`.
  - Prose container narrowed from `880px` to `720px`, now centered (`margin: 0 auto`); dropped redundant `max-width: 68ch` from `<p>` and `<ul>/<ol>` so the column width is the single source of truth.
  - Prose lede divider `56px/56px` → `32px/32px`; `<hr>` `56px` → `40px`.
  - Footer / checklist / callout / `<pre>` padding tightened for higher reading density.
- Hero h1 `max-width` `22ch` → `18ch`; hero sub-lede `62ch/44px` → `48ch/28px`; hero-meta `gap 32/padding-top 22` → `24/16`.
- Eyebrow rule bar is now an amber linear-gradient (`var(--amber) → transparent`) instead of a flat `--line-strong` solid.
- `--ease-fast` upgraded from Material's `cubic-bezier(0.4, 0, 0.2, 1)` to Emil-strong `cubic-bezier(0.23, 1, 0.32, 1)`.
- `gallery.html.j2` rewritten to match the dark editorial design system:
  - Dropped Pico CSS; uses the same `:root` tokens, Google Fonts (Inter + Instrument Serif + JetBrains Mono), and `data-theme="atv"` as the doc template.
  - Sticky topbar matches the doc topbar (52px, `backdrop-filter: blur(10px)`, gradient brand glyph, amber-dot status pill).
  - Editorial hero with mono eyebrow, serif h1 with amber italic accent, mono meta strip.
  - Card grid with `--surface` background, amber tier badges, accent-line "Open artifact →" links.

### Added
- **`paperboard schema` subcommand** — agent-discoverable documentation of the atv-tier section graph. Without args, lists all 15 kinds (`hero`, `sec`, `stack-list`, `dep-list`, `q-list`, `steps`, `code-shell`, `color-strip`, `fit-row`, `anti`, `checklist`, `callout`, `subhead`, `props-table`, `status-table`) with one-line descriptions. `--kind <name>` shows fields + an example JSON payload for one kind. `--format json` emits a machine-readable dump. `--list-kinds` prints kind names one per line for scripting. Closes the discoverability gap that meant agents installed via the skill defaulted to prose/table output and never exercised the card-tier rendering path.
- **`core/section_schema.py`** — single source of truth for the section graph schema (description, fields, example per kind). New parametrised test (`test_every_example_is_renderable`) renders each documented example through the real emitter on every CI run, so a doc example that drifts from the emitter is caught immediately. A second test pins that `SECTION_SCHEMA.keys() == _SECTION_EMITTERS.keys()` so adding a new kind without documenting it (or vice versa) fails CI.
- **`skills/render-artifact/SKILL.md` input-shape guidance.** Adds an "Input shape — pick the richest one that fits" section telling agents the section-graph path is the right answer for almost all structured content, with a runnable example and a pointer to `paperboard schema` for full per-kind detail.
- Accessibility scaffolding in `atv-tier.html.j2` and `gallery.html.j2`:
  - `@media (prefers-reduced-motion: reduce)` block neutralises transitions/animations for users with vestibular sensitivity.
  - All `:hover` rules gated behind `@media (hover: hover) and (pointer: fine)` so touch devices no longer get sticky hover states.
  - `:focus-visible` rings on all links (`outline: 2px solid var(--accent); outline-offset: 3px`).
- Press-feedback on interactive elements:
  - `a:active { opacity: 0.7; transition-duration: 60ms; }` across both templates.
  - `.stack-row / .dep-row / .q-row:active { transform: scale(0.997); }` for card rows.
- `@supports (animation-timeline: scroll())` block with `@starting-style { opacity: 0 }` for a subtle initial fade-in on the prose hero `<h1>` (modern browsers only; legacy browsers see instant text).

### Fixed
- Long-document performance: dropped body-level `text-rendering: optimizeLegibility` and `background-attachment: fixed`. `optimizeLegibility` now scoped to display sizes (`.display, hero h1, sec-head h2, prose hero/h2, blockquote`). On the 1 MB+ unsloth doc this measurably improves scroll FPS.
- Topbar Safari compatibility: added `-webkit-backdrop-filter` alongside `backdrop-filter`; reduced blur from `14px` to `10px` to lower per-frame paint cost on iOS Safari.
- `gallery.html.j2` cohesion break: gallery was light-themed (Pico's `data-theme="light"` won specificity) even when dark token overrides were injected. Gallery now visually continues from the docs it indexes.

## [0.1.3] — 2026-05-16

### Added
- **Markdown-rendering pipeline.** `paperboard render --input foo.md` now produces a fully-styled editorial document. `_load_input` detects `.md` / `.markdown`, extracts the first H1 as the title, and routes the body to `body_md`. `_md_to_html` is now a full GFM-ish parser supporting tables, fenced code blocks (with `data-lang` for language labels), blockquotes, GFM alerts (`[!NOTE]` / `[!TIP]` / `[!IMPORTANT]` / `[!WARNING]` / `[!CAUTION]`), ordered + unordered lists, horizontal rules, inline images, HTML passthrough, bare-URL autolinking, and underscore-italics with snake_case word-boundary safety. The four repo MDs (README, CHANGELOG, CONTRIBUTING, RELEASE) all round-trip cleanly.
- **`.prose` editorial dialect** scoped under `.prose` in the atv template (~250 lines of CSS). Instrument Serif display hero (clamp 56–92px) with italic-amber accent, Instrument Serif italic lede, auto-numbered amber section eyebrows (`01`, `02`, `03`…) via CSS counter, traffic-light window-chrome code blocks with language label, polished props-style tables with amber mono uppercase headers, amber-rail serif italic pull-quotes, amber-tinted inline `code` chips, typed GFM-alert callouts. Inter + Instrument Serif + JetBrains Mono loaded from Google Fonts. Atmospheric body radial-gradient (amber top-center + indigo bottom-right, fixed).
- **Topbar populates for MD inputs.** `_load_input` now emits `breadcrumb` (slug as `.md` filename) and `status_tag = "doc"` so the sticky topbar reads `■ atv-paperboard / README.md ● doc` for markdown renders instead of being empty.
- **`paperboard doctor` version-checks the bridge.** Reports `✓ in tested range` / `⚠ above tested range` / `⚠ below tested range` based on `BRIDGE_VERSION_MIN` and `BRIDGE_VERSION_MAX_EXCL` in `core/bridge.py`. The compatibility-range constants represent what humans have verified; they're bumped manually when a new bridge version passes the test suite.
- **`paperboard doctor` surfaces available `@google/design.md` upgrades** by polling the npm registry (3 s timeout, 24 h cached in `~/.atv-paperboard/upgrade-cache.json`, fully network-tolerant). Offline / DNS / 4xx failures are silent. Doctor only suggests upgrades that fall inside the tested compatibility range; never installs anything. *Silent* auto-update remains a non-goal — the doctor row makes available bumps visible without surprising the user.
- **`.github/workflows/sync-bridge-version.yml`** rewrites the `@google/design.md@X.Y.Z` pin in `README.md`, `recipes/github-actions/workflow.yml.template`, and the three per-adapter `INSTALL.md` files whenever Dependabot opens a `package.json` bump PR — so the bump carries its own doc updates and CI sees the synchronized state before review. The tested-range constants in `core/bridge.py` are *not* auto-widened; humans bump those after verification.

### Fixed
- **The "tables render as white panels with invisible text" bug.** `core/designs/paperboard.DESIGN.md` was a light theme (`surface: #FFFFFF`, `background: #FAFAFA`, `foreground: #0F172A`) while the atv-tier template is a dark theme — `--surface` resolved to white, table body text used the template's hardcoded light-gray `--text-2: #d0d6e0`, producing invisible text on white panels embedded in dark chrome. Flipped DESIGN.md to a coherent dark editorial palette (`background: #08090A`, `surface: #0E0F12`, `foreground: #F7F8F8`, `primary: #7170FF`, `accent: #F1B13B`, plus warm-muted `danger: #C97070`, `success: #7FAE6E`). All tier consumers (atv direct, pico via `--pico-*` mapping, daisy via `--p/--b1/--bc` mapping) now render coherent dark documents from the same DESIGN.md source.
- **`paperboard doctor` no longer crashes when `@google/design.md` is missing.** Previously hit an unhandled `BridgeEnvError` traceback at the lint step; now catches the error and reports `✗ bridge unavailable — Enforce pillar is silently degraded` with a copy-pasteable `npm install -g @google/design.md@0.1.1` remediation line.
- **Bridge resolves `@google/design.md` from a global npm install.** `core/bridge.py::_resolve_binary` now queries `npm root -g` (with a 10 s timeout and graceful failure) in addition to the existing local `node_modules/` candidates, so a `pip install atv-paperboard` + `npm install -g @google/design.md@0.1.1` flow works from any cwd without cloning the repo.
- **Doctor reads the bridge version from the resolved binary** (`bridge.version()`) instead of a hardcoded `node_modules/@google/design.md/package.json` path, so a global npm install correctly reports its version instead of showing `not installed`.

### Changed
- **Editorial accent flipped from cool rose to warm amber.** `*italics*` in body, headings, and blockquotes now render in amber italic (`#F1B13B`) — that's the editorial signature pulled from the `harness-alignment-proposal` reference design. Inline `` `code` `` chips are amber-tinted with amber border. Section eyebrows, table headers, list markers, and blockquote left rails all amber. JSON section-graph renders (Linear Spec dialect) continue to use indigo `--accent` directly and are visually unchanged.
- **Default tier is now `atv`** (the dark designed-document template that properly showcases the neubrutalism palette). Previously the `paperboard render` CLI silently fell back to `pico` even though every SKILL.md, the Copilot Coding Agent instructions template, and the GH Actions recipe all promised `atv` as the default. Now the docs match reality: omitting `--tier` produces the rich dark artifact every harness's SKILL.md describes. Pass `--tier pico` or `--tier daisy` explicitly for the light, framework-styled tiers.
- Regenerated `examples/output/` (`build-status`, `bug-hunt`, `harness-comparison`, `gallery`) against the new default so the README's "What you get" links show neubrutalism in its canonical atv presentation. `harness-comparison.json` rewritten to drop the OpenCode column and replace it with a Copilot CLI / Copilot Coding Agent split.

### Removed
- **OpenCode adapter scaffolding.** The `opencode` harness branch in `core/detect.py` and `core/persist.py`, the `OPENCODE_CONFIG_DIR` env-var probe, the `opencode` row in the README's auto-detection ladder and persistence-paths table, the `opencode` test cases in `tests/phase0/test_v3_v4_v5_v6.py`, the `OPENCODE_CONFIG_DIR` references in `tests/test_adapter_copilot_cli.py`, the `opencode` column in `examples/inputs/harness-comparison.json`, and the OpenCode roadmap line are all gone. The TS plugin model had upstream issues that made an empirical-verification cycle infeasible for the v0.1.x line; removing the placeholder is cleaner than continuing to advertise a deferred adapter.

### Documentation
- **README install section rewritten** with an explicit prerequisites table (Python 3.10+, Node.js 18+, `npm install -g @google/design.md@0.1.1`, `pip install atv-paperboard`) and a `paperboard doctor` verify step in every harness's install block. Quick start no longer requires a repo clone.
- **Per-adapter `INSTALL.md` files** (`adapters/{claude-code,copilot-cli,codex}/INSTALL.md`) now have consistent Node.js + `@google/design.md` prerequisites.
- **README threat-model row** for `@google/design.md` schema drift now references `BRIDGE_VERSION_MIN` / `BRIDGE_VERSION_MAX_EXCL` and the sync-pins workflow.

### Tests
- `test_render_visual_fidelity.test_pico_tier_cascade_fidelity` expected pixels updated for the new dark palette (`#7170FF` primary, `#08090A` background). `_dominant_color` helper now ignores near-black pixels in addition to near-white so it can detect indigo h1 text on a dark canvas.
- Removed two permanently-skipped V3/V4 placeholder stubs from `tests/phase0/test_v3_v4_v5_v6.py` (`harness_claude_code` and `harness_codex` markers were hardcoded to skip and the function bodies were `...` — they asserted nothing). The original Phase-0 V3 (Claude Code hook propagates `CLAUDE_PLUGIN_DATA`) and V4 (Codex `PostToolUse` fires on Write) were validated manually against real harness sessions and remain documented under the 0.1.2 release notes.

### Philosophy
- Embedded the core motivation in the README — Karpathy's progression (text → markdown → HTML → interactive sims) and Thariq's "Unreasonable Effectiveness of HTML" piece, with four explicit philosophy principles tied to the four pillars.

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

