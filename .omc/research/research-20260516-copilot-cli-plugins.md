# Research note — Copilot CLI plugins as a third harness

Date: 2026-05-16
Status: research-only, no code changes
Trigger: user shared https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins

## TL;DR

GitHub Copilot **CLI** (the interactive `copilot` terminal agent, distinct from the
Copilot **Coding Agent** we already target in `recipes/github-actions/`) ships a
first-class plugin system whose on-disk layout is **near-identical** to what
atv-paperboard already produces for the Claude Code adapter and the open-agent-skills
shape called out in SPEC.md Track 2. Adding a Copilot CLI adapter is a low-lift
addition — primarily a new `adapters/copilot-cli/` directory plus one paragraph in
SPEC.md §3 listing the harness.

## Sources

- Plugins overview — https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins
- Custom agents — https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents
- Enterprise plugin standards — https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-enterprise-plugin-standards
- Config dir reference — https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference
- CLI command reference — https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference

## Plugin layout (what Copilot CLI expects)

A plugin is a directory containing any subset of:

| Component | Path inside plugin | Notes |
|-----------|--------------------|-------|
| Custom agents | `agents/<name>.agent.md` | YAML frontmatter: `name?`, `description` (req), `prompt` (req), `tools?`, `mcp-servers?` |
| Skills | `skills/<name>/SKILL.md` | Same shape Claude Code / open-agent-skills uses |
| Hooks | `hooks.json` (root) or `hooks/` | Event handlers; specific event names not documented on the overview page |
| MCP servers | `.mcp.json` (root) or `.github/mcp.json` | Standard MCP config |
| LSP servers | `lsp.json` (root) or `.github/lsp.json` | Out of scope for paperboard |

No dedicated `plugin.json` manifest is documented — presence of these well-known
files **is** the manifest.

## On-disk install locations

User-level config dir is `~/.copilot/` (override via `COPILOT_HOME`):

- `~/.copilot/installed-plugins/` — plugin install root, managed via `copilot plugin` commands
- `~/.copilot/agents/` — user-level custom agents
- `~/.copilot/skills/` — user-level skills
- `~/.copilot/mcp-config.json` — user-level MCP servers
- `~/.copilot/hooks/` — user-level hook scripts
- `~/.copilot/settings.json` — primary settings (JSONC)

Settings cascade: **local > repo > user**, CLI flags highest. Repo settings live at
`.github/copilot/settings.json`; uncommitted overrides at
`.github/copilot/settings.local.json`.

## Install / management commands

Interactive (inside `copilot`):

- `/plugin marketplace` — manage marketplaces (default marketplaces include `copilot-plugins` and `awesome-copilot`)
- `/plugin install`
- `/plugin uninstall`
- `/plugin update`
- `/plugin list`

CLI flag:

- `copilot --plugin-dir=DIRECTORY` (repeatable) — load plugins from a local directory without installing

MCP-specific (interactive `/mcp` or `copilot mcp ...`): `add | remove | get | list | edit | enable | disable | auth | reload`. `--json` output supported.

## How this maps to atv-paperboard today

Existing atv-paperboard layout we already ship:

```
skills/
  render-artifact/SKILL.md
  regenerate-artifact/SKILL.md
agents/
  artifact-reviewer.md             # not yet .agent.md
adapters/
  claude-code/agents/artifact-reviewer.md
```

What Copilot CLI would need to consume those:

1. **Skills** — `skills/render-artifact/SKILL.md` and `skills/regenerate-artifact/SKILL.md` already match Copilot's expected shape (open-agent-skills standard). Drop-in.
2. **Agent** — Copilot wants `agents/<name>.agent.md`. Our file is `agents/artifact-reviewer.md`. Either rename or ship a Copilot-specific copy at `adapters/copilot-cli/agents/artifact-reviewer.agent.md` with frontmatter:
   ```yaml
   ---
   name: artifact-reviewer
   description: Reviews rendered paperboard artifacts for design-contract compliance.
   tools: [bash]   # only needs to run `paperboard validate`
   ---
   ```
   Body = the existing `## Purpose / ## Trigger / ## Steps / ## Output format` prose.
3. **Hooks** — Optional. A `PostToolUse` hook (or whatever Copilot's analogue is — needs deeper docs lookup) could auto-invoke `paperboard render` after a file write matching the trigger patterns from `copilot-instructions.md.template`. Defer until event names are confirmed.
4. **MCP** — Not needed for v0.1. `paperboard` is a CLI; agents call it via the `bash` tool. An MCP server could come later if we want richer typed integration.

## Proposed adapter scope (v0.1, not committed yet)

```
adapters/copilot-cli/
  README.md                         # install via /plugin install <repo> or --plugin-dir
  agents/
    artifact-reviewer.agent.md      # Copilot frontmatter shape
  skills/
    render-artifact/SKILL.md        # symlink or copy of skills/render-artifact/SKILL.md
    regenerate-artifact/SKILL.md    # symlink or copy
  hooks.json                        # OPTIONAL — only if event names check out
```

SPEC.md §3 ("Harness targets") would gain a row:

| Harness | Location | Install |
|---------|----------|---------|
| Copilot CLI | `~/.copilot/installed-plugins/atv-paperboard/` | `/plugin install <org>/atv-paperboard` or `copilot --plugin-dir=$(pwd)/adapters/copilot-cli` |

## Open questions before implementing

1. **Skill discoverability** — does Copilot auto-discover skills from a plugin's `skills/` dir, or must agents declare `tools: [skill:render-artifact]`? Custom-agents page implies `tools` defaults to all-available, suggesting auto-discovery, but worth confirming with a real install. *(hooks question resolved — see "Hook schema" section below)*
2. **Persistence path under Copilot harness** — paperboard.core.harness needs a `copilot` branch. Likely candidate: `~/.copilot/plugin-data/atv-paperboard/artifacts/`. Compare with existing branches:
   - `claude-code` → `${CLAUDE_PLUGIN_DATA}` or `.claude/paperboard-artifacts/`
   - `codex` → `~/.codex/atv-paperboard-artifacts/`
   - `copilot-coding-agent` → `paperboard-artifacts/` (repo-relative)
3. **Naming clash** — `paperboard-artifacts/` (repo-relative for Coding Agent) vs. `~/.copilot/plugin-data/atv-paperboard/` (user-scoped for CLI). Two different Copilot products, two different defaults. Worth a SPEC.md disambiguation paragraph.
4. **Marketplace publishing** — the default `copilot-plugins` / `awesome-copilot` marketplaces are GitHub repos; publishing likely means a PR adding atv-paperboard's repo URL. Defer to v0.2.0.

## Recommendation (updated)

Hook schema is now fully resolved (see section below). The adapter is no longer
blocked on documentation — only on whether we want to ship it now. Remaining
mechanical work:

- ~40 lines: `paperboard/hooks/copilot_post_tool_use.py`
- ~10 lines: `adapters/copilot-cli/hooks.json`
- ~15 lines: `adapters/copilot-cli/agents/artifact-reviewer.agent.md` (frontmatter + body rewrite)
- 2 symlinks/copies for the two skills
- ~20-line `core/harness.py` branch for `copilot-cli`
- SPEC.md §3 row + INSTALL.md paragraph

Estimated effort: ~90 min end-to-end. No changes to `core/render.py` or
`core/validate.py` required.

---

## Hook schema (resolved 2026-05-16)

Sources:
- https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks
- https://docs.github.com/en/copilot/reference/hooks-reference

### Event names (7 total)

`sessionStart`, `sessionEnd`, `userPromptSubmitted`, `preToolUse`, `postToolUse`,
`errorOccurred`, `agentStop`. Both camelCase and PascalCase variants are accepted;
PascalCase (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`) is closer to
Claude Code's hook family.

### hooks.json shape

```json
{
  "version": 1,
  "hooks": {
    "postToolUse": [
      {
        "type": "command",
        "matcher": "^(create|edit)$",
        "bash": "paperboard render --input \"$FILE\" --no-open",
        "powershell": "paperboard render --input $env:FILE --no-open",
        "cwd": ".",
        "timeoutSec": 30,
        "env": { "PAPERBOARD_HARNESS": "copilot-cli" }
      }
    ]
  }
}
```

`matcher` is a regex anchored as `^(?:pattern)$` against the tool name. Available
tool names: `ask_user`, `bash`, `create`, `edit`, `glob`, `grep`, `powershell`,
`task`, `view`, `web_fetch`.

### Hook input (stdin JSON)

| Event | Key fields (camelCase) |
|-------|-------------------------|
| `sessionStart` | `sessionId`, `timestamp`, `cwd`, `source` (`startup`/`resume`/`new`), `initialPrompt?` |
| `sessionEnd` | `sessionId`, `timestamp`, `cwd`, `reason` (`complete`/`error`/`abort`/`timeout`/`user_exit`) |
| `userPromptSubmitted` | `sessionId`, `timestamp`, `cwd`, `prompt` |
| `preToolUse` | `sessionId`, `timestamp`, `cwd`, `toolName`, `toolArgs` |
| `postToolUse` | `sessionId`, `timestamp`, `cwd`, `toolName`, `toolArgs`, `toolResult: { resultType, textResultForLlm }` |
| `errorOccurred` | `sessionId`, `timestamp`, `cwd`, `error: { message, name, stack? }`, `errorContext`, `recoverable` |
| `agentStop` | `sessionId`, `timestamp`, `cwd`, `transcriptPath`, `stopReason` |

### Exit codes — FAIL-OPEN

| Exit | Behavior |
|------|----------|
| `0` | Success. `stdout` parsed as JSON hook output if present. |
| `2` | `stderr` shown to user, execution continues. In `permissionRequest` context this is a **deny**; in `postToolUseFailure` it is additional context. |
| other non-zero | Logged as hook failure, execution **continues**. |

**This is the opposite of Claude Code's hook semantics.** Copilot CLI hooks
cannot hard-block a tool call except inside a permission flow. For paperboard,
this means a render failure inside a hook is recoverable (the user keeps
working) but **a hook cannot enforce the design contract**. Enforcement still
belongs in `paperboard validate` / CI.

### Output conventions

- `stdout` on exit 0 is parsed as structured JSON: supports `permissionDecision`
  (`allow`/`deny`/`ask`), `permissionDecisionReason`, `modifiedArgs`,
  `additionalContext` (injects text into the agent's next turn), `decision`,
  `behavior`.
- Plain non-JSON stdout is ignored, so hook scripts can `echo` freely during
  development.

### Locations

- Repo: `.github/hooks/<name>.json`
- User (Linux/macOS): `~/.copilot/hooks/` (or `$COPILOT_HOME/hooks/`)
- User (Windows): `%USERPROFILE%\.copilot\hooks\` (or `%COPILOT_HOME%\hooks\`)
- Plugin: `hooks.json` at plugin root, or `hooks/` subdirectory

## How this changes the adapter plan

Concrete `adapters/copilot-cli/hooks.json`:

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
        "timeoutSec": 30
      }
    ]
  }
}
```

A new `paperboard/hooks/copilot_post_tool_use.py`:

1. Reads stdin JSON.
2. Extracts the written file path from `toolArgs` (varies per tool — `create` and
   `edit` both carry a `file_path` field in practice; confirm during impl).
3. Runs the existing trigger-pattern matcher (the table in
   `recipes/github-actions/copilot-instructions.md.template` — status dashboards,
   comparison tables, ≥2-numeric-column data, etc.).
4. If it matches, shells out to `paperboard render --input <path> --no-open --tier atv`.
5. On success, prints
   `{"additionalContext": "Rendered <slug>.html at <path>. See paperboard-artifacts/."}`
   to stdout so the agent's next turn is aware of the new file.
6. On failure, exits non-zero — Copilot will log it and continue (fail-open).
