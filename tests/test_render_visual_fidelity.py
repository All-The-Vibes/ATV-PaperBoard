"""tests/test_render_visual_fidelity.py — headless-browser render-fidelity guards.

Two guards:
1. Pico tier — the cascade-loss bug must not regress. DESIGN.md primary color
   must reach the rendered <h1>.
2. ATV tier — the new dark-document tier must produce a dark canvas at the
   pixel level, not just write the right hex to a `<style>` block.

If Chrome isn't installed on the test host, both tests are skipped.
"""
from __future__ import annotations

import http.server
import os
import shutil
import socketserver
import subprocess
import threading
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = REPO_ROOT / "designs"
INPUTS_DIR = REPO_ROOT / "examples" / "inputs"


def _find_chrome() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chrome"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


CHROME = _find_chrome()
HAS_PIL = True
try:
    from PIL import Image  # type: ignore
except ImportError:
    HAS_PIL = False


pytestmark = [
    pytest.mark.skipif(CHROME is None, reason="Chrome/Chromium not found"),
    pytest.mark.skipif(not HAS_PIL, reason="Pillow not installed"),
]


@pytest.fixture()
def http_server(tmp_path: Path):
    """Spin up local HTTP server rooted at tmp_path. Yields the base URL."""
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(tmp_path), **kwargs)

        def log_message(self, *_a, **_kw):
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _dominant_color(img, x0: int, y0: int, x1: int, y1: int,
                    ignore_near_white: bool = True) -> tuple[int, int, int] | None:
    pixels = []
    for y in range(y0, y1, 3):
        for x in range(x0, x1, 3):
            r, g, b = img.getpixel((x, y))
            if ignore_near_white and r > 240 and g > 240 and b > 240:
                continue
            pixels.append((r, g, b))
    return Counter(pixels).most_common(1)[0][0] if pixels else None


def _close(a, b, tol: int = 4) -> bool:
    return all(abs(x - y) <= tol for x, y in zip(a, b, strict=False))


def _render_and_shot(input_path: Path, out_dir: Path, http_base: str,
                     tier: str, design: Path | None = None) -> Path:
    from core.cli import main as cli_main

    args = ["render", "--input", str(input_path),
            "--output-dir", str(out_dir), "--no-open", "--tier", tier]
    if design is not None:
        args += ["--design", str(design)]
    rc = cli_main(args)
    assert rc == 0, f"render failed for tier={tier}"

    htmls = [p for p in out_dir.glob("*.html") if p.name != "gallery.html"]
    assert len(htmls) == 1, f"expected 1 artifact, got {[p.name for p in htmls]}"
    html_path = htmls[0]

    png = out_dir / f"{html_path.stem}.png"
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--window-size=1280,900",
        "--virtual-time-budget=20000",
        "--run-all-compositor-stages-before-draw",
        f"--screenshot={png}",
        f"{http_base}/{html_path.name}",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    assert png.exists(), (
        f"chrome failed (exit {result.returncode}): "
        f"{result.stderr.decode(errors='replace')[:300]}"
    )
    return png


def test_pico_tier_cascade_fidelity(tmp_path: Path, http_server: str):
    """Pico tier: DESIGN.md colors.primary must reach the rendered <h1>.

    Guards the v0.1.1 -> v0.1.2 cascade-loss fix. If anyone removes !important
    from templates/pico-tier.html.j2, this test catches it.
    """
    input_path = INPUTS_DIR / "build-status.json"
    png = _render_and_shot(input_path, tmp_path, http_server, tier="pico")
    img = Image.open(png).convert("RGB")

    expected_primary = _hex_to_rgb("#1A1A1A")
    expected_bg = _hex_to_rgb("#FAFAFA")

    bg_pixel = img.getpixel((5, 5))
    h1_pixel = _dominant_color(img, 60, 60, 700, 110)

    assert _close(bg_pixel, expected_bg, tol=3), (
        f"pico body background mismatch: expected ~{expected_bg}, got {bg_pixel}. "
        f"Cascade lost — DESIGN.md `colors.background` not applied."
    )
    assert h1_pixel is not None and _close(h1_pixel, expected_primary, tol=3), (
        f"pico H1 color mismatch: expected ~{expected_primary}, got {h1_pixel}. "
        f"DESIGN.md `colors.primary` not reaching --pico-h1-color."
    )


def test_atv_tier_dark_canvas(tmp_path: Path, http_server: str):
    """ATV tier: page must render with the dark canvas from atv.DESIGN.md.

    Confirms the section-emitter pipeline + tokenized atv-tier.html.j2 produce
    a visually dark document, not just write the right hex into <style>.
    """
    input_path = INPUTS_DIR / "atv-showcase.json"
    if not input_path.exists():
        pytest.skip(f"atv-showcase fixture missing at {input_path}")

    design_path = DESIGNS_DIR / "atv.DESIGN.md"
    png = _render_and_shot(input_path, tmp_path, http_server,
                           tier="atv", design=design_path)
    img = Image.open(png).convert("RGB")

    expected_bg = _hex_to_rgb("#08090a")
    bg_pixel = img.getpixel((5, 5))

    assert _close(bg_pixel, expected_bg, tol=4), (
        f"atv body background mismatch: expected ~{expected_bg}, got {bg_pixel}. "
        f"DESIGN.md `colors.background` not applied to atv tier."
    )

    # Confirm the dark canvas dominates — at least 30% of sampled body pixels
    # should be the dark background (rules out a single light/white element
    # accidentally taking over the page).
    w, h = img.size
    dark_count = 0
    total = 0
    for y in range(100, h - 100, 6):
        for x in range(50, w - 50, 6):
            px = img.getpixel((x, y))
            total += 1
            if _close(px, expected_bg, tol=15):
                dark_count += 1
    assert total > 0
    dark_ratio = dark_count / total
    assert dark_ratio > 0.30, (
        f"atv tier did not produce a dark-dominant canvas: only {dark_ratio:.1%} "
        f"of sampled pixels are near rgb{expected_bg}. Expected >30%."
    )
