---
name: Lin-ear-inspired
version: "0.1.0"
description: Linear-evoking design — dark UI, indigo accents, geometric sans typography.
attribution:
  inspired_by: "Lin-ear"
  not_affiliated_with: "Linear Orbit Inc."
  source_repo: "VoltAgent/awesome-design-md"
  source_path: "design-md/linear/DESIGN.md"
  source_commit: "TBD"
  source_license: "MIT"
  redistributed_under: "Apache-2.0"
  imported_at: "2026-05-14"
  notes: |
    Tokens are reverse-engineered impressions of Linear's public visual brand;
    not a verbatim copy. No trademark license claimed.
colors:
  primary: "#5E6AD2"
  background: "#0F0F12"
  foreground: "#E8E8F0"
  accent: "#7C8CF8"
  surface: "#1A1A22"
  muted: "#6B6B7E"
typography:
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  mono:
    fontFamily: "'Courier New', Consolas, 'Liberation Mono', monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontWeight: 600
    lineHeight: 1.25
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: 6px
    padding: 20px
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.background}"
    rounded: 6px
    padding: 10px
  link:
    textColor: "{colors.primary}"
  caption:
    textColor: "{colors.muted}"
---

# Lin-ear-inspired Design

## Overview

Linear-evoking dark UI: deep near-black background, indigo primary, geometric sans system fonts.
Dense, focused, productivity-tool aesthetic. All system fonts — no custom font shipping.

## Colors

- **primary** `#5E6AD2` — signature indigo for interactive elements
- **background** `#0F0F12` — deep near-black canvas
- **foreground** `#E8E8F0` — near-white readable body text
- **accent** `#7C8CF8` — lighter indigo for hover / links
- **surface** `#1A1A22` — elevated card background
- **muted** `#6B6B7E` — secondary / caption text

## Typography

`body` and `heading` use the OS geometric sans stack. `mono` uses system monospace.
No custom font downloads — all system fallbacks.

## Components

- **card**: Dark surface container with 6px radius and 20px padding
- **button-primary**: Indigo fill, deep-black label, 6px radius, 10px padding
- **link**: Light indigo text for high contrast on dark backgrounds
- **caption**: Muted slate for secondary labels and timestamps

## Do's and Don'ts

- Do use a single accent color per hierarchy level
- Don't use light backgrounds — the dark canvas is load-bearing to the aesthetic
- Do keep interactive elements tightly spaced; density is intentional
