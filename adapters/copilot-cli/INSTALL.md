# atv-paperboard — Copilot CLI Install Guide

Native plugin adapter for the [GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/copilot-cli)
local terminal agent. This is **not** the GitHub Actions recipe — that one
lives in `recipes/github-actions/` and targets the Copilot Coding Agent.

## Prerequisites

- [`copilot` CLI](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins) installed and authenticated
- Python 3.10+ on PATH
- `paperboard` on PATH (`pip install atv-paperboard` or `pipx install atv-paperboard`)
- Node.js 20+ for the `@google/design.md` lint bridge

## Path A — Marketplace install (recommended)

```
# Inside copilot (interactive)
/plugin marketplace add <owner>/atv-paperboard
/plugin install atv-paperboard@<marketplace>
```

Replace `<owner>` with the GitHub org hosting the plugin. The marketplace
manifest is read from this repository's `adapters/copilot-cli/_dist/`
directory after running `python adapters/copilot-cli/build.py`.

## Path B — Local plugin-dir (development / unpacked install)

For testing the adapter without installing through the marketplace:

```bash
# 1. Build the self-contained dist
python adapters/copilot-cli/build.py

# 2. Launch copilot with the local plugin loaded
copilot --plugin-dir=$(pwd)/adapters/copilot-cli/_dist
```

`--plugin-dir` is repeatable and bypasses the marketplace entirely — useful
for adapter development and CI smoke tests.

## Path C — Repo-scoped install

Some teams prefer the plugin to live alongside the repo so contributors
share one config:

```bash
git clone https://github.com/<owner>/atv-paperboard ~/.copilot/installed-plugins/atv-paperboard
pip install atv-paperboard
```

Copilot CLI auto-loads anything under `~/.copilot/installed-plugins/`.

## Verify

After any install path, run:

```
paperboard doctor
```

The `harness:` line should read `copilot-cli`. If it reads `standalone`,
either `COPILOT_HOME` is unset and the plugin is not under
`~/.copilot/installed-plugins/atv-paperboard/`, or you exported
`PAPERBOARD_HARNESS` to something else.

**Confirm the hook fires:**

1. Inside a `copilot` session, ask Copilot to create a markdown file
   containing a status-column table (e.g. `| Job | Status |`).
2. On the next agent turn, look for the injected reminder:

   ```
   [atv-paperboard] This looks like a data artifact.
   To render it:
     paperboard render --input <path>
   ```

   If the reminder does not appear within one tool turn, check
   `~/.copilot/logs/` for hook-execution errors. The hook is **fail-open**:
   non-zero exit codes are logged but do not block tool execution.

## Persistence

Artifacts are written to:

```
${COPILOT_HOME:-$HOME/.copilot}/plugin-data/atv-paperboard/artifacts/<date>/<slug>.{html,DESIGN.md,meta.yaml}
```

This path survives plugin upgrades (Copilot CLI versions the install root
but not `plugin-data/`). To pin a different location:

```bash
export PAPERBOARD_ARTIFACT_DIR=~/my-artifacts
```

## Enforcement note (fail-open hooks)

Copilot CLI hooks are **fail-open** by design — a hook returning non-zero
does not block the tool call (opposite of Claude Code, which fail-closes).
The `postToolUse` hook in this adapter therefore _suggests_ rendering via
`additionalContext` injection rather than enforcing it. Hard enforcement of
design-contract compliance stays in CI via `paperboard validate-all` (see
`recipes/github-actions/workflow.yml.template`).

## Uninstall

```
# Inside copilot (interactive)
/plugin uninstall atv-paperboard
```

Or remove the directory directly:

```bash
rm -rf ~/.copilot/installed-plugins/atv-paperboard
```

Artifacts under `~/.copilot/plugin-data/atv-paperboard/` are **not**
removed. Delete that directory manually to reclaim disk.

## References

- [Copilot CLI plugins overview](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins)
- [Custom agents](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents)
- [Hooks reference (payload schemas + exit codes)](https://docs.github.com/en/copilot/reference/hooks-reference)
- [CLI config directory reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
- SPEC addendum: [`SPEC-addendum-2026-05-16-copilot-cli.md`](../../SPEC-addendum-2026-05-16-copilot-cli.md)
