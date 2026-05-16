# Copilot CLI Adapter — Status Dashboard

Release-proof scenario, 2026-05-16 (harness=copilot-cli)

| Check                                    | Status | Tests | Duration (ms) |
|------------------------------------------|--------|-------|---------------|
| manifest hooks.json parses               | pass   | 1/1   | 2             |
| postToolUse matcher matches create/edit  | pass   | 4/4   | 3             |
| timeoutSec <= 60                         | pass   | 1/1   | 1             |
| bash + powershell both declared          | pass   | 1/1   | 1             |
| env PAPERBOARD_HARNESS injected          | pass   | 1/1   | 1             |
| agent frontmatter (description + prompt) | pass   | 3/3   | 2             |
| stdin-JSON hook helpers                  | pass   | 11/11 | 11            |
| harness detection cascade                | pass   | 5/5   | 4             |
| persistence path resolution              | pass   | 4/4   | 3             |
| end-to-end CLI subcommand                | pass   | 5/5   | 17            |

Totals: 130 tests passing · 2 skipped · 37 new regression tests added.
