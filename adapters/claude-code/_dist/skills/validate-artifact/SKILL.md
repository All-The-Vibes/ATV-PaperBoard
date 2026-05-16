---
name: validate-artifact
description: >
  Run ENFORCE checks on a rendered artifact slug: Google design.md lint + HTML-side
  color-token trace. Reports ACCEPT or FAIL with fail_class. Invokes `paperboard validate`.
---

# validate-artifact

Enforces design contract compliance on a previously rendered artifact.

## Usage

```
paperboard validate <slug>
```

## When to invoke

- After `render-artifact` completes, to confirm the artifact is compliant.
- When the `artifact-reviewer` agent requests validation.
- Before publishing or persisting an artifact as final.

## Checks performed

1. **lint** — `@google/design.md` JSON lint on the paired DESIGN.md sidecar.
2. **color-trace** — Every inline hex color in the HTML must appear in the DESIGN.md Colors section.

## Output

Prints one of:
- `✓ ACCEPT  slug=<slug>` — all checks passed; exit 0.
- `✗ FAIL(<fail_class>)  slug=<slug>` — details follow; exit 1.

`fail_class` is one of: `none | lint | color-trace | environment`
