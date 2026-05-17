# Upstream: pbakaus/impeccable

| Field | Value |
|---|---|
| Repository | https://github.com/pbakaus/impeccable |
| License | Apache 2.0 (see LICENSE-APACHE-2.0 in this directory) |
| Pinned commit | `4af581e23f17d112d8f9d6b7a5b7ff37823494e1` |
| Source path | `skill/reference/` |
| Retrieved | 2026-05-16 |

## Vendored files

| File | Upstream URL |
|---|---|
| typography.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/typography.md |
| color-and-contrast.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/color-and-contrast.md |
| spatial-design.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/spatial-design.md |
| motion-design.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/motion-design.md |
| interaction-design.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/interaction-design.md |
| responsive-design.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/responsive-design.md |
| ux-writing.md | https://github.com/pbakaus/impeccable/blob/4af581e23f17d112d8f9d6b7a5b7ff37823494e1/skill/reference/ux-writing.md |

## Re-sync procedure

To refresh from a newer upstream commit:

1. `gh api repos/pbakaus/impeccable/commits/main --jq .sha` — get latest SHA
2. For each of the 7 files above, run `gh api repos/pbakaus/impeccable/contents/skill/reference/<file>?ref=<SHA> --header 'Accept: application/vnd.github.raw' > core\designs\impeccable-context\<file>`
3. Update the `Pinned commit` and `Retrieved` rows above.
4. Re-run `pytest -q` to confirm no regressions.

## Modifications

These files are vendored unmodified from upstream. No paperboard-side edits.
