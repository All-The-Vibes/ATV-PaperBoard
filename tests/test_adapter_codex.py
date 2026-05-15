"""
tests/test_adapter_codex.py

Regression tests for adapters/codex/ — verifies that SPEC v4.1 corrections are in place
and guards against re-introducing the v4 bugs:
  - openai.yaml: `allowed_tools` field (undocumented; removed in v4.1)
  - config.toml.snippet: `[hooks.PostToolUse]` single-table syntax (must be array-of-tables)
  - config.toml.snippet: `match.tool` dotted key (must be `matcher` regex string)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths (absolute, resolved relative to this file's location)
# ---------------------------------------------------------------------------
ADAPTER_DIR = Path(__file__).parent.parent / "adapters" / "codex"
OPENAI_YAML = ADAPTER_DIR / "agents" / "openai.yaml"
TOML_SNIPPET = ADAPTER_DIR / "hooks" / "config.toml.snippet"
AGENTS_TEMPLATE = ADAPTER_DIR / "AGENTS.md.template"


# ---------------------------------------------------------------------------
# TOML import — prefer stdlib tomllib (3.11+), fall back to tomli
# ---------------------------------------------------------------------------
def _load_toml(text: str) -> dict:
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ModuleNotFoundError:
        pass
    try:
        import tomli  # type: ignore[import]
        return tomli.loads(text)
    except ModuleNotFoundError:
        pytest.skip("Neither tomllib nor tomli is available; skipping TOML tests")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _strip_toml_comments(text: str) -> str:
    """Remove comment lines so we can parse the snippet as valid TOML."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# openai.yaml tests
# ---------------------------------------------------------------------------
class TestOpenAIYaml:
    def test_file_exists(self):
        assert OPENAI_YAML.exists(), f"Missing: {OPENAI_YAML}"

    def test_parses_cleanly(self):
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
        assert isinstance(data, dict), "openai.yaml must parse to a dict"

    def test_has_interface_key(self):
        """SPEC v4.1 requires top-level `interface:` key (regression: v4 had `allowed_tools`)."""
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
        assert "interface" in data, "openai.yaml must have top-level 'interface' key"

    def test_has_policy_key(self):
        """SPEC v4.1 requires top-level `policy:` key."""
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
        assert "policy" in data, "openai.yaml must have top-level 'policy' key"

    def test_no_allowed_tools_field(self):
        """Regression: SPEC v4 had `allowed_tools: [...]` which is undocumented in openai.yaml."""
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
        assert "allowed_tools" not in data, (
            "openai.yaml must NOT have 'allowed_tools' — that field is undocumented "
            "in the Codex openai.yaml schema (SPEC v4 bug, fixed in v4.1)"
        )

    def test_interface_has_display_name(self):
        data = yaml.safe_load(OPENAI_YAML.read_text(encoding="utf-8"))
        assert "display_name" in data.get("interface", {}), (
            "openai.yaml interface block must include 'display_name'"
        )


# ---------------------------------------------------------------------------
# config.toml.snippet tests
# ---------------------------------------------------------------------------
class TestConfigTomlSnippet:
    def _text(self) -> str:
        return TOML_SNIPPET.read_text(encoding="utf-8")

    def test_file_exists(self):
        assert TOML_SNIPPET.exists(), f"Missing: {TOML_SNIPPET}"

    def test_parses_cleanly(self):
        """Snippet must be valid TOML after stripping comment lines."""
        text = _strip_toml_comments(self._text())
        data = _load_toml(text)
        assert isinstance(data, dict)

    def test_uses_array_of_tables_syntax(self):
        """Regression: SPEC v4 used `[hooks.PostToolUse]` (single table) — wrong.
        Correct syntax is `[[hooks.PostToolUse]]` (array-of-tables)."""
        raw = self._text()
        # Must contain double-bracket form
        assert "[[hooks.PostToolUse]]" in raw, (
            "config.toml.snippet must use [[hooks.PostToolUse]] array-of-tables syntax "
            "(SPEC v4 bug: used single-table [hooks.PostToolUse])"
        )
        # Must NOT contain the single-table form (would be a regression)
        single_table_lines = [
            ln for ln in raw.splitlines()
            if re.match(r"^\[hooks\.PostToolUse\]$", ln.strip())
        ]
        assert not single_table_lines, (
            "config.toml.snippet must NOT contain [hooks.PostToolUse] single-table syntax"
        )

    def test_matcher_is_regex_string(self):
        """Regression: SPEC v4 used `match.tool = \"Write\"` (dotted key) — wrong.
        Correct field is `matcher = \"...\"` with a regex value."""
        text = _strip_toml_comments(self._text())
        data = _load_toml(text)

        hooks_list = data.get("hooks", {}).get("PostToolUse", [])
        assert hooks_list, "hooks.PostToolUse must be a non-empty list after TOML parse"

        # Find the entry with a `matcher` field
        matchers = [entry.get("matcher") for entry in hooks_list if "matcher" in entry]
        assert matchers, (
            "At least one [[hooks.PostToolUse]] entry must have a 'matcher' key "
            "(SPEC v4 bug: used 'match.tool' dotted key instead)"
        )

        for m in matchers:
            assert isinstance(m, str), f"matcher value must be a string, got {type(m)}"
            # Verify it compiles as a regex
            try:
                re.compile(m)
            except re.error as exc:
                pytest.fail(f"matcher '{m}' is not a valid regex: {exc}")

    def test_no_match_tool_dotted_key(self):
        """Regression: SPEC v4 had `match.tool = \"Write\"` — dotted key, wrong field."""
        raw = self._text()
        # Only check non-comment lines (comments may reference the bug for documentation)
        non_comment_lines = [
            ln for ln in raw.splitlines() if not ln.strip().startswith("#")
        ]
        non_comment_text = "\n".join(non_comment_lines)
        assert "match.tool" not in non_comment_text, (
            "config.toml.snippet must NOT use 'match.tool' in TOML keys (SPEC v4 bug) — use 'matcher'"
        )


# ---------------------------------------------------------------------------
# AGENTS.md.template tests
# ---------------------------------------------------------------------------
class TestAgentsMdTemplate:
    def _text(self) -> str:
        return AGENTS_TEMPLATE.read_text(encoding="utf-8")

    def test_file_exists(self):
        assert AGENTS_TEMPLATE.exists(), f"Missing: {AGENTS_TEMPLATE}"

    def test_non_empty(self):
        assert self._text().strip(), "AGENTS.md.template must not be empty"

    def test_contains_paperboard_render(self):
        """Template must instruct Codex to invoke `paperboard render`."""
        assert "paperboard render" in self._text(), (
            "AGENTS.md.template must contain the literal string 'paperboard render'"
        )
