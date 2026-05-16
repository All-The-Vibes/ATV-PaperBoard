"""tests/phase0/test_v3_v4_v5_v6.py

V3 (Claude Code hook propagates CLAUDE_PLUGIN_DATA) and V4 (Codex PostToolUse
fires on Write) are validated manually against real harness sessions; see
docs/checkpoints 001-native-copilot-cli-adapter and 002-real-copilot-cli-
sandbox-valid for the recorded evidence. They have no automatable form here.

V5: parametrize over 5 mock environments, assert detect_harness() returns expected value.
V6: assert python/py is resolvable on PATH.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.detect import detect_harness

# ---------------------------------------------------------------------------
# V5 — detect_harness() mock-env parametrize
# ---------------------------------------------------------------------------

_HARNESS_ENVS: list[tuple[str, dict[str, str], dict[str, str], str]] = [
    # (id, env_set, env_unset, expected)
    (
        "claude-code",
        {"CLAUDE_PLUGIN_DATA": "/tmp/plugin-data"},
        {},
        "claude-code",
    ),
    (
        "codex",
        {"CODEX_HOME": "/home/user/.codex"},
        {"CLAUDE_PLUGIN_ROOT": "", "CLAUDE_PLUGIN_DATA": "", "GITHUB_ACTIONS": ""},
        "codex",
    ),
    (
        "copilot-coding-agent",
        {"GITHUB_ACTIONS": "true"},
        {"CLAUDE_PLUGIN_ROOT": "", "CLAUDE_PLUGIN_DATA": "", "CODEX_HOME": ""},
        "copilot-coding-agent",
    ),
    (
        "standalone",
        {},
        {"CLAUDE_PLUGIN_ROOT": "", "CLAUDE_PLUGIN_DATA": "", "GITHUB_ACTIONS": "",
         "CODEX_HOME": "", "VSCODE_PID": "", "TERM_PROGRAM": ""},
        "standalone",
    ),
]


@pytest.mark.parametrize(
    "env_id,env_set,env_unset,expected",
    [
        pytest.param(env_id, env_set, env_unset, expected, id=env_id)
        for env_id, env_set, env_unset, expected in _HARNESS_ENVS
    ],
)
def test_v5_detect_harness_mock_envs(
    monkeypatch: pytest.MonkeyPatch,
    env_id: str,
    env_set: dict[str, str],
    env_unset: dict[str, str],
    expected: str,
    tmp_path: Path,
) -> None:
    """V5: detect_harness() returns expected value for each mock environment."""
    # Remove interfering vars first
    for key in env_unset:
        monkeypatch.delenv(key, raising=False)
    # Also clear all harness vars not explicitly set
    for key in (
        "CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "GITHUB_ACTIONS",
        "CODEX_HOME", "VSCODE_PID", "TERM_PROGRAM",
    ):
        if key not in env_set:
            monkeypatch.delenv(key, raising=False)
    # Set the desired vars
    for key, val in env_set.items():
        monkeypatch.setenv(key, val)

    # Patch Path.home() to a tmp dir without ~/.codex/config.toml so
    # filesystem heuristic doesn't fire unexpectedly
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    result = detect_harness()
    assert result == expected, (
        f"[{env_id}] expected detect_harness()={expected!r}, got {result!r}"
    )


# ---------------------------------------------------------------------------
# V6 — python is invokable on PATH
# ---------------------------------------------------------------------------

def test_v6_python_on_path() -> None:
    """V6: shutil.which('python') or shutil.which('py') returns a real path."""
    python = shutil.which("python") or shutil.which("py")
    assert python is not None, (
        "Neither 'python' nor 'py' found on PATH. "
        "Hook commands need a PATH-resolution shim; document in INSTALL.md."
    )
    assert Path(python).exists(), f"Resolved python path does not exist: {python}"
