# Source Playbook

Which tool to use for which source. Read this once per report, not per source.

## Source trust hierarchy

Every section below already names its own primary source, but keep this ordering in
mind whenever a claim could be pulled from more than one place — it's what makes a
material fact "verified" rather than just "found":

1. **Primary sources** — exchange filings (BSE/NSE Regulation 30 disclosures, annual
   reports, investor presentations as filed), NCLT/court orders, credit-rating agency
   rationales, and the company's own concall transcripts/press releases as filed. These
   are citable as-is.
2. **Structured financial data** — screener.in (P&L, balance sheet, cash flow, ratios,
   shareholding-pattern history) or an equivalent aggregator that mirrors filed data
   without editorializing on it. Reliable for numbers; still worth a primary-source
   cross-check for anything that ends up in a Key Risks or Investment Thesis Summary
   claim.
3. **Discovery-only sources** — news aggregators, PR-syndicated releases, Trendlyne/
   Moneycontrol-style sites. Fine for finding leads (a contract win, a rating action, a
   management interview worth checking) but never cite a number from one of these
   without tracing it back to the primary filing or press release it originated from —
   aggregators garble numbers more often than the fetch effort to verify would suggest.

Flag an unverified management claim explicitly rather than silently upgrading its
confidence (e.g. "management states X on the concall — not yet corroborated by an
independent filing") — this is the same discipline as the "customer's own guidance"
corroboration check below, just stated as a general rule.

## Important sandbox constraint

The shell sandbox's outbound network is allowlisted — raw `curl`/`requests`/`urllib`
calls to arbitrary domains (screener.in, bseindia.com, nseindia.com, company IR pages)
will fail with a proxy 403. This is expected, not a bug. **Never write or run a Python
fetch script against these domains.** All fetching goes through the platform's own web
tools (`WebSearch`, `mcp__workspace__web_fetch`, and Claude in Chrome as fallback), which
route through an approved path. Scripts in `scripts/` only ever touch local files.

## Primary source: screener.in

screener.in is the fastest single source for an Indian listed company — it aggregates:
- Key ratios, quarterly/annual financials, shareholding pattern (structured, no PDF
  parsing needed)
- A "Documents" tab linking the company's BSE/NSE-filed annual reports, credit rating
  reports, and (for many companies) concall transcripts and investor presentations

Steps:
1. `WebSearch` for `site:screener.in <company name>` to find the exact company page
   (or construct `https://www.screener.in/company/<BSE_OR_NSE_SYMBOL>/consolidated/`
   if the symbol is already known).
2. `mcp__workspace__web_fetch` the page. screener.in is mostly server-rendered, so
   web_fetch should return real content — ratios table, quarterly results, and the
   Documents section with links.
3. If the fetch returns a mostly-empty shell (JS-rendered widgets like the
   price chart won't matter, but if the *data tables* are missing), escalate to Claude
   in Chrome (`navigate` + `get_page_text`) per the platform's escalation rule.
4. Pull the direct links to the latest concall transcript, investor presentation, and
   annual report from the Documents tab, then fetch/download those individually (see below).

## Concall transcripts

Usually PDFs hosted on BSE announcements, the company's own investor relations page, or
linked from screener.in's Documents tab. Some are also summarized/hosted by third-party
aggregators.
1. Get the direct PDF URL (from screener.in Documents tab or `WebSearch` for
   `<company name> concall transcript <quarter> filetype:pdf`).
2. `mcp__workspace__web_fetch` the PDF URL — if the tool returns the PDF content, save it
   directly to `research_cache/<COMPANY_SLUG>/raw/<file>.pdf`.
3. If web_fetch can't retrieve a binary PDF cleanly, ask the user to download and drop it
   in the workspace folder instead, or use Chrome to navigate + download.
4. Run `scripts/pdf_to_text.py` on the saved PDF (local, no network).

## Investor presentations

Same path as concall transcripts — usually a PDF from the same BSE filing/IR page/
screener.in Documents tab for the same quarter.

## Annual reports

Same path, larger PDF (100-300 pages). Only extract the sections relevant to forward
guidance (Management Discussion & Analysis / Chairman's letter / outlook section) —
don't run the full report through `extract_theme_quotes.py`; grep the extracted text
for the MD&A section heading first and slice to that range before further processing,
to avoid burning tokens on financial statement boilerplate.

## Value chain positioning

The investor presentation is almost always the fastest source — many Indian
small/midcap decks include a "business model" or "value chain" slide showing
raw-material/component inputs on one side and end-customers/end-markets on the other,
with the company placed in the middle. If no such slide exists, piece it together
from: the concall's opening remarks (management often frames the business this way
when introducing it — "we supply generators to OEMs who in turn..."), the annual
report's industry-overview section, and any explicit tier language management uses
about itself (Tier 1/2/3 supplier, EMS/CDMO/ODM, etc.). Don't guess a multi-tier chain
from a bare one-line "what we make" description — if the sources only describe what
the company makes and not who buys it and what they do with it, say the downstream
chain wasn't fully disclosed rather than inferring it.

## Checking prior concalls for guidance status (for the outlook status pointers)

Building an accurate `[On Track]` vs. `[Pending]` pointer (see report_format.md's
Status Pointer rule) sometimes requires checking more than just the latest concall —
you need to know whether an item was *first* guided a few quarters ago and has been
reiterated, raised, or pushed out since. Two different situations:
- **First-ever run for a company (`no_state`)**: while processing the required source
  documents, also skim 1-2 concalls prior to the most recent one (if readily
  available from screener.in's Concalls list) specifically for guidance items that
  reappear in the latest call — this is what lets you log the full chain via
  `--supersedes-id` on the very first run instead of starting every item at
  `[Pending]` with no history.
- **Every subsequent refresh (`new_quarter`)**: you don't need to re-fetch old
  transcripts at all — `guidance_history.json` already has the prior entries from
  earlier runs. Just check whether anything in the newest concall revises, reaffirms,
  or completes an item already logged, and log the new entry with `--supersedes-id`
  pointing at it. This is the entire point of keeping the history durable: the
  evolution accumulates for free across refreshes without ever needing a bulk
  re-fetch.

## Total addressable market (TAM)

Look for an actual market-size figure, not a growth-rate: `WebSearch`/fetch the
investor presentation's "market opportunity" or "TAM" slide (very common — often
broken into segments the company addresses, e.g. separate TAM figures per product
line), and check concall Q&A for any analyst question about market size ("what's the
addressable market for X"). If management ties a specific capture target to the TAM
(e.g. "we aim to capture 50-60% of the X TAM by FY28"), that's also a status-pointer
item for the Long Term outlook (see report_format.md) — log it the same way as any
other tracked guidance item. Note the TAM figure's own date; if it's more than ~2
years old and hasn't been reiterated since, flag it as potentially dated rather than
presenting it as current.

## Marquee & niche customers

Investor presentations are the best single source — most Indian small/midcap decks
have a dedicated "Our Clients" / "Marquee Customers" slide, often segmented by
sector or geography. The annual report's business overview section and concall Q&A
("who are your top customers", "how concentrated is your revenue") are secondary
sources. Only report a customer name if a source document actually names it — do not
infer a relationship from a case study, a photo, or a LinkedIn mention. If the company
states top-10 or top-client revenue concentration (a number, not a name), capture that
figure too; it feeds both this section and, if material, Key Risks.

**Checking a named customer's own guidance**: once a customer is named, do one targeted
search per customer for its own public disclosures — `<customer name> annual report
capacity expansion`, `<customer name> investor call guidance`, or `<customer name>
expansion plans <year>` — looking specifically for anything that implies future demand
for the reporting company's products (a capacity doubling, a store-rollout target, a
new-plant announcement). This is quick to skip when there's nothing (many customers,
especially private ones, disclose nothing public) — in that case state plainly that no
independent guidance was found for that customer, rather than leaving the check out
entirely. Don't over-search; one or two queries per named customer is enough.

**Discovering additional customers via export-shipment data** (for an exporting
company — see "Export/import shipment data" below): this is a legitimate way to
surface customer names the company itself hasn't named in any filing, but it must be
labeled distinctly, not blended into the company-disclosed list — write it as "per
third-party export-shipment records (not disclosed by the company itself): shipments
recorded to <consignee>, <country>" rather than presenting it with the same confidence
as an investor-presentation logo slide. This doesn't relax the existing rule against
inferring a relationship from a photo or a bare LinkedIn mention — shipment records are
a specific, checkable data point (an actual bill of lading/shipping bill), not an
indirect inference, which is why they get a different treatment.

## Export/import shipment data, awards & social media — supplementary corroboration

These are secondary/discovery-tier sources (per the "Source trust hierarchy" above) —
useful for corroboration and for surfacing leads the primary filings don't mention, but
never a substitute for the primary source when one exists, and always labeled as coming
from a third-party record rather than company disclosure.

**Export/import shipment data** — sites like Volza, Seair Exim Solutions, ImportGenius,
Zauba Corp, or Panjiva aggregate customs shipping-bill records (shipper, consignee,
country, sometimes product description/quantity/value) for companies that export or
import physical goods. Two direct uses in this report:
- **Marquee & Niche Customers**: search `<company name> export shipments site:volza.com`
  (or similar) to find actual consignee names/countries — useful both to corroborate a
  customer the company already named and to surface one it didn't. Label per the rule
  above.
- **Raw material import dependency** (see Manufacturing Locations in
  `report_format.md`): if the annual report's indigenous-vs-imported note isn't
  accessible, shipment-data sites can show actual *inbound* shipments (raw material
  imports) with shipper/origin-country — a genuine, if partial, substitute when the
  primary disclosure can't be reached. Most of these sites gate full records behind a
  paywall/signup — a few free preview records are usually enough to establish whether
  imports exist and roughly which countries, even without the complete shipment log;
  say so if only a partial picture was available.

**Awards & recognition** — check the investor presentation for an "Awards & Accolades"
slide (common in Indian small/midcap decks, often listing the awarding body and year)
before doing a fresh search; if there's no such slide, a quick
`<company name> award <year>` search or a look at the company's own LinkedIn page /
news section can surface something not otherwise disclosed. An industry-body or
customer-awarded recognition (e.g. "Best Vendor" from a named marquee customer) is
worth a line in Marquee & Niche Customers or the Capex/Milestones/Certifications
Timeline (treat it as an achieved milestone) — a generic self-nominated award list
adds little and isn't worth chasing hard.

**LinkedIn / X (Twitter)** — the company's own official page/handle is a legitimate
primary-ish source for recent announcements not yet reflected in a filing (a new hire
in a leadership role, a plant inauguration, an order-win post, a product launch) —
cite it as "company LinkedIn/X post, <date>" like any other source. A *third-party*
post (an employee, a customer, an analyst) is discovery-only — a lead to verify, not
something to cite as fact on its own. **Run this check on every report** — it's quick
(one targeted search, `<company name> linkedin OR twitter <year>` or `<company name>
news <year>`, not a mandatory deep social-media audit), and skipping it entirely is
the actual failure mode to avoid, not over-searching it. **Only surface what's
genuinely noteworthy** — fold a real finding into the section it's actually relevant to
(a new order/customer into Marquee & Niche Customers or the outlook, a facility/award
into the Capex/Milestones Timeline, a leadership change into Promoter/Governance, a
controversy or negative development into Key Risks) rather than manufacturing a new
heading just because a search was run. If nothing noteworthy turns up, don't mention
that the check was made — this tier is opportunistic corroboration, not a section that
needs its own "nothing found" line the way litigation or TAM do.

## Legal & litigation

Check this on every report, not only when litigation is suspected — annual reports
disclose pending legal/tax matters as a matter of course, and this is one of the few
places a real, quantified contingent liability shows up outside of what management
chooses to volunteer on a concall.

- **Primary source: the annual report's Contingent Liabilities note** — virtually every
  Indian annual report has one (often numbered, e.g. "Note 34 — Contingent
  Liabilities"), itemizing pending tax disputes, customer/vendor litigation, and
  guarantees given. This is usually the single richest source and doesn't require a
  fresh search if the annual report was already fetched for other sections.
- **BSE/NSE Regulation 30 disclosures** — a material litigation development (a new
  suit, an adverse order, a settlement) is a disclosable event in its own right; search
  `<company name> litigation BSE announcement` or `<company name> court order NSE
  disclosure` for anything not yet reflected in the last annual report.
- **News search** — `<company name> lawsuit`, `<company name> court case`, `<company
  name> tribunal`, `<company name> high court` — useful for catching something recent
  enough that it hasn't yet appeared in a filed annual report.
- **Legal/judgment databases** — for case-level detail once a matter is known to
  exist (forum, order text, current stage), search `<company name> site:indiankanoon.org`
  or `<company name> <forum> site:casemine.com`; both index actual court orders/
  judgments and are usually more precise than a news summary for confirming what a
  ruling actually said and whether an appeal window is mentioned. Legal/business news
  sites focused on this beat (livelaw.in, barandbench.com) are also useful for
  ongoing-case updates that haven't reached a formal judgment yet. Treat a judgment
  database as the more authoritative source when it and a news article disagree on
  case status.
- **The "old case that can reopen" distinction is the point of this check**: a case
  dismissed or decided in the company's favor at a lower forum (tribunal, single judge)
  is frequently still open to appeal by the other side — commonly a tax or regulatory
  authority — within a defined limitation period (often 60-90 days for tribunal orders,
  longer for some tax matters). If a source describes a case as "dismissed" or "decided
  in the company's favor," check whether it also mentions an appeal window or a pending
  appeal at a higher forum before treating it as closed. Log it with
  `scripts/litigation_tracker.py add-case --status dismissed_appealable` rather than
  `closed_final` whenever that ambiguity exists — the tracker's `report` command flags
  this status explicitly so it isn't lost on a later refresh.
- Also check for litigation involving the **promoters personally** (not just the
  company) if named in a source — e.g. a promoter-level dispute disclosed in the annual
  report's related-party section or in a rating agency's rationale.

## Capex, milestones & certifications

Sources, roughly in order of reliability:
1. **Investor presentation** — almost always has a dedicated capex/expansion slide
   with a timeline (past commissioning dates, planned future dates/horizons, capex
   amounts).
2. **Concall Q&A** — management often gives more specific timing color here than the
   deck ("we expect this line to go live by Q3").
3. **BSE/NSE announcements** — plant commissioning, capacity expansion completion, and
   certifications (ISO, AS9100/aerospace, USFDA, customer-specific vendor approvals)
   are frequently disclosed as standalone Regulation 30 announcements the moment they
   happen — search `<company name> certification BSE announcement` or `<company name>
   commissioned capacity BSE`.
4. **Annual report MD&A** — for a fuller history of what's already been achieved.
Build the timeline table from whichever combination of these actually has dates; don't
force a date that wasn't given — use the horizon management stated instead (e.g. "H2
FY27") for anything still planned.

## CDMO pipeline (only if the company is a CDMO)

If the company describes itself as a CDMO/CRAMS (contract development and
manufacturing organization) — common in pharma, specialty chemicals, and API
businesses — the investor presentation almost always has a pipeline slide with a
Phase 1/2/3/Commercial funnel chart or table. The concall Q&A sometimes gives updated
counts even when the deck is stale (e.g. "we now have 2 more molecules that entered
Phase 3 since the last presentation"). Molecule/sponsor names are essentially never
disclosed by design (client confidentiality is core to the CDMO business model) — do
not attempt to identify them via outside search; report only what the company itself
discloses (counts, and therapeutic-area splits if given).

## Financial performance summary (YoY revenue, margins, PBT, PAT)

This is already sitting in the screener.in fetch done in step 1 above — the quarterly
and annual results tables give revenue, PBT, and PAT directly for at least the last
5 years (and gross margin or EBITDA margin, whichever the company discloses). No
separate fetch needed; just don't discard these columns when you scope the rest of the
report to the 6-month lookback window (see "Filtering to a 6-month window" below) —
this section is explicitly a multi-year trend, not a recent-quarter snapshot, and is
exempt from that lookback default.

## Segment-wise performance, order book composition & exports vs. domestic split

The annual report's Ind AS 108 segment note (usually titled "Segment Reporting" or
"Operating Segments" in the notes to accounts) is the most formal source for a
product-line/end-market/geography breakdown; screener.in sometimes mirrors a
simplified version of this on the company page directly. The investor presentation and
concall Q&A are the more common source for an **exports vs. domestic** split
specifically — many Indian small/midcaps state this informally (e.g. "exports were
18% of revenue this quarter") without a formal segment note behind it; search the
transcript for "export" if `extract_theme_quotes.py`'s candidate buckets didn't
surface it, the same way as the capacity-utilization "utili" search above. The same
export/domestic distinction is also worth checking on the **order book** specifically
(not just revenue) — an investor presentation's order-book slide sometimes breaks
composition out by export vs. domestic contracts separately from the revenue split, and
the two shouldn't be assumed to match just because a revenue-side figure was found.

## Capacity utilization inputs

Management usually states current utilization % directly on the concall in response to
a direct analyst question ("what's your current capacity utilization") — search the
transcript text for "utili" if `extract_theme_quotes.py`'s candidate buckets didn't
surface it (utilization commentary is often backward-looking, not forward-looking, so
the forward-looking-keyword filter can miss it). If a direct % wasn't given, the
investor presentation's operations/manufacturing slide sometimes states installed
capacity and actual production/sales volume separately, from which
`scripts/capacity_utilization.py` can derive utilization (Mode B).

**Post-capex revenue potential** — don't do a separate fetch for this: it's almost
always the same figure already captured in the Capex/Milestones timeline or a Medium/
Long Term outlook bullet (e.g. "capacity sized for INR3,000-3,200cr sales by FY28").
Reuse that figure via `--post-capex-max-revenue-cr` rather than re-deriving or
re-searching for a number management already gave.

## BSE / NSE filings (fallback / verification)

- BSE: `https://www.bseindia.com/stock-share-price/<company>/<code>/corp-announcements/`
- NSE: `https://www.nseindia.com/companies-listing/corporate-filings-announcements`

Use this whenever screener.in is giving trouble, not only for a missing filing —
covers two distinct failure modes seen in practice:

1. **A specific filing is missing** — screener.in's Documents tab hasn't indexed a very
   recent announcement yet. Go straight to the exchange's own announcements page.
2. **screener.in's numeric widgets won't populate** — the price ticker, market cap,
   quarterly/annual P&L, or balance sheet tables come back masked (`x`/`xx`/`xxx`) or
   blank in both `WebFetch` and Claude Browser, even after a wait. This happens
   occasionally (a client-side widget failing to load real data, sometimes
   bot-detection-related) and is not worth repeatedly retrying. When it does:
   - **BSE/NSE directly** for the raw financial results filing (quarterly/annual
     results are filed as a Regulation 33/30 disclosure, often with the full P&L as a
     PDF or structured table) — this is a primary source anyway, a step up from
     screener.in's aggregation, not just a workaround.
   - **The concall transcript and investor presentation** (already being fetched for
     the outlook sections) usually restate the full P&L, balance sheet, and segment
     splits directly — check there first before making a special trip to BSE/NSE, since
     it's a document you're fetching regardless and often has more detail (segment/
     geography splits, multi-year history) than screener.in shows anyway.
   - **A secondary quote aggregator** (Tickertape, Trendlyne, etc.) for just the
     live price/market cap/52-week range if that's the only piece screener.in won't
     give you — no need to solve the whole screener.in problem just to get one number.
   Don't burn more than one retry on screener.in itself before falling back — the
   fallback sources are usually faster than debugging why a widget won't load.

Same web_fetch → Chrome fallback pattern applies to BSE/NSE directly; NSE in particular
is heavily JS-rendered and often needs Chrome.

## Forward PE inputs

From screener.in's summary block: current market price, shares outstanding (Equity
Capital ÷ Face Value, both shown on the page), and trailing PAT/revenue (for a
fallback margin assumption if management didn't guide one). Revenue guidance itself
comes from the concall, not screener.in. If the user gives their own price, use that
instead and label it "user-supplied" per `reference/report_format.md`.

**Median PE**: this is a computed historical statistic, not something management
discloses, so it comes from a secondary aggregator rather than a filing — check
screener.in first (occasionally shown directly), then Trendlyne, Tijori Finance, or
MoneyWorks4Me (`<company name> median PE 5 year`). These sources don't always agree
exactly (different lookback windows) — if two sources diverge by more than a couple of
points, report the range and cite both rather than picking one arbitrarily. If no
source publishes it, say so rather than computing your own median from a partial price
series.

## Raw material import dependency

A standard Companies Act/Ind AS disclosure, but one easy to miss because it isn't in
the concall or investor presentation — it lives in the **annual report's Notes to
Accounts**, usually under a heading like "Value of raw materials, components and spare
parts consumed" or "Additional Information pursuant to Schedule III," broken into
indigenous vs. imported ₹ value and %. Fetch the latest available annual report (per
"Annual reports" below) and search its extracted text for "imported" / "indigenous" /
"raw material consumed." If the annual report genuinely isn't accessible this run,
fall back to concall Q&A about raw-material sourcing or supply-chain risk (management
sometimes volunteers directional color — e.g. "we import our nickel content" — without
a hard %) and report that as qualitative color, explicitly labeled as such rather than
presented as a quantified figure. Don't substitute generic industry knowledge (e.g.
"India imports most of its nickel") for a company-specific disclosure — if the
company's own number isn't found, say so.

## Manufacturing locations

The annual report's Property, Plant & Equipment note or "our facilities"/"corporate
information" section is the most reliable source for a full list of plant locations,
ownership (owned/leased), and area; the investor presentation's manufacturing-footprint
slide and concall Q&A about plant locations or expansion sites are secondary sources
that are often faster to fetch but less complete than the annual report.

## Industry tailwinds / headwinds

Don't infer these from the single company's concall alone — that's already covered
in the Near/Medium/Long Term sections. Look outward:
- `WebSearch` for `<industry/sector> India outlook <year>`, `<industry> order inflow
  trend India`, or the same query for 1-2 direct peers/competitors named in the
  concall or on screener.in's Peers tab.
- Sector-level commentary from industry bodies (e.g. CII, sector-specific
  associations), rating agency sector notes (CRISIL/ICRA/CARE publish free sector
  outlook notes), or a peer's own concall commentary on the same demand drivers.
- Keep this section tight — 2-4 bullets, not a literature review.

## Peer comparison, entry barriers & product criticality

Start from screener.in's own "Peers" tab on the company page — it lists 5-10 comparable
listed companies by default, already scoped to the same industry classification. Narrow
to the 3-5 the company's own concall names as competitors, if it names any (management
sometimes does when asked "how do you differentiate from X/Y" in Q&A) — those are more
relevant than an arbitrary screener.in peer-set cutoff.

- **IP / technology moat, per peer**: `WebSearch` each peer's own investor presentation
  (`<peer name> investor presentation site:bseindia.com` or a direct search for the
  peer's IR page) for a "competitive strengths" or "why us" slide — this is where
  patents, proprietary processes, or in-house R&D claims usually surface. If a peer
  discloses nothing on this, say so rather than assuming parity.
- **Niche/marquee customers, per peer**: same investor presentation, "Our Clients"
  slide, cross-checked the same way as the reporting company's own customers (name a
  customer only if a source actually names it).
- **Certifications, per peer**: investor presentation and, if relevant, a BSE/NSE
  announcement search (`<peer name> certification BSE announcement`) the same way as
  the reporting company's own Capex/Milestones sourcing above.
- **Entry barriers**: don't guess these generically from the industry name — check the
  reporting company's own concall Q&A for a direct analyst question along the lines of
  "what stops a new player from entering this space," which management frequently
  answers with specifics (capex quantum, qualification timeline, customer approval
  cycle). The annual report's "Industry Overview" or "Competitive Strengths" section in
  the Management Discussion & Analysis is the other common source. A peer's own framing
  of the same barriers (from its investor presentation) can corroborate or add color.
- **Product criticality**: look for management's own language about what happens if the
  product fails or is substituted (e.g. "a single failed component can ground an
  aircraft," "this is a life-critical device," "switching suppliers requires
  re-qualification with the end customer") — this is usually volunteered in the same
  concall/investor-presentation context as the entry-barriers discussion, not a separate
  fetch. If nothing this specific was said, state the product's role factually (e.g.
  "used in X system") without asserting a criticality level the sources don't support.
- Keep this proportionate — one or two searches per peer is enough, the same discipline
  as the "customer's own guidance" check above; this section doesn't need a full report
  on each peer, just enough to fill the comparison table's cells.

## Technical snapshot

Get a pre-computed technicals summary rather than fetching raw daily OHLC data and
calculating indicators yourself — no reliable free historical-price API is reachable
from this sandbox, and hand-rolling RSI/moving averages from scraped data is a poor
use of tokens for what's meant to be a one-line snapshot.
- `WebSearch`/`mcp__workspace__web_fetch` a technicals page for the ticker — Trendlyne,
  MoneyControl's technicals tab, or Screener AI's technical widgets often list
  moving averages, RSI, and support/resistance directly.
- If the page is JS-rendered and web_fetch returns a shell, escalate to Claude in
  Chrome per the platform's own escalation rule.
- Always record the as-of date next to the numbers — this section goes stale fast.

## Credit rating agencies (CRISIL / ICRA / CARE / India Ratings / Acuite / Brickwork)

Check this for every report, not just when the company has visibly raised debt — a
rating rationale is one of the few genuinely independent, professionally-underwritten
views in the whole pipeline (unlike the concall, which is management's own words, or
screener.in, which aggregates public filings without an opinion on them).

- **Which agencies cover the company**: not every listed company is rated by all four
  major agencies — many SME-listed companies use only one, sometimes CRISIL, ICRA, CARE,
  India Ratings & Research, or (common for smaller issuers) Acuite Ratings or Brickwork
  Ratings. Search `<company name> CRISIL rating rationale`, `<company name> ICRA rating
  rationale`, `<company name> CARE rating rationale`, `<company name> India Ratings
  rationale`, `<company name> Acuite rating rationale` — don't assume absence of a
  result means "unrated"; it may just mean a different agency covers them. If genuinely
  no rating rationale is found anywhere, say so explicitly rather than silently omitting
  the section.
- **Where rationales live**: each agency publishes free rating-rationale documents
  (PDF or webpage) on its own site whenever a rating is assigned, reviewed, or revised;
  for listed companies these are also frequently mirrored on BSE/NSE as a disclosure
  under SEBI LODR. `WebSearch`/`mcp__workspace__web_fetch` the agency's own site first;
  fall back to the BSE/NSE-mirrored copy if the agency's own page is paywalled or
  JS-gated.
- **What to extract from the rationale**: current rating and outlook (e.g. "CRISIL
  A-/Stable"), the instrument it applies to (bank facilities, NCD, commercial paper —
  a company can carry different ratings for different instruments), the date of the
  rationale, and 1-2 lines of the agency's own reasoning — leverage/coverage trend,
  liquidity assessment (strong/adequate/stretched/poor), and any promoter-support,
  personal-guarantee, or related-party-transaction commentary the agency called out.
- **Log it**: use `scripts/rating_tracker.py add-rating` once per rating action found
  (don't re-log an unchanged rating on every regeneration — it's a durable record like
  fund raises, not a per-quarter one like guidance). State the `--action` yourself
  (`first_time`/`reaffirmed`/`upgrade`/`downgrade`/`outlook_revised_positive`/
  `outlook_revised_negative`/`withdrawn`) based on what the rationale itself says
  relative to the company's prior rating — don't try to infer it purely from comparing
  rating-scale notches.
- **Treat a downgrade or negative/watch-negative outlook as a first-class risk signal**:
  run `scripts/rating_tracker.py <slug> report` and reproduce its flag verbatim if the
  currently-in-force rating on any instrument is a downgrade or carries a negative/
  watch-negative outlook — this belongs in both the Promoter/Governance section and, if
  material, the Key Risks section, not softened into a passing mention.
- **Rating rationales are point-in-time**, usually issued once or twice a year (annual
  surveillance, or on a trigger event like a fund raise) — state the rationale's own
  date next to the rating, the same staleness discipline as the Technical Snapshot.

## Promoter / governance track record

Three separate things to check:
1. **Guidance reliability** — use `scripts/guidance_tracker.py` against the cached
   `guidance_history.json` for the company (built up over successive report runs from
   this skill; see SKILL.md). This needs no new fetching once a couple of quarters are
   logged — it's a local comparison.
2. **Other governance signals** — pull directly from screener.in's Shareholding
   Pattern (promoter holding trend, pledge % if shown) and Documents tab (auditor
   qualifications or delayed filings usually show up as flagged BSE/NSE
   announcements). A falling promoter holding % is not automatically a red flag
   (could be a planned OFS/QIP) — state the fact and, if the concall or an
   announcement explains it, cite that; don't speculate.

   **For the visual PDF's shareholding-pattern chart** (`charts.shareholding_chart()` —
   see report_format.md), screener.in's Shareholding Pattern table already returns the
   full multi-quarter history (Promoter/FII/DII/Public %, typically 8-12 quarters back)
   in the one page fetch already done — no separate tracking script or extra fetch
   needed, unlike guidance/fund-raises/ratings/litigation, which persist across runs in
   their own JSON files because screener.in itself only shows the current state, not a
   log of past report runs. Just read the last several columns of that one table.
3. **Promoter fund raises (preferential equity, warrants, debt)** — use
   `scripts/fundraise_tracker.py` against the cached `fundraise_history.json` for the
   company. Sourcing:
   - **Preferential equity / warrants**: BSE/NSE corporate announcements filtered to
     "Preferential Issue" / "Allotment pursuant to Preferential Issue" — search
     `<company name> preferential issue warrants BSE announcement` or check
     screener.in's Documents/Announcements tab. The allotment notice gives date,
     instrument count, issue price, and allottee names — cross-check allottee names
     against the promoter/promoter-group names in the Shareholding Pattern to classify
     `--allottee promoter` vs `public`/`institution` correctly. **Capture the actual
     allottee names**, not just the category, whenever the notice lists them —
     recognizable HNIs, FPIs, or mutual funds among the allottees are a real signal
     worth naming (pass them via `fundraise_tracker.py add-raise --investors`). A quick
     `<company name> preferential allotment investors` news search often surfaces a
     press writeup naming the allottees even faster than parsing the notice's annexure.
   - **Warrant status (conversion or lapse)**: warrants allotted under SEBI ICDR rules
     have up to 18 months to convert. On every regeneration, check whether any
     `pending` warrant in `fundraise_history.json` has since converted (a follow-up
     BSE allotment announcement / shareholding pattern increase) or lapsed (no
     conversion announcement within the window, or an explicit forfeiture disclosure)
     and call `fundraise_tracker.py update-status` accordingly before running `report`.
   - **NCDs / term loans / promoter loans**: BSE/NSE announcements ("Issue of
     Non-Convertible Debentures") and, especially, the same credit-rating rationale
     documents covered in "Credit rating agencies" above — these typically state the
     amount, tenure, coupon, purpose, and whether the promoter has furnished a personal
     guarantee or pledged shares as security. Search `<company name> NCD allotment BSE`.
     Log the debt instrument itself in `fundraise_history.json` via `fundraise_tracker.py`
     and the agency's opinion on it separately in `rating_history.json` via
     `rating_tracker.py` — they're two different facts (what was raised vs. what an
     independent agency thinks of the company's ability to service it).
   - Log every raise found via `fundraise_tracker.py add-raise` once, the first time
     it's seen (don't re-log it on every regeneration — it's a durable record, not a
     per-quarter one like guidance). Then run `fundraise_tracker.py <slug> report`
     (optionally with `--cmp <price>` to show issue price as a premium/discount to the
     current price) and reproduce its output/flags in the Promoter Fund Raises
     sub-section per `reference/report_format.md`.

## YouTube (supplementary, optional — not a primary source)

Some concalls are only available as a recording, not a written transcript (screener.in's
Concalls section links these as "REC" against the relevant quarter, alongside the
Transcript/PPT links). YouTube is also occasionally useful for a management interview
(CNBC/ET Now/ETMarkets) that adds outlook color beyond the concall — treat that as
industry/company color, not as the primary near/medium/long-term source.

**What actually works here, tested in this sandbox:**
- `mcp__workspace__web_fetch` on a `youtube.com/watch?v=...` URL returns nothing usable
  — YouTube is fully JS-rendered, so a plain fetch gets an empty shell, not the video
  transcript. Don't rely on it.
- Reading the actual transcript requires Claude in Chrome (`navigate` to the video,
  open the "Show transcript" panel via `find`/`computer`, then `get_page_text`). This
  is a real path but depends on the Chrome extension being installed and connected —
  it was **not connected** when this was last tested. If it's unavailable when you need
  it, say so explicitly and skip the YouTube source rather than guessing at content
  from the video title/description alone.
- If Chrome is connected: prefer the exact YouTube link screener.in already ties to
  the quarter you need (the "REC" link) over an open-ended YouTube search — this
  guarantees you're watching the right, already-dated recording instead of having to
  filter search results by upload date yourself (see the "Filtering to a 6-month
  window" section below for why this matters).
- If no transcript panel exists for a given video (auto-captions off), don't try to
  transcribe audio — there's no audio-transcription tool in this environment. Skip it
  and note the gap rather than fabricating quotes.

## Filtering to a 6-month window — how it actually works

There's no server-side "give me the last 6 months only" parameter on either
screener.in or YouTube/WebSearch. The 6-month lookback (the framework's fixed default
— see SKILL.md) is enforced by what gets *used and cached*, not by what gets fetched:

- **screener.in**: one `web_fetch` always returns the entire page — the full
  multi-year quarterly table, full P&L/balance sheet history, full shareholding
  history back to 2015-17, and the full concalls list back to whenever the company
  started disclosing them. There is no URL parameter or lighter endpoint that returns
  only recent data. The 6-month filter happens after the fetch: read only the last 1-2
  columns of the quarterly table, only the top 1-2 entries of the Concalls list, and
  only the most recent shareholding-pattern column. Don't cache or carry forward the
  older columns/entries into `research_cache/` — leave them in the one-time fetch and
  discard them once you've pulled what you need. This means the fetch itself isn't
  smaller, but the tokens spent reasoning over the result, and what persists in the
  cache, are scoped to 6 months.
- **YouTube / WebSearch**: `WebSearch`'s schema has no date-range parameter, so you
  can't ask it for "concalls from the last 6 months" directly. Two ways to stay
  scoped: (1) prefer the quarter-linked link from screener.in as above, which is
  already dated by construction; (2) if doing a genuinely open search (e.g. industry
  commentary, not a specific concall), phrase the query with the specific
  month/quarter you want (e.g. "TD Power Systems management interview June 2026") and
  then check the actual publish date shown in the search result or on the fetched
  page before using it — discard anything you can't confirm falls inside the window.

## Regenerating for a new quarter — what to actually (re)fetch

This is the single biggest token-saving lever in the whole pipeline, and it's easy to
under-use by "just re-running everything to be safe." When `check_freshness.py` returns
`new_quarter`, fetch **only**:

- The new quarter's **concall transcript** and **investor presentation** (the two
  documents that actually changed).
- **screener.in's last 1-2 columns** of the quarterly/annual results table and the most
  recent shareholding-pattern column — not the full history, per "Filtering to a
  6-month window" above.
- Any **new** BSE/NSE announcement, rating action, or litigation development since the
  last run — check dates against what's already logged in `guidance_history.json`/
  `fundraise_history.json`/`rating_history.json`/`litigation_history.json` and only
  fetch/log what's actually new, not the full history again.

**Do not re-fetch or re-derive** anything that doesn't change quarter to quarter and is
already sitting in `research_cache/<company_slug>/report.md` from the last run:
manufacturing locations, certifications, TAM figures, entry barriers, product
criticality, peer identities (their financials may need a quick refresh if quoted, but
the peer set itself rarely changes), the value chain description, or older annual
reports already processed. Carry these sections forward from the cached `report.md`
unmodified unless the new concall/presentation specifically mentions a change (a new
certification obtained, a new plant, a new peer entering the conversation).

**What does need a fresh look every quarter**: the Near/Medium/Long Term outlook
(supersedes the old bullets, per SKILL.md), Financial Performance Summary (add the new
quarter/year as a row, don't rebuild the table), Order Book, Capacity Utilization,
the Capex/Milestones timeline (append new rows only), Valuation (new price/guidance),
Technical Snapshot (always stale, always refresh), and the Promoter/Governance
sub-sections — but even those only get a new *entry* appended if something actually
happened (a new rating action, a new fund raise, a new case) rather than a full rebuild
of an unchanged history.

## User-uploaded documents

If the user has already uploaded the concall transcript / investor PPT / annual report
(they said they'd share templates and source documents directly), always prefer those
over fetching — check the uploads/workspace folder first before doing any web research.
