"""core/persist.py — Harness-aware artifact directory resolution."""
from __future__ import annotations

import os
from pathlib import Path


def artifact_dir(harness: str) -> Path:
    """Return the absolute artifact directory for *harness*.

    Paths are stable and harness-scoped; no cross-harness aggregation (v0.1.0).
    """
    if harness == "claude-code":
        data = os.environ.get("CLAUDE_PLUGIN_DATA")
        if not data:
            raise RuntimeError(
                "CLAUDE_PLUGIN_DATA not set; cannot resolve Claude Code artifact dir."
            )
        return Path(data)
    if harness == "codex":
        return Path.home() / ".codex" / "atv-paperboard-artifacts"
    if harness == "opencode":
        cfg = os.environ.get("OPENCODE_CONFIG_DIR")
        if not cfg:
            raise RuntimeError(
                "OPENCODE_CONFIG_DIR not set; cannot resolve OpenCode artifact dir."
            )
        return Path(cfg) / "atv-paperboard-artifacts"
    if harness.startswith("copilot"):
        return Path.cwd() / "paperboard-artifacts"
    # standalone (and any unknown harness)
    return Path.cwd() / "paperboard-artifacts"
