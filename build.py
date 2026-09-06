#!/usr/bin/env python3
"""
Build the Leaders Series page into its three delivery formats.

    python3 build.py

Everything is generated from src/template.html. Never edit dist/ by hand —
it is overwritten on every build.

Outputs
    index.html             Standalone site, at the repo root so GitHub Pages
                           serves it with default settings (main branch, / root).
                           Loads the photographs from images/.
    dist/wordpress.html    Fragment for an Elementor HTML widget. Images point
                           at the WordPress media library (see WP_MEDIA_BASE).
    dist/single-file.html  One self-contained file, images inlined as data URIs.
                           No external assets at all — email it, open it from a
                           USB stick, drop it anywhere.
"""

import base64
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src" / "template.html"
IMAGES = ROOT / "images"
DIST = ROOT / "dist"

# Where the images live once uploaded to WordPress. WordPress files uploads
# under /wp-content/uploads/YYYY/MM/ by upload date -- if you upload in a
# different month, or WordPress renames a file on a name clash (it appends -1),
# change this to whatever the Media library shows as the File URL.
WP_MEDIA_BASE = "https://leadersseries.com/wp-content/uploads/2026/09/"

COLUMBIA = "columbia-low-memorial-library.jpg"
STANFORD = "stanford-main-quad.jpg"

TITLE = "Leaders Series"
DESCRIPTION = (
    "Conversations with global decision-makers. An independent, student-led "
    "series at Columbia University and Stanford University."
)


def document(fragment: str) -> str:
    """Wrap the fragment in a real HTML document.

    The viewport meta is not optional: without it a phone renders the page at
    desktop width and every mobile breakpoint is skipped.
    """
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:type" content="website">
<meta name="color-scheme" content="dark">
<style>html,body{{margin:0;padding:0;background:#0F1014}}</style>
</head>
<body>
{fragment}
</body>
</html>
"""


def data_uri(name: str) -> str:
    raw = (IMAGES / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode()


def render(template: str, columbia: str, stanford: str, preloads: str = "") -> str:
    out = template.replace("__IMG_COLUMBIA__", columbia)
    out = out.replace("__IMG_STANFORD__", stanford)
    return out.replace("<!--__PRELOADS__-->", preloads)


def preload_tags(*urls: str) -> str:
    return "\n".join(f'<link rel="preload" as="image" href="{u}">' for u in urls)


def main() -> int:
    if not SRC.exists():
        print(f"error: {SRC} not found", file=sys.stderr)
        return 1
    for img in (COLUMBIA, STANFORD):
        if not (IMAGES / img).exists():
            print(f"error: images/{img} not found", file=sys.stderr)
            return 1

    template = SRC.read_text(encoding="utf-8")
    DIST.mkdir(exist_ok=True)

    # 1. standalone site, at the repo root for zero-config GitHub Pages
    site = render(
        template,
        f"images/{COLUMBIA}",
        f"images/{STANFORD}",
        preload_tags(f"images/{COLUMBIA}", f"images/{STANFORD}"),
    )
    (ROOT / "index.html").write_text(document(site), encoding="utf-8")

    # 2. WordPress / Elementor fragment
    wp = render(
        template,
        WP_MEDIA_BASE + COLUMBIA,
        WP_MEDIA_BASE + STANFORD,
        preload_tags(WP_MEDIA_BASE + COLUMBIA, WP_MEDIA_BASE + STANFORD),
    )
    (DIST / "wordpress.html").write_text(wp, encoding="utf-8")

    # 3. one self-contained file
    single = render(template, data_uri(COLUMBIA), data_uri(STANFORD))
    (DIST / "single-file.html").write_text(document(single), encoding="utf-8")

    for f in [ROOT / "index.html", *sorted(DIST.iterdir())]:
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size:>9,} bytes")

    # the standalone build must not smuggle in an absolute path to the author's
    # machine or to WordPress -- it has to work from any directory it is served
    body = (ROOT / "index.html").read_text(encoding="utf-8")
    for bad in ("leadersseries.com/wp-content", "/Users/", "file://"):
        if bad in body:
            print(f"error: dist/index.html leaks {bad!r}", file=sys.stderr)
            return 1
    if not re.search(r'name="viewport"', body):
        print("error: dist/index.html is missing the viewport meta", file=sys.stderr)
        return 1
    print("\nok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
