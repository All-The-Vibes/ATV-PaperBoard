# Stage 3: Codex CLI Skill/Hook Model - SPEC v4 Section 2.2 Verification

**Date:** 2026-05-14
**Budget used:** 8 fetches
**Sources read:** SPEC.md section 2.2, existing Track 2 research note (obsidian-vault), 6 live developer docs pages

---

## Research Questions and Findings

---

### Q1: Is ~/.agents/skills/NAME/SKILL.md the canonical skill location?

[FINDING] **CONFIRMED WITH NUANCE.**

The canonical user-scoped install path is `~/.agents/skills/<name>/SKILL.md`. However, Codex uses a **6-tier precedence** (not 5-tier as SPEC section 8 Q3 recalls from Track 2), and user-scoped is Tier 4:

| Tier | Path | Scope |
|------|------|-------|
| 1 | `$CWD/.agents/skills` | CWD (closest) |
| 2 | `$CWD/../.agents/skills` | Parent folders (ascending) |
| 3 | `$REPO_ROOT/.agents/skills` | Repo root |
| 4 | `$HOME/.agents/skills` | User (global) |
| 5 | `/etc/codex/skills` | Admin |
| 6 | Built-in | Bundled by OpenAI |

Closest wins: a repo-local `.agents/skills/atv-paperboard/` would shadow the user-scoped install.

The "open-agent-skills standard" term appears in OpenAI docs branding but the GitHub `docs/skills.md` stub merely redirects to the developers portal. There is **no external independent spec document** -- the standard is OpenAI's own `developers.openai.com/codex/skills` page. SPEC framing overstates it slightly; it is an OpenAI-proprietary convention, not a cross-vendor open standard.

[EVIDENCE]
- https://developers.openai.com/codex/skills (fetched 2026-05-14 -- confirms layout, precedence, frontmatter)
- https://github.com/openai/codex/blob/main/docs/skills.md (fetched -- stub only, redirects to portal)

[CONFIDENCE] HIGH for path and precedence. MEDIUM for "open-agent-skills standard" naming (OpenAI-specific, not cross-vendor).

---

### Q2: Do Codex hooks share Claude Code hook names (PostToolUse, PreToolUse, Stop)?

[FINDING] **CONFIRMED.** The six documented Codex hook event names are:

- `SessionStart`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `UserPromptSubmit`
- `Stop`

These exactly match Claude Code hook names. The SPEC claim is correct.

**HOWEVER: The TOML syntax shown in SPEC section 2.2 is WRONG.**

SPEC section 2.2 writes:
```toml
[hooks.PostToolUse]
match.tool = "Write"
command = "python ..."
```

The **actual documented syntax** uses array-of-tables with a `matcher` regex field:
```toml
[[hooks.PostToolUse]]
matcher = "^Write$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "/usr/bin/python3 path/to/hook.py"
timeout = 30
statusMessage = "Reviewing file write"
```

Two bugs in SPEC section 2.2:
1. `match.tool` should be `matcher` (regex pattern string, not a dotted key)
2. `[hooks.PostToolUse]` (single table) should be `[[hooks.PostToolUse]]` (array of tables)

**Additional finding:** Plugin-bundled hooks receive `PLUGIN_ROOT` and `PLUGIN_DATA` env vars, plus `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility. This partially undercuts the SPEC claim that "Codex has no documented CODEX_PLUGIN_DATA analogue" -- there IS a `PLUGIN_DATA` for plugin-scoped hooks. However, atv-paperboard skills are installed via git clone, not as a formal Codex plugin, so this env var does not apply unless we also ship a Codex plugin manifest.

[EVIDENCE]
- https://developers.openai.com/codex/config-advanced (fetched -- TOML syntax with matcher field)
- https://developers.openai.com/codex/hooks (fetched -- event names, JSON schema, plugin hook env vars)
- https://developers.openai.com/codex/config-reference (fetched -- hooks section, features.hooks flag)

[CONFIDENCE] HIGH for hook names. HIGH for TOML syntax bugs. MEDIUM for PLUGIN_DATA scope (plugin vs skill distinction needs implementation-time verification).

---

### Q3: Is there a stable CODEX_* env var to detect runtime?

[FINDING] **CONFIRMED -- NO STABLE DETECTION ENV VAR (with nuance).**

The only documented CODEX_* variable is `CODEX_HOME` (defaults to `~/.codex`). There is no `CODEX_SESSION_ID`, `CODEX_RUN_ID`, or similar injection into skill subprocess environments. SPEC claim that detection must fall back to filesystem heuristics is **correct**.

However, `CODEX_HOME` IS a documented variable -- users can set it to relocate the Codex home directory. Its presence is therefore a usable (if soft) detection signal. The current SPEC `detect.py` does not check `CODEX_HOME` at all.

Recommended detection order (improved from SPEC):
1. `CODEX_HOME` env var presence (documented; user-settable; reliable soft signal)
2. `~/.codex/config.toml` existence (filesystem heuristic; current SPEC approach)
3. Parent process named `codex` (requires psutil; most reliable but heavier)

[EVIDENCE]
- https://developers.openai.com/codex/config-advanced (`CODEX_HOME` documented as default path for local state)
- https://developers.openai.com/codex/config-reference (no other CODEX_* vars found)

[CONFIDENCE] HIGH.

---

### Q4: 5-tier skill precedence -- authoritative source, correct install scope?

[FINDING] **6 tiers, not 5. User-scoped install is the correct default.**

SPEC section 8 Q3 and the Track 2 research note both recall "5-tier precedence." The live developers.openai.com/codex/skills page lists **6 tiers**, apparently because Track 2 collapsed CWD-level and ascending-parents into one entry.

For atv-paperboard, user-scoped (`~/.agents/skills/atv-paperboard/`) remains the correct default -- it applies across all repos without per-project setup. Tier count discrepancy (5 vs 6) has no practical impact on the install strategy.

[EVIDENCE]
- https://developers.openai.com/codex/skills (6-tier table, fetched directly)

[CONFIDENCE] HIGH.

---

### Q5: AGENTS.md template fallback -- is this a real Codex pattern?

[FINDING] **CONFIRMED.** `AGENTS.md` is Codex's documented primary instruction layer (analogous to `CLAUDE.md`).

- Global: `~/.codex/AGENTS.md` (or `~/.codex/AGENTS.override.md`)
- Project: `AGENTS.md` or `AGENTS.override.md` in any directory from Git root to cwd
- Custom fallback names configurable via `project_doc_fallback_filenames` in config.toml (e.g., `TEAM_GUIDE.md`, `.agents.md`)
- Max size: `project_doc_max_bytes` (default 32 KiB)
- Closer files override farther files (concatenated with blank lines)

SPEC `adapters/codex/AGENTS.md.template` fallback pattern is entirely correct. The template correctly targets `~/.codex/AGENTS.md` (global) or `<repo>/AGENTS.md` (project).

[EVIDENCE]
- https://developers.openai.com/codex/guides/agents-md (fetched -- precedence, file names, config knobs)

[CONFIDENCE] HIGH.

---

### Q6: allowed_tools frontmatter field -- does Codex use this?

[FINDING] **SPEC allowed_tools FIELD IS IN THE WRONG FILE (and possibly wrong format).**

SPEC section 2.2 shows `agents/openai.yaml` with `allowed_tools: [Bash, Read, Write]`. This field does **not appear** in the documented `agents/openai.yaml` schema. The actual documented top-level fields are:

```yaml
interface:
  display_name: ...
  short_description: ...
  icon_small: ...
  icon_large: ...
  brand_color: ...
  default_prompt: ...

policy:
  allow_implicit_invocation: true/false

dependencies:
  tools:
    - type: "mcp"
      value: "toolName"
      description: ...
      transport: ...
      url: ...
```

Tool access in Codex is governed by `config.toml` `[permissions]` blocks and sandbox policy, not by skill-level frontmatter. The `dependencies.tools` field in `openai.yaml` is for declaring MCP tool dependencies only.

SPEC section 8 Q2 asks about `allowed_tools` vs `allowed-tools` (hyphen) difference between Codex and Claude Code. That question is **moot** for `agents/openai.yaml` -- Codex simply does not use this field in openai.yaml. If `SKILL.md` frontmatter carries `allowed_tools`, it is likely a Claude Code convention that Codex silently ignores (consistent with the "Claude-compatible" portability claim).

[EVIDENCE]
- https://developers.openai.com/codex/skills (agents/openai.yaml schema, fetched directly)

[CONFIDENCE] HIGH that `allowed_tools` is absent from documented openai.yaml schema. MEDIUM on whether SKILL.md frontmatter allowed_tools is silently ignored vs unsupported in Codex.

---

## Summary Table: SPEC Section 2.2 Claims vs Live Docs

| Claim | Status | Severity |
|---|---|---|
| Skill location `~/.agents/skills/<name>/SKILL.md` | CORRECT | -- |
| "open-agent-skills standard" (cross-vendor framing) | OVERSTATED | Low -- rename to "OpenAI Agent Skills standard" |
| Hooks share Claude Code names | CORRECT | -- |
| TOML hook syntax `match.tool` field | BUG | P0 -- wrong field name |
| `[hooks.PostToolUse]` single table | BUG | P0 -- must be array-of-tables `[[...]]` |
| No stable CODEX_* env var | CORRECT | -- |
| Fall back to config.toml existence | CORRECT | -- |
| detect.py missing CODEX_HOME check | GAP | P1 -- add as Tier 1 detection signal |
| No CODEX_PLUGIN_DATA analogue | PARTIAL | P2 -- PLUGIN_DATA exists for plugin-bundled hooks |
| `agents/openai.yaml` `allowed_tools` field | INCORRECT | P0 -- field undocumented; remove or replace |
| AGENTS.md fallback pattern | CORRECT | -- |
| User-scoped install as default | CORRECT | -- |
| 5-tier precedence | MINOR ERROR | Low -- actually 6 tiers; no functional impact |

---

## Actionable Issues for SPEC v4 (Priority Order)

### P0 -- Must Fix Before Implementation

**Issue 1: TOML hook syntax (section 2.2)**

Replace:
```toml
[hooks.PostToolUse]
match.tool = "Write"
command = "python ${HOME}/.agents/skills/atv-paperboard/core/cli.py detect-artifact-candidate"
```

With:
```toml
[[hooks.PostToolUse]]
matcher = "^Write$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "python ${HOME}/.agents/skills/atv-paperboard/core/cli.py detect-artifact-candidate"
timeout = 30
```

**Issue 2: agents/openai.yaml schema (section 2.2)**

Remove `allowed_tools: [Bash, Read, Write]`. Replace entire file content with documented fields:
```yaml
interface:
  display_name: "atv-paperboard"
  brand_color: "#3B82F6"
  short_description: "Cross-harness HTML artifact toolkit."
policy:
  allow_implicit_invocation: true
```

### P1 -- Should Fix

**Issue 3: detect.py CODEX_HOME check**

Add before the config.toml filesystem heuristic:
```python
if "CODEX_HOME" in os.environ:
    return "codex"
```

**Issue 4: "open-agent-skills standard" prose**

Update to: "OpenAI Agent Skills standard (developers.openai.com/codex/skills)".

**Issue 5: Section 8 Q3 tier count**

Update "5-tier" to "6-tier" in the open question note.

### P2 -- Investigate at Implementation Time

**Issue 6: PLUGIN_DATA for formal Codex plugins**

If atv-paperboard later ships a formal Codex plugin manifest (beyond git-clone skill), `PLUGIN_DATA` becomes available and `persist.py` could use it instead of `~/.codex/atv-paperboard-artifacts/`. Defer; current scope uses git-clone install.

---

[STAGE_COMPLETE:3]