"""tests/test_core_gallery.py — COMPOUND pillar tests for core/gallery.py."""
from __future__ import annotations

import datetime
import time
from pathlib import Path

import pytest
import yaml


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_mock_artifact(art_dir: Path, slug: str, title: str, index: int = 0) -> None:
    """Write a minimal HTML + DESIGN.md + meta.yaml triple into art_dir."""
    # HTML
    (art_dir / f"{slug}.html").write_text(
        f"<html><head><title>{title}</title></head><body><h1>{title}</h1></body></html>",
        encoding="utf-8",
    )
    # DESIGN.md sidecar
    (art_dir / f"{slug}.DESIGN.md").write_text(
        "---\nname: test\ncolors:\n  primary: \"#1A1A1A\"\n---\n# Test Design\n",
        encoding="utf-8",
    )
    # meta.yaml
    base = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    created = (base + datetime.timedelta(days=index)).isoformat()
    meta = {
        "slug": slug,
        "title": title,
        "harness": "standalone",
        "design": "designs/paperboard.DESIGN.md",
        "tier": "pico",
        "created_at": created,
        "lint_passed": True,
    }
    (art_dir / f"{slug}.meta.yaml").write_text(yaml.dump(meta), encoding="utf-8")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_gallery_renders_three_artifacts(tmp_path):
    """Render 3 mock artifacts; assert gallery.html exists with all 3 titles."""
    from core.gallery import regenerate_gallery

    art_dir = tmp_path / "paperboard-artifacts"
    art_dir.mkdir()

    titles = ["Alpha Report", "Beta Dashboard", "Gamma Summary"]
    for i, title in enumerate(titles):
        slug = title.lower().replace(" ", "-")
        _write_mock_artifact(art_dir, slug, title, i)

    # Monkey-patch _resolve_artifact_dir to use tmp_path
    import core.gallery as _gallery
    original = _gallery._resolve_artifact_dir
    _gallery._resolve_artifact_dir = lambda h: art_dir
    try:
        gallery_path = regenerate_gallery("standalone")
    finally:
        _gallery._resolve_artifact_dir = original

    assert gallery_path.exists(), "gallery.html was not written"
    content = gallery_path.read_text(encoding="utf-8")
    for title in titles:
        assert title in content, f"Title {title!r} not found in gallery"


def test_gallery_no_design_md_emitted(tmp_path):
    """Assert that regenerate_gallery does NOT write a gallery.DESIGN.md."""
    from core.gallery import regenerate_gallery

    art_dir = tmp_path / "paperboard-artifacts"
    art_dir.mkdir()
    _write_mock_artifact(art_dir, "test-slug", "Test Artifact", 0)

    import core.gallery as _gallery
    original = _gallery._resolve_artifact_dir
    _gallery._resolve_artifact_dir = lambda h: art_dir
    try:
        regenerate_gallery("standalone")
    finally:
        _gallery._resolve_artifact_dir = original

    assert not (art_dir / "gallery.DESIGN.md").exists(), \
        "gallery.DESIGN.md should NOT be created (SPEC §0.1 reuse-design rule)"


def test_gallery_auto_regen_after_render(tmp_path):
    """After render_artifact, gallery.html should be updated (via CLI auto-regen)."""
    from core.render import render_artifact
    from core.gallery import regenerate_gallery

    art_dir = tmp_path / "paperboard-artifacts"
    art_dir.mkdir()

    import core.gallery as _gallery
    original = _gallery._resolve_artifact_dir
    _gallery._resolve_artifact_dir = lambda h: art_dir
    try:
        # Render creates the artifact triple
        design = Path(__file__).parent.parent / "designs" / "paperboard.DESIGN.md"
        render_artifact(
            input_data={"title": "Auto Regen Test", "body_html": "<p>hello</p>"},
            design_path=design,
            tier="pico",
            output_dir=art_dir,
        )
        # Now regenerate gallery
        gallery_path = regenerate_gallery("standalone")
        assert gallery_path.exists()
        content = gallery_path.read_text(encoding="utf-8")
        assert "Auto Regen Test" in content or "auto-regen-test" in content
    finally:
        _gallery._resolve_artifact_dir = original


def test_gallery_performance_50_artifacts(tmp_path):
    """50 mock artifacts; regenerate_gallery must complete in < 5 seconds."""
    from core.gallery import regenerate_gallery

    art_dir = tmp_path / "paperboard-artifacts"
    art_dir.mkdir()

    for i in range(50):
        slug = f"artifact-{i:03d}"
        _write_mock_artifact(art_dir, slug, f"Artifact {i}", i)

    import core.gallery as _gallery
    original = _gallery._resolve_artifact_dir
    _gallery._resolve_artifact_dir = lambda h: art_dir
    try:
        t0 = time.perf_counter()
        regenerate_gallery("standalone")
        elapsed = time.perf_counter() - t0
    finally:
        _gallery._resolve_artifact_dir = original

    assert elapsed < 5.0, f"Gallery took {elapsed:.3f}s for 50 artifacts (limit: 5s)"
