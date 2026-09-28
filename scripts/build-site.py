#!/usr/bin/env python3
"""Build the site from stories.json.

stories.json is the single source of truth. This script writes:

  index.html                  the LANDING page (what a parent lands on)
  app/index.html              the reader app, generated from the same source
  stories/index.html          a plain index of every story
  stories/<slug>/index.html   one crawlable page per story (OG tags, canonical, cover)
  404.html                     a not-found page that offers a way back
  sitemap.xml, robots.txt     so search engines can find those pages

Why the app moved to /app/: "/" used to be the app, which meant the entry
URL had no description, no OG tags and no share image, and a crawler got
an empty shelf. A visitor and a search engine need different pages.
The app is generated, not hand-maintained, so there is still one source.

Why generate: one story URL per story is the difference between "an app in a browser"
and a site people can find and share. Adding a story = append to stories.json, re-run.

  ./scripts/build-site.py            # regenerate everything
  ./scripts/build-site.py --check    # report drift/duplicates, write nothing
"""
import base64
import html
import json
import pathlib
import re
import sys
import urllib.parse
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://yanbing2026.github.io/story-twirl"
PREFIX = urllib.parse.urlsplit(SITE).path.rstrip("/")   # "" on a custom domain
STORIES = ROOT / "stories.json"
BEGIN = "/* STORIES:BEGIN"
END = "/* COVERS:END */"

CSS = """
:root{--bg:#1b1436;--bg2:#241a4a;--card:#2c2158;--ink:#f4f1ff;--dim:#b9aee6;--accent:#ffd166;--accent2:#7ee0c1;--line:#3d2f70}
*{box-sizing:border-box}
body{margin:0;background:linear-gradient(170deg,var(--bg),var(--bg2) 60%,#150f2c);color:var(--ink);
  font:18px/1.7 ui-rounded,"Segoe UI",system-ui,-apple-system,sans-serif;min-height:100%}
.wrap{max-width:680px;margin:0 auto;padding:22px 20px 60px}
a{color:var(--accent2)}
header a{color:var(--dim);text-decoration:none;font-size:15px;letter-spacing:.3px}
h1{font-size:30px;line-height:1.2;margin:14px 0 6px}
.meta{color:var(--dim);font-size:14px;margin-bottom:18px}
img.cover{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:14px;margin:0 0 22px;background:#150f2c}
p{margin:0 0 16px}
.lesson{background:#1a1236;border-left:3px solid var(--accent2);border-radius:10px;padding:14px 16px;margin:24px 0}
.lesson b{color:var(--accent2)}
.cta{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;margin:26px 0}
.cta a.btn{display:inline-block;background:var(--accent);color:#2a1c00;font-weight:650;border-radius:999px;
  padding:12px 20px;text-decoration:none;margin-top:10px}
footer{margin-top:30px;color:var(--dim);font-size:14px;text-align:center}
ul.index{list-style:none;padding:0}
ul.index li{margin:14px 0;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
ul.index a{display:block;text-decoration:none;color:var(--ink)}
ul.index img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}
ul.index .txt{padding:12px 14px}
ul.index small{color:var(--dim)}

/* ---- landing page only (the app has its own stylesheet) ---- */
.hero{padding:38px 0 8px;text-align:center}
.hero .dot{display:inline-block;width:12px;height:12px;border-radius:50%;
  background:var(--accent);box-shadow:0 0 14px rgba(255,209,102,.5);margin-bottom:14px}
.hero h1{font-size:34px;line-height:1.18;margin:0 0 14px;letter-spacing:-.4px}
.lead{color:var(--dim);font-size:17px;line-height:1.65;margin:0 auto 24px;max-width:46ch}
a.btn{display:inline-block;background:var(--accent);color:#2a1c00;font-weight:650;
  border-radius:999px;padding:14px 26px;text-decoration:none;font-size:17px}
a.btn.big{padding:16px 34px;font-size:18px}
a.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
a.btn:hover{filter:brightness(1.07)}
.facts{display:grid;gap:12px;margin:30px 0}
.facts div{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 17px}
.facts b{display:block;font-size:16px;margin-bottom:4px;color:var(--ink)}
.facts span{color:var(--dim);font-size:14.5px;line-height:1.55}
.wall h2{font-size:23px;margin:34px 0 4px}
.wall .sub{color:var(--dim);font-size:15px;margin:0 0 18px}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
a.c{display:block;text-decoration:none;color:var(--ink);background:var(--card);
  border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:transform .12s ease}
a.c:hover{transform:translateY(-3px)}
a.c img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;background:#150f2c}
a.c b{display:block;padding:12px 14px 2px;font-size:16px;line-height:1.3}
a.c small{display:block;padding:0 14px 10px;color:var(--dim);font-size:13.5px;line-height:1.45}
a.c em{display:block;padding:0 14px 14px;color:var(--accent);font-size:12.5px;
  font-style:normal;font-weight:650;letter-spacing:.4px}
.cta{text-align:center;margin:34px 0}
.cta h2{margin-bottom:8px}
.cta p{color:var(--dim)}
.cta a.btn{margin:6px 5px}
.nf{text-align:center;padding-top:60px}
.nf h1{margin-bottom:10px}
.nf .lead{margin-bottom:26px}
.nf .btn{margin:5px}
@media (min-width:860px){
  .wrap{max-width:900px;padding:26px 24px 70px}
  .facts{grid-template-columns:repeat(3,1fr);gap:14px}
  .hero{padding:54px 0 10px}
  .hero h1{font-size:44px;max-width:19ch}
}
"""


def esc(s):
    return html.escape(s, quote=True)


def plain(s):
    """Resolve the personalisation placeholders for a static, nameless page."""
    return s.replace("{{namePos}}", "your child's").replace("{{name}}", "your child")


def load():
    stories = json.loads(STORIES.read_text())
    seen, seen_paras = set(), set()
    for s in stories:
        if s["slug"] in seen:
            raise SystemExit(f"duplicate slug: {s['slug']}")
        seen.add(s["slug"])
        for k in ("id", "slug", "title", "blurb", "minutes", "cover", "lesson", "body"):
            if k not in s:
                raise SystemExit(f"{s.get('slug')}: missing field {k}")
        # Contract: body is a FLAT list of paragraph strings, and the app renders s.body.
        # (It used to be [[...]] and a regenerated block silently broke openStory.)
        if not (isinstance(s["body"], list) and s["body"]
                and all(isinstance(p, str) for p in s["body"])):
            raise SystemExit(f"{s['slug']}: body must be a non-empty list of paragraph strings")
        # Ending contract. Without this, 'THE END.' drifts to a lowercase
        # 'The end.' and the narrator reads it as just another sentence.
        if s["body"][-1].strip() != "THE END.":
            raise SystemExit(f"{s['slug']}: last paragraph must be exactly 'THE END.', "
                             f"got {s['body'][-1].strip()[:40]!r}")
        if sum(1 for q in s["body"] if q.strip() == "THE END.") != 1:
            raise SystemExit(f"{s['slug']}: 'THE END.' must appear exactly once")
        # Length contract. These are read ALOUD to a 3-6 year old at bedtime.
        # The three originals ship at 431-521 words; a story twice that long is
        # not a longer bedtime story, it is one the child falls asleep halfway
        # through. Cap it rather than trusting the writer's own label.
        # Blurb length is a layout constraint, not taste: it renders on one line
        # under the title on the landing-page card. Nothing enforced it, so a
        # rewrite could quietly wrap and break the grid.
        if len(s["blurb"]) >= 70:
            raise SystemExit(f"{s['slug']}: blurb is {len(s['blurb'])} chars, must be under 70")
        # A slug is the URL a parent might search for. If the title's own words
        # do not appear in it, the page can only be found by typing the slug --
        # which is how 'mabel-and-the-slab' ended up invisible.
        title_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", s["title"])}
        slug_words = set(s["slug"].split("-"))
        if not (title_words & slug_words):
            raise SystemExit(
                f"{s['slug']}: slug shares no word with the title {s['title']!r}, so it "
                f"matches nothing a parent would search for. Rename it, and list the "
                f"old slug in REDIRECTS to keep the old URL alive.")
        words = sum(len(q.split()) for q in s["body"])
        if not (250 <= words <= 750):
            raise SystemExit(f"{s['slug']}: {words} words is outside the 250-750 "
                             f"bedtime band (stated {s['minutes']} min)")
        # Prose duplicated across two stories reads as a bug to a parent, and a
        # copied one-liner is the usual cause. (The shared closing is exempt.)
        for q in s["body"]:
            if q.strip() in seen_paras and q.strip() != "THE END.":
                raise SystemExit(f"{s['slug']}: paragraph reused from another story: "
                                 f"{q.strip()[:50]!r}")
            seen_paras.add(q.strip())
    return stories


def covers_inlined(stories):
    """Inline each cover as a data URI, skipping any whose file is absent.

    A missing cover must never stop a build: the app already renders a story
    without art (no COVERS entry, no <img>), and a shelf of 13 stories should
    still publish while 10 illustrations are still being made. It used to
    raise FileNotFoundError and take the whole build down with it."""
    out = {}
    for s in stories:
        p = ROOT / s["cover"]
        if not p.exists():
            print(f"  no cover yet for {s['id']} (renders without art): {s['cover']}")
            continue
        out[s["id"]] = "data:image/webp;base64," + base64.b64encode(p.read_bytes()).decode()
    return out


def build_stamp():
    """Short sha + date, so 'did the site update?' is answerable without asking anyone."""
    import subprocess
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        sha = ""
    return f"{sha or 'nogit'} {datetime.now().strftime('%Y-%m-%dT%H:%M')}"


def build_short():
    """What the status line shows: the moment of the build, so 'did it refresh?'
    needs no sha comparison."""
    return datetime.now().strftime("%m-%d %H:%M")


def app_block(stories):
    """The generated JS data block inside index.html."""
    lines = [f"{BEGIN} — generated by scripts/build-site.py from stories.json; do not hand-edit */",
             f"const BUILD = {json.dumps(build_short())};",
             "const STORIES = ["]
    for s in stories:
        body = json.dumps(s["body"], ensure_ascii=False, indent=1).replace("\n", "\n ")
        lines.append(" {")
        lines.append(f"  id: {json.dumps(s['id'])}, title: {json.dumps(s['title'], ensure_ascii=False)},")
        lines.append(f"  blurb: {json.dumps(s['blurb'], ensure_ascii=False)}, minutes: {s['minutes']},")
        lines.append(f"  body: {body},")
        lines.append(f"  lesson: {json.dumps(s['lesson'], ensure_ascii=False)}")
        lines.append(" },")
    lines.append("];")
    lines.append("const COVERS = {")
    for sid, uri in sorted(covers_inlined(stories).items()):
        lines.append(f"  {sid}: '{uri}',")
    lines.append("};")
    lines.append(END)
    return "\n".join(lines)


APP = ROOT / "app" / "index.html"

# Slugs that have been published under a different name. GitHub Pages cannot
# 301, so the old path stays as a real page that redirects. Keep the old path
# alive for as long as it has been public; delete it once the old URLs have
# aged out of search results.
REDIRECTS = {
    "mabel-and-the-slab": "the-worm-under-the-garden-slab",
}


def build_app(stories):
    """Regenerate the app's data block in place.

    The app lives at app/index.html and is a generated file, but the generator
    only rewrites its STORIES/COVERS region -- the surrounding HTML is authored
    once by hand and preserved. That is the one place where a hand edit is
    correct, and it is overwritten on every build, so treat app/index.html as
    generated.
    """
    if not APP.exists():
        raise SystemExit(
            "app/index.html is missing. It is the reader app and the asset the "
            "Android build syncs; the landing page cannot replace it. Restore it "
            "from git (git show 21d903a:index.html > app/index.html).")
    html_src = APP.read_text()
    # Match from the BEGIN marker, not from `const STORIES = [`, or anything the
    # generator writes above that line (the BUILD stamp) accumulates on every run.
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if not pat.search(html_src):
        raise SystemExit("index.html: could not find the generated STORIES/COVERS region")
    new = pat.sub(lambda _: app_block(stories), html_src, count=1)
    APP.write_text(new)
    return len(html_src), len(new)


def page(title, desc, canonical, body, og_image=None, head_extra=""):
    """head_extra goes inside <head>. A <meta http-equiv="refresh"> placed in
    <body> is ignored by every browser, so a redirect page has to inject it
    here rather than in the body markup."""
    og = f'<meta property="og:image" content="{SITE}/{og_image}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#1b1436">
<meta name="build" content="{build_stamp()}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
{og}
<meta name="twitter:card" content="summary_large_image">
{head_extra}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>
"""


def landing_page(stories):
    """The page a parent lands on. Says what this is, for whom, how to use it,
    then shows every story. Every claim here is checkable against the app:
    no accounts, no server, one story a night."""
    n = len(stories)
    mins = sum(st["minutes"] for st in stories)
    cards = "".join(
        f'<a class="c" href="{PREFIX}/stories/{st["slug"]}/">'
        f'<img src="{PREFIX}/{st["cover"]}" alt="" loading="lazy" width="900" height="506">'
        f'<b>{esc(st["title"])}</b>'
        f'<small>{esc(st["blurb"])}</small>'
        f'<em>{st["minutes"]} min</em></a>'
        for st in stories)
    desc = (f"Free bedtime stories for children aged 3-6 that read themselves "
            f"aloud in your own device's voice. No accounts, no ads, no server. "
            f"One story every night, free.")
    body = f"""
<header class="hero">
  <span class="dot" aria-hidden="true"></span>
  <h1>A story a night, read aloud by the device itself</h1>
  <p class="lead">{esc(desc)}</p>
  <a class="btn big" href="{PREFIX}/app/">Tonight's story &rarr;</a>
</header>

<section class="facts">
  <div><b>One free story every night</b><span>The shelf unlocks again at midnight. Membership is only for more in one night.</span></div>
  <div><b>Offline, on your own device</b><span>It uses the phone's built-in voice. Nothing is uploaded, because there is no server to upload to.</span></div>
  <div><b>No account, no ads, no tracking</b><span>One optional first name, kept on the device and never sent anywhere.</span></div>
</section>

<section class="wall">
  <h2>All {n} stories</h2>
  <p class="sub">{mins} minutes of stories in total, each with a question to talk about afterwards.</p>
  <div class="grid">{cards}</div>
</section>

<section class="cta">
  <h2>Tonight, in about four minutes</h2>
  <p>The app opens on one story. Press play and the device reads it aloud in a calm voice, then stops.
     If the child wants another, that is what membership is for.</p>
  <a class="btn" href="{PREFIX}/app/">Open the app</a>
  <a class="btn ghost" href="{PREFIX}/stories/">Read without the app</a>
</section>

<footer>Story Twirl &middot; a story a night &middot; ages 3-6 &middot; no accounts, no ads, no server</footer>"""
    return page("Story Twirl — a free bedtime story every night, read aloud offline",
                desc, f"{SITE}/", body,
                og_image=stories[0]["cover"] if stories else None)


def not_found_page():
    body = f"""
<div class="wrap nf">
  <h1>That story has gone to bed</h1>
  <p class="lead">This page does not exist. It may have been renamed, or the link
     may have a typo in it.</p>
  <a class="btn" href="{PREFIX}/">Back to Story Twirl</a>
  <a class="btn ghost" href="{PREFIX}/stories/">All stories</a>
</div>"""
    return page("Not found — Story Twirl", "This page does not exist.",
                f"{SITE}/404.html", body)


def redirect_page(old_slug, new_slug):
    """A real page at the old URL that forwards to the new one.

    GitHub Pages has no redirect support, so this is the honest way to keep an
    old link alive: the visitor lands on a page that immediately forwards, and
    the canonical link tells a crawler the new address. The meta refresh also
    covers no-JS, and the visible link is there if the script is blocked."""
    dest = f"{PREFIX}/stories/{new_slug}/"
    # A plain string, not an f-string with an HTML entity: page() escapes the
    # title, so writing &mdash; here produced "&amp;mdash;".
    body = """<div class="nf">
  <h1>This story has a new name</h1>
  <p class="lead">It is the same story, it just lives somewhere else now.</p>
  <a class="btn" href="__DEST__">Go to the story</a>
</div>""".replace("__DEST__", dest)
    # The refresh must live in <head>; the script stays in the body for the
    # common case, and the visible link above is the no-JS fallback.
    head_extra = (f'<meta http-equiv="refresh" content="0; url={dest}">'
                  f'<script>location.replace({dest!r});</script>')
    return page("Moved - Story Twirl", "This page has moved.", dest, body,
                head_extra=head_extra)


def story_page(s, stories):
    paras = "\n".join(f"<p>{esc(plain(p))}</p>" for p in s["body"])
    others = [o for o in stories if o["slug"] != s["slug"]]
    more = "".join(
        f'<li><a href="{PREFIX}/stories/{o["slug"]}/">{thumb(o)}'
        f'<div class="txt"><b>{esc(o["title"])}</b><br><small>{esc(o["blurb"])}</small></div></a></li>'
        for o in others)
    # No art yet -> no <img>. A broken image icon is worse than a clean page.
    art = (f'<img class="cover" src="{PREFIX}/{s["cover"]}" alt="{esc(s["title"])} illustration">'
           if (ROOT / s["cover"]).exists() else "")
    body = f"""<header><a href="{PREFIX}/">← Story Twirl</a></header>
<h1>{esc(s["title"])}</h1>
<div class="meta">{s["minutes"]} min read · ages 3–6 · bedtime story</div>
{art}
{paras}
<div class="lesson"><b>One question for afterwards:</b> {esc(plain(s["lesson"]["ask"]))}<br><br>
<b>Did you know?</b> {esc(plain(s["lesson"]["fact"]))}</div>
<div class="cta">In the app this story reads itself aloud — offline, in the phone's own voice — and it can
use your child's name instead of “your child”. One story every night is free.
<a class="btn" href="{PREFIX}/">Open Story Twirl</a></div>
<h2 style="font-size:20px">More stories</h2>
<ul class="index">{more}</ul>
<footer>Story Twirl · a story a night · build {build_short()}</footer>"""
    desc = f'{s["title"]}: {plain(s["blurb"])} A {s["minutes"]}-minute bedtime story for ages 3–6.'
    return page(s["title"], desc, f"{SITE}/stories/{s['slug']}/", body, og_image=s["cover"] if (ROOT / s["cover"]).exists() else None)


def thumb(s):
    """Cover art if it exists; otherwise nothing. A story is never dropped from
    a listing just because its illustration has not been drawn yet."""
    return (f'<img src="{PREFIX}/{s["cover"]}" alt="">' if (ROOT / s["cover"]).exists() else "")


def index_page(stories):
    items = "".join(
        f'<li><a href="{PREFIX}/stories/{s["slug"]}/">{thumb(s)}'
        f'<div class="txt"><b>{esc(s["title"])}</b><br><small>{esc(s["blurb"])} · {s["minutes"]} min</small></div></a></li>'
        for s in stories)
    body = f"""<header><a href="{PREFIX}/">← Story Twirl</a></header>
<h1>Bedtime stories</h1>
<div class="meta">{len(stories)} stories · ages 3–6 · one free a night in the app</div>
<ul class="index">{items}</ul>
<footer>Story Twirl · a story a night · build {build_short()}</footer>"""
    return page("Bedtime stories for ages 3–6 — Story Twirl",
                "Short bedtime stories for children aged 3–6, each with a question to talk about afterwards.",
                f"{SITE}/stories/", body)


def sitemap(stories):
    """Only the pages a search engine should index. /app/ is deliberately
    absent: it is a JS reader with no text of its own, and indexing it would
    compete with the landing page for the same query."""
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [f"{SITE}/", f"{SITE}/stories/"] + [f"{SITE}/stories/{s['slug']}/" for s in stories]
    entries = "".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}</urlset>\n")


def main():
    stories = load()
    check = "--check" in sys.argv
    if check:
        print(f"stories.json: {len(stories)} stories, slugs unique")
        for s in stories:
            missing = [s["cover"]] if not (ROOT / s["cover"]).exists() else []
            print(f"  {s['slug']:<40} {len(s['body'])} paragraphs"
                  + (f"  MISSING {missing}" if missing else ""))
        return 0

    # The app's <head> is hand-written, and a page with no description or OG
    # tags previews as a blank box when someone shares the link. It is the one
    # hand-edited part of a generated file, so assert it rather than trust it.
    head = APP.read_text()[:APP.read_text().find("</head>")]
    for tag in ('name="description"', 'property="og:title"', 'property="og:image"', 'rel="canonical"'):
        if tag not in head:
            raise SystemExit(f"app/index.html <head> is missing {tag}. It is hand-written, "
                             f"so add it back; a shared /app/ link previews blank without it.")

    before, after = build_app(stories)
    out = [f"app/index.html {before // 1024}KB -> {after // 1024}KB (data block regenerated)"]

    # The landing page replaces the app at the root. It is written last so a
    # failure above leaves the old root in place rather than a half-built one.
    (ROOT / "index.html").write_text(landing_page(stories))
    out.append("index.html (landing page)")
    (ROOT / "404.html").write_text(not_found_page())
    out.append("404.html")

    for old_slug, new_slug in REDIRECTS.items():
        d = ROOT / "stories" / old_slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(redirect_page(old_slug, new_slug))
        out.append(f"stories/{old_slug}/ -> {new_slug} (redirect)")

    (ROOT / "stories").mkdir(exist_ok=True)
    (ROOT / "stories/index.html").write_text(index_page(stories))
    for s in stories:
        d = ROOT / "stories" / s["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(story_page(s, stories))
        out.append(f"stories/{s['slug']}/index.html")
    (ROOT / "sitemap.xml").write_text(sitemap(stories))
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    out.append("sitemap.xml, robots.txt")
    print("\n".join("  " + l for l in out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
