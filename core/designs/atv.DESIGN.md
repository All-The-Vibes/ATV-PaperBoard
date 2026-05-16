---
version: alpha
name: atv
description: ATV design language — dark, dense, technical. Linear/Vercel/Stripe internal-doc lineage. Near-black canvas, hairline borders, mono eyebrows, one accent, depth from ambient gradients rather than elevation.
colors:
  primary: "#7170ff"
  secondary: "#5e6ad2"
  accent: "#f43f5e"
  background: "#08090a"
  surface: "#0e0f12"
  border: "#252830"
  foreground: "#f7f8f8"
  muted: "#8a8f98"
  danger: "#fb7185"
  success: "#34d399"
typography:
  body:
    fontFamily: "Inter, Geist, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.55
  heading:
    fontFamily: "Inter, Geist, -apple-system, sans-serif"
    fontSize: 34px
    fontWeight: 510
    lineHeight: 1.1
    letterSpacing: -0.025em
  mono:
    fontFamily: "Geist Mono, JetBrains Mono, SF Mono, Menlo, Consolas, monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: 4px
  md: 12px
  lg: 14px
spacing:
  xs: 6px
  sm: 12px
  md: 22px
  lg: 36px
  xl: 88px
---

# ATV

Dark, dense, technical design language for atv-paperboard artifacts. Built for engineers reading status reports, integration notes, comparison docs, and bug-hunt summaries.

## Colors

The palette is 6 grays plus 1 indigo accent plus 1 rose accent plus 2 status colors (green/rose dots). Loud colors only appear in 4-8px dots — never as fills, never as borders > 1px.

- `{colors.background}` is the page canvas. Never pure black.
- `{colors.surface}` for raised regions (cards, code shells, tables).
- `{colors.border}` is the 1px hairline color on every container. Borders define depth — no drop shadows.
- `{colors.foreground}` for primary text, `{colors.muted}` for secondary/eyebrow text.
- `{colors.primary}` (accent indigo) sparingly — interactive highlights, file-path indicators, hover states.
- `{colors.accent}` (rose) for status dots, never for large fills.

## Typography

Inter or Geist body, Geist Mono for code/eyebrows. Heading weight is 510 (between regular and semibold) — distinctly lighter than typical bold. Letter-spacing tightens on every heading (`-0.025em` on H2, `-0.04em` on hero H1). Mono digits use `font-feature-settings: "tnum"` for aligned tabular numbers.

`{typography.body}` is the page body stack. `{typography.heading}` carries `letterSpacing: -0.025em` — the slight tightening is the brand. `{typography.mono}` is used for eyebrows (UPPERCASE, 0.12em tracking), code, file paths, and tabular numerics.

## Components

- **Topbar**: 52px sticky, `{colors.surface}` with `backdrop-filter: blur(14px)`, brand glyph + breadcrumb + status pill.
- **Hero**: 112px top padding, mono eyebrow, large `clamp(44px, 6vw, 72px)` headline, 18px subtitle, meta strip with hairline separator.
- **Section head**: `00 / Eyebrow / H2 / aside-pill`. Numbers in `{colors.muted}` mono.
- **Stack-list / Dep-list / Q-list**: Bordered list containers with grid rows. No card grids — single-column lists with hairline separators between rows.
- **Code shell**: macOS traffic-light dots, language tag right-aligned, dark `#06060a` code surface.
- **Color strip**: 6-column grid, no gap (1px hairline), per-cell swatch + name + hex + role.
- **Fit chips**: pill with leading dot. Green dot = good fit, rose dot = avoid.
- **Anti-pattern block**: bordered container with "DO NOT" mono label at top-right.
- **Checklist**: single-column list, hairline-separated rows, mono `·` markers.

## Do's and Don'ts

### Do

- Use `{colors.background}` as the page canvas. Never pure black.
- Use `{colors.surface}` for raised regions (cards, code shells, tables).
- Use `{colors.border}` as 1px hairlines on every container.
- Use `{colors.foreground}` for primary text, `{colors.muted}` for secondary text.
- Use `{colors.primary}` sparingly — interactive highlights only.
- Use `{colors.accent}` for status dots, never large fills.
- Number every section. `00`, `01`, `02` — two digits, mono.
- Mono eyebrows above section titles — UPPERCASE, 0.12em tracking.

### Don't

- Don't use drop shadows. Depth comes from blurred ambient gradients on the hero only.
- Don't fill large areas with `{colors.accent}` or `{colors.danger}`.
- Don't introduce a light theme variant inside an atv-tier artifact. Dark is the contract.
- Don't use more than one accent color per artifact. Indigo or rose, not both.
- Don't render generic `<table>` markup without an atv-typed wrapper.
