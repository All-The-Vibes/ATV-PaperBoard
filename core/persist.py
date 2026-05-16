"""core/persist.py — Harness-aware artifact directory resolution."""
from __future__ import annotations

import os
from pathlib import Path


def artifact_dir(harness: str) -> Path:
    """Return the absolute artifact directory for *harness*.

    Paths are stable and harness-scoped; no cross-harness aggregation (v0.1.0).

    ``PAPERBOARD_ARTIFACT_DIR`` always wins when set, regardless of harness, so
    users can pin a single location without editing this file.
    """
    override = os.environ.get("PAPERBOARD_ARTIFACT_DIR")
    if override:
        return Path(override).expanduser()

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
    if harness == "copilot-cli":
        # Per SPEC addendum 2026-05-16 §5.4 — user-scoped, survives plugin
        # upgrades. ${COPILOT_HOME:-$HOME/.copilot}/plugin-data/atv-paperboard/artifacts
        home = os.environ.get("COPILOT_HOME")
        base = Path(home) if home else (Path.home() / ".copilot")
        return base / "plugin-data" / "atv-paperboard" / "artifacts"
    if harness.startswith("copilot"):
        # copilot-coding-agent and copilot-ide → repo-relative (PR-attached
        # artifacts, IDE-local artifacts).
        return Path.cwd() / "paperboard-artifacts"
    # standalone (and any unknown harness)
    return Path.cwd() / "paperboard-artifacts"
