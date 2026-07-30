#!/usr/bin/env python3
"""Inject canonical, Open Graph, Twitter Card and Course structured data.

Runs over EVERY page, hand-built and generated alike, so the two cannot drift.
_build_pages.py calls this at the end of its run; it is also safe to run alone:

    python _seo_meta.py

Idempotent. It strips any block it wrote previously before writing a fresh one,
so re-running never duplicates tags.

Why each piece:
  canonical  - the old site served the same content at several addresses
               (/uk/... and /w/uk/... for every course). Canonicals tell Google
               which address is the real one so the ranking is not split.
  Open Graph - controls the title, description and image shown whenever anyone
               shares a course link in email, LinkedIn, Teams or WhatsApp.
               Without it those previews fall back to whatever Google guesses.
  Course JSON-LD - what produces the rich course results in Google carrying
               dates and prices. Every figure comes from the same Arlo feed the
               visible page uses, so the markup can never disagree with the page
               (which is what gets structured data penalised).

Canonicals deliberately use the PRODUCTION domain, not the preview one. The
site is noindex until go-live, so they are inert now and correct the moment the
domain moves.
"""
import datetime
import html as html_mod
import json
import pathlib
import re

BASE = pathlib.Path(__file__).parent
SITE_URL = "https://www.the-training-centre.com"
OG_IMAGE = SITE_URL + "/assets/ttc-logo.png"
SITE_NAME = "The Training Centre"

START = "<!-- seo-meta:start -->"
END = "<!-- seo-meta:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def page_url(f):
    rel = f.relative_to(BASE).as_posix()
    if rel == "index.html":
        return SITE_URL + "/"
    if rel.endswith("/index.html"):
        return SITE_URL + "/" + rel[: -len("index.html")]
    return SITE_URL + "/" + rel


def course_schema(f, title, desc, url):
    """Course + CourseInstance markup, built from the baked Arlo snapshot."""
    rel = f.relative_to(BASE).as_posix()
    if not rel.startswith("courses/") or rel == "courses/index.html":
        return None
    snap = BASE / "assets" / "schedule-data.js"
    if not snap.exists():
        return None
    raw = snap.read_text(encoding="utf-8")
    m = re.search(r"window\.TTC_SNAPSHOT\s*=\s*(\[.*?\]);", raw, re.S)
    if not m:
        return None
    events = json.loads(m.group(1))

    html = f.read_text(encoding="utf-8")
    codes = set(re.findall(r'data-ttc-(?:dates|price|meta)="([A-Z0-9]+)"', html))
    if len(codes) != 1:
        return None  # category/overview pages cover many courses: not a Course
    code = codes.pop()
    mine = [e for e in events if e.get("code") == code]
    if not mine:
        return None

    data = {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": re.sub(r"\s*\|\s*The Training Centre\s*$", "", title).strip(),
        "description": desc,
        "url": url,
        "provider": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/"},
    }
    instances = []
    for e in sorted(mine, key=lambda x: x.get("start") or "")[:12]:
        start, end = (e.get("start") or "")[:10], (e.get("end") or "")[:10]
        inst = {
            "@type": "CourseInstance",
            "courseMode": "Online",
            "startDate": start,
            "endDate": end,
        }
        # Real run length from the dates. Never hard-code this: a wrong
        # courseWorkload is worse than none, because it contradicts the page.
        try:
            d0 = datetime.date.fromisoformat(start)
            d1 = datetime.date.fromisoformat(end)
            days = (d1 - d0).days + 1
            if days >= 1:
                inst["courseWorkload"] = f"P{days}D"
        except ValueError:
            pass
        if e.get("price") is not None:
            inst["offers"] = {
                "@type": "Offer",
                "price": e["price"],
                "priceCurrency": "GBP",
                "availability": ("https://schema.org/SoldOut" if e.get("full")
                                 else "https://schema.org/InStock"),
                "url": e.get("book") or url,
            }
        instances.append(inst)
    if instances:
        data["hasCourseInstance"] = instances
    return data


def build_block(f):
    html = f.read_text(encoding="utf-8")
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    d = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
    if not t:
        return None
    # Decode first, then re-escape. The title and description are already
    # HTML-escaped in the page, so escaping them again turns "&amp;" into
    # "&amp;amp;" and the ampersand shows up literally in link previews.
    title = html_mod.unescape(re.sub(r"\s+", " ", t.group(1)).strip())
    desc = html_mod.unescape(re.sub(r"\s+", " ", d.group(1)).strip()) if d else ""
    url = page_url(f)

    lines = [START,
             f'<link rel="canonical" href="{esc(url)}">',
             '<meta property="og:type" content="website">',
             f'<meta property="og:site_name" content="{esc(SITE_NAME)}">',
             f'<meta property="og:title" content="{esc(title)}">',
             f'<meta property="og:description" content="{esc(desc)}">',
             f'<meta property="og:url" content="{esc(url)}">',
             f'<meta property="og:image" content="{esc(OG_IMAGE)}">',
             '<meta name="twitter:card" content="summary_large_image">',
             f'<meta name="twitter:title" content="{esc(title)}">',
             f'<meta name="twitter:description" content="{esc(desc)}">',
             f'<meta name="twitter:image" content="{esc(OG_IMAGE)}">']

    schema = course_schema(f, title, desc, url)
    if schema:
        lines.append('<script type="application/ld+json">'
                     + json.dumps(schema, separators=(",", ":"), ensure_ascii=False)
                     + "</script>")
    lines.append(END)
    return "\n".join(lines)


def main():
    done = schema_n = 0
    for f in sorted(BASE.rglob("*.html")):
        if ".git" in f.parts:
            continue
        html = f.read_text(encoding="utf-8")
        html = BLOCK_RE.sub("", html)          # idempotent: drop any previous block
        f.write_text(html, encoding="utf-8")
        block = build_block(f)
        if not block:
            continue
        html = f.read_text(encoding="utf-8")
        anchor = '<meta name="robots"'
        if anchor in html:
            i = html.index(anchor)
            j = html.index(">", i) + 1
            html = html[:j] + "\n" + block + html[j:]
        else:
            html = html.replace("</head>", block + "\n</head>", 1)
        f.write_text(html, encoding="utf-8")
        done += 1
        if "application/ld+json" in block:
            schema_n += 1
    print(f"seo meta written to {done} pages ({schema_n} with Course structured data)")


if __name__ == "__main__":
    main()
