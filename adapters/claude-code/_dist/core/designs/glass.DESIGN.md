---
name: Glass
version: "0.1.0"
description: Premium opt-in glassmorphism tier — frosted surfaces, translucent layers, depth.
attribution:
  inspired_by: "atv-paperboard glass aesthetic"
  not_affiliated_with: "N/A — original design for atv-paperboard"
  source_repo: "atv-paperboard"
  source_path: "designs/glass.DESIGN.md"
  source_commit: "TBD"
  source_license: "Apache-2.0"
  redistributed_under: "Apache-2.0"
  imported_at: "2026-05-14"
  notes: |
    Original design created for atv-paperboard. No upstream brand affiliation.
    Glassmorphism aesthetic: frosted-glass surfaces via backdrop-filter.
colors:
  primary: "#4338CA"
  background: "#0D1117"
  foreground: "#F0F4FF"
  accent: "#A5B4FC"
  surface: "#1C2033"
  muted: "#94A3B8"
typography:
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.65
  mono:
    fontFamily: "'Courier New', Consolas, 'Liberation Mono', monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontWeight: 600
    lineHeight: 1.2
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: 16px
    padding: 28px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.foreground}"
    rounded: 12px
    padding: 12px
  link:
    textColor: "{colors.accent}"
  caption:
    backgroundColor: "{colors.background}"
    textColor: "{colors.muted}"
---

# Glass Design

## Overview

Premium opt-in glassmorphism tier for atv-paperboard. Frosted translucent surfaces on a rich dark
canvas. Achieves depth through `backdrop-filter: blur` rather than opaque fills.
System fonts throughout — no custom font shipping.

## Colors

- **primary** `#4338CA` — deep indigo for interactive elements and focus rings
- **background** `#0D1117` — deep dark canvas (supports blur layers)
- **foreground** `#F0F4FF` — near-white readable text
- **accent** `#A5B4FC` — soft lavender for links and highlights
- **surface** `#1C2033` — dark blue-tinted fill simulating frosted glass (CSS backdrop-filter provides the blur)
- **muted** `#94A3B8` — slate for secondary text

## Typography

`body` and `heading` use the OS sans stack at comfortable sizes. `mono` uses system monospace.
No custom font downloads — all system fallbacks.

## Components

- **card**: Dark blue-tinted surface with 16px radius and 28px padding; `backdrop-filter: blur` applied in CSS
- **button-primary**: Deep indigo fill, near-white label, generous 12px radius
- **link**: Soft lavender text; legible on both dark and frosted backgrounds
- **caption**: Deep-canvas background with slate text for secondary labels

## Do's and Don'ts

- Do apply `backdrop-filter: blur(12px)` to every card surface
- Don't omit the dark canvas — glassmorphism collapses on light backgrounds
- Do keep border-radius large and consistent (≥ 12px) for cohesion
