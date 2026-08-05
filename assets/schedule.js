/* The Training Centre - live course schedule renderer.
   Data source: Arlo Pub API (no auth, CORS-enabled) on ARLO_HOST below.
   Strategy: render immediately from the baked snapshot (schedule-data.js),
   then refresh from the live API at most once per hour per browser
   (localStorage cache) so page views never hammer the API (429 guard). */
(function () {
  "use strict";

  /* Arlo's OWN hostname - not www.the-training-centre.com.
     www.the-training-centre.com is currently a CNAME to this host, which is why the
     old site, the booking checkout and this API all answer on it today.
     The API is fine on this host. BOOKING IS NOT: while the custom domain is active,
     Arlo 302s any /uk/register hit on this host across to www.../uk/checkout, and the
     booking session does not survive the cross-domain hop - the delegate lands on an
     EMPTY cart (verified 31 Jul 2026; John hit exactly this reviewing the dev site).
     So Book links must stay on BOOK_HOST below, and the API stays here. */
  var ARLO_HOST = "https://marketstreetconsultantsltdevents.arlo.co";

  /* The host booking links must use = wherever Arlo's checkout actually answers.
     Today that is www (www still CNAMEs to Arlo). AT DOMAIN CUTOVER THIS MUST CHANGE
     with the DNS decision: either Arlo moves its custom domain to e.g.
     book.the-training-centre.com (set that here), or Cloudflare proxies /uk/register,
     /uk/checkout + /api through to Arlo on www (leave as-is). Pointing this at
     ARLO_HOST does NOT work - see the empty-cart note above. */
  var BOOK_HOST = "https://www.the-training-centre.com";
  var ARLO_ALIASES = ["https://www.the-training-centre.com", "https://the-training-centre.com", ARLO_HOST];

  var API_BASE = ARLO_HOST + "/api/2012-02-01/pub/resources/eventsearch/";
  var API_FIELDS = "EventID,Name,StartDateTime,EndDateTime,ViewUri,TemplateCode,AdvertisedOffers,IsFull,RegistrationInfo,Location";

  var CACHE_KEY = "ttc-schedule-v5"; // v5: venue added per event (John, 4 Aug: London classroom dates must not present as live online) - new key so no browser serves cached venue-less events
  var CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

  var MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

  function parseLocal(iso) {
    // "2026-08-24T09:00:00.0000000+01:00" -> treat the wall-clock part as UK time
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso || "");
    if (!m) return null;
    return { y: +m[1], mo: +m[2], d: +m[3], h: +m[4], mi: +m[5],
             date: new Date(+m[1], +m[2] - 1, +m[3]) };
  }

  function fmtTime(p) {
    var h12 = p.h % 12 === 0 ? 12 : p.h % 12;
    var ampm = p.h < 12 ? "am" : "pm";
    return h12 + ":" + (p.mi < 10 ? "0" : "") + p.mi + ampm;
  }

  function fmtPrice(n) {
    if (n == null) return "";
    var whole = Math.round(n) === n;
    return "£" + n.toLocaleString("en-GB", { minimumFractionDigits: whole ? 0 : 2, maximumFractionDigits: whole ? 0 : 2 });
  }

  function decorate(ev) {
    var s = parseLocal(ev.start), e = parseLocal(ev.end);
    if (!s || !e) return null;
    var days = Math.round((e.date - s.date) / 864e5) + 1;
    var sameMonth = s.mo === e.mo;
    ev.s = s; ev.e = e; ev.days = days;
    ev.tileTop = days === 1 ? String(s.d) : (sameMonth ? s.d + "–" + e.d : s.d + " " + MONTHS[s.mo - 1].slice(0, 3) + "–" + e.d);
    ev.tileMonth = MONTHS[e.mo - 1].slice(0, 3);
    var sd = DAYS[s.date.getDay()].slice(0, 3), ed = DAYS[e.date.getDay()].slice(0, 3);
    if (days === 1) ev.dayLabel = sd + " " + s.d + " " + MONTHS[s.mo - 1];
    else if (days === 2) ev.dayLabel = sd + " " + s.d + " & " + ed + " " + e.d + " " + MONTHS[e.mo - 1];
    else ev.dayLabel = sd + " " + s.d + (sameMonth ? "" : " " + MONTHS[s.mo - 1]) + " to " + ed + " " + e.d + " " + MONTHS[e.mo - 1];
    ev.timeLabel = fmtTime(s) + "–" + fmtTime(e) + " UK";
    ev.lengthLabel = days === 1 ? "1 day" : days + " full days";
    ev.priceLabel = fmtPrice(ev.price);
    // Venue labels. Online events have no venue; in-person ones show the full venue
    // details on their date row and just the city in compact contexts.
    var v = ev.venue;
    ev.placeRow = v
      ? [v.name, v.street, ((v.city || "") + (v.postcode ? " " + v.postcode : "")).trim()].filter(Boolean).join(", ")
      : "live online";
    ev.placeShort = v ? (v.city || v.name) : "live online";
    return ev;
  }

  // "live online" / "live online or in London" / "in London" for a course's date list.
  function placeSummary(evs) {
    var cities = [];
    var online = false;
    evs.forEach(function (ev) {
      if (!ev.venue) { online = true; }
      else if (cities.indexOf(ev.placeShort) < 0) cities.push(ev.placeShort);
    });
    if (!cities.length) return "live online";
    return (online ? "live online or in " : "in ") + cities.join(" / ");
  }

  function upcoming(events) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    return events
      .map(function (ev) { return decorate(Object.assign({}, ev)); })
      .filter(function (ev) { return ev && ev.s.date >= today; })
      .sort(function (a, b) { return a.s.date - b.s.date; });
  }

  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /* ---------- row templates (brand tokens from the demo set) ---------- */

  function rowHtml(ev, showName) {
    return '<div class="px-5 sm:px-8 py-4 flex flex-wrap items-center gap-x-6 gap-y-3">' +
      '<div class="flex items-center gap-4 flex-1 min-w-[14rem]">' +
        '<div class="w-16 shrink-0 text-center border border-[#323F48]/15 rounded-[4px] py-1.5">' +
          '<p class="font-display font-extrabold text-[#1E2B34] leading-none text-sm">' + esc(ev.tileTop) + '</p>' +
          '<p class="text-[11px] font-semibold uppercase tracking-wide text-[#47545D] mt-1">' + esc(ev.tileMonth) + '</p></div>' +
        '<div class="min-w-0">' +
          (showName ? '<p class="font-semibold text-[#1E2B34]">' + esc(ev.name) + '</p><p class="text-sm text-[#47545D]">' + esc(ev.dayLabel) + ' · ' + esc(ev.timeLabel) + ' · ' + esc(ev.placeRow) + '</p>'
                    : '<p class="font-semibold text-[#1E2B34]">' + esc(ev.dayLabel) + '</p><p class="text-sm text-[#47545D]">' + esc(ev.timeLabel) + ' · ' + esc(ev.placeRow) + '</p>') +
        '</div></div>' +
      (ev.priceLabel ? '<p class="font-display font-bold text-[#1E2B34]">' + esc(ev.priceLabel) + '</p>' : '') +
      (ev.full
        ? '<span class="ml-auto text-sm font-semibold text-[#47545D] border border-[#323F48]/20 rounded-[4px] px-5 py-2.5 whitespace-nowrap">Fully booked</span>'
        : '<a href="' + esc(ev.book) + '" target="_blank" rel="noopener" class="btn-solid ml-auto text-sm px-5 py-2.5 whitespace-nowrap">Book this date</a>') +
      '</div>';
  }

  // Light-card variant used inside the white "Starting soon" panel.
  function heroRowHtml(ev) {
    return '<a href="' + esc(ev.book) + '" target="_blank" rel="noopener" class="flex items-center gap-4 py-3.5 group">' +
      '<div class="w-14 shrink-0 text-center border border-[#323F48]/15 rounded-[4px] py-1.5">' +
        '<p class="font-display font-extrabold text-[#1E2B34] leading-none text-sm">' + esc(ev.tileTop) + '</p>' +
        '<p class="text-[10px] font-semibold uppercase tracking-wide text-[#47545D] mt-1">' + esc(ev.tileMonth) + '</p></div>' +
      '<div class="min-w-0 flex-1">' +
        '<p class="font-semibold text-[#1E2B34] text-sm leading-snug group-hover:text-[#0085B7]">' + esc(ev.name) + '</p>' +
        '<p class="text-xs text-[#47545D] mt-0.5">' + esc(ev.dayLabel) + (ev.venue ? ' · ' + esc(ev.placeShort) : '') + (ev.priceLabel ? ' · ' + esc(ev.priceLabel) : '') + '</p></div>' +
      '<span class="text-[#0085B7]" aria-hidden="true">&rarr;</span></a>';
  }

  /* ---------- DOM fill ---------- */

  function render(events) {
    var list = upcoming(events);
    var byCode = {};
    list.forEach(function (ev) { (byCode[ev.code] = byCode[ev.code] || []).push(ev); });

    // Full date tables: <div data-ttc-dates="CERT7" data-ttc-max="4">
    document.querySelectorAll("[data-ttc-dates]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-dates")] || [];
      var max = +(el.getAttribute("data-ttc-max") || 6);
      if (!evs.length) {
        el.innerHTML = '<div class="px-5 sm:px-8 py-4"><p class="text-sm text-[#47545D]">New dates are being scheduled. <a href="#ask" class="font-semibold text-[#0085B7]">Ask us</a> and we will let you know as soon as they open.</p></div>';
        return;
      }
      el.innerHTML = evs.slice(0, max).map(function (ev) { return rowHtml(ev, false); }).join("");
    });

    // Course meta line: <p data-ttc-meta="CERT7"> -> "2 full days · 9:00am–4:00pm UK · live online"
    // (or "... · live online or in London" when a course has classroom dates too)
    document.querySelectorAll("[data-ttc-meta]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-meta")] || [];
      if (evs.length) el.textContent = evs[0].lengthLabel + " · " + evs[0].timeLabel + " · " + placeSummary(evs);
    });

    // Format label: <dd data-ttc-place="CERT7"> -> "Live online" / "Live online or in London"
    document.querySelectorAll("[data-ttc-place]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-place")] || [];
      if (!evs.length) return;
      var p = placeSummary(evs);
      el.textContent = p.charAt(0).toUpperCase() + p.slice(1);
    });

    // Catch-all: any course template in the feed that has no table on this page
    // renders automatically, so new courses published in Arlo appear without a code change.
    document.querySelectorAll("[data-ttc-rest]").forEach(function (el) {
      var claimed = {};
      document.querySelectorAll("[data-ttc-dates]").forEach(function (d) { claimed[d.getAttribute("data-ttc-dates")] = true; });
      var restCodes = Object.keys(byCode).filter(function (c) { return c && !claimed[c]; }).sort(function (a, b) {
        return byCode[a][0].s.date - byCode[b][0].s.date;
      });
      var wrap = el.closest("[data-ttc-rest-section]");
      if (!restCodes.length) { el.innerHTML = ""; if (wrap) wrap.hidden = true; return; }
      el.innerHTML = restCodes.map(function (c) {
        var evs = byCode[c];
        return '<article class="bg-white border border-[#323F48]/10 rounded-[8px] mt-6 overflow-hidden">' +
          '<div class="px-6 sm:px-8 pt-5 pb-4 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 border-b border-[#323F48]/10">' +
            '<div><h3 class="font-display font-bold text-lg text-[#1E2B34]">' + esc(evs[0].name) + '</h3>' +
            '<p class="text-sm text-[#47545D] mt-1">' + esc(evs[0].lengthLabel + " · " + evs[0].timeLabel + " · " + placeSummary(evs)) + '</p></div>' +
            (evs[0].priceLabel ? '<p class="tnum font-display font-extrabold text-[#0085B7] text-xl">' + esc(evs[0].priceLabel) + '</p>' : '') +
          '</div>' +
          '<div class="divide-y divide-[#323F48]/10 tnum">' + evs.slice(0, 3).map(function (ev) { return rowHtml(ev, false); }).join("") + '</div>' +
        '</article>';
      }).join("");
      if (wrap) wrap.hidden = false;
    });

    // Next-N across all courses: <div data-ttc-next="4"> (sold-out runs skipped)
    document.querySelectorAll("[data-ttc-next]").forEach(function (el) {
      var max = +(el.getAttribute("data-ttc-next") || 4);
      var open = list.filter(function (ev) { return !ev.full; });
      el.innerHTML = open.length
        ? open.slice(0, max).map(heroRowHtml).join("")
        : '<p class="text-sm text-[#47545D] py-4">New dates are being scheduled. <a href="/schedule/" class="font-semibold text-[#0085B7]">See the course schedule</a>.</p>';
    });

    // "From £X" across a set of codes: <span data-ttc-minprice="ISO2,ISO21,...">
    document.querySelectorAll("[data-ttc-minprice]").forEach(function (el) {
      var codes = el.getAttribute("data-ttc-minprice").split(",");
      var prices = [];
      codes.forEach(function (c) { (byCode[c.trim()] || []).forEach(function (ev) { if (ev.price != null) prices.push(ev.price); }); });
      if (prices.length) el.textContent = "From " + fmtPrice(Math.min.apply(null, prices));
    });

    // Inline next date: <span data-ttc-nextdate="CERT7">
    document.querySelectorAll("[data-ttc-nextdate]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-nextdate")] || [];
      if (evs.length) el.textContent = "Next: " + evs[0].tileTop + " " + evs[0].tileMonth;
    });

    // Inline price: <span data-ttc-price="CERT7">
    document.querySelectorAll("[data-ttc-price]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-price")] || [];
      if (evs.length && evs[0].priceLabel) el.textContent = evs[0].priceLabel;
    });

    document.dispatchEvent(new CustomEvent("ttc:rendered", { detail: { events: list, byCode: byCode } }));
  }

  /* ---------- live refresh with cache ---------- */

  function readCache() {
    try {
      var c = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (c && c.t && Date.now() - c.t < CACHE_TTL_MS && c.events && c.events.length) return c;
    } catch (e) {}
    return null;
  }

  /* Send every booking/event link to BOOK_HOST, whatever host the feed hands us.
     Booking must run on the custom domain while it is active - Arlo bounces its own
     arlo.co host to www and loses the cart on the way (empty-cart bug, 31 Jul 2026).
     Anything that is not a plain http(s) URL on a known Arlo alias is dropped, which
     keeps the original guard against a poisoned feed rendering e.g. a javascript:
     URI as a clickable Book button. */
  function toBooking(u) {
    if (!u || typeof u !== "string") return null;
    if (u.charAt(0) === "/") return BOOK_HOST + u;           // relative -> booking host
    for (var i = 0; i < ARLO_ALIASES.length; i++) {
      if (u.indexOf(ARLO_ALIASES[i] + "/") === 0) {
        return BOOK_HOST + u.slice(ARLO_ALIASES[i].length);
      }
    }
    return null;                                              // unknown host -> refuse
  }

  /* Same display-side name fixes the page generator applies (_build_pages.py clean_name):
     the "IS0 27001" typo with a zero, stray double spaces, trailing whitespace. Without
     this the generated course pages read "ISO" while the live schedule rendering the same
     course read "IS0". John said on 30 Jul he would correct these in Arlo; this stays
     regardless, so a future typo cannot reach the page. */
  function cleanName(n) {
    return String(n || "").replace(/IS0 /g, "ISO ").replace(/\s{2,}/g, " ").trim();
  }

  function slim(items) {
    return items.map(function (ev) {
      var offer = ((ev.AdvertisedOffers || [])[0] || {}).OfferAmount || {};
      var view = ev.ViewUri || "";
      // Book straight into Arlo registration (the event page's own Book Now target);
      // fall back to the per-date event page if a register link is ever missing.
      var register = toBooking((ev.RegistrationInfo || {}).RegisterUri);
      var fallback = toBooking(view.replace("/uk/courses/", "/w/uk/courses/") + "/" + ev.EventID);
      // In-person venue from Arlo's scheduling data; online events carry none.
      var loc = ev.Location || {};
      var venue = null;
      if (loc && loc.IsOnline !== true && (loc.VenueName || loc.City || (loc.Name && loc.Name !== "Online"))) {
        venue = {
          name: loc.VenueName || loc.Name || "",
          street: loc.StreetLine1 || "",
          city: loc.City || loc.Name || "",
          postcode: loc.PostCode || ""
        };
      }
      return {
        id: ev.EventID,
        code: ev.TemplateCode || "",
        name: cleanName(ev.Name),
        start: ev.StartDateTime || "",
        end: ev.EndDateTime || "",
        // VAT-INCLUSIVE, at John's instruction 31 Jul 2026 ("All prices should show
        // with VAT included. I have amended the T&C's to reflect this."). Supersedes
        // his 30 Jul ex-VAT instruction. Templates with no VAT rate in Arlo have
        // inclusive == exclusive; the 5 with a rate display 20% higher. CYBE5 is
        // entered inclusive (395) so the old PRICE_HOLD is no longer needed.
        price: offer.AmountTaxInclusive != null ? offer.AmountTaxInclusive : null,
        book: register || fallback,
        full: !!ev.IsFull,
        venue: venue
      };
    });
  }

  function fetchPage(url, acc, done, fail) {
    fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (d) {
      acc = acc.concat(d.Items || []);
      var next = d.NextPageUri;
      if (next && acc.length < 400) {
        fetchPage(next.indexOf("http") === 0 ? next : ARLO_HOST + next, acc, done, fail);
      } else { done(acc); }
    }).catch(fail);
  }

  function refresh() {
    var cached = readCache();
    if (cached) { render(cached.events); return; }
    var url = API_BASE + "?format=json&top=50&fields=" + API_FIELDS;
    fetchPage(url, [], function (items) {
      var events = slim(items);
      if (!events.length) return; // keep snapshot render
      try { localStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), events: events })); } catch (e) {}
      render(events);
    }, function () { /* offline or rate-limited: snapshot render stands */ });
  }

  function init() {
    if (window.TTC_SNAPSHOT && window.TTC_SNAPSHOT.length) render(window.TTC_SNAPSHOT);
    refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
