# The Training Centre - sitemap generator.
# Walks the committed static site for index.html pages and writes sitemap.xml.
# Existing URLs keep the lastmod already in the file, so re-running churns nothing;
# a page that has just appeared (a new Arlo course) gets today's date.
# Run after _build_pages.py:
#   python _build_sitemap.py
import os, re, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.the-training-centre.com"
OUT = os.path.join(BASE, "sitemap.xml")

# Directories that hold pages people should never reach from search.
EXCLUDE_DIRS = {"thank-you", "functions", "assets", "__pycache__", ".git", ".github"}
EXCLUDE_FILES = {"404.html"}


def existing_lastmod():
    """URL -> lastmod already published, so settled pages keep their date."""
    if not os.path.exists(OUT):
        return {}
    xml = open(OUT, encoding="utf-8").read()
    return dict(re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", xml))


def page_urls():
    urls = []
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        if "index.html" not in files:
            continue
        rel = os.path.relpath(root, BASE).replace(os.sep, "/")
        if rel == ".":
            urls.append(SITE + "/")
        else:
            if rel.split("/")[0] in EXCLUDE_DIRS:
                continue
            urls.append(f"{SITE}/{rel}/")
    return sorted(set(urls))


def main():
    known = existing_lastmod()
    today = datetime.date.today().isoformat()
    urls = page_urls()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    new = 0
    for u in urls:
        lastmod = known.get(u)
        if not lastmod:
            lastmod = today
            new += 1
        lines.append(f"  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>")
    gone = sorted(set(known) - set(urls))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"sitemap written: {len(urls)} urls ({new} new, {len(gone)} dropped)")
    for g in gone:
        print("   dropped:", g)


if __name__ == "__main__":
    main()
