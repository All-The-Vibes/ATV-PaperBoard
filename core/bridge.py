"""core/bridge.py — Thin Python wrapper around the @google/design.md Node CLI.

Caches binary resolution at ~/.atv-paperboard/config.json (schema_version: 1).
All subprocess calls use list args; no shell=True with f-strings.

Error taxonomy:
  BridgeError           — base; all bridge failures
  LintFindings          — exit 1 with parseable findings JSON
  BridgeEnvError        — other exit codes / environment problems
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class BridgeError(Exception):
    """Base class for all bridge failures."""


class LintFindings(BridgeError):
    """Lint returned exit 1 with parseable findings.

    Attributes:
        findings: Parsed findings dict from the CLI.
    """
    def __init__(self, message: str, findings: dict[str, Any]) -> None:
        super().__init__(message)
        self.findings = findings


class BridgeEnvError(BridgeError):
    """Non-lint exit code or environment problem (node missing, binary not found, etc.)."""


# ---------------------------------------------------------------------------
# Config cache
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path.home() / ".atv-paperboard"
_CONFIG_PATH = _CONFIG_DIR / "config.json"
_SCHEMA_VERSION = 1


def _load_cache() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("schema_version") == _SCHEMA_VERSION:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_cache(data: dict[str, Any]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data["schema_version"] = _SCHEMA_VERSION
    _CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Binary resolution
# ---------------------------------------------------------------------------

def _resolve_binary() -> tuple[str, str]:
    """Return (node_exe, bin_js) pair, using cache when possible.

    Raises BridgeEnvError if node is not on PATH or the JS binary cannot be found.
    """
    cache = _load_cache()
    node_exe: str | None = cache.get("node_exe")
    bin_js: str | None = cache.get("bin_js")

    if node_exe and bin_js and Path(bin_js).exists():
        return node_exe, bin_js

    # Locate node
    node_exe = shutil.which("node")
    if not node_exe:
        raise BridgeEnvError(
            "node not found on PATH. Install Node.js (>=18) and re-run."
        )

    # Locate @google/design.md dist/index.js relative to this project
    # Walk upward from this file's directory looking for node_modules.
    candidate_roots = [
        Path(__file__).parent.parent,  # repo root (most common)
        Path.cwd(),
    ]
    bin_js = None
    for root in candidate_roots:
        candidate = root / "node_modules" / "@google" / "design.md" / "dist" / "index.js"
        if candidate.exists():
            bin_js = str(candidate)
            break

    if not bin_js:
        raise BridgeEnvError(
            "@google/design.md dist/index.js not found. Run `npm install` in the project root."
        )

    _save_cache({"node_exe": node_exe, "bin_js": bin_js})
    return node_exe, bin_js


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def _run(args: list[str]) -> str:
    """Run the design.md CLI with *args* appended; return stdout as str.

    Raises:
        LintFindings  — exit 1 + parseable JSON in stdout (lint failure with findings)
        BridgeEnvError — any other non-zero exit
    """
    node_exe, bin_js = _resolve_binary()
    cmd = [node_exe, bin_js] + args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode == 0:
        return stdout

    # exit 1 from `lint` returns findings JSON — distinguish from env errors
    if result.returncode == 1 and stdout:
        try:
            parsed = json.loads(stdout)
            if "findings" in parsed:
                raise LintFindings(
                    f"Lint returned findings: {parsed.get('summary', {})}",
                    findings=parsed,
                )
        except (json.JSONDecodeError, KeyError):
            pass

    raise BridgeEnvError(
        f"design.md CLI exited {result.returncode}.\n"
        f"cmd: {' '.join(cmd)}\n"
        f"stdout: {stdout}\n"
        f"stderr: {stderr}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lint(path: str | Path) -> dict[str, Any]:
    """Lint *path* (a DESIGN.md file).

    Returns the parsed JSON dict ``{"findings": [...], "summary": {...}}``.
    Raises LintFindings if there are lint errors (exit 1 with findings).
    Raises BridgeEnvError for environment / invocation failures.
    """
    raw = _run(["lint", "--format", "json", str(Path(path).resolve())])
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BridgeEnvError(f"lint output is not valid JSON: {raw!r}") from exc


def export(path: str | Path, fmt: str = "tailwind") -> dict[str, Any]:
    """Export tokens from *path* in *fmt* format (tailwind | dtcg).

    Returns the parsed JSON dict.
    Raises BridgeEnvError for environment / invocation failures.
    """
    raw = _run(["export", "--format", fmt, str(Path(path).resolve())])
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BridgeEnvError(f"export output is not valid JSON: {raw!r}") from exc


def spec() -> dict[str, Any]:
    """Return the DESIGN.md format specification.

    Returns ``{"content": <markdown string>, "version": <version string>}``
    so callers can do schema-drift checks without parsing markdown.
    """
    raw = _run(["spec"])
    ver = version()
    return {"content": raw, "version": ver}


def version() -> str:
    """Return the @google/design.md CLI version string (e.g. "0.1.1")."""
    node_exe, bin_js = _resolve_binary()
    result = subprocess.run(
        [node_exe, bin_js, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise BridgeEnvError(
            f"design.md --version exited {result.returncode}: {result.stderr.strip()}"
        )
    return result.stdout.strip()
