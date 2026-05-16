# SPEC Addendum — GitHub Copilot CLI plugin model

**Date:** 2026-05-16 · **Author:** research pass triggered by user-supplied docs links · **Target SPEC:** v4.2 (delivered as v0.1.0-preview)
**Status:** Documentation-only. No code changes shipped with this addendum.
**Source research note:** `.omc/research/research-20260516-copilot-cli-plugins.md` (260 lines, full payload schemas + adapter sketch)

---

## Verdict

**SPEC.md §0.3 line 66 is now factually incorrect.** It states:

> Copilot has NO local plugin model for filesystem/browser access — confirmed (Extensions = remote HTTPS only)

That claim was true for **GitHub Copilot Extensions** (the remote-HTTPS Copilot Apps surface that Track 3 of the v4 research evaluated). Since then GitHub has shipped a **separate, first-class local plugin model for the `copilot` CLI** — a terminal agent product that is distinct from both Copilot Extensions and the Copilot Coding Agent we already target in `recipes/github-actions/`.

This addendum documents the new surface so SPEC.md can be updated in a later pass and so a v0.1.1 / v0.2.0 adapter can be scoped accurately.

---

## 1. Three Copilot surfaces — disambiguation

The SPEC currently treats "Copilot" as one harness. There are now three meaningfully different surfaces, each with its own integration story:

| Surface | What it is | Plugin model | Currently addressed by atv-paperboard? |
|---|---|---|---|
| **Copilot Extensions** (Copilot Apps) | Remote HTTPS endpoints invoked from chat | No local plugins; no filesystem access | N/A — SPEC.md §0.3 correctly rules this out |
| **Copilot Coding Agent** | GitHub-hosted agent that runs in Actions / on PRs | Repo-level instructions + workflow YAML | ✅ `recipes/github-actions/copilot-instructions.md.template` |
| **Copilot CLI** | Interactive `copilot` terminal agent on the user's machine | ✅ **Full local plugin model** with agents, skills, hooks, MCP | ❌ Not yet — gap this addendum documents |

The third row is what's new. The SPEC's "no local plugin model" line conflated row 1 and row 3.

---

## 2. Copilot CLI plugin layout (authoritative)

Plugins are directories. The presence of well-known files **is** the manifest — there is no separate `plugin.json`. Any subset of the following is valid:

| Component | Path inside plugin | Frontmatter / shape |
|---|---|---|
| Custom agents | `agents/<name>.agent.md` | YAML: `name?`, `description` (req), `prompt` (req), `tools?`, `mcp-servers?` |
| Skills | `skills/<name>/SKILL.md` | Open-agent-skills standard — identical shape to Claude Code and Codex |
| Hooks | `hooks.json` (plugin root) or `hooks/` subdir | See §4 below |
| MCP servers | `.mcp.json` (root) or `.github/mcp.json` | Standard MCP config |
| LSP servers | `lsp.json` (root) or `.github/lsp.json` | Out of scope for paperboard |

User-level config dir is `~/.copilot/` (override via `COPILOT_HOME`):

- `~/.copilot/installed-plugins/` — plugin install root (managed via `copilot plugin` commands)
- `~/.copilot/agents/`, `~/.copilot/skills/`, `~/.copilot/hooks/` — user-level overrides
- `~/.copilot/mcp-config.json`, `~/.copilot/settings.json` (JSONC)
- `~/.copilot/plugin-data/<plugin>/` — persistent plugin data (the likely paperboard persistence path)

Settings cascade: **local > repo > user**, CLI flags highest. Repo settings live at `.github/copilot/settings.json`; uncommitted overrides at `.github/copilot/settings.local.json`.

---

## 3. Install / management commands

Interactive (inside `copilot`):

- `/plugin marketplace` — manage marketplaces (defaults: `copilot-plugins`, `awesome-copilot`)
- `/plugin install <repo-or-name>`
- `/plugin uninstall`, `/plugin update`, `/plugin list`

CLI flag (for unpacked local development — important for our adapter testing):

- `copilot --plugin-dir=DIRECTORY` (repeatable) — load a plugin from a local path without installing

MCP-specific: `/mcp add|remove|get|list|edit|enable|disable|auth|reload` or `copilot mcp ...` from a non-interactive shell. Both support `--json`.

---

## 4. Hook schema (the load-bearing detail)

Seven event names, accepted in both camelCase and PascalCase. PascalCase aligns with Claude Code / Codex CLI:

`sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `errorOccurred`, `agentStop`.

### `hooks.json` shape

```json
{
  "version": 1,
  "hooks": {
    "postToolUse": [
      {
        "type": "command",
        "matcher": "^(create|edit)$",
        "bash": "python -m paperboard.hooks.copilot_post_tool_use",
        "powershell": "python -m paperboard.hooks.copilot_post_tool_use",
        "timeoutSec": 30,
        "env": { "PAPERBOARD_HARNESS": "copilot-cli" }
      }
    ]
  }
}
```

`matcher` is a regex anchored as `^(?:pattern)$` against `toolName`. Available tool names: `ask_user`, `bash`, `create`, `edit`, `glob`, `grep`, `powershell`, `task`, `view`, `web_fetch`.

### Hook input (stdin JSON, camelCase variant)

| Event | Key fields |
|---|---|
| `sessionStart` | `sessionId`, `timestamp`, `cwd`, `source` (`startup`/`resume`/`new`), `initialPrompt?` |
| `sessionEnd` | `sessionId`, `timestamp`, `cwd`, `reason` (`complete`/`error`/`abort`/`timeout`/`user_exit`) |
| `userPromptSubmitted` | `sessionId`, `timestamp`, `cwd`, `prompt` |
| `preToolUse` | `sessionId`, `timestamp`, `cwd`, `toolName`, `toolArgs` |
| `postToolUse` | + `toolResult: { resultType, textResultForLlm }` |
| `errorOccurred` | + `error: { message, name, stack? }`, `errorContext`, `recoverable` |
| `agentStop` | + `transcriptPath`, `stopReason` |

### Exit codes — **FAIL-OPEN by default** (opposite of Claude Code)

| Exit | Behavior |
|---|---|
| `0` | Success. `stdout` parsed as JSON if present (decision-control fields below). |
| `2` | `stderr` shown to user; execution continues. In `permissionRequest` context = deny; in `postToolUseFailure` = additional context. |
| other non-zero | Logged as hook failure; execution **continues**. |

**Architectural implication for the Enforce pillar:** A Copilot CLI hook cannot hard-block a tool call outside a permission flow. This means a paperboard hook on Copilot CLI can auto-render and inject context, but **it cannot enforce design-contract compliance the way the Claude Code hooks can.** Enforcement stays in `paperboard validate` and CI (`recipes/github-actions/workflow.yml.template`).

### `stdout` JSON fields on exit 0

`permissionDecision` (`allow`/`deny`/`ask`), `permissionDecisionReason`, `modifiedArgs`, `additionalContext`, `decision`, `behavior`.

`additionalContext` is the analogue of Claude Code's `<system-reminder>` injection — text returned here is injected into the agent's next turn. This is the cleanest channel for `paperboard render` to tell the agent "I rendered your output to `<slug>.html`" without polluting the `bash` tool's output stream.

### Hook locations

- Plugin: `hooks.json` at plugin root, or `hooks/` subdir
- Repo: `.github/hooks/<name>.json`
- User (Linux/macOS): `~/.copilot/hooks/` (or `$COPILOT_HOME/hooks/`)
- User (Windows): `%USERPROFILE%\.copilot\hooks\` (or `%COPILOT_HOME%\hooks\`)

---

## 5. Proposed delta against SPEC v4.2

### 5.1 §0.3 row to correct

Replace:

> Copilot has NO local plugin model for filesystem/browser access | ❌ confirmed (Extensions = remote HTTPS only) | Track 3

With:

> Copilot **Extensions** has no local plugin model — ✅ still true (remote HTTPS only)
> Copilot **CLI** ships a full local plugin model (agents + skills + hooks + MCP) — ✅ verified 2026-05-16

### 5.2 §0.2 row to add

| Pattern | Harnesses | Mechanism |
|---|---|---|
| **Native plugin** | Claude Code, Codex CLI, **Copilot CLI** | Per-harness wrapper file; same SKILL.md payloads; same Python core via subprocess. |

### 5.3 §1 layout row to add (when adapter ships)

```
adapters/copilot-cli/
  README.md                            # install via /plugin install or --plugin-dir
  agents/
    artifact-reviewer.agent.md         # Copilot frontmatter shape
  skills/                              # symlink/copy of root skills/
    render-artifact/SKILL.md
    regenerate-artifact/SKILL.md
  hooks.json                           # postToolUse → auto-render
core/
  hooks/
    copilot_post_tool_use.py           # ~40 LOC stdin-JSON reader + render shellout
```

### 5.4 Persistence-path branch for `core/persist.py`

`core/persist.py` resolves persistence per harness. The new `copilot-cli` branch should resolve to:

```
${COPILOT_HOME:-$HOME/.copilot}/plugin-data/atv-paperboard/artifacts/
```

Detection (for `core/detect.py`): presence of `${COPILOT_HOME}` env var, or `~/.copilot/installed-plugins/atv-paperboard/`, or `COPILOT_*` parent env, or invocation from a `--plugin-dir` resolved path under `adapters/copilot-cli/`. Order matters — see SPEC §17 auto-detect heuristic.

### 5.5 Naming-clash note for §3

Two Copilot harnesses persist to different defaults — this needs an explicit disambiguation paragraph:

- **Copilot Coding Agent** (`recipes/github-actions/`) → `paperboard-artifacts/` (repo-relative; PR-attached)
- **Copilot CLI** (proposed adapter) → `~/.copilot/plugin-data/atv-paperboard/artifacts/` (user-scoped)

Same brand, different scopes, different defaults. The gallery (Compound pillar) needs to know which root to walk.

---

## 6. What's still open

1. **Skill auto-discovery** — does Copilot CLI auto-load skills from a plugin's `skills/` dir, or must each agent declare `tools: [skill:render-artifact]`? The custom-agents page implies `tools` defaults to all-available, so auto-discovery is likely, but this should be empirically verified by `copilot --plugin-dir=$(pwd)/adapters/copilot-cli` against a built artifact-reviewer agent before v0.1.1 ships.
2. **`toolArgs` shape for `create` / `edit` tools** — the addendum assumes both carry a `file_path` field. The hooks reference confirms `toolArgs` exists as a free-form object but doesn't enumerate per-tool keys. The first version of `copilot_post_tool_use.py` should defensively probe `toolArgs.get("file_path") or toolArgs.get("path") or toolArgs.get("filename")` and log the raw payload on miss.
3. **Marketplace publishing path** — defaults `copilot-plugins` and `awesome-copilot` are GitHub repos; publishing means a PR adding atv-paperboard's repo URL. Defer to v0.2.0 alongside the existing PyPI + Claude Code marketplace work in SPEC §10.

---

## 7. Estimated incremental effort

~90 min end-to-end, no changes to `core/render.py` or `core/validate.py`:

| Component | LOC | Notes |
|---|---|---|
| `core/hooks/copilot_post_tool_use.py` | ~40 | stdin JSON → trigger-pattern match → `paperboard render` shellout → `additionalContext` stdout |
| `adapters/copilot-cli/hooks.json` | ~10 | postToolUse with `^(create\|edit)$` matcher |
| `adapters/copilot-cli/agents/artifact-reviewer.agent.md` | ~15 + body | Frontmatter + existing reviewer prose |
| `adapters/copilot-cli/skills/*` | 2 symlinks | Reuse root `skills/` |
| `core/persist.py` `copilot-cli` branch | ~20 | Resolve to `~/.copilot/plugin-data/...` |
| `core/detect.py` `copilot-cli` branch | ~15 | Env-var + path heuristics |
| SPEC.md §0.2 / §0.3 / §1 / §3 edits | ~25 lines | See §5 of this addendum |
| `README.md` / `RELEASE.md` / `recipes/.../INSTALL.md` mentions | ~30 lines | User-facing install instructions |

Recommend landing this in **v0.1.1** alongside the OpenCode adapter that SPEC v4.2 already deferred. Both are "second native plugin batch" — one shared CHANGELOG entry, one release.

---

## Sources

- Copilot CLI plugins overview — <https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins>
- Custom agents — <https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents>
- Enterprise plugin standards — <https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-enterprise-plugin-standards>
- CLI config directory reference — <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference>
- CLI command reference — <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference>
- Use hooks (how-to) — <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>
- Hooks reference (payload schemas + exit codes) — <https://docs.github.com/en/copilot/reference/hooks-reference>

Working research note (longer, with implementation sketches): `.omc/research/research-20260516-copilot-cli-plugins.md`
