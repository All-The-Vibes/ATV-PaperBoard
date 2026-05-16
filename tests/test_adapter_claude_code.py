"""
tests/test_adapter_claude_code.py

Regression tests for adapters/claude-code/:
  - plugin.json parses and has required fields
  - hooks/hooks.json has outer "hooks" wrapper (regression on SPEC v4 bug)
  - hooks/hooks.json timeout is ≤ 60 seconds (regression on SPEC v4 2000ms bug)
  - §16 heuristic: 5 Write inputs → only the status dashboard fires the hook
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ADAPTER_DIR = Path(__file__).parent.parent / "adapters" / "claude-code"
PLUGIN_JSON = ADAPTER_DIR / ".claude-plugin" / "plugin.json"
HOOKS_JSON = ADAPTER_DIR / "hooks" / "hooks.json"

# Add repo root to sys.path so we can import core.cli directly
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# plugin.json tests
# ---------------------------------------------------------------------------

class TestPluginJson:
    def test_parses(self):
        assert PLUGIN_JSON.exists(), f"plugin.json not found at {PLUGIN_JSON}"
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_has_name(self):
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        assert "name" in data, "plugin.json must have 'name' field"
        assert data["name"] == "atv-paperboard"

    def test_optional_fields_present(self):
        """Spec §2.1 recommends version, description, license, homepage."""
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        for field in ("version", "description", "license", "homepage"):
            assert field in data, f"plugin.json missing recommended field: {field}"


# ---------------------------------------------------------------------------
# hooks/hooks.json tests
# ---------------------------------------------------------------------------

class TestHooksJson:
    def _load(self) -> dict:
        assert HOOKS_JSON.exists(), f"hooks.json not found at {HOOKS_JSON}"
        return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))

    def test_parses(self):
        data = self._load()
        assert isinstance(data, dict)

    def test_outer_hooks_wrapper(self):
        """Regression: SPEC v4 was missing the outer 'hooks' key."""
        data = self._load()
        assert "hooks" in data, (
            "hooks.json MUST have an outer 'hooks' wrapper key "
            "(SPEC v4.1 §2.1 correction; source: deep-research stage 2)"
        )

    def test_post_tool_use_present(self):
        data = self._load()
        assert "PostToolUse" in data["hooks"], "hooks.hooks must have PostToolUse"

    def test_timeout_lte_60_seconds(self):
        """Regression: SPEC v4 wrote 2000 (≈33 minutes). Corrected to 2 seconds."""
        data = self._load()
        post = data["hooks"]["PostToolUse"]
        for entry in post:
            for hook in entry.get("hooks", []):
                timeout = hook.get("timeout")
                if timeout is not None:
                    assert timeout <= 60, (
                        f"hooks.json timeout {timeout} exceeds 60 seconds "
                        "(SPEC v4 bug: 2000 was interpreted as seconds not ms)"
                    )

    def test_matcher_is_write(self):
        data = self._load()
        post = data["hooks"]["PostToolUse"]
        matchers = [e.get("matcher") for e in post]
        assert "Write" in matchers, "PostToolUse must include a 'Write' matcher"

    def test_command_references_cli(self):
        data = self._load()
        post = data["hooks"]["PostToolUse"]
        for entry in post:
            if entry.get("matcher") == "Write":
                for hook in entry.get("hooks", []):
                    cmd = hook.get("command", "")
                    # Hook invokes the PyPI-installed `paperboard` binary
                    # directly (previously: `python ... core/cli.py`).
                    assert "paperboard" in cmd, "hook command should reference the paperboard binary"
                    assert "detect-artifact-candidate" in cmd


# ---------------------------------------------------------------------------
# §16 heuristic tests
# ---------------------------------------------------------------------------

# Five synthetic Write "outputs" (paths or content strings) used as inputs to
# detect-artifact-candidate.  Only the status dashboard should fire the hook.

TASK_LIST_MD = """\
# TODO

| Task | Done |
|------|------|
| Write tests | [ ] |
| Review PR  | [x] |
| Deploy     | [ ] |
"""

COMPARISON_NO_NUMBERS_MD = """\
# Framework Comparison

| Feature     | Framework A | Framework B |
|-------------|-------------|-------------|
| Hot reload  | Yes         | No          |
| TypeScript  | Yes         | Yes         |
| Plugin API  | Limited     | Full        |
"""

STATUS_DASHBOARD_MD = """\
# CI Status Dashboard

| Job        | Status  | Duration |
|------------|---------|----------|
| unit-tests | pass    | 42s      |
| lint       | fail    | 3s       |
| deploy     | pending | -        |
"""

README_EXCERPT_MD = """\
# atv-paperboard

A cross-harness HTML artifact toolkit.

| Pillar   | What it does              |
|----------|---------------------------|
| Enforce  | Validates DESIGN.md       |
| Render   | Serves HTML over loopback |
"""

# The fifth input is a path under the artifact_dir — self-recursion guard.
# We'll resolve this dynamically in the test.


class TestHookHeuristic:
    """Tests for SPEC §16 heuristic rules in core/cli._has_data_table and
    the full detect-artifact-candidate filter chain."""

    def _has_data_table(self, content: str) -> bool:
        from core.cli import _has_data_table
        return _has_data_table(content)

    # -- Rule 1: numeric-or-status column requirement --

    def test_task_list_no_fire(self):
        """Task list (checkbox column) does NOT have numeric/status header → skip."""
        assert not self._has_data_table(TASK_LIST_MD)

    def test_comparison_no_numbers_no_fire(self):
        """Comparison table with no numeric cells and no status header → skip."""
        assert not self._has_data_table(COMPARISON_NO_NUMBERS_MD)

    def test_status_dashboard_fires(self):
        """Status column header matches pattern → should fire."""
        assert self._has_data_table(STATUS_DASHBOARD_MD)

    def test_readme_no_fire(self):
        """README table with no numeric/status columns → skip."""
        assert not self._has_data_table(README_EXCERPT_MD)

    def test_numeric_two_columns_fires(self):
        """Table with ≥2 numeric cell values fires even without status header."""
        content = """\
| Name | p50 latency | p99 latency |
|------|-------------|-------------|
| api  | 12          | 450         |
"""
        assert self._has_data_table(content)

    # -- Rule 3: self-recursion guard --

    def test_self_recursion_guard(self, tmp_path, monkeypatch):
        """Path under artifact_dir → skip (exit 0 silently)."""
        from core.cli import _cmd_detect_artifact_candidate, _resolve_artifact_dir
        import argparse

        # Point artifact dir to tmp_path
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

        # Create a fake artifact file inside the artifact dir
        artifact_file = tmp_path / "2026-05-14" / "slug.html"
        artifact_file.parent.mkdir(parents=True)
        artifact_file.write_text("<html/>")

        args = argparse.Namespace(tool_output=str(artifact_file))
        result = _cmd_detect_artifact_candidate(args, "claude-code")
        assert result == 0  # silently skipped

    # -- Rule 2: path-prefix skiplist --

    def test_readme_path_skiplist(self, tmp_path, monkeypatch, capsys):
        """*.md under README* prefix → skip."""
        from core.cli import _cmd_detect_artifact_candidate
        import argparse

        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "data"))

        readme = tmp_path / "README.md"
        readme.write_text(STATUS_DASHBOARD_MD)  # has status table, but path should skip

        args = argparse.Namespace(tool_output=str(readme))
        result = _cmd_detect_artifact_candidate(args, "standalone")
        captured = capsys.readouterr()
        # Should be skipped due to README* path prefix
        assert "[atv-paperboard]" not in captured.out

    # -- Integration: only status dashboard fires from 5 inputs --

    def test_only_status_dashboard_fires_content_check(self):
        """Comprehensive: among 5 content strings only the status dashboard passes Rule 1."""
        inputs = [
            (TASK_LIST_MD, False),
            (COMPARISON_NO_NUMBERS_MD, False),
            (STATUS_DASHBOARD_MD, True),
            (README_EXCERPT_MD, False),
        ]
        for content, expected in inputs:
            result = self._has_data_table(content)
            assert result == expected, (
                f"Expected _has_data_table={expected} for content starting with "
                f"{content[:40]!r}"
            )
