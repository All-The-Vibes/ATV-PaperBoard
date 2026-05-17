# atv-paperboard — Codex CLI Install Guide

Three install paths are provided. Choose the one that matches your setup.

---

## Prerequisites (all paths)

- Codex CLI installed and authenticated
- Python 3.10+ on PATH (`pip install atv-paperboard`)
- Node.js 18+ on PATH plus the `@google/design.md` lint binary:
  ```bash
  npm install -g @google/design.md@0.1.1
  ```
  Without this, design lint silently degrades to a Python fallback. Run
  `paperboard doctor` to confirm `@google/design.md: 0.1.1` and
  `paperboard.DESIGN.md lint: ✓ clean`.

---

## Path A — Recommended: Skill + Hook

Install the skill and register the PostToolUse hook so Codex automatically suggests
rendering when you produce dashboards, comparison tables, or benchmark results.

**Step 1 — Clone the skill:**

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard ~/.agents/skills/atv-paperboard
```

The clone also lands the design authority artifacts that the
`impeccable-design` skill (`skills/impeccable-design/SKILL.md`) reads on
demand: `core/designs/DESIGN-AUTHORITY.md`, the vendored Apache 2.0 reference
files under `core/designs/impeccable-context/`, and the repo-root `NOTICE.md`.
No extra copy step is required for Path A.

**Step 2 — Install Python dependencies:**

```bash
pip install atv-paperboard
```

**Step 3 — Append the hook snippet to `~/.codex/config.toml`:**

```bash
cat adapters/codex/hooks/config.toml.snippet >> ~/.codex/config.toml
```

Or open `~/.codex/config.toml` in your editor and paste the contents of
`adapters/codex/hooks/config.toml.snippet` at the end of the file.

> **Note:** The snippet uses `[[hooks.PostToolUse]]` (array-of-tables) syntax. If you
> already have a `[[hooks.PostToolUse]]` block, the new block is additive — TOML
> array-of-tables allows multiple entries.

---

## Path B — Skill Only (no hook)

Install the skill but skip the config edit. You invoke `paperboard render` manually.

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard ~/.agents/skills/atv-paperboard
pip install atv-paperboard
```

Codex will load the skill's `SKILL.md` automatically from `~/.agents/skills/atv-paperboard/`
on the next session start.

---

## Path C — Fallback (no skill install)

If you cannot or prefer not to use the git-clone install, drop the instructions template
into your global Codex instructions file:

```bash
cat adapters/codex/AGENTS.md.template >> ~/.codex/AGENTS.md
```

This tells Codex to invoke `paperboard render --input <path>` on qualifying structured
output. You still need the `paperboard` CLI on PATH (`pip install atv-paperboard`).

The template includes a `Design authority for .DESIGN.md files` section that
points at `core/designs/DESIGN-AUTHORITY.md` and the vendored
`core/designs/impeccable-context/` reference files. Under Path C those files
are **not** auto-copied — clone the repo separately if you want offline access
to the doctrine, or fetch them from GitHub on demand:

```bash
git clone --depth 1 https://github.com/All-The-Vibes/ATV-PaperBoard ~/.codex/atv-paperboard-doctrine
```

Then update your AGENTS.md paths to point under `~/.codex/atv-paperboard-doctrine/`.

---

## Verify

After any install path, open a new Codex session and run:

```
paperboard doctor
```

Confirm the output includes:

```
harness: codex
```

If it shows `harness: standalone`, the detection heuristics did not find a Codex signal.
Ensure either `CODEX_HOME` is set in your environment or `~/.codex/config.toml` exists.

---

## Persistence

Artifacts are written to:

```
~/.codex/atv-paperboard-artifacts/<date>/<slug>.{html,DESIGN.md,meta.yaml}
```

Codex's git-clone skill install has no equivalent of `${PLUGIN_DATA}` — there is no
documented `CODEX_PLUGIN_DATA` environment variable for skills installed via git clone.
atv-paperboard therefore uses a stable user-scoped path under `~/.codex/` so artifacts
survive Codex upgrades and skill re-installs without migration.

To change the artifact root, set the `PAPERBOARD_ARTIFACT_DIR` environment variable:

```bash
export PAPERBOARD_ARTIFACT_DIR=~/my-artifacts
```

---

## Uninstall

```bash
rm -rf ~/.agents/skills/atv-paperboard
pip uninstall atv-paperboard
```

If you added the hook snippet, remove the `[[hooks.PostToolUse]]` block (and its nested
`[[hooks.PostToolUse.hooks]]` block) from `~/.codex/config.toml`.
