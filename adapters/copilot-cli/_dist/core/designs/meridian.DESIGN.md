---
version: alpha
name: meridian
description: Meridian editorial document system for atv-paperboard. Dark, composed, decision-first, with restrained indigo structure and amber emphasis.
colors:
  primary: "#7170FF"
  secondary: "#5E6AD2"
  accent: "#F1B13B"
  background: "#08090A"
  surface: "#0E0F12"
  border: "#252830"
  foreground: "#F7F8F8"
  muted: "#8A8F98"
  danger: "#C97070"
  success: "#7FAE6E"
typography:
  body:
    fontFamily: "Inter, Geist, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.6
  heading:
    fontFamily: "Instrument Serif, Georgia, Times New Roman, serif"
    fontSize: 44px
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: -0.01em
  mono:
    fontFamily: "JetBrains Mono, Geist Mono, SF Mono, Menlo, Consolas, monospace"
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

# Meridian

Meridian is an opt-in editorial style for PaperBoard's `atv` HTML output. It is
built for proposals, plans, reviews, and decision documents that need to feel
authored rather than dumped from a chat transcript.

## Colors

The canvas is near-black. Surfaces stay dark. Indigo is structural, amber is the
editorial accent, and status colors are muted enough to avoid dashboard noise.

- `{colors.background}` is the page canvas.
- `{colors.surface}` is the container fill for tables, code shells, and cards.
- `{colors.foreground}` carries primary text.
- `{colors.muted}` carries secondary metadata.
- `{colors.primary}` is used for brand glyphs and sparse interactive emphasis.
- `{colors.accent}` is used for editorial section markers and decision emphasis.

## Typography

Use Instrument Serif for major editorial headings. Use Inter for body copy. Use
JetBrains Mono for labels, code, data, and file paths.

## Components

- Hero: decision-first, high contrast, no decorative card grid.
- Tables: dark surfaces, compact headings, mobile definition-row behavior.
- Code and file trees: dark shell, no tiny unreadable horizontal scroll when a
  structured component can represent the same content.
- Callouts: reserved for quotes, warnings, and decision emphasis.

## Don't

- Do not render large white surfaces inside Meridian documents.
- Do not use generic dashboard-card mosaics for proposals.
- Do not let renderer branding outrank the document's own title or decision.
