"""CLI style selection regression tests."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from core.cli import _resolve_design
from core.cli import main as cli_main


def _write_input(tmp_path: Path, title: str = "Style Default Test") -> Path:
    path = tmp_path / "input.json"
    path.write_text(json.dumps({"title": title, "body_md": "# Hello\n\nWorld"}), encoding="utf-8")
    return path


def _render(tmp_path: Path, *extra_args: str) -> tuple[int, Path, str]:
    input_path = _write_input(tmp_path)
    output_dir = tmp_path / "out"
    args = [
        "render",
        "--input",
        str(input_path),
        "--no-open",
        "--output-dir",
        str(output_dir),
        *extra_args,
    ]
    rc = cli_main(args)
    meta_files = sorted(output_dir.glob("*.meta.yaml"))
    slug = meta_files[0].stem.removesuffix(".meta") if meta_files else ""
    return rc, output_dir, slug


def test_resolve_design_defaults_to_paperboard_style() -> None:
    assert _resolve_design(None, style_arg=None).name == "paperboard.DESIGN.md"


def test_resolve_design_named_styles() -> None:
    assert _resolve_design(None, style_arg="paperboard").name == "paperboard.DESIGN.md"
    assert _resolve_design(None, style_arg="meridian").name == "meridian.DESIGN.md"
    assert _resolve_design(None, style_arg="atv").name == "atv.DESIGN.md"


def test_design_override_wins_over_style(tmp_path: Path) -> None:
    custom = tmp_path / "custom.DESIGN.md"
    custom.write_text("---\nversion: alpha\nname: custom\n---\n# Custom\n", encoding="utf-8")

    assert _resolve_design(str(custom), style_arg="meridian") == custom


def test_render_without_style_writes_paperboard_design(tmp_path: Path) -> None:
    rc, output_dir, slug = _render(tmp_path)

    assert rc == 0
    meta = yaml.safe_load((output_dir / f"{slug}.meta.yaml").read_text(encoding="utf-8"))
    assert Path(meta["design"]).name == "paperboard.DESIGN.md"


def test_render_named_style_writes_selected_design(tmp_path: Path) -> None:
    rc, output_dir, slug = _render(tmp_path, "--style", "meridian")

    assert rc == 0
    meta = yaml.safe_load((output_dir / f"{slug}.meta.yaml").read_text(encoding="utf-8"))
    assert Path(meta["design"]).name == "meridian.DESIGN.md"


def test_unknown_style_reports_available_options(tmp_path: Path, capsys) -> None:
    input_path = _write_input(tmp_path)
    rc = cli_main([
        "render",
        "--input",
        str(input_path),
        "--no-open",
        "--output-dir",
        str(tmp_path / "out"),
        "--style",
        "foo",
    ])

    captured = capsys.readouterr()
    assert rc == 2
    assert "Unknown style 'foo'" in captured.err
    assert "paperboard, meridian, atv" in captured.err


def test_styles_list_and_show_commands(capsys) -> None:
    rc = cli_main(["styles", "list"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "paperboard" in captured.out
    assert "meridian" in captured.out
    assert "atv" in captured.out

    rc = cli_main(["styles", "show", "meridian"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "Meridian" in captured.out
    assert "proposals" in captured.out
