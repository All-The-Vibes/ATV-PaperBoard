"""tests/test_md_converter.py — built-in markdown converter contracts.

These tests pin behaviour of ``core.render._md_to_html()``, the dependency-free
markdown converter used when a ``.md`` file or ``body_md`` JSON field is the
render input. They guard the GFM subset documented in README.md against silent
regressions and against the two visible-defect bugs discovered in the
mega-corpus audit:

* HTML entities like ``&mdash;`` rendered as literal text because the inline
  escape pass double-escaped the ampersand into ``&amp;mdash;``.
* ATX headings ``#####`` and ``######`` rendered as literal text because the
  heading regex only matched 1-4 hashes; h5/h6 fell through to the paragraph
  branch.
"""
from __future__ import annotations

from core.render import _md_to_html

# ── HTML-entity handling ─────────────────────────────────────────────────────


def test_named_html_entity_renders_intact() -> None:
    """``&mdash;`` must reach the browser unmangled, not as ``&amp;mdash;``."""
    out = _md_to_html("An em-dash entity: &mdash; OK.")
    assert "&mdash;" in out
    assert "&amp;mdash;" not in out


def test_multiple_named_entities_render_intact() -> None:
    out = _md_to_html("Spacing: &nbsp; en-dash &ndash; copyright &copy;.")
    for ent in ("&nbsp;", "&ndash;", "&copy;"):
        assert ent in out, f"missing {ent!r} in {out!r}"
        assert f"&amp;{ent[1:]}" not in out


def test_numeric_entity_renders_intact() -> None:
    """Decimal (``&#8212;``) and hex (``&#x2014;``) entities also pass through."""
    out = _md_to_html("Decimal em-dash: &#8212;. Hex em-dash: &#x2014;.")
    assert "&#8212;" in out
    assert "&#x2014;" in out


def test_bare_ampersand_still_escaped() -> None:
    """A bare ``&`` (not part of an entity) must still be escaped to ``&amp;``
    so it's safe HTML. This is the property the entity-preserving fix must not
    break."""
    out = _md_to_html("A & B without an entity name.")
    assert "&amp; B" in out


def test_inline_html_tag_still_escaped() -> None:
    """Inline HTML in prose text must still be escaped (we only relax entities,
    not tags). ``<script>`` in prose must render as literal text."""
    out = _md_to_html("Prose with <script>alert(1)</script> embed.")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


# ── Heading levels ──────────────────────────────────────────────────────────


def test_heading_levels_1_through_6_emit_tags() -> None:
    """All six ATX heading levels must produce real ``<hN>`` tags."""
    src = "\n".join(f"{'#' * n} Level {n}" for n in range(1, 7))
    out = _md_to_html(src)
    for n in range(1, 7):
        assert f"<h{n}>Level {n}</h{n}>" in out, (
            f"heading level {n} did not render as <h{n}>. Got:\n{out}"
        )
    # The literal markdown markers must not survive.
    assert "##### Level 5" not in out
    assert "###### Level 6" not in out


def test_heading_with_trailing_hashes_supported() -> None:
    """The closing ``#`` decoration must be stripped at every level."""
    out = _md_to_html("###### Level six ######")
    assert "<h6>Level six</h6>" in out


# ── Inline construct preservation across the entity fix ─────────────────────


def test_entity_inside_emphasis_and_link() -> None:
    """Entities must survive the bold/italic/link rewriters, too."""
    out = _md_to_html("**Bold &mdash; em-dash** and a [link &mdash; arrow](https://example.com).")
    assert "<strong>Bold &mdash; em-dash</strong>" in out
    assert '<a href="https://example.com">link &mdash; arrow</a>' in out


def test_entity_inside_code_span_kept_literal() -> None:
    """Inside ``code``, content is intentionally escaped (so the user sees the
    literal source). ``&mdash;`` inside backticks remains ``&amp;mdash;``
    because that's what the author typed and the displayed code should match."""
    out = _md_to_html("Source: `&mdash;` literal.")
    assert "<code>&amp;mdash;</code>" in out
