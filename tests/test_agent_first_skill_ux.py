"""Agent-first PaperBoard skill UX regression tests."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
PAPERBOARD_SKILL = REPO_ROOT / "skills" / "paperboard" / "SKILL.md"
ROOT_SKILL = REPO_ROOT / "SKILL.md"
RENDER_ARTIFACT_SKILL = REPO_ROOT / "skills" / "render-artifact" / "SKILL.md"
CODEX_AGENTS_TEMPLATE = REPO_ROOT / "adapters" / "codex" / "AGENTS.md.template"
ADAPTER_DIST_SKILLS = [
    REPO_ROOT / "adapters" / "claude-code" / "_dist" / "skills" / "paperboard" / "SKILL.md",
    REPO_ROOT / "adapters" / "copilot-cli" / "_dist" / "skills" / "paperboard" / "SKILL.md",
]


def _skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    end = text.find("\n---\n", 4)
    assert end != -1, f"{path} frontmatter must close with ---"
    return yaml.safe_load(text[4:end]) or {}


def test_agent_first_paperboard_skill_exists_with_user_facing_name() -> None:
    assert PAPERBOARD_SKILL.exists(), "Expected an umbrella /paperboard skill"

    frontmatter = _skill_frontmatter(PAPERBOARD_SKILL)
    assert frontmatter["name"] == "paperboard"
    assert "agent" in frontmatter["description"].lower()


def test_repo_root_skill_supports_codex_git_clone_install() -> None:
    """Codex git-clone install loads the skill from repo-root SKILL.md."""
    assert ROOT_SKILL.exists(), "Expected root SKILL.md for Codex git-clone skill install"

    frontmatter = _skill_frontmatter(ROOT_SKILL)
    assert frontmatter["name"] == "paperboard"
    assert "/paperboard <path> [--style paperboard|meridian|atv]" in ROOT_SKILL.read_text(
        encoding="utf-8"
    )


def test_adapter_dists_include_agent_first_paperboard_skill() -> None:
    for skill_path in ADAPTER_DIST_SKILLS:
        assert skill_path.exists(), f"Adapter dist missing /paperboard skill: {skill_path}"
        frontmatter = _skill_frontmatter(skill_path)
        assert frontmatter["name"] == "paperboard"


def test_paperboard_skill_documents_agent_command_style_flags() -> None:
    text = PAPERBOARD_SKILL.read_text(encoding="utf-8")

    expected_examples = [
        "/paperboard path/to/file.md",
        "/paperboard path/to/proposal.md --style meridian",
        "/paperboard path/to/report.json --style atv",
        "/paperboard styles",
        "/paperboard gallery",
    ]
    for example in expected_examples:
        assert example in text

    assert "paperboard render --input <path> --style <style>" in text
    assert "default" in text.lower()
    assert "paperboard" in text
    assert "meridian" in text
    assert "atv" in text


def test_low_level_render_skill_points_agents_to_paperboard_skill() -> None:
    text = RENDER_ARTIFACT_SKILL.read_text(encoding="utf-8")

    assert "/paperboard" in text
    assert "preferred" in text.lower()
    assert "low-level" in text.lower()


def test_readme_leads_with_agent_first_usage_before_standalone_cli() -> None:
    text = README.read_text(encoding="utf-8")

    agent_heading = text.index("## Agent-first usage")
    standalone_heading = text.index("## Quick start (standalone")
    assert agent_heading < standalone_heading

    assert "/paperboard path/to/file.md" in text
    assert "/paperboard path/to/proposal.md --style meridian" in text
    assert "The CLI is the engine" in text


def test_readme_correctly_describes_copilot_cli_manifest() -> None:
    text = README.read_text(encoding="utf-8")

    assert "There is no `plugin.json`" not in text
    assert "`plugin.json`" in text
    assert re.search(r"Copilot CLI adapter.*`plugin\.json`", text, re.DOTALL)


def test_codex_fallback_template_uses_agent_first_paperboard_command() -> None:
    text = CODEX_AGENTS_TEMPLATE.read_text(encoding="utf-8")

    assert "/paperboard <path> [--style paperboard|meridian|atv]" in text
    assert "/paperboard path/to/proposal.md --style meridian" in text
    assert "paperboard render --input <path> --style <style>" in text
