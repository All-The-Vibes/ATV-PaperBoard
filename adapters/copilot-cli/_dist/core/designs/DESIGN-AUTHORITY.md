# Design Authority

**Effective:** 2026-05-16
**Binding doctrine:** `pbakaus/impeccable` — Apache 2.0 — pinned commit `4af581e23f17d112d8f9d6b7a5b7ff37823494e1`
**Scope:** All `.DESIGN.md` files in `core/designs/` and `core/designs/starters/`, plus any new tier authored downstream.

---

## What this document binds

Every `.DESIGN.md` file shipped by atv-paperboard — including the default `paperboard.DESIGN.md`, the `atv` tier, and every starter — is authored under impeccable's anti-slop doctrine. Impeccable governs **how** design tokens and Do/Don't rules are written; it does **not** override paperboard's aesthetic identity (cold, dark, technical). This is a **methodology import**, not an aesthetic import.

If a future contributor lifts a `.DESIGN.md` from another project, it must be audited against this document before merge.

## Methodology vs. aesthetic — the load-bearing distinction

| Layer | Source of truth | Example |
|------|-----------------|---------|
| **Methodology** (how rules are authored) | impeccable | "Every Don't is a hard, enforceable ban — never advisory" |
| **Absolute bans** (what may never appear) | impeccable | glassmorphism, gradient text, side-stripes, AI emoji, nested cards |
| **Aesthetic tokens** (color, type, spacing) | paperboard | `#08090A` near-black canvas; Geist Mono eyebrows; indigo accent |
| **Component vocabulary** | paperboard | Stack-list, dep-list, atv topbar, fit chip |

Impeccable's own tokens (Cormorant Garamond, Editorial Magenta, Warm Ash Cream) are **not** adopted. Paperboard's tokens remain canonical for paperboard artifacts.

## Absolute bans inherited from impeccable

These bans are non-negotiable. Every `.DESIGN.md` file in this repo enforces them in its Don't list.

- **Glassmorphism** — no `backdrop-filter: blur`, no frosted-translucent surfaces, no glow-on-blur cards. Rationale: the most recognizable "AI-generated UI" tell of 2023–2025. Impeccable §6 Don'ts.
- **Gradient text** — no `background-clip: text` with a gradient fill. Rationale: a marketing trick that signals "designed by template," not by intent. Impeccable §6 Don'ts.
- **Side-stripe borders** — no `border-left` or `border-right` greater than 1px as a colored stripe on cards, list items, callouts, or alerts. Rationale: the single most recognizable AI-dashboard tell. Impeccable §6 Don'ts.
- **Nested card-in-card patterns** — no card containers visually nested inside other cards. Rationale: flatten the hierarchy; depth from negative space, not bounded boxes. Impeccable §6 Don'ts.
- **Generic AI emoji decoration** — no ✨ 🚀 ⚡ 🎯 🔥 💎 or comparable cliché glyphs used decoratively. Status dots, mono `·`, and typographic emphasis are the only allowed ornaments. Impeccable's anti-slop principle, restated across `skill/reference/`.
- **Identical-card feature grids** — no `repeat(auto-fit, minmax(280px, 1fr))` of same-shaped icon-heading-text cards endlessly tiled. Impeccable §6 Don'ts.
- **Hero-metric SaaS layouts** — no big-number-with-tiny-label-and-gradient-accent template. Impeccable §6 Don'ts.
- **Bounce / elastic easing** — animations decelerate via expo-out only (`cubic-bezier(0.16, 1, 0.3, 1)`). Impeccable §5 Motion.
- **Pure `#000`/`#fff`** — always tinted neutrals. Paperboard's `#08090A` / `#F7F8F8` satisfy this.

## Do (paperboard aesthetic, impeccable-compliant)

- Use 1px hairline borders on every container; depth comes from layered tonal surfaces, not drop shadows.
- Keep accent colors (indigo, rose) to ≤ 15% of visible surface area; loud colors live in 4–8px status dots only.
- Number sections (`00`, `01`, `02`) with mono eyebrows in UPPERCASE 0.12em tracking.
- Tighten letter-spacing on headings (`-0.02em` to `-0.04em`). Brand signature.
- Mono digits use `font-feature-settings: "tnum"` for aligned tabular numbers.
- Cap body line-length at 65–75ch via `max-width`.
- Respect `prefers-reduced-motion` on every transition.

## Don't (the bans above, restated as enforcement)

- Don't ship a `.DESIGN.md` file whose Do/Don't list omits the impeccable bans.
- Don't introduce a glass / frosted / blurred / glow tier. The retired `glass.DESIGN.md` (2026-05-16) is the precedent.
- Don't hedge in design prose. "Maybe consider," "could be helpful," "might want to" are banned — impeccable's expert-decisive voice.
- Don't expand the accent palette to a second hue. One accent per artifact; use scale or weight for a second emphasis point.

## Full reference

The seven impeccable reference files — vendored under Apache 2.0 with original headers — live at:

```
core/designs/impeccable-context/
  typography.md
  color-and-contrast.md
  spatial-design.md
  motion-design.md
  interaction-design.md
  responsive-design.md
  ux-writing.md
```

These are agent-context documents: when an LLM is asked to author or modify a `.DESIGN.md`, the harness adapter injects them so the agent reads doctrine before writing tokens. They are not consumed by the Python render pipeline.

## Audit cadence

- **Every new `.DESIGN.md` file** is reviewed against this doctrine before merge. The reviewer adds an HTML audit comment at the top of the file: `<!-- YYYY-MM-DD: audited against impeccable doctrine; <N> violations corrected: <list> -->` or `<!-- ... no violations found -->`.
- **Existing files** carry their audit comment from the most recent review. Re-audit on any material change to the Do/Don't list, tokens, or component definitions.
- **The CLI lint pass** (`npm run lint:artifacts`, optional, Node.js) catches anti-pattern regressions in *generated HTML* artifacts. The design-tier audit catches them at the source — in the token spec itself.

## Provenance

- Impeccable: https://github.com/pbakaus/impeccable @ commit `4af581e2…` — Apache License 2.0.
- Attribution: `NOTICE.md` records the vendored reference files and their license.
- Paperboard remains MIT-licensed (or whatever the repo LICENSE declares); the borrowed impeccable files retain their Apache 2.0 headers.
