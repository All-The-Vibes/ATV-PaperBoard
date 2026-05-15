# Adversarial Review of SPEC v2 - atv-paperboard

**Reviewer:** adversarial pass | **Date:** 2026-05-14 | **Document:** SPEC.md (577 lines)

## Verdict

**Ship-blocking issues present.** The SPEC has at least three load-bearing assumptions that have not been empirically verified: (a) that @google/design.md exists on npm under that exact name with a lint/export CLI surface, (b) that awesome-design-md actually contains DESIGN.md files (not just a brand index), and (c) that the narrowed DESIGN.md round-trip will pass the same lint it was generated from. Any one of these failing voids the 9-day plan.


---

## Threat 1: External dependency risk

**Severity: critical.**

The entire ENFORCE pillar (S0 line 23, S5.2 lines 294-328) is delegated to @google/design.md, a package whose own docs are explicitly marked **alpha**. The SPEC acknowledges this only at S11 #2 (line 546) and dismisses it with "pin the version via npx @google/design.md@<pinned>." That is not adequate mitigation.

**Failure scenarios:**

1. **Rule semantics drift, not just version numbers.** npx @google/design.md@0.x pins the binary but not the rule set's *meaning*. If Google adds a new mandatory section (e.g., `accessibility:`) in 0.3 -> 0.4, every paperboard.DESIGN.md (S3.1, lines 133-221) and every starter (S3.3) will start failing lint the day a user runs npx without a lockfile. The SPEC has no lockfile, no package.json, no offline cache strategy.

2. **npx resolves over the network by default.** S8.3 lines 442-445 shell out to npx with no --prefer-offline, no --no-install guard. Offline users see ENFORCE fail with a cryptic npm ERR! 404 indistinguishable from a real lint failure. render-artifact (S5.1 step 1, line 283) *rejects* the artifact if lint fails, and design-md-bridge.py returns {"error": r.stderr} with no error-class taxonomy.

3. **Package rename / scope move.** @google/design.md lives in Google Labs, which has documented history of renaming/archiving repos. If the package becomes @google-labs/design.md or is deprecated entirely, every skill, every test fixture, and the plugin.json dependencies.external block (S2 lines 111-120) silently rot. The literal string "npx @google/design.md" appears in S2, S3, S5.2, S8.3, S9 Phase 0.

4. **Node/npx prerequisite is hand-waved.** S8 line 462 calls out stdlib-only Python except design-md-bridge.py which shells out to npx. But Claude Code users are not guaranteed to have Node installed. plugin.json (S2) hopes a dependencies.external field exists; S2 line 124 already admits it may not. The only enforcement of "Node is installed" is a README sentence. First-run failure looks like a Python traceback.

5. **No exit ramp.** S10 line 529 says "we do not fork or extend the DESIGN.md spec." Combined with no abstraction layer, the plugin's value proposition is structurally yoked to Google's whim.

**Required mitigations before Phase 0:**
- Vendor a copy at a known-good SHA into vendor/, OR add a package.json with exact-pinned dep and committed lockfile.
- Add an OfflineMode lint stub for Python-implementable rules (broken-ref, missing-sections, missing-typography) - already covers ~50% of S5.2's authoritative rules.
- Wrap every npx invocation and classify exit codes: 0 = pass, 1 = lint findings, other = environment error -> degraded mode, do not reject the artifact.

---

## Threat 2: Scope honesty - 9 days is fiction

**Severity: high.**

### Phase 3 is the worst offender (line 491, "Day 5")

VoltAgent/awesome-design-md is a brand **index** - a curated list pointing at other resources, not a corpus of ready-to-ship *.DESIGN.md files. S3.3 (lines 226-237) and S9 Phase 3 (lines 491-495) assume the 5 starters can be "curated" in one day. They cannot. To author a credible Stripe DESIGN.md you must:

1. Reverse-engineer Stripe's ~40-color palette into the 8-token semantic schema (lines 140-148).
2. Identify typography stack (Stripe uses custom `Sohne` which we cannot ship; substitution decisions are subjective).
3. Pick component primitives that evoke the brand without infringing.
4. Pass @google/design.md lint with contrast-ratio (S5.2 line 304) - non-trivial when chasing a brand palette.
5. Pass an aesthetic review (otherwise "Stripe starter" delivers no value).

Realistic estimate: **1.5-2 days per brand x 5 brands = 7.5-10 days for Phase 3 alone.** Phase 3 is 7x under-budgeted.

### Phase 5 (line 502, "Day 7")

The gallery must (a) iframe-embed up to 50 sandboxed artifacts (S5.4 step 3, line 350), (b) emit its *own* paired index.DESIGN.md (line 351), (c) pass @google/design.md lint on that emitted DESIGN.md (line 506), and (d) auto-regenerate within 1 second (line 506). That is not one day; it is a self-hosting compiler problem. The gallery's DESIGN.md must describe iframe wrappers, search/filter controls, meta-cards - none defined in paperboard.DESIGN.md's components: block (S3.1 lines 180-193). Either the gallery violates the design system or S3.1 must grow. Neither is acknowledged.

### Phase 2 (line 485, "Day 4")

The token-trace HTML check (S5.2 step 2 bullet 3, line 309) is the hardest static analysis in the SPEC. Every color/spacing/typography value in inline styles must trace to a token in the paired DESIGN.md - requiring CSS parsing, Tailwind utility-class inversion (Tailwind JIT is non-trivial to invert), and matching against the generated :root block. Hand-waved in one bullet, budgeted as part of a single day. Plan 2 days minimum; possibly punt to color-only token trace for v0.1.0.

### Net re-estimate

Honest scoping: **15-18 working days**, not 9. Either ship with 3 starters (Stripe/Linear/Vercel; drop Apple+Notion), defer daisy tier to v0.2, accept token-trace as color-only - or move public-release from v0.1.0 to v0.2.0 and label v0.1.0 a private preview.

---

## Threat 3: Licensing and attribution exposure

**Severity: high (legal), medium (technical).**

### Brand trademark exposure (S3.3, lines 226-237)

The interpretations-not-endorsements disclaimer (line 237) is not a legal force-field. The relevant test for trademark infringement is *likelihood of consumer confusion*, not the upstream license of the file. Three concrete risks:

1. **Apple.** Apple Legal is notoriously aggressive about any artifact named apple.* that visually evokes their identity, regardless of whether the upstream is MIT-licensed. That VoltAgent published an apple.DESIGN.md does not establish safe harbor; it only establishes VoltAgent has not yet been sued. We inherit none of their notice posture. **Drop apple.DESIGN.md entirely; replace with a generic minimal.DESIGN.md or premium-consumer.DESIGN.md.**

2. **Stripe / Linear / Vercel / Notion** carry lower-but-nonzero risk. Stripe in particular guards the wordmark and the purple gradient aggressively in payment-adjacent contexts. A Stripe customer using --design stripe to generate a payments dashboard creates exactly the confusion vector Stripe legal watches for.

3. **Apache-2.0 + MIT compatibility (S3.3 line 237)** is correctly stated as a copyright matter but says nothing about trademark. The two questions are independent and the SPEC conflates them.

### Per-file attribution (S11 #5, line 549)

Marked open - must lock before v0.1.0:
- Each starters/<brand>.DESIGN.md MUST include a YAML attribution: block in its frontmatter with upstream VoltAgent path, original commit SHA, and a not-affiliated-with-<brand> notice.
- README footer is not sufficient because DESIGN.md files travel - once a user runs /atv-paperboard:import-design stripe and the file lands in ~/.claude/artifacts/_designs/, it is detached from our README.

### The atv name

USPTO TESS check has not been done. ATV is a registered mark in multiple categories including some software ICs. The SPEC family (atv-starterkit, atv-design, atv-paperboard) means a single objection sinks the family. Pre-Phase-0: run a real TESS search in IC 009/042. Cheap; reduces a tail risk.

---

## Threat 4: Hidden assumptions and circular deps

**Severity: high.**

### Circular dependency: narrowed DESIGN.md may break its own lint (S5.1 step 4, line 288; S11 #6, line 550)

The SPEC says render-artifact emits a *narrowed* DESIGN.md - only the components actually used in the HTML. But:

- @google/design.md lint has a missing-sections rule (S5.2 line 304) and a missing-primary rule. Narrowing the components map likely violates these rules.
- S3.1 DESIGN.md declares button-primary. If the emitted artifact uses only card, the narrowed DESIGN.md drops button-primary - but if button-primary is required per Google spec, lint fails.
- The validator (S5.2 step 1) is run on the narrowed DESIGN.md, not the source. Validator success depends on a narrowing strategy that has not been validated against Google spec.

S11 #6 flags this and explicitly does not resolve it. Carrying this into Phase 1 means Phase 1 success test (S9 line 483) cannot be defined precisely. **Decide before Phase 0: emit the full source DESIGN.md verbatim** for v0.1.0; revisit narrowing post-release.

### Hook false positives (S7, lines 377-400)

bin/detect-artifact-candidate.py triggers on every Write containing a markdown table >= 4 rows (line 398). Agents write 4-row tables constantly - task lists, comparison matrices, plan trees, CHANGELOG entries. The hook will fire on virtually every meaningful Write. Suggests-never-autocompletes (line 400) does not save UX: a <system-reminder> that fires on every write becomes background noise the model learns to ignore.

Mitigations not in the SPEC:
- Require the table to have >= 2 numeric columns or a Status-like column (status/state/result/pass-fail). Otherwise skip.
- Suppress within N seconds of the previous suggestion.
- Skip if file path is *.md (user is authoring docs, not requesting a render).
- Skip if file path is inside ~/.claude/ (no recursive triggers on our own artifacts).

### Reviewer loop dead-end (S6.1 step 4, line 368)

Cap retries at 3 then escalate. But the retry loop sends the same violation report back to render-artifact, which uses the same DESIGN.md, with no strategy variation. If the failure is structural (e.g., a tier template hard-codes #ffffff), all 3 retries fail identically. The user receives three duplicate failure reports. Specify retry differentiation: each retry must change something - switch tier (pico <-> daisy), drop optional components, fall back to paperboard default - otherwise abandon at retry 1.

### examples/ referenced before it exists (S1 lines 69-72 vs S9 Phase 6 line 511)

S1 declares examples/status-dashboard/, examples/comparison-table/, examples/output-viewer/ as if present from Day 1. They are not produced until Phase 6 (Day 8). Anyone running claude plugin list at Phase 0-5 sees a broken layout. Either move examples/ creation to Phase 0 (empty placeholders) or remove from S1.

### data-aesthetic=glass referenced but never defined (S3.1 line 220)

The DESIGN.md says use data-aesthetic=glass opt-in for full swap - but no template, skill, or bin shim implements that switch. Either spec it or remove the line.

### Starter count contradiction

S0 line 9 lists Stripe, Linear, Vercel, Apple, plus a default - *four* brands + default. S1 layout and S3.3 table list *five* (adding Notion). The intro contradicts the layout and phase plan. Fix before Phase 0.

---

## Threat 5: Karpathy rule violations

**Severity: medium.**

### Minimum code

The plugin ships 4 skills + 1 agent + 1 hook + 3 bin shims + 3 templates + 7 designs + 3 example sets. Some is required by the four pillars, but:

- **skills/gallery/** is the Compound pillar but functionally a nice-to-have that costs an entire phase (Phase 5) and pulls in iframe/srcdoc/sandbox complexity. Cutting to v0.2 sheds ~1.5 days and one skill.
- **skills/import-design/** overlaps heavily with render-artifact --design <url>. S5.1 step 1 already says render-artifact resolves URLs and caches them. What does import-design add? Only pre-caching. Merge into render-artifact and shed a skill.
- **bin/open-browser.py** (S8.2) is 3 lines of code. It does not need a separate file; inline into serve-artifact.py.

### Surgical changes

S3 line 130 admits the previous SPEC hand-rolled tokens/paperboard.css. v2 replaces that with paperboard.DESIGN.md - sound. But v2 *also* adds: import-design skill, 5 brand starters, gallery-self-design mandate, the narrowing question, the hook artifact-detection heuristic. That is scope expansion riding on the DESIGN.md decision. Per Karpathy rule 5, every changed line should trace to the specific user request. Three new sub-systems (import, gallery-self-design, hook-detection) were not in the locked-decisions delta.

### Verifier separate from writer

S6.1 line 369 says Reviewer commissions; it does not author. Good. But the reviewers commission triggers render-artifact with a reviewer-supplied prompt - the reviewer prompt choice IS the authorial decision. The separation is nominal: reviewer is functionally a writer-via-proxy. Cleaner: reviewer reports; a *separate* regenerate-artifact skill decides retry strategy. Per CLAUDE.md: never self-approve in the same active context. Current design has the reviewer approving its own commissioned regeneration. Add an explicit gate.

---

## Required pre-implementation actions

These MUST resolve before Phase 0 begins:

1. **Verify @google/design.md exists with the claimed CLI surface.** Run npx -y @google/design.md@latest --help; lint --help; export --help. If the CLI does not expose --format json (S5.2 line 302) or --format css-tailwind (S3 line 131), the SPEC is non-implementable as written.
2. **Verify awesome-design-md actually contains parseable .DESIGN.md files** for the 5 starters. If it is an index repo, rewrite S3.3 and Phase 3 to reflect author-from-scratch effort, or drop bundled starters from v0.1.0.
3. **Lock the narrowing decision (S11 #6).** Recommend: emit verbatim source DESIGN.md for v0.1.0.
4. **Drop apple.DESIGN.md** (trademark exposure). Replace with a generic name. Re-evaluate stripe/notion after legal-lite check.
5. **Lock per-file attribution format** in starter frontmatter (S11 #5). Block until done.
6. **Reconcile starter count** between S0 line 9 (4 brands), S3.3 table (5 brands), S1 layout (5 files).
7. **Vendor or lockfile-pin @google/design.md.** No bare npx calls in production paths.
8. **Re-estimate the phase plan honestly.** Either expand to 15-18 days or cut scope (cut Phase 5 gallery, cut Phase 6 daisy tier, cut to 3 starters). The 9-day commitment is not credible.
9. **Add error taxonomy to design-md-bridge.py** distinguishing lint findings from environment failures.
10. **Tighten the hook heuristic** to avoid false-positive storms (numeric-column requirement + suppression window + path filters).
11. **Run a TESS check on atv** in software ICs before any public push.

## Nice-to-haves

- Merge import-design into render-artifact to shed a skill.
- Inline bin/open-browser.py into serve-artifact.py.
- Differentiate retry strategies in artifact-reviewer (do not loop with identical prompt 3x).
- Specify or remove data-aesthetic=glass (S3.1 line 220).
- Move examples/ creation to Phase 0 as empty placeholders.
- Add a --offline flag that short-circuits to the Python-side lint subset.
- Document a v0.2 migration path *now* in CHANGELOG for the inevitable @google/design.md schema break.
- Define behavior when --design <url> points at a non-DESIGN.md file or 404 (S5.1 step 1 says reject if lint fails - but lint cannot run on a 404).

---

*Reviewer recommendation: re-scope to v0.1.0-preview (private), 12 days, 3 starters, no Apple, gallery deferred. Public v0.1.0 ships only after pre-implementation actions 1-11 are closed.*
