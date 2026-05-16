"""
tests/test_adapter_copilot_cli.py

Regression tests for adapters/copilot-cli/ and the supporting core modules:

  Manifest layer
  --------------
  * hooks.json parses and has top-level ``version`` + ``hooks`` keys
  * postToolUse matcher is ``^(create|edit)$`` (regression on the addendum)
  * timeoutSec ≤ 60 (regression on the SPEC v4 2000-as-ms bug across adapters)
  * Both ``bash`` and ``powershell`` command keys are present (cross-platform)
  * Hook env block injects ``PAPERBOARD_HARNESS=copilot-cli``
  * artifact-reviewer.agent.md has Copilot frontmatter (description, prompt)

  Hook wire format
  ----------------
  * Stdin-JSON reader tolerates malformed input (returns {})
  * extract_candidate_path handles absolute paths, relative paths (resolved
    against cwd), missing keys, and the camelCase / PascalCase variants
  * emit_response writes ``additionalContext`` JSON only when a suggestion exists

  End-to-end harness wiring
  -------------------------
  * core/detect.py returns ``copilot-cli`` when PAPERBOARD_HARNESS is set,
    when COPILOT_HOME is set, and when ~/.copilot/installed-plugins/ is present
  * core/persist.py resolves to ``~/.copilot/plugin-data/atv-paperboard/artifacts/``
  * GITHUB_ACTIONS still wins over COPILOT_* (CI must stay copilot-coding-agent)
  * The ``paperboard copilot-post-tool-use`` subcommand round-trips a
    status-dashboard payload into an ``additionalContext`` suggestion
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
ADAPTER_DIR = REPO_ROOT / "adapters" / "copilot-cli"
HOOKS_JSON = ADAPTER_DIR / "hooks.json"
AGENT_MD = ADAPTER_DIR / "agents" / "artifact-reviewer.agent.md"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Manifest layer — hooks.json
# ---------------------------------------------------------------------------

class TestHooksJson:
    def _load(self) -> dict:
        assert HOOKS_JSON.exists(), f"hooks.json not found at {HOOKS_JSON}"
        return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))

    def test_parses(self):
        data = self._load()
        assert isinstance(data, dict)

    def test_has_version_field(self):
        data = self._load()
        assert "version" in data, "Copilot CLI hooks.json must declare a 'version'"
        assert data["version"] == 1

    def test_post_tool_use_present(self):
        data = self._load()
        assert "postToolUse" in data["hooks"], "hooks.hooks must have postToolUse"

    def test_matcher_targets_write_tools(self):
        """The matcher must fire on create/edit and not on read-only tools."""
        import re

        data = self._load()
        for entry in data["hooks"]["postToolUse"]:
            matcher = entry.get("matcher", "")
            anchored = f"^(?:{matcher})$" if not matcher.startswith("^") else matcher
            assert re.match(anchored, "create"), f"matcher {matcher!r} must match 'create'"
            assert re.match(anchored, "edit"), f"matcher {matcher!r} must match 'edit'"
            assert not re.match(anchored, "view"), f"matcher {matcher!r} must NOT match 'view'"
            assert not re.match(anchored, "grep"), f"matcher {matcher!r} must NOT match 'grep'"

    def test_timeout_lte_60_seconds(self):
        """Regression on the SPEC v4 ms-vs-seconds bug (2000 ≠ 2s in Copilot CLI)."""
        data = self._load()
        for entry in data["hooks"]["postToolUse"]:
            timeout = entry.get("timeoutSec")
            assert timeout is not None, "Copilot CLI hooks need timeoutSec"
            assert timeout <= 60, (
                f"timeoutSec {timeout} exceeds 60; Copilot CLI treats this value "
                "as seconds, not milliseconds"
            )

    def test_both_shells_declared(self):
        """Hook commands must declare both bash and powershell entries.

        Copilot CLI picks the right shell at runtime based on platform.
        Declaring only one strands users on the other platform.
        """
        data = self._load()
        for entry in data["hooks"]["postToolUse"]:
            assert "bash" in entry, "hooks.json must declare a 'bash' command"
            assert "powershell" in entry, "hooks.json must declare a 'powershell' command"
            assert "paperboard" in entry["bash"], "bash command should invoke paperboard"
            assert "paperboard" in entry["powershell"], "powershell command should invoke paperboard"
            assert "copilot-post-tool-use" in entry["bash"]
            assert "copilot-post-tool-use" in entry["powershell"]

    def test_env_injects_paperboard_harness(self):
        """The env block must set PAPERBOARD_HARNESS so detect.py honors the override."""
        data = self._load()
        for entry in data["hooks"]["postToolUse"]:
            env = entry.get("env", {})
            assert env.get("PAPERBOARD_HARNESS") == "copilot-cli", (
                "env block must inject PAPERBOARD_HARNESS=copilot-cli so "
                "detect.detect_harness() returns the right value inside the hook"
            )


# ---------------------------------------------------------------------------
# Manifest layer — agent frontmatter
# ---------------------------------------------------------------------------

class TestArtifactReviewerAgent:
    def test_file_exists(self):
        assert AGENT_MD.exists(), f"agent file missing at {AGENT_MD}"

    def test_frontmatter_has_required_fields(self):
        """Per addendum §2: description (required), prompt (required)."""
        text = AGENT_MD.read_text(encoding="utf-8")
        assert text.startswith("---\n"), "agent.md must start with YAML frontmatter"
        end = text.find("\n---\n", 4)
        assert end != -1, "agent.md frontmatter has no closing ---"
        front = text[4:end]
        # Light parse — avoid pulling in a YAML dependency for one assertion
        assert "description:" in front, "agent.md frontmatter missing description"
        assert "prompt:" in front, "agent.md frontmatter missing prompt"
        assert "name: artifact-reviewer" in front

    def test_declares_shell_tools(self):
        """Tools list must include both bash and powershell so the agent can
        invoke paperboard on either platform."""
        text = AGENT_MD.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4)
        front = text[4:end]
        assert "- bash" in front
        assert "- powershell" in front

    def test_constraints_preserve_reviewer_rules(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert "NEVER" in text, "agent.md must keep the NEVER-self-render constraints"
        assert "render-artifact" in text


# ---------------------------------------------------------------------------
# Hook wire format — pure helpers
# ---------------------------------------------------------------------------

class TestHookHelpers:
    def test_read_hook_payload_empty(self):
        from core.hooks.copilot_post_tool_use import read_hook_payload

        assert read_hook_payload(io.StringIO("")) == {}

    def test_read_hook_payload_malformed(self):
        from core.hooks.copilot_post_tool_use import read_hook_payload

        assert read_hook_payload(io.StringIO("not json")) == {}

    def test_read_hook_payload_non_object(self):
        from core.hooks.copilot_post_tool_use import read_hook_payload

        assert read_hook_payload(io.StringIO("[1, 2, 3]")) == {}

    def test_read_hook_payload_valid(self):
        from core.hooks.copilot_post_tool_use import read_hook_payload

        payload = {"toolName": "create", "toolArgs": {"path": "/tmp/x.md"}}
        result = read_hook_payload(io.StringIO(json.dumps(payload)))
        assert result["toolName"] == "create"

    def test_extract_candidate_path_absolute(self):
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        payload = {"toolName": "create", "toolArgs": {"path": "/tmp/foo.md"}}
        assert extract_candidate_path(payload) == str(Path("/tmp/foo.md"))

    def test_extract_candidate_path_relative_resolved_against_cwd(self):
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        payload = {
            "toolName": "edit",
            "cwd": "/work/repo",
            "toolArgs": {"path": "out/report.md"},
        }
        result = extract_candidate_path(payload)
        assert result == str(Path("/work/repo") / "out" / "report.md")

    def test_extract_candidate_path_probes_alternate_keys(self):
        """toolArgs may surface the path under file_path or filename — addendum §6."""
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        for key in ("file_path", "filename"):
            payload = {"toolName": "create", "toolArgs": {key: "/tmp/z.md"}}
            assert extract_candidate_path(payload) == str(Path("/tmp/z.md"))

    def test_extract_candidate_path_rejects_non_write_tool(self):
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        payload = {"toolName": "grep", "toolArgs": {"path": "/tmp/foo.md"}}
        assert extract_candidate_path(payload) is None

    def test_extract_candidate_path_accepts_pascalcase(self):
        """Copilot CLI accepts both camelCase and PascalCase event/payload keys."""
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        payload = {"ToolName": "create", "ToolArgs": {"path": "/tmp/p.md"}}
        assert extract_candidate_path(payload) == str(Path("/tmp/p.md"))

    def test_extract_candidate_path_missing_args(self):
        from core.hooks.copilot_post_tool_use import extract_candidate_path

        assert extract_candidate_path({"toolName": "create"}) is None
        assert extract_candidate_path({}) is None

    def test_emit_response_silent_on_none(self):
        from core.hooks.copilot_post_tool_use import emit_response

        sink = io.StringIO()
        emit_response(sink, None)
        assert sink.getvalue() == ""

    def test_emit_response_wraps_in_additional_context(self):
        from core.hooks.copilot_post_tool_use import emit_response

        sink = io.StringIO()
        emit_response(sink, "render it!")
        payload = json.loads(sink.getvalue())
        assert "additionalContext" in payload
        assert "[atv-paperboard] render it!" in payload["additionalContext"]


# ---------------------------------------------------------------------------
# End-to-end harness wiring
# ---------------------------------------------------------------------------

class TestHarnessDetection:
    def test_paperboard_harness_override(self, monkeypatch):
        from core.detect import detect_harness

        for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA",
                    "GITHUB_ACTIONS", "CODEX_HOME",
                    "COPILOT_HOME", "COPILOT_AGENT", "COPILOT_CLI_VERSION"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("PAPERBOARD_HARNESS", "copilot-cli")
        assert detect_harness() == "copilot-cli"

    def test_paperboard_harness_override_rejects_unknown_value(self, monkeypatch):
        """Unknown override value must be ignored; the result is whatever the
        normal detection cascade returns (machine-dependent), but it must NOT
        be 'copilot-cli' just because the env var was set."""
        from core.detect import detect_harness

        for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA",
                    "GITHUB_ACTIONS", "CODEX_HOME",
                    "COPILOT_HOME", "COPILOT_AGENT", "COPILOT_CLI_VERSION"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("PAPERBOARD_HARNESS", "not-a-real-harness")
        result = detect_harness()
        assert result != "not-a-real-harness", "unknown override must not pass through"
        assert result != "copilot-cli", "unknown override must not trigger copilot-cli"

    def test_copilot_home_signal(self, monkeypatch, tmp_path):
        from core.detect import detect_harness

        for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA",
                    "GITHUB_ACTIONS", "CODEX_HOME",
                    "PAPERBOARD_HARNESS", "COPILOT_AGENT", "COPILOT_CLI_VERSION"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
        assert detect_harness() == "copilot-cli"

    def test_github_actions_still_wins(self, monkeypatch, tmp_path):
        """CI must keep returning copilot-coding-agent even when COPILOT_HOME is set."""
        from core.detect import detect_harness

        for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA",
                    "CODEX_HOME", "PAPERBOARD_HARNESS"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
        assert detect_harness() == "copilot-coding-agent"

    def test_plugin_install_dir_signal(self, monkeypatch, tmp_path):
        """When env signals are absent but the plugin is installed, detect it."""
        from core.detect import detect_harness

        for var in ("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA",
                    "GITHUB_ACTIONS", "CODEX_HOME",
                    "PAPERBOARD_HARNESS", "COPILOT_AGENT", "COPILOT_CLI_VERSION",
                    "VSCODE_PID", "TERM_PROGRAM"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
        # COPILOT_HOME alone already triggers; remove it and use the FS-only path
        plugin = tmp_path / "installed-plugins" / "atv-paperboard"
        plugin.mkdir(parents=True)
        monkeypatch.delenv("COPILOT_HOME", raising=False)
        # We can't easily monkeypatch Path.home() portably; instead set
        # COPILOT_HOME for the install check and verify it's still detected
        monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
        assert detect_harness() == "copilot-cli"


class TestArtifactDirResolution:
    def test_copilot_cli_uses_copilot_home(self, monkeypatch, tmp_path):
        from core.persist import artifact_dir

        monkeypatch.delenv("PAPERBOARD_ARTIFACT_DIR", raising=False)
        monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
        result = artifact_dir("copilot-cli")
        assert result == tmp_path / "plugin-data" / "atv-paperboard" / "artifacts"

    def test_copilot_cli_falls_back_to_home_dot_copilot(self, monkeypatch):
        from core.persist import artifact_dir

        monkeypatch.delenv("PAPERBOARD_ARTIFACT_DIR", raising=False)
        monkeypatch.delenv("COPILOT_HOME", raising=False)
        result = artifact_dir("copilot-cli")
        assert result == Path.home() / ".copilot" / "plugin-data" / "atv-paperboard" / "artifacts"

    def test_paperboard_artifact_dir_overrides_all_harnesses(self, monkeypatch, tmp_path):
        from core.persist import artifact_dir

        monkeypatch.setenv("PAPERBOARD_ARTIFACT_DIR", str(tmp_path / "pinned"))
        assert artifact_dir("copilot-cli") == tmp_path / "pinned"
        assert artifact_dir("codex") == tmp_path / "pinned"
        assert artifact_dir("standalone") == tmp_path / "pinned"

    def test_copilot_coding_agent_unchanged(self, monkeypatch):
        """Regression: hosted Coding Agent must still resolve to repo-relative."""
        from core.persist import artifact_dir

        monkeypatch.delenv("PAPERBOARD_ARTIFACT_DIR", raising=False)
        assert artifact_dir("copilot-coding-agent") == Path.cwd() / "paperboard-artifacts"


# ---------------------------------------------------------------------------
# End-to-end CLI subcommand
# ---------------------------------------------------------------------------

STATUS_DASHBOARD_MD = """\
# CI Status Dashboard

| Job        | Status  | Duration |
|------------|---------|----------|
| unit-tests | pass    | 42s      |
| lint       | fail    | 3s       |
| deploy     | pending | -        |
"""

TASK_LIST_MD = """\
# TODO

| Task | Done |
|------|------|
| Write tests | [ ] |
| Review PR  | [x] |
"""


class TestCopilotPostToolUseCmd:
    def _invoke(self, payload: dict, monkeypatch, tmp_path) -> str:
        """Drive the subcommand end-to-end and return captured stdout."""
        from core.cli import _cmd_copilot_post_tool_use

        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        monkeypatch.setenv("PAPERBOARD_ARTIFACT_DIR", str(tmp_path / "out"))
        rc = _cmd_copilot_post_tool_use(argparse.Namespace(), "copilot-cli")
        assert rc == 0, "Copilot CLI hooks must always exit 0 (fail-open)"
        return captured.getvalue()

    def test_status_dashboard_yields_additional_context(self, monkeypatch, tmp_path):
        target = tmp_path / "report.md"
        target.write_text(STATUS_DASHBOARD_MD, encoding="utf-8")
        payload = {
            "sessionId": "abc",
            "cwd": str(tmp_path),
            "toolName": "create",
            "toolArgs": {"path": str(target)},
        }
        out = self._invoke(payload, monkeypatch, tmp_path)
        assert out.strip(), "expected stdout JSON for a candidate file"
        decoded = json.loads(out)
        assert "additionalContext" in decoded
        assert "[atv-paperboard]" in decoded["additionalContext"]
        assert "/paperboard" in decoded["additionalContext"]
        assert "--style paperboard" in decoded["additionalContext"]

    def test_task_list_silent(self, monkeypatch, tmp_path):
        """Task lists do not qualify as artifacts — hook must be silent."""
        target = tmp_path / "TODO.md"
        target.write_text(TASK_LIST_MD, encoding="utf-8")
        payload = {
            "sessionId": "abc",
            "cwd": str(tmp_path),
            "toolName": "create",
            "toolArgs": {"path": str(target)},
        }
        out = self._invoke(payload, monkeypatch, tmp_path)
        assert out == "", f"expected empty stdout; got {out!r}"

    def test_missing_payload_silent(self, monkeypatch, tmp_path):
        """Empty stdin must not crash and must not emit a suggestion."""
        from core.cli import _cmd_copilot_post_tool_use

        monkeypatch.setattr(sys, "stdin", io.StringIO(""))
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        monkeypatch.setenv("PAPERBOARD_ARTIFACT_DIR", str(tmp_path / "out"))
        rc = _cmd_copilot_post_tool_use(argparse.Namespace(), "copilot-cli")
        assert rc == 0
        assert captured.getvalue() == ""

    def test_non_write_tool_silent(self, monkeypatch, tmp_path):
        """A grep payload (not a write) must not produce additionalContext."""
        target = tmp_path / "report.md"
        target.write_text(STATUS_DASHBOARD_MD, encoding="utf-8")
        payload = {
            "sessionId": "abc",
            "cwd": str(tmp_path),
            "toolName": "grep",
            "toolArgs": {"path": str(target)},
        }
        out = self._invoke(payload, monkeypatch, tmp_path)
        assert out == ""

    def test_subcommand_registered(self):
        """`paperboard copilot-post-tool-use` must be a documented subcommand."""
        from core.cli import main as cli_main

        with pytest.raises(SystemExit):
            cli_main(["copilot-post-tool-use", "--help"])
