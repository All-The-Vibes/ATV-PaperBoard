"""tests/test_impeccable_integration.py — Validate impeccable doctrine integration.

Covers the SPEC-impeccable-2026-05-16 acceptance criteria:

1. All 7 impeccable reference files vendored verbatim under
   `core/designs/impeccable-context/`.
2. `LICENSE-APACHE-2.0` + `UPSTREAM.md` accompany the vendored files.
3. Root `NOTICE.md` attributes pbakaus/impeccable under Apache-2.0.
4. `core/designs/DESIGN-AUTHORITY.md` exists and cites the pinned upstream SHA.
5. `core/designs/glass.DESIGN.md` is hard-retired (does not exist).
6. `skills/impeccable-design/SKILL.md` exists with valid YAML frontmatter.
7. Both shipped adapter `_dist/` trees mirror the impeccable artifacts.
8. `adapters/codex/AGENTS.md.template` includes the Design authority block.
9. `recipes/github-actions/copilot-instructions.md.template` includes
   the Design authority block.

Failures here mean the doctrine import is incomplete — DO NOT release.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent

IMPECCABLE_DIR = REPO_ROOT / "core" / "designs" / "impeccable-context"
DESIGNS_DIR = REPO_ROOT / "core" / "designs"
SKILL_PATH = REPO_ROOT / "skills" / "impeccable-design" / "SKILL.md"
NOTICE_PATH = REPO_ROOT / "NOTICE.md"
AUTHORITY_PATH = DESIGNS_DIR / "DESIGN-AUTHORITY.md"

PINNED_SHA = "4af581e23f17d112d8f9d6b7a5b7ff37823494e1"

VENDORED_FILES = [
    "typography.md",
    "color-and-contrast.md",
    "spatial-design.md",
    "motion-design.md",
    "interaction-design.md",
    "responsive-design.md",
    "ux-writing.md",
]

ADAPTER_DIST_ROOTS = [
    REPO_ROOT / "adapters" / "claude-code" / "_dist",
    REPO_ROOT / "adapters" / "copilot-cli" / "_dist",
]


# ---------------------------------------------------------------------------
# 1. Vendored impeccable reference files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", VENDORED_FILES)
def test_impeccable_reference_files_vendored(fname: str) -> None:
    """Each of the 7 doctrinal references must exist and be non-empty."""
    path = IMPECCABLE_DIR / fname
    assert path.exists(), f"Missing vendored impeccable file: {path}"
    assert path.stat().st_size > 0, f"Vendored impeccable file is empty: {path}"


# ---------------------------------------------------------------------------
# 2. License + upstream provenance
# ---------------------------------------------------------------------------

def test_impeccable_license_present() -> None:
    """LICENSE-APACHE-2.0 must accompany the vendored files and contain the Apache 2.0 header."""
    license_path = IMPECCABLE_DIR / "LICENSE-APACHE-2.0"
    assert license_path.exists(), f"Missing: {license_path}"
    text = license_path.read_text(encoding="utf-8")
    assert "Apache License" in text and "Version 2.0" in text, (
        "LICENSE-APACHE-2.0 does not contain the Apache 2.0 license header"
    )


def test_impeccable_upstream_pins_sha() -> None:
    """UPSTREAM.md must pin the upstream commit SHA we vendored from."""
    upstream_path = IMPECCABLE_DIR / "UPSTREAM.md"
    assert upstream_path.exists(), f"Missing: {upstream_path}"
    text = upstream_path.read_text(encoding="utf-8")
    assert PINNED_SHA in text, (
        f"UPSTREAM.md does not pin the expected impeccable commit {PINNED_SHA}"
    )


# ---------------------------------------------------------------------------
# 3. Root NOTICE.md attribution
# ---------------------------------------------------------------------------

def test_root_notice_attributes_impeccable() -> None:
    """Root NOTICE.md must attribute pbakaus/impeccable under Apache 2.0."""
    assert NOTICE_PATH.exists(), f"Missing: {NOTICE_PATH}"
    text = NOTICE_PATH.read_text(encoding="utf-8")
    assert "pbakaus/impeccable" in text, "NOTICE.md does not reference pbakaus/impeccable"
    assert "Apache License" in text or "Apache-2.0" in text or "Apache 2.0" in text, (
        "NOTICE.md does not reference the Apache 2.0 license"
    )


# ---------------------------------------------------------------------------
# 4. DESIGN-AUTHORITY.md
# ---------------------------------------------------------------------------

def test_design_authority_exists_and_cites_pinned_sha() -> None:
    """DESIGN-AUTHORITY.md must exist and reference the pinned impeccable SHA."""
    assert AUTHORITY_PATH.exists(), f"Missing: {AUTHORITY_PATH}"
    text = AUTHORITY_PATH.read_text(encoding="utf-8")
    assert PINNED_SHA in text, (
        f"DESIGN-AUTHORITY.md does not cite pinned impeccable commit {PINNED_SHA}"
    )


# ---------------------------------------------------------------------------
# 5. Glass tier hard-retired
# ---------------------------------------------------------------------------

def test_glass_tier_hard_retired() -> None:
    """core/designs/glass.DESIGN.md must NOT exist; glass tier is retired."""
    glass_path = DESIGNS_DIR / "glass.DESIGN.md"
    assert not glass_path.exists(), (
        f"glass.DESIGN.md still exists at {glass_path} — should be hard-retired"
    )


def test_atv_tier_has_no_glassmorphism_prescription() -> None:
    """atv.DESIGN.md must not prescribe `backdrop-filter: blur` as a Do.

    A reference to the banned property inside an audit comment or Don't list
    is allowed; an unqualified prescription is not.
    """
    atv_path = DESIGNS_DIR / "atv.DESIGN.md"
    text = atv_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if "backdrop-filter" not in stripped:
            continue
        # Allow audit comments and explicit bans (Don't lines, negative phrasing).
        if stripped.startswith("<!--"):
            continue
        if stripped.lower().startswith(("- don't", "- do not", "- no ", "**don't")):
            continue
        if "no `backdrop-filter`" in stripped.lower() or "banned" in stripped.lower():
            continue
        pytest.fail(
            f"atv.DESIGN.md prescribes glassmorphism (line: {stripped!r}); "
            "must not appear outside audit comments or Don't lists."
        )


# ---------------------------------------------------------------------------
# 6. Paperboard-owned skill source
# ---------------------------------------------------------------------------

def test_impeccable_design_skill_exists_with_frontmatter() -> None:
    """skills/impeccable-design/SKILL.md must exist with a valid `name` frontmatter key."""
    assert SKILL_PATH.exists(), f"Missing: {SKILL_PATH}"
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md missing YAML frontmatter (--- delimiters)"
    fm = yaml.safe_load(match.group(1)) or {}
    assert fm.get("name") == "impeccable-design", (
        f"SKILL.md frontmatter `name` must be 'impeccable-design', got {fm.get('name')!r}"
    )
    assert "description" in fm and str(fm["description"]).strip(), (
        "SKILL.md frontmatter must include a non-empty `description`"
    )


# ---------------------------------------------------------------------------
# 7. Adapter _dist mirrors
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dist_root", ADAPTER_DIST_ROOTS, ids=lambda p: p.parent.name)
def test_adapter_dist_mirrors_impeccable_artifacts(dist_root: Path) -> None:
    """Shipped adapter _dist trees must mirror impeccable doctrine artifacts.

    Each of the 3 build-based adapters (claude-code, copilot-cli) bundles:
      - skills/impeccable-design/SKILL.md
      - core/designs/DESIGN-AUTHORITY.md
      - core/designs/impeccable-context/typography.md  (proxy for vendored dir)
      - NOTICE.md
    """
    required = [
        dist_root / "skills" / "impeccable-design" / "SKILL.md",
        dist_root / "core" / "designs" / "DESIGN-AUTHORITY.md",
        dist_root / "core" / "designs" / "impeccable-context" / "typography.md",
        dist_root / "NOTICE.md",
    ]
    missing = [p for p in required if not p.exists()]
    assert not missing, (
        f"{dist_root.parent.name} adapter _dist missing mirrored artifacts: "
        + ", ".join(str(p.relative_to(dist_root)) for p in missing)
    )


# ---------------------------------------------------------------------------
# 8. Codex template injection
# ---------------------------------------------------------------------------

def test_codex_template_contains_design_authority_block() -> None:
    """adapters/codex/AGENTS.md.template must include the Design authority section."""
    template_path = REPO_ROOT / "adapters" / "codex" / "AGENTS.md.template"
    assert template_path.exists(), f"Missing: {template_path}"
    text = template_path.read_text(encoding="utf-8")
    assert "Design authority" in text, (
        "Codex AGENTS.md.template missing the Design authority block"
    )
    assert "impeccable-design" in text or "DESIGN-AUTHORITY.md" in text, (
        "Codex AGENTS.md.template must reference impeccable-design skill or DESIGN-AUTHORITY.md"
    )


# ---------------------------------------------------------------------------
# 9. Coding-Agent recipe injection
# ---------------------------------------------------------------------------

def test_coding_agent_recipe_contains_design_authority_block() -> None:
    """The Coding-Agent recipe template must include the Design authority block."""
    template_path = (
        REPO_ROOT / "recipes" / "github-actions" / "copilot-instructions.md.template"
    )
    assert template_path.exists(), f"Missing: {template_path}"
    text = template_path.read_text(encoding="utf-8")
    assert "Design authority" in text, (
        "Coding-Agent recipe template missing the Design authority block"
    )
    assert "impeccable" in text.lower(), (
        "Coding-Agent recipe template must reference the impeccable doctrine"
    )
