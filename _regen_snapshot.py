# Regenerates assets/schedule-data.js from the live Arlo Pub API (no auth needed).
# Run from this folder before a deploy to refresh the baked fallback snapshot:
#   python _regen_snapshot.py
# The site also refreshes itself client-side (1 hour localStorage cache), so the
# snapshot only needs to be fresh enough to cover visitors with JS fetch failures.
import json, time, datetime, urllib.request

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

ALIASES = ("https://www.the-training-centre.com", "https://the-training-centre.com", ARLO_HOST)

# The host booking links must use = wherever Arlo's checkout actually answers.
# NOT ARLO_HOST: while the custom domain is active, Arlo 302s /uk/register hits on
# its own arlo.co host across to www.../uk/checkout and the booking session does not
# survive the cross-domain hop - the delegate lands on an EMPTY cart (verified
# 31 Jul 2026; John hit exactly this reviewing the dev site). Keep in sync with
# BOOK_HOST in assets/schedule.js. At domain cutover this changes with the DNS
# decision (Arlo's branded checkout subdomain, or Cloudflare proxying /uk/* to Arlo).
BOOK_HOST = "https://www.the-training-centre.com"


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
    slim.append({
        "id": ev["EventID"],
        "code": ev.get("TemplateCode", ""),
        "name": ev.get("Name", ""),
        "start": ev.get("StartDateTime", ""),
        "end": ev.get("EndDateTime", ""),
        # Ex-VAT at John's instruction 30 Jul 2026 (competitors advertise the bare number),
        # and the only consistent option: Arlo has a VAT rate on the 3 AI templates only.
        "price": offer.get("AmountTaxExclusive"),
        "book": register or fallback,
        "full": ev.get("IsFull", False),
    })
slim.sort(key=lambda e: e["start"])

out = "// Baked snapshot of the Arlo Pub API event feed. Regenerated at deploy time.\n"
out += "// Snapshot taken: " + datetime.date.today().isoformat() + "\n"
out += "window.TTC_SNAPSHOT = " + json.dumps(slim, separators=(",", ":")) + ";\n"
open("assets/schedule-data.js", "w", encoding="utf-8").write(out)
print("written assets/schedule-data.js,", len(slim), "events")
