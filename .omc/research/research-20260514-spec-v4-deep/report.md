# Research Report — SPEC v4 Deep Verification

**Session:** `research-20260514-spec-v4-deep`
**Date:** 2026-05-14
**Status:** complete
**Verdict:** **NOT READY for Phase 0 as written.** Spec needs a v4.1 patch pass first. Estimate ≈ ½ day of doc work, no implementation.

---

## Executive Summary

Seven parallel research stages audited SPEC v4's load-bearing claims against current upstream documentation and registry state. Findings sort into three buckets:

1. **External reality is largely as claimed (stages 1, 6, partial 5).** The `@google/design.md` package exists at the pinned version, the JSON output shape is parseable, namespace availability for `atv-paperboard` is clean on PyPI + npm, and the Copilot integration architecture (instructions + Coding Agent) is sound.

2. **Every concrete code block in §2 has at least one runtime-fatal bug (stages 2, 3, 4).** Claude Code's `hooks/hooks.json` is missing the `"hooks"` wrapper key. Codex's TOML hook syntax is fabricated. OpenCode's TypeScript plugin example has 4 breaking errors and a 5th likely bug — it will not load. These were drafted from intuition, not docs.

3. **The architectural critique is severe (stage 7).** The 11-day, 4-harness estimate is unrealistic (re-est 17–22 days), SKILL.md "verbatim portability" is contradicted by the SPEC's own open questions, subprocess env inheritance is unverified across all 4 harnesses with no fallback, and the Copilot "adapter" is two template files dressed up as a 4th harness.

**Recommendation:** patch SPEC v4 → v4.1 to fix the concrete bugs and re-scope the schedule. Then proceed to Phase 0 with a re-scoped target: **v0.1.0-preview, 12 days, Claude Code + Codex only.** OpenCode → v0.1.1. Copilot reframed as `recipes/github-actions/` not an adapter.

---

## Methodology

### Stages

| Stage | Focus | Tier | Status |
|---|---|---|---|
| 1 | `@google/design.md` package state | HIGH (opus) | ✅ complete |
| 2 | Claude Code plugin model | MEDIUM (sonnet) | ✅ complete |
| 3 | Codex CLI skill/hook model | MEDIUM (sonnet) | ✅ complete |
| 4 | OpenCode plugin loader | MEDIUM (sonnet) | ✅ complete |
| 5 | GitHub Copilot constraints | MEDIUM (sonnet) | ✅ complete |
| 6 | Namespace availability | LOW (haiku) | ✅ complete |
| 7 | Architectural critique | HIGH (critic/opus) | ✅ complete |

All stages fired in parallel; aggregate wall-clock ≈ 20 minutes.

---

## Findings — by severity

### 🔴 CRITICAL (must fix before Phase 0)

#### C1. OpenCode plugin loader (§2.3) — will not run
Stage 4 found **4 breaking defects** in the 14-line TypeScript example:
- Import path `@opencode/plugin` is 404 on npm. Real package: `@opencode-ai/plugin@1.14.51`.
- Export name must be `server` (per `Plugin` type contract), not `paperboardPlugin`.
- Function must be `async` and return `hooks` directly, not `{ hooks }`.
- `ctx.pluginDir` does not exist on `PluginInput`. Use `import.meta.dirname`.
- `opencode.json` key is `"plugin"` (singular), not `"plugins"`.
- Hook handler signature is `(input, output)` — SPEC reads `input.output` which is `undefined`.

**Remediation:** rewrite §2.3 TypeScript block verbatim from `opencode.ai/docs/plugins`. ~30 minutes.

#### C2. Claude Code hooks (§2.1) — silently fails to register
Stage 2 found the `hooks/hooks.json` example is missing the outer `"hooks"` wrapper key required by the plugin format (distinct from `settings.json` which doesn't use the wrapper). Additionally, `"timeout": 2000` reads as **33 minutes** because the unit is seconds, not milliseconds.

**Remediation:** wrap the object; change `2000` → `2` (or remove, default 600s is fine). ~5 minutes.

#### C3. Codex hooks (§2.2) — fabricated TOML syntax
Stage 3 found `[hooks.PostToolUse]` with `match.tool = "Write"` is not the documented schema. Real syntax is array-of-tables `[[hooks.PostToolUse]]` with `matcher = "^Write$"` (regex string) and nested `[[hooks.PostToolUse.hooks]]` blocks. Additionally, `agents/openai.yaml`'s `allowed_tools` field doesn't exist in the documented schema (`interface.*`, `policy.*`, `dependencies.tools` instead).

**Remediation:** rewrite §2.2 TOML and YAML blocks against `codex` repo docs. ~30 minutes.

#### C4. 11-day, 4-harness budget unrealistic
Stage 7's re-estimate: **17–22 days** for the SPEC-as-written, driven by:
- C1–C3 above demonstrate the per-harness adapter complexity is not "~50 LOC of glue."
- Subprocess env inheritance must be tested empirically on **each** harness (Phase 0 budgets 1 day for all 4).
- The "shared SKILL.md ports verbatim" claim is hand-waved in §4 but already contradicted by §8 Q2 (`allowed_tools` vs `allowed-tools` hyphen divergence) and now by C1's discovery that frontmatter fields are silently ignored in OpenCode but enforced elsewhere.
- Phase 6 day-2 ("gallery", "compound pillar") is hand-waved at 1 day — it's a self-hosting compiler problem.

**Remediation:** re-cut scope. See §"Recommended re-scope" below.

### 🟠 HIGH (must address before public release; can be Phase-0 commits)

#### H1. License mischaracterization (§0 lineage notes)
Stage 1 found `@google/design.md` is **Apache-2.0**, not "proprietary" as SPEC claims. Public-release docs cannot misstate upstream license.

**Remediation:** change "alpha, proprietary" → "alpha, Apache-2.0." 1 line.

#### H2. Hook false-positive filters from v3-review never landed
SPEC review pre-action #10 demanded 4 specific filter rules (numeric column requirement, `*.md` path skip, `~/.claude/` path skip, suppression window). SPEC v4 says "tightened per-adapter" with zero concrete rules. Stage 7 confirms.

**Remediation:** add §17 "Hook detection heuristic" with the 4 filters as bullets. ~15 minutes.

#### H3. Per-file starter attribution schema undefined
SPEC §9 T3 says "per-file frontmatter" but never defines the schema. Phase 3 (1 day) cannot be unambiguously executed.

**Remediation:** add §18 "Starter attribution schema" — concrete YAML block (upstream-path, commit-SHA, not-affiliated-with-X notice). ~10 minutes.

#### H4. Auto-detect filesystem-heuristic mis-fires
Stage 7 surfaced two concrete failure modes for `detect_harness()`:
- F2: user has OpenCode installed *and* `OPENCODE_CONFIG_DIR` exported (e.g., dotfiles) but currently running inside Codex → detected as OpenCode.
- F4: VS Code integrated terminal running standalone (no Copilot) → detected as `copilot-ide`.

Stage 3 also notes `CODEX_HOME` env var should be checked before falling back to filesystem.

**Remediation:** add an explicit precedence order with negative checks (e.g., "OpenCode only if `OPENCODE_CONFIG_DIR` *and* no `CLAUDE_PLUGIN_ROOT`/`CODEX_HOME`"), plus document the "wrong detection → wrong persist path" failure mode. ~20 minutes.

#### H5. Pico/daisyUI export-target mismatch
Stage 1: `@google/design.md export` produces `json-tailwind` / `css-tailwind` / `tailwind` / `dtcg` formats. None of those are what Pico or daisyUI consume natively. SPEC §5 hand-waves "CSS variables consumed by Pico (cheap tier) or daisyUI (rich tier)" — a token-rename layer is needed.

**Remediation:** either acknowledge the rename layer as part of Phase 1 (and budget accordingly), or simplify v0.1.0 to one tier with one concrete consumer.

#### H6. npm `paperboard` is taken
Stage 6: `paperboard` is published by Majid Sajadi (bookmark CLI, v0.0.2). PyPI `paperboard` is free.

**Remediation:** SPEC §8 Q6 already specified the fallback (`atv-paperboard` for both PyPI and npm). Make it the default in v4.1, drop the "if taken" conditional. 1 line.

#### H7. GitHub repo collision
Stage 6: `All-The-Vibes/ATV-PaperBoard` exists. Not the user's org (presumably).

**Remediation:** confirm publishing org and add a note in §0 if it's a different org. Worth a 30-second check before push.

### 🟡 MEDIUM (Phase 0–1 hardening)

- **M1.** SPEC's Codex 5-tier precedence is actually 6-tier (§8 Q3 off-by-one).
- **M2.** `core/detect.py` should add `TERM_PROGRAM=vscode` alongside `VSCODE_PID` for a documented IDE signal.
- **M3.** Hooks shell out to `python core/cli.py` — Windows users without `python` on PATH (only `py`) hit a TypeError. Stage 7 flagged. Either ship `pipx`-style entry point or detect on first run.
- **M4.** Regenerator retry sequence per SPEC §6 phase 2 is "same → switch tier → fall back to paperboard." Original v3-review rejected step-1 = "same." It's back. Drop step 1 or differentiate it.
- **M5.** Bridge cache (`~/.atv-paperboard/config.json`) lacks a `schema_version` field; future SPEC bumps will need to invalidate it. Add the field now.

### 🟢 LOW

- **L1.** SPEC under-counts `@google/design.md` CLI subcommands — `diff` and `spec` also exist. `spec` is a free schema-drift guard for the integration test (§3 carryover).
- **L2.** "Copilot has NO local plugin model" overstated — VS Code Chat Participant API *is* a local plugin path with FS + browser access. Deferring to v0.2 is correct, but the reason is VSIX packaging complexity, not low marginal value.
- **L3.** SPEC §0.3 "npx zero-byte stdout on Windows" claim has no public citation. Mitigation (`node <bin>/dist/index.js`) is robust either way, but preserve the probe transcript for auditability.

---

## Cross-Validation

Where stages overlapped, findings were consistent:

- **Stage 1 + Stage 7** agree on H5 (token export mismatch is not just a typo, it's a real Phase 1 risk).
- **Stage 4 + Stage 7** agree the OpenCode adapter is the most fragile of the four — Stage 4 found the runtime bugs, Stage 7 surfaced the architectural reason (no CI lane for TS, no shared test infra).
- **Stage 6 + Stage 7** agree on the brand-name hyphen tactic (stripi/lin-ear) — Stage 7 says "needs counsel, not hyphens"; Stage 6 doesn't have a legal POV but confirms the names are not taken on package registries.
- **Stage 2 + Stage 3** independently arrived at "every concrete code block in §2 has at least one bug." Strong signal that §2 was written from memory rather than docs.

No contradictions between stages.

---

## Open from this research (manual follow-up owed)

- **USPTO TESS** for "paperboard" and "atv" in IC 009/042 — Stage 6 couldn't reach the JS-heavy UI. Manual check, ~10 minutes.
- **Confirm publishing GitHub org** is not `All-The-Vibes` (Stage 6 H7).
- **Phase 0 empirical test** — subprocess env inheritance across all 4 harnesses (Stage 7 C1 / Stage 2 partial confirmation). This is in-codebase work, not research.

---

## Recommended re-scope (v0.1.0-preview)

Adopting Stage 7's recommendation, lightly amended:

| Item | v4 spec | v4.1 recommendation |
|---|---|---|
| Harness count v0.1.0 | 4 (Claude Code, Codex, OpenCode, Copilot) | **2** (Claude Code + Codex) |
| OpenCode | v0.1.0 §2.3 | Defer to **v0.1.1** (1-week patch release after v0.1.0 ships) |
| Copilot | v0.1.0 §2.4 as "4th harness" | Reframe as **`recipes/github-actions/`** in v0.1.0; not an adapter |
| Schedule | 11 days, 4 harnesses | **12 days, 2 harnesses + recipe** |
| Public/private | Public v0.1.0 | **v0.1.0-preview** (private/limited); public v0.1.0 after v0.1.1 covers OpenCode |

Rationale: the cross-harness *architecture* (shared core + thin adapter) is sound. The shared-core *cost amortization* is what's overstated. Shipping 2 harnesses cleanly proves the architecture; shipping 4 with C1–C3 unresolved ships bugs publicly under the ATV name.

---

## Phase-0 readiness checklist (revised)

Before scaffolding starts:

- [ ] Apply v4 → v4.1 SPEC patches: C1, C2, C3, H1, H2, H3, H4, H5, H6, M1, M2, M4, M5 (≈ 2–3 hours)
- [ ] Decide on re-scope (v0.1.0-preview, 12 days, 2 harnesses) or defend the original
- [ ] Manual USPTO TESS check on "paperboard" + "atv" IC 009/042
- [ ] Confirm publishing GitHub org ≠ `All-The-Vibes`
- [ ] `git init` on `atv-paperboard/` (project root has no `.git`)
- [ ] Land `pyproject.toml` + `package.json` (with `@google/design.md@0.1.1` exact-pinned) + `package-lock.json` committed — closes v3-review action #7

If those are green, Phase 0 (`core/bridge.py`, `core/detect.py`, `designs/paperboard.DESIGN.md`, smoke test) is one honest day.

---

## Appendix — raw stage findings

- `stages/stage-1.md` — `@google/design.md` package state (8.5 KB)
- `stages/stage-2.md` — Claude Code plugin model
- `stages/stage-3.md` — Codex CLI skill/hook model (10.8 KB)
- `stages/stage-4.md` — OpenCode plugin loader
- `stages/stage-5.md` — GitHub Copilot constraints (10.9 KB)
- `stages/stage-6.md` — Namespace availability
- `stages/stage-7.md` — Architectural critique (22.8 KB)

State: `state.json`
