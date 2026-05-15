---
stage: 5
title: GitHub Copilot integration constraints - SPEC v4 section 2.4 verification
date: 2026-05-14
sources_fetched: 8
status: complete
---

# Stage 5 - GitHub Copilot Integration Constraints

Verifying five specific claims in SPEC v4 section 2.4 against current docs.
Research basis: Track 3 (harness-github-copilot-plugin-model-2026-05-14.md), VS Code API docs fetch, GitHub Copilot custom-instructions docs fetch.

---

## Claim 1: "Copilot has NO local plugin model for filesystem/browser access - Extensions are remote HTTPS only"

[FINDING] PARTIALLY CORRECT, but significantly understated.

The claim is accurate for the Copilot Extensions surface (Agents and Skillsets), but it misses multiple local-actionable surfaces that DO exist:

**Copilot Extensions (Agents/Skillsets): CONFIRMED remote HTTPS only.**
An Agent extension is a developer-hosted HTTPS service with no access to the local filesystem.
The GitHub App manifest lives in GitHub App settings UI, not in a repo file.
Skillsets are similarly remote - declarative HTTPS endpoints that GitHub platform calls as tools.

**VS Code Chat Participant / Language Model Tools API: NOT remote.**
This is a VS Code extension running in the extension host with full access to:
- vscode.workspace.fs (filesystem write)
- vscode.env.openExternal (browser open)
- child_process (subprocess invocation)
This IS a genuine local plugin model and is the correct surface for writing HTML to disk and opening in browser.

**Copilot Coding Agent (cloud):** Headless GitHub Actions environment - local to the runner, not the user machine. Has filesystem access in the runner context.

**Copilot CLI plugins:** Installable packages with agents, skills, hooks. Local to the user CLI environment.

The SPEC section 2.4 statement "No native plugin path" is accurate ONLY if scoped to Copilot Extensions (Agents/Skillsets). The VS Code Chat Participant API IS a local plugin path with the exact capabilities atv-paperboard needs. Track 3 (section 5 capability matrix) confirms: VS Code surface can write via vscode.workspace.fs and auto-open browser tab via vscode.env.openExternal. Track 3 conclusion: "for a plugin whose job is write an HTML file to disk and open it in a browser, Copilot Extensions and Skillsets are the wrong surface - the local-actionable surfaces are (a) a VS Code extension and (b) the Coding Agent shell-hooks."

[EVIDENCE]
- Track 3 research: obsidian-vault/raw/research/harness-github-copilot-plugin-model-2026-05-14.md section 5
- VS Code Chat Participant API: https://code.visualstudio.com/api/extension-guides/chat
- VS Code Language Model Tools: https://code.visualstudio.com/api/extension-guides/tools

[CONFIDENCE] HIGH
Track 3 is cross-source verified. The primary Copilot Extensions docs pages (building-copilot-extensions/*) returned 404 in this stage, but the capability matrix is anchored to VS Code API docs which are accessible.

SPEC IMPACT: Section 2.4 opening sentence needs clarification.
Change: "No native plugin path."
To: "No native plugin path analogous to Claude Code plugin.json or Codex SKILL.md for the Copilot Extensions surface."
The VS Code Chat Participant path was correctly deferred to v0.2 in section 7, but the section 2.4 rationale is incomplete.

---

## Claim 2: ".github/copilot-instructions.md is the canonical custom-instructions file"

[FINDING] CORRECT, with important addendum on size limits and alternatives.

Confirmed:
- .github/copilot-instructions.md at repo root is the canonical repository-wide custom instructions file.
- No frontmatter required for this file (unlike path-specific instruction files).
- Path-specific variant: .github/instructions/NAME.instructions.md requires YAML frontmatter with applyTo glob and optional excludeAgent.
- Additional files recognized by Copilot: AGENTS.md, CLAUDE.md, GEMINI.md in repo root.
- Precedence (highest to lowest): personal -> path-specific repo -> repo-wide -> agent files -> org instructions.

Size/character limits:
- Copilot code review: reads only the FIRST 4,000 CHARACTERS of .github/copilot-instructions.md.
- Copilot Chat / Coding Agent: no documented character cap found.
- SPEC template is ~300 chars - well within the 4,000-char code-review limit.

[EVIDENCE]
- https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
- Track 3 research section 2c: "4,000-char cap on code review; Chat/cloud agent have no such cap"

[CONFIDENCE] HIGH - Confirmed from two independent fetches (current stage + Track 3).

SPEC IMPACT: None blocking. INSTALL.md for the copilot adapter should note the 4,000-char code-review limit so users know not to bloat the instructions file.

---

## Claim 3: "GitHub Actions hook is the correct integration point for Copilot Coding Agent"

[FINDING] CORRECT.

The Copilot Coding Agent runs in an ephemeral GitHub Actions-powered environment. GitHub docs describe it as "its own ephemeral development environment, powered by GitHub Actions." The workflow.yml pattern in SPEC section 2.4 (triggered on pull_request, paths: paperboard-artifacts/**) is architecturally sound.

The Coding Agent has explicit hooks (shell commands at lifecycle points) as a documented customization surface. MCP servers are also supported in the Coding Agent environment.

Trigger analysis: The SPEC workflow uses on: pull_request: paths: [paperboard-artifacts/**]. This fires when those paths change in a PR. The Coding Agent itself opens PRs; the workflow validates artifacts in those PRs. This is the correct pattern for deterministic artifact validation.

[EVIDENCE]
- Track 3 research section 2f: "Coding Agent runs in ephemeral GitHub-Actions-powered environment; hooks: shell commands at lifecycle points"
- Track 3 section 4: "GITHUB_ACTIONS=true confirmed as standard Actions env var"

[CONFIDENCE] HIGH - Multiple consistent sources.

SPEC IMPACT: None. The GitHub Actions integration pattern is correct.

---

## Claim 4: VS Code Chat Participant API deferral to v0.2 - defensible?

[FINDING] DEFERRAL IS DEFENSIBLE, but the stated rationale is weak.

SPEC section 7 states: "Copilot VS Code Chat Participant extension (the in-IDE chat path; complex, low marginal value over the instructions+CLI pattern). Defer to v0.2."

Complexity assessment: CONFIRMED.
A VS Code Chat Participant requires: VSIX packaging, package.json contributes.chatParticipants declaration, runtime vscode.chat.createChatParticipant() call, VS Code Marketplace publication, and separate user install. This is materially higher-effort than a CLI + instructions file.

"Low marginal value" assessment: WEAK FRAMING.
The VS Code Chat Participant IS the only path that can DETERMINISTICALLY open a browser tab from within VS Code Copilot interactions. The instructions+CLI pattern is best-effort - the model must "remember" to invoke the CLI. The Participant pattern enforces it. That is non-trivial marginal value.

However, marginal value is context-dependent: for CLI-oriented users the instructions+CLI pattern suffices; for VS Code Chat UI users, the extension is significantly better.

Verdict: Deferral is defensible for v0.1.0 on COMPLEXITY grounds. The "low marginal value" framing is incorrect. The real reason to defer is packaging overhead, not value.

[EVIDENCE]
- VS Code Chat Participant API: https://code.visualstudio.com/api/extension-guides/chat
- Track 3 section 7: "VS Code extension (chat-participant + tool)" listed as the CORRECT architecture for the IDE surface

[CONFIDENCE] HIGH on architectural analysis; MEDIUM on marginal-value counter-claim (context-dependent).

SPEC IMPACT: Deferral survives but rationale needs update.
Change: "low marginal value over the instructions+CLI pattern"
To: "deferred due to VSIX packaging complexity; this is the correct primary path for VS Code IDE users and should be v0.2 priority."

---

## Claim 5: Detection signals GITHUB_ACTIONS=true and VSCODE_PID

[FINDING] GITHUB_ACTIONS=true: CORRECT. VSCODE_PID: PLAUSIBLE but undocumented contract.

GITHUB_ACTIONS=true:
Confirmed. GitHub Actions sets GITHUB_ACTIONS=true as a documented standard environment variable in all Actions runners. Reliable and stable signal for the Coding Agent path.

VSCODE_PID:
Plausible but NOT confirmed from primary VS Code documentation (the VS Code environment docs page returned 404 in this stage). The variable is widely observed in practice - VS Code sets VSCODE_PID to the PID of the main VS Code process in terminals it spawns - but it is NOT a documented API contract. It is an implementation detail that could change between VS Code versions or be absent in some configurations (remote SSH, Codespaces, web editor).

More stable supplementary signals for VS Code detection:
- TERM_PROGRAM=vscode (set in VS Code integrated terminal, more standard)
- VSCODE_INJECTION (set in VS Code integrated terminal)

[EVIDENCE]
- Track 3 research section 4: "GITHUB_ACTIONS=true confirmed; VSCODE_PID flagged as partially unverified"
- GitHub Actions documented standard env vars (GITHUB_ACTIONS is explicitly listed)

[CONFIDENCE] HIGH for GITHUB_ACTIONS=true; MEDIUM for VSCODE_PID (works in practice, not a stable documented API).

SPEC IMPACT: Two changes recommended:
1. Add TERM_PROGRAM=vscode as supplementary signal in core/detect.py alongside VSCODE_PID.
2. Add to section 8 open questions: "VSCODE_PID is an undocumented VS Code implementation detail. TERM_PROGRAM=vscode is the more standard signal. Verify both in Phase 0."

---

## Summary Table

| SPEC 2.4 Claim | Verdict | Impact Level |
|----------------|---------|--------------|
| Extensions are remote HTTPS only | PARTIALLY CORRECT (true for Agents/Skillsets; VS Code Chat Participant is local) | Minor - clarify language |
| .github/copilot-instructions.md is canonical | CORRECT | None blocking |
| GitHub Actions is correct Coding Agent hook | CORRECT | None |
| VS Code Chat Participant deferral defensible | DEFENSIBLE (complexity valid; low-value framing weak) | Minor - update rationale |
| GITHUB_ACTIONS=true signal | CORRECT | None |
| VSCODE_PID signal | PLAUSIBLE, not documented | Minor - add fallback signal |

---

## Recommended SPEC v4 Patches (all minor, none blocking Phase 0)

1. Section 2.4 opening: Narrow "No native plugin path" to "No native plugin path analogous to Claude Code plugin.json or Codex SKILL.md"

2. Section 7: Change "complex, low marginal value over the instructions+CLI pattern" to "deferred due to VSIX packaging complexity; this is the correct primary path for VS Code IDE users and should be v0.2 priority"

3. core/detect.py: Add TERM_PROGRAM=vscode fallback alongside VSCODE_PID check

4. Section 8: Add open question on VSCODE_PID vs TERM_PROGRAM=vscode stability

5. adapters/copilot/INSTALL.md: Note the 4,000-char code-review limit for copilot-instructions.md

---

[STAGE_COMPLETE:5]
