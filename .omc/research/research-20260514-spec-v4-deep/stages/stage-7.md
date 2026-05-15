# Stage 7 — Architectural Critique of SPEC v4 (independent adversarial pass)

**Reviewer:** independent v4 audit · **Date:** 2026-05-14 · **Target:** SPEC.md (v4, 4-harness)
**Reference:** SPEC-review-2026-05-14.md (v3 review)

## Executive verdict

v4 closes most v3-review threats on paper, but it does so by **moving cost from "harness work" into "shared core + adapters" without re-pricing the shared core**, and by **deferring at least three load-bearing unknowns into Phase 0-5** rather than resolving them at spec-time. The 11-day budget is not credible. The "4-harness" framing is also load-bearing marketing: by v4 own §2.4, Copilot is not a fourth harness in any meaningful adapter sense, and shipping it as one creates support-surface debt disproportionate to the two-template payload.

Top three blockers if v4 is the spec we cut from:
1. **C-1 (schedule):** 11 days for 4 adapters + shared core + public release polish is fiction (see §1 below). Honest re-estimate: 17-22 working days.
2. **C-2 (portability claim):** "SKILL.md ports verbatim" is asserted but only one frontmatter field divergence (allowed_tools vs allowed-tools) has been spot-checked. §8 Q2 effectively concedes a build-time normalization layer is needed, while §4 still says "ported verbatim." One of these statements is wrong.
3. **C-3 (env inheritance):** §8 Q1 admits subprocess env inheritance is unverified on **every** harness, and the persist pillar correctness on Claude Code depends on it. Phase 0 budgets 1 day to verify across 4 harnesses; if it fails on any one, that harness PERSIST pillar is broken and there is no fallback in v4.

---

## 1. The 11-day estimate is not defensible

[FINDING] v4 holds the same 11-day budget the v3 review re-estimated at 15-18 days for a *single* harness, by appealing to "shared-core pays for adapters almost for free" (§6 closing line). The appeal is structurally unsound. **CRITICAL.**

[EVIDENCE]
- v3-review Threat 2 priced single-harness v3 at 15-18 working days even after cutting daisy tier, dropping Apple, and going color-only on token-trace. None of those cuts were reversed in v4.
- v4 §6 maps 11 days as: Phase 0 (1d) + Phase 1 RENDER (2d) + Phase 2 ENFORCE (2d) + Phase 3 starters (1d) + Phase 4 Claude Code adapter (1d) + Phase 5 Codex + OpenCode adapters (1d) + Phase 6 Copilot + COMPOUND gallery (2d) + Phase 7 release polish (1d).
- Phase 4 (1 day) bundles core/persist.py (harness-aware paths for **all 4 harnesses**, including §8 Q1 unverified subprocess-env work) with the entire Claude Code adapter (plugin.json, hooks.json, agent, INSTALL.md, AND a real-session install test).
- Phase 5 (1 day) bundles **two adapters** including OpenCode TypeScript plugin loader (opencode.plugin.ts), the only non-declarative wrapper in the entire repo, plus shared-SKILL.md portability verification, plus real-session smoke tests in two fresh harnesses.
- Phase 6 (2 days) is "Copilot adapter + COMPOUND pillar." v3-review Threat 2 priced the gallery alone at "not one day; it is a self-hosting compiler problem."
- Phase 7 (1 day) bundles per-harness README sections, 4 screenshots, USPTO check, marketplace PR, PyPI publish, and a green test matrix across all 4 harnesses. Release rehearsal across 4 platforms in one day is not credible.

[CONCRETE RE-ESTIMATE]

| Phase | v4 budget | Honest estimate | Why |
|---|---|---|---|
| 0 - scaffold + cross-harness verify | 1d | 2-3d | §8 Q1 + §8 Q2 verification on 4 platforms; Windows npx already broken |
| 1 - RENDER core | 2d | 2d | OK |
| 2 - ENFORCE core | 2d | 2-3d | v3-review token-trace concern still applies |
| 3 - starters | 1d | 1-2d | Per-file attribution + lint-passing is real work |
| 4 - PERSIST + Claude Code adapter | 1d | 2-3d | Real-session install + first encounter with CLAUDE_PLUGIN_DATA propagation |
| 5 - Codex + OpenCode adapters | 1d | 3-4d | OpenCode TS plugin is bespoke; Codex hook registration is invasive; two real-session smoke tests |
| 6 - Copilot + gallery | 2d | 3-4d | Gallery self-design problem from v3-review carries forward unchanged |
| 7 - release polish | 1d | 2-3d | 4 install paths, 4 screenshots, USPTO + PyPI name check, marketplace PR rehearsal |
| **Total** | **11d** | **17-22d** | |

[CONFIDENCE] HIGH that 11d is wrong; MEDIUM on the exact upper bound. The shared-core *does* reduce duplication, but it does not eliminate per-harness verification, which is what dominates cost in cross-platform plugin work.

[REMEDIATION] Either (a) cut Copilot adapter and gallery from v0.1.0 and re-quote as 12-14d for 3 native harnesses, or (b) split v0.1.0 into a private preview at day-11 (Claude Code + Codex only) and a public v0.1.0 at day-18+ once OpenCode + Copilot are real.

---

## 2. "SKILL.md ports verbatim" is hand-waved

[FINDING] §4 says SKILL.md files are "authored once and copy-deployed" to 3 harnesses. §8 Q2 simultaneously admits at least one frontmatter field (allowed_tools vs allowed-tools) diverges between Claude Code and OpenCode and "must be verified and normalized at build time." Both cannot be true. **HIGH.**

[EVIDENCE - fields likely to diverge across Claude Code / Codex / OpenCode SKILL.md frontmatters]
- allowed-tools vs allowed_tools (hyphen vs underscore) - already flagged.
- tools whitelist semantics: Claude Code uses MCP-server-prefixed names (mcp__server__tool); Codex open-agent-skills may use bare names; OpenCode Plugin factory exposes tools via a different surface entirely (the TS plugin owns hook registration, so SKILL frontmatter is partly redundant).
- model field: Claude Code recognizes haiku/sonnet/opus; Codex maps to OpenAI model IDs; OpenCode is provider-agnostic. A "verbatim" model: opus line is either ignored or misinterpreted in 2 of 3.
- argument-hint (Claude Code commands convention) has no analogue in Codex skills.
- disable-model-invocation / auto-trigger semantics differ.
- Trigger phrase / description length budgets differ.
- File-path conventions inside the skill folder (SKILL.md casing, assets/, references/) may be enforced or ignored differently.

[CONFIDENCE] HIGH that at least 3 fields diverge; MEDIUM on which exact ones since v4 has not done the cross-harness frontmatter audit.

[REMEDIATION]
- Rewrite §4 to say "shared *content*, normalized frontmatter at build time" rather than "ported verbatim."
- Add build/skills_normalize.py to Phase 4 (it currently does not exist in §1 repo layout; §4 says copy-deploy with no transform step).
- Add a frontmatter-divergence audit to Phase 0 verification list.
- Move §8 Q2 out of "open questions reserved for implementation" - it is a spec-time decision determining whether skills/ is one folder or three.

---

## 3. Auto-detect (T6) is more fragile than v4 admits

[FINDING] The detection ladder in core/detect.py (§3.1) has realistic mis-detection cases v4 does not call out. **MEDIUM.**

[EVIDENCE - actual order in §3.1]
1. CLAUDE_PLUGIN_ROOT/CLAUDE_PLUGIN_DATA -> claude-code
2. GITHUB_ACTIONS=true -> copilot-coding-agent
3. OPENCODE_CONFIG_DIR -> opencode
4. ~/.codex/config.toml exists -> codex
5. VSCODE_PID -> copilot-ide
6. else -> standalone

Failure modes:
- **F1: Codex-in-VS-Code.** OK by ordering luck.
- **F2: OpenCode-installed-but-running-Codex.** User who once tried OpenCode and still has OPENCODE_CONFIG_DIR in shell rc, currently invoking Codex. Order returns opencode. **WRONG.** Persistence goes to wrong directory.
- **F3: GitHub Actions running Claude Code.** Claude env vars also set, but GITHUB_ACTIONS check would fire second. v4 has Claude first, so OK - but only by luck of ordering.
- **F4: standalone with VS Code open.** Power user runs paperboard from VS Code integrated terminal. VSCODE_PID is set; returns copilot-ide and pushes artifact to ./paperboard-artifacts/. **WRONG mode**, sensible path.

[CONFIDENCE] HIGH on F2 and F4 being real; LOW on how often.

[REMEDIATION]
- Replace FS-heuristic with active probe: check process tree ancestry (ppid chain) for codex. Filesystem existence != active session.
- Add PAPERBOARD_HARNESS env var that any adapter sets at activation; detection first check is explicit-opt-in.
- paperboard doctor must print the detected harness *and the reason* (which rule fired).

---

## 4. Subprocess env inheritance (§8 Q1) is a CRITICAL deferred risk

[FINDING] v4 §8 Q1 carries forward v3 issue that CLAUDE_PLUGIN_DATA may not be visible to subprocesses invoked from the bin/ shim. Phase 0 budget of "verify on each platform" within a single day is inadequate. **CRITICAL.**

[EVIDENCE]
- PERSIST pillar correctness on Claude Code depends on os.environ["CLAUDE_PLUGIN_DATA"] being present in the Python subprocess. v4 core/persist.py (§3.2) hard-KeyErrors if not - no fallback.
- v4 §3.2 has zero graceful degradation. If env inheritance fails, every emission on Claude Code crashes the hook.
- Phase 0 verify spans Claude Code, Codex, OpenCode, and Copilot Actions runner. Each requires real session to test, not unit tests. One day for four real-session investigations including discovery of *why* inheritance fails (if it does) and engineering a fallback is unrealistic.
- OpenCode ctx.pluginDir (§2.3) is passed at TS-plugin time and spawns subprocess with stdio: "inherit", detached: true - but OPENCODE_CONFIG_DIR is not explicitly forwarded; it is assumed inherited. If OpenCode strips env vars when spawning plugin children, persistence goes to wrong path silently.

[CONFIDENCE] HIGH that this is at least a 2-day investigation; MEDIUM on whether any harness actually fails.

[REMEDIATION]
- Add defensive path-resolution fallback in core/persist.py: if env var missing, read from a file the hook writes at activation (~/.atv-paperboard/last-harness-context.json).
- Promote §8 Q1 to a Phase 0 *blocker* with explicit "if this fails for harness X, that harness is deferred to v0.2" exit ramp.
- Re-budget Phase 0 to 2-3 days minimum.

---

## 5. The "4th harness" framing is dishonest

[FINDING] v4 §2.4 admits Copilot has no local plugin model. The "adapter" is two YAML/markdown templates the user must hand-place in their own repo. Calling this an *adapter* and treating it as 1/4 of the integration story creates support-surface debt disproportionate to its surface area. **HIGH.**

[EVIDENCE]
- adapters/copilot/ is exactly two template files + INSTALL.md.
- §2.4 detection-signal check returns copilot-coding-agent or copilot-ide, but neither code path does anything beyond setting a persistence directory and a remote-headless flag. No hook, no skill loader, no plugin manifest - by §0.2 own taxonomy this is the "Instructions + CLI" pattern, not "Native plugin."
- v4 promises in §6 Phase 7 "4 install paths, 4 screenshots" and in §0.3 lists Copilot as one of four empirically-verified harnesses. The screenshot for Copilot is going to be a screenshot of a .github/copilot-instructions.md file. That is not a plugin install.
- Support-surface debt: every issue against "Copilot adapter" will be a Copilot configuration issue (user repo, workflow permissions, PR settings) - none debuggable remotely. This dwarfs the value of two template files.
- COMPOUND pillar is structurally impossible for the Copilot-coding-agent path because each PR is ephemeral and there is no persistent gallery across PRs.

[CONFIDENCE] HIGH.

[REMEDIATION]
- Re-frame: "atv-paperboard supports 3 native harnesses (Claude Code, Codex, OpenCode) and ships a GitHub workflow recipe for repos that use Copilot. The recipe is opt-in and not framed as an adapter."
- Move adapters/copilot/ to recipes/github-actions/.
- Drop copilot-coding-agent and copilot-ide branches from detect.py for v0.1.0. Keep GITHUB_ACTIONS=true -> workspace-scoped path as generic CI fallback with no Copilot framing.
- Removes ~2 days from Phase 6 and removes a fake-4-harness claim.

---

## 6. Hook false-positive storm (T4 / pre-action #10) - unaddressed

[FINDING] §9 claims T4 hook false-positives are "tightened (Claude Code only; Codex/OpenCode have different matchers); same logic, applied per-adapter." This is a non-answer. **HIGH.**

[EVIDENCE]
- v3-review Threat 4 listed 4 concrete filters: (a) require numeric/status column, (b) suppress within N seconds, (c) skip *.md paths, (d) skip ~/.claude/ paths.
- v4 hooks.json (§2.1) registers matcher: "Write" with no path or content filter. core/cli.py detect-artifact-candidate is the only filtering site, but no spec exists for what it filters on - no module in §3, no test in §1 layout (test_core_detect.py is harness-detection).
- "Per-adapter" is empty: Codex hook (§2.2) uses match.tool = "Write" with same lack of filter; OpenCode TS (§2.3) checks if (input.tool === "Write") with same lack.
- Result: a system-reminder on every Write the agent does. v3-review prediction - "background noise the model learns to ignore" - applies verbatim.

[CONFIDENCE] HIGH.

[REMEDIATION]
- Add core/candidate.py with explicit heuristics: numeric column >=2 OR status/state/result column, plus suppression window keyed on ~/.atv-paperboard/last-suggestion.timestamp, plus path filters (*.md, ~/.claude/, CLAUDE_PLUGIN_DATA, .atv-paperboard/, paperboard-artifacts/).
- Add tests under tests/test_core_candidate.py with positive and negative fixtures.
- Make detection adaptive: configurable cooloff via ~/.atv-paperboard/config.json.

---

## 7. Schedule landmines in §8 open questions

[FINDING] Six unresolved questions in §8. By Karpathy rule #1 these are guesses that will surface as Phase-N surprises.

| Q# | Topic | Severity | Why |
|---|---|---|---|
| Q1 | bin/-subprocess env inheritance | CRITICAL | See §4. Blocks PERSIST pillar correctness. |
| Q2 | SKILL.md frontmatter divergence | CRITICAL | See §2. Determines whether skills/ is shared or per-adapter. |
| Q3 | Codex skill precedence (5-tier) | MEDIUM | Affects whether install instructions are correct day one. |
| Q4 | Copilot workflow trigger | MEDIUM | UX/safety; default plausible but unverified. |
| Q5 | @google/design.md 0.2 release | LOW | Carried forward; integration-test guard exists. |
| Q6 | paperboard CLI name collision | HIGH | If taken on PyPI or Brew, every README example, every adapter template, every INSTALL.md, every copilot-instructions.md.template references wrong name. 30-minute pre-Phase-0 check that v4 has not done. |

[REMEDIATION] Resolve Q1, Q2, Q6 before Phase 0 starts. Q1 by real-session probe. Q2 by writing build-time normalizer spec. Q6 by 5 minutes of registry searches.

---

## 8. Brand-trademark exposure - the hyphen tactic

[FINDING] v4 keeps "stripi-inspired", "lin-ear-inspired", "vercel-inspired" as starter names. The hyphenated misspellings (stripi for Stripe, lin-ear for Linear) look like a trademark-evasion tactic. Whether this *helps* legally is exactly the kind of question that requires actual legal review before a public release. **HIGH (legal-process risk), MEDIUM (technical).**

[EVIDENCE]
- Vercel is not misspelled - it is the real wordmark. Inconsistency signals an incomplete legal strategy.
- Deliberate misspelling of a trademark to evade infringement is a known and generally unsuccessful tactic in US trademark law. Courts apply the "likelihood of confusion" test (Polaroid factors); an obvious near-spelling is often treated as evidence of *intent to confuse*, not avoidance.
- v3-review Threat 3 - "interpretations-not-endorsements disclaimer is not a legal force-field" - applies identically to v4. Adding a hyphen does not change consumer-confusion analysis.
- Apple was correctly dropped. The same reasoning argues for caution on Stripe (v3-review specifically flagged "Stripe guards the wordmark and the purple gradient aggressively in payment-adjacent contexts").
- v4 §6 Phase 7 mentions "USPTO basic search on atv-paperboard + paperboard" - but says nothing about searching brand names used in starters.

[CONFIDENCE] HIGH that this needs a lawyer before public release; reviewer here is not one.

[REMEDIATION]
- Treat any release shipping a starter visually-evocative-of-a-real-brand as requiring counsel review. The hyphen tactic is not a substitute.
- Safer v0.1.0: rename starters to aesthetic descriptors: payments-clarity.DESIGN.md, flat-minimal.DESIGN.md, monochrome-developer.DESIGN.md. Lose zero design value; lose legal exposure.
- If keeping brand-evocative starters, add a Phase 7 line item: "Counsel review of starter names + visual evocation." Currently absent.
- Add top-level TRADEMARKS.md disclaiming affiliation and listing upstream attribution. README footer is insufficient because DESIGN.md files travel.

---

## 9. New v4-introduced risks not in v3-review

### N1 - core/cli.py as cross-platform Python entry point. MEDIUM.
[EVIDENCE] §2.1 hooks.json hard-codes "python ${CLAUDE_PLUGIN_ROOT}/core/cli.py". On Windows it is python.exe or py -3; on macOS Homebrew it is python3; in some Docker images neither resolves. v4 has zero PATH-resolution strategy and no shebang. v3 had this at smaller surface area; v4 multiplies across 4 hook registrations.
[REMEDIATION] Ship a paperboard console-script entrypoint via pip install (already in §6 Phase 7) and have every adapter hook call paperboard detect-artifact-candidate, not python core/cli.py.

### N2 - OpenCode TS plugin is the only non-declarative wrapper. MEDIUM.
[EVIDENCE] §2.3 opencode.plugin.ts is real TypeScript importing @opencode/plugin types and using node:child_process. The §12 test matrix is GitHub Actions Python; no TS toolchain mentioned. CI for the TS loader is undefined.
[REMEDIATION] Add to Phase 5: tsconfig.json, minimal TS build step, CI lane that typechecks opencode.plugin.ts against @opencode/plugin typings.

### N3 - core/bridge.py cache schema. LOW.
[EVIDENCE] §3.4 caches at ~/.atv-paperboard/config.json with no schema_version, no migration. Future bridge.py expecting different fields breaks silently.
[REMEDIATION] Add schema_version + "if mismatched, rebuild" path. Five lines of code.

### N4 - CLAUDE_PLUGIN_DATA lifetime contradicts PERSIST pillar. HIGH.
[EVIDENCE] §0.3 row 5: "plugin root cleaned after 7 days." §2.1: "Persistence: ${CLAUDE_PLUGIN_DATA}/<date>/...". If CLAUDE_PLUGIN_DATA is *also* cleaned at 7 days, COMPOUND pillar's compounding gallery is structurally broken - artifacts older than 7 days disappear. v4 text is ambiguous: §0.3 says "plugin root", not CLAUDE_PLUGIN_DATA, but spec does not explicitly say CLAUDE_PLUGIN_DATA survives marketplace reinstall / plugin upgrade / harness uninstall.
[REMEDIATION] Verify CLAUDE_PLUGIN_DATA lifetime in Phase 0. If ephemeral, PERSIST contract for Claude Code must mirror to ~/.atv-paperboard/artifacts/ and gallery must read from mirror.

### N5 - Adapter install does invasive hand-editing of user config. MEDIUM.
[EVIDENCE] §2.2 says "Optional: edit ~/.codex/config.toml". §2.3 says edit ~/.config/opencode/opencode.json. Hand-editing JSON/TOML is a 2026 anti-pattern; users expect idempotent CLI commands.
[REMEDIATION] Add paperboard install --harness codex / opencode commands doing the mutation idempotently with backup. Few hours; eliminates a class of install support issues.

---

## 10. v3-review threats NOT fully closed in v4 despite §9 claim

- **T2 - Token-trace too hard:** §9 says "Color-only - Same." OK, but §6 Phase 2 still budgets only 2 days for ENFORCE including HTML-side color-trace + regenerator 3-step retry. v3-review hand-wave applies identically.
- **T2 - Gallery self-DESIGN.md:** §9 says "Reuse paperboard.DESIGN.md - Same." Dodges v3-review issue: gallery components (iframe wrappers, search, meta-cards) are not present in paperboard.DESIGN.md components: block. Either gallery doesn't use these (impoverished) or it uses components not in the DESIGN.md (lint fails).
- **T4 - Hook false positives:** See §6.
- **T4 - Reviewer 3-retry dead-end:** §9 says "Differentiated retries via regenerator - Same." But §6 Phase 2 doesn't enumerate strategies; §3 doesn't either. The 3-step retry "same -> switch tier -> fall back" with "same" as step 1 is precisely what v3-review said does not help. First retry should already be different.

---

## 11. Severity-ranked remediation list (concrete, blocking before Phase 0)

| # | Severity | Action |
|---|---|---|
| 1 | CRITICAL | Re-estimate to 17-22d or cut Copilot+gallery from v0.1.0; do not ship with 11d on the cover page. |
| 2 | CRITICAL | Resolve §8 Q1 (subprocess env inheritance) via real-session probe; add fallback in core/persist.py. |
| 3 | CRITICAL | Resolve §8 Q2 (SKILL.md frontmatter divergence); add build/skills_normalize.py; rewrite §4 "verbatim" claim. |
| 4 | HIGH | Replace ~/.codex/config.toml FS-heuristic with process-ancestry check + opt-in PAPERBOARD_HARNESS env var. |
| 5 | HIGH | Move adapters/copilot/ to recipes/github-actions/; rename framing to 3-harness + GH Actions recipe. |
| 6 | HIGH | Add core/candidate.py with explicit hook filters (numeric/status column, path filters, suppression window). |
| 7 | HIGH | Resolve §8 Q6 (paperboard PyPI/Brew name availability) pre-Phase-0. |
| 8 | HIGH | Add TRADEMARKS.md + counsel review line item; rename brand-evocative starters to aesthetic-descriptive names. |
| 9 | HIGH | Verify CLAUDE_PLUGIN_DATA lifetime; if ephemeral, mirror to ~/.atv-paperboard/artifacts/ for COMPOUND. |
| 10 | MEDIUM | Hook adapters call paperboard <subcommand> console script, not python core/cli.py. |
| 11 | MEDIUM | Add paperboard install --harness <name> idempotent config mutation; stop hand-editing TOML/JSON in INSTALL.md. |
| 12 | MEDIUM | Add TS build/typecheck CI lane for opencode.plugin.ts. |
| 13 | MEDIUM | Enumerate concrete retry strategies in §3 / Phase 2 (must differ at retry-1, not retry-3). |
| 14 | LOW | Add schema_version to core/bridge.py ~/.atv-paperboard/config.json cache. |

---

## 12. Bottom line

v4 is a real improvement on v3 in *scope honesty about what each harness offers* (the §0.3 verification table is genuinely valuable) and in *architectural separation* (shared core + adapters is the right shape). It regresses on *schedule honesty* by absorbing the cost of three additional harnesses into the same 11-day budget the v3 reviewer already said was insufficient for one harness. The Copilot "adapter" is a marketing artifact, not a fourth harness. The SKILL.md "verbatim portability" claim contradicts the spec's own open question. And the subprocess-env-inheritance unknown is load-bearing for the PERSIST pillar on every harness.

Recommended path forward: re-cut as **v0.1.0-preview** at 12 days covering Claude Code + Codex only (the two harnesses with the most mature plugin contracts), close the §11 CRITICALs in Phase 0, then add OpenCode in v0.1.1 and ship the Copilot recipe as a recipes/ entry rather than an adapter.

[STAGE_COMPLETE:7]