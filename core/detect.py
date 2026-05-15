"""core/detect.py — Auto-detect which agentic harness we're running in.

Precedence (v4.1 corrected):
  Tier 1 — harness-specific session env vars (strongest signal)
  Tier 2 — filesystem heuristics (only after Tier 1 misses)
  Tier 3 — IDE pairing (require both signals)
  Tier 4 — standalone fallback
"""
from __future__ import annotations

import os
from pathlib import Path


def detect_harness() -> str:
    """Return the name of the current harness, or 'standalone'.

    Return values: 'claude-code' | 'copilot-coding-agent' | 'opencode' |
                   'codex' | 'copilot-ide' | 'standalone'
    """
    # Tier 1 — harness-specific session env vars (strongest signal)
    if "CLAUDE_PLUGIN_ROOT" in os.environ or "CLAUDE_PLUGIN_DATA" in os.environ:
        return "claude-code"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "copilot-coding-agent"
    if "OPENCODE_CONFIG_DIR" in os.environ:
        return "opencode"
    if "CODEX_HOME" in os.environ:
        return "codex"

    # Tier 2 — filesystem heuristics (only after Tier 1 misses)
    if (Path.home() / ".codex" / "config.toml").exists():
        return "codex"

    # Tier 3 — IDE pairing (require both signals to avoid false positives
    # from terminals that re-export VSCODE_PID without an active VS Code session)
    if "VSCODE_PID" in os.environ and os.environ.get("TERM_PROGRAM") == "vscode":
        return "copilot-ide"

    return "standalone"
