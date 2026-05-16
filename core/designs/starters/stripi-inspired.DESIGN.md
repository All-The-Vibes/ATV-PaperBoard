---
name: Stripi-inspired
version: "0.1.0"
description: Stripe-evoking design — purple/violet primary, generous whitespace, Inter-style typography.
attribution:
  inspired_by: "Stripi"
  not_affiliated_with: "Stripe Inc."
  source_repo: "VoltAgent/awesome-design-md"
  source_path: "design-md/stripe/DESIGN.md"
  source_commit: "TBD"
  source_license: "MIT"
  redistributed_under: "Apache-2.0"
  imported_at: "2026-05-14"
  notes: |
    Tokens are reverse-engineered impressions of Stripe's public visual brand;
    not a verbatim copy. No trademark license claimed.
colors:
  primary: "#635BFF"
  background: "#FFFFFF"
  foreground: "#0A2540"
  accent: "#80E9FF"
  surface: "#F6F9FC"
  muted: "#697386"
typography:
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  mono:
    fontFamily: "'Courier New', Consolas, 'Liberation Mono', monospace"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif"
    fontWeight: 700
    lineHeight: 1.2
components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: 8px
    padding: 24px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.background}"
    rounded: 4px
    padding: 12px
  link:
    textColor: "{colors.accent}"
  caption:
    textColor: "{colors.muted}"
---

# Stripi-inspired Design

## Overview

Stripe-evoking aesthetic: purple/violet primary, clean white background, generous whitespace.
Crisp, trustworthy, conversion-focused. System fonts only — no custom font shipping.

## Colors

- **primary** `#635BFF` — signature Stripe-violet for CTAs and focus indicators
- **background** `#FFFFFF` — stark white canvas
- **foreground** `#0A2540` — deep navy-black body text
- **accent** `#80E9FF` — electric cyan highlight
- **surface** `#F6F9FC` — off-white card fill
- **muted** `#697386` — secondary / caption text

## Typography

`body` and `heading` use the OS sans-serif stack (Inter-style intent). `mono` uses system monospace.
No custom font downloads — all system fallbacks.

## Components

- **card**: White surface container with 8px radius and 24px padding
- **button-primary**: Violet fill, white label, 4px radius, 12px padding
- **link**: Cyan accent text, no underline at rest
- **caption**: Muted grey for secondary labels and helper text

## Do's and Don'ts

- Do use generous whitespace between sections (≥ 48px vertical gaps)
- Don't use more than two font weights per screen
- Do keep primary color reserved for a single CTA per view
