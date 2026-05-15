# atv-paperboard — Claude Code Install Guide

## Prerequisites

- Claude Code with plugin support enabled
- Python 3.9+ on PATH

---

## Install

```
/plugin marketplace add <owner>/atv-paperboard
/plugin install atv-paperboard@<marketplace>
```

Replace `<owner>` with the GitHub organisation hosting the plugin (e.g. `All-The-Vibes`).

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

3. Alternatively, run the doctor command from a Bash tool:

   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/core/cli.py doctor
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
