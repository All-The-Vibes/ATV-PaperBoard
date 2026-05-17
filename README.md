# atv-paperboard

> **Cross-harness HTML artifact toolkit for AI coding agents.** One spec. Three native adapters. Zero lock-in.
>
> Drop it into **Claude Code**, **Codex CLI**, or **GitHub Copilot CLI** and your agent stops dumping markdown into the chat — it emits paired `.html` + `.DESIGN.md` artifacts governed by Google's [DESIGN.md spec](https://github.com/google-labs-code/design.md), persisted to disk, and rolled into a compounding gallery you can actually share.

<!-- Inline-playable on github.com — keep this URL bare and on its own line. -->

https://github.com/user-attachments/assets/47a1c38e-58ae-4eac-8841-790181c2e3f3

<p align="center">
  <sub><strong><a href="assets/paperboard-teaser.mp4">▶ Fallback: open the 60-second teaser file</a></strong></sub>
</p>

---

## Why this exists

In May 2026, two posts crystallized what every AI coding agent gets wrong about output:

> **"Audio is the human-preferred _input_ to AIs, but vision is the preferred _output_ from them. Around a ~third of our brains is a massively parallel processor dedicated to vision — the 10-lane superhighway of information into the brain. The progression: 1) raw text 2) markdown _(current default)_ 3) HTML _(early but forming the new default)_ … _n_) interactive neural simulations. Hot tip: try ask for HTML."**
>
> — Andrej Karpathy, [May 11 2026](https://x.com/karpathy/status/2053872850101285137)

> **"Using Claude Code: The Unreasonable Effectiveness of HTML."** For plans, docs, prototypes, and mockups, HTML is _strictly better_ than markdown. Have the agent write `.html` files and open them in a browser.
>
> — Thariq ([@trq212](https://x.com/trq212/status/2052809885763747935)), May 8 2026

Paperboard is the toolkit that makes step 3 trivial **today**. Every coding agent right now renders status updates the same way: a wall of monospace markdown in a chat window. That output is **ephemeral, ugly, and impossible to share with stakeholders.** Paperboard intercepts the moment an agent emits structured data — a status table, a triage list, a comparison matrix — and turns it into a **lint-clean, single-file HTML artifact** that lives on disk, links into a gallery, and renders identically across Claude Code, Codex CLI, and GitHub Copilot CLI.

### Core philosophy

1. **Vision is the right output channel.** A table the agent wrote in HTML is read faster, shared more easily, and embeds in any PR — no Markdown renderer required, no copy-paste reformatting on the human side.
2. **Single-file or it doesn't ship.** Every artifact is one `.html` you can drag into a Slack thread or attach to a Jira ticket. CSS inlined, no CDN, no build step, no `npm install` on the recipient's machine.
3. **Design tokens are the contract, not vibes.** Every `.html` is paired with a `.DESIGN.md` (Google's spec) declaring allowable colors and type. The lint walks the HTML and rejects any drift. Quality stays consistent across N renders without policing prose.
4. **Compounding > one-shot.** Each render auto-regenerates `gallery.html` — your agent's output becomes a growing portfolio of paste-ready artifacts, not throwaway chat turns.

It's the same toolkit, the same contract, the same `core/` Python package — wired into **three different agent runtimes** via thin native adapters, plus a GitHub Actions recipe for the Copilot Coding Agent.

## Where it runs (today)

| Harness | Type | Status |
|---|---|---|
| **Claude Code** | Native plugin (`adapters/claude-code/`) | ✅ Shipping |
| **Codex CLI** | Native plugin (`adapters/codex/`) | ✅ Shipping |
| **GitHub Copilot CLI** | Native plugin (`adapters/copilot-cli/`) | ✅ Shipping — validated end-to-end against `copilot.exe v1.0.49` in an isolated sandbox |
| **GitHub Copilot Coding Agent** | GitHub Actions recipe (`recipes/github-actions/`) | ✅ Shipping |

> The Copilot CLI integration was validated against the real binary inside a fully isolated sandbox (`USERPROFILE`/`HOME`/`COPILOT_HOME` pinned). Hook fires, payload parses, suggestion injects, file lands, `exit=0`.

## The four pillars

| Pillar | What it does | How you'd break it |
|---|---|---|
| **Enforce** | Validates the paired DESIGN.md via the upstream Google CLI **and** an HTML-side color-token trace | Reference `{colors.nonexistent}` in DESIGN.md → lint rejects |
| **Render** | Single-file HTML → loopback HTTP server → auto-opens a browser tab (skipped in headless/remote) | `paperboard render --input data.json` → triple on disk + tab in <2s |
| **Persist** | Writes `{name}.html` + `{name}.DESIGN.md` + `{name}.meta.yaml` to the harness-resolved persistence path | After 3 emissions → 3 triples at the right path for that harness |
| **Compound** | Auto-regenerates a `gallery.html` that reflects every prior artifact, governed by its own DESIGN.md | Add a new artifact → gallery reflects it within 1s, gallery's own lint passes |

---

## Install — pick your harness

### Prerequisites (all paths)

| Requirement | Why | Install |
|---|---|---|
| **Python 3.10+** | ships the `paperboard` CLI every harness's hook invokes | system installer |
| **Node.js 18+** | the [`@google/design.md`](https://github.com/google-labs-code/design.md) lint bridge runs on Node — without it the **Enforce pillar silently degrades** | system installer |
| **`@google/design.md` 0.1.1** | the actual lint binary | `npm install -g @google/design.md@0.1.1` |
| **`atv-paperboard`** | the Python CLI + templates + default design | `pip install atv-paperboard` |

```bash
# One-shot prereqs (works from anywhere — no repo clone needed)
pip install atv-paperboard
npm install -g @google/design.md@0.1.1
paperboard doctor   # should show ✓ on every line
```

`paperboard doctor` is the canonical health check — run it after every install path below. If `@google/design.md` shows `not installed` or the lint row shows `✗ bridge unavailable`, the Enforce pillar is degraded and renders skip the real design lint (Python fallback only). Fix that before anything else.

### GitHub Copilot CLI (native plugin)

```bash
pip install atv-paperboard
npm install -g @google/design.md@0.1.1
# Then inside copilot (interactive):
/plugin marketplace add All-The-Vibes/ATV-PaperBoard
/plugin install atv-paperboard@atv-paperboard
```

Full instructions: [`adapters/copilot-cli/INSTALL.md`](adapters/copilot-cli/INSTALL.md)

### Claude Code (native plugin)

```bash
pip install atv-paperboard
npm install -g @google/design.md@0.1.1
# Then inside Claude Code:
/plugin marketplace add All-The-Vibes/ATV-PaperBoard
/plugin install atv-paperboard@atv-paperboard
```

Full instructions: [`adapters/claude-code/INSTALL.md`](adapters/claude-code/INSTALL.md)

### Codex CLI (native plugin)

```bash
pip install atv-paperboard
npm install -g @google/design.md@0.1.1
git clone https://github.com/All-The-Vibes/ATV-PaperBoard ~/.agents/skills/atv-paperboard
# Optional: add the hook to ~/.codex/config.toml (see INSTALL.md)
```

Full instructions: [`adapters/codex/INSTALL.md`](adapters/codex/INSTALL.md)

### GitHub Copilot Coding Agent (Actions recipe)

```bash
cp recipes/github-actions/*.template .github/
# Rename the .template extensions and fill in repo-specific values
```

The workflow installs both `atv-paperboard` (pip) and `@google/design.md` (npm) in CI — no extra setup on your machine. Full instructions: [`recipes/github-actions/INSTALL.md`](recipes/github-actions/INSTALL.md)

## Quick start (standalone — no harness needed)

Requires Python 3.10+ and Node.js 18+.

```bash
pip install atv-paperboard
npm install -g @google/design.md@0.1.1

# Render a sample artifact (default tier is `atv` — dark designed-document)
echo '{"title":"Hello","columns":["item","status"],"rows":[["paperboard","ok"]]}' | \
  paperboard render --input - --output-dir ./out
paperboard gallery --output-dir ./out
```

You'll get `out/<slug>.html`, `out/<slug>.DESIGN.md`, `out/<slug>.meta.yaml`, and `out/gallery.html` — a single neubrutalism-styled artifact + an auto-regenerated compounding gallery. The browser auto-opens on render unless `--no-open` is passed or the environment is headless.

To work on paperboard itself (instead of just using it), clone the repo and run `npm install && pip install -e .` from the root — that's the only path that exercises `core/`'s source directly.

## What you get

Three real example artifacts ship in `examples/output/`:

- [`build-status.html`](examples/output/build-status.html) — CI dashboard
- [`harness-comparison.html`](examples/output/harness-comparison.html) — side-by-side adapter feature matrix
- [`bug-hunt.html`](examples/output/bug-hunt.html) — triage snapshot
- [`gallery.html`](examples/output/gallery.html) — the compounding index, auto-regenerated on every render

Each artifact is a paired `.html` + `.DESIGN.md` + `.meta.yaml` **triple**. The HTML uses only design tokens declared in the DESIGN.md. The lint trace will reject any drift.

---

## How it actually works

### The artifact triple

Every `paperboard render` writes three files that travel together:

| File | Purpose |
|---|---|
| `{slug}.html` | Single-file, self-contained HTML. CSS inlined. No external runtime. Opens in any browser, embeds in any wiki, attaches to any PR. |
| `{slug}.DESIGN.md` | The Google [DESIGN.md](https://github.com/google-labs-code/design.md) contract: design tokens, type scale, do's & don'ts. **The lint pass walks the HTML and rejects any color/typography token that isn't declared here.** |
| `{slug}.meta.yaml` | Sidecar metadata — source input path, design used, tier, harness that produced it, timestamp. The gallery walks this to compose its index. |

The lint isn't generic "is this valid markdown" — it's a token-trace. If your HTML uses `#e63946` and that hex never appears in any token in the DESIGN.md, lint fails with a `fail-class` of `color-not-in-contract`. That's how design quality stays consistent across renders without policing prose.

### The render tiers (Pico vs daisyUI)

Two Jinja2 templates ship out of the box (plus the default `atv` tier):

- **`atv-tier`** — dark designed-document presentation; the canonical render that shows off the neubrutalism palette. **Default.** Use for dashboards, reports, and any rich multi-section output — the right answer in almost all cases.
- **`pico-tier`** — minimal, classless CSS via [Pico](https://picocss.com/). Sub-20KB HTML. Use only when the target audience explicitly wants a lightweight, framework-styled document.
- **`daisy-tier`** — richer component palette via [daisyUI](https://daisyui.com/). Use for marketing-grade hero artifacts.

Both consume the same design tokens via a **token-rename layer** in `core/render.py` that bridges `@google/design.md export tailwind` output to each framework's CSS variables (`--pico-primary` for Pico, `--p` for daisyUI). Adding a new tier = new Jinja template + new rename block; no changes to validation or persistence.

### Supported markdown features (input `body_md` / `.md` files)

When you feed a `.md` file or `body_md` JSON field, paperboard runs a small built-in markdown converter. The subset is chosen to match what the design contract can token-trace and to keep the rendered HTML reviewable as a static file. **Anything outside this list passes through unchanged** — useful for plain text, but no fancy renderer kicks in.

| Feature | Supported | Notes |
| --- | --- | --- |
| `# H1` – `###### H6` | ✅ | All six ATX heading levels render as `<hN>` tags; h5/h6 inherit type without dedicated styles |
| `**bold**`, `*italic*`, `` `code` `` | ✅ | Inline emphasis + code spans |
| `[text](url)` | ✅ | Autolinks `<https://...>` also work |
| `![alt](url)` | ✅ | Images |
| `- item` / `* item` / `1. item` | ✅ | Unordered and ordered lists |
| `> quote` | ✅ | Blockquotes |
| ` ``` ` fenced code blocks | ✅ | Language hint preserved as `class="language-<lang>"` |
| `---` horizontal rule | ✅ | Renders as `<hr>` |
| Pipe tables (GFM) | ✅ | `\| col \| col \|` with header separator |
| YAML frontmatter `---\n...\n---` | ✅ | Stripped before parsing; not rendered |
| Task lists `- [ ]` / `- [x]` | ❌ | Rendered as literal `[ ]`/`[x]` text |
| Strikethrough `~~text~~` | ❌ | Renders as `~~text~~` |
| Footnotes `[^1]` | ❌ | Renders as literal text |
| Definition lists | ❌ | Renders as paragraphs |
| Mermaid / KaTeX / mathjax | ❌ | Fenced blocks remain `<pre><code>` |
| Raw HTML inside markdown | ⚠️  Pass-through | Not sanitized; trust the agent that wrote it |

For richer compositions, use the **sections schema** (`hero`, `sec`, `stack-list`, `q-list`, `dep-list`, `steps`, `callout`, etc.) consumed by the atv tier. The sections schema is what gives you proper editorial typography, color-strip motifs, fit-rows, and the rest of the Linear-grade layout vocabulary; markdown is the lowest-friction input path but trades richness for portability.

### Auto-detection — `core/detect.py`

The CLI resolves which harness it's running inside via a strict precedence ladder. Env vars beat filesystem heuristics so that a user with multiple harnesses installed gets detected by the one currently running, not the one whose dotfiles happen to exist:

| Tier | Signal | Returns |
|---|---|---|
| 1 | `CLAUDE_PLUGIN_ROOT` or `CLAUDE_PLUGIN_DATA` in env | `claude-code` |
| 1 | `GITHUB_ACTIONS=true` | `copilot-coding-agent` |
| 1 | `COPILOT_HOME` in env, or `~/.copilot/installed-plugins/atv-paperboard/` exists | `copilot-cli` |
| 1 | `CODEX_HOME` in env | `codex` |
| 2 | `~/.codex/config.toml` exists | `codex` |
| 3 | `VSCODE_PID` AND `TERM_PROGRAM=vscode` | `copilot-ide` *(reserved for v0.2)* |
| Default | — | `standalone` |

The IDE-pairing tier requires **both** signals to avoid false positives from terminals that re-export `VSCODE_PID`.

### Per-harness persistence paths

`core/persist.py` resolves where artifacts land based on the detected harness. This is the load-bearing piece — get this wrong and the harness deletes your output:

| Harness | Persistence root |
|---|---|
| Claude Code | `${CLAUDE_PLUGIN_DATA}/<date>/` — **NOT** `${CLAUDE_PLUGIN_ROOT}`; the root is cleaned ~7 days after plugin updates |
| Codex CLI | `~/.codex/atv-paperboard-artifacts/<date>/` — user-scoped (Codex has no `CODEX_PLUGIN_DATA` analogue) |
| Copilot CLI | `${COPILOT_HOME:-~/.copilot}/plugin-data/atv-paperboard/artifacts/` — user-scoped |
| Copilot Coding Agent | `${repo}/paperboard-artifacts/<date>/` — workspace-scoped (PR-attached) |
| Standalone | `$(pwd)/paperboard-artifacts/` |

`--output-dir` overrides this for every subcommand.

### The three integration patterns

Different harnesses expose different surfaces. We don't fight that — we use one of three patterns per harness:

| Pattern | Harnesses using it | Mechanism |
|---|---|---|
| **Native plugin** | Claude Code, Codex CLI, Copilot CLI | Per-harness wrapper file (manifest/loader); same SKILL.md payloads; same Python core invoked via subprocess. |
| **Instructions + CLI** | Codex CLI fallback | `AGENTS.md` directs the agent to invoke `paperboard render` as a shell command — for users who don't want a full skill install. |
| **GitHub Actions hook** | Copilot Coding Agent | `.github/workflows/copilot-coding-agent-paperboard.yml` runs the CLI in CI for PR-attached artifacts. |

### Hook heuristic — why your terminal isn't on fire

A naive PostToolUse hook on `Write` would fire on every markdown table the agent emits and the user would get a `<system-reminder>` storm. The detect-artifact-candidate hook filters before suggesting anything:

1. **Numeric-or-status column requirement.** Skip unless the table has ≥ 2 numeric columns OR a column whose header matches `^(status|state|result|pass|fail|score|count|%|cost|p\d{2,3})$` (case-insensitive). Plain task lists do not fire.
2. **Path-prefix skiplist.** Skip if the written file is `*.md` and lives under `docs/`, `CHANGELOG`, `README*`, or `.github/` — those are user-authored docs, not requested renders.
3. **Self-recursion guard.** Skip if the path is under any `artifact_dir(harness)` — prevents the hook re-firing on artifacts it just wrote.
4. **Suppression window.** Skip if the prior suggestion fired < 30 seconds ago (per-session). State stored in `${persist_dir}/.suggest-cooldown`.
5. **Suggestion never auto-renders.** The hook only emits a `<system-reminder>`-style note with a paste-ready command. Auto-render is explicitly out of scope (avoids "magic" mis-fires).

### Copilot CLI — three Copilot surfaces, disambiguated

"Copilot" is now three meaningfully different products and Paperboard targets two of them:

| Surface | What it is | Plugin model | Paperboard support |
|---|---|---|---|
| **Copilot Extensions** (Copilot Apps) | Remote HTTPS endpoints invoked from chat | No local plugins; no FS access | Out of scope (remote-HTTPS only) |
| **Copilot Coding Agent** | GitHub-hosted agent on PRs | Repo-level instructions + workflow YAML | ✅ via `recipes/github-actions/` |
| **Copilot CLI** | Interactive `copilot` terminal agent on your machine | Full local plugin model (agents + skills + hooks + MCP) | ✅ via `adapters/copilot-cli/` |

The Copilot CLI adapter is a native plugin: a directory laid out as `agents/`, `skills/`, `hooks.json`, optional `.mcp.json`. There is no `plugin.json` — the **presence** of those well-known files is the manifest.

**Hook event names** (Copilot CLI accepts both camelCase and PascalCase): `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `errorOccurred`, `agentStop`.

**Architectural caveat — Copilot CLI hooks are FAIL-OPEN by default.** Unlike Claude Code (where a non-zero exit blocks the tool call), a Copilot CLI hook returning non-zero is *logged and ignored* — execution continues. This means the Enforce pillar on Copilot CLI is advisory at the hook layer; hard enforcement lives in `paperboard validate` and the CI recipe.

**The `additionalContext` channel.** A Copilot CLI hook that exits 0 with `{"additionalContext": "..."}` on stdout gets that text injected into the agent's next turn — the cleanest channel for `paperboard render` to tell the agent "I rendered your output to `<slug>.html`" without polluting the `bash` tool's output stream.

### What's NOT in v0.1.x

Explicit non-goals so you know what to expect:

- **Cross-harness artifact aggregation.** Each harness maintains its own gallery from its own persistence root. One unified gallery showing artifacts from multiple harnesses on one machine is a v0.1.x follow-up.
- **VS Code Chat Participant extension.** The in-IDE Copilot path. Complex, low marginal value over the instructions+CLI pattern. Deferred to v0.2.
- **MCP server integration.** Any harness. Deferred to v0.2.
- **Live-reload via WebSocket.** Artifacts are static HTML by design.
- **Full HTML-side token trace.** v0.1.x is **color-only**; spacing/typography/shadow lint is v0.2.
- **Silent plugin auto-update, telemetry, Anthropic Artifacts API adapter.** None. `paperboard doctor` surfaces available `@google/design.md` upgrades (24 h-cached, network-tolerant) and warns when the resolved bridge version drifts outside the tested compatibility range, but never installs anything — you control when to bump.

### Threat model & mitigations

The contract is hostile to a few specific failure modes:

| Threat | Mitigation |
|---|---|
| `@google/design.md` schema drift (it's alpha, pinned to 0.1.1) | `tests/test_core_bridge.py` is the drift guard; `paperboard doctor` warns when the resolved version falls outside `BRIDGE_VERSION_MIN`/`BRIDGE_VERSION_MAX_EXCL` in `core/bridge.py`; Dependabot opens a PR on minor/patch bumps and the `sync-bridge-version` workflow rewrites the install pins on the same PR so docs and `package.json` never drift apart. |
| `npx` zero-byte stdout on Windows | Replaced with node-direct: `node <bin>/dist/index.js ...` |
| Auto-detect false negatives (Codex lacks a stable session env var) | Tier-2 filesystem heuristic + "standalone" final fallback |
| Cross-harness state divergence | Each harness has its own persistence path; v0.1.x makes this explicit (no aggregation) |
| Prompt injection in fetched DESIGN.md (e.g., `--design <url>` later) | Loader must treat fetched content as data, lint before consumption, never expand `${...}` from fetched content into commands |
| Hook re-firing on its own artifacts | Self-recursion guard in heuristic rule 3 |

### Apache-2.0 throughout

- This toolkit: Apache-2.0.
- `@google/design.md@0.1.1` (pinned dev dep): Apache-2.0.
- Starter designs in `designs/starters/` carry per-file `attribution:` frontmatter with `inspired_by`, `not_affiliated_with`, `source_repo`, `source_commit`, `source_license`, `redistributed_under`. The `test_starter_attribution.py` lint fails the build if any starter lacks the required keys.

---

## Architecture

```
atv-paperboard/
├── core/                                    # SHARED Python core (harness-agnostic)
│   ├── bridge.py                            # node + @google/design.md wrapper
│   ├── render.py                            # html generation, tier templates, token-rename
│   ├── validate.py                          # google lint + html-side color-trace
│   ├── regenerate.py                        # 3-step retry (same → switch tier → fall back)
│   ├── gallery.py                           # compounding artifact
│   ├── persist.py                           # harness-aware persistence paths
│   ├── detect.py                            # auto-detect harness via env + fs heuristics
│   └── cli.py                               # `paperboard` standalone CLI (universal)
│
├── skills/                                  # SHARED SKILL.md payloads (3 harnesses portable)
│   ├── render-artifact/SKILL.md
│   ├── validate-artifact/SKILL.md
│   ├── regenerate-artifact/SKILL.md
│   └── gallery/SKILL.md
│
├── adapters/                                # per-harness wrapper files (~50 LOC each)
│   ├── claude-code/                         # .claude-plugin/plugin.json + hooks/hooks.json
│   ├── codex/                               # agents/openai.yaml + AGENTS.md.template
│   └── copilot-cli/                         # agents/ + skills/ + hooks.json
│
├── recipes/                                 # CI/workflow recipes (not adapters)
│   └── github-actions/                      # copilot-instructions.md + workflow.yml templates
│
├── designs/
│   ├── paperboard.DESIGN.md                 # default (dialed-back neubrutalism)
│   ├── starters/                            # stripi-, lin-ear-, vercel-inspired (attributed)
│   └── glass.DESIGN.md                      # opt-in premium tier
│
├── templates/
│   ├── atv-tier.html.j2                     # default — dark designed-document
│   ├── pico-tier.html.j2
│   ├── daisy-tier.html.j2
│   └── gallery.html.j2
│
├── examples/                                # 3 real artifact triples + gallery
└── tests/                                   # 130 passing, 2 live-harness gates skipped
```

The same SKILL.md files end up inside Claude Code's `/plugin install`, Codex's `~/.agents/skills/`, and Copilot CLI's `--plugin-dir` via per-adapter build steps. Every adapter and recipe invokes the same `core/cli.py` entry point via subprocess.

## CLI surface

```bash
paperboard render [--design <name|path|url>] [--tier atv|pico|daisy] [--input <path>]
paperboard validate <slug>
paperboard regenerate <slug>
paperboard gallery
paperboard detect-artifact-candidate <tool-output>   # hook helper
paperboard doctor                                     # diagnose install
```

Every command resolves the harness via `detect_harness()` first, then routes to the harness-appropriate persistence path. Browser-open is guarded by `CLAUDE_CODE_REMOTE` / `GITHUB_ACTIONS` / no-display heuristics so headless and remote sessions don't try to pop a tab.

## Optional artifact lint

If Node.js is available, paperboard ships an optional anti-pattern lint pass
backed by [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0).

```sh
npm install
npm run lint:artifacts                       # lints examples/output/
```

Or invoke the wrappers directly:

```sh
./scripts/lint-artifacts.sh path/to/*.html   # POSIX
```

```powershell
.\scripts\lint-artifacts.ps1 -Targets path\to\file.html   # Windows
```

The lint runs against generated HTML artifacts after `paperboard render`. The
core Python CLI does NOT invoke npm — lint is a separate opt-in step. Exit
code is non-zero if Critical/High issues are found, so CI can gate on it.
See `core/designs/impeccable-context/` for the underlying doctrine.

## Roadmap

- [CHANGELOG.md](CHANGELOG.md) — version history
- **v0.1.x** — Cross-harness gallery aggregation, additional render tiers, expanded design starters
- **v0.2** — VS Code Chat Participant (Copilot in-IDE path), MCP server integration, full HTML-side token trace (spacing/typography/shadow)

## License

Apache-2.0. See [LICENSE](LICENSE).

## Contributing

PRs welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for project layout, dev setup, test markers, lint config, branching, commit conventions, recipes for common contributions (new harness adapter, new design starter, new CLI subcommand), and where to file bug reports vs security issues. No CLA — inbound = outbound under Apache-2.0.



