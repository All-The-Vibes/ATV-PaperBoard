# Contributing to atv-paperboard

Thank you for considering a contribution. This guide covers the project layout, dev environment, conventions, and the kinds of contributions that have the highest chance of landing quickly.

If you're new to the project, **read [README.md](README.md) first** — it documents the architecture, the four pillars, the artifact triple, auto-detection, per-harness persistence paths, the hook heuristic, and the integration patterns. Everything below assumes you've skimmed that.

---

## Table of contents

1. [Ground rules](#ground-rules)
2. [Project layout](#project-layout)
3. [Local development setup](#local-development-setup)
4. [Running the test suite](#running-the-test-suite)
5. [Linting and formatting](#linting-and-formatting)
6. [Branching and PRs](#branching-and-prs)
7. [Commit message conventions](#commit-message-conventions)
8. [What goes where](#what-goes-where)
9. [Recipes for common contributions](#recipes-for-common-contributions)
10. [Reporting bugs and security issues](#reporting-bugs-and-security-issues)
11. [License and CLA](#license-and-cla)

---

## Ground rules

- **Be kind, be precise, be brief.** Bug reports and PR descriptions should include enough to reproduce or evaluate — no more.
- **Don't ship what you can't test.** Every code change should come with a passing test or a clear note explaining why one wasn't feasible. The two existing live-harness gates (Claude Code / Codex) are skipped in CI by design.
- **Respect the contract.** The artifact triple (`.html` + `.DESIGN.md` + `.meta.yaml`), the lint behaviour, the auto-detection precedence, and the per-harness persistence paths are load-bearing. Changes to them need a corresponding test and a CHANGELOG entry.
- **No telemetry. No auto-updates. No remote calls at runtime.** These are explicit non-goals (see the README "What's NOT in v0.1.x" section).

---

## Project layout

```
atv-paperboard/
├── core/                # SHARED Python core (harness-agnostic)
│   ├── bridge.py        # node + @google/design.md wrapper
│   ├── render.py        # html generation, tier templates, token-rename
│   ├── validate.py      # google lint + html-side color-trace
│   ├── regenerate.py    # 3-step retry strategy
│   ├── gallery.py       # compounding artifact
│   ├── persist.py       # harness-aware persistence paths
│   ├── detect.py        # auto-detect harness via env + fs heuristics
│   └── cli.py           # `paperboard` standalone CLI (universal entry point)
│
├── skills/              # SHARED SKILL.md payloads (portable across harnesses)
├── adapters/            # per-harness wrappers (~50 LOC each — manifest, hook, install glue)
│   ├── claude-code/
│   ├── codex/
│   └── copilot-cli/
├── recipes/             # CI/workflow recipes for harnesses without a local plugin model
│   └── github-actions/  # Copilot Coding Agent
├── designs/             # default + starters + glass tier
├── templates/           # Jinja2 templates: pico-tier, daisy-tier, gallery
├── examples/            # 3 real artifact triples + gallery (golden-output reference)
└── tests/               # pytest; 130 passing, 2 live-harness gates skipped in CI
```

The same SKILL.md files end up inside Claude Code's `/plugin install`, Codex's `~/.agents/skills/`, and Copilot CLI's `--plugin-dir` via per-adapter build steps. Every adapter and recipe invokes the same `core/cli.py` entry point via subprocess.

---

## Local development setup

Requirements:

- **Python 3.10+** (3.13 used in CI)
- **Node.js 18+** (for `@google/design.md`)
- **Git**

Clone and install:

```bash
git clone https://github.com/All-The-Vibes/ATV-PaperBoard
cd ATV-PaperBoard

# Python in editable mode + dev extras
pip install -e ".[dev]"

# Node deps (pulls @google/design.md@0.1.1 — pinned exact)
npm install
```

Verify the install:

```bash
paperboard doctor          # diagnoses node/python/bridge resolution
pytest tests/ -q           # expect: 130 passed, 2 skipped
```

Optional but recommended for cross-platform parity:

- macOS / Linux: nothing extra.
- Windows: keep using `python` (not `py -3`) so hook commands match the Linux/macOS examples in the docs.

---

## Running the test suite

```bash
pytest tests/ -q
```

Expected baseline: **130 passed, 2 skipped**. The two skipped tests are real-session gates (`harness_claude_code`, `harness_codex`) that require a live agent session and are not run in CI.

### Selecting by marker

| Marker | Scope | Default? |
|---|---|---|
| `phase0` | Cross-harness empirical verification (V1–V6) — requires Node + `@google/design.md` installed | ✅ runs |
| `harness_claude_code` | Tests requiring a real Claude Code session | ⏭ skipped |
| `harness_codex` | Tests requiring a real Codex CLI session | ⏭ skipped |
| `slow` | Tests that take >5 seconds | ✅ runs |

Run a subset:

```bash
pytest -m phase0           # only empirical verification
pytest -m "not slow"       # quick smoke
pytest tests/test_core_validate.py -v
```

### Test fixtures

- `tests/fixtures/compliant/` — DESIGN.md inputs that should lint clean.
- `tests/fixtures/violations/` — DESIGN.md inputs that should produce specific `fail-class` outputs.

When you add a new fail-class, add a paired compliant/violation fixture.

### Live-harness validation (manual, pre-release)

Before tagging a release, the three live adapters should be exercised against real binaries. See the per-adapter `INSTALL.md` for the local-dev `--plugin-dir` flow:

- `adapters/claude-code/INSTALL.md`
- `adapters/codex/INSTALL.md`
- `adapters/copilot-cli/INSTALL.md`

---

## Linting and formatting

Ruff is the only lint/format tool. Config lives in `pyproject.toml`:

```bash
ruff check .               # lint
ruff format .              # format
```

Rules enabled: `E`, `F`, `W`, `I`, `B`, `UP`. `E501` (line length) is intentionally ignored — the formatter handles it. Line length: **100**.

CI runs both `ruff check` and `pytest`. PRs that fail either will be flagged.

---

## Branching and PRs

- **Default branch:** `main`. Releases are tagged from `main` (`v0.1.0-preview`, `v0.1.1`, …).
- **Feature branches:** `feat/<short-slug>` (e.g., `feat/opencode-adapter`).
- **Bug-fix branches:** `fix/<short-slug>` (e.g., `fix/tailwind-flatten-envelope`).
- **Doc-only branches:** `docs/<short-slug>`.

Before opening a PR:

1. Rebase on top of `main` (`git fetch && git rebase origin/main`).
2. Run `ruff check .` and `pytest tests/ -q` locally; both green.
3. Update `CHANGELOG.md` under `[Unreleased]` with a one-liner under the right section (`Added` / `Changed` / `Fixed` / `Removed` / `Deprecated` / `Security` / `Internal`).
4. If your PR touches a load-bearing contract (artifact triple, auto-detect precedence, persistence path, hook semantics), call that out in the PR description with a paragraph explaining the behavioural delta.

PR description checklist (copy/paste into the body):

```
## What
<one-line summary>

## Why
<motivation — link to issue if one exists>

## How
<key implementation choices; anything reviewers should look at first>

## Verification
- [ ] `ruff check .` passes
- [ ] `pytest tests/ -q` passes (130 passed, 2 skipped)
- [ ] CHANGELOG updated under [Unreleased]
- [ ] If touching a load-bearing contract: test added, behavioural delta documented
```

PRs are squash-merged by default. Keep the PR title in [Conventional Commits](#commit-message-conventions) format because it becomes the merge commit message.

---

## Commit message conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/) v1.0.0:

```
<type>(<scope>): <imperative summary>

<optional body — wrap at 72 cols, explain the why, not the what>

<optional trailers>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Scopes used in this repo: `core`, `render`, `validate`, `persist`, `detect`, `gallery`, `bridge`, `cli`, `claude-code`, `codex`, `copilot-cli`, `gh-actions`, `designs`, `templates`, `tests`, `docs`, `readme`, `changelog`, `gitignore`, `deps`.

Examples:

```
feat(copilot-cli): add native plugin adapter with postToolUse hook
fix(render): unwrap theme.extend envelope in tailwind export
docs(readme): fold spec content into single source of truth
chore(deps): bump @google/design.md to 0.1.2
```

### Co-author trailer for AI-assisted commits

If a commit was authored with substantial assistance from GitHub Copilot CLI (or any other Copilot surface), include the co-author trailer at the bottom of the message:

```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

This is the same trailer GitHub uses for Coding Agent commits. It's optional for fully human-authored commits.

---

## What goes where

This is the most common source of confusion. A quick cheat-sheet:

| Add this | Put it here | Why |
|---|---|---|
| New rendering logic (template, tier, token-rename rule) | `core/render.py` + `templates/*.html.j2` | Harness-agnostic; never duplicate per-adapter |
| New lint rule | `core/validate.py` | Must produce a `fail-class` consumable by `regenerate.py` |
| New harness-aware path | `core/persist.py` AND `core/detect.py` | Both files must agree |
| New `paperboard` subcommand | `core/cli.py` | Resolve harness first, then route |
| New harness wrapper (manifest / hook / agent) | `adapters/<harness>/` | ~50 LOC of glue; no logic duplicated from `core/` |
| New CI / workflow template | `recipes/<surface>/` | For harnesses without a local plugin model |
| Cross-harness skill payload | `skills/<skill>/SKILL.md` | Authored once, copied into adapters at build time |
| New design starter | `designs/starters/<brand>-inspired.DESIGN.md` | **Must** include the `attribution:` frontmatter — see the recipe below |
| New example artifact | `examples/inputs/<name>.json` + run `paperboard render --input` to populate `examples/output/` | Golden-output reference for tests + README links |
| Test for `core/` | `tests/test_core_<module>.py` | Mark `phase0` if it needs Node + `@google/design.md` |
| Test for an adapter | `tests/test_adapter_<harness>.py` | Mark `harness_<name>` if it needs a real session |

---

## Recipes for common contributions

### Add a new harness adapter

Estimated effort: ~90 min if the harness's plugin model is documented and reachable from a local install. Most of the time goes into empirical verification (selectors, env vars, exit-code semantics), not code.

1. **Empirical verification first.** Before writing any code, verify the harness's plugin layout against its live docs and (if possible) a real install. Document any deltas from the docs in a short note in your PR. The Copilot CLI adapter's "fail-open hooks" caveat is the canonical example of an empirically-discovered constraint.
2. **Detection signal** — add a branch in `core/detect.py` that prefers env-var signals over filesystem heuristics. Document the precedence rationale.
3. **Persistence path** — add a branch in `core/persist.py`. Use the harness's documented user-scoped data directory; never write to the plugin root if the harness cleans it on update.
4. **Adapter directory** — create `adapters/<harness>/` with:
    - `INSTALL.md` covering both local-dev (`--plugin-dir` or similar) and marketplace install flows.
    - Whatever manifest / hook config / agent file the harness requires. Keep it under 50 LOC of glue if possible.
    - A `build.py` if the adapter needs file-copy or symlink steps to assemble its install directory.
5. **Tests** — add `tests/test_adapter_<harness>.py` covering at minimum: detect-harness returns the right value when the harness's env vars are present; persist resolves to the right path; the hook payload (if any) is parsed correctly.
6. **Docs** — README install section + a row in the "Where it runs" table + the "Per-harness persistence paths" table.
7. **CHANGELOG** — entry under `[Unreleased] / Added`.

### Add a new design starter

1. Pick a brand whose public design impressions you can credibly reverse-engineer. **No verbatim copies; no trademark assertions.**
2. Use the hyphenated `-inspired` naming: `stripi-inspired.DESIGN.md`, `lin-ear-inspired.DESIGN.md`. The hyphenation is **not** a trademark-evasion tactic — it's an explicit signal that this is an interpretation. Pair it with the `not_affiliated_with` field below.
3. Place it in `designs/starters/<name>-inspired.DESIGN.md` with the required `attribution:` frontmatter:

```yaml
---
attribution:
  inspired_by: "<Brand>"                    # the brand name (hyphenated form preserved)
  not_affiliated_with: "<Legal Entity>"     # explicit non-affiliation
  source_repo: "VoltAgent/awesome-design-md"
  source_path: "design-md/<brand>/DESIGN.md"
  source_commit: "<full SHA at import time>"
  source_license: "MIT"
  redistributed_under: "Apache-2.0"          # this project's license
  imported_at: "YYYY-MM-DD"
  notes: |
    Tokens reverse-engineered from public brand impressions; not a verbatim copy.
    No trademark license claimed.
---
```

4. Run `pytest tests/test_starter_attribution.py` — the public-release blocker test will fail if any required key is missing.
5. Render a sample artifact with `--design <name>-inspired` and check the lint passes.
6. CHANGELOG entry under `[Unreleased] / Added`.

### Add a new CLI subcommand

1. Implement the logic in the relevant `core/<module>.py`. Do not put business logic in `core/cli.py` itself.
2. Add the subcommand to `core/cli.py`. Always call `detect_harness()` first if persistence is involved.
3. Add unit tests in `tests/test_core_cli.py` covering happy path + at least one error case.
4. Document the subcommand in the README's "CLI surface" section.

### Debug a lint failure

`paperboard validate <slug>` outputs a structured `fail-class`. The most common ones:

- `color-not-in-contract` — the HTML uses a color that isn't declared as a token in the DESIGN.md.
- `broken-token-ref` — the DESIGN.md references a token alias (e.g., `{colors.primary}`) that doesn't resolve.
- `missing-sections` — the DESIGN.md is missing a required section per the Google spec.
- `missing-typography` — the DESIGN.md declares no type scale.

For deeper debugging:

```bash
# Run the upstream Google CLI directly, JSON output
node node_modules/@google/design.md/dist/index.js lint --format json path/to.DESIGN.md
```

Compare the upstream output to `core/validate.py`'s post-processing.

---

## Reporting bugs and security issues

### Bugs

Open an issue at <https://github.com/All-The-Vibes/ATV-PaperBoard/issues> with:

- What you ran (`paperboard ...` command + flags)
- What you expected
- What you got (full stderr, not a paraphrase)
- Your environment (`paperboard doctor` output is ideal — it includes Python / Node / `@google/design.md` / detected harness)
- A minimal repro if possible (a fixture DESIGN.md + an input JSON)

### Security issues

**Do not open a public issue for security vulnerabilities.** Email the maintainers privately at the address in the repo's GitHub profile, or use [GitHub's private vulnerability reporting](https://github.com/All-The-Vibes/ATV-PaperBoard/security/advisories/new).

In particular: if you find a path traversal, command injection, or template injection in the CLI or any adapter, treat it as a security issue. The threat model assumes a hostile DESIGN.md input is possible (e.g., a future `--design <url>` flag that pulls a remote DESIGN.md).

---

## License and CLA

- This project is licensed under [Apache-2.0](LICENSE).
- **No CLA.** Inbound = outbound: by submitting a PR, you agree your contribution is licensed under Apache-2.0.
- `@google/design.md@0.1.1` (pinned dev dep) is Apache-2.0.
- Starter designs in `designs/starters/` carry per-file `attribution:` frontmatter; the redistribution license is Apache-2.0 across the board.

Welcome aboard, and thanks for the help.
