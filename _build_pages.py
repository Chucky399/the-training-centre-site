# The Training Centre - course + category page generator.
# Fetches every course template from the Arlo Pub API (John's own content) and
# writes /courses/<slug>/ pages and /courses/<category>/ pages in the site design.
# Pages carry data-ttc-* hooks so dates/prices/sold-out states stay live via
# assets/schedule.js. Rerun any time John's course content changes materially:
#   python _build_pages.py
# Static copy (headings, buttons, shared claims) is the same approved set used
# on the hand-built pages. Course body content comes verbatim from the feed.
import json, os, re, sys, time, html, urllib.request
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
# Arlo's OWN hostname - deliberately NOT www.the-training-centre.com.
# www is a CNAME to this host today, which is why the old site, the checkout and this
# API all answer on it. Once www serves the new site, anything addressed to www hits
# the new site instead and the feed/booking break. Address Arlo directly.
ARLO_HOST = "https://marketstreetconsultantsltdevents.arlo.co"

API = (ARLO_HOST + "/api/2012-02-01/pub/resources/eventtemplates/"
       "?format=json&top=20&fields=TemplateID,Code,Name,Description,AdvertisedDuration,Categories,BestAdvertisedOffers")

# Courses that already have hand-built pages (do not regenerate these).
HANDBUILT = {"CERT7": "/courses/cipp-e/", "CERT13": "/courses/cdpo/",
             "AIGO": "/courses/aigp/", "TRUS": "/courses/taise/"}
SKIP = {"CERT34"}  # hard-copy study guide: a product, not a course page

SLUGS = {
    "EURO": "dpo-ready", "CERT8": "cipm", "ISO2": "iso-27001-lead-implementer",
    "ISO21": "iso-27001-lead-auditor", "CERT14": "gdpr-foundation",
    "ISO3": "iso-31000-lead-risk-manager", "ISO23": "iso-22301-lead-auditor",
    "ISO24": "iso-22301-lead-implementer", "CERT16": "cipt",
    "ISO25": "cybersecurity-manager", "ISO210": "iso-27701-lead-implementer",
    "GDPR": "gdpr-awareness", "ISO212": "iso-27005-risk-manager",
    "ISO35": "iso-31000-risk-analyst", "LEAD": "lead-disaster-recovery-manager",
    "ISO213": "iso-27035-lead-incident-manager", "ISO214": "cyber-security-analyst",
    "CERT27": "cipa", "CERT28": "iso-22361-lead-crisis-manager",
    "ISO43": "iso-42001-lead-implementer", "ISO44": "iso-42001-lead-auditor",
    "CERT30": "operational-resilience-manager", "BCSE": "bcs-essentials-ai",
    "BCSF": "bcs-foundation-ai", "CYBE4": "cyber-assurance-practitioner",
    "CYBE5": "cyber-security-foundation", "ARTI1": "ai-for-project-managers",
    "AIPR": "ai-productivity", "AIAG": "ai-agents", "AIST": "ai-strategy-governance",
}

CATEGORIES = {  # feed category name -> (slug, page path). ISO maps to the existing overview page.
    "IAPP Training": ("iapp-training", "/courses/iapp-training/"),
    "Data Protection": ("data-protection", "/courses/data-protection/"),
    "GDPR Training": ("gdpr-training", "/courses/gdpr-training/"),
    "Compliance Training": ("compliance-training", "/courses/compliance-training/"),
    "ISO Standards Training": ("iso-standards", "/courses/iso-standards/"),
    "Cybersecurity Courses": ("cybersecurity", "/courses/cybersecurity/"),
    "IT Governance & Audit": ("it-governance-audit", "/courses/it-governance-audit/"),
    "Risk Management": ("risk-management", "/courses/risk-management/"),
    "Disaster Recovery & Business Continuity Training": ("disaster-recovery", "/courses/disaster-recovery/"),
    "Business Resilience Training": ("business-resilience", "/courses/business-resilience/"),
    "Business Analysis & Design": ("business-analysis-design", "/courses/business-analysis-design/"),
    "Artificial Intelligence Training": ("ai-training", "/courses/ai-training/"),
    "BCS Training Courses": ("bcs-training", "/courses/bcs-training/"),
}
CATEGORY_INTROS = {  # 1 factual line each; counts are injected from live data
    "IAPP Training": "Official IAPP certification courses: CIPP/E, CIPM, CIPT, AIGP and the combined DPO Ready programme.",
    "Data Protection": "Data protection and privacy training, from 1-day GDPR awareness through to full DPO certification.",
    "GDPR Training": "GDPR courses at every level: awareness for teams, foundation certificates and certified practitioner routes.",
    "Compliance Training": "Certified courses for the people who own compliance: DPOs, auditors and privacy programme managers.",
    "Cybersecurity": "Certified cybersecurity courses, from foundation level to security manager and analyst certifications.",
    "IT Governance & Audit": "Governance and audit certifications across privacy, AI and information security.",
    "Risk Management": "Certified risk management courses built on ISO 31000, ISO 27005 and incident management standards.",
    "Disaster Recovery & Business Continuity Training": "Business continuity and disaster recovery certifications built on ISO 22301 and ISO 22361.",
    "Business Resilience Training": "Resilience certifications covering continuity, crisis management and operational resilience.",
    "Business Analysis & Design": "Courses for analysts and designers working across security, assurance and AI implementation.",
    "Artificial Intelligence Training": "AI governance, safety and productivity courses, including AIGP, TAISE and ISO 42001 routes.",
    "BCS Training Courses": "Official BCS artificial intelligence qualifications: Essentials and Foundation certificates.",
}

# --------------------------------------------------------------- page metadata
# Written per course rather than derived, because the derived version truncated
# descriptions mid-word and ran titles past what Google will display.
# Titles are kept to ~38 chars so that with " | The Training Centre" they land
# under 60. Descriptions target 130-165. Every figure here is from the Arlo feed
# or the About page stat block; nothing is invented.
META = {
    "AIAG": ("AI Agents Foundation & Practitioner",
             "Build and govern AI agents that run real business workflows. 4 days live online, \u00a32,154, taught by practitioners with 25+ years in the field."),
    "AIGO": ("AIGP Certification Course",
             "The IAPP's AI Governance Professional certification, taught on official materials. 2 days live online, \u00a31,550, exam and IAPP membership included."),
    "AIPR": ("AI Productivity Training Course",
             "Put AI to work across your team's day-to-day: prompting, content, research and analysis. 4 days live online, \u00a32,154, capped at 15 delegates."),
    "AIST": ("AI Strategy & Governance Course",
             "AI strategy and governance in one programme: ROI mapping, global regulation, IP and data risk, procurement. 4 days live online, \u00a32,154."),
    "ARTI1": ("AI for Project Managers Course",
              "AI applied to real project delivery: core concepts, predictive analytics and smart resource allocation. 1 day live online plus support, \u00a31,395."),
    "BCSE": ("BCS Essentials in AI Certificate",
             "The official BCS Essentials Certificate in Artificial Intelligence: key AI terminology, tools, and what they mean for society. 1 day live online, \u00a3495."),
    "BCSF": ("BCS Foundation Certificate in AI",
             "The official BCS Foundation Certificate in Artificial Intelligence, the step up from Essentials. 3 days live online, \u00a31,314, capped at 15 delegates."),
    "CERT13": ("CDPO Certification Course",
               "Three days covering the whole DPO role, taught by working DPOs. Certified Data Protection Officer training, live online, \u00a31,450, exam included."),
    "CERT14": ("Certified GDPR Foundation",
               "Get properly grounded in the GDPR and the UK Data Protection Act 2018. Certified GDPR Foundation, 2 days live online, \u00a3595, capped at 15 delegates."),
    "CERT16": ("CIPT Certification Course",
               "Privacy engineering for the people who build and run the systems. IAPP CIPT, 2 days live online, \u00a31,395, exam and IAPP membership included."),
    "CERT27": ("CIPA Certification Course",
               "Audit privacy programmes with confidence. Certified Information Privacy Auditor, 3 days live online, \u00a31,250, taught by people who still do the job."),
    "CERT28": ("ISO 22361 Lead Crisis Manager",
               "Plan, run and lead crisis response to ISO 22361. Certified Lead Crisis Manager, 3 days live online, \u00a31,450, taught by practitioners, not career trainers."),
    "CERT30": ("Operational Resilience Manager",
               "Lead operational resilience across the organisation. Certified Operational Resilience Manager, 3 days live online, \u00a31,450, capped at 15 delegates."),
    "CERT7": ("CIPP/E Certification Course",
              "The recognised benchmark for European data protection law. IAPP CIPP/E, 2 days live online, \u00a31,395, exam and IAPP membership included."),
    "CERT8": ("CIPM Certification Course",
              "The privacy programme management credential that pairs with CIPP/E. IAPP CIPM, 2 days live online, \u00a31,395, exam and IAPP membership included."),
    "CYBE4": ("Cyber Assurance Practitioner",
              "Build and evidence cyber assurance that stands up to scrutiny. Certified Cyber Assurance Practitioner, 3 days live online, \u00a31,450, exam included."),
    "CYBE5": ("Cyber Security Foundation",
              "A single day to get grounded in cyber security fundamentals, for teams who need the basics right. Live online, \u00a3395, capped at 15 delegates."),
    "EURO": ("DPO Ready | CIPP/E and CIPM in a Week",
             "CIPP/E and CIPM combined in one week, the fastest route to both IAPP credentials. 4 days live online, \u00a32,750, exams and IAPP membership included."),
    "GDPR": ("GDPR Awareness Training",
             "Our 1 day workshop on Data Protection Act 2018 and GDPR obligations, worth 8 CPD hours. Live online, \u00a3325, capped at 15 delegates."),
    "ISO2": ("ISO 27001 Lead Implementer",
             "Implement an ISO 27001 information security management system end to end. Certified Lead Implementer, 3 days live online, \u00a31,450."),
    "ISO21": ("ISO 27001 Lead Auditor",
              "Plan and lead ISO 27001 audits to ISO 19011. Certified ISO 27001 Lead Auditor, 3 days live online, \u00a31,450, taught by working auditors."),
    "ISO210": ("ISO 27701 Lead Implementer",
               "The privacy extension to ISO 27001. Certified ISO 27701 Lead Implementer, 3 days live online, \u00a31,450, taught by practitioners with 25+ years' experience."),
    "ISO212": ("ISO 27005 Risk Manager",
               "Run an effective information security risk process built on ISO 27005. 3 days live online, \u00a31,450, capped at 15 delegates."),
    "ISO213": ("ISO 27035 Lead Incident Manager",
               "Build and lead incident response to ISO 27035. Certified Lead Incident Manager, 3 days live online, \u00a31,450, taught by people who still do the job."),
    "ISO214": ("Certified Cyber Security Analyst",
               "Internet, web and network security and how they fit together. Certified Cyber Security Analyst, 2 days live online, \u00a3695, capped at 15 delegates."),
    "ISO23": ("ISO 22301 Lead Auditor",
              "Plan and carry out business continuity audits to ISO 22301 and ISO 19011. Certified Lead Auditor, 3 days live online, \u00a31,450."),
    "ISO24": ("ISO 22301 Lead Implementer",
              "Implement a business continuity management system to ISO 22301. Certified Lead Implementer, 3 days live online, \u00a31,450, capped at 15 delegates."),
    "ISO25": ("Certified Cybersecurity Manager",
              "Lead cyber security across an organisation, not just the tooling. Certified Cybersecurity Manager, 3 days live online, \u00a31,450, capped at 15 delegates."),
    "ISO3": ("ISO 31000 Lead Risk Manager",
             "Build a risk management framework on ISO 31000 that the business will actually use. Certified Lead Risk Manager, 3 days live online, \u00a31,450."),
    "ISO35": ("ISO 31000 Risk Analyst",
              "The analyst route into ISO 31000 risk management. Certified ISO 31000 Risk Analyst, 3 days live online, \u00a31,250, capped at 15 delegates."),
    "ISO43": ("ISO 42001 Lead Implementer",
              "Implement an AI management system to ISO 42001, the first international AI standard. 3 days live online, \u00a31,450, capped at 15 delegates."),
    "ISO44": ("ISO 42001 Lead Auditor",
              "Audit AI management systems against ISO 42001. 3 days live online, \u00a31,450, taught by practitioners with 25+ years in the field."),
    "LEAD": ("Lead Disaster Recovery Manager",
             "Design, run and test disaster recovery that holds up under pressure. Lead Disaster Recovery Manager, 3 days live online, \u00a31,450."),
    "TRUS": ("TAISE | Trusted AI Safety Expert",
             "The first credential for trustworthy AI. Trusted AI Safety Expert, 3 days live online, \u00a31,995, taught by practitioners with 25+ years in the field."),
}

# Category (subject) pages. Same rules.
CATEGORY_META = {
    "IAPP Training": ("IAPP Certification Training Courses",
                      "Official IAPP courses taught live online: CIPP/E, CIPM, CIPT, AIGP and the combined DPO Ready week. Exam and IAPP membership included in the price."),
    "Data Protection": ("Data Protection Training Courses",
                        "Data protection and privacy training taught live online, from 1 day GDPR awareness through to full DPO certification. Classes capped at 15 delegates."),
    "GDPR Training": ("GDPR Training Courses",
                      "GDPR courses at every level: awareness for teams, foundation certificates and certified practitioner routes. Live online, capped at 15 delegates."),
    "Compliance Training": ("Compliance Training Courses",
                            "Certified courses for the people who own compliance: DPOs, auditors and privacy programme managers. Taught live online by working practitioners."),
    "ISO Standards Training": ("ISO Standards Training Courses",
                               "Certified ISO lead implementer, lead auditor and risk courses across 27001, 27701, 22301, 31000 and 42001. Taught live online, capped at 15."),
    "Cybersecurity Courses": ("Cybersecurity Training Courses",
                              "Certified cybersecurity courses from foundation level through to security manager and analyst certifications. Taught live online by practitioners."),
    "IT Governance & Audit": ("IT Governance & Audit Courses",
                              "Governance and audit certifications across privacy, AI and information security. Taught live online by auditors who still do the work."),
    "Risk Management": ("Risk Management Training Courses",
                        "Certified risk management courses built on ISO 31000, ISO 27005 and incident management standards. Live online, capped at 15 delegates."),
    "Disaster Recovery & Business Continuity Training": ("Disaster Recovery & BC Training",
                                                         "Business continuity and disaster recovery certifications built on ISO 22301 and ISO 22361. Taught live online, classes capped at 15 delegates."),
    "Business Resilience Training": ("Business Resilience Training",
                                     "Resilience certifications covering business continuity, crisis management and operational resilience. Taught live online by practitioners."),
    "Business Analysis & Design": ("Business Analysis & Design Courses",
                                   "Courses for analysts and designers working across security, assurance and AI implementation. Taught live online, capped at 15 delegates."),
    "Artificial Intelligence Training": ("AI Training Courses",
                                         "AI governance, safety and productivity courses including AIGP, TAISE and the ISO 42001 routes. Taught live online by practitioners, capped at 15."),
    "BCS Training Courses": ("BCS AI Training Courses",
                             "Official BCS artificial intelligence qualifications: the Essentials and Foundation certificates. Taught live online, classes capped at 15 delegates."),
}

def fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def fetch_templates():
    items, url = [], API
    while url:
        d = fetch_json(url)
        items += d.get("Items", [])
        nxt = d.get("NextPageUri")
        url = (nxt if nxt.startswith("http") else ARLO_HOST + nxt) if nxt else None
        time.sleep(1)
    return items

def clean_name(name):
    # Display-side fixes only (the feed keeps John's raw names until he fixes Arlo):
    # "IS0" typo with a zero, stray double spaces, trailing whitespace.
    n = name.replace("IS0 ", "ISO ").strip()
    return re.sub(r"\s{2,}", " ", n)

def esc(t):
    return html.escape(str(t), quote=True)

# ---------- content sanitiser: Arlo xhtml -> site-styled HTML ----------
BLOCK_P = 'class="text-[#47545D] leading-relaxed mt-4"'
BLOCK_H = 'class="font-display font-bold text-lg text-[#1E2B34] mt-7"'
BLOCK_UL = 'class="mt-4 space-y-2.5"'
BLOCK_LI = ('class="flex items-start gap-3 text-[#47545D] leading-relaxed"><span '
            'class="text-[#13B4EA] mt-1 shrink-0"><svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg></span><span')

class Sanitiser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.list_depth = 0
        self.drop_depth = 0        # inside dropped tags (img/script/style/iframe/table)
        self.para_open = False
        self.notes = []
    def handle_starttag(self, tag, attrs):
        if self.drop_depth:
            if tag in ("script", "style", "iframe", "table"): self.drop_depth += 1
            return
        if tag in ("script", "style", "iframe", "table"):
            self.drop_depth += 1
            self.notes.append("dropped:" + tag)
            return
        if tag == "img":
            self.notes.append("dropped:img")
            return
        if tag == "p" or tag == "div":
            self._close_para()
            self.out.append(f"<p {BLOCK_P}>")
            self.para_open = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._close_para()
            self.out.append(f"<h3 {BLOCK_H}>")
            self.para_open = "h3"
        elif tag in ("ul", "ol"):
            self._close_para()
            self.out.append(f"<ul {BLOCK_UL}>")
            self.list_depth += 1
        elif tag == "li":
            self.out.append(f"<li {BLOCK_LI}>")
        elif tag in ("strong", "b"):
            self.out.append('<strong class="font-semibold text-[#1E2B34]">')
        elif tag in ("em", "i"):
            self.out.append("<em>")
        elif tag == "br":
            self.out.append("<br>")
        elif tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith(("http://", "https://", "mailto:")):
                self.out.append(f'<a href="{esc(href)}" target="_blank" rel="noopener" class="font-semibold text-[#0085B7]">')
            else:
                self.out.append("<span>")
                self.notes.append("stripped-link:" + href[:40])
    def handle_endtag(self, tag):
        if self.drop_depth:
            if tag in ("script", "style", "iframe", "table"): self.drop_depth -= 1
            return
        if tag in ("p", "div"):
            if self.para_open is True: self.out.append("</p>"); self.para_open = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.para_open == "h3": self.out.append("</h3>"); self.para_open = False
        elif tag in ("ul", "ol"):
            if self.list_depth: self.out.append("</ul>"); self.list_depth -= 1
        elif tag == "li":
            self.out.append("</span></li>")
        elif tag in ("strong", "b"):
            self.out.append("</strong>")
        elif tag in ("em", "i"):
            self.out.append("</em>")
        elif tag == "a":
            self.out.append("</a></span>" if self.out and self.out[-1] == "<span>" else "</a>")
    def handle_data(self, data):
        if self.drop_depth: return
        t = data.replace("—", " - ").replace("–", " - ")  # no em/en dashes site-wide
        t = re.sub(r"\s+\-\s+", " - ", t)
        if t.strip() or self.para_open:
            self.out.append(esc(t) if "<" not in t else esc(t))
    def _close_para(self):
        if self.para_open is True: self.out.append("</p>")
        elif self.para_open == "h3": self.out.append("</h3>")
        self.para_open = False
    def result(self):
        self._close_para()
        h = "".join(self.out)
        h = re.sub(r"<p [^>]*>\s*(&nbsp;|\s)*</p>", "", h)  # empty paragraphs
        h = re.sub(r"(&nbsp;)+", " ", h)
        return h.strip()

def sanitise(raw_html, notes_sink):
    s = Sanitiser()
    s.feed(raw_html or "")
    notes_sink.extend(s.notes)
    return s.result()

def field_map(t):
    out = {}
    for f in ((t.get("Description") or {}).get("ContentFields") or []):
        out[f["FieldName"]] = (f.get("Content") or {}).get("Text", "")
    return out

def plain_text(raw_html):
    t = re.sub(r"<[^>]+>", " ", raw_html or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def duration_label(t):
    d = (t.get("AdvertisedDuration") or "").strip()
    if not d or d.upper() == "N/A": return "See dates"
    d = d[0].upper() + d[1:]
    return re.sub(r"\bdays\b", "days", d)


def baked_price(t):
    offers = t.get("BestAdvertisedOffers") or []
    if not offers: return ""
    # VAT-INCLUSIVE at John's instruction 31 Jul 2026 ("All prices should show with VAT
    # included. I have amended the T&C's to reflect this."). This supersedes his 30 Jul
    # ex-VAT instruction. On the 5 templates with a VAT rate in Arlo the inclusive figure
    # is 20% higher (AIPR/AIST/AIAG £2,154, BCSF £1,314); the rest have no VAT rate set,
    # so inclusive == exclusive. CYBE5 is entered inclusive (£395) so no hold is needed.
    amt = (offers[0].get("OfferAmount") or {}).get("AmountTaxInclusive")
    if amt is None: return ""
    whole = round(amt) == amt
    return "£" + format(amt, ",.0f" if whole else ",.2f")

VAT_RE = re.compile(r"[^.!?]*\bVAT\b[^.!?]*[.!?]?", re.I)

def strip_vat_sentences(txt, notes_sink):
    # VAT presentation is an open client decision; imported copy must not pre-empt it.
    hits = VAT_RE.findall(txt)
    if hits:
        notes_sink.extend("vat-sentence-removed: " + h.strip()[:80] for h in hits)
        txt = VAT_RE.sub("", txt)
    return txt

# ---------- shared page chrome ----------
HEAD = """<!DOCTYPE html>
<html lang="en-GB" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | The Training Centre</title>
<meta name="description" content="{meta_desc}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/@tailwindcss/browser@4"></script>
<style type="text/tailwindcss">
  @theme {{ --font-display: "Montserrat", sans-serif; --font-body: "Open Sans", sans-serif; }}
  body {{ font-family: var(--font-body); }}
  .font-display {{ font-family: var(--font-display); }}
  .tnum {{ font-variant-numeric: tabular-nums; }}
  .jumpnav::-webkit-scrollbar {{ display: none; }}
  .jumpnav {{ scrollbar-width: none; }}
  .btn-solid {{ display:inline-block; background:#13B4EA; color:#fff; font-weight:600; border-radius:4px; box-shadow:4px 4px 0 0 #1E2B34; transition:transform .12s ease, box-shadow .12s ease, background-color .12s ease; }}
  .btn-solid:hover {{ background:#0085B7; transform:translate(2px,2px); box-shadow:2px 2px 0 0 #1E2B34; }}
  .btn-light {{ display:inline-block; background:#fff; color:#1E2B34; font-weight:600; border:2px solid #1E2B34; border-radius:4px; box-shadow:4px 4px 0 0 #13B4EA; transition:transform .12s ease, box-shadow .12s ease; }}
  .btn-light:hover {{ transform:translate(2px,2px); box-shadow:2px 2px 0 0 #13B4EA; }}
  .card-pop {{ box-shadow:8px 8px 0 0 rgba(19,180,234,.28); }}
</style>
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','GTM-PHR6JF2');</script>
</head>
<body class="bg-[#F7F9FA] text-[#2C2C2C] antialiased pb-20 md:pb-0">
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PHR6JF2" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
"""

HEADER = """
<header class="bg-white border-b border-[#323F48]/10 sticky top-0 z-50">
  <div class="bg-[#1E2B34] text-[#C8D2D9]">
    <div class="max-w-6xl mx-auto px-5 py-1.5 flex items-center justify-between gap-4 text-xs sm:text-sm">
      <p class="whitespace-nowrap">Got a question? Call <a href="tel:+442038589207" class="font-semibold text-white hover:text-[#13B4EA]">020 3858 9207</a></p>
      <a href="mailto:info@the-training-centre.com" class="hidden sm:block hover:text-white">info@the-training-centre.com</a>
    </div>
  </div>
  <div class="max-w-6xl mx-auto px-5 py-3 flex items-center justify-between gap-4">
    <a href="/" aria-label="The Training Centre home"><img src="/assets/ttc-logo.png" alt="The Training Centre. Learn. Evolve. Lead." class="h-9 sm:h-11 w-auto"></a>
    <nav class="hidden lg:flex items-center gap-7 text-sm text-[#47545D]" aria-label="Site">
      <a href="/courses/" class="{nav_courses}">Courses</a>
      <a href="/schedule/" class="{nav_schedule}">Course schedule</a>
      <a href="/in-house-training/" class="hover:text-[#0085B7]">In-house training</a>
      <a href="/about/" class="hover:text-[#0085B7]">About us</a>
      <a href="/insights/" class="hover:text-[#0085B7]">Insights</a>
      <a href="/contact/" class="hover:text-[#0085B7]">Contact</a>
    </nav>
    <div class="flex items-center gap-2 sm:gap-4">
      <a href="tel:+442038589207" class="hidden xl:flex items-center gap-2 font-semibold text-[#1E2B34] whitespace-nowrap"><span class="text-[#13B4EA]"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5c0 8 7 15 15 15l2-4-4-2-2 2c-3-1.5-5.5-4-7-7l2-2-2-4-4 2z"/></svg></span>020 3858 9207</a>
      <a href="{cta_href}" class="btn-solid hidden sm:inline-block text-sm px-5 py-2.5 whitespace-nowrap">{cta_label}</a>
      <a href="tel:+442038589207" class="lg:hidden flex items-center justify-center w-11 h-11 rounded-[4px] border border-[#13B4EA] text-[#0085B7]" aria-label="Call us on 020 3858 9207"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5c0 8 7 15 15 15l2-4-4-2-2 2c-3-1.5-5.5-4-7-7l2-2-2-4-4 2z"/></svg></a>
      <button id="menu-toggle" type="button" class="lg:hidden flex items-center justify-center w-11 h-11 rounded-[4px] border border-[#323F48]/20 text-[#1E2B34]" aria-expanded="false" aria-controls="mobile-menu" aria-label="Open menu">
        <svg id="menu-icon-open" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
        <svg id="menu-icon-close" class="w-6 h-6 hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </div>
  </div>
{jumpnav}
  <div id="mobile-menu" hidden class="lg:hidden border-t border-[#323F48]/10 bg-white">
    <nav class="divide-y divide-[#323F48]/10" aria-label="Site menu">
      <a href="/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">Home</a>
      <a href="/courses/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">Courses</a>
      <a href="/schedule/" class="block px-5 py-3.5 font-semibold text-[#0085B7]">Course schedule</a>
      <a href="/in-house-training/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">In-house training</a>
      <a href="/about/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">About us</a>
      <a href="/insights/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">Insights</a>
      <a href="/contact/" class="block px-5 py-3.5 font-semibold text-[#1E2B34]">Contact</a>
    </nav>
    <div class="px-5 py-4 border-t border-[#323F48]/10 flex flex-col gap-3">
      <a href="{cta_href}" class="mobile-menu-cta btn-solid block text-center py-3.5">{cta_label}</a>
      <a href="tel:+442038589207" class="flex items-center justify-center gap-2 font-semibold text-[#1E2B34] py-2"><span class="text-[#13B4EA]"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5c0 8 7 15 15 15l2-4-4-2-2 2c-3-1.5-5.5-4-7-7l2-2-2-4-4 2z"/></svg></span>020 3858 9207</a>
    </div>
  </div>
</header>
"""

FOOTER = """
<footer class="bg-[#1E2B34] text-[#8FA0AB]">
  <div class="max-w-6xl mx-auto px-5 py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4 text-sm">
    <div>
      <p class="text-white font-display font-bold text-base">The Training Centre</p>
      <p class="mt-3">Certified privacy, data protection, AI and ISO training, taught live online by trainers who still do the job.</p>
      <a href="tel:+442038589207" class="block mt-4 font-semibold text-white hover:text-[#13B4EA]">020 3858 9207</a>
      <a href="mailto:info@the-training-centre.com" class="block mt-1 hover:text-white">info@the-training-centre.com</a>
    </div>
    <div>
      <p class="text-white font-display font-bold text-base">Courses</p>
      <ul class="mt-3 space-y-2">
        <li><a href="/courses/iapp-training/" class="hover:text-white">IAPP Training</a></li>
        <li><a href="/courses/data-protection/" class="hover:text-white">Data Protection</a></li>
        <li><a href="/courses/ai-training/" class="hover:text-white">Artificial Intelligence Training</a></li>
        <li><a href="/courses/iso-standards/" class="hover:text-white">Certified ISO Standards Training</a></li>
        <li><a href="/courses/cybersecurity/" class="hover:text-white">Cybersecurity Courses</a></li>
      </ul>
    </div>
    <div>
      <p class="text-white font-display font-bold text-base">Quick links</p>
      <ul class="mt-3 space-y-2">
        <li><a href="/schedule/" class="hover:text-white">Course schedule</a></li>
        <li><a href="/in-house-training/" class="hover:text-white">In-house training</a></li>
        <li><a href="/trainers/" class="hover:text-white">Meet the trainers</a></li>
        <li><a href="/about/" class="hover:text-white">About us</a></li>
        <li><a href="/insights/" class="hover:text-white">Insights</a></li>
        <li><a href="/contact/" class="hover:text-white">Speak to a course adviser</a></li>
      </ul>
    </div>
    <div>
      <p class="text-white font-display font-bold text-base">Legal</p>
      <ul class="mt-3 space-y-2">
        <li><a href="/terms/" class="hover:text-white">Terms &amp; conditions</a></li>
        <li><a href="/privacy/" class="hover:text-white">Privacy notice</a></li>
      </ul>
    </div>
  </div>
  <div class="border-t border-white/10">
    <div class="max-w-6xl mx-auto px-5 py-5 text-xs leading-relaxed">
      <p>&copy; 2026 The Training Centre. The Training Centre Ltd is registered in England, company number 15746376. Registered office: Seedbed Business Centre, Vanguard Way, Shoeburyness, Essex, SS3 9QY. VAT number GB476426465.</p>
    </div>
  </div>
</footer>
"""

MENU_JS = """
<script>
(function () {
  var btn = document.getElementById('menu-toggle');
  var menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  var io = document.getElementById('menu-icon-open');
  var ic = document.getElementById('menu-icon-close');
  function setOpen(open) {
    menu.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    io.classList.toggle('hidden', open);
    ic.classList.toggle('hidden', !open);
  }
  btn.addEventListener('click', function () { setOpen(menu.hidden); });
  menu.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { setOpen(false); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.hidden) { setOpen(false); btn.focus(); }
  });
})();
</script>
"""

FORM_JS = """
<script>
document.getElementById('enquiry-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var form = this;
  var btn = form.querySelector('button[type="submit"]');
  btn.disabled = true; btn.textContent = 'Sending...';
  fetch('https://lp-form-handler.claireljarrett.workers.dev/submit', { method: 'POST', body: new FormData(form) })
    .then(function() { window.location.href = '/thank-you/'; })
    .catch(function() { btn.disabled = false; btn.textContent = 'Send my question'; alert('Something went wrong. Please call us on 020 3858 9207.'); });
});
</script>
"""

def enquiry_form(course_value):
    return f"""
<section id="enquire" class="scroll-mt-28 max-w-6xl mx-auto px-5 py-16 grid md:grid-cols-[0.9fr_1.1fr] gap-10">
  <div>
    <h2 class="font-display font-extrabold text-3xl sm:text-4xl text-[#1E2B34]" style="text-wrap:balance">Ask us anything about this course</h2>
    <p class="text-[#47545D] mt-4 leading-relaxed">Booking for a team, need sign-off from above, or just want to check it is the right course? Send the form and a course adviser replies the same working day. If we are not the right fit, we will say so.</p>
    <a href="tel:+442038589207" class="mt-6 inline-flex items-center gap-2 font-semibold text-[#1E2B34]"><span class="text-[#13B4EA]"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5c0 8 7 15 15 15l2-4-4-2-2 2c-3-1.5-5.5-4-7-7l2-2-2-4-4 2z"/></svg></span>020 3858 9207</a>
    <p class="text-sm text-[#47545D] mt-2">Our office team answers during UK business hours.</p>
  </div>
  <form id="enquiry-form" action="https://lp-form-handler.claireljarrett.workers.dev/submit" method="POST" class="bg-white border border-[#323F48]/10 rounded-[8px] p-6 sm:p-8 space-y-4">
    <input type="hidden" name="project" value="the-training-centre">
    <input type="hidden" name="Course" value="{esc(course_value)}">
    <div><label for="name" class="block text-sm font-semibold text-[#1E2B34] mb-1.5">Your name</label>
      <input required type="text" id="name" name="name" class="w-full border border-[#323F48]/20 rounded-[4px] px-4 py-3 focus:outline-none focus:border-[#13B4EA]" autocomplete="name"></div>
    <div><label for="email" class="block text-sm font-semibold text-[#1E2B34] mb-1.5">Work email</label>
      <input required type="email" id="email" name="email" class="w-full border border-[#323F48]/20 rounded-[4px] px-4 py-3 focus:outline-none focus:border-[#13B4EA]" autocomplete="email"></div>
    <div><label for="phone" class="block text-sm font-semibold text-[#1E2B34] mb-1.5">Phone number</label>
      <input required type="tel" id="phone" name="phone" class="w-full border border-[#323F48]/20 rounded-[4px] px-4 py-3 focus:outline-none focus:border-[#13B4EA]" autocomplete="tel"></div>
    <div><label for="message" class="block text-sm font-semibold text-[#1E2B34] mb-1.5">Your question <span class="font-normal text-[#47545D]">(optional)</span></label>
      <textarea id="message" name="message" rows="3" class="w-full border border-[#323F48]/20 rounded-[4px] px-4 py-3 focus:outline-none focus:border-[#13B4EA]" placeholder="Dates, team bookings, payment plans, whether this is the right course..."></textarea></div>
    <button type="submit" class="btn-solid w-full py-3.5">Send my question</button>
    <p id="form-note" class="text-xs text-[#47545D]">We reply the same working day. Your details go to our course advisers and nowhere else.</p>
  </form>
</section>
"""

STATS_BAND = """
<section class="bg-white border-y border-[#323F48]/10">
  <div class="max-w-6xl mx-auto px-5 py-8 grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-6 md:divide-x md:divide-[#323F48]/10">
    <div class="md:px-6 md:first:pl-0"><p class="tnum font-display text-2xl font-semibold text-[#1E2B34]">No 1</p><p class="text-sm text-[#47545D] mt-1">IAPP training provider in the UK</p></div>
    <div class="md:px-6"><p class="tnum font-display text-2xl font-semibold text-[#1E2B34]">3,500+</p><p class="text-sm text-[#47545D] mt-1">delegates trained</p></div>
    <div class="md:px-6"><p class="tnum font-display text-2xl font-semibold text-[#1E2B34]">25 yrs</p><p class="text-sm text-[#47545D] mt-1">minimum industry experience, every trainer</p></div>
    <div class="md:px-6"><p class="tnum font-display text-2xl font-semibold text-[#1E2B34]">2017</p><p class="text-sm text-[#47545D] mt-1">delivering certified training since</p></div>
  </div>
</section>
"""

def jumpnav_course():
    return """<nav class="jumpnav border-t border-[#323F48]/10 bg-white overflow-x-auto whitespace-nowrap px-5 hidden md:block">
    <div class="max-w-6xl mx-auto flex gap-7 text-sm py-2.5 text-[#47545D]">
      <a href="#dates" class="hover:text-[#0085B7]">Dates &amp; times</a>
      <a href="#about" class="hover:text-[#0085B7]">What it covers</a>
      <a href="#who" class="hover:text-[#0085B7]">Who it&rsquo;s for</a>
      <a href="#details" class="hover:text-[#0085B7]">Course details</a>
      <a href="#enquire" class="hover:text-[#0085B7]">Enquire</a>
      <a href="#dates" class="font-semibold text-[#0085B7]">Book</a>
    </div>
  </nav>"""

STICKY_CTA = """
<div class="fixed bottom-0 inset-x-0 z-50 md:hidden bg-white border-t border-[#323F48]/15 px-4 py-3 flex gap-3">
  <a href="tel:+442038589207" class="btn-light flex-1 text-center py-3">Call us</a>
  <a href="{cta_href}" class="btn-solid flex-1 text-center py-3">{cta_label}</a>
</div>
"""

def included_items(fm, notes):
    """Items come as one-per-<p> (or <li>/<br>). Trailing '*' marks footnoted items;
    a paragraph starting '*' is the footnote itself. Returns (items, footnote)."""
    raw = fm.get("What's Included?", "")
    chunks = re.findall(r"<li[^>]*>(.*?)</li>", raw, re.S)
    if not chunks:
        chunks = re.split(r"</p>|<br\s*/?>", raw)
    items, footnote = [], ""
    for c in chunks:
        txt = plain_text(c)
        txt = strip_vat_sentences(txt, notes).strip()
        if not txt: continue
        if txt.startswith("*"):
            footnote = (footnote + " " + txt.lstrip("* ").strip()).strip()
            continue
        items.append(txt.rstrip("*").strip(" ."))
    return items[:8], footnote

def build_course_page(t, notes):
    code = t["Code"]
    name = clean_name(t["Name"])
    fm = field_map(t)
    cats = [c["Name"] for c in (t.get("Categories") or [])]
    primary_cat = cats[0] if cats else "Certified training"
    summary = plain_text((t.get("Description") or {}).get("Summary", "")) or plain_text(fm.get("Description", ""))[:180]
    summary = strip_vat_sentences(summary, notes)
    dur = duration_label(t)
    slug = SLUGS[code]

    about_html = ""
    for fname in ("About This Course", "Description"):
        raw = fm.get(fname)
        if raw:
            cleaned = sanitise(strip_vat_sentences(raw, notes), notes)
            if cleaned: about_html += cleaned
    who_html = sanitise(strip_vat_sentences(fm.get("Who Should Attend?", ""), notes), notes)
    prereq_html = sanitise(strip_vat_sentences(fm.get("Prerequisites", ""), notes), notes)

    detail_fields = []
    for fname in ("Assessment", "Accreditation", "CPD Hours", "Provided by", "Our Guarantee"):
        raw = fm.get(fname)
        if raw:
            cleaned = sanitise(strip_vat_sentences(raw, notes), notes)
            if cleaned and plain_text(raw):
                detail_fields.append((fname, cleaned))

    inc, inc_note = included_items(fm, notes)
    inc_html = "".join(
        f'<li class="flex items-start gap-3"><span class="text-[#13B4EA] mt-0.5"><svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 13l4 4L19 7"/></svg></span><span>{esc(i)}</span></li>'
        for i in inc)
    aside = f"""
  <aside class="bg-[#1E2B34] rounded-[8px] p-6 sm:p-7">
    <h2 class="font-display font-bold text-white text-lg">Included in your fee</h2>
    <ul class="mt-4 space-y-3 text-[#C8D2D9]">{inc_html}</ul>
    {("<p class=\"text-sm text-[#8FA0AB] mt-4\">* " + esc(inc_note) + "</p>") if inc_note else ""}<p class="text-sm text-[#8FA0AB] mt-5 border-t border-white/10 pt-4">0% interest payment plans available on all courses. Pay by card, invoice with a PO reference, or direct debit.</p>
  </aside>""" if inc else ""

    details_html = "".join(f"""
      <details class="group border border-[#323F48]/10 rounded-[8px] bg-white">
        <summary class="flex items-center justify-between cursor-pointer list-none px-6 py-4 font-semibold text-[#1E2B34]">
          {esc(fname)}
          <span class="text-[#0085B7] group-open:rotate-45 text-2xl font-light leading-none ml-4">+</span>
        </summary>
        <div class="px-6 pb-5 -mt-1">{content}</div>
      </details>""" for fname, content in detail_fields)

    price_fb = baked_price(t)
    nextdate_fallback = "Being scheduled"
    _m = META.get(code)
    meta_desc = _m[1] if _m else (
        (summary[:150] + "...") if len(summary) > 153 else summary)

    page = HEAD.format(title=esc(_m[0] if _m else name), meta_desc=esc(meta_desc))
    page += HEADER.format(nav_courses='hover:text-[#0085B7]', nav_schedule='hover:text-[#0085B7]',
                          cta_href="#dates", cta_label="See dates &amp; book", jumpnav=jumpnav_course())
    page += f"""
<nav class="max-w-6xl mx-auto px-5 pt-5 text-sm text-[#47545D]" aria-label="Breadcrumb">
  <a href="/courses/" class="hover:text-[#0085B7]">Courses</a> <span class="mx-1">/</span> <a href="{CATEGORIES.get(primary_cat, ('', '/courses/'))[1]}" class="hover:text-[#0085B7]">{esc(primary_cat)}</a> <span class="mx-1">/</span> <span class="text-[#1E2B34] font-semibold">{esc(name)}</span>
</nav>

<section class="max-w-6xl mx-auto px-5 pt-6 pb-10 md:pb-14 grid md:grid-cols-[1.15fr_0.85fr] gap-10 items-start">
  <div>
    <p class="text-[#0085B7] font-display font-bold uppercase tracking-[0.14em] text-xs">{esc(primary_cat)} &middot; <span data-ttc-place="{esc(code)}">Live online</span></p>
    <h1 class="font-display font-extrabold text-[#1E2B34] text-3xl sm:text-4xl md:text-[2.7rem] leading-tight mt-4" style="text-wrap:balance">{esc(name)}</h1>
    <p class="text-[#47545D] text-lg leading-relaxed mt-5 max-w-[54ch]">{esc(summary)}</p>
    <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4 mt-8 tnum">
      <div><dt class="text-xs font-semibold uppercase tracking-wide text-[#47545D]">Length</dt><dd class="font-display font-bold text-[#1E2B34] mt-1">{esc(dur)}</dd></div>
      <div><dt class="text-xs font-semibold uppercase tracking-wide text-[#47545D]">Next date</dt><dd class="font-display font-bold text-[#1E2B34] mt-1" data-ttc-nextdate="{esc(code)}">{esc(nextdate_fallback)}</dd></div>
      <div><dt class="text-xs font-semibold uppercase tracking-wide text-[#47545D]">Format</dt><dd class="font-display font-bold text-[#1E2B34] mt-1" data-ttc-place="{esc(code)}">Live online</dd></div>
      <div><dt class="text-xs font-semibold uppercase tracking-wide text-[#47545D]">Fee</dt><dd class="font-display font-bold text-[#1E2B34] mt-1" data-ttc-price="{esc(code)}">{esc(price_fb)}</dd></div>
    </dl>
    <div class="flex flex-wrap items-center gap-4 mt-8">
      <a href="#dates" class="btn-solid px-7 py-3.5">See dates &amp; book</a>
      <a href="#enquire" class="btn-light px-7 py-3.5">Ask a question</a>
    </div>
  </div>{aside}
</section>
""" + STATS_BAND + f"""

<section id="dates" class="scroll-mt-28 max-w-6xl mx-auto px-5 py-16">
  <div class="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
    <h2 class="font-display font-extrabold text-3xl sm:text-4xl text-[#1E2B34]">Upcoming dates</h2>
    <p class="text-[#47545D]" data-ttc-meta="{esc(code)}">Live online</p>
  </div>
  <div class="bg-white border border-[#323F48]/10 rounded-[8px] mt-8 overflow-hidden divide-y divide-[#323F48]/10 tnum" data-ttc-dates="{esc(code)}" data-ttc-max="6">
    <div class="px-6 sm:px-8 py-4"><p class="text-sm text-[#47545D]">Loading dates...</p></div>
  </div>
  <p class="text-sm text-[#47545D] mt-4">Plans change? You can transfer to another date yourself, free of charge, up to the day before the course, straight from your booking email.</p>
</section>

<section id="about" class="scroll-mt-28 bg-white border-y border-[#323F48]/10">
  <div class="max-w-3xl mx-auto px-5 py-16">
    <h2 class="font-display font-extrabold text-3xl sm:text-4xl text-[#1E2B34]">What the course covers</h2>
    <div class="mt-2">{about_html or '<p ' + BLOCK_P + '>' + esc(summary) + '</p>'}</div>
  </div>
</section>

<section id="who" class="scroll-mt-28 max-w-6xl mx-auto px-5 py-16 grid md:grid-cols-2 gap-10">
  <div>
    <h2 class="font-display font-extrabold text-2xl sm:text-3xl text-[#1E2B34]">Who should attend</h2>
    <div class="mt-2">{who_html or '<p ' + BLOCK_P + '>Ask us whether this course fits your role: a course adviser will tell you straight.</p>'}</div>
  </div>
  <div>
    <h2 class="font-display font-extrabold text-2xl sm:text-3xl text-[#1E2B34]">Prerequisites</h2>
    <div class="mt-2">{prereq_html or '<p ' + BLOCK_P + '>None.</p>'}</div>
  </div>
</section>
""" + (f"""
<section id="details" class="scroll-mt-28 bg-white border-y border-[#323F48]/10">
  <div class="max-w-3xl mx-auto px-5 py-16">
    <h2 class="font-display font-extrabold text-3xl sm:text-4xl text-[#1E2B34]">Course details</h2>
    <div class="space-y-3 mt-9">{details_html}</div>
  </div>
</section>""" if details_html else "") + enquiry_form(name)
    page += FOOTER
    page += STICKY_CTA.format(cta_href="#dates", cta_label="See dates &amp; book")
    page += '\n<script src="/assets/schedule-data.js"></script>\n<script src="/assets/schedule.js"></script>\n'
    page += FORM_JS + MENU_JS + "</body>\n</html>\n"

    outdir = os.path.join(BASE, "courses", slug)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    return f"/courses/{slug}/"

def course_url(code):
    if code in HANDBUILT: return HANDBUILT[code]
    if code in SLUGS: return f"/courses/{SLUGS[code]}/"
    return None

def build_category_page(cat_name, slug, templates, notes):
    courses = [t for t in templates
               if cat_name in [c["Name"] for c in (t.get("Categories") or [])]
               and t["Code"] not in SKIP]
    courses.sort(key=lambda t: clean_name(t["Name"]))
    intro = CATEGORY_INTROS.get(cat_name) or CATEGORY_INTROS.get(cat_name.replace(" Courses", ""))
    if not intro:
        intro = f"Certified {cat_name.lower()} courses, taught live online."
    rows = ""
    for t in courses:
        name = clean_name(t["Name"])
        url = course_url(t["Code"])
        summary = strip_vat_sentences(plain_text((t.get("Description") or {}).get("Summary", "")), notes)
        dur = duration_label(t)
        code = t["Code"]
        rows += f"""
      <article class="bg-white border border-[#323F48]/10 rounded-[8px] overflow-hidden">
        <div class="px-6 sm:px-8 py-6 flex flex-wrap items-start gap-x-8 gap-y-4">
          <div class="flex-1 min-w-[16rem]">
            <h2 class="font-display font-bold text-xl text-[#1E2B34]"><a href="{url}" class="hover:text-[#0085B7]">{esc(name)}</a></h2>
            <p class="text-[#47545D] leading-relaxed mt-2">{esc(summary)}</p>
            <p class="text-sm text-[#47545D] mt-3 tnum">{esc(dur)} &middot; live online &middot; <span data-ttc-nextdate="{esc(code)}">dates being scheduled</span></p>
          </div>
          <div class="flex flex-col items-start sm:items-end gap-3 sm:text-right">
            <p class="tnum font-display font-extrabold text-[#0085B7] text-xl" data-ttc-price="{esc(code)}">{esc(baked_price(t))}</p>
            <div class="flex gap-3">
              <a href="{url}" class="btn-solid text-sm px-5 py-2.5 whitespace-nowrap">Course details</a>
              <a href="{url}#dates" class="btn-light text-sm px-5 py-2.5 whitespace-nowrap">Dates</a>
            </div>
          </div>
        </div>
      </article>"""
    title = cat_name if "course" in cat_name.lower() or "training" in cat_name.lower() else cat_name + " courses"
    _cm = CATEGORY_META.get(cat_name)
    page = HEAD.format(title=esc(_cm[0] if _cm else title),
                       meta_desc=esc(_cm[1] if _cm else intro))
    page += HEADER.format(nav_courses='font-semibold text-[#0085B7]', nav_schedule='hover:text-[#0085B7]',
                          cta_href="/schedule/", cta_label="Course schedule", jumpnav="")
    page += f"""
<nav class="max-w-6xl mx-auto px-5 pt-5 text-sm text-[#47545D]" aria-label="Breadcrumb">
  <a href="/courses/" class="hover:text-[#0085B7]">Courses</a> <span class="mx-1">/</span> <span class="text-[#1E2B34] font-semibold">{esc(cat_name)}</span>
</nav>

<section class="max-w-6xl mx-auto px-5 pt-6 pb-10">
  <p class="text-[#0085B7] font-display font-bold uppercase tracking-[0.14em] text-xs">{len(courses)} course{"s" if len(courses) != 1 else ""} &middot; Live online</p>
  <h1 class="font-display font-extrabold text-[#1E2B34] text-3xl sm:text-4xl md:text-[2.7rem] leading-tight mt-4" style="text-wrap:balance">{esc(cat_name)}</h1>
  <p class="text-[#47545D] text-lg leading-relaxed mt-5 max-w-[60ch]">{esc(intro)}</p>
</section>

<section class="max-w-6xl mx-auto px-5 pb-16">
  <div class="space-y-6 tnum">{rows}
  </div>
</section>
""" + enquiry_form(cat_name)
    page += FOOTER
    page += STICKY_CTA.format(cta_href="/schedule/", cta_label="Course schedule")
    page += '\n<script src="/assets/schedule-data.js"></script>\n<script src="/assets/schedule.js"></script>\n'
    page += FORM_JS + MENU_JS + "</body>\n</html>\n"

    outdir = os.path.join(BASE, "courses", slug)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    return len(courses)

def build_courses_index(templates, cat_counts):
    cats_html = ""
    for cat_name, (slug, path) in CATEGORIES.items():
        n = cat_counts.get(cat_name, 0)
        if not n: continue
        cats_html += f"""
      <a href="{path}" class="block bg-white border border-[#323F48]/10 rounded-[8px] px-6 py-5 hover:border-[#13B4EA] group">
        <p class="font-display font-bold text-lg text-[#1E2B34] group-hover:text-[#0085B7]">{esc(cat_name)}</p>
        <p class="text-sm text-[#47545D] mt-1 tnum">{n} course{"s" if n != 1 else ""}</p>
      </a>"""
    az = ""
    listed = [t for t in templates if t["Code"] not in SKIP and course_url(t["Code"])]
    listed.sort(key=lambda t: clean_name(t["Name"]).lower())
    for t in listed:
        az += f"""
      <li class="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-3">
        <a href="{course_url(t["Code"])}" class="font-semibold text-[#1E2B34] hover:text-[#0085B7]">{esc(clean_name(t["Name"]))}</a>
        <span class="text-sm text-[#47545D] tnum">{esc(duration_label(t))} &middot; <span data-ttc-nextdate="{esc(t["Code"])}">dates being scheduled</span></span>
      </li>"""
    page = HEAD.format(title="All courses", meta_desc="Every certified course we run: privacy, data protection, GDPR, AI, cybersecurity, risk and ISO standards. All taught live online.")
    page += HEADER.format(nav_courses='font-semibold text-[#0085B7]', nav_schedule='hover:text-[#0085B7]',
                          cta_href="/schedule/", cta_label="Course schedule", jumpnav="")
    page += f"""
<section class="max-w-6xl mx-auto px-5 pt-10 pb-10">
  <p class="text-[#0085B7] font-display font-bold uppercase tracking-[0.14em] text-xs">{len(listed)} certified courses &middot; Live online</p>
  <h1 class="font-display font-extrabold text-[#1E2B34] text-3xl sm:text-4xl md:text-[2.7rem] leading-tight mt-4" style="text-wrap:balance">Find your course</h1>
  <p class="text-[#47545D] text-lg leading-relaxed mt-5 max-w-[60ch]">Browse by subject, or scan the full list. Every course runs live online with real trainers, and every date on this site comes straight from our live schedule.</p>
</section>

<section class="max-w-6xl mx-auto px-5 pb-14">
  <h2 class="font-display font-extrabold text-2xl sm:text-3xl text-[#1E2B34]">By subject</h2>
  <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-7">{cats_html}
  </div>
</section>

<section class="bg-white border-y border-[#323F48]/10">
  <div class="max-w-3xl mx-auto px-5 py-14">
    <h2 class="font-display font-extrabold text-2xl sm:text-3xl text-[#1E2B34]">All courses A to Z</h2>
    <ul class="divide-y divide-[#323F48]/10 mt-6 tnum">{az}
    </ul>
  </div>
</section>
""" + enquiry_form("Course finder")
    page += FOOTER
    page += STICKY_CTA.format(cta_href="/schedule/", cta_label="Course schedule")
    page += '\n<script src="/assets/schedule-data.js"></script>\n<script src="/assets/schedule.js"></script>\n'
    page += FORM_JS + MENU_JS + "</body>\n</html>\n"
    with open(os.path.join(BASE, "courses", "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)

def main():
    templates = fetch_templates()
    print(f"templates fetched: {len(templates)}")
    notes = []
    built = []
    for t in templates:
        code = t.get("Code")
        if code in SKIP or code in HANDBUILT: continue
        if code not in SLUGS:
            print(f"  !! no slug for {code} ({t.get('Name')}) - add to SLUGS"); continue
        built.append(build_course_page(t, notes))
    print(f"course pages written: {len(built)}")
    cat_counts = {}
    for cat_name, (slug, path) in CATEGORIES.items():
        if cat_name == "ISO Standards Training":
            cat_counts[cat_name] = sum(1 for t in templates if cat_name in [c["Name"] for c in (t.get("Categories") or [])] and t["Code"] not in SKIP)
            continue  # existing hand-built overview page serves this category
        n = build_category_page(cat_name, slug, templates, notes)
        cat_counts[cat_name] = n
        print(f"  category {slug}: {n} courses")
    build_courses_index(templates, cat_counts)
    print("courses index written")
    uniq = sorted(set(notes))
    if uniq:
        print("\ncontent notes (dropped/stripped):")
        for n in uniq: print("  ", n)

if __name__ == "__main__":
    main()
    # Canonical / Open Graph / Course structured data. Run last so it sees the
    # final titles and descriptions, and so a regen can never drop them.
    import _seo_meta
    _seo_meta.main()
