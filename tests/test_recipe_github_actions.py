"""tests/test_recipe_github_actions.py — Validate GitHub Actions recipe files."""
from __future__ import annotations

from pathlib import Path

import yaml

_RECIPES_DIR = Path(__file__).parent.parent / "recipes" / "github-actions"


def test_workflow_yml_template_parses_as_yaml():
    """workflow.yml.template must be valid YAML."""
    template_path = _RECIPES_DIR / "workflow.yml.template"
    assert template_path.exists(), f"Missing: {template_path}"
    content = template_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    assert parsed is not None, "Parsed YAML is empty"
    assert isinstance(parsed, dict), "Parsed YAML is not a mapping"


def test_copilot_instructions_non_empty_and_contains_render():
    """copilot-instructions.md.template must exist, be non-empty, and mention 'paperboard render'."""
    template_path = _RECIPES_DIR / "copilot-instructions.md.template"
    assert template_path.exists(), f"Missing: {template_path}"
    content = template_path.read_text(encoding="utf-8")
    assert content.strip(), "copilot-instructions.md.template is empty"
    assert "paperboard render" in content, \
        "copilot-instructions.md.template must contain the literal 'paperboard render'"


def test_workflow_has_required_steps():
    """workflow.yml.template must include checkout, setup-node, and setup-python steps."""
    template_path = _RECIPES_DIR / "workflow.yml.template"
    parsed = yaml.safe_load(template_path.read_text(encoding="utf-8"))

    # Collect all step 'uses' values across all jobs
    uses_values: list[str] = []
    jobs = parsed.get("jobs", {})
    for job in jobs.values():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses:
                uses_values.append(uses)

    checkout_steps = [u for u in uses_values if u.startswith("actions/checkout")]
    setup_node_steps = [u for u in uses_values if u.startswith("actions/setup-node")]
    setup_python_steps = [u for u in uses_values if u.startswith("actions/setup-python")]

    assert checkout_steps, "Workflow must include an actions/checkout step"
    assert setup_node_steps, "Workflow must include an actions/setup-node step"
    assert setup_python_steps, "Workflow must include an actions/setup-python step"
