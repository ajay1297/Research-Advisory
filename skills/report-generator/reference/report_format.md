# Report Format Spec

Fixed structure, modeled on the Venus Pipes example (`examples/venus_pipes_report.md`).
Do not deviate from this structure unless the user explicitly asks for a different
template.

## Title

`# <Company Name>`

## Cover (PDF only)

The visual PDF (see "Assembly — building the visual PDF" at the end of this file) opens
with a dedicated cover page via `html_helpers.cover()`: company name, ticker(s) and
exchange(s), a **situation badge** (`html_helpers.badge()`), and the report date. The
markdown deliverable doesn't need a literal cover page — just make sure the situation
classification (see below) and the inputs the badge needs (company name, tickers,
exchanges) are unambiguous in the drafted markdown so the PDF-assembly step can pull
them straight through.

Badge kind mapping (`badge(text, kind)`):
- `kind='growth'` — structural growth situation
- `kind='bull'` — steady compounder or a turnaround with solid interim evidence
- `kind='watch'` — cyclical, or a turnaround/growth story still short on evidence
- `kind='bear'` — structural decline / red-flag-heavy situation
- `kind='neutral'` — mixed or genuinely hard to classify; don't force one of the above

## Company Summary (immediately after the title, before Near Term)

A single short paragraph (3-5 sentences) orienting a reader who has never heard of the
company: what it makes/does, its sector/industry, how long it's been in business or
listed, which exchange(s) it trades on, and current market cap. Source from the
screener.in "About" text, the concall's own opening remarks, or the annual report's
business overview — never invent a description. Keep this factual and neutral; it is
scene-setting, not analysis (the analysis is what the rest of the report is for). No
heading needed for this paragraph beyond the title itself — it sits directly under
`# <Company Name>`, before `## Near Term`.

**Headline stat card grid** — immediately follow the paragraph with a `card_grid()` of
3-4 at-a-glance stats: market cap, current price, 52-week range, sector. Pull these
straight from the screener.in fetch already done for this section; don't compute
anything new. This gives a reader the same orientation the paragraph does, but scannable
in under five seconds — the same principle as the cover badge.

## Situation Classification (immediately after Value Chain Positioning, before Near Term)

Before drafting the outlook sections, state plainly — from the evidence gathered so
far, not from assumption — which broad situation the company is actually in right now.
This single classification drives the cover badge above and should be revisited (not
just carried forward unchanged) on every regeneration, since a company's situation can
shift between refreshes. One short paragraph, with the evidence for the classification:

- **Distress recovery / turnaround** — real financial trouble (debt default, NCLT
  resolution, negative net worth, trade-to-trade classification) with a documented
  reset since.
- **Steady compounder** — consistent revenue/profit growth, stable or improving margins
  and returns on capital, no major structural change — durability and reasonable
  valuation are the story, not a catalyst.
- **Cyclical** — earnings and stock price move with a commodity price, interest rate, or
  capacity-utilization cycle; the question is where in the cycle the company sits now.
- **Structural growth** — riding a multi-year secular trend (market share gains, new
  product category, geographic expansion) with evidence of execution, not just
  narrative.
- **Structural decline / red-flag heavy** — genuine deterioration with no credible
  turnaround evidence yet. It's completely fine, and expected sometimes, for this
  classification to be the honest one — don't force a "turnaround" or "growth" framing
  onto a company that's actually just declining, and don't force red flags onto a
  genuinely boring, healthy compounder just to fill this out.

A mix of two is fine (e.g. "cyclical, currently in a structural-growth phase of the
cycle") if the evidence genuinely points that way — state both rather than picking one
artificially.

## Value Chain Positioning (immediately after Company Summary, before Near Term)

A short paragraph answering: where does this company sit in its industry's value
chain? What does it buy and from whom (upstream — raw materials, components, licensed
technology)? What does it sell and to whom (downstream — OEMs, retailers,
end-consumers, exports)? Is it a raw-material processor, a component/sub-assembly
maker, an OEM, a brand, a pure distributor, or some combination? Name the specific
tier if the company or its customers describe it that way (e.g. "Tier 2 supplier to X
OEMs, who in turn supply Y end market"). Source from the investor presentation's
business-model/value-chain slide (very common in Indian small/midcap decks), concall
description of customers' customers, or the annual report's industry-overview
section — never invent a position that wasn't stated or a reasonably direct inference
from what was disclosed (e.g., "an OEM's own OEM customers are X" is fair to name if
the company said so; don't guess an entire multi-tier chain from a one-line business
description).

**Always follow the paragraph with a flow diagram** in a fenced code block (four
backticks... no, three: ```` ``` ````) in the markdown deliverable. Use a **vertical
stacked-box layout**, one box per value-chain stage, connected by a `|` / `v`
arrow — never a wide horizontal side-by-side layout, regardless of which renderer
produces the final PDF (see below) — a vertical stack is bounded only by its single
longest line, so it stays safe regardless of content length, while a horizontal
multi-box layout can silently exceed page width for a company with longer names/
descriptions. Size each box's width to its own longest inner line (pad the `+---+`
border to match, at least 2 spaces of padding either side of the text). Standard
four-stage template — adapt the number of stages/wording to what the company actually
described, don't force exactly four if the real chain is shorter or longer:

```
+--------------------------------------------------+
|  UPSTREAM                                         |
|  <inputs bought, and from whom>                   |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  THE COMPANY -- <Company Name>                    |
|  <what it makes/does, in a few words>             |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  DOWNSTREAM CUSTOMERS                             |
|  <who buys directly from the company>             |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  END MARKET                                       |
|  <where the product/service ultimately ends up>   |
+--------------------------------------------------+
```

Only ASCII characters in the diagram (`+`, `-`, `|`, `v`, letters, digits, standard
punctuation) — no Unicode box-drawing characters (─│┌┐ etc.) or arrow glyphs (→, ↓) —
this keeps the markdown deliverable portable and safe if it's ever rendered through the
legacy `scripts/report_to_pdf.py` reportlab path (see "Assembly" below), whose base
font renders those glyphs as black boxes. If a stage isn't disclosed clearly enough to
fill in confidently, say so in the box text itself (e.g. `<not disclosed beyond "OEMs
and distributors">`) rather than inventing specifics.

**In the visual PDF** (the default output — see "Assembly" below), this same
upstream/company/downstream/end-market breakdown is rendered with `html_helpers.
flow_diagram()` as styled boxes with a real arrow glyph, not the monospace ASCII block —
WeasyPrint embeds a proper font, so the glyph-safety constraint above only binds the
markdown/reportlab path, not the primary visual pipeline. Pass the same stage
label/detail pairs used to build the ASCII block; don't maintain two different
descriptions of the value chain.

## Three sections, in this exact order

1. `## Near Term (Next 1 to 2 Quarters)`
2. `## Medium Term (6 to 12 Months)`
3. `## Long Term (1+ Years)`

## Bullet rules (apply to every bullet in every section)

- 2-3 bullets per section. No more than 4.
- Format: `**<Headline, 3-6 words>** \`[STATUS]\`: <one to two sentence factual claim
  in third person>. "<verbatim quote from management, attributed only implicitly by
  context>"`
- The quote must be a real, verbatim line from the concall/transcript/presentation —
  never invented or paraphrased. If no verbatim quote supports a claim, drop the claim.
- The claim sentence states the fact (numbers, dates, %, INR crore figures) and the
  quote substantiates the *tone/certainty* behind it. Numbers belong in the claim
  sentence, not just buried in the quote.
- Near Term bullets should reference concrete near-dated items: this quarter's/next
  quarter's order book, revenue guidance for the current year, near-dated capacity
  coming online, near-dated order wins/LOIs.
- Medium Term bullets should reference 6-12 month items: capex/expansion completion,
  new segment entry, order pipeline over the next few quarters.
- Long Term bullets should reference 1+ year items: new geographies, new end-markets,
  structural margin/mix shift, multi-year growth ranges.

### Status pointer — `[STATUS]` on every bullet

Every Near/Medium/Long Term bullet carries one of five status pointers, right after
the headline:

- **`[Pending]`** — a forward-looking claim whose horizon hasn't arrived yet, and
  there's no interim evidence yet to judge progress one way or the other. The default
  for anything genuinely new this quarter.
- **`[On Track]`** — horizon hasn't arrived, but interim evidence (an earlier phase
  delivered, a reaffirmed or raised subsequent guide, a milestone hit on schedule)
  supports it happening. This is the one status that most needs cross-checking prior
  concalls, not just the latest one — see below.
- **`[Delivered]`** — the horizon has passed and the actual outcome met or beat it.
- **`[Delayed]`** — a horizon or milestone that was pushed out from what was originally
  guided (a facility launch slipping a quarter, a target period extended).
- **`[Missed]`** — the horizon has passed and the outcome fell short.

**How to assess it, not guess it**: log every outlook item you draft into
`guidance_history.json` via `scripts/guidance_tracker.py add-guidance`, with your own
`--status` assessment based on what the sources actually say (never auto-derived — a
facility-launch milestone and a revenue number aren't comparable the same way). When a
later concall revises an item already logged (raises/lowers a number, extends a
timeline, confirms an earlier phase completed), log the new entry with
`--supersedes-id` pointing at the earlier one, so the item's full evolution can be
reconstructed — the same way the example status cards work: "at the Q3 call, guided
X; at the Q4 call, revised to Y; now considered on track." Run
`scripts/guidance_tracker.py <slug> report` and pull each item's current status and
evolution history from there — this is not lookback-limited to 6 months, since an
item's full guidance history is exactly what determines whether it's genuinely
"on track" or just freshly asserted. If a bullet is being drafted for the first time
with no prior mention anywhere, its status is almost always `[Pending]`.

## Sourcing discipline

- Every quote must be traceable to a specific document (concall date, investor
  presentation, or annual report). Keep that mapping in the cached `quotes.json` even
  if it's not printed in the final report, so the user can verify any line if asked.
- If the user wants sourcing shown inline, append `(Q&A, <Month YYYY> concall)` or
  `(Investor Presentation, <Month YYYY>)` after the quote instead of a bare quote mark.
- Never blend two different speakers/documents into a single quote.

## Never mention internal tooling in the report text

This report is built with the help of local scripts (`scripts/guidance_tracker.py`,
`scripts/fundraise_tracker.py`, `scripts/rating_tracker.py`, `scripts/litigation_tracker.py`,
`scripts/forward_pe.py`, `scripts/capacity_utilization.py`, etc.) — those names belong in
SKILL.md and source_playbook.md, which describe *how the report gets built*, never in
the report itself, which is *the finished deliverable*. Write findings directly: "Guidance
reliability (last 2 tracked quarters):" not "Guidance reliability (via
`scripts/guidance_tracker.py report`):"; "The following fund raises are on record:" not
"Sourced from `scripts/fundraise_tracker.py report`." State the fact, the source document
it came from (concall date, filing, rationale), and — where a flag fires — the flag
itself, in plain language. A reader of the final report should never see a file path,
a script name, or a `--flag` value.

## Sections after the Near/Medium/Long Term outlook

Append these eighteen sections, in this order, after Long Term. Each is conditional — skip
a section entirely (don't print an empty heading) if the underlying input isn't
available, and say so in one line rather than silently omitting it (the sole exception
is section 3, CDMO Pipeline, which is omitted with no mention at all for a non-CDMO
company — see below).

### 1. Marquee & Niche Customers

2-5 bullets naming the company's most notable clients — both large/marquee names
(recognizable global or domestic majors) and niche ones (a specialized customer that
signals a particular capability, e.g. a defense/aerospace client, a global pharma
innovator for a CDMO, a premium retail chain). Format: `**<Customer name>**: <what they
buy / since when / any disclosed scale of the relationship>. (Source: <investor
presentation/annual report/concall, date>)`. Only name a customer if it is explicitly
disclosed in a source document — never infer a customer relationship from indirect
evidence (e.g. a logo seen in a photo, an analyst's guess). If the company discloses
customer concentration (e.g. "top 10 clients = X% of revenue"), state that fact here
too, factually, without editorializing on whether that's good or bad (a duplicate,
risk-framed version of this fact belongs in Key Risks if concentration is material).

**Customer's own guidance, where disclosed**: for each named customer, check whether
that customer has itself publicly disclosed guidance, capacity plans, or an outlook
that implies future demand for the reporting company's products (e.g. an OEM customer
stating it plans to double its own capacity, or a retail customer announcing a store
rollout). This is independent, third-party corroboration of the demand story — treat
it with the same weight as the rating-agency or peer-concall corroboration used
elsewhere in this report. State explicitly, per customer, whether such guidance was
found or not (e.g. "No independently disclosed guidance from Style Bazaar was found in
the sources reviewed") rather than silently omitting the check.

**Export-shipment data as a supplementary lead** — for an exporting company, a quick
check of an export/shipping-data aggregator (Volza, Seair Exim, ImportGenius, Zauba
Corp — see `reference/source_playbook.md`) can surface actual shipment consignees,
corroborating a named customer or surfacing one the company hasn't itself named. Label
anything sourced this way distinctly ("per third-party export-shipment records, not
disclosed by the company") rather than blending it into the company-disclosed list —
same discipline as every other fact in this report, just with a third-party-data label
attached.

### 2. Capex, Milestones & Certifications Timeline

A chronological table of capacity expansions, plant/line commissioning dates,
regulatory or quality certifications (e.g. aerospace/AS9100, ISO, USFDA, customer
-specific vendor approvals), industry/customer-awarded recognitions, and other
disclosed milestones — both **achieved** (past, with actual dates) and **planned**
(future, with management's expected dates). Format as a table: `Date/Quarter |
Milestone | Status (achieved/on-track/delayed) | Amount (INR crore, if capex) |
Source`. Order chronologically, past first. If management has given a capex plan
without specific dates, use the horizon they gave (e.g. "FY27-28") rather than
inventing a specific date. A certification (or an award) is a fact the moment it's
disclosed as obtained — don't hedge it as an opinion. Check the investor
presentation's "Awards & Accolades" slide (common in Indian small/midcap decks) before
a fresh search for these — see `reference/source_playbook.md`.

**Pull in every other future-dated item disclosed elsewhere in the report too** — a
TAM-capture target with its own horizon, a new-geography or new-segment entry date, a
product-launch or qualification-cycle completion date, a JV/subsidiary milestone, a
disclosed order-execution deadline. Any of these carrying a specific date or horizon
belongs in this table as its own row, not only the strict capex/certification subset —
this table is meant to be the single place a reader can scan every forward-dated
commitment the company has made. Add a one-line cross-reference in the row (e.g. "see
Total Addressable Market" / "see Long Term Outlook") instead of re-explaining the full
context here.

**In the visual PDF**, render this as `html_helpers.timeline()` instead of (or, for the
markdown deliverable, alongside) the table — map each row's status through
`html_helpers.STATUS_KIND` so achieved/on-track/delayed items get the same five-state
color coding as the outlook bullets' status pointers, not the simpler binary done/
pending scheme.

### 3. CDMO Pipeline (Phase 1 / 2 / 3 / Commercial)

**Only include this section if the company is a CDMO (contract development and
manufacturing organization) or has an explicit CDMO/CRAMS business line** — determine
this from how the company describes its own business (concall, investor presentation,
annual report), never from a keyword guess. For a non-CDMO company, omit this section
entirely with no heading and no mention that it was skipped (unlike every other
conditional section here, which states explicitly when data wasn't found — a molecule
pipeline is simply not an applicable concept for a non-CDMO business, so there is
nothing to flag).

When it applies: show the number of molecules/projects the company has disclosed at
each stage — Phase 1, Phase 2, Phase 3, and Commercial/Approved — as a simple count
table. CDMO disclosures almost never name the molecule or sponsor (confidentiality is
part of the business model); report the counts and, if disclosed, the therapeutic
area/end-market split (e.g. "3 commercial-stage, 5 in Phase 3, across oncology and
CNS") rather than inventing specifics that weren't given. Note the as-of date, since
pipeline counts shift every reporting period.

### 4. Financial Performance Summary

A table of the last 3-5 fiscal years (or last 6-8 quarters if the company is early in
its listed history) showing: Revenue, YoY growth %, Gross Margin %, PBT, PAT, PAT
margin %. Source from screener.in's quarterly/annual results tables (already fetched
for other sections — don't re-fetch). Compute YoY growth % yourself from the raw
figures; state the formula isn't needed inline (unlike Forward PE, this is a plain
historical trend, not a forward estimate) but the underlying revenue/PAT figures must
match what screener.in shows. If gross margin isn't a separately disclosed line (some
companies only report EBITDA margin), say so and show EBITDA margin instead, labeled
correctly — don't back into a gross margin figure that wasn't actually disclosed.

**In the visual PDF, this is a `data_table()` only** — no revenue/profit chart by
default (see "Assembly" below for why). It's fine to close the section with a small
`card_grid()` of compounded growth rates (10yr/5yr/3yr/TTM revenue and profit CAGR,
whichever the history supports) — cards aren't a chart, and these single numbers are
often the fastest read on the shape of the story.

**Balance sheet anomaly check** — while building this section, pull the same-period
balance sheet (already part of the screener.in/investor-presentation fetch) and scan
for anything that doesn't track normal scale-up: receivables or payables growing
sharply faster than revenue in a single year (compute debtor days = receivables ÷
revenue × 365 per year and look for a jump, not just a level), a cash balance that
stays thin relative to short-term borrowings across multiple years, a sudden spike in
"other assets"/"loans and advances" (sometimes used to mask related-party transactions),
goodwill or intangible write-offs, or a swing to negative net worth. State whatever you
find plainly, in one or two sentences, cross-referencing a credit-rating agency's own
"elongated operating cycle" or similar language if one of the ratings in the Promoter/
Governance section already flags the same thing independently — that's real
corroboration, not just your own read of two numbers. If nothing anomalous is found,
say so explicitly ("no balance sheet anomaly was identified in the periods reviewed")
rather than silently skipping the check.

### 5. Segment-wise Performance

Only include if the company actually reports revenue by segment — product line,
business division, or geography — per its Ind AS 108 segment-reporting note (annual
report), a segment breakout on screener.in, or management's own segment commentary on
the concall. **Always render this as a markdown table — never as inline prose or a
bare bullet list**, even when the company only discloses splits informally on a
concall rather than in a formal Ind AS 108 note. Table: `Segment | Revenue (INR cr) or
% of Total | YoY Growth | Segment Margin (if disclosed)`. If the company discloses
only one reportable segment (common for smaller/newer listings), say so plainly and
skip the table — don't force a breakdown (e.g. by product SKU) that wasn't actually
reported as a segment. If segment revenue is disclosed but segment margin isn't, show
revenue only and say margin wasn't broken out — don't back into an assumed split.

**Multiple disclosed bases**: if the company discloses segment splits on more than one
basis (e.g. by product line on one call, by end-market on an investor presentation, for
different periods), do not force them into a single blended table — render **one table
per basis/period**, each labeled with its own basis and as-of date/period, immediately
one after another. This is the same sourcing-discipline principle as the rest of this
spec: show what was actually disclosed, on its own terms, rather than reconciling
figures that weren't given on a common basis.

**Exports vs. domestic** is a basis worth checking specifically, even when not framed
as a formal Ind AS 108 segment — many Indian small/midcaps disclose it informally on
the concall or investor presentation. If disclosed (revenue INR cr or % of total, and
YoY growth if given), render it as its own table alongside any product-line/end-market
table rather than folding it into either. If exports revenue is disclosed but the
specific export geography/customer mix isn't, show the exports/domestic split alone
and say the geographic mix within exports wasn't broken out — don't infer it.

### 6. Order Book

Only include if the company discloses an order book figure (backlog of contracted/
awarded work not yet executed — common for capital-goods, EPC, defence, and
engineering businesses; less common for consumer/retail businesses, where it can be
omitted with a one-line note that no order-book figure was disclosed). **Always render
as a markdown table**: `As-of Date | Order Book (INR cr) | Basis (standalone/
consolidated/JV, if the company discloses more than one) | Composition (by order
type or end-market, if disclosed) | Source`. The order book is a point-in-time
snapshot, not a period figure — always state its as-of date next to the number, the
same staleness discipline as the Technical Snapshot and Total Addressable Market
sections.

If the company discloses order book on more than one basis for the same date (e.g.
standalone vs. consolidated, or a JV/subsidiary's order book reported separately), show
each as its own row rather than blending them into one number. Likewise, if the order
book's composition is broken out on more than one basis (e.g. by order type — production/
development/export — and separately by end-market — defence/space/exports), show both
breakdowns rather than picking one arbitrarily. If a quarter-specific order **inflow**
figure was also disclosed (new orders booked in the period, as distinct from the
cumulative order book level), it's fine to note it in one line under the table rather
than adding it as its own row — it's a different metric (a flow, not a stock) and
shouldn't be blended into the order-book figure itself.

**Exports vs. domestic composition** — if the order book's export/domestic split is
disclosed (INR cr or % of total for each), always show it as part of the Composition
column, or as its own row pair if the company gives it a level of detail that doesn't
fit cleanly alongside an order-type/end-market breakdown already shown. Treat this the
same as any other composition basis above: show what was actually disclosed rather than
estimating an export share from the customer list alone.

### 7. Manufacturing Locations & Physical Assets

Only include if the company discloses where its physical operations actually are.
List every manufacturing plant/facility/major office: location (city/state), owned vs.
leased, land/built-up area if given (sq ft or acres), and what it produces or houses
(e.g. "Howrah, West Bengal — owned, garment manufacturing" or "Pune, Maharashtra —
leased, bus-bar and connector assembly, Phase 1 operational"). If a specific plant's
own capacity or output was broken out separately from the company-wide utilization
figure in Capacity Utilization below, note it here rather than duplicating the whole
explanation. If management discloses notable machinery/equipment (a specific
certified line, an automated cutting system, a particular production technology), a
one-line mention is fine — this is about giving a reader a concrete sense of the
physical footprint, not an equipment inventory. Source from the annual report's
Property, Plant & Equipment note or "our facilities" section, the investor
presentation's manufacturing-footprint slide, and concall Q&A about plant locations
or expansion sites. If no source discloses specific locations beyond a general
headquarters city, say so rather than guessing from the registered office address
alone (a registered office is not necessarily a manufacturing site). **Always render
as a bullet list, one point per location/fact — never merge into a single paragraph**,
per the Assembly section's formatting rule below.

**Raw material import dependency** — check whether the company's key raw material
(the metal/chemical/component input specific to its industry — e.g. stainless steel
billets for a pipe maker, API intermediates for a pharma company) is imported,
domestically sourced, or a mix, and capture the disclosed import % and country/region
of origin if given. The primary source is the annual report's "Value of raw materials
consumed — indigenous vs. imported" note (a standard Companies Act/Ind AS disclosure,
usually in the Notes to Accounts, sometimes titled "Additional Information pursuant to
Schedule III"); concall Q&A about raw-material sourcing or supply-chain risk is a
secondary source. If the annual report isn't accessible, an export/import
shipment-data aggregator (Volza, Seair Exim, ImportGenius, Zauba Corp — see
`reference/source_playbook.md`) can show actual inbound shipment records (shipper,
origin country) as a partial substitute — say explicitly if only a partial picture was
available this way, since these sites usually gate full records behind a paywall.
State the fact plainly — if imports are a majority of raw-material consumption, or
concentrated in one country, this is a real cost/FX/geopolitical exposure and should be
cross-referenced in Key Risks (alongside the existing commodity/FX-exposure risk
category). If a specific import % or country genuinely isn't disclosed anywhere
reviewed, say so explicitly rather than assuming full domestic sourcing or estimating a
figure — a qualitative management comment about raw-material supply-chain risk (without
a hard %) is still worth reporting, just labeled as qualitative, not quantified.

### 8. Capacity Utilization & Headroom

Only include if a capacity utilization % or the inputs to derive one (installed
capacity, units produced) were disclosed — usually from the concall Q&A or an investor
presentation's operations slide. Compute via `scripts/capacity_utilization.py`: current
revenue at current utilization %, and the max revenue achievable at 100% utilization of
*existing* capacity with no further capex. State both figures and the headroom between
them plainly — e.g. "At 82% utilization, the company is doing INR248cr; its current
capacity alone could support ~INR302cr (22% headroom) before any new capex is needed."
If utilization is already at or above 85%, reproduce the script's high-utilization flag
verbatim — near-term growth beyond that point depends on the Capex/Milestones timeline
above, not just running the existing plant harder.

**Before vs. after capex, where a post-capex figure exists**: if the Capex/Milestones
timeline (section 2) or the outlook sections already captured a management-disclosed
revenue potential once planned capacity additions complete (e.g. "capacity to support
INR3,000-3,200cr sales by FY28"), pass it to `scripts/capacity_utilization.py` via
`--post-capex-max-revenue-cr` (don't re-derive a number management already gave) so the
section shows both figures side by side: current-capacity ceiling ("before capex") and
the disclosed post-capex potential ("after capex"), plus the revenue the capex itself
unlocks (the gap between the two). If no post-capex revenue figure was disclosed
anywhere, show the before-capex figure alone and say so, rather than estimating one.

**In the visual PDF, this is a `data_table()` only** (before-capex / after-capex /
headroom-unlocked as columns or rows) — no chart by default, per "Assembly" below.

### 9. Total Addressable Market (TAM)

Only include if management or an investor presentation disclosed an actual TAM figure
(a market-size number, not just a growth-rate or a generic "large opportunity"
statement — that belongs in Industry Tailwinds/Headwinds instead). Show: the TAM
figure(s) — broken down by product/segment if management gave it that way (e.g.
"INR700cr bimetal, INR600cr shunt, INR300cr contacts" rather than one blended number
that wasn't actually stated as such), the disclosed time horizon (TAM figures are
often paired with a 5-7 year capture window), and, if given, the % of TAM management
is targeting to capture and by when. Cite the source and its date — TAM estimates are
usually stated once in an investor presentation and simply carried forward, so note if
the figure looks dated (over ~2 years old) rather than presenting it as current. If a
specific TAM-capture target has its own timeline (e.g. "capture 50-60% of the bus-bar
TAM by FY28"), that claim should *also* appear as a status-pointer-tagged bullet in the
Long Term outlook per the Status Pointer rule above — cross-reference rather than
duplicate the full explanation twice.

### 10. Valuation — Forward PE

Only include if the company gave explicit forward revenue guidance (which the Near/
Medium/Long Term sections should already have captured). Compute via
`scripts/forward_pe.py`:

- Forward EPS = (revenue guidance x PAT margin assumption) / shares outstanding.
- PAT margin assumption: use management's explicitly guided margin if they gave one;
  otherwise fall back to trailing actual PAT margin and label it clearly as an
  **assumption, not guidance**.
- Price: use the current market price fetched from screener.in unless the user
  supplied their own price, in which case use theirs and say so.
- **Lead with a table** — this is the primary format for this section, not an
  afterthought below a paragraph. One row per input, so every number and its basis can
  be scanned without parsing a sentence:

  | Input | Value | Source/Basis |
  |---|---|---|
  | Revenue guidance | INR<guidance>cr | <management guidance source, e.g. "FY28 target, Q4 FY26 concall"> |
  | PAT margin used | <margin>% | <"management-guided" or "assumed — trailing FY26 actual"> |
  | Shares outstanding | <shares>cr | Equity capital ÷ face value |
  | Forward EPS | Rs.<EPS> | Revenue guidance × margin ÷ shares |
  | Price | Rs.<price> | <source, date> |
  | **Forward PE** | **<N>x** | Price ÷ Forward EPS |
  | Median PE (company, historical) | <N>x | <source, e.g. "5-year median, MoneyWorks4Me/Trendlyne/Tijori, as of <date>"> |

- **Add the company's own historical median PE as a row in the same table** — this is
  the company's typical trading multiple over time (commonly a 3-5 year median,
  whichever window the source actually states), not a peer comparison and not a
  forward estimate; it's the reference point for whether the current/forward multiple
  is trading rich or cheap versus the stock's own history. Source it from a secondary
  aggregator that publishes this directly (screener.in sometimes shows it; Trendlyne,
  Tijori Finance, and MoneyWorks4Me often do) since it's a computed statistic, not
  something management discloses — cite the aggregator and the window it used. If
  different sources disagree by more than a couple of points, say so and give a range
  rather than presenting a single falsely-precise number. If no source publishes a
  median PE for this company, say so rather than computing one from a partial price
  history yourself.
- Follow the table with a short note on what the multiple is arithmetic on (management's
  own guidance figure and the margin basis used), then — since this report is for
  personal research, not a distributed advisory product — it's fine to add one or two
  sentences of directional read *if it's actually evidenced*: how the resulting multiple
  compares to the Peer Comparison table's peers, to the company's own historical trading
  range (if visible on screener.in), or to the growth/CAGR figures from Financial
  Performance Summary. Ground any "rich/cheap-looking" language in a specific comparison
  number, not a bare adjective — "trading at 22x forward vs. peers at 14-18x on
  comparable growth" is evidenced; "looks expensive" on its own is not. Never present
  forward PE as a standalone number with no table/inputs anywhere nearby.
- Keep using the ₹ symbol in the markdown itself, for readability. The legacy
  `scripts/report_to_pdf.py` reportlab path substitutes "Rs." automatically since its
  base font renders a raw ₹ as a black box; the primary WeasyPrint pipeline (see
  "Assembly" below) embeds a real font and renders ₹ natively, no substitution needed.

### 11. Industry Tailwinds / Headwinds

2-4 bullets, each citing a specific external source (peer concall, sector report, news
on order inflow/pricing/regulation across the industry — not just this company).
Format: `**<Tailwind/Headwind name>**: <one to two sentence factual claim>. (Source:
<name, date>)`. Separate tailwinds from headwinds with a one-line subheading each if
both are present.

### 12. Competitive Positioning: Peer Comparison, Entry Barriers & Product Criticality

Always attempt this section — unlike a disclosure-gated section (TAM, order book), a
basic peer comparison is normally sourceable for any listed company from screener.in's
own "Peers" tab plus each peer's investor presentation, so a genuinely empty section
should be rare. If nothing usable can be sourced for a peer, say so explicitly for that
peer rather than dropping the section.

**Peer Comparison table** — identify 3-5 direct listed peers (screener.in's Peers tab,
the company's own concall references to competitors, or a sector report) and compare
each — including the reporting company itself as a row — on the factors that actually
differentiate competitive positioning in this business, not generic valuation ratios
(those belong in Financial Performance / Forward PE, not here):

| Company | IP / Technology Moat | Niche / Marquee Customers | Certifications & Qualifications | Other Differentiator | Source |
|---|---|---|---|---|---|
| <Peer 1> | <patents, proprietary process, in-house R&D, or "none disclosed"> | <named niche/marquee customers, if any> | <e.g. AS9100, USFDA, defense empanelment> | <backward integration, scale, cost position, geography> | <investor presentation/annual report/screener.in Peers tab, date> |
| **<The Company>** | ... | ... | ... | ... | ... |

Follow the table with one or two lines stating plainly which peer(s), if any, appear to
hold a stronger position than the reporting company on IP, customer niche-ness, or
certifications — and where the reporting company leads instead. This is a factual
comparison of what each company has itself disclosed (or what a sector report states),
not a ranking score, a moat "score," or a buy/sell signal — never editorialize beyond
the disclosed facts.

**Entry Barriers** — list the barriers a new entrant would actually face in this
specific business, sourced from the company's own commentary (concalls often address
"why can't a new entrant just walk in" when analysts ask), peer commentary, or the
annual report's industry-overview/competitive-strengths section: capital intensity
(plant/equipment cost to reach minimum viable scale), certification/qualification lead
time (e.g. aerospace AS9100, defense vendor empanelment, pharma USFDA approval — often
multi-year processes), customer qualification/design-in cycles, proprietary technology
or know-how, and switching costs for existing customers. Only state a barrier the
sources actually support — don't assume high barriers just because a business sounds
specialized.

**Product Criticality** — state how critical the company's product is to its
customer's end-use, per what's actually disclosed: is it a safety-critical or
mission-critical component (aerospace, defense, power-plant, pharma) where a failure or
substitution carries an outsized cost to the customer beyond the product's own price —
or is it a more discretionary/substitutable input? This is usually the same underlying
fact that drives the entry-barrier and switching-cost points above — cross-reference
rather than re-explain. Source from management's own framing of the product's role, a
customer's disclosed qualification requirements, or industry context; never invent a
criticality claim the sources don't support.

### 13. Technical Snapshot

Pull, don't compute — get the trend/moving-average/RSI/support-resistance summary from
a technicals-focused source (see source_playbook.md) rather than deriving indicators
from raw OHLC data. State the data-as-of date. Cover: current price, 52-week high/low,
trailing P/E, trend versus 50/200-day moving averages, RSI reading and what it implies
(overbought/neutral/oversold), nearest support and resistance. Always timestamp this
section since it goes stale within days — flag that explicitly if the report is more
than a week old.

**In the visual PDF, lead with a `data_table()`** — `Metric | Value | As of`, one row
per metric (Price, 52-Week High, 52-Week Low, Trailing P/E, Moving Averages, RSI,
Support/Resistance) — this is the default format, not a paragraph. If a specific
metric (moving averages, RSI, support/resistance) genuinely wasn't sourced this run,
put "Not reliably sourced this run" as its value rather than omitting the row or
guessing a number. Follow the table with a short `para()` (normal body text, not the
small italic `.note` style — this section has real numbers a reader needs to read
comfortably) giving context on the 52-week range and the staleness caveat.

### 14. Promoter / Governance Track Record

Sourced from `scripts/guidance_tracker.py`'s output (see SKILL.md workflow). Show a
short table or list of the last 2 quarters (6 months — the framework's fixed lookback
default for every query, not a per-report choice): guidance given vs. actual delivered,
and whether it was a beat/met/miss. If 2 or more of the last 4 tracked guidance calls
were missed by a meaningful margin, say so plainly — this is exactly the kind of
pattern the section exists to surface, not to soften. Also note, if visible from
screener.in: promoter shareholding trend, any pledged shares, and any auditor
qualification or delayed filing. State facts; do not speculate about motive.

**In the visual PDF, render the shareholding trend as a `data_table()`** (Promoter/FII/
DII/Public % as columns, one row per quarter) — no chart by default, per "Assembly"
below. Pull it straight from screener.in's shareholding-pattern table, which already
returns the multi-quarter history in one fetch (see source_playbook.md) — no separate
tracking script needed for this one, unlike guidance/fund-raises/ratings/litigation. Add
a promoter-pledge `card_grid()` metric alongside it if a pledge % is disclosed.

**Promoter Fund Raises** (sub-section, always included once any raise is on record —
unlike guidance, this is not lookback-limited to 6 months; a preferential/warrant/debt
raise from several years ago is still relevant governance context). Sourced from
`scripts/fundraise_tracker.py report`. List every preferential equity issue, warrant
allotment, NCD/debenture issue, term loan, or promoter loan/guarantee on record, each
with: date, instrument, amount (INR crore), allottee category (promoter/promoter
group/public/institution), **named individual/institutional investors where disclosed**
(e.g. a well-known HNI, FPI, or mutual fund named in the BSE/NSE allotment notice — not
just the category), issue price versus current market price if both are known, and
status (allotted/pending/converted/lapsed/outstanding/repaid). Naming a recognizable
investor is a real, verifiable signal (the same principle as naming a marquee customer
in the Marquee & Niche Customers section) — never infer participation from a
shareholding-pattern increase alone; only name someone the allotment notice, exchange
filing, or a news report actually names as an allottee. Always reproduce
the script's LAPSED-warrant flag verbatim if it fires — a promoter forfeiting the 25%
upfront payment on preferentially-allotted warrants rather than converting is a direct,
factual signal worth stating plainly, not a speculative one. If the company has raised
debt, note whether the promoter personally guaranteed it (from the credit rating
rationale, if available) — this ties leverage risk back to promoter accountability.
Never editorialize beyond the facts on record (no "this proves promoters have no
confidence" — state the lapse/dilution/leverage fact and let it stand).

Keep the full named-allottee detail as a `data_table()` in the visual PDF, with a
**named-investor column** per the rule above — don't summarize away individual names/
amounts, that's exactly the precision a chart would lose. **No donut chart by
default** — a table already shows each allottee's amount and share precisely; per
"Assembly" below, add `charts.donut_chart()` only if the user specifically asks for a
visual breakdown.

**Credit Rating Snapshot** (sub-section, included whenever any rating rationale was
found — say explicitly if none could be found for any agency rather than omitting the
sub-section silently). Sourced from `scripts/rating_tracker.py report`. For each rated
instrument, show: agency, rating, outlook, the rationale's own date, and the current
action (reaffirmed/upgrade/downgrade/outlook revised/withdrawn). Always reproduce the
script's downgrade / negative-outlook flag verbatim if it fires, and carry that flag
through into Key Risks below — a rating agency's own credit opinion is one of the few
independent, professionally-underwritten views in this whole report, and a negative
action should not be buried under the company's own more upbeat framing elsewhere.

**Legal & Litigation** (sub-section, checked on every report — say explicitly if no
litigation was found rather than omitting the sub-section silently). Sourced from
`scripts/litigation_tracker.py report`. List every material court case, tax dispute, or
regulatory/arbitration matter on record, each with: case reference, forum, case type,
parties, disclosed contingent-liability amount (if any), and status (ongoing/disposed
favorable/disposed unfavorable/settled/**dismissed but appealable**/closed final).
Always reproduce the script's reopen-risk flag verbatim if it fires — a matter that was
decided in the company's favor or dismissed at a lower forum is not necessarily over if
the other side (commonly a tax or regulatory authority) still has an open appeal
window; describe such a case as "dismissed, appealable within \<window\>," never simply
as "resolved" or "closed." Like Fund Raises and Credit Rating, this is not
lookback-limited — an old case with a live appeal window is exactly the kind of thing
this section exists to surface, however long ago it originated.

### 15. Investment Thesis Summary

Plain text (or a `flag_list(..., kind='bull')` in the visual PDF if the claims split
cleanly into bullets): the specific, falsifiable argument for why this could work,
synthesized from what's already been gathered above — not a restatement of the whole
report, and not general enthusiasm. Pull from:
- Near/Medium/Long Term bullets currently marked `[On Track]` or `[Delivered]` — these
  are the outlook claims with actual interim evidence behind them, the strongest
  material for a thesis.
- The Competitive Positioning table, if the reporting company leads peers on IP,
  certifications, or niche customers.
- Total Addressable Market headroom and the Capacity Utilization before/after-capex gap,
  if both point the same direction.
- Any independent third-party corroboration surfaced elsewhere (a named customer's own
  capacity guidance, a credit-rating reaffirmation/upgrade).

Each claim keeps its source, the same discipline as every other section — this reads as
"here is the specific, evidenced case," not marketing copy. **If the research gathered
above genuinely doesn't support a real thesis, say so plainly here rather than padding
it out** — a report that concludes "there isn't a well-evidenced thesis here yet" is
more useful than one that manufactures a story. This applies at the claim level too: if
there are only one or two genuinely strong claims, write one or two, don't stretch to
three for the appearance of thoroughness.

### 16. Key Risks (Red Flags / Bear Case)

3-5 bullets (`flag_list(..., kind='bear')` in the visual PDF) covering whichever of
these actually apply, sourced from the concall, filings, or industry context gathered
above — never invented:
- Business/execution risk (capacity constraints — cross-reference the Capacity
  Utilization headroom figure if utilization is already high, customer concentration —
  cross-reference the Marquee & Niche Customers section if concentration was
  disclosed there, single large contracts, delivery/quality disputes, a peer with a
  clearly stronger IP/certification/customer position from the Competitive Positioning
  section above)
- Financial risk (working capital trend, receivables/payables days, leverage,
  commodity/input-cost exposure, FX exposure)
- Governance risk (from the Promoter/Governance section above, if flagged — including
  any credit-rating downgrade or negative/watch-negative outlook from the Credit
  Rating Snapshot, and any dismissed-but-appealable or ongoing litigation from Legal &
  Litigation with a disclosed amount; treat each with at least as much weight as a
  guidance miss)
- Macro/industry risk (from the Tailwinds/Headwinds section above, if a headwind rises
  to the level of a real risk to the guidance given)

**This section is mandatory even in a strongly positive report** — a bullish Investment
Thesis Summary does not excuse a thin Key Risks section. If the company is genuinely
troubled, this section (not section 15) should dominate the report, and the Verdict
below should say so plainly.

### 17. Verdict

`verdict_box()` in the visual PDF (a short highlighted paragraph in the markdown
deliverable) — one or two honest sentences: the situation classification (see above),
the single strongest piece of evidence for the thesis, and the single biggest open
question or risk. State confidence level honestly — "well-evidenced but early,"
"speculative," and "not enough here for a real thesis" are all legitimate verdicts; pick
whichever the evidence actually supports, not whichever makes the best-sounding
closing line.

### 18. Sources

`sources_list()` in the visual PDF (a numbered, hyperlinked list in the markdown
deliverable) — every URL cited anywhere in the report, numbered, each with a short note
on what it supports (e.g. "3. CRISIL rating rationale, March 2026 — Credit Rating
Snapshot"). This is the reader-facing counterpart to the internal `quotes.json`
traceability already required by the Sourcing discipline above — the same mapping,
surfaced for the reader instead of kept only in the cache.

## What NOT to include

- No financial-ratio dumps — only the specific figures a bullet's claim needs.
- No editorializing beyond what management said, what a public filing/data source
  states, or a comparison actually shown elsewhere in the report (see Forward PE and
  Investment Thesis Summary above for how a directional read must stay tied to a cited
  number, not float free as a bare adjective).
- No fabricated evidence, ever, regardless of how the thesis would benefit — a claim
  without a source and a date is not evidence, it's marketing. If, after real research,
  there isn't enough verifiable material to support a genuine thesis, the Investment
  Thesis Summary and Verdict should say so plainly rather than manufacture one.

## Assembly — building the visual PDF

The default, primary deliverable is an infographic-style PDF assembled as HTML and
rendered with WeasyPrint — the same pattern as `scripts/charts.py` and
`scripts/html_helpers.py`'s own docstrings, which live in this plugin's `scripts/`
directory, paired with `assets/report_style.css`. The drafted markdown report (per the
section-by-section spec above) is still produced and cached as usual — see SKILL.md's
"Save and cache" step — the HTML/PDF assembly consumes the same facts and figures, it
doesn't replace the markdown as the source of truth for what was found.

**Tables are the default; charts are opt-in, not automatic.** Earlier drafts of this
skill defaulted to a matplotlib chart in Financial Performance Summary, Capacity
Utilization, the Promoter/Governance shareholding trend, and Promoter Fund Raises — this
was reversed after the report itself came out too chart-heavy without a corresponding
gain in clarity. **Financial Performance Summary, Segment-wise Performance, Order Book,
Capacity Utilization & Headroom, the shareholding trend, and Promoter Fund Raises all
render as `data_table()` only by default — no `charts.*` call for any of them unless
the user explicitly asks for a visual/chart version.** `scripts/charts.py` still exists
and still works if a chart is specifically requested for a given report, or if a
genuinely long time series (10+ years) makes a table hard to scan — but that's now the
exception, not the default. A one-off list of named allottees with exact amounts, or a
detailed litigation/rating table, was always better as a dense `data_table()` anyway —
charting it would lose precision the reader needs. Narrative sections (Company Summary,
Situation Classification, Investment Thesis Summary, Key Risks) stay as text/
`flag_list()`. **Marquee & Niche Customers and Manufacturing Locations & Physical
Assets always render as a bullet list (`flag_list()` with `kind=''` or a plain `<ul>`),
never merged into one paragraph** — each customer/location is its own scannable point.

**Use real Unicode punctuation characters, never HTML entities, anywhere in report
text** — write an actual `—` (em dash), `–` (en dash), `·` (middle dot), `…` (ellipsis)
or `→` (arrow) character in the string, not `&mdash;`, `&ndash;`, `&middot;`, `&hellip;`,
or `&rarr;`. WeasyPrint/DejaVu Sans renders real Unicode punctuation natively (this
pipeline has none of reportlab's base-font glyph-safety problem — see the Value Chain
Positioning section above), and typing the HTML-entity form instead is actively unsafe:
several `html_helpers` functions (`cover()`'s `meta_line`, `card_grid()`, `data_table()`,
`sources_list()`) pass their text through `esc()` for safety, which converts the
entity's leading `&` into `&amp;` — so `&middot;` renders as the literal text
"`&middot;`" on the page instead of a middle dot. Only `para()`, `flag_list()`, and
`verdict_box()` accept raw HTML and would render an entity correctly, and relying on
that split is exactly the kind of inconsistency that causes this bug — so just never use
entities, in any field, and the whole class of bug is impossible.

**Keep the page tight — avoid layout choices that create dead whitespace.** Use
`chart_row()` only when you're genuinely placing two or more charts side by side; a
single chart is `chart_block(...)` on its own, never `chart_row([chart_block(...)])` —
wrapping one chart in a flex row buys nothing and can stretch a small chart (e.g. a
donut) wider than intended, leaving an oddly empty-looking block. The cover page
itself should stay short (title, ticker, badge, date) — it's an orientation page, not
a page meant to be mostly blank.

**Exactly one `page_break()` call in the whole document** — immediately before section
15 (Investment Thesis Summary), so the closing thesis/risks/verdict run together on
a fresh page. Don't add one after Long Term Outlook, after Marquee & Niche Customers,
or anywhere else "to give the section room" — content flows naturally between sections
without help, and an extra `page_break()` reliably produces a gap of dead whitespace at
the bottom of whatever page it interrupts, which is worse than a section spanning a
page boundary normally would be. If you find yourself adding a second `page_break()`
call, that's a signal to remove it, not a sign the layout needs it.

```python
import sys
sys.path.insert(0, '<skill_dir>/scripts')
from charts import revenue_profit_chart, quarterly_trend_chart, shareholding_chart, \
    before_after_chart, donut_chart, line_compare_chart
from html_helpers import *

body = ''
body += cover('Company Name', 'NSE: TICKER | BSE: 000000',
               badge('STRUCTURAL GROWTH', 'growth'), 'Report date: 12 July 2026')
body += section('Company Summary')
body += para('...')
body += card_grid([('Market cap', 'Rs X Cr', ''), ('Price', 'Rs Y', ''), ...])
# ... Value Chain Positioning, flow_diagram(), Situation Classification,
#     Near/Medium/Long Term outlook, sections 1-18 ...
body += section('Financial Performance Summary')
revenue_profit_chart('rp.png', years, revenue, profit)
body += chart_block('rp.png', 'Annual revenue and net profit. Source: screener.in')
body += data_table(['Year', 'Revenue', 'YoY %', 'PBT', 'PAT', 'PAT margin %'], rows)
# ... through section 18 (Sources) ...

html = render(body, '<skill_dir>/assets/report_style.css')
open('report.html', 'w').write(html)
```

Then: `python3 -m weasyprint report.html report.pdf` (`pip install weasyprint
matplotlib --break-system-packages` once, if either is missing).

Save chart PNGs to a working directory alongside the intermediate HTML, and delete both
(along with the HTML) once the PDF is built and verified — only the final PDF and the
source `report.md` belong in `~/.report-generator/output/<company_slug>/`.

**Verify the rendered output before delivering it**: render a few pages to JPEG
(`pdftoppm -jpeg -r 120 report.pdf page`) to visually check charts aren't clipped,
tables aren't overflowing the page width, and page breaks land sensibly.

**Legacy fallback**: `scripts/report_to_pdf.py` (markdown → PDF via reportlab, no
charts, no cover/badges) still exists and still works if WeasyPrint genuinely can't be
installed in a given environment — text-only, but never blocks delivery. Prefer the
visual pipeline above whenever both are available.

Two easy mistakes to avoid:
- WeasyPrint needs `pip install weasyprint --break-system-packages` if it's not already
  present — check before assuming it's missing.
- `data_table()`'s `total_row_index` bolds one row (typically a "Total" summary row) —
  pass the row's index within `rows`, not counting the header.
