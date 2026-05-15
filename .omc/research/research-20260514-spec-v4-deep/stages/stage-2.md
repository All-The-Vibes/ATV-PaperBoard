# Stage 2 — Claude Code Adapter: SPEC v4 §2.1 Claim Verification

**Date:** 2026-05-14
**Research target:** SPEC.md §2.1 (Claude Code adapter) — all Claude-Code-specific claims
**Sources:** `code.claude.com/docs/en/plugins`, `code.claude.com/docs/en/plugins-reference`, `code.claude.com/docs/en/hooks`, `code.claude.com/docs/en/discover-plugins`
**Fetch budget used:** 6 fetches (2 redirect + 4 content)

---

## Finding 1 — Plugin Manifest: Required Fields

**SPEC claim:** "Per Track 1: only `name` is *required*; other fields are optional."

[FINDING] CONFIRMED with important nuance.

[EVIDENCE]
From `plugins-reference` §Required fields:
> "If you include a manifest, `name` is the only required field."

Additional nuance from same page:
> "The manifest is optional. If omitted, Claude Code auto-discovers components in default locations and derives the plugin name from the directory name."

So `.claude-plugin/plugin.json` is itself **optional** — Claude Code works without it via directory-name auto-discovery. When present, `name` is the only required field.

SPEC manifest includes `version`, `description`, `license`, `homepage` — all confirmed optional.

[CONFIDENCE] HIGH — directly stated in official docs.

---

## Finding 2 — Hook Event Count: 29 events, 5 types

**SPEC claim:** "29 hook events, 5 hook types"

[FINDING] CONFIRMED — exactly 29 unique events, 5 types.

[EVIDENCE]
The `plugins-reference` hook table lists 29 unique events:

1. SessionStart 2. Setup 3. UserPromptSubmit 4. UserPromptExpansion 5. PreToolUse
6. PermissionRequest 7. PermissionDenied 8. PostToolUse 9. PostToolUseFailure
10. PostToolBatch 11. Notification 12. SubagentStart 13. SubagentStop 14. TaskCreated
15. TaskCompleted 16. Stop 17. StopFailure 18. TeammateIdle 19. InstructionsLoaded
20. ConfigChange 21. CwdChanged 22. FileChanged 23. WorktreeCreate 24. WorktreeRemove
25. PreCompact 26. PostCompact 27. Elicitation 28. ElicitationResult 29. SessionEnd

Hook types confirmed as 5: `command`, `http`, `mcp_tool`, `prompt`, `agent`.

[CONFIDENCE] HIGH — counted directly from official table.

---

## Finding 3 — PostToolUse with matcher "Write"

**SPEC claim (hooks/hooks.json):**
```json
{
  "PostToolUse": [{
    "matcher": "Write",
    "hooks": [{ "type": "command", "command": "python ...", "timeout": 2000 }]
  }]
}
```

[FINDING] Write matcher CONFIRMED valid. STRUCTURAL BUG: hooks.json in SPEC is missing the outer "hooks" wrapper key.

[EVIDENCE]
Official plugin `hooks/hooks.json` canonical example from `plugins-reference`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "..." }]
      }
    ]
  }
}
```

From the hooks reference: `"matcher": "Edit|Write"` — Write is explicitly listed as matchable for PostToolUse. Single-tool matcher `"Write"` is valid regex.

The standalone `settings.json` hooks format does NOT use the `"hooks"` wrapper key.
The plugin `hooks/hooks.json` file DOES require the `"hooks"` wrapper — confirmed by every official plugin example and the migration guide.

SPEC shows PostToolUse at top level without wrapper. This would silently fail to register the hook at plugin load time.

[CONFIDENCE] HIGH for Write matcher; HIGH for structural bug (all official examples use wrapper).

**ACTION REQUIRED:** Add outer `"hooks": { ... }` wrapper to `adapters/claude-code/hooks/hooks.json`.

---

## Finding 4 — CLAUDE_PLUGIN_ROOT vs CLAUDE_PLUGIN_DATA Lifecycle

**SPEC claim:** "plugin root is ephemeral (cleaned after 7 days); CLAUDE_PLUGIN_DATA is the durable persistence path"

[FINDING] CONFIRMED with a precision correction.

[EVIDENCE]
From `plugins-reference` §Environment variables:

``: "This path changes when the plugin updates. The previous version's directory remains on disk for about **seven days** after an update before cleanup, but treat it as ephemeral and do not write state here."

``: "a persistent directory for plugin state that **survives updates**. Use this for installed dependencies such as node_modules or Python virtual environments, generated code, caches, and any other files that should persist across plugin versions."

Resolved path: `~/.claude/plugins/data/{id}/` where `{id}` has non-alphanumeric chars replaced by `-`.
Example: plugin `atv-paperboard@marketplace` resolves to `~/.claude/plugins/data/atv-paperboard-marketplace/`.

**Precision correction:** The 7-day ephemeral window applies to *old versions after a plugin update*, not the currently-running version. The current CLAUDE_PLUGIN_ROOT is always valid for the session lifetime. SPEC wording is directionally correct but could mislead.

CLAUDE_PLUGIN_DATA lifecycle: deleted only when plugin is uninstalled from all scopes. Not time-bounded. SPEC is correct here.

[CONFIDENCE] HIGH — both variable names, resolved paths, and lifecycle confirmed.

---

## Finding 5 — Subprocess Env Inheritance of CLAUDE_PLUGIN_DATA

**SPEC §8 Q1:** "CLAUDE_PLUGIN_DATA may not be visible to subprocesses from bin/ shims. Verify in Phase 0."

[FINDING] PARTIALLY RESOLVED — hook command subprocesses confirmed; bin/ shim subprocess inheritance not explicitly documented.

[EVIDENCE]
From `plugins-reference` §Environment variables:
> "All are also exported as environment variables to **hook processes** and MCP or LSP server subprocesses."

This confirms CLAUDE_PLUGIN_DATA IS available to `"type": "command"` hook subprocesses — which is the execution path SPEC §2.1 uses for `hooks/hooks.json`.

For `bin/` executables: docs only say they are "added to the Bash tool's PATH while the plugin is enabled" — no explicit statement about CLAUDE_PLUGIN_DATA inheritance from bin/ context.

**Resolution:** The hook command path used in §2.1 (`"type": "command", "command": "python /core/cli.py ..."`) IS confirmed to inherit CLAUDE_PLUGIN_DATA. Phase 0 empirical test remains warranted only if bin/ shims are used instead of/in addition to hook commands.

[CONFIDENCE] HIGH for hook command subprocesses; LOW for bin/ shim subprocesses.

---

## Finding 6 — Plugin Distribution Command Syntax

**SPEC claim:**
```
/plugin marketplace add <owner>/atv-paperboard
/plugin install atv-paperboard@<marketplace>
```

[FINDING] CONFIRMED — command syntax is correct.

[EVIDENCE]
From `discover-plugins`:
- Add marketplace (GitHub): `/plugin marketplace add anthropics/claude-code` (owner/repo format)
- Install plugin: `/plugin install github@claude-plugins-official` (name@marketplace format)

The two-step sequence (add marketplace first, then install) is the documented flow.
NOT `npx skills add` or any npm command. SPEC is correct.

Official Anthropic marketplace submission is via in-app forms (claude.ai or Console), not CLI commands.

[CONFIDENCE] HIGH — exact command syntax and flow confirmed.

---

## Finding 7 — Hook Timeout: Unit and Default

**SPEC claim:** `"timeout": 2000` (appears to intend "2 seconds")

[FINDING] **BUG IN SPEC** — timeout unit is SECONDS, not milliseconds.

[EVIDENCE]
From both the `hooks` reference and `plugins-reference`, default timeouts:

| Hook type | Default timeout |
|-----------|----------------|
| command, http, mcp_tool | **600 seconds** (10 min) |
| UserPromptSubmit (all types) | 30 seconds |
| prompt | 30 seconds |
| agent | 60 seconds |

The `timeout` field value is in **seconds**. No maximum cap is documented.

**Impact:** `"timeout": 2000` sets a ~33-minute timeout (almost certainly unintentional).
To set a 2-second timeout: `"timeout": 2`.
The default 600 seconds is acceptable for a short Python subprocess; remove the field to accept default.

[CONFIDENCE] HIGH — unit explicitly documented as seconds in multiple doc pages.

**CORRECTION REQUIRED:** Change `"timeout": 2000` to `"timeout": 2`, or remove the field entirely.

---

## Finding 8 — CLAUDE_CODE_REMOTE Environment Variable

**SPEC claim:** "check CLAUDE_CODE_REMOTE=true before calling webbrowser.open_new_tab. Remote sessions get a returned URL only."

[FINDING] CONFIRMED — variable is real, documented, and available in all hooks.

[EVIDENCE]
From `hooks` reference environment variables table:
> `CLAUDE_CODE_REMOTE` — value: `"true"` if running in web environment — Available in: **All hooks**

Official example:
```bash
if [ "" = "true" ]; then
  # Running in web environment — skip browser open
fi
```

Variable signals a "web environment" (Claude.ai / Console). Remote SSH without a local browser is a separate case — CLAUDE_CODE_REMOTE alone may not cover headless SSH. Combining with DISPLAY/no-display heuristics (as in SPEC §3.3) handles SSH/headless correctly.

[CONFIDENCE] HIGH — variable name, value `"true"`, and availability confirmed.

---

## Summary Table

| SPEC §2.1 Claim | Status | Action Required |
|---|---|---|
| `name` only required manifest field | ✅ CONFIRMED | None |
| Manifest location: `.claude-plugin/plugin.json` | ✅ CONFIRMED | None |
| 29 hook events | ✅ CONFIRMED (exact count) | None |
| 5 hook types | ✅ CONFIRMED | None |
| `PostToolUse` + `matcher: "Write"` valid | ✅ CONFIRMED | Fix outer `"hooks"` wrapper in hooks.json |
| CLAUDE_PLUGIN_ROOT ephemeral (7-day cleanup) | ✅ CONFIRMED | Clarify: only old versions; current always live |
| CLAUDE_PLUGIN_DATA durable at `~/.claude/plugins/data/{id}/` | ✅ CONFIRMED | None |
| Hook command subprocess inherits CLAUDE_PLUGIN_DATA | ✅ CONFIRMED | bin/ shim: empirical test Phase 0 |
| `/plugin marketplace add owner/repo` syntax | ✅ CONFIRMED | None |
| `/plugin install name@marketplace` syntax | ✅ CONFIRMED | None |
| `"timeout": 2000` (as ms) | ❌ BUG — unit is seconds | Change to `"timeout": 2` or remove |
| `CLAUDE_CODE_REMOTE=true` skip-browser signal | ✅ CONFIRMED | Add DISPLAY heuristic for SSH contexts |

---

## Required SPEC Corrections (Priority Order)

### P1 — Critical Bug
**`hooks/hooks.json` missing outer `"hooks"` wrapper key.**

SPEC shows:
```json
{ "PostToolUse": [{ "matcher": "Write", "hooks": [...] }] }
```

All official plugin hook examples use:
```json
{ "hooks": { "PostToolUse": [{ "matcher": "Write", "hooks": [...] }] } }
```

Without the wrapper key, the hook silently fails to register at plugin load time.

### P2 — High Bug
**`"timeout": 2000` sets a 33-minute timeout, not 2 seconds.**
Fix: change to `"timeout": 2` or remove the field entirely (600s default is fine for a subprocess).

### P3 — Low Wording
**"CLAUDE_PLUGIN_ROOT is ephemeral"** — the currently-installed version is valid for the full session. Only old versions (post-update) are cleaned after ~7 days. Recommended rephrase: "do not write persistent state to CLAUDE_PLUGIN_ROOT; it changes on plugin updates and old versions are cleaned up after ~7 days."

[STAGE_COMPLETE:2]