---
name: Vercel-inspired
version: "0.1.0"
description: Vercel-evoking design — monochrome, high contrast, Geist-style system typography.
attribution:
  inspired_by: "Vercel"
  not_affiliated_with: "Vercel Inc."
  source_repo: "VoltAgent/awesome-design-md"
  source_path: "design-md/vercel/DESIGN.md"
  source_commit: "TBD"
  source_license: "MIT"
  redistributed_under: "Apache-2.0"
  imported_at: "2026-05-14"
  notes: |
    Tokens are reverse-engineered impressions of Vercel's public visual brand;
    not a verbatim copy. No trademark license claimed.
colors:
  primary: "#000000"
  background: "#FFFFFF"
  foreground: "#000000"
  accent: "#0070F3"
  surface: "#FAFAFA"
  muted: "#888888"
typography:
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.6
  mono:
    fontFamily: "'Courier New', Consolas, 'Liberation Mono', monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontWeight: 700
    lineHeight: 1.15
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: 4px
    padding: 20px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: 4px
    padding: 10px
  link:
    textColor: "{colors.accent}"
  caption:
    textColor: "{colors.muted}"
---

# Vercel-inspired Design

## Overview

Vercel-evoking monochrome aesthetic: black-on-white, high contrast, minimal ornamentation.
Typography reads as Geist-style via system sans stack. No custom font shipping.

## Colors

- **primary** `#000000` — pure black for primary actions and headings
- **background** `#FFFFFF` — pure white canvas
- **foreground** `#000000` — pure black body text, maximum contrast
- **accent** `#0070F3` — Vercel blue for interactive links and focus rings
- **surface** `#FAFAFA` — near-white card fill
- **muted** `#888888` — secondary / caption text

## Typography

`body` and `heading` use the OS sans stack (Geist-style intent — Geist not shipped).
`mono` uses system monospace. No custom font downloads — all system fallbacks.

## Components

- **card**: Near-white surface with 4px radius and 20px padding, 1px border implied
- **button-primary**: Pure black fill, white label, sharp 4px radius
- **link**: Vercel-blue text for high visibility on white
- **caption**: Muted grey for secondary labels and meta text

## Do's and Don'ts

- Do keep color use to black, white, and a single accent per page
- Don't introduce gradients — the monochrome palette is intentional
- Do use font-weight contrast (400 vs 700) as the primary visual hierarchy signal
