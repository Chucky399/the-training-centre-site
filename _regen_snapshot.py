# Regenerates assets/schedule-data.js from the live Arlo Pub API (no auth needed).
# Run from this folder before a deploy to refresh the baked fallback snapshot:
#   python _regen_snapshot.py
# The site also refreshes itself client-side (1 hour localStorage cache), so the
# snapshot only needs to be fresh enough to cover visitors with JS fetch failures.
import json, time, datetime, urllib.request

FIELDS = "EventID,Code,Name,StartDateTime,EndDateTime,ViewUri,RegistrationInfo,AdvertisedOffers,TemplateCode,Location,IsFull"
BASE = "https://www.the-training-centre.com/api/2012-02-01/pub/resources/eventsearch/?format=json&top=50&fields=" + FIELDS

items = []
url = BASE
for _ in range(10):
    with urllib.request.urlopen(url) as r:
        d = json.load(r)
    items += d.get("Items", [])
    nxt = d.get("NextPageUri")
    if not nxt:
        break
    url = nxt if nxt.startswith("http") else "https://www.the-training-centre.com" + nxt
    time.sleep(0.5)

slim = []
for ev in items:
    offer = (ev.get("AdvertisedOffers") or [{}])[0].get("OfferAmount", {})
    view = ev.get("ViewUri", "")
    # Book straight into Arlo registration (the event page's own Book Now target);
    # fall back to the per-date event page if a register link is ever missing.
    register = (ev.get("RegistrationInfo") or {}).get("RegisterUri")
    slim.append({
        "id": ev["EventID"],
        "code": ev.get("TemplateCode", ""),
        "name": ev.get("Name", ""),
        "start": ev.get("StartDateTime", ""),
        "end": ev.get("EndDateTime", ""),
        "price": offer.get("AmountTaxInclusive"),
        "book": register or (view.replace("/uk/courses/", "/w/uk/courses/") + "/" + str(ev["EventID"])),
        "full": ev.get("IsFull", False),
    })
slim.sort(key=lambda e: e["start"])

out = "// Baked snapshot of the Arlo Pub API event feed. Regenerated at deploy time.\n"
out += "// Snapshot taken: " + datetime.date.today().isoformat() + "\n"
out += "window.TTC_SNAPSHOT = " + json.dumps(slim, separators=(",", ":")) + ";\n"
open("assets/schedule-data.js", "w", encoding="utf-8").write(out)
print("written assets/schedule-data.js,", len(slim), "events")
