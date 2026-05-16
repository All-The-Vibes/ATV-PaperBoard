"""core/hooks/copilot_post_tool_use.py — Copilot CLI postToolUse hook.

Wire format (stdin JSON, camelCase variant; PascalCase also accepted by
Copilot CLI but we emit/consume camelCase to match the docs reference):

    {
      "sessionId": "...",
      "timestamp": "...",
      "cwd": "/path/to/repo",
      "toolName": "create" | "edit" | ...,
      "toolArgs": { "path": "relative/or/absolute.md", ... },
      "toolResult": { "resultType": "...", "textResultForLlm": "..." }
    }

Wire format (stdout JSON on exit 0):

    {"additionalContext": "..."}

Copilot CLI hooks are FAIL-OPEN: non-zero exit is logged but tool execution
continues regardless. So the hook always exits 0 and only signals via the
JSON payload on stdout.

Schema source: https://docs.github.com/en/copilot/reference/hooks-reference
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import IO, Any

# Keys that ``create`` / ``edit`` / future write tools may use for the target
# path. Probed in order; first non-empty wins. Kept defensive because the
# hooks reference does not enumerate per-tool toolArgs shapes.
_PATH_KEYS = ("path", "file_path", "filename")

# toolName values we consider write events worth classifying. The hooks.json
# matcher already filters at the Copilot CLI level; this is a second-line
# guard for when the hook is invoked directly (e.g. from tests).
_WRITE_TOOLS = frozenset({"create", "edit", "write", "Write", "Edit"})


def read_hook_payload(stream: IO[str]) -> Mapping[str, Any]:
    """Read a single JSON document from *stream*.

    Returns ``{}`` on any parse failure or empty input so the caller never
    has to special-case malformed payloads — they just produce no suggestion.
    """
    try:
        raw = stream.read()
    except (OSError, ValueError):
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def extract_candidate_path(payload: Mapping[str, Any]) -> str | None:
    """Extract the target file path from a postToolUse payload.

    Returns an absolute path string when *payload* describes a write tool
    invocation, or ``None`` when the payload is missing required fields,
    references a non-write tool, or fails to surface a path.
    """
    tool_name = payload.get("toolName") or payload.get("ToolName")
    if tool_name and tool_name not in _WRITE_TOOLS:
        return None

    tool_args = payload.get("toolArgs") or payload.get("ToolArgs") or {}
    if not isinstance(tool_args, Mapping):
        return None

    raw_path: str | None = None
    for key in _PATH_KEYS:
        value = tool_args.get(key)
        if isinstance(value, str) and value.strip():
            raw_path = value.strip()
            break
    if raw_path is None:
        return None

    candidate = Path(raw_path)
    if not candidate.is_absolute():
        cwd = payload.get("cwd") or payload.get("Cwd")
        if isinstance(cwd, str) and cwd.strip():
            candidate = Path(cwd) / candidate
    return str(candidate)


def emit_response(stream: IO[str], suggestion: str | None) -> None:
    """Write the postToolUse response to *stream*.

    When *suggestion* is None nothing is emitted; Copilot CLI treats empty
    stdout as "no decision-control fields" and proceeds normally. When a
    suggestion is provided it is wrapped in the documented ``additionalContext``
    field so Copilot injects it into the agent's next turn (the analogue of
    Claude Code's ``<system-reminder>`` block).
    """
    if not suggestion:
        return
    payload = {"additionalContext": f"[atv-paperboard] {suggestion}"}
    json.dump(payload, stream)
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m core.hooks.copilot_post_tool_use``.

    Delegates to ``paperboard copilot-post-tool-use`` so the module can be
    invoked directly from hooks.json on systems where ``paperboard`` is not
    on PATH but the package is importable.
    """
    import argparse  # noqa: PLC0415

    from core.cli import _cmd_copilot_post_tool_use, _detect_harness  # noqa: PLC0415

    args = argparse.Namespace()
    harness = _detect_harness()
    return _cmd_copilot_post_tool_use(args, harness)


if __name__ == "__main__":
    sys.exit(main())
