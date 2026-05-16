"""Named PaperBoard style registry.

Styles are the user-facing preset layer. They choose a bundled DESIGN.md and a
default renderer tier without making users learn the lower-level design/tier
split.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_STYLE_ID = "paperboard"
STYLE_ORDER = ("paperboard", "meridian", "atv")
STYLE_ROOT = Path(__file__).parent / "styles"


@dataclass(frozen=True)
class Style:
    id: str
    name: str
    description: str
    design_path: Path
    default_tier: str
    aliases: tuple[str, ...]
    best_for: tuple[str, ...]
    source_path: Path


class UnknownStyleError(ValueError):
    """Raised when a style id or alias cannot be resolved."""

    def __init__(self, style_id: str, available: list[str]) -> None:
        self.style_id = style_id
        self.available = available
        super().__init__(
            f"Unknown style {style_id!r}. Available styles: {', '.join(available)}"
        )


def list_styles() -> list[Style]:
    """Return bundled styles in display order, with extra style folders appended."""
    styles: list[Style] = []
    seen: set[str] = set()

    for style_id in STYLE_ORDER:
        path = STYLE_ROOT / style_id / "style.yaml"
        if path.exists():
            style = _load_style(path)
            styles.append(style)
            seen.add(style.id)

    for path in sorted(STYLE_ROOT.glob("*/style.yaml")):
        if path.parent.name in seen:
            continue
        style = _load_style(path)
        styles.append(style)
        seen.add(style.id)

    return styles


def available_style_ids() -> list[str]:
    """Return canonical style ids in display order."""
    return [style.id for style in list_styles()]


def resolve_style(style_arg: str | None) -> Style:
    """Resolve a style id or alias. ``None`` means the PaperBoard default."""
    requested = style_arg or DEFAULT_STYLE_ID
    styles = list_styles()
    by_name: dict[str, Style] = {}

    for style in styles:
        by_name[style.id] = style
        for alias in style.aliases:
            by_name[alias] = style

    try:
        return by_name[requested]
    except KeyError as exc:
        raise UnknownStyleError(requested, [style.id for style in styles]) from exc


def _load_style(path: Path) -> Style:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    design_raw = data.get("design")
    if not design_raw:
        raise ValueError(f"Style file missing design: {path}")

    design_path = Path(str(design_raw))
    if not design_path.is_absolute():
        design_path = (path.parent / design_path).resolve()

    return Style(
        id=str(data.get("id") or path.parent.name),
        name=str(data.get("name") or data.get("id") or path.parent.name),
        description=str(data.get("description") or ""),
        design_path=design_path,
        default_tier=str(data.get("default_tier") or "atv"),
        aliases=tuple(str(alias) for alias in (data.get("aliases") or [])),
        best_for=tuple(str(item) for item in (data.get("best_for") or [])),
        source_path=path,
    )
