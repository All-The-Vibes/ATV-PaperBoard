"""tests/test_cli_output_dir.py — Phase 7a UX regression tests.

Verifies that --output-dir is honoured by render, validate, and gallery
commands, and that auto-gallery-after-render writes to the correct dir.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.cli import main as cli_main

# ── Fixtures ──���───────────────────────────────────────────────────────────────


MINIMAL_INPUT = {
    "title": "CLI Output Dir Test",
    "rows": [
        {"label": "Alpha", "status": "pass", "score": 95},
        {"label": "Beta", "status": "fail", "score": 42},
    ],
}


@pytest.fixture()
def input_file(tmp_path: Path) -> Path:
    p = tmp_path / "input.json"
    p.write_text(json.dumps(MINIMAL_INPUT), encoding="utf-8")
    return p


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


# ── Helpers ───────────────────────────────────────────────────────────────────


def _render_to(input_file: Path, output_dir: Path) -> str:
    """Run render, capture stdout, return slug."""
    import io
    import sys

    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        rc = cli_main([
            "render",
            "--input", str(input_file),
            "--no-open",
            "--output-dir", str(output_dir),
        ])
    finally:
        sys.stdout = old_stdout

    assert rc == 0, f"render failed: {buf.getvalue()}"
    output = buf.getvalue()
    # Extract slug from "  Slug:   <slug>" line
    for line in output.splitlines():
        if line.strip().startswith("Slug:"):
            return line.split("Slug:")[-1].strip()
    raise AssertionError(f"Could not find slug in render output: {output}")


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_validate_with_output_dir(input_file: Path, output_dir: Path) -> None:
    """validate <slug> --output-dir <tmp> should succeed after render to that dir."""
    slug = _render_to(input_file, output_dir)

    rc = cli_main([
        "validate", slug,
        "--output-dir", str(output_dir),
    ])
    assert rc == 0, f"validate failed for slug={slug} in {output_dir}"


def test_auto_gallery_written_to_output_dir(input_file: Path, output_dir: Path) -> None:
    """After render --output-dir, gallery.html must appear in that same dir."""
    _render_to(input_file, output_dir)

    gallery_in_output = output_dir / "gallery.html"
    assert gallery_in_output.exists(), (
        f"gallery.html not found in --output-dir={output_dir}. "
        f"Files present: {list(output_dir.iterdir())}"
    )


def test_gallery_cmd_with_output_dir(input_file: Path, output_dir: Path) -> None:
    """gallery --output-dir <tmp> should regenerate against that dir."""
    slug = _render_to(input_file, output_dir)

    import io  # noqa: E401
    import sys
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        rc = cli_main(["gallery", "--output-dir", str(output_dir)])
    finally:
        sys.stdout = old_stdout

    assert rc == 0
    output = buf.getvalue()
    # Output line should reference the output_dir path
    assert str(output_dir) in output, f"gallery output didn't reference output_dir: {output}"

    gallery_path = output_dir / "gallery.html"
    assert gallery_path.exists()
    content = gallery_path.read_text(encoding="utf-8")
    # The slug should appear in the gallery (it was rendered there)
    assert slug in content, f"slug {slug!r} not found in gallery.html"
