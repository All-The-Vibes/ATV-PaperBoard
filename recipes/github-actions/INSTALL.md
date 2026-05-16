# ${repo} — Paperboard CI Setup

Wire `atv-paperboard` into your GitHub repository so every PR that touches
`paperboard-artifacts/` is validated and the gallery is rebuilt automatically.

## Steps

### 1. Copy workflow

```bash
cp recipes/github-actions/workflow.yml.template .github/workflows/paperboard.yml
```

Edit `paperboard.yml` and replace `${repo}` with your repository slug if needed.

### 2. Copy Copilot instructions

```bash
cp recipes/github-actions/copilot-instructions.md.template .github/copilot-instructions.md
```

This tells GitHub Copilot Coding Agent when to invoke `paperboard render`.

### 3. Enable Copilot Coding Agent (repo settings)

1. Go to **Settings → Copilot → Coding agent**.
2. Enable the agent for this repository.
3. The default tier is `atv` (dark designed-document) — recommended for dashboards and reports. Optionally set `PAPERBOARD_TIER=pico` (or `daisy`) as a repo secret only if your audience explicitly wants a light, framework-styled document.

### 4. Commit and push

```bash
git add .github/
git commit -m "chore: add paperboard CI + Copilot instructions"
git push
```

### 5. Verify

Open a PR that adds or modifies a file in `paperboard-artifacts/`.
The `Paperboard Validate` workflow should trigger and report pass/fail per artifact.

## References

- [GitHub Copilot Coding Agent docs](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent-to-work-on-tasks)
- [atv-paperboard on PyPI](https://pypi.org/project/atv-paperboard/)
- [paperboard.DESIGN.md spec](../../designs/paperboard.DESIGN.md)
