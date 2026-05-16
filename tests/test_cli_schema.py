"""tests/test_cli_schema.py — Coverage for the `paperboard schema` subcommand.

Verifies the schema discovery subcommand emits the expected kinds, handles
unknown kinds with a non-zero exit + stderr message, and produces JSON that
round-trips. Pins the public contract that `core/section_schema.py` exposes the
same kind names as `core/render._SECTION_EMITTERS` — drift between the two will
break agent-side rendering.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest

from core.cli import main as cli_main
from core.section_schema import SECTION_SCHEMA, list_kinds


# Source-of-truth pin: the schema module and the emitter registry must agree.
def test_schema_matches_render_emitters() -> None:
    from core.render import _SECTION_EMITTERS

    schema_kinds = set(list_kinds())
    emitter_kinds = set(_SECTION_EMITTERS.keys())
    assert schema_kinds == emitter_kinds, (
        f"section_schema and _SECTION_EMITTERS diverged.\n"
        f"  in schema only: {schema_kinds - emitter_kinds}\n"
        f"  in emitters only: {emitter_kinds - schema_kinds}"
    )


def _run_cli(*argv: str) -> tuple[int, str, str]:
    """Invoke cli_main and capture (exit_code, stdout, stderr)."""
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = cli_main(list(argv))
    return rc, out_buf.getvalue(), err_buf.getvalue()


def test_schema_overview_lists_all_kinds() -> None:
    rc, out, _ = _run_cli("schema")
    assert rc == 0
    for kind in list_kinds():
        assert kind in out, f"kind {kind!r} missing from overview output"
    # Top banner present
    assert "atv-tier section kinds" in out
    assert "sections" in out  # mentions the input shape


def test_schema_list_kinds_one_per_line() -> None:
    rc, out, _ = _run_cli("schema", "--list-kinds")
    assert rc == 0
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines == list_kinds()


def test_schema_kind_detail_includes_example() -> None:
    rc, out, _ = _run_cli("schema", "--kind", "hero")
    assert rc == 0
    assert "kind: hero" in out
    assert "Fields:" in out
    assert "Example JSON:" in out
    # The example body should be valid JSON when extracted from the "Example JSON:" block.
    _, _, example_block = out.partition("Example JSON:")
    parsed = json.loads(example_block.strip())
    assert parsed["kind"] == "hero"
    assert "title" in parsed


def test_schema_unknown_kind_exits_2_with_stderr() -> None:
    rc, out, err = _run_cli("schema", "--kind", "definitely-not-real")
    assert rc == 2
    assert out == ""
    assert "Unknown section kind" in err
    # Lists the available kinds so the caller can fix their input.
    assert "hero" in err
    assert "status-table" in err


def test_schema_json_full_dump_round_trips() -> None:
    rc, out, _ = _run_cli("schema", "--format", "json")
    assert rc == 0
    parsed = json.loads(out)
    assert set(parsed.keys()) == set(list_kinds())
    # Every entry must have the three documented top-level fields.
    for name, entry in parsed.items():
        assert {"description", "fields", "example"} <= set(entry.keys()), (
            f"entry for {name!r} is missing required keys"
        )


def test_schema_json_single_kind() -> None:
    rc, out, _ = _run_cli("schema", "--format", "json", "--kind", "status-table")
    assert rc == 0
    parsed = json.loads(out)
    assert list(parsed.keys()) == ["status-table"]
    assert parsed["status-table"]["example"]["kind"] == "status-table"


# ── Schema integrity: examples are renderable by the real emitters ─────────────


@pytest.mark.parametrize("kind", list_kinds())
def test_every_example_is_renderable(kind: str) -> None:
    """Each documented example JSON must render without raising.

    This catches drift where the example payload doesn't match what the emitter
    actually expects (wrong field name, wrong type, etc.).
    """
    from core.render import _SECTION_EMITTERS

    entry = SECTION_SCHEMA[kind]
    example = entry["example"]
    emitter = _SECTION_EMITTERS[kind]
    html = emitter(example)
    assert isinstance(html, str)
    assert len(html) > 0


def test_smoke_run_via_subprocess_when_invoked_as_module() -> None:
    """Belt-and-suspenders: confirm the CLI also works when invoked as a module.

    The other tests call cli_main() directly. This one shells out via the same
    mechanism agents use, so a packaging / entry-point regression would be
    caught here even if the in-process path keeps working.
    """
    import subprocess

    proc = subprocess.run(
        [sys.executable, "-m", "core.cli", "schema", "--list-kinds"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines == list_kinds()
