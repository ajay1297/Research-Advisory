# Source Playbook — per-report-topic sourcing for Step 2

**Read only by `reference/step2_synthesize.md`.** Where and how to fetch each
source (tool, URL pattern, fallback chain, uploads) lives in
`reference/data_sources.md` — read it once per report. This file tells you what to
pull for each part of the report; each section below names its primary source and
points back to `data_sources.md` for the mechanics of getting it. Document-set/
depth/cadence policy (how far back, what's standard, what changes on a refresh)
lives in `reference/sourcing_depth.md`, not here.

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
entirely. Don't over-search; one or two queries per named customer is enough for a
customer that turns out to be private/unlisted.

**If a named marquee customer is itself a publicly listed company — Indian or
foreign, any exchange — go further than a one-off search: analyze its last 4
quarterly concalls/earnings calls.** A one-off search only catches whatever a news
aggregator already wrote up; the customer's own quarterly earnings calls are where
they actually discuss capacity plans, supplier relationships, and demand outlook in
their own words — the same kind of primary-source evidence this pipeline insists on
for the reporting company itself, just applied one hop downstream. The kind of
relationship this applies to: e.g. Rossell Techsys's customer Lam Research, which is
confirmed listed on NASDAQ (LRCX) — a genuinely material, named marquee customer that
itself files quarterly results and holds earnings calls, not a niche one-off buyer.
**Verify listed status before assuming it** — don't assert a customer is listed on a
given exchange without checking; a named customer described as a large multinational
is not automatically public (e.g. a customer that turns out to be a private-equity-owned
subsidiary has no listing at all, and no amount of searching will find one — confirm
via step 1 below rather than guessing an exchange).

1. **Confirm the customer is actually listed, fast: try Google Finance first.**
   `https://www.google.com/finance/quote/<TICKER>:<EXCHANGE>` (exchange codes like
   `NASDAQ`, `NYSE`, `LON`, `XETR`, `NSE`, `BSE`, etc.) works as a **universal,
   cross-exchange company lookup** — verified in this sandbox to render real content
   (not JS-blocked) via Claude in Chrome, including live price, an Earnings tab with
   **actual embedded call transcripts** and EPS/revenue actuals-vs-estimates by
   quarter, going back several quarters. If you don't already know the ticker/exchange,
   a plain `WebSearch` for `<customer name> stock ticker` usually surfaces it quickly.
   A "Page Not Found" result on a reasonable ticker guess is itself a useful signal —
   not proof of being private, but a prompt to verify with one more search before
   concluding the customer isn't listed at all. This single lookup often replaces both
   the "is it listed" check and the transcript fetch in one step when it works.

   **If Google Finance comes back "Page Not Found" on a reasonable ticker guess,
   don't stop there — that alone isn't proof of being private.** Fall back in this
   order before concluding not-listed:
   1. `WebSearch` for `<customer name> stock ticker exchange` — you may have simply
      guessed the wrong ticker or exchange code the first time; retry Google Finance
      with whatever ticker/exchange this search surfaces.
   2. A general financial-data site check — Yahoo Finance
      (`finance.yahoo.com/quote/<TICKER>`) or the exchange's own listing search (e.g.
      the LSE's or NASDAQ's own company-lookup page) as a second independent lookup,
      since Google Finance occasionally lacks coverage for a smaller-cap or
      less-common-exchange listing that another aggregator does carry.
   3. `WebSearch` for `<customer name> investor relations` or `<customer name>
      annual report` — a company with genuine IR materials/annual reports is
      listed somewhere even if neither lookup above found the right ticker; a
      company with nothing but a corporate "About Us" page and no investor-facing
      material at all is a strong (though not certain) signal it's genuinely
      private.
   Only after this fallback chain comes up empty should you conclude "not listed" —
   and even then, state which of the three fallback steps you actually tried, per the
   "write down why" rule below, rather than a bare "not found."

   **When the answer comes back "not listed," write down *why*, not just "no
   guidance found."** These are different findings and must not be blended into the
   same vague sentence: (a) **confirmed never public** — no listing history found
   anywhere; (b) **confirmed formerly listed, now private** — state the exchange it
   was delisted from, the year, and the acquirer if found (e.g. "was listed on the
   London Stock Exchange/FTSE 250 until Fidelity Investments acquired it in August
   2015; privately held since, no current earnings calls exist to check"); (c)
   **genuinely inconclusive** — a real search was made and didn't resolve either way,
   say that plainly rather than implying (a) or (b). Writing "no independently
   disclosed guidance was found for this customer" when the real situation is (b) —
   a company that used to be listed and has a clear, findable delisting history —
   reads as an inconclusive search when it's actually a confirmed, citable fact; a
   reader can't tell the difference between "I checked and there's nothing to find"
   and "I didn't check thoroughly enough to find it." This is the same discipline as
   the "Never drop anything silently" rule in `reference/rules_and_validation.md`, applied specifically to
   customer-listing checks since it's a recurring place the distinction gets blurred.

   This step is what separates "worth 4 quarters of analysis" from "quick guidance
   search is enough" above. Most named customers are private/subsidiaries/unlisted;
   only listed ones get this deeper treatment.
2. **This is not India-specific — the pipeline overall is, but a foreign customer's
   own disclosures are fair game regardless of exchange** (US, UK, EU, or elsewhere).
   If Google Finance's Earnings tab doesn't have the transcript for a given quarter,
   fall back in this order:
   - The customer's own **investor relations page** (search `<customer name> investor
     relations earnings call transcript` or `<customer name> quarterly results
     presentation`) — almost every listed company globally publishes its own earnings
     call transcripts, press releases, or webcast replays there; this is the most
     reliable path regardless of exchange, since it doesn't depend on a
     regional-specific aggregator existing.
   - For US-listed customers specifically: SEC EDGAR (8-K filings often attach the
     earnings press release/prepared remarks) as a secondary check, and Motley
     Fool/Seeking Alpha as free-tier transcript aggregators if the IR page doesn't
     have the transcript itself.
   - For UK/EU-listed customers: Google Finance (step 1 above) already covers these
     exchanges via the same URL pattern (e.g. `:LON` for London, `:XETR` for
     Frankfurt) — try it there first before falling back to the customer's own IR
     page. Beyond those two, treat any other regional aggregator as unverified until
     you've confirmed it actually returns usable content.
   - **Only one retry per source, same as any other stuck-source rule** — if a
     customer's transcripts genuinely aren't fetchable (paywalled investor portal, no
     public transcript for that market), say so explicitly rather than silently
     skipping the check or presenting an incomplete picture as complete.
3. **Pull the last 4 quarters** (not just the latest), extract each via
   `pdf_to_text.py`, save under `~/.report-generator/sources/<company_slug>/customers/<customer_slug>/`
   (this is bulky raw material, same as the reporting company's own concalls — it
   belongs in `sources/`, not `research_cache/`, per the directory split above), and
   run `extract_theme_quotes.py` or `semantic_search.py` on each looking specifically
   for language relevant to *the reporting company's* business — capacity expansion,
   supplier/sourcing commentary, capex plans, new-plant or JV activity, order growth —
   not for building out the customer's own investment thesis, which is out of scope
   here.
4. **Write the finding as 2-4 bullets under that customer's entry in Marquee & Niche
   Customers**, each one clearly attributed to the customer's own call, not the
   reporting company's: `"<Customer> reiterated on its Q<N> FY<year> earnings call
   that it plans to <capacity/demand-relevant claim>, which corroborates <reporting
   company>'s <specific claim/section>."` Cite the quarter and date for each of the 4
   calls checked, even the ones that turned up nothing relevant — the point is showing
   the check was done across 4 quarters, not just cherry-picking the one call that
   happened to be favorable.

**Awards & recognition** — check the investor presentation for an "Awards & Accolades"
slide (common in Indian small/midcap decks, often listing the awarding body and year)
before doing a fresh search; if there's no such slide, a quick
`<company name> award <year>` search or a look at the company's own LinkedIn page /
news section can surface something not otherwise disclosed. An industry-body or
customer-awarded recognition (e.g. "Best Vendor" from a named marquee customer) is
worth a line in Marquee & Niche Customers or the Capex/Milestones/Certifications
Timeline (treat it as an achieved milestone) — a generic self-nominated award list
adds little and isn't worth chasing hard.

**LinkedIn / X (Twitter)** — access mechanics (which URL types work, escalation
pattern) are in `reference/data_sources.md`.

**Lookback window: 3 months.** Only surface posts dated within the last 3 months —
older posts are either already reflected in a subsequent filing/concall or are stale
by the time the report is read. This is tighter than the 6-month window used for
ratings/BSE-NSE announcement rechecks, deliberately: social posts are a fast,
low-friction discovery channel, not a formal disclosure record, so a shorter window
keeps it to genuinely fresh, still-actionable news rather than pulling in things the
report's other sections would already have caught.

**How to use either**: the company's own official account/page is a legitimate
primary-ish source for recent announcements not yet reflected in a filing (a new hire
in a leadership role, a plant inauguration, an order-win or project-completion post, a
product launch) — cite it as "company LinkedIn/X post, <date>" like any other source.
A *third-party* post (an employee, a customer, an analyst) is discovery-only — a lead
to verify, not something to cite as fact on its own. **Run this check on every
report** — it's quick (navigate directly to `x.com/<handle>` if you know it, one
targeted `WebSearch` for `<company name> linkedin OR twitter <year>` if you don't),
and skipping it entirely is the actual failure mode to avoid, not over-searching it.
**Only surface what's genuinely noteworthy** — fold a real finding into the section
it's actually relevant to (a new order/customer/project into Marquee & Niche Customers
or the outlook, a facility/award into the Capex/Milestones Timeline, a leadership
change into Promoter/Governance, a controversy or negative development into Key
Risks) rather than manufacturing a new heading just because a search was run. If
nothing noteworthy turns up, don't mention that the check was made — this tier is
opportunistic corroboration, not a section that needs its own "nothing found" line the
way litigation or TAM do.

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
report to the standard 18-month/6-quarter lookback window (see
`reference/sourcing_depth.md`'s "Filtering to an 18-month window" section) — this
section is explicitly a multi-year trend, not a
recent-quarter snapshot, and is exempt from that lookback default.

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

**Find the industry's own physical capacity unit, not just a %** — every industry
reports capacity differently, and the physical unit is the primary figure a reader
needs, not a derived percentage alone: fiber-km/annum (optical fiber), MT/annum
(metals, chemicals, cement), MW/MWp (power, renewables), number of units/annum
(vehicles, cylinders, kegs, looms), bed-days or occupancy % (healthcare), etc. Look for
this in the same operations/manufacturing slide or concall answer that gives the
utilization % — management usually states both together ("installed capacity of 50
million fiber-km, we did about 39 million this year"). If the company breaks capacity
out by product sub-type or grade (e.g. standard vs. specialty fiber, flat vs. long
steel products), capture that split too rather than only the blended aggregate — the
specialty/high-margin sub-type's utilization is often more decision-relevant than the
aggregate.

**Check whether the capacity is a shared, multi-purpose pool** — ask specifically (via
a `grep`/targeted read of the concall, or a direct look at the investor presentation's
operations slide) whether the same production line/plant/asset can be swung across
multiple product variants, or whether each variant has dedicated capacity. Management
sometimes states this directly when explaining a product-mix shift ("we can allocate
the same line between standard and hollow-core fiber depending on order mix"). If nothing
explicit is found either way, don't assume dedicated capacity by default — say the
sources reviewed didn't clarify whether the capacity pool is shared or dedicated, rather
than presenting a blended utilization % as if it necessarily described one dedicated
line.

**Post-capex revenue potential** — don't do a separate fetch for this: it's almost
always the same figure already captured in the Capex/Milestones timeline or a Medium/
Long Term outlook bullet (e.g. "capacity sized for INR3,000-3,200cr sales by FY28").
Reuse that figure via `--post-capex-max-revenue-cr` rather than re-deriving or
re-searching for a number management already gave.

## Forward PE inputs

From screener.in's summary block: current market price, shares outstanding (Equity
Capital ÷ Face Value, both shown on the page), and trailing PAT/revenue (for a
fallback margin assumption if management didn't guide one). Revenue guidance itself
comes from the concall, not screener.in. If the user gives their own price, use that
instead and label it "user-supplied" per `reference/report_sections.md`'s Forward PE section.

**Median PE** comes from a secondary aggregator, not a filing — sourcing mechanics
and the divergent-sources rule are in `reference/data_sources.md`.

## Raw material sourcing — domestic vs. imported, country-wise

A standard Companies Act/Ind AS disclosure, but one easy to miss because it isn't in
the concall or investor presentation — it lives in the **annual report's Notes to
Accounts**, usually under a heading like "Value of raw materials, components and spare
parts consumed" or "Additional Information pursuant to Schedule III," broken into
indigenous vs. imported ₹ value and %. Fetch the latest available annual report (per
`reference/sourcing_depth.md`'s "Annual reports — processing" section) and search its
extracted text for "imported" / "indigenous" /
"raw material consumed."

**Don't stop at the aggregate %** — if any portion is imported, look specifically for a
country-of-origin breakdown, which sometimes sits in the same note or nearby in the
MD&A (e.g. "62% imported: China 40%, South Korea 15%, others 7%"). A single blended
"imported" % without a country split hides a real difference in exposure — a
single-country dependency is a materially different geopolitical/FX risk than a
diversified import basket at the same aggregate %. If the annual report gives the
aggregate % but not the country split, say so explicitly rather than treating the
aggregate as the complete picture, and try one of the following before giving up:

- **Annual report MD&A / risk-factors section** — sometimes names key sourcing
  countries qualitatively even without a hard % (e.g. "primarily sourced from China and
  South Korea").
- **Concall Q&A about raw-material sourcing or supply-chain risk** — management
  sometimes volunteers directional color (e.g. "we import our nickel content from
  Indonesia") without a hard %; report this as qualitative color, explicitly labeled as
  such rather than presented as a quantified figure.
Don't substitute generic industry knowledge (e.g. "India imports most of its nickel")
for a company-specific disclosure — if the company's own number or country breakdown
isn't found anywhere reviewed, say so plainly rather than guessing.

**Important: this specific breakdown is no longer universally mandatory, and may
genuinely not exist in the filing** — the indigenous-vs-imported raw-material split was
a standard Schedule VI disclosure under the Companies Act 1956, but is not a required
line item under the current Schedule III/Ind AS regime the way "Cost of Materials
Consumed" itself (a single aggregate figure, always present) is. Many companies now
disclose only the aggregate consumption note and omit the indigenous/imported split
entirely, even in a fully-read, successfully-fetched annual report. Once you have
actually located and read the "Cost of Materials Consumed" note (or equivalent) and it
contains no indigenous/imported breakdown, that is a **definitive finding** — "the
company's FY26 annual report discloses total raw material consumption of ₹Xcr but does
not break this out by indigenous vs. imported source" — not an unresolved fetch
failure. Don't keep searching once you've actually read the note itself and confirmed
the split isn't there; that's a different (and stronger) conclusion than "couldn't
fetch the document."

**A useful fallback, once you've confirmed no direct breakdown exists**: the Board's
Report annexure on "Conservation of Energy, Technology Absorption and Foreign Exchange
Earnings and Outgo" (a mandatory disclosure under Section 134(3)(m) of the Companies
Act, present in every annual report regardless of the Schedule III raw-material note)
gives an aggregate **Foreign Exchange Earnings and Outgo** figure for the year. This
isn't a substitute for a raw-material-specific import % — the "outgo" figure includes
imports of capital goods, travel, and other foreign-currency spend alongside raw
material — but it's a real, citable aggregate forex-exposure figure worth reporting
alongside an honest note that it isn't raw-material-specific. The same annexure's
"technology absorption" section sometimes separately discloses an **imported
technology** item (name of the technology, source country, year of import) — cite this
too if present, labeled as a technology import, not a raw-material one.

**If a target annual report PDF is too large to fetch in one shot** (a common failure
mode for 100-300 page reports — direct `web_fetch`/`WebFetch` on the full PDF can time
out or exceed the tool's content-size limit): don't give up on the section entirely.
Instead:
1. `WebSearch` for the specific note by name first — e.g. `"<company name>" "raw
   material consumed" indigenous imported annual report` or `"<company name>"
   "contingent liabilities" annual report crore` — search snippets or secondary
   aggregator summaries (Screener's "documents" excerpts, equity-research annual-report
   analyses, Trendlyne) sometimes quote the exact note's figures directly without
   needing the full PDF.
2. If a direct BSE/NSE-hosted copy of the same annual report exists at a different
   (sometimes smaller/differently-encoded) URL than the company's own IR-site copy, try
   that second URL — file size and encoding can differ between mirrors of the same
   filing, and a fetch that times out on one mirror sometimes succeeds on another.
3. If the annual report is genuinely only available as one large file with no smaller
   mirror, this is one of the few cases worth a second attempt (contrary to the general
   "don't burn more than one retry" rule) specifically because this note is a real,
   recurring reporting requirement, not a one-off fact — try Claude in Chrome
   (`navigate` to the PDF URL, then `get_page_text`) as a genuinely different fetch path
   than `WebFetch`/`web_fetch`, since Chrome renders the PDF natively rather than
   proxying the raw bytes through the tool's own size-limited fetch. Note that some
   sites block the browser tool entirely (policy-blocked domains) or force a download
   dialog rather than an in-browser-renderable page for direct PDF links — if either
   happens, that path is genuinely closed, not worth a second attempt on the same URL.
4. **If steps 1-3 all fail, ask the user to download and share/upload the PDF
   directly** rather than continuing to retry automated fetches — once a large PDF is a
   local file (via upload), it can be read page-range by page-range with no size limit
   or timeout at all, which resolves the entire class of "file too large to fetch"
   failures in one step. This is the single most reliable escalation for a large annual
   report specifically, and should be offered proactively once 2-3 fetch paths have
   failed, rather than treated as a last resort after many more attempts.
5. Only after exhausting the above should the report state the figure couldn't be
   verified this run — and even then, prefer reporting whatever qualitative color the
   concall/investor presentation gave (per the bullet above) over a bare "not found"
   line, so the section still carries some signal.

**Once a large annual report PDF has been supplied locally (uploaded), reading it
efficiently still matters** — a 250-300 page annual report exceeds a single read, so
page-range reads are required (see the platform's own PDF-paging guidance). Don't
guess which page range holds a given note — the Standalone/Consolidated Financial
Statements section usually starts well past the halfway point of the document (Table of
Contents gives exact page numbers), and printed footer page numbers rarely match the
PDF's raw page index one-for-one (divider pages between major sections are usually
unnumbered) — sample a 15-20 page range near your estimate, note the footer-to-physical
offset from what comes back, and adjust the next read accordingly rather than assuming
a fixed offset holds across the whole document. The two notes worth targeting directly
by name via the Table of Contents/note index: "Cost of Materials Consumed" (or "Cost of
Raw Materials Consumed") for the raw-material figure itself, and "Contingent
Liabilities" (usually 1-3 notes later) for litigation/tax-dispute amounts — both are
usually within a few pages of each other, late in the Notes to Accounts, so one
well-targeted read often surfaces both at once.

## Manufacturing locations

The annual report's Property, Plant & Equipment note or "our facilities"/"corporate
information" section is the most reliable source for a full list of plant locations,
ownership (owned/leased), and area; the investor presentation's manufacturing-footprint
slide and concall Q&A about plant locations or expansion sites are secondary sources
that are often faster to fetch but less complete than the annual report.

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

Fetch mechanics (which sites, escalation pattern) in `reference/data_sources.md`.
Always record the as-of date next to the numbers — this section goes stale fast.

## Promoter / governance track record

Three separate things to check:
1. **Guidance reliability** — use `scripts/guidance_tracker.py` against the cached
   `guidance_history.json` for the company (built up over successive report runs from
   this skill; see `reference/step0_perceive.md`). This needs no new fetching once a couple of quarters are
   logged — it's a local comparison.
2. **Other governance signals** — pull directly from screener.in's Shareholding
   Pattern (promoter holding trend, pledge % if shown) and Documents tab (auditor
   qualifications or delayed filings usually show up as flagged BSE/NSE
   announcements). A falling promoter holding % is not automatically a red flag
   (could be a planned OFS/QIP) — state the fact and, if the concall or an
   announcement explains it, cite that; don't speculate.

   **For the visual PDF's shareholding-pattern chart** (`charts.shareholding_chart()` —
   see reference/report_sections.md's Promoter/Governance section), screener.in's Shareholding Pattern table already returns the
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
     documents covered in `reference/data_sources.md`'s "Credit rating agencies" section — these typically state the
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
     sub-section per `reference/report_sections.md`.

## Announcements sweep — last 6 months, materiality-assessed (standing requirement)

**Fetch every BSE/NSE corporate announcement from the last 6 months on every run, not
just when something else prompts a look** — this is a standing part of the standard
sourcing depth, the same status as the 6-quarter concall/investor-presentation window
and the 6-month rating recheck, not an optional extra. Rating actions, fund raises,
and litigation already get their own dedicated checks elsewhere in this playbook —
this sweep is for the *rest* of what a company discloses: order wins, management
changes, new client relationships, capacity/capex approvals, and anything else that
moved the stock or the story between concalls.

**Where to fetch it**: BSE (`https://www.bseindia.com/stock-share-price/<company>/
<code>/corp-announcements/`) or NSE (`https://www.nseindia.com/companies-listing/
corporate-filings-announcements`) — see `reference/data_sources.md`'s "BSE / NSE filings" section for the fetch
mechanics (fallback pattern, Chrome escalation if JS-rendered). Filter to the last 6
months by announcement date.

**Assess materiality before deciding what to fold in — most announcements are routine
noise, and forcing all of them into the report would bury the ones that matter.**
Two tiers:

- **High materiality — actively look for these, and fold each one into the section it
  actually belongs to, not a generic "announcements" dump:**
  - **Order wins / large contract awards** → Near Term outlook (if recent enough to
    be forward-looking) or the Capex/Milestones/Certifications Timeline (as an
    achieved milestone) or Order Book (if it changes the disclosed backlog).
  - **Management/KMP changes** (CEO, CFO, MD, or a board-level appointment/
    resignation) → Promoter/Governance Track Record — a leadership change is
    governance-relevant even without a wrongdoing angle; state it as a fact with the
    effective date, and note if the announcement gives a reason (retirement,
    resignation, expiry of term) or is silent on why.
  - **New client relationships / client exits** → Marquee & Niche Customers (a new
    named client) or Key Risks (a disclosed client exit/concentration change).
  - **Capacity expansion / capex approvals** not already captured from the investor
    presentation → Capex/Milestones/Certifications Timeline.
  - **M&A, JV formation, or subsidiary/stake changes** → Value Chain Positioning (if
    it changes the business's actual structure) and/or Capex/Milestones Timeline.
  - **Regulatory action, show-cause notices, or exchange queries** (distinct from
    litigation, which has its own tracker) → Key Risks.
  - Anything that independently corroborates or contradicts a concall claim is
    automatically high-materiality regardless of category — cross-reference it
    explicitly rather than letting it sit unconnected.
- **Low materiality — don't force these into the report just because they exist:**
  routine board-meeting intimations with no substantive content, trading-window
  closure/reopening notices, compliance certificates (e.g. reconciliation of share
  capital), routine KYC/registrar updates, newspaper-publication confirmations. These
  exist on every company's announcement feed and reading past the headline to confirm
  they're genuinely routine (not, say, a board meeting intimation whose only content
  turns out to be a material capex approval) is still worth a quick check — the
  materiality judgment is about the actual content, not the announcement category
  label BSE/NSE assigns it.

**Log what you found and checked, don't just silently fold in what turned out to be
material**: for each high-materiality announcement actually used in the report, note
its date and BSE/NSE reference in the Sources list like any other citation. If the
6-month sweep turned up genuinely nothing material, say so in one line (e.g. in the
Capex/Milestones Timeline or Key Risks, wherever most relevant) rather than silently
omitting any mention that the check was made — this is the same "Never drop anything
silently" discipline applied to a sweep that legitimately came up empty.
