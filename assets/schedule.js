/* The Training Centre - live course schedule renderer.
   Data source: Arlo Pub API (no auth, CORS-enabled) on the-training-centre.com.
   Strategy: render immediately from the baked snapshot (schedule-data.js),
   then refresh from the live API at most once per hour per browser
   (localStorage cache) so page views never hammer the API (429 guard). */
(function () {
  "use strict";

  var API_BASE = "https://www.the-training-centre.com/api/2012-02-01/pub/resources/eventsearch/";
  var API_FIELDS = "EventID,Name,StartDateTime,EndDateTime,ViewUri,TemplateCode,AdvertisedOffers,IsFull";
  var CACHE_KEY = "ttc-schedule-v1";
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
    return ev;
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
        '<div class="w-16 shrink-0 text-center border border-[#323F48]/15 rounded-[6px] py-1.5">' +
          '<p class="font-display font-extrabold text-[#1E2B34] leading-none text-sm">' + esc(ev.tileTop) + '</p>' +
          '<p class="text-[11px] font-semibold uppercase tracking-wide text-[#47545D] mt-1">' + esc(ev.tileMonth) + '</p></div>' +
        '<div class="min-w-0">' +
          (showName ? '<p class="font-semibold text-[#1E2B34]">' + esc(ev.name) + '</p><p class="text-sm text-[#47545D]">' + esc(ev.dayLabel) + ' · ' + esc(ev.timeLabel) + '</p>'
                    : '<p class="font-semibold text-[#1E2B34]">' + esc(ev.dayLabel) + '</p><p class="text-sm text-[#47545D]">' + esc(ev.timeLabel) + ' · live online</p>') +
        '</div></div>' +
      (ev.priceLabel ? '<p class="font-display font-bold text-[#1E2B34]">' + esc(ev.priceLabel) + '</p>' : '') +
      '<a href="' + esc(ev.book) + '" target="_blank" rel="noopener" class="ml-auto bg-[#13B4EA] hover:bg-[#0085B7] text-white font-semibold text-sm px-5 py-2.5 rounded-[6px] whitespace-nowrap">Book this date</a>' +
      '</div>';
  }

  function heroRowHtml(ev) {
    return '<a href="' + esc(ev.book) + '" target="_blank" rel="noopener" class="flex items-center gap-4 py-3.5 group">' +
      '<div class="w-14 shrink-0 text-center border border-white/20 rounded-[6px] py-1.5">' +
        '<p class="font-display font-extrabold text-white leading-none text-sm">' + esc(ev.tileTop) + '</p>' +
        '<p class="text-[10px] font-semibold uppercase tracking-wide text-[#8FA0AB] mt-1">' + esc(ev.tileMonth) + '</p></div>' +
      '<div class="min-w-0 flex-1">' +
        '<p class="font-semibold text-white text-sm leading-snug group-hover:text-[#13B4EA]">' + esc(ev.name) + '</p>' +
        '<p class="text-xs text-[#8FA0AB] mt-0.5">' + esc(ev.dayLabel) + (ev.priceLabel ? ' · ' + esc(ev.priceLabel) : '') + '</p></div>' +
      '<span class="text-[#13B4EA]" aria-hidden="true">&rarr;</span></a>';
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
    document.querySelectorAll("[data-ttc-meta]").forEach(function (el) {
      var evs = byCode[el.getAttribute("data-ttc-meta")] || [];
      if (evs.length) el.textContent = evs[0].lengthLabel + " · " + evs[0].timeLabel + " · live online";
    });

    // Next-N across all courses: <div data-ttc-next="4">
    document.querySelectorAll("[data-ttc-next]").forEach(function (el) {
      var max = +(el.getAttribute("data-ttc-next") || 4);
      el.innerHTML = list.slice(0, max).map(heroRowHtml).join("");
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

  function slim(items) {
    return items.map(function (ev) {
      var offer = ((ev.AdvertisedOffers || [])[0] || {}).OfferAmount || {};
      var view = ev.ViewUri || "";
      return {
        id: ev.EventID,
        code: ev.TemplateCode || "",
        name: ev.Name || "",
        start: ev.StartDateTime || "",
        end: ev.EndDateTime || "",
        price: offer.AmountTaxInclusive != null ? offer.AmountTaxInclusive : null,
        book: view.replace("/uk/courses/", "/w/uk/courses/") + "/" + ev.EventID,
        full: !!ev.IsFull
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
        fetchPage(next.indexOf("http") === 0 ? next : "https://www.the-training-centre.com" + next, acc, done, fail);
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
