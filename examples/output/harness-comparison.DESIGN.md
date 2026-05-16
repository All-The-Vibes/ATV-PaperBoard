---
version: alpha
name: paperboard
description: Default design for atv-paperboard gallery and emitted artifacts. Dialed-back neubrutalism — bold structure, restrained palette, no decorative excess.
colors:
  primary: "#1A1A1A"
  secondary: "#3B82F6"
  accent: "#F59E0B"
  background: "#FAFAFA"
  surface: "#FFFFFF"
  border: "#E2E8F0"
  foreground: "#0F172A"
  muted: "#64748B"
  danger: "#EF4444"
  success: "#22C55E"
typography:
  body:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  heading:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, monospace"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: 2px
  md: 4px
  lg: 6px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
---

# Paperboard

Default design system for atv-paperboard. The aesthetic is dialed-back neubrutalism: high-contrast structure and decisive typography, but no rainbow palettes or thick drop-shadows unless the artifact content warrants it.

## Do

- Use `{colors.primary}` for borders, headings, and interactive states.
- Use `{colors.secondary}` for primary calls-to-action and links.
- Use `{colors.accent}` sparingly — status badges, highlights.
- Prefer `{typography.body}` for prose; `{typography.mono}` for code and data.
- Keep spacing on the `{spacing.md}` / `{spacing.lg}` scale for card interiors.
- Border thickness: 1px for dividers, 2px for card outlines.

## Don't

- Don't use drop-shadows by default. Borders define depth here.
- Don't mix more than 3 type sizes on one artifact.
- Don't apply `{colors.accent}` to more than 15 % of visible surface area.
- Don't use decorative background patterns in the default tier.

## Colors

Primary (`{colors.primary}`) anchors text and outlines. Secondary (`{colors.secondary}`) drives action. Accent (`{colors.accent}`) is reserved for status and emphasis. Background (`{colors.background}`) and surface (`{colors.surface}`) are near-white — no pure white, avoids harshness on high-DPI.

Muted (`{colors.muted}`) for secondary text and metadata rows.

## Typography

One font stack throughout: system-ui. Heading weight 700, body weight 400. Letter-spacing tightened on headings (`-0.02em`) for the neubrutalist compression feel without custom fonts.

## Components

Gallery frame: flat card, `{colors.border}` 2px outline, `{rounded.md}` radius, `{spacing.md}` padding.
Artifact card: same as gallery frame; heading row uses `{colors.primary}`, metadata row uses `{colors.muted}`.
Status badge: `{colors.accent}` background, `{colors.primary}` text, `{rounded.sm}` radius, `{spacing.xs}` padding.
Code block: `{colors.surface}` background, `{colors.border}` 1px outline, `{typography.mono}`.
