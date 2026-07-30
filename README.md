# The Training Centre — site rebuild (the-training-centre-site)

Full front-end rebuild of the-training-centre.com on our stack. Arlo stays the engine
behind it (registration, payment, confirmations, transfers, CRM). Built 29 Jul 2026.

- **Live:** https://the-training-centre-site.pages.dev/ (CF Pages project `the-training-centre-site`)
- **Deploys:** push to main auto-deploys via CI (project already exists). Manual: `wrangler pages deploy . --project-name=the-training-centre-site --branch=main`
- **Ad LPs are separate:** the 5 live ad landing pages live in `the-training-centre/` on their own Pages project. Never merge the two.

## How the schedule stays up to date (IMPORTANT — read before "maintaining" anything)

The schedule maintains itself. There is no monthly content task.

1. **Live data:** every page loads `assets/schedule.js`, which renders instantly from the
   baked snapshot (`assets/schedule-data.js`) and then refreshes from the Arlo Pub API
   (no auth, CORS-enabled) at most **once per hour per browser** (localStorage cache,
   key `ttc-schedule-v2`). Dates, prices, sold-out states and Book buttons all come from
   the feed. When John changes a date or price in Arlo, the site follows within the hour.
2. **Book buttons:** each date's button uses the event's `RegistrationInfo.RegisterUri`
   (`/uk/register?sgid=...`) — the same URL as the old site's own "Book Now" button. It
   lands directly on Arlo registration with the course and date pre-loaded. URLs are
   allowlisted to `https://www.the-training-centre.com/`. Fallback if a register link is
   missing: the per-date event page (`/w/uk/courses/<slug>/<eventId>`).
3. **New courses appear automatically:** the schedule page has a hidden "More courses"
   section (`data-ttc-rest`). Any course template in the feed that has no table on the
   page renders there automatically. A brand-new course John publishes in Arlo shows up
   with dates, price and booking — no code change. Give it a proper home in a curated
   section later if it earns one.

## Generated pages: `_build_pages.py`

The 30 course pages and 12 category pages under `/courses/` (plus `/courses/index.html`)
are GENERATED from the Arlo Pub API - every word of course content is John's own
(Description, About This Course, Who Should Attend?, Prerequisites, What's Included?,
Assessment, Accreditation, Provided by, Our Guarantee). Regenerate when John materially
changes course content in Arlo, or when he adds a brand-new course that deserves its own
page (add its code to SLUGS and, if needed, CATEGORIES):

```
python _build_pages.py
```

Hand-built pages are never touched by the generator: home, schedule, about, contact,
insights, thank-you, trainers, in-house-training, cipp-e (+outline/faq), cdpo, aigp,
taise, iso-standards. VAT-mentioning sentences are stripped from imported copy
(VAT display is an open client decision); the "IS0" Arlo typo is corrected display-side
only. `/trainers/` bios were lifted verbatim from his old presenter pages 30 Jul 2026
(source data: see the session scratchpad ttc_presenter_bios.json / re-scrape if stale).

### The ONE recurring job: `_regen_snapshot.py`

`assets/schedule-data.js` is the baked fallback used for the instant first paint and
for any visitor whose live fetch fails. It goes stale over time. **Run this from the
project folder before every deploy** (any machine, no credentials needed):

```
python _regen_snapshot.py
```

It refetches the full Arlo feed and rewrites `assets/schedule-data.js`. Commit it with
your change. If the site ever goes months without a deploy, run it and deploy anyway
(or automate it: a small weekly CI/cron job that regenerates + redeploys would remove
even this task).

### Gotchas learned the hard way

- **Arlo blocks headless browsers.** Playwright with the default HeadlessChrome UA gets
  "Not Found" on every Arlo page. Always set a real Chrome user-agent string when
  testing Arlo URLs. An HTTP 200 from curl does NOT mean the page renders.
- **Do not hammer the Pub API** — global rate limits (429). The 1-hour client cache and
  the baked snapshot exist for this reason. Never fetch per page-view.
- **Never touch Arlo's own settings** (management console, checkout themes, the
  "My own site" integration switch). Single shared login, John's. Claire + John only.

## Forms

All 8 enquiry forms post to `lp-form-handler` (KV key `the-training-centre` →
info@the-training-centre.com, extra field `Course`), then redirect to `/thank-you/`.
E2E proven 29 Jul 2026. When editing KV: READ the current value first and preserve
every field (see _OPEN-ACTIONS 29 Jul webhook-wipe incident).

## Tracking

Client's GTM `GTM-PHR6JF2` on every page (head + noscript). GA4 `G-5EEG7DCBX1` and the
Google Ads tag fire through it (verified live 29 Jul). Never swap in a JD container.

## Go-live checklist (when Claire + John say go)

1. Run `_regen_snapshot.py`, commit, deploy.
2. Remove `<meta name="robots" content="noindex">` from every page.
3. Add sitemap.xml.
4. Custom domain on the Pages project + John's DNS (Claire coordinates).
5. VAT copy decision applied (prices currently bare; feed carries tax-exclusive and
   tax-inclusive amounts — see _OPEN-ACTIONS flags).
