# Release Checklist

Audience: maintainer cutting a release. Follow in order. Do not skip steps.

---

## Pre-release

- [ ] All feature work merged to `main`; no open PRs targeting this version
- [ ] `pytest tests/ -q` — all tests pass, zero failures (skipped is acceptable for harness-gated tests)
- [ ] CHANGELOG.md has a dated `[<version>]` section for the version you are releasing — **do not release without it**
- [ ] Version in `pyproject.toml` matches the tag you will create (e.g. `0.1.1`)
- [ ] `git log --oneline -10` — confirm the fix/feature commits are present on `main`

---

## Test PyPI gate

Build and validate the distribution before touching real PyPI.

- [ ] `python -m build` — produces `dist/atv_paperboard-<version>-py3-none-any.whl` and `.tar.gz`; no build errors
- [ ] `twine check dist/*` — passes with no warnings
- [ ] `twine upload --repository testpypi dist/*` — upload succeeds; confirm package appears at `https://test.pypi.org/project/atv-paperboard/`
- [ ] Create a fresh venv: `python -m venv /tmp/testpypi-venv && source /tmp/testpypi-venv/bin/activate`
- [ ] Install from Test PyPI: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ atv-paperboard==<version>`
- [ ] `paperboard doctor` — exits 0, no missing-dependency errors
- [ ] Run the workflow template against a sandbox repo with one issue assigned to Copilot Coding Agent; confirm artifact is written to `paperboard-artifacts/`
- [ ] Deactivate and delete the test venv

> **STOP / ABORT**: If any step in the Test PyPI gate fails, do **not** proceed to real PyPI. Diagnose, fix, bump to the next rc number (e.g. `0.1.1rc2`), update `pyproject.toml` and CHANGELOG, and restart from Pre-release.

---

## Real PyPI publish (Trusted Publishing via GitHub Actions)

PyPI publish is automated. **No twine token, no manual upload.** The `.github/workflows/pypi-publish.yml` workflow triggers on `v*` tag push, uses OIDC to authenticate to PyPI, builds sdist + wheel, runs `twine check`, then publishes.

### One-time PyPI publisher setup

Done once per project, by a PyPI account that owns or will own the `atv-paperboard` project name.

1. Go to https://pypi.org/manage/account/publishing/
2. Add a **Pending publisher** (works even before the project exists — the first publish claims the name):
   - PyPI Project Name: `atv-paperboard`
   - Owner: `All-The-Vibes`
   - Repository name: `ATV-PaperBoard`
   - Workflow filename: `pypi-publish.yml`
   - Environment name: `pypi`
3. On GitHub, create the `pypi` environment under repo Settings → Environments. Optionally add required reviewers — protected environments add a manual-approval gate to every publish, which is recommended for production releases.

### Per-release flow

- [ ] `git tag -a v<version> -m "v<version>"` — annotated tag on the release commit
- [ ] `git push origin v<version>` — this triggers `.github/workflows/pypi-publish.yml`
- [ ] Watch the Actions tab: the workflow checks tag↔pyproject version parity, builds, and publishes to PyPI
- [ ] Confirm at `https://pypi.org/project/atv-paperboard/<version>/`
- [ ] Create a fresh venv: `python -m venv /tmp/pypi-venv && source /tmp/pypi-venv/bin/activate`
- [ ] `pip install atv-paperboard==<version>` — installs from real PyPI without errors
- [ ] `paperboard render --input examples/inputs/build-status.json --no-open --output-dir /tmp/pb-smoke` — render works end-to-end
- [ ] Deactivate and delete the venv

> **If the workflow fails on the version-parity step**: the tag and `pyproject.toml` `version` don't match. Either fix `pyproject.toml` and re-tag, or delete the tag and retag on the correct commit.

---

## Tag and release

The tag push above already triggers PyPI publish. This section just covers the GitHub Release notes.

- [ ] Determine release type:
  - Version has `-rc`, `-preview`, `-alpha`, or `-beta` suffix → `gh release create v<version> --prerelease --notes-file <(...))`
  - Stable version (no suffix) → `gh release create v<version> --notes-file <(...)`
- [ ] Paste the relevant CHANGELOG section as the release notes body
- [ ] Verify the release appears on GitHub with correct tag, assets, and prerelease flag

---

## Post-release

- [ ] Close the `v<version>` milestone on GitHub; confirm all milestone issues are closed or moved
- [ ] Open the next milestone (e.g. `v0.1.2`) on GitHub
- [ ] Update `pyproject.toml` version to the next development version (e.g. `0.1.2.dev0`) and commit as `chore: bump version to 0.1.2.dev0`
- [ ] Announce: post release notes link to relevant channels
