---
name: regenerate-artifact
description: >
  3-step differentiated retry for a failing artifact slug: switch tier, drop optional
  components, fall back to default design. Invokes `paperboard regenerate`.
---

# regenerate-artifact

Recovers a failing artifact via three progressively conservative retry steps.

## Usage

```
paperboard regenerate <slug>
```

## When to invoke

- `validate-artifact` returns FAIL and the `artifact-reviewer` recommends `REGENERATE_VIA regenerate-artifact`.
- Never invoke without a prior validation failure — check first.

## Retry strategy

| Step | Change | Rationale |
|------|--------|-----------|
| 1 | Switch tier (pico ↔ daisy) | Different CSS framework may avoid inline color conflicts |
| 2 | Drop optional components from input | Reduces surface area for color violations |
| 3 | Fall back to `paperboard.DESIGN.md` | Known-good default design always lints clean |

## Output

Prints: `Regenerate step=<N>  new_slug=<slug>  status=ACCEPT|FAIL(<fail_class>)`

Exit 0 on ACCEPT, exit 1 if all three steps fail.
