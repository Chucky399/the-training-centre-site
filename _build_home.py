# The Training Centre - homepage course rows.
#
# The homepage lists courses in five hand-written blocks. The headings and the
# intro lines are editorial and are left alone; only the ROWS are generated, from
# the same Arlo feed as everything else. That way a course added in Arlo can reach
# the homepage on its own, and every row links to its own course page.
#
# Each block is marked in index.html with:
#   <!-- ttc-rows: <Arlo category name> -->  ...rows...  <!-- /ttc-rows -->
# Every course in that category is listed, ordered by name. A course tagged to
# more than one category is shown once only, in the first block that claims it,
# so the page never repeats itself.
# Run after _regen_snapshot.py and _build_pages.py:
#   python _build_home.py
import os, re, sys

import _build_pages as bp

BASE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.join(BASE, "index.html")

_A = ('<a href="{url}" class="px-6 sm:px-8 py-3.5 flex flex-wrap items-center gap-x-6 gap-y-1 '
      'hover:bg-[#F7F9FA]"><span class="font-semibold text-[#1E2B34] flex-1 min-w-[14rem]"{hook}>{label}</span>'
      '<span class="text-sm text-[#47545D]" data-ttc-nextdate="{code}">{datefb}</span>'
      '<span class="font-display font-bold text-[#1E2B34] w-20 text-right" data-ttc-price="{code}">{price}</span></a>')


def row(url, code, label, price, hook):
    """hook=True adds data-ttc-name, which lets schedule.js replace the label with
    the live Arlo name. Curated labels are editorial copy, so they do not get it."""
    return _A.format(url=url, code=bp.esc(code), label=label, price=price,
                     datefb="Being scheduled",
                     hook=f' data-ttc-name="{bp.esc(code)}"' if hook else "")


# The homepage rows exactly as they were curated before this script existed.
# A code listed here keeps its editorial label and its position, so nothing
# a visitor sees today moves or is reworded. Anything Arlo adds to the
# category is appended below these, and a course withdrawn from Arlo drops
# out on its own. Labels are already HTML-escaped: do not re-escape them.
CURATED = {
    'IAPP Training': [
        ('CERT7', 'CIPP/E &middot; Certified Information Privacy Professional Europe'),
        ('CERT8', 'CIPM &middot; Certified Information Privacy Manager'),
        ('EURO', 'DPO Ready &middot; CIPP/E and CIPM in one week'),
        ('AIGO', 'AIGP &middot; AI Governance Professional'),
        ('CERT16', 'CIPT &middot; Certified Information Privacy Technologist'),
    ],
    'Data Protection': [
        ('CERT13', 'CDPO &middot; Certified Data Protection Officer'),
        ('CERT27', 'CIPA &middot; Certified Information Privacy Auditor'),
        ('CERT14', 'Certified GDPR Foundation'),
        ('GDPR', 'GDPR Awareness Training'),
    ],
    'Artificial Intelligence Training': [
        ('TRUS', 'TAISE &middot; Trusted AI Safety Expert'),
        ('AIST', 'AI Strategy &amp; Governance Foundation and Practitioner'),
        ('AIAG', 'AI Agents Foundation &amp; Practitioner'),
        ('AIPR', 'AI Productivity Foundation &amp; Practitioner'),
        ('ARTI1', 'Artificial Intelligence for Project Managers'),
    ],
    'ISO Standards Training': [
        ('ISO2', 'Certified ISO 27001 Lead Implementer'),
        ('ISO21', 'Certified ISO 27001 Lead Auditor'),
        ('ISO212', 'ISO 27005 Information Security Risk Manager'),
        ('ISO210', 'Certified ISO 27701 Lead Implementer'),
        ('ISO43', 'ISO 42001 Lead Implementer &middot; AI management systems'),
        ('ISO44', 'ISO 42001 Lead Auditor &middot; AI management systems'),
        ('ISO3', 'Certified ISO 31000 Lead Risk Manager'),
        ('ISO35', 'Certified ISO 31000 Risk Analyst'),
        ('ISO24', 'Certified ISO 22301 Lead Implementer &middot; business continuity'),
        ('ISO23', 'Certified ISO 22301 Lead Auditor &middot; business continuity'),
        ('CERT28', 'Certified ISO 22361 Lead Crisis Manager'),
    ],
    'Cybersecurity Courses': [
        ('ISO25', 'Certified Cybersecurity Manager'),
        ('CYBE4', 'Cyber Assurance Framework Practitioner'),
        ('ISO214', 'Certified Cyber Security Analyst'),
        ('CERT30', 'Certified Operational Resilience Manager'),
        ('LEAD', 'Lead Disaster Recovery Manager'),
    ],
}


# The category is anything up to the closing "-->", so a name with a hyphen
# ("E-Learning") still matches. A character class here once excluded "-" and
# would have made a hyphenated category silently stop regenerating.
def warn(msg):
    """Loud on the console, and an annotation on the Actions run page when this
    runs in CI, so a warning is not buried in an hourly log nobody opens."""
    print("  WARNING: " + msg, file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning file=index.html::{msg}")


def page_exists(code):
    """Only link a row to a page that is actually on disk. This script fetches
    Arlo separately from _build_pages.py, so a course published between the two
    fetches would otherwise get a homepage link that 404s until the next run."""
    url = bp.course_url(code)
    if not url:
        return False
    rel = url.strip("/").replace("/", os.sep)
    return os.path.exists(os.path.join(BASE, rel, "index.html"))


BLOCK_RE = re.compile(
    r'(<!-- ttc-rows:\s*(?P<cat>.*?)\s*-->)(?P<body>.*?)(<!-- /ttc-rows -->)', re.S)

# The headline figures. John hand-corrected "34 certified courses" to 35 on
# 11 Sep 2026; the /courses/ page had derived the same number automatically for
# weeks. These markers put the homepage on that same source so neither number
# can go stale again.
COUNT_RE = re.compile(r'(<!-- ttc-count -->)(.*?)(<!-- /ttc-count -->)', re.S)
BLOCKCOUNT_RE = re.compile(r'(<!-- ttc-blocks -->)(.*?)(<!-- /ttc-blocks -->)', re.S)



def main():
    templates = bp.fetch_templates()
    if len(templates) < bp.MIN_TEMPLATES:
        sys.exit(f"ABORT: Arlo returned {len(templates)} templates, below the floor of "
                 f"{bp.MIN_TEMPLATES}. index.html left untouched.")
    bp.merge_categories(templates)
    bp.resolve_slugs(templates, bp.read_manifest())

    with open(HOME, "rb") as f:
        raw = f.read()
    # Keep whatever line ending the file already uses, so a rewrite only ever
    # changes the rows, never every line of the file.
    eol = "\r\n" if raw.count(b"\r\n") else "\n"
    html = raw.decode("utf-8").replace("\r\n", "\n")
    opens = len(re.findall(r"<!-- ttc-rows:", html))
    closes = len(re.findall(r"<!-- /ttc-rows -->", html))
    pairs = len(BLOCK_RE.findall(html))
    if not opens:
        sys.exit("ABORT: no <!-- ttc-rows: ... --> markers in index.html. Nothing to generate.")
    if not (opens == closes == pairs):
        # An unclosed or nested marker would make a block swallow the
        # hand-written HTML after it. Refuse to touch the file.
        sys.exit(f"ABORT: marker mismatch in index.html - {opens} openers, "
                 f"{closes} closers, {pairs} matched pairs. index.html left untouched.")

    report = []
    shown = set()   # a course tagged to several categories is listed once only
    empty = []      # blocks whose category matched nothing

    def render(m):
        cat = m.group("cat").strip()
        by_code = {t["Code"]: t for t in templates if t.get("Code")}
        usable = lambda c: (c in by_code and c not in bp.SKIP
                            and bp.course_url(c) and page_exists(c))

        # 1. The curated rows, in their curated order and wording. A course
        #    withdrawn from Arlo simply is not in by_code, so it drops out.
        picked = []
        for code, label in CURATED.get(cat, []):
            if usable(code) and code not in shown:
                picked.append((code, label, False))

        # 2. Anything else Arlo puts in this category, newest additions included,
        #    labelled from the feed and free to follow a rename. A course curated
        #    into a LATER block is skipped here, otherwise an earlier block whose
        #    Arlo category also matches would steal it and move it on the page.
        claimed = {c for c, _, _ in picked} | shown | {
            c for c2, rows2 in CURATED.items() if c2 != cat for c, _ in rows2}
        extra = [t for t in templates
                 if cat in [c["Name"] for c in (t.get("Categories") or [])]
                 and usable(t.get("Code")) and t["Code"] not in claimed]
        extra.sort(key=lambda t: bp.clean_name(t["Name"]).lower())
        for t in extra:
            picked.append((t["Code"], bp.esc(bp.clean_name(t["Name"])), True))

        rows = ""
        for code, label, hook in picked:
            shown.add(code)
            price = bp.esc(bp.baked_price(by_code[code]))
            if not price:
                # No price set in Arlo. schedule.js only fills this in when the
                # course has a scheduled event, so without a fallback the column
                # would sit blank for good and nobody would be told.
                price = "See dates"
                warn(f"{code} has no price in Arlo, so the homepage shows "
                     f"'See dates'. Add a price to the course in Arlo.")
            rows += "\n      " + row(bp.course_url(code), code, label, price, hook)
        if not picked:
            empty.append(cat)
        report.append(f"  {cat}: {len(picked)} course(s), "
                      f"{len(picked) - len(extra)} curated + {len(extra)} from Arlo")
        # Rebuild the markers from the named values rather than by group number.
        # Named groups still occupy numbered slots, so m.group() by number would
        # hand back the OLD body and duplicate every row instead of replacing it.
        return (f"<!-- ttc-rows: {cat} -->" + rows
                + "\n      " + "<!-- /ttc-rows -->")

    new = BLOCK_RE.sub(render, html)

    if empty:
        # A homepage block matched no course at all. The usual cause is the
        # category being renamed in Arlo, which would otherwise publish a
        # heading with nothing under it. Leave the page alone and say so.
        known = sorted({c["Name"] for t in templates for c in (t.get("Categories") or [])})
        sys.exit("ABORT: homepage block(s) matched no courses: "
                 + ", ".join(repr(c) for c in empty)
                 + ". The Arlo category may have been renamed. index.html left "
                 "untouched. Category names currently in Arlo: "
                 + ", ".join(repr(c) for c in known))

    # Same rule _build_pages.py uses for the /courses/ headline count, so the
    # two pages state the same number. It counts every course that has a page,
    # not just the ones the five blocks show, which is why the headline can read
    # 35 above 34 rows: the homepage features five of Arlo's subject areas, and
    # a course in none of them still exists and is still listed on /courses/.
    # Both scripts fetch Arlo separately, so a course added or withdrawn in the
    # seconds between the two fetches can leave the two counts differing by one
    # until the next hourly run. page_exists keeps that from ever producing a
    # link to a page that does not exist, which is the only harmful version.
    total = len([t for t in templates
                 if t.get("Code") and t.get("Code") not in bp.SKIP
                 and bp.course_url(t["Code"]) and page_exists(t["Code"])])
    new, n_count = COUNT_RE.subn(lambda m: m.group(1) + str(total) + m.group(3), new)
    new, n_blocks = BLOCKCOUNT_RE.subn(lambda m: m.group(1) + str(pairs) + m.group(3), new)
    # Warn rather than abort: the rows are the promise that matters, and a
    # missing headline marker must not stop a new course reaching the page.
    for label, n in (("ttc-count", n_count), ("ttc-blocks", n_blocks)):
        if not n:
            warn(f"no <!-- {label} --> markers in index.html, so that headline "
                 f"figure is no longer generated and will go stale. Re-add the "
                 f"markers around the number.")
    if n_count and n_blocks:
        report.append(f"  headline: {total} certified courses across {pairs} subject areas")
    for line in report:
        print(line)
    # A course whose Arlo categories match none of the homepage blocks would
    # silently never appear here. Say so on every run rather than hiding it.
    unclaimed = [t for t in templates
                 if t.get("Code") and bp.course_url(t.get("Code"))
                 and t.get("Code") not in shown]
    for t in sorted(unclaimed, key=lambda t: t["Code"]):
        cats = ", ".join(c["Name"] for c in (t.get("Categories") or [])) or "none"
        warn(f"{t['Code']} ({bp.clean_name(t['Name'])}) is in no homepage block, "
             f"so it will not appear there. Its Arlo categories: {cats}")
    if new == html:
        print("index.html already matches Arlo - not rewritten")
        return
    with open(HOME, "w", encoding="utf-8", newline=eol) as f:
        f.write(new)
    print("index.html rows regenerated")


if __name__ == "__main__":
    main()
