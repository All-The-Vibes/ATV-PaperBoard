"""core/detect.py — Auto-detect which agentic harness we're running in.

Precedence (v4.1 corrected; v0.1.1 adds copilot-cli):
  Tier 0 — explicit override (PAPERBOARD_HARNESS)
  Tier 1 — harness-specific session env vars (strongest signal)
  Tier 2 — filesystem heuristics (only after Tier 1 misses)
  Tier 3 — IDE pairing (require both signals)
  Tier 4 — standalone fallback
"""
from __future__ import annotations

import os
from pathlib import Path

# Whitelist of harness names PAPERBOARD_HARNESS may set. Anything outside this
# list is ignored so a stale env var can't silently rewrite persistence paths.
_VALID_OVERRIDES = frozenset({
    "claude-code",
    "copilot-cli",
    "copilot-coding-agent",
    "copilot-ide",
    "codex",
    "opencode",
    "standalone",
})


def detect_harness() -> str:
    """Return the name of the current harness, or 'standalone'.

    Return values: 'claude-code' | 'copilot-cli' | 'copilot-coding-agent' |
                   'opencode' | 'codex' | 'copilot-ide' | 'standalone'
    """
    # Tier 0 — explicit override (e.g. injected by hooks.json env block).
    override = os.environ.get("PAPERBOARD_HARNESS", "").strip()
    if override in _VALID_OVERRIDES:
        return override

    # Tier 1 — harness-specific session env vars (strongest signal).
    # Order matters: GITHUB_ACTIONS is checked before COPILOT_* so a hosted
    # Copilot Coding Agent run does not get misclassified as Copilot CLI.
    if "CLAUDE_PLUGIN_ROOT" in os.environ or "CLAUDE_PLUGIN_DATA" in os.environ:
        return "claude-code"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "copilot-coding-agent"
    if _has_copilot_cli_env():
        return "copilot-cli"
    if "OPENCODE_CONFIG_DIR" in os.environ:
        return "opencode"
    if "CODEX_HOME" in os.environ:
        return "codex"

    # Tier 2 — filesystem heuristics (only after Tier 1 misses)
    if (Path.home() / ".codex" / "config.toml").exists():
        return "codex"
    if _has_copilot_cli_plugin_install():
        return "copilot-cli"

    # Tier 3 — IDE pairing (require both signals to avoid false positives
    # from terminals that re-export VSCODE_PID without an active VS Code session)
    if "VSCODE_PID" in os.environ and os.environ.get("TERM_PROGRAM") == "vscode":
        return "copilot-ide"

    return "standalone"


def _has_copilot_cli_env() -> bool:
    """True when env vars indicate an active Copilot CLI session.

    Copilot CLI does not document a single canonical session env var, so we
    accept any of: ``COPILOT_HOME`` (user override of ~/.copilot), any other
    ``COPILOT_*`` variable (excluding the GitHub-Actions ``GITHUB_*`` family
    which is handled earlier), or the explicit ``COPILOT_AGENT`` /
    ``COPILOT_CLI_VERSION`` markers if a future release adds them.
    """
    if "COPILOT_HOME" in os.environ:
        return True
    if "COPILOT_AGENT" in os.environ or "COPILOT_CLI_VERSION" in os.environ:
        return True
    return False


def _has_copilot_cli_plugin_install() -> bool:
    """True when the atv-paperboard plugin is installed under ~/.copilot/."""
    home = os.environ.get("COPILOT_HOME")
    base = Path(home) if home else (Path.home() / ".copilot")
    return (base / "installed-plugins" / "atv-paperboard").exists()
