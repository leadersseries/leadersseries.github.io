# Leaders Series

Homepage for [The Leaders Series](https://leadersseries.com) — *Conversations with
Global Decision-Makers*, an independent, student-led series at Columbia University
and Stanford University.

A single hand-written HTML page: no framework, no build dependencies, no npm.
Two typefaces from Google Fonts and two photographs. That's the whole site.

---

## Repository layout

```
src/template.html      The source. This is the only file you edit.
images/                The two campus photographs.
build.py               Generates the three outputs below.
index.html             GENERATED — the standalone site.
dist/wordpress.html    GENERATED — paste-in block for Elementor.
dist/single-file.html  GENERATED — one self-contained file.
```

**Edit `src/template.html`, never the generated files.** `index.html` and everything
in `dist/` are overwritten on every build.

## Building

```bash
python3 build.py
```

No dependencies — Python 3 standard library only. It prints the three file sizes,
then checks that the standalone build contains a viewport meta and no absolute
paths, and fails loudly if either is wrong.

## The three outputs

| File | Size | For |
|---|---|---|
| `index.html` | ~47 KB | Hosting the site anywhere. Loads images from `images/`. |
| `dist/wordpress.html` | ~47 KB | Pasting into an Elementor HTML widget on leadersseries.com. |
| `dist/single-file.html` | ~730 KB | One file, images embedded. No external assets at all. |

---

## Deploying

### Option A — into the existing WordPress site

The shortest route to a real page on leadersseries.com.

1. Upload both files from `images/` to **Media**.
2. Open each in Media and copy its **File URL**.
3. If those URLs differ from the two in `dist/wordpress.html`, update
   `WP_MEDIA_BASE` in `build.py` and re-run the build. (WordPress files uploads
   by date and appends `-1` on a name clash, so the path can shift.)
4. Paste `dist/wordpress.html` into an Elementor **HTML widget**.

If your theme header is still showing, delete the block in the pasted code marked
`>>> NAV — DELETE TO KEEP THEME HEADER <<<`, otherwise you get two navigations.

### Option B — GitHub Pages

`index.html` sits at the repo root specifically so this needs no configuration:
**Settings → Pages → Deploy from a branch → `main` / `/ (root)`**.

You get `https://<username>.github.io/leaders-series/`. To serve it at
leadersseries.com instead, add a `CNAME` file containing the domain and point the
DNS at GitHub.

**Free-tier caveat:** GitHub Pages only publishes from a **public** repository
unless you have GitHub Pro. If this repo needs to stay private, use Netlify or
Cloudflare Pages — both deploy from a private repo on their free tier, and both
just need "no build command, publish directory `/`".

### Option C — anywhere else

`index.html` plus `images/` is a complete static site. Drag the folder onto Netlify
Drop, or upload it to any host. There is no server-side anything.

---

## Notes on the build

- **Namespaced.** Every style is scoped under `.ls-root`, so the block can be
  pasted into WordPress without colliding with the theme's CSS in either direction.
- **Works without JavaScript.** All content is visible; JS only adds the menu,
  the scroll-telling, and the reveals. Sections already scrolled past are revealed
  immediately on load, so a deep link like `#events` never leaves the sections
  above it blank.
- **Respects `prefers-reduced-motion`.** The sticky scroll-telling stage collapses
  to a plain stacked layout.
- **Single-theme dark, deliberately.** The page paints its own background rather
  than inheriting one, so it looks the same regardless of the visitor's theme.

## Photograph credits

Both photographs are used under Creative Commons licences that **require
attribution**. The credit line is in the page footer — if you rework the footer,
keep it. Full details in [CREDITS.md](CREDITS.md).

## Content

Copy is drawn from the existing leadersseries.com pages (Home, Events, Connect) and
kept verbatim where possible. Two typos from the live site are corrected here:
*excutives* → executives, *Prespective* → Perspective.
