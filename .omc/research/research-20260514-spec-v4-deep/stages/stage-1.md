# Stage 1 — @google/design.md Package State Audit

**Mission:** Verify SPEC v4 ENFORCE-pillar claims about `@google/design.md@0.1.1`.
**Date:** 2026-05-14
**Stage:** 1 of N

---

## [FINDING 1] Package exists on npm; 0.1.1 IS the latest published version.

[EVIDENCE] npm registry metadata via https://registry.npmjs.org/@google/design.md :
- dist-tags.latest = 0.1.1
- versions = ["0.1.0", "0.1.1"]
- description = "Bridging design systems and code: a linter and exporter for the DESIGN.md format"
- Not deprecated.
- bin = { "design.md": "dist/index.js" }

[CONFIDENCE] HIGH. Direct registry fetch.

**SPEC alignment:** OK — SPEC pin to 0.1.1 is correct and currently latest. No 0.2 has shipped.

---

## [FINDING 2] License is Apache-2.0, NOT proprietary. SPEC v4 is WRONG.

[EVIDENCE]
- GitHub repo google-labs-code/design.md ships an Apache-2.0 LICENSE file at root (verified via https://raw.githubusercontent.com/google-labs-code/design.md/main/LICENSE — full Apache 2.0 text returned).
- README footer confirmed Apache-2.0 license.
- npm registry metadata returned no explicit license field at the top level. Monorepo root package.json is "private": true and lacks a license field — consistent with a Turborepo monorepo where the publishable package lives under packages/cli/.

[CONFIDENCE] HIGH on Apache-2.0 license existence. MEDIUM on whether the published tarball carries the LICENSE file (would need `npm pack` to verify).

**SPEC alignment:** DEFECT — SPEC §0 anchor line "@google/design.md@0.1.1 (alpha, proprietary)" and §9 T1 "proprietary" claim are inaccurate. The project is Apache-2.0 OSS. Replace "alpha, proprietary" with "alpha, Apache-2.0". Only legitimate residual concern is "alpha" (true: 0.1.x, two dot-releases).

---

## [FINDING 3] CLI subcommands: SPEC undercounts. Four exist, not two.

[EVIDENCE] README at https://github.com/google-labs-code/design.md :
- lint — validates DESIGN.md
- diff — compares two DESIGN.md files (token-level)
- export — converts tokens to other formats
- spec — outputs the DESIGN.md format specification

[CONFIDENCE] HIGH.

**SPEC alignment:** PARTIAL — SPEC §0.1 ENFORCE row names `lint --format json` (correct). SPEC §5 mentions `@google/design.md export` (correct). SPEC does not mention `diff` or `spec` subcommands; not load-bearing for v0.1.0, but the schema-drift guard (§Open Question 5) would benefit from invoking `spec` to capture the canonical spec version at integration-test time.

---

## [FINDING 4] --format values: SPEC claim partially incorrect.

[EVIDENCE] README documents these `export --format` values:
- json-tailwind (Tailwind v3 theme object)
- css-tailwind (Tailwind v4 @theme CSS)
- tailwind (alias for json-tailwind)
- dtcg (W3C Design Tokens Format Module)

For `lint`: `--format json` exists and JSON is the default. No other lint format.

[CONFIDENCE] HIGH on export formats; HIGH on lint defaulting to JSON.

**SPEC alignment:**
- OK — `lint --format json` works as SPEC §0.1 claims.
- OK — `css-tailwind` is real.
- DEFECT — SPEC §5 says tokens flow through `@google/design.md export` to generate "CSS variables consumed by Pico (cheap tier) or daisyUI (rich tier)." Pico CSS uses --pico-* custom-property names; daisyUI uses its own theme structure. Neither directly consumes a Tailwind v4 @theme block. paperboard will need a token-rename layer between css-tailwind output and Pico/daisyUI consumption, OR use `dtcg` and post-process. Phase 1 implementation risk SPEC currently glosses over.

---

## [FINDING 5] bin/dist/index.js invocation path is valid.

[EVIDENCE] npm registry shows bin = { "design.md": "dist/index.js" }. SPEC invocation `node <bin>/dist/index.js` is the documented entry point. The shebang-vs-Windows issue that breaks npx on Windows does not affect direct `node <path>` invocation.

[CONFIDENCE] HIGH.

**SPEC alignment:** OK — SPEC §0.1 and §3.4 (core/bridge.py caches resolved dist/index.js path) are correct.

---

## [FINDING 6] JSON output schema appears stable and parseable.

[EVIDENCE] README example output: top-level keys `findings[]` (severity, path, message) and `summary` (errors, warnings, info counters) form a minimal, stable contract. Easy to consume from core/validate.py fail-class taxonomy.

[CONFIDENCE] MEDIUM-HIGH. Schema is simple enough that minor-version drift risk is low, but absent a published JSON Schema we cannot guarantee field stability.

**SPEC alignment:** OK — SPEC reliance on JSON output is well-founded. §12 pins to 0.1.1 exact and §Open-Question 5 reserves a schema-drift integration test.

---

## [FINDING 7] No 0.2 release; no namespace move detected.

[EVIDENCE]
- Registry has only [0.1.0, 0.1.1].
- WebSearch for "@google-labs/design.md" returned no relevant results.
- GitHub repo is still google-labs-code/design.md.

[CONFIDENCE] HIGH for current state.

**SPEC alignment:** OK — Pin to 0.1.1 is safe as of 2026-05-14.

---

## [FINDING 8] Npx-on-Windows zero-byte stdout claim — UNVERIFIED but plausible.

[EVIDENCE]
- No public bug report for @google/design.md specifically (WebSearch zero hits).
- SPEC §0.3 claims this as a direct probe empirical result, not a citation.
- Well-known class of bug: npx-on-Windows shebang/ENOENT/stdout-buffering issues are documented for many npm CLIs (especially those with Unix-style shebangs and bun-built outputs — the monorepo uses `bun run packages/cli/src/index.ts`).
- dist/index.js is bundled output; if it contains a Unix-only shebang or stdout-handling assumption, npx-on-Windows breaking is plausible.

[CONFIDENCE] MEDIUM. Cannot independently reproduce without a Windows sandbox; defer to SPEC direct-probe evidence. Mitigation (`node <bin>/dist/index.js`) is robust regardless.

**SPEC alignment:** RECOMMENDATION — Preserve the direct-probe artifact (transcript or screenshot) in SPEC-review-2026-05-14.md or core/bridge.py docstring so the claim is auditable in v0.2 if Google fixes npx behavior.

---

## [FINDING 9] Monorepo structure has a downstream implication SPEC ignores.

[EVIDENCE] package.json at repo root shows:
- "private": true
- "cli": "bun run packages/cli/src/index.ts"
- Turbo monorepo with multiple packages/*.

The published npm package @google/design.md therefore corresponds to packages/cli/ (or similar), not the repo root. Anyone wanting to vendor source for offline CI (a plausible v0.2 hedge against alpha-package churn) needs to know this.

[CONFIDENCE] HIGH.

**SPEC alignment:** MINOR — Worth a one-liner in core/bridge.py docstring: "The published artifact corresponds to packages/cli/ in the monorepo, not the repo root."

---

## Summary of SPEC v4 corrections needed (Stage-1 verdict)

| SPEC location | Issue | Severity | Recommendation |
|---|---|---|---|
| §0 anchors, §9 T1 | License claim "proprietary" is wrong (it is Apache-2.0) | HIGH — public-release SPEC must not misstate upstream license | Replace "alpha, proprietary" with "alpha, Apache-2.0" |
| §5 Design Contract | Pico/daisyUI do not consume css-tailwind directly | MEDIUM | Note token-rename layer requirement; consider dtcg route |
| §0.3 empirical probe | npx-Windows bug claim has no public citation | LOW | Preserve probe transcript in SPEC-review or bridge.py |
| §0.1 / §5 | No mention of diff or spec subcommands | LOW | Use `spec` subcommand to capture canonical spec version for schema-drift test |
| §3.4 bridge.py docstring | Monorepo source layout undocumented | LOW | One-line clarification |

**Pin to 0.1.1 remains correct.** Package exists, bin path is what SPEC claims, JSON output is parseable, no namespace move has occurred. Principal SPEC defect uncovered in Stage 1 is the **license mischaracterization** — meaningful because v4 markets the toolkit as Apache-2.0 OSS; an OSS toolkit depending on what its own SPEC calls a "proprietary" upstream is a credibility risk that doesn't actually exist.

---

## Sources

- npm: @google/design.md registry metadata — https://registry.npmjs.org/@google/design.md
- GitHub: google-labs-code/design.md README — https://github.com/google-labs-code/design.md
- GitHub: google-labs-code/design.md LICENSE — https://raw.githubusercontent.com/google-labs-code/design.md/main/LICENSE
- GitHub: google-labs-code/design.md package.json (monorepo root) — https://raw.githubusercontent.com/google-labs-code/design.md/main/package.json
- GitHub: VoltAgent/awesome-design-md — https://github.com/VoltAgent/awesome-design-md

[STAGE_COMPLETE:1]