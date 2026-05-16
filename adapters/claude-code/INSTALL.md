# atv-paperboard — Claude Code Install Guide

## Prerequisites

- Claude Code with plugin support enabled
- Python 3.10+ on PATH
- **Node.js 18+ on PATH** — the Enforce pillar runs `@google/design.md`
  via Node. Without it, design lint silently degrades to a Python fallback.
- **`paperboard` on PATH** — the plugin's PostToolUse hook invokes the
  `paperboard` binary directly. Install via PyPI first:
  ```bash
  pip install atv-paperboard
  # or, for an isolated CLI install:
  pipx install atv-paperboard
  ```
- **`@google/design.md`** — the lint binary the bridge calls:
  ```bash
  npm install -g @google/design.md@0.1.1
  ```
  After install, run `paperboard doctor` and confirm the `@google/design.md`
  row shows `0.1.1` and the `paperboard.DESIGN.md lint` row shows `✓ clean`.

---

## Install

```
/plugin marketplace add All-The-Vibes/ATV-PaperBoard
/plugin install atv-paperboard@atv-paperboard
```

The first command registers the marketplace defined in
`.claude-plugin/marketplace.json` at the repo root. The second installs the
plugin source from `./adapters/claude-code/_dist`.

---

## Verify

After install, confirm the plugin is registered:

```
/plugin list
```

You should see `atv-paperboard` in the output.

**Confirm the hook fires:**

1. Ask Claude Code to write any file containing a markdown table with numeric or status columns.
2. Check stderr — you should see a line like:

   ```
   [atv-paperboard] This looks like a data artifact. To render it:
     paperboard render --input <path>
   ```

3. Or, from a Bash tool:

   ```bash
   paperboard doctor
   ```

   The `harness` line should read `claude-code`.

---

## Persistence

Artifacts are written to `${CLAUDE_PLUGIN_DATA}/<date>/<slug>.{html,DESIGN.md,meta.yaml}`.

`CLAUDE_PLUGIN_DATA` is injected by Claude Code at runtime and points to a stable,
version-independent location. **Do not** store data under `CLAUDE_PLUGIN_ROOT` — that
path changes on plugin updates and old versions are cleaned after ~7 days.

---

## Uninstall

```
/plugin uninstall atv-paperboard
```

Artifacts already written to `${CLAUDE_PLUGIN_DATA}` are **not** deleted. To remove
them, delete the directory manually:

```bash
rm -rf "$CLAUDE_PLUGIN_DATA"
```

Uninstall the Python package separately:

```bash
pip uninstall atv-paperboard
```
