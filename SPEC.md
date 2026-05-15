# atv-paperboard — v1 Build Specification (v4.2)

**Status:** v4.2 (delivered as v0.1.0-preview) · **Date:** 2026-05-14 · **License:** Apache-2.0
**Research lineage:**
- v1 → v2: integrated Google DESIGN.md format
- v2 → v3: adversarial-review + empirical CLI probe
- v3 → v4: expanded scope to 4 harnesses (Claude Code, Codex CLI, OpenCode, GitHub Copilot)
- v4 → v4.1: parallel deep-research pass against live docs corrected per-harness code blocks (§2.1 hooks wrapper + timeout unit, §2.2 TOML syntax + openai.yaml schema, §2.3 OpenCode plugin shape × 5 bugs), fixed @google/design.md license attribution, added §17 hook heuristic, §18 starter attribution schema, tightened auto-detect order
- v4.1 → v4.2: re-scoped to v0.1.0-preview = 2 native adapters (Claude Code, Codex) + 1 recipe (Copilot GH Actions); OpenCode deferred to v0.1.1 after Stage 4 found 5 breaking defects in the SPEC v4 OpenCode TS plugin that needed an empirical-verification cycle the schedule didn't accommodate.
**Research sources:**
- `obsidian-vault/raw/research/harness-synthesis-brief-2026-05-14.md`
- `obsidian-vault/raw/research/harness-claude-code-plugin-model-2026-05-14.md`
- `obsidian-vault/raw/research/harness-codex-cli-plugin-model-2026-05-14.md`
- `obsidian-vault/raw/research/harness-opencode-plugin-model-2026-05-14.md`
- `obsidian-vault/raw/research/harness-github-copilot-plugin-model-2026-05-14.md`
- Adversarial review: `SPEC-review-2026-05-14.md`
**External anchors:**
- DESIGN.md format — <https://github.com/google-labs-code/design.md>
- `@google/design.md` (0.1.1, alpha, Apache-2.0)
- Brand library — <https://github.com/VoltAgent/awesome-design-md>

A publicly-released **cross-harness** HTML-artifact toolkit that emits paired `.html` + `.DESIGN.md` artifacts governed by Google's DESIGN.md spec, served from loopback, persisted with metadata, and gathered into a compounding gallery. Ships native plugin wrappers for **Claude Code**, **Codex CLI**, and **OpenCode**, plus an instructions+CLI pattern for **GitHub Copilot**. Detects which harness it's running in and adapts persistence + invocation accordingly.

Part of the **ATV** family (Compound Engineering / gstack / Karpathy Guidelines lineage). Independent of `atv-starterkit` and `atv-design` — no shared packages, no required co-installation. Family-history only.

---

## 0. North Star

> **One Python core, **two native harness adapters + one CI recipe**, one design contract.** The plugin justifies its existence against raw-prompting by doing four things prompting cannot reliably do: Enforce, Render, Persist, Compound — **and it does them identically across every major agentic coding harness**.

Any v1 feature that doesn't strengthen a pillar or expand harness coverage to additional harnesses is out of scope.

### 0.1 The Four Pillars (harness-invariant)

| Pillar | What it does | Success test |
|---|---|---|
| **Enforce** | Validates the paired DESIGN.md via `node <bin>/dist/index.js lint --format json`, then HTML-side color-token-trace. | Lint rejects an artifact whose DESIGN.md has `{colors.nonexistent}`. |
| **Render** | Single-file HTML → loopback HTTP server → auto-open browser tab (or skip-open in headless contexts). | `paperboard render` writes the triple and opens a tab in <2s (unless remote/headless). |
| **Persist** | Writes the triple to harness-resolved persistence path with YAML metadata sidecar. | After 3 emissions, 3 triples exist at the harness's correct path. |
| **Compound** | Auto-regenerates a gallery HTML reflecting all prior artifacts. Gallery uses `paperboard.DESIGN.md` as its design source. | Gallery reflects new artifact within 1s; gallery's own lint passes. |

### 0.2 The Three Integration Patterns (one per harness type)

| Pattern | Harnesses | Mechanism |
|---|---|---|
| **Native plugin** | Claude Code, Codex CLI | Per-harness wrapper file (manifest/loader); same SKILL.md payloads; same Python core via subprocess. |
| **Instructions + CLI** | Codex CLI fallback, GitHub Copilot | `AGENTS.md` (Codex) or `.github/copilot-instructions.md` (Copilot) directs the agent to invoke a local CLI. |
| **Coding-Agent hook** | GitHub Copilot (headless) | `.github/workflows/copilot-coding-agent-paperboard.yml` runs the CLI in Actions for PR-attached artifacts. |
| **Deferred (v0.1.1)** | OpenCode | Native TS plugin (5 breaking SPEC v4 defects found in Stage 4; empirical-verification cycle required). |

### 0.3 Empirical Verifications (all four harnesses, pre-SPEC)

| Verification | Result | Source |
|---|---|---|
| `@google/design.md` produces parseable JSON via `node <bin>` | ✅ 238-byte JSON for minimal DESIGN.md | direct probe |
| `@google/design.md` via npx | ❌ zero-byte stdout on Windows | direct probe |
| awesome-design-md ships real DESIGN.md files | ✅ `design-md/<brand>/DESIGN.md` per brand, fully authored | WebFetch |
| Claude Code plugin manifest = `.claude-plugin/plugin.json` | ✅ verified, plus 29 hook events, 5 hook types | Track 1 |
| Claude Code persistence = `${CLAUDE_PLUGIN_DATA}` (NOT plugin root) | ✅ confirmed; plugin root cleaned after 7 days | Track 1 |
| Claude Code distribution = `/plugin install <name>@<marketplace>` (NOT `npx skills add`) | ✅ confirmed | Track 1 |
| Codex skill format = `~/.agents/skills/<name>/SKILL.md` (open-agent-skills standard) | ✅ confirmed | Track 2 |
| Codex hooks share Claude Code names (PreToolUse, PostToolUse, Stop, etc.) | ✅ confirmed | Track 2 |
| OpenCode SKILL.md format = Claude-compatible (verbatim portable) | ✅ confirmed | Track 4 |
| OpenCode plugin loader = TypeScript Plugin factory, NOT JSON | ⚠️ different shape; wrapper file is JS not declarative | Track 4 |
| Copilot has NO local plugin model for filesystem/browser access | ❌ confirmed (Extensions = remote HTTPS only) | Track 3 |
| Copilot integration path = custom instructions + local CLI + Coding Agent hook | ✅ documented | Track 3 |

---

## 1. Repository Layout

```
atv-paperboard/
├── LICENSE                                  # Apache-2.0
├── README.md                                # public-facing intro + per-harness install
├── SPEC.md                                  # this file
├── SPEC-review-2026-05-14.md                # adversarial review record
├── CHANGELOG.md
│
├── core/                                    # SHARED Python core (harness-agnostic)
│   ├── __init__.py
│   ├── bridge.py                            # node + @google/design.md wrapper
│   ├── render.py                            # html generation, tier templates
│   ├── validate.py                          # google lint + html-side color-trace
│   ├── regenerate.py                        # 3-step retry strategy
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
│   ├── claude-code/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── hooks/hooks.json                 # PostToolUse → detect-artifact-candidate
│   │   ├── agents/artifact-reviewer.md
│   │   └── INSTALL.md                       # `/plugin marketplace add` + `/plugin install`
│   └── codex/
│       ├── agents/openai.yaml
│       ├── AGENTS.md.template               # instructions snippet for fallback users
│       └── INSTALL.md                       # `git clone` into ~/.agents/skills/
│
├── recipes/                                 # CI/workflow recipes (not adapters)
│   └── github-actions/
│       ├── copilot-instructions.md.template # for ${repo}/.github/copilot-instructions.md
│       ├── workflow.yml.template            # for ${repo}/.github/workflows/...
│       └── INSTALL.md                       # how to wire into a GitHub repo
│
├── designs/
│   ├── paperboard.DESIGN.md                 # default (dialed-back neubrutalism)
│   ├── starters/
│   │   ├── stripi-inspired.DESIGN.md
│   │   ├── lin-ear-inspired.DESIGN.md
│   │   └── vercel-inspired.DESIGN.md
│   └── glass.DESIGN.md                      # opt-in premium tier
│
├── templates/
│   ├── pico-tier.html.j2
│   ├── daisy-tier.html.j2
│   └── gallery.html.j2
│
├── examples/                                # populated Phase 7
│   └── .gitkeep
│
└── tests/
    ├── test_core_bridge.py                  # node-direct invocation works cross-platform
    ├── test_core_validate.py                # lint + html checks
    ├── test_core_persist.py                 # harness-aware path resolution
    ├── test_core_detect.py                  # 4 harnesses + standalone detection
    ├── test_adapter_claude_code.py
    ├── test_adapter_codex.py
    ├── test_adapter_opencode.py
    ├── test_adapter_copilot.py              # CLI-invocation fixture only
    └── fixtures/
        ├── compliant/
        └── violations/
```

**Key change from SPEC v3:** the plugin is now structured as `core/` (Python, harness-agnostic) + `skills/` (SKILL.md payloads, ported verbatim to 2 native harnesses) + `adapters/` (one folder per native harness, thin wrappers) + `recipes/` (CI templates for harnesses without a local plugin model). The same SKILL.md files end up inside Claude Code's `plugin install` and Codex's `~/.agents/skills/` via build-time copy steps. OpenCode support is deferred to v0.1.1.

---

## 2. Per-Harness Adapter Specifications

### 2.1 Claude Code (`adapters/claude-code/`)

**Manifest** (`.claude-plugin/plugin.json`):
```json
{
  "name": "atv-paperboard",
  "version": "0.1.0",
  "description": "Cross-harness HTML artifact toolkit. Enforce, render, persist, compound.",
  "license": "Apache-2.0",
  "homepage": "https://github.com/<org>/atv-paperboard"
}
```

(Per Track 1: only `name` is *required*; other fields are optional. The build-time copy step lands `skills/`, `agents/`, `hooks/`, and a `bin/` directory pointing into the Python core at `core/cli.py` shim.)

**Hooks** (`hooks/hooks.json`):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [{
        "type": "command",
        "command": "python ${CLAUDE_PLUGIN_ROOT}/core/cli.py detect-artifact-candidate \"${TOOL_OUTPUT}\"",
        "timeout": 2
      }]
    }]
  }
}
```

(Plugin `hooks/hooks.json` requires the outer `"hooks"` wrapper key — distinct from standalone `settings.json` which does not. Timeout unit is **seconds**, default 600s; SPEC v4 wrote `2000` which would have been ~33 minutes — fixed to `2`. Source: deep-research stage 2, code.claude.com/docs/en/plugins-reference.)

**Persistence:** `${CLAUDE_PLUGIN_DATA}/<date>/<slug>.{html,DESIGN.md,meta.yaml}` (CRITICAL — *not* plugin root. Per Track 1 + deep-research stage 2: `CLAUDE_PLUGIN_ROOT` *changes on plugin updates* and old versions are cleaned after ~7 days; the currently-running version stays valid for the session. Treat `CLAUDE_PLUGIN_ROOT` as ephemeral for write purposes either way. This was a SPEC v3 bug.)

**Browser open guard:** check `CLAUDE_CODE_REMOTE=true` before calling `webbrowser.open_new_tab`. Remote sessions get a returned URL only.

**Install (per Track 1):**
```
/plugin marketplace add <owner>/atv-paperboard
/plugin install atv-paperboard@<marketplace>
```

### 2.2 Codex CLI (`adapters/codex/`)

**Skill location:** `~/.agents/skills/atv-paperboard/SKILL.md` (per Track 2's open-agent-skills standard; identical SKILL.md files as the Claude Code adapter).

**Codex-specific config** (`agents/openai.yaml`):
```yaml
# Codex-specific metadata that complements SKILL.md.
# Schema source: developers.openai.com/codex/skills
interface:
  display_name: "atv-paperboard"
  short_description: "Cross-harness HTML artifact toolkit."
  brand_color: "#3B82F6"
policy:
  allow_implicit_invocation: true
```

(SPEC v4 wrote an `allowed_tools: [...]` field — that field does not exist in the documented `openai.yaml` schema. Tool access in Codex is governed by `~/.codex/config.toml` `[permissions]` blocks and sandbox policy, not by skill frontmatter. Source: deep-research stage 3.)

**Hooks** (`~/.codex/config.toml` `[hooks]` block — applied per-user or per-project):
```toml
[[hooks.PostToolUse]]
matcher = "^Write$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "python ${HOME}/.agents/skills/atv-paperboard/core/cli.py detect-artifact-candidate"
timeout = 30
```

(SPEC v4 wrote `[hooks.PostToolUse]` with `match.tool = "Write"` — both wrong. Real schema uses TOML array-of-tables `[[hooks.PostToolUse]]` plus a nested `[[hooks.PostToolUse.hooks]]` block; matcher is a regex string under the key `matcher`. Source: deep-research stage 3, developers.openai.com/codex/config-advanced.)

**Persistence:** `${HOME}/.codex/atv-paperboard-artifacts/<date>/...` (Codex has no documented `${CODEX_PLUGIN_DATA}` analogue; we use a stable user-scoped path).

**Detection signal at runtime:** Codex does not inject a session-scoped `CODEX_*` env var (Track 2 + stage 3). Detection order: (1) `CODEX_HOME` env var present (user-settable, documented), (2) `~/.codex/config.toml` exists. Both are "soft" — a user who has *installed* Codex but is currently running another harness can mis-detect; the runtime precedence in `core/detect.py` checks Claude Code's and OpenCode's env vars first to prevent this.

**Install:**
```bash
git clone https://github.com/<org>/atv-paperboard ~/.agents/skills/atv-paperboard
# Optional: edit ~/.codex/config.toml to register the hook
```

**Fallback path (no skill install):** drop `adapters/codex/AGENTS.md.template` content into the user's `AGENTS.md` directing Codex to invoke `paperboard render` as a shell command.

### 2.3 GitHub Copilot (`recipes/github-actions/` — recipe, not an adapter)

Copilot has no local plugin path for filesystem + browser access (see §0.3); v0.1.0-preview ships this as a GitHub Actions recipe rather than a 4th adapter.

**No local plugin path via Copilot Extensions.** Track 3 + stage 5 confirmed Copilot Extensions are *remote HTTPS services* with no filesystem or browser access. The VS Code Chat Participant API *does* give local FS + browser access, but ships as a VSIX and is deferred to v0.2 (the instructions+CLI pattern reaches Coding Agent users too, which the Chat Participant alone doesn't). Integration for v0.1.0 is via two templates:

**Template 1** — `copilot-instructions.md.template` (drops into `${repo}/.github/copilot-instructions.md`):
```markdown
## HTML Artifact Generation

When you produce structured output (tables, comparisons, status snapshots, dashboards),
upgrade it to a beautiful HTML artifact by invoking:

    paperboard render --input <path-to-structured-output>

The artifact and its DESIGN.md sidecar will be written to ./paperboard-artifacts/.
Reference the latest artifact in your PR body via:

    [![Latest paperboard artifact](paperboard-artifacts/index.svg)](paperboard-artifacts/index.html)
```

**Template 2** — `workflow.yml.template` (for `.github/workflows/`):
```yaml
name: atv-paperboard (Copilot Coding Agent hook)
on:
  workflow_dispatch:
  pull_request:
    paths: ['paperboard-artifacts/**']
jobs:
  validate-artifacts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install -g @google/design.md@0.1.1
      - uses: actions/setup-python@v5
      - run: pip install atv-paperboard
      - run: paperboard validate-all paperboard-artifacts/
```

**Persistence:** `${repo}/paperboard-artifacts/<date>/...` (workspace-scoped, NOT user-scoped, because Copilot operates per-repo and per-PR).

**Detection signal at runtime:** `${GITHUB_ACTIONS}=true` (for Coding Agent path) OR (`${VSCODE_PID}` AND `${TERM_PROGRAM}=vscode`) (for IDE path; pairing prevents false positives from terminals that re-export `VSCODE_PID`). Track 3 + stage 5 flagged the IDE chat path as v0.2 deferred.

**Install:**
```bash
# In your repo:
pip install atv-paperboard
cp recipes/github-actions/*.template .github/
```

### 2.4 OpenCode (deferred to v0.1.1)

OpenCode was scoped as the 3rd native adapter in SPEC v4.1 (§2.3 in that version). During Stage 4 of the deep-research pass, five runtime-fatal bugs were found in the SPEC v4 TypeScript plugin block: wrong package name (`@opencode/plugin` → `@opencode-ai/plugin@1.14.51`), wrong export name, wrong `Plugin` type signature, non-existent `ctx.pluginDir` field, and wrong hook-handler argument shape. These defects required an empirical-verification cycle (real install, live plugin execution) that the v0.1.0-preview schedule did not accommodate. The corrected plugin block is preserved in git history at the v4.1 SPEC commit. It will be implemented and verified in v0.1.1.

---

## 3. The Universal Python Core (`core/`)

Same logic as SPEC v3's skills/bin shims, but reorganized as importable Python modules. The standalone CLI (`core/cli.py`) is the universal entry point that all adapters subprocess into.

### 3.1 `core/detect.py` — Auto-detect harness

```python
"""Detect which harness we're running in. Falls back to 'standalone' for headless CLI use.

Precedence rationale (deep-research stage 7 H4):
- Env vars beat filesystem heuristics — a user with multiple harnesses installed should be
  detected by the one currently running, not the one whose dotfiles happen to exist.
- Claude Code first because its env vars are the most specific and least likely to be
  re-exported in unrelated contexts.
- Copilot's `GITHUB_ACTIONS` is checked early because it dominates the CI execution path.
"""
import os
from pathlib import Path

def detect_harness() -> str:
    # Tier 1 — harness-specific session env vars (strongest signal)
    if "CLAUDE_PLUGIN_ROOT" in os.environ or "CLAUDE_PLUGIN_DATA" in os.environ:
        return "claude-code"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "copilot-coding-agent"
    if "OPENCODE_CONFIG_DIR" in os.environ:
        return "opencode"
    if "CODEX_HOME" in os.environ:
        return "codex"
    # Tier 2 — filesystem heuristics (only after Tier 1 misses)
    if (Path.home() / ".codex" / "config.toml").exists():
        return "codex"
    # Tier 3 — IDE pairing (require both signals to avoid false positives from
    # terminals that re-export VSCODE_PID; deep-research stage 5)
    if "VSCODE_PID" in os.environ and os.environ.get("TERM_PROGRAM") == "vscode":
        return "copilot-ide"
    return "standalone"
```

**Note (v0.1.0-preview):** the `opencode` and `copilot-ide` return values are reserved for v0.1.1+. The v0.1.0-preview product only acts on `claude-code | codex | copilot-coding-agent | standalone`; `opencode` and `copilot-ide` fall through to `standalone` behavior in all current code paths.

### 3.2 `core/persist.py` — Harness-aware paths

```python
def artifact_dir(harness: str) -> Path:
    if harness == "claude-code":
        return Path(os.environ["CLAUDE_PLUGIN_DATA"])
    if harness == "codex":
        return Path.home() / ".codex" / "atv-paperboard-artifacts"
    if harness == "opencode":
        return Path(os.environ["OPENCODE_CONFIG_DIR"]) / "atv-paperboard-artifacts"
    if harness.startswith("copilot"):
        return Path.cwd() / "paperboard-artifacts"  # workspace-scoped
    return Path.cwd() / "paperboard-artifacts"      # standalone
```

### 3.3 `core/cli.py` — Universal entry point

```bash
paperboard render [--design <name|path|url>] [--tier pico|daisy] [--input <path>]
paperboard validate <slug>
paperboard regenerate <slug>
paperboard gallery
paperboard detect-artifact-candidate <tool-output>  # hook helper
paperboard doctor                                    # diagnose install
```

Every command resolves the harness via `detect_harness()` first, then routes to the harness-appropriate persistence path. **Browser-open** checks `detect_harness()` AND the `CLAUDE_CODE_REMOTE` / `GITHUB_ACTIONS` / no-display heuristics before calling `webbrowser.open_new_tab`.

### 3.4 `core/bridge.py` — Google CLI wrapper (revised from SPEC v3)

Unchanged behavior; structured as a Python module rather than a `bin/` shim. Caches the `node <bin>/dist/index.js` resolution at `~/.atv-paperboard/config.json` (user-scoped, harness-agnostic — avoids per-harness divergence). Cache file MUST include a `schema_version: int` field so future SPEC bumps can invalidate without manual cleanup. Same node-direct invocation, same JSON shape, same `fail-class` taxonomy.

---

## 4. Shared SKILL.md Payloads (`skills/`)

Same SKILL.md files as SPEC v3's §5. They're authored once and copy-deployed to:
- Claude Code: `${plugin}/skills/` via the adapter directory layout
- Codex: `~/.agents/skills/atv-paperboard/skills/` via git clone
- OpenCode: `.opencode/skills/` via npm install + config entry

Per Track 4 (OpenCode docs say it reads "Claude-compatible paths") and Track 2 (open-agent-skills standard), this is genuinely portable, not a hack.

---

## 5. Design Contract (unchanged from SPEC v3 §3)

- `designs/paperboard.DESIGN.md` — dialed-back neubrutalism (default).
- `designs/glass.DESIGN.md` — premium opt-in.
- 3 starters with `-inspired` naming and per-file attribution.
- Apple dropped (trademark).
- Tokens flow through `@google/design.md export` (formats: `json-tailwind`, `css-tailwind`, `tailwind`, `dtcg`) to generate CSS variables consumed by Pico (cheap tier) or daisyUI (rich tier). **NB:** none of the four upstream export formats are natively Pico/daisyUI-shaped — a thin token-rename layer in `core/render.py` maps `--color-primary-500` → Pico's `--pico-primary` / daisyUI's `--p`. This layer is Phase 1 work; deep-research stage 1 flagged the mismatch.

---

## 6. Build Phases (v0.1.0-preview delivered; v0.1.1 OpenCode budget: 2 days)

The shared-core architecture means harness expansion is mostly *adapter* work, not *core* duplication.

### Phase 0 — Scaffold + cross-harness verification (Day 1)
- Init repo, Apache-2.0 LICENSE, directory skeleton
- `core/bridge.py` + smoke-test against `@google/design.md@0.1.1`
- `core/detect.py` + unit tests covering all 4 harnesses' detection signals
- `designs/paperboard.DESIGN.md`
- **Verify on each platform:** does `bin/`-shim subprocess inherit `CLAUDE_PLUGIN_DATA`? (SPEC v3 flagged this as unverified.) Test in Claude Code session.

### Phase 1 — Core RENDER pillar (Days 2–3)
- `core/render.py` + `templates/pico-tier.html.j2`
- `skills/render-artifact/SKILL.md`
- `core/cli.py render` works standalone
- **Success test:** `paperboard render --input fixture.json` writes triple + opens browser in <2s.

### Phase 2 — Core ENFORCE pillar (Days 4–5)
- `core/validate.py` (lint + color-only HTML token-trace)
- `core/regenerate.py` (3-step retry: same → switch tier → fall back to paperboard)
- `skills/validate-artifact/SKILL.md` + `skills/regenerate-artifact/SKILL.md`
- `agents/artifact-reviewer.md` (Claude Code adapter; reports only)
- **Success test:** validator correctly assigns `fail-class`; regenerator differentiates retries; reviewer never self-approves.

### Phase 3 — Starters + design import (Day 6)
- 3 starter DESIGN.md files copied from awesome-design-md with full attribution
- `core/cli.py render --design <name|path|url>` resolves all three sources
- **Success test:** `paperboard render --design stripi-inspired` produces a Stripi-themed artifact; lint passes; attribution preserved.

### Phase 4 — Core PERSIST + Claude Code adapter (Day 7)
- `core/persist.py` (harness-aware paths)
- `adapters/claude-code/` (plugin.json, hooks.json, agent, INSTALL.md)
- **Success test:** install via `/plugin install` in a real Claude Code session; emit artifact; verify it lands in `${CLAUDE_PLUGIN_DATA}/<date>/`.

### Phase 5 — Codex + OpenCode adapters (Day 8)
- `adapters/codex/` (openai.yaml, AGENTS.md template, INSTALL.md)
- `adapters/opencode/` (opencode.plugin.ts, opencode.json template, INSTALL.md)
- Verify shared SKILL.md files work in both contexts
- **Success test:** in a fresh Codex session and a fresh OpenCode session, render a sample artifact; verify it lands at the harness's correct persistence path.

### Phase 6 — Copilot adapter + COMPOUND pillar (Days 9–10)
- `adapters/copilot/` (copilot-instructions.md template, workflow.yml template, INSTALL.md)
- `core/gallery.py` + `skills/gallery/SKILL.md` + `templates/gallery.html.j2`
- Gallery reuses `paperboard.DESIGN.md` as its design
- **Success test:** after 3 artifacts emitted from 3 different harnesses, each harness's gallery reflects the same harness-local artifacts. Cross-harness aggregation deferred to v0.2.

### Phase 7 — Public release polish (Day 11)
- README with per-harness install sections (4 install paths, 4 screenshots)
- CHANGELOG seeded with v0.1.0 + documented v0.2 migration plan
- Run `gh search code` prior-art check
- USPTO basic search on "atv-paperboard" + "paperboard"
- Full Phase 0–6 test matrix runs green across all 4 harnesses
- Tag v0.1.0; publish to PyPI (`atv-paperboard`); push to GitHub; submit Claude Code marketplace PR

### Phase 7a — Real-world test pass (deep-research-driven)

10 bugs surfaced and fixed by driving the actual CLI on 3 real-world fixtures (build-status, harness-comparison, bug-hunt). All four pillars (Enforce / Render / Persist / Compound) verified end-to-end. Bugs RW-1 through RW-10 resolved same-session.

**Total: 11 working days.** Same as SPEC v3's single-harness estimate — the universal-core architecture pays for cross-harness coverage almost for free.

---

## 7. Non-Goals (v2+)

- Forking the DESIGN.md spec.
- Cross-harness artifact aggregation (one gallery showing artifacts from multiple harnesses on one machine). Defer to v0.2.
- Copilot VS Code Chat Participant extension (the in-IDE chat path; complex, low marginal value over the instructions+CLI pattern). Defer to v0.2.
- MCP server integration (any harness).
- Live-reload via WebSocket.
- Anthropic Artifacts API adapter.
- Narrowed DESIGN.md emission. Verbatim only for v0.1.0.
- Full HTML-side token trace (spacing/typography/shadow). Color-only for v0.1.0.
- Apple-style starter. Dropped.
- shadcn/ui tier.
- Plugin auto-update.
- Telemetry.

---

## 8. Open Questions Reserved for Implementation Time

1. **`bin/`-subprocess env inheritance** — Track 1 flagged that `CLAUDE_PLUGIN_DATA` may not be visible to subprocesses invoked from `bin/` shims. Verify in Phase 0 across all 4 harnesses' subprocess models.
2. **OpenCode SKILL.md verbatim portability** — Track 4 says SKILL.md format is identical, but the `allowed_tools` frontmatter field may differ from Claude Code's `allowed-tools` (hyphen). Verify and normalize at build time.
3. **Codex `~/.agents/skills/` global vs per-repo precedence** — Track 2 documented the precedence ladder; deep-research stage 3 corrected the count to **6 tiers** (CWD → ascending parents → repo root → user → admin `/etc/codex/skills` → built-in). Default for atv-paperboard: user-scoped (`~/.agents/skills/atv-paperboard/`).
4. **Copilot Coding Agent workflow trigger conditions** — should the workflow run on every PR with `paperboard-artifacts/` changes, or only on demand? Default: PR-on-change for v0.1.0, opt-in for `workflow_dispatch` v0.2.
5. **`@google/design.md` 0.2 release** — same integration-test guard as SPEC v3.
6. **`paperboard` CLI name** — deep-research stage 6 confirmed: PyPI `paperboard` is available; **npm `paperboard` is taken** (Majid Sajadi's bookmark CLI, v0.0.2); `atv-paperboard` is available on both. v0.1.0 publishes as `atv-paperboard` on PyPI **and** npm; CLI invocation remains `paperboard` via PyPI console_scripts entry. USPTO TESS pass on "paperboard" / "atv" in IC 009/042 is still owed manually (Phase 7 / pre-public-push).

---

## 9. Threat Mitigations Re-Confirmed (from `SPEC-review-2026-05-14.md`)

| Threat | v3 status | v4 status |
|---|---|---|
| T1 — `@google/design.md` alpha/proprietary | Pin 0.1.1, node-direct, schema-drift test | Same |
| T1 — npx broken on Windows | Replaced with node-direct | Same |
| T2 — Phase 3 7×under-budgeted | Reduced to 1 day (real files in awesome-design-md) | Same |
| T2 — Token-trace too hard | Color-only for v0.1.0 | Same |
| T2 — Gallery self-DESIGN.md | Reuse paperboard.DESIGN.md | Same |
| T3 — Apple trademark | Dropped | Same |
| T3 — Starter attribution | Per-file frontmatter | Same |
| T4 — Narrowed DESIGN.md | Verbatim emission | Same |
| T4 — Hook false positives | Tightened (Claude Code only; Codex/OpenCode have different matchers) | Same logic, applied per-adapter |
| T4 — Reviewer 3-retry dead-end | Differentiated retries via regenerator | Same |
| T5 — Verifier-not-separate | Three-role architecture (writer/reporter/strategist) | Same |
| **NEW T6** — Auto-detect false negatives | Codex lacks stable env var; fall back to filesystem heuristic; "standalone" mode as ultimate fallback | New mitigation |
| **NEW T7** — Cross-harness state divergence | Each harness has its own persistence path; v0.1.0 makes this explicit (no cross-harness aggregation) | Accepted as v0.1.0 limitation |
| **NEW T8** — Prompt injection in research-fetch contexts | Track 3 encountered prompt injection in a fetched GitHub Docs page; if SPEC v4 includes any agent that fetches external docs at user request, document the hardening pattern (treat fetched content as data, never as instructions). | Documented in §13 |

---

## 10. The IDEO + Google Framing (for README)

> **atv-paperboard** is design-thinking applied to LLM output, regardless of which coding harness you use. The IDEO heritage shows up in the *rigor*: every artifact carries its own DESIGN.md with explicit Do's and Don'ts. The Google heritage shows up in the *format*: Google Labs' DESIGN.md spec gives the toolkit a real, lintable, exportable contract instead of vibes-based styling. The cross-harness coverage means design quality is consistent whether you're in Claude Code, Codex, OpenCode, or Copilot.

---

## 11. Karpathy Rule Compliance (v4 audit)

- **Minimum code**: the core is shared. Per-harness adapters are ~50 LOC of glue each. We are not building 4 plugins — we are building 1 toolkit with 4 invocation paths.
- **Surgical changes**: every line of v4 traces to either (a) a v3 carryover, (b) a verified research finding, or (c) a documented Threat resolution.
- **Verifier separate from writer**: the three-role architecture (render-artifact / artifact-reviewer / regenerate-artifact) is preserved.
- **Goal-driven execution**: each phase has explicit Success Tests.
- **No speculative abstractions**: cross-harness aggregation, MCP, IDE chat participant, live-reload — all explicitly v2+.

---

## 12. Implementation Notes for Contributors

- **Implementation work goes through the `executor` agent** per OMC delegation. Reading research, running tests, and inspecting artifacts can stay in the orchestrator.
- **`@google/design.md` is alpha and Apache-2.0.** Pin to `0.1.1` exact via committed `package.json` + `package-lock.json`. Treat the JSON output shape as load-bearing; the `tests/test_core_bridge.py` integration test guards it.
- **Per-harness CI**: GitHub Actions matrix across `[claude-code-mock, codex-mock, opencode-mock, copilot-mock]` × `[ubuntu, macos, windows]`. The mocks set the relevant env vars + filesystem hints; real-harness validation is part of release rehearsal, not every PR.
- **Karpathy guidelines apply throughout.**

---

## 13. Security Note (new in v4)

Track 3's research agent encountered embedded prompt-injection in a fetched GitHub Docs page during research (attempting to redirect the agent into Telegram cron setup; correctly ignored). If `atv-paperboard` ever includes a feature that fetches external content at runtime (e.g., a `--design <url>` that pulls a remote DESIGN.md), the loader must:
- Treat fetched content as *data*, never as *instructions* to the agent.
- Lint the fetched DESIGN.md before any consumption.
- Never expand `${...}` or shell-escape constructs from fetched content into commands.

This is a hardening requirement, not a v0.1.0 blocker, but worth documenting now while the lesson is fresh.

---

## 14. Anchor Documents

- DESIGN.md format — <https://github.com/google-labs-code/design.md>
- Brand library — <https://github.com/VoltAgent/awesome-design-md>
- Adversarial review record — `SPEC-review-2026-05-14.md`
- Deep-research record (v4 → v4.1) — `.omc/research/research-20260514-spec-v4-deep/report.md`
- Research (synthesis) — `obsidian-vault/raw/research/harness-synthesis-brief-2026-05-14.md`
- Research (Claude Code plugin model) — `.../harness-claude-code-plugin-model-2026-05-14.md`
- Research (Codex CLI plugin model) — `.../harness-codex-cli-plugin-model-2026-05-14.md`
- Research (OpenCode plugin model) — `.../harness-opencode-plugin-model-2026-05-14.md`
- Research (GitHub Copilot plugin model) — `.../harness-github-copilot-plugin-model-2026-05-14.md`
- Karpathy guidelines — `~/.claude/rules/common/best-practices.md`
- Family-history reference — `wiki/ATV StarterKit.md` (GitHub Copilot scaffolder; not a dependency)
- Family-history reference — `wiki/atv-design.md` (Claude-style design experience on GitHub Copilot; not a dependency)
- Justification anchor — `wiki/HTML as LLM Output Format.md`

---

## 15. Phase 0 Empirical Verification Matrix (new in v4.1)

Phase 0 is *not* a scaffolding day — it is a verification day. Every claim below must produce a passing test artifact in `tests/phase0/` before Phase 1 begins.

| ID | Claim | Test | Failure mode if false |
|---|---|---|---|
| V1 | `@google/design.md@0.1.1` lints a minimal DESIGN.md and emits parseable JSON via `node <bin>/dist/index.js lint --format json` | Run on `fixtures/compliant/minimal.DESIGN.md`; assert `findings == []` | ENFORCE pillar collapses; switch to OfflineMode subset (broken-ref + missing-sections + missing-typography) |
| V2 | `node <bin>/dist/index.js export --format css-tailwind` produces tokens consumable after the Pico/daisyUI rename layer | Run on `paperboard.DESIGN.md`; assert at least 5 `--color-*` and 3 `--font-*` vars present | RENDER pillar tier templates need redesign; consider single-tier v0.1.0 |

**V2 addendum (empirically corrected at execution time):** `@google/design.md` export emits only `tailwind | dtcg` formats — the `css-tailwind` format flag is not available. The token-rename layer in `core/render.py` bridges exported `tailwind` tokens to Pico/daisyUI CSS variables.
| V3 | Hook command subprocess in Claude Code inherits `CLAUDE_PLUGIN_DATA` | Install plugin into a real Claude Code session; trigger PostToolUse Write; assert log line contains a real path | PERSIST pillar broken for Claude Code; fallback to `CLAUDE_PLUGIN_ROOT/../data` or filesystem walk |
| V4 | Codex `[[hooks.PostToolUse]]` block fires on Write tool with `matcher = "^Write$"` | Set hook in real Codex session; perform a Write; assert log line contains the right TOOL_OUTPUT | Fall back to AGENTS.md instructions-only pattern for v0.1.0 Codex |
| V5 | `core/detect.py` returns the correct harness in 5 mock environments (cc, codex, opencode, copilot-CI, standalone) | `pytest tests/test_core_detect.py` | T6 mitigation insufficient; tighten precedence further |
| V6 | `python` is invokable on PATH across Win/macOS/Linux runners | CI matrix smoke test; fall back to `py -3` on Windows if `python` missing | Hook commands need a PATH-resolution shim; document in INSTALL.md |

If V1, V3, V4, V5 don't pass on Day 1, the 4-harness scope is the wrong target and a re-scope conversation (see deep-research report.md "Recommended re-scope") happens *before* Phase 1.

---

## 16. Hook Heuristic Rules (new in v4.1 — closes SPEC-review pre-action #10)

`detect-artifact-candidate` triggers from PostToolUse on Write. Without filters, every markdown-table Write fires the hook and the user gets a `<system-reminder>` storm (SPEC-review T4). Rules MUST be implemented in `core/cli.py detect-artifact-candidate`:

1. **Numeric-or-status column requirement.** Skip unless the table has ≥ 2 numeric columns OR a column whose header matches `^(status|state|result|pass|fail|score|count|%|cost|p\d{2,3})$` (case-insensitive). Plain task lists do not fire.
2. **Path-prefix skiplist.** Skip if `${TOOL_OUTPUT}` path matches `*.md` *and* is under `docs/`, `CHANGELOG`, `README*`, or `.github/` — these are user-authored docs, not requested renders.
3. **Self-recursion guard.** Skip if `${TOOL_OUTPUT}` path is under any `artifact_dir(harness)` (per §3.2) — prevents the hook re-firing on artifacts it just wrote.
4. **Suppression window.** Skip if the prior suggestion fired < 30 seconds ago (per-session). State stored in `${persist_dir}/.suggest-cooldown`.
5. **Suggestion never auto-renders.** The hook only emits a `<system-reminder>`-style note with a paste-ready command (`paperboard render --input ${TOOL_OUTPUT}`). Auto-render is explicitly out of scope for v0.1.0 (avoids "magic" mis-fires).

Phase 4 success test must include: in a fresh session, write 5 unrelated markdown tables (task lists, comparison without numbers, status dashboard, README excerpt, render-output) — only the status dashboard fires the hook.

---

## 17. Starter Attribution Schema (new in v4.1 — closes SPEC-review pre-action #5)

Every `designs/starters/<name>-inspired.DESIGN.md` MUST carry a YAML frontmatter `attribution:` block. The block travels with the file when it lands in `~/.claude/plugins/data/.../`, ensuring trademark + license posture follows the artifact.

Required schema:

```yaml
---
attribution:
  inspired_by: "Stripi"                              # the brand name (hyphenated form preserved)
  not_affiliated_with: "Stripe Inc."                 # explicit non-affiliation
  source_repo: "VoltAgent/awesome-design-md"
  source_path: "design-md/stripe/DESIGN.md"
  source_commit: "abc123def4567"                     # full SHA at the time of import
  source_license: "MIT"
  redistributed_under: "Apache-2.0"                  # this project's license
  imported_at: "2026-05-21"
  notes: |
    Tokens reverse-engineered from public brand impressions; not a verbatim copy.
    No trademark license claimed.
---
```

The lint rule `tests/test_starter_attribution.py` MUST fail if any file in `designs/starters/` lacks the required keys. Public release is blocked on this test passing.

**Brand-name hyphenation note:** "Stripi-inspired" / "Lin-ear-inspired" are *not* a trademark-evasion tactic; they are explicit signals that these are interpretations, paired with the `not_affiliated_with` field. Final decision on whether to ship any brand-derivative starter requires counsel review before v0.1.0 public push (deep-research stage 7 H-tier finding).

---

## 18. Open Carry-Forward (manual follow-ups owed before public push)

- USPTO TESS search on "paperboard" and "atv" in IC 009/042. Stage 6 couldn't reach the JS-heavy UI; manual lookup, ~10 minutes.
- Confirm publishing GitHub org is not `All-The-Vibes` (collision on repo name `ATV-PaperBoard`).
- Counsel sign-off on brand-derivative starters per §17.

---

*~4700 words. SPEC v4.2 — re-scoped to v0.1.0-preview (2 native adapters + 1 recipe); OpenCode deferred to v0.1.1; Phase 7a real-world test pass documented; V2 export format corrected empirically. v0.1.0-preview shipped 2026-05-15 (single-session execution; 93 tests passing). v0.1.1 roadmap: OpenCode adapter, USPTO TESS clearance, public release.*
