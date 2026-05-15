---
name: gallery
description: >
  Regenerate the Paperboard Gallery — a local HTML index of all rendered artifact triples.
  Invokes `paperboard gallery` via the atv-paperboard CLI.
---

# gallery

Rebuilds `gallery.html` in the artifact directory by scanning all `*.meta.yaml` sidecars.

## Usage

```
paperboard gallery
```

## When to invoke

- After a `paperboard render` run to see all artifacts in one place.
- Periodically in CI to publish a browsable artifact index.

## Output

Writes `gallery.html` to the harness artifact directory and prints the path.
The gallery links to each artifact's `.html` file — no iframes in v0.1.0.

## Notes

- Uses `paperboard.DESIGN.md` as its design; no separate `gallery.DESIGN.md` is created.
- Completes in < 1 second for up to 50 artifacts.
