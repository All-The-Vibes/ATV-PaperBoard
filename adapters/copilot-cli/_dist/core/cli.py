"""core/cli.py — Universal CLI entry point for atv-paperboard.

Subcommands:
  render                 — render an artifact triple (also auto-regens gallery)
  validate               — run ENFORCE checks on a slug
  validate-all           — validate every artifact in a directory
  regenerate             — 3-step retry for a failing slug
  gallery                — (re)generate the COMPOUND gallery HTML
  detect-artifact-candidate — PostToolUse hook helper (Phase 4 hook heuristics; §16)
  doctor                 — diagnose install

Every command resolves harness via detect.detect_harness() first.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 stdout/stderr on Windows so glyphs like ✓ ✗ — and other non-cp1252
# characters in subcommand output don't crash with UnicodeEncodeError. Stdlib-only;
# no-op on systems that already use UTF-8. Discovered via Phase 7a real-world run.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass  # non-tty stream or older interpreter; silently degrade


# ─�� Main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="paperboard",
        description="atv-paperboard — cross-harness HTML artifact toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # render
    p_render = sub.add_parser("render", help="Render an artifact triple")
    p_render.add_argument(
        "--input",
        default="-",
        help="Path to JSON/Markdown input file, or '-' to read from stdin",
    )
    p_render.add_argument(
        "--design",
        default=None,
        help="Design name, path, or URL (defaults to paperboard.DESIGN.md)",
    )
    p_render.add_argument(
        "--tier",
        choices=["pico", "daisy", "atv"],
        default="atv",
        help="CSS framework tier (default: atv — the dark designed-document tier)",
    )
    p_render.add_argument(
        "--no-open",
        action="store_true",
        help="Skip browser open after render",
    )
    p_render.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory",
    )

    # validate
    p_validate = sub.add_parser("validate", help="Run ENFORCE checks on an artifact")
    p_validate.add_argument("slug", help="Artifact slug")
    p_validate.add_argument("--output-dir", default=None, help="Look for artifact in this dir instead of harness default")

    # regenerate
    p_regen = sub.add_parser("regenerate", help="3-step differentiated retry")
    p_regen.add_argument("slug", help="Failing artifact slug")
    p_regen.add_argument("--output-dir", default=None, help="Look for artifact in this dir instead of harness default")

    # gallery (Phase 6)
    p_gallery = sub.add_parser("gallery", help="Regenerate the compound gallery HTML")
    p_gallery.add_argument(
        "--harness",
        default=None,
        help="Override harness for artifact dir resolution",
    )
    p_gallery.add_argument("--output-dir", default=None, help="Override artifact directory")

    # validate-all
    p_val_all = sub.add_parser("validate-all", help="Validate every artifact in a directory")
    p_val_all.add_argument("directory", help="Path to the artifact directory to scan")

    # detect-artifact-candidate (Phase 4 placeholder; hook helper)
    p_detect = sub.add_parser(
        "detect-artifact-candidate",
        help="PostToolUse hook helper — checks if Write output is an artifact candidate",
    )
    p_detect.add_argument("tool_output", nargs="?", default="", help="TOOL_OUTPUT JSON string")

    # copilot-post-tool-use (Copilot CLI hook helper; stdin-JSON, fail-open)
    sub.add_parser(
        "copilot-post-tool-use",
        help=(
            "Copilot CLI postToolUse hook helper — reads stdin JSON and emits "
            "an additionalContext suggestion when the written file looks like a "
            "data artifact. Always exits 0 (fail-open per Copilot CLI semantics)."
        ),
    )

    # doctor
    sub.add_parser("doctor", help="Diagnose atv-paperboard install")

    args = parser.parse_args(argv)

    # Resolve harness
    harness = _detect_harness()

    if args.command == "render":
        return _cmd_render(args, harness)
    elif args.command == "validate":
        return _cmd_validate(args, harness)
    elif args.command == "regenerate":
        return _cmd_regenerate(args, harness)
    elif args.command == "gallery":
        return _cmd_gallery(args, harness)
    elif args.command == "validate-all":
        return _cmd_validate_all(args, harness)
    elif args.command == "detect-artifact-candidate":
        return _cmd_detect_artifact_candidate(args, harness)
    elif args.command == "copilot-post-tool-use":
        return _cmd_copilot_post_tool_use(args, harness)
    elif args.command == "doctor":
        return _cmd_doctor(args, harness)
    return 0


# ── Command implementations ────────────────────────────────────────────────────


def _cmd_render(args: argparse.Namespace, harness: str) -> int:
    from core import render as _render  # noqa: PLC0415

    # Load input
    input_data = _load_input(args.input)

    # Resolve design path
    design_path = _resolve_design(args.design)

    # Resolve output dir
    output_dir = Path(args.output_dir) if args.output_dir else _resolve_artifact_dir(harness)

    triple = _render.render_artifact(
        input_data=input_data,
        design_path=design_path,
        tier=args.tier,
        output_dir=output_dir,
    )

    print(f"Rendered: {triple['html_path']}")
    print(f"  DESIGN: {triple['design_path']}")
    print(f"  Meta:   {triple['meta_path']}")
    print(f"  Slug:   {triple['slug']}")

    if not args.no_open:
        _render._serve_and_open(triple["html_path"])

    # COMPOUND pillar: auto-regenerate gallery after successful render.
    try:
        from core.gallery import regenerate_gallery  # noqa: PLC0415
        art_dir = Path(args.output_dir) if args.output_dir else None
        regenerate_gallery(harness, artifact_dir=art_dir)
    except Exception:  # noqa: BLE001
        pass  # gallery regen is non-fatal

    return 0


def _cmd_validate(args: argparse.Namespace, harness: str) -> int:
    from core.validate import validate_artifact  # noqa: PLC0415

    art_dir = Path(args.output_dir) if args.output_dir else None
    result = validate_artifact(args.slug, harness, artifact_dir=art_dir)
    if result.passed:
        print(f"✓ ACCEPT  slug={args.slug}")
        return 0
    else:
        print(f"✗ FAIL({result.fail_class})  slug={args.slug}")
        for f in result.lint_findings:
            print(f"  lint: {f.get('message', f)}")
        for v in result.color_violations:
            print(f"  color-trace: undeclared hex {v}")
        return 1


def _cmd_regenerate(args: argparse.Namespace, harness: str) -> int:
    from core import regenerate as _regen  # noqa: PLC0415
    from core.validate import validate_artifact  # noqa: PLC0415

    art_dir = Path(args.output_dir) if args.output_dir else None
    # Validate current slug first
    initial = validate_artifact(args.slug, harness, artifact_dir=art_dir)
    if initial.passed:
        print(f"✓ slug={args.slug} already passes; no regeneration needed.")
        return 0

    result = _regen.regenerate(args.slug, initial, artifact_dir=art_dir)
    step = result["retry_step"]
    new_slug = result["new_slug"]
    vr = result["validation"]
    status = "ACCEPT" if vr.passed else "FAIL"
    print(f"Regenerate step={step}  new_slug={new_slug}  status={status}({vr.fail_class})")
    return 0 if vr.passed else 1


def _cmd_gallery(args: argparse.Namespace, harness: str) -> int:
    from core.gallery import regenerate_gallery  # noqa: PLC0415

    override = getattr(args, "harness", None)
    art_dir = Path(args.output_dir) if args.output_dir else None
    gallery_path = regenerate_gallery(override or harness, artifact_dir=art_dir)
    print(f"Gallery: {gallery_path}")
    return 0


def _cmd_validate_all(args: argparse.Namespace, _harness: str) -> int:
    from core.validate import validate_all  # noqa: PLC0415

    directory = Path(args.directory)
    results = validate_all(directory)
    if not results:
        print(f"No artifacts found in {directory}")
        return 0
    failed = 0
    for r in results:
        # derive slug from lint_findings message or just count
        status = "✓ ACCEPT" if r.passed else f"✗ FAIL({r.fail_class})"
        print(status)
        if not r.passed:
            failed += 1
            for f in r.lint_findings:
                print(f"  lint: {f.get('message', f)}")
            for v in r.color_violations:
                print(f"  color-trace: undeclared hex {v}")
    print(f"\n{len(results)} artifact(s) checked — {failed} failed.")
    return 1 if failed else 0


def _cmd_detect_artifact_candidate(args: argparse.Namespace, harness: str) -> int:
    """Hook heuristic rules per SPEC §16. Exits 0 silently if not a candidate."""
    tool_output = args.tool_output or os.environ.get("TOOL_OUTPUT", "")
    suggestion = classify_artifact_candidate(tool_output, harness)
    if suggestion:
        print(f"\n[atv-paperboard] {suggestion}\n")
    return 0


def _cmd_copilot_post_tool_use(_args: argparse.Namespace, harness: str) -> int:
    """Copilot CLI postToolUse hook — reads stdin JSON, emits additionalContext.

    Copilot CLI hooks are fail-open: any non-zero exit is logged and execution
    continues, so this handler always exits 0. Output is JSON with an
    ``additionalContext`` field that Copilot injects into the agent's next turn.

    Schema source: https://docs.github.com/en/copilot/reference/hooks-reference
    """
    from core.hooks.copilot_post_tool_use import (  # noqa: PLC0415
        emit_response,
        extract_candidate_path,
        read_hook_payload,
    )

    payload = read_hook_payload(sys.stdin)
    candidate_path = extract_candidate_path(payload)
    if not candidate_path:
        emit_response(sys.stdout, None)
        return 0

    # Honor harness override from hooks.json env block
    effective_harness = os.environ.get("PAPERBOARD_HARNESS", harness)
    suggestion = classify_artifact_candidate(candidate_path, effective_harness)
    emit_response(sys.stdout, suggestion)
    return 0


def classify_artifact_candidate(tool_output: str, harness: str) -> str | None:
    """Apply SPEC §16 hook heuristic rules.

    Returns a suggestion message string if the path qualifies as an artifact
    candidate, or ``None`` otherwise. Shared by the Claude Code positional-arg
    hook (``detect-artifact-candidate``) and the Copilot CLI stdin-JSON hook
    (``copilot-post-tool-use``) so the two adapters apply identical filters.
    """
    import time  # noqa: PLC0415

    if not tool_output:
        return None

    # Rule 3: self-recursion guard
    artifact_dir = _resolve_artifact_dir(harness)
    try:
        out_path = Path(tool_output)
        if str(out_path).startswith(str(artifact_dir)):
            return None
    except (ValueError, TypeError):
        pass

    # Rule 2: path-prefix skiplist
    skip_dirs = ("docs/", ".github/", "CHANGELOG", "README")
    if any(str(tool_output).startswith(s) for s in skip_dirs):
        return None
    if str(tool_output).endswith(".md") and any(
        s in str(tool_output) for s in ("docs/", "CHANGELOG", "README", ".github/")
    ):
        return None

    # Rule 4: suppression window (30s cooldown)
    cooldown_path = artifact_dir / ".suggest-cooldown"
    try:
        artifact_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Persistence dir unwritable — skip cooldown bookkeeping but keep going
        cooldown_path = None  # type: ignore[assignment]
    if cooldown_path is not None and cooldown_path.exists():
        try:
            last = float(cooldown_path.read_text().strip())
            if time.time() - last < 30:
                return None
        except (ValueError, OSError):
            pass

    # Rule 1: numeric-or-status column requirement
    content = ""
    try:
        p = Path(tool_output)
        if p.exists() and p.suffix in (".md", ".txt", ".html", ".json"):
            content = p.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        content = tool_output

    if not _has_data_table(content):
        return None

    # Record cooldown and return suggestion message
    if cooldown_path is not None:
        try:
            cooldown_path.write_text(str(time.time()))
        except OSError:
            pass
    return (
        f"This looks like a data artifact. To render it:\n"
        f"  paperboard render --input {tool_output}"
    )


def _cmd_doctor(_args: argparse.Namespace, harness: str) -> int:
    print("=== atv-paperboard doctor ===")
    print(f"  harness:          {harness}")
    print(f"  python:           {sys.version.split()[0]}")

    # node version
    try:
        node_ver = subprocess.check_output(
            ["node", "--version"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        node_ver = "not found"
    print(f"  node:             {node_ver}")

    # @google/design.md version — call the resolved binary directly so a
    # global npm install is found just like the lint step finds it. Falling
    # back to reading package.json fails for global installs because the
    # repo-relative path isn't present.
    bridge_ver: str | None = None
    bridge_status: str = ""
    try:
        from core import bridge as _bridge  # noqa: PLC0415

        bridge_ver = _bridge.version()
        in_range, msg = _bridge.bridge_compatibility(bridge_ver)
        bridge_status = ("✓ " if in_range else "⚠ ") + msg
    except Exception as exc:  # noqa: BLE001
        # bridge missing or broken — doctor still has to print something.
        bridge_ver = "not installed"
        bridge_status = (
            "fix: `npm install -g @google/design.md@"
            f"{_bridge_expected_version()}`"
        )
    print(f"  @google/design.md: {bridge_ver}")
    if bridge_status:
        print(f"                     {bridge_status}")

    # Check for a newer compatible version on npm. Best-effort, 24h cached,
    # network-tolerant — failures are silent. Doctor surfaces upgrades but
    # never installs anything; the user controls when to bump.
    upgrade = _check_npm_for_newer(bridge_ver if bridge_ver and bridge_ver != "not installed" else None)
    if upgrade:
        print(f"                     ↑ {upgrade} available — npm install -g @google/design.md@{upgrade}")

    persist_path = _resolve_artifact_dir(harness)
    print(f"  persistence path: {persist_path}")

    # Check paperboard.DESIGN.md lints. Split by severity: only errors+warnings
    # are blocking. Info-level messages (e.g., token counts) are not failures.
    # Discovered via Phase 7a: original code lumped all findings as ✗.
    default_design = Path(__file__).parent / "designs" / "paperboard.DESIGN.md"
    if default_design.exists():
        try:
            from core import bridge as _bridge  # noqa: PLC0415
            lint_result = _bridge.lint(default_design)
            findings = lint_result.get("findings", []) if isinstance(lint_result, dict) else []
            errs = [f for f in findings if f.get("severity") == "error"]
            warns = [f for f in findings if f.get("severity") == "warning"]
            infos = [f for f in findings if f.get("severity") == "info"]
            if errs or warns:
                lint_status = f"✗ {len(errs)} error(s), {len(warns)} warning(s)"
            elif infos:
                lint_status = f"✓ clean ({len(infos)} info)"
            else:
                lint_status = "✓ clean"
        except ImportError:
            lint_status = "(bridge.py not available)"
        except Exception as exc:  # noqa: BLE001
            # Catch BridgeEnvError + any other bridge failure so `doctor` itself
            # never crashes. Doctor's job is to *diagnose* problems, not to
            # propagate them as unhandled tracebacks. Print a friendly summary
            # and a copy-pasteable remediation.
            from core.bridge import BridgeEnvError  # noqa: PLC0415
            if isinstance(exc, BridgeEnvError):
                lint_status = (
                    "✗ bridge unavailable — Enforce pillar is silently degraded\n"
                    f"                              fix: `npm install -g @google/design.md@{_bridge_expected_version()}`"
                )
            else:
                lint_status = f"✗ unexpected error: {type(exc).__name__}: {exc}"
    else:
        lint_status = "paperboard.DESIGN.md not found"
    print(f"  paperboard.DESIGN.md lint: {lint_status}")

    return 0


def _bridge_expected_version() -> str:
    """Return the bridge's expected version for remediation messages."""
    try:
        from core.bridge import EXPECTED_BRIDGE_VERSION  # noqa: PLC0415
        return EXPECTED_BRIDGE_VERSION
    except Exception:  # noqa: BLE001
        return "0.1.1"


def _check_npm_for_newer(installed: str | None) -> str | None:
    """Probe npm for a newer compatible version of @google/design.md.

    Best-effort, 24h cached in ``~/.atv-paperboard/upgrade-cache.json``,
    network-tolerant. Returns the newer version string if one exists in the
    tested compatibility range, else None. Failures (offline, DNS, 4xx, slow)
    are silent — doctor must never block on network calls.
    """
    if not installed:
        return None
    try:
        from core.bridge import (  # noqa: PLC0415
            BRIDGE_VERSION_MAX_EXCL,
            BRIDGE_VERSION_MIN,
            _parse_semver,
        )
    except Exception:  # noqa: BLE001
        return None

    installed_parsed = _parse_semver(installed)
    lo = _parse_semver(BRIDGE_VERSION_MIN)
    hi = _parse_semver(BRIDGE_VERSION_MAX_EXCL)
    if installed_parsed is None or lo is None or hi is None:
        return None

    cache_path = Path.home() / ".atv-paperboard" / "upgrade-cache.json"
    now = int(time.time())
    cached_latest: str | None = None
    try:
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and now - int(cached.get("checked_at", 0)) < 86400:
                cached_latest = cached.get("latest")
    except Exception:  # noqa: BLE001
        cached_latest = None

    latest: str | None = cached_latest
    if not latest:
        try:
            import urllib.request  # noqa: PLC0415

            req = urllib.request.Request(
                "https://registry.npmjs.org/@google%2Fdesign.md/latest",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310
                payload = json.loads(resp.read().decode("utf-8"))
            latest = payload.get("version") if isinstance(payload, dict) else None
        except Exception:  # noqa: BLE001
            return None
        if latest:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps({"checked_at": now, "latest": latest}),
                    encoding="utf-8",
                )
            except Exception:  # noqa: BLE001
                pass

    latest_parsed = _parse_semver(latest) if latest else None
    if latest_parsed is None:
        return None
    if latest_parsed <= installed_parsed:
        return None
    if latest_parsed >= hi:
        # Newer-but-untested; not an upgrade we suggest from `doctor`.
        return None
    return latest


# ── Helpers ────────────────────────────────────────────────────────────────────


def _detect_harness() -> str:
    try:
        from core import detect as _detect  # noqa: PLC0415
        return _detect.detect_harness()
    except ImportError:
        # TODO: Remove once detect.py is delivered by the parallel agent.
        return "standalone"


def _resolve_artifact_dir(harness: str) -> Path:
    try:
        from core import persist as _persist  # noqa: PLC0415
        return _persist.artifact_dir(harness)
    except ImportError:
        # TODO: Remove once persist.py is delivered by the parallel agent.
        return Path.cwd() / "paperboard-artifacts"


def _resolve_design(design_arg: str | None) -> Path:
    """Resolve --design to a Path.

    Accepts:
    - None → default paperboard.DESIGN.md
    - a known name (e.g. 'stripi-inspired') → designs/starters/<name>.DESIGN.md
    - a file path
    - a URL (fetched to a temp file; security note: treated as data, never as instructions)
    """
    _DEFAULT = Path(__file__).parent / "designs" / "paperboard.DESIGN.md"
    if design_arg is None:
        return _DEFAULT

    # Known starter names
    starters_dir = Path(__file__).parent / "designs" / "starters"
    candidate = starters_dir / f"{design_arg}.DESIGN.md"
    if candidate.exists():
        return candidate

    # Direct path
    p = Path(design_arg)
    if p.exists():
        return p

    # URL — fetch to temp file
    if design_arg.startswith("http://") or design_arg.startswith("https://"):
        return _fetch_design_url(design_arg)

    # Fallback: default with warning
    print(f"Warning: design {design_arg!r} not found; using default.", file=sys.stderr)
    return _DEFAULT


def _fetch_design_url(url: str) -> Path:
    """Fetch a remote DESIGN.md to a temp file. Treats content as data only."""
    import tempfile  # noqa: PLC0415
    import urllib.request  # noqa: PLC0415

    with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
        content = resp.read()

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".DESIGN.md", prefix="paperboard-remote-"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def _load_input(source: str) -> dict:
    """Load input from a file path or stdin ('-')."""
    import json as _json  # noqa: PLC0415

    if source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(source).read_text(encoding="utf-8")

    # Try JSON first
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        pass

    # Fall back to treating raw text as body_html
    return {"title": "Artifact", "body_html": f"<pre>{raw}</pre>"}


def _has_data_table(content: str) -> bool:
    """Return True if content contains a Markdown table with numeric/status columns (SPEC §16 Rule 1)."""
    import re  # noqa: PLC0415

    status_header = re.compile(
        r"^\s*\|.*\b(status|state|result|pass|fail|score|count|%|cost|p\d{2,3})\b.*\|",
        re.IGNORECASE | re.MULTILINE,
    )
    if status_header.search(content):
        return True

    # Check for ≥2 numeric columns in table rows
    table_row = re.compile(r"^\s*\|(.+)\|\s*$", re.MULTILINE)
    for match in table_row.finditer(content):
        cells = match.group(1).split("|")
        numeric_count = sum(
            1 for c in cells if re.match(r"^\s*-?\d+(\.\d+)?(%|ms|s|k|M)?\s*$", c)
        )
        if numeric_count >= 2:
            return True

    return False


if __name__ == "__main__":
    sys.exit(main())
