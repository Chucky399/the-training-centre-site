# Regenerates assets/schedule-data.js from the live Arlo Pub API (no auth needed).
# Run from this folder before a deploy to refresh the baked fallback snapshot:
#   python _regen_snapshot.py
# The site also refreshes itself client-side (1 hour localStorage cache), so the
# snapshot only needs to be fresh enough to cover visitors with JS fetch failures.
import json, re, sys, time, datetime, urllib.request

# Arlo's OWN hostname - deliberately NOT www.the-training-centre.com.
# www is a CNAME to this host today, which is why the old site, the checkout and this
# API all answer on it. Once www serves the new site, anything addressed to www hits
# the new site instead and the feed/booking break. Address Arlo directly.
ARLO_HOST = "https://marketstreetconsultantsltdevents.arlo.co"

FIELDS = "EventID,Code,Name,StartDateTime,EndDateTime,ViewUri,RegistrationInfo,AdvertisedOffers,TemplateCode,Location,IsFull"
BASE = ARLO_HOST + "/api/2012-02-01/pub/resources/eventsearch/?format=json&top=50&fields=" + FIELDS

items = []
url = BASE
for _ in range(10):
    with urllib.request.urlopen(url) as r:
        d = json.load(r)
    items += d.get("Items", [])
    nxt = d.get("NextPageUri")
    if not nxt:
        break
    url = nxt if nxt.startswith("http") else ARLO_HOST + nxt
    time.sleep(0.5)

ALIASES = ("https://book.the-training-centre.com", "https://www.the-training-centre.com",
           "https://the-training-centre.com", ARLO_HOST)

# The host booking links must use = wherever Arlo's checkout actually answers.
# Since 6 Aug 2026 that is book.the-training-centre.com (Arlo completed the paid
# custom-domain move: all hosted pages + checkout, SSL issued; www now serves the
# new site). NOT ARLO_HOST: Arlo 302s /uk/register hits on its own arlo.co host
# across to the custom domain and the booking session does not survive the
# cross-domain hop - the delegate lands on an EMPTY cart (verified 31 Jul 2026).
# Keep in sync with BOOK_HOST in assets/schedule.js.
BOOK_HOST = "https://book.the-training-centre.com"


def to_booking(u):
    """Point a booking/event link at BOOK_HOST whatever host the feed gave us.

    Anything on an unknown host is dropped rather than rendered as a clickable
    Book button (guard against a poisoned feed).
    """
    if not u or not isinstance(u, str):
        return None
    if u.startswith("/"):
        return BOOK_HOST + u
    for a in ALIASES:
        if u.startswith(a + "/"):
            return BOOK_HOST + u[len(a):]
    return None


slim = []
for ev in items:
    offer = (ev.get("AdvertisedOffers") or [{}])[0].get("OfferAmount", {})
    view = ev.get("ViewUri", "")
    # Book straight into Arlo registration (the event page's own Book Now target);
    # fall back to the per-date event page if a register link is ever missing.
    register = to_booking((ev.get("RegistrationInfo") or {}).get("RegisterUri"))
    fallback = to_booking(view.replace("/uk/courses/", "/w/uk/courses/") + "/" + str(ev["EventID"]))
    # In-person venue straight from Arlo's scheduling data (John, 4 Aug 2026: London
    # classroom dates must not present as live online). IsOnline events carry no venue.
    loc = ev.get("Location") or {}
    venue = None
    if loc and not loc.get("IsOnline", False) and (
        loc.get("VenueName") or loc.get("City") or (loc.get("Name") and loc.get("Name") != "Online")
    ):
        venue = {
            "name": loc.get("VenueName") or loc.get("Name") or "",
            "street": loc.get("StreetLine1") or "",
            "city": loc.get("City") or loc.get("Name") or "",
            "postcode": loc.get("PostCode") or "",
        }
    slim.append({
        "id": ev["EventID"],
        "code": ev.get("TemplateCode", ""),
        "name": ev.get("Name", ""),
        "start": ev.get("StartDateTime", ""),
        "end": ev.get("EndDateTime", ""),
        # VAT-INCLUSIVE at John's instruction 31 Jul 2026 ("All prices should show with
        # VAT included"). Supersedes the 30 Jul ex-VAT instruction. Templates with no
        # VAT rate in Arlo have inclusive == exclusive.
        "price": offer.get("AmountTaxInclusive"),
        "book": register or fallback,
        "full": ev.get("IsFull", False),
        "venue": venue,
    })
slim.sort(key=lambda e: e["start"])

PATH = "assets/schedule-data.js"

# Safety floor for the unattended hourly sync. Arlo can answer HTTP 200 with a
# short or empty event list (hiccup, throttling, a half-written response). Writing
# that would strip every course page of its dates, prices and structured data, and
# the sync would push it live. Refuse: an absolute floor, and never accept a set
# less than half the size of the one already published.
MIN_EVENTS = 20
existing = ""
try:
    with open(PATH, encoding="utf-8") as f:
        existing = f.read()
except OSError:
    pass
m = re.search(r"window\.TTC_SNAPSHOT\s*=\s*(\[.*?\]);", existing, re.S)
prev_count = len(json.loads(m.group(1))) if m else 0

if len(slim) < MIN_EVENTS or (prev_count and len(slim) < prev_count / 2):
    sys.exit(f"ABORT: Arlo returned {len(slim)} events (floor {MIN_EVENTS}, "
             f"currently published {prev_count}). {PATH} left untouched - "
             "check the feed before rerunning.")

payload = "window.TTC_SNAPSHOT = " + json.dumps(slim, separators=(",", ":")) + ";\n"

# Only rewrite when the events themselves changed. The date stamp below would
# otherwise differ every day and commit a diff that carries no new information.
prev_payload = ("window.TTC_SNAPSHOT = " + json.dumps(json.loads(m.group(1)), separators=(",", ":")) + ";\n") if m else ""
if payload == prev_payload:
    print(f"{PATH} already matches Arlo, {len(slim)} events - not rewritten")
else:
    out = "// Baked snapshot of the Arlo Pub API event feed. Regenerated at deploy time.\n"
    out += "// Snapshot taken: " + datetime.date.today().isoformat() + "\n"
    out += payload
    # newline="\n" so a run on Windows cannot flip the file to CRLF and make every
    # hourly run see a whole-file diff.
    with open(PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("written " + PATH + ",", len(slim), "events")
