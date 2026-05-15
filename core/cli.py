"""core/cli.py — Universal CLI entry point for atv-paperboard.

Subcommands:
  render                 — render an artifact triple
  validate               — run ENFORCE checks on a slug
  regenerate             — 3-step retry for a failing slug
  gallery                — placeholder (Phase 6)
  detect-artifact-candidate — PostToolUse hook helper (Phase 4 hook heuristics; §16)
  doctor                 — diagnose install

Every command resolves harness via detect.detect_harness() first.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


# ── Main ──────────────────────────────────────────────────────────────────────


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
        choices=["pico", "daisy"],
        default="pico",
        help="CSS framework tier (default: pico)",
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

    # regenerate
    p_regen = sub.add_parser("regenerate", help="3-step differentiated retry")
    p_regen.add_argument("slug", help="Failing artifact slug")

    # gallery (Phase 6 placeholder)
    sub.add_parser("gallery", help="[Phase 6] Build compounding gallery (placeholder)")

    # detect-artifact-candidate (Phase 4 placeholder; hook helper)
    p_detect = sub.add_parser(
        "detect-artifact-candidate",
        help="PostToolUse hook helper — checks if Write output is an artifact candidate",
    )
    p_detect.add_argument("tool_output", nargs="?", default="", help="TOOL_OUTPUT JSON string")

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
    elif args.command == "detect-artifact-candidate":
        return _cmd_detect_artifact_candidate(args, harness)
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

    return 0


def _cmd_validate(args: argparse.Namespace, harness: str) -> int:
    from core.validate import validate_artifact  # noqa: PLC0415

    result = validate_artifact(args.slug, harness)
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
    from core.validate import validate_artifact  # noqa: PLC0415
    from core import regenerate as _regen  # noqa: PLC0415

    # Validate current slug first
    initial = validate_artifact(args.slug, harness)
    if initial.passed:
        print(f"✓ slug={args.slug} already passes; no regeneration needed.")
        return 0

    result = _regen.regenerate(args.slug, initial)
    step = result["retry_step"]
    new_slug = result["new_slug"]
    vr = result["validation"]
    status = "ACCEPT" if vr.passed else "FAIL"
    print(f"Regenerate step={step}  new_slug={new_slug}  status={status}({vr.fail_class})")
    return 0 if vr.passed else 1


def _cmd_gallery(_args: argparse.Namespace, _harness: str) -> int:
    print("[gallery] Phase 6 placeholder — not yet implemented.")
    return 0


def _cmd_detect_artifact_candidate(args: argparse.Namespace, harness: str) -> int:
    """Hook heuristic rules per SPEC §16. Exits 0 silently if not a candidate."""
    import re  # noqa: PLC0415
    import time  # noqa: PLC0415

    tool_output = args.tool_output or os.environ.get("TOOL_OUTPUT", "")

    # Rule 3: self-recursion guard
    artifact_dir = _resolve_artifact_dir(harness)
    try:
        out_path = Path(tool_output)
        if str(out_path).startswith(str(artifact_dir)):
            return 0
    except (ValueError, TypeError):
        pass

    # Rule 2: path-prefix skiplist
    skip_dirs = ("docs/", ".github/", "CHANGELOG", "README")
    if any(str(tool_output).startswith(s) for s in skip_dirs):
        return 0
    if str(tool_output).endswith(".md") and any(
        s in str(tool_output) for s in ("docs/", "CHANGELOG", "README", ".github/")
    ):
        return 0

    # Rule 4: suppression window (30s cooldown)
    cooldown_path = artifact_dir / ".suggest-cooldown"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if cooldown_path.exists():
        try:
            last = float(cooldown_path.read_text().strip())
            if time.time() - last < 30:
                return 0
        except (ValueError, OSError):
            pass

    # Rule 1: numeric-or-status column requirement
    # Try to read the file to check for table content
    content = ""
    try:
        p = Path(tool_output)
        if p.exists() and p.suffix in (".md", ".txt", ".html", ".json"):
            content = p.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        content = tool_output

    if not _has_data_table(content):
        return 0

    # Emit suggestion
    cooldown_path.write_text(str(time.time()))
    print(
        f"\n[atv-paperboard] This looks like a data artifact. "
        f"To render it:\n  paperboard render --input {tool_output}\n"
    )
    return 0


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

    # @google/design.md version
    try:
        pkg_json = Path(__file__).parent.parent / "node_modules" / "@google" / "design.md" / "package.json"
        if pkg_json.exists():
            import json as _json  # noqa: PLC0415
            data = _json.loads(pkg_json.read_text())
            bridge_ver = data.get("version", "unknown")
        else:
            bridge_ver = "not installed"
    except Exception:
        bridge_ver = "error reading"
    print(f"  @google/design.md: {bridge_ver}")

    persist_path = _resolve_artifact_dir(harness)
    print(f"  persistence path: {persist_path}")

    # Check paperboard.DESIGN.md lints
    default_design = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"
    if default_design.exists():
        try:
            from core import bridge as _bridge  # noqa: PLC0415
            findings = _bridge.lint(default_design)
            lint_status = "✓ clean" if not findings else f"✗ {len(findings)} finding(s)"
        except ImportError:
            lint_status = "(bridge.py not available)"
    else:
        lint_status = "paperboard.DESIGN.md not found"
    print(f"  paperboard.DESIGN.md lint: {lint_status}")

    return 0


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
    _DEFAULT = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"
    if design_arg is None:
        return _DEFAULT

    # Known starter names
    starters_dir = Path(__file__).parent.parent / "designs" / "starters"
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
