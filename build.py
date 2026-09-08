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
THANKS_SRC = ROOT / "src" / "thanks.html"
IMAGES = ROOT / "images"
DIST = ROOT / "dist"

# Where the images live once uploaded to WordPress. WordPress files uploads
# under /wp-content/uploads/YYYY/MM/ by upload date -- if you upload in a
# different month, or WordPress renames a file on a name clash (it appends -1),
# change this to whatever the Media library shows as the File URL.
WP_MEDIA_BASE = "https://leadersseries.com/wp-content/uploads/2026/09/"

# Where the CV form returns after FormSubmit accepts it (its _next field needs
# an absolute URL, which differs per deployment).
SITE_URL = "https://leadersseries.github.io/"
WP_SITE_URL = "https://leadersseries.com/"

# FormSubmit falls back to its own confirmation page when _next carries a URL
# fragment, so the application form redirects to a real page instead.
THANKS_URL = SITE_URL + "thanks.html"
WP_THANKS_URL = WP_SITE_URL          # no such page on WordPress; land on the site
MAIL = "Christinabaroudi@gmail.com"

COLUMBIA = "columbia-low-memorial-library.jpg"
STANFORD = "stanford-main-quad.jpg"

# Company logos live in images/logos/. Each target rewrites __LOGO_BASE__ to
# whatever prefix works there: a relative folder, the WordPress media library,
# or (for the single-file build) an inlined data URI per logo.
LOGOS = "logos"

TITLE = "Leaders Series"
DESCRIPTION = (
    "Conversations with global decision-makers. An independent, student-led "
    "series at Columbia University and Stanford University."
)


def document(fragment: str, title: str = TITLE) -> str:
    """Wrap the fragment in a real HTML document.

    The viewport meta is not optional: without it a phone renders the page at
    desktop width and every mobile breakpoint is skipped.
    """
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{DESCRIPTION}">
<meta property="og:title" content="{title}">
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


def render(template: str, columbia: str, stanford: str, preloads: str = "",
           logo_base: str = "", site_url: str = SITE_URL,
           thanks_url: str = THANKS_URL) -> str:
    out = template.replace("__THANKS_URL__", thanks_url)
    out = out.replace("__SITE_URL__", site_url)
    out = out.replace("__IMG_COLUMBIA__", columbia)
    out = out.replace("__IMG_STANFORD__", stanford)
    out = out.replace("__LOGO_BASE__", logo_base)
    return out.replace("<!--__PRELOADS__-->", preloads)


def inline_logos(html: str) -> str:
    """Replace every remaining __LOGO_BASE__<file> with that file as a data URI."""
    def repl(m):
        name = m.group(1)
        path = IMAGES / LOGOS / name
        mime = "image/svg+xml" if name.endswith(".svg") else "image/png"
        return "data:%s;base64,%s" % (
            mime, base64.b64encode(path.read_bytes()).decode())
    return re.sub(r"__LOGO_BASE__([\w.\-]+)", repl, html)


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
        logo_base=f"images/{LOGOS}/",
    )
    (ROOT / "index.html").write_text(document(site), encoding="utf-8")

    # 2. WordPress / Elementor fragment
    wp = render(
        template,
        WP_MEDIA_BASE + COLUMBIA,
        WP_MEDIA_BASE + STANFORD,
        preload_tags(WP_MEDIA_BASE + COLUMBIA, WP_MEDIA_BASE + STANFORD),
        logo_base=WP_MEDIA_BASE,
        site_url=WP_SITE_URL,
        thanks_url=WP_THANKS_URL,
    )
    (DIST / "wordpress.html").write_text(wp, encoding="utf-8")

    # 3. one self-contained file
    # keep the token intact through render() so inline_logos can still see it
    single = inline_logos(render(template, data_uri(COLUMBIA), data_uri(STANFORD),
                                 logo_base="__LOGO_BASE__"))
    (DIST / "single-file.html").write_text(document(single), encoding="utf-8")

    # 4. the page FormSubmit redirects to after an application
    thanks = THANKS_SRC.read_text(encoding="utf-8")
    thanks = thanks.replace("__SITE_URL__", SITE_URL).replace("__MAIL__", MAIL)
    (ROOT / "thanks.html").write_text(
        document(thanks, title="Application received"), encoding="utf-8")

    for f in [ROOT / "index.html", ROOT / "thanks.html", *sorted(DIST.iterdir())]:
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size:>9,} bytes")

    # the standalone build must not smuggle in an absolute path to the author's
    # machine or to WordPress -- it has to work from any directory it is served
    body = (ROOT / "index.html").read_text(encoding="utf-8")
    for bad in ("leadersseries.com/wp-content", "/Users/", "file://",
                "__LOGO_BASE__", "__SITE_URL__"):
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
