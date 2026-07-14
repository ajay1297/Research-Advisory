# Report Sections Spec (the nineteen sections after the outlook)

Universal rules (Title, Cover, Company Summary, Situation Classification, Value Chain
Positioning, Bullet rules, Paragraph length limit, Sourcing discipline) are in
`reference/report_format.md` — read that first. This file is the per-section spec for
everything that comes after the Near/Medium/Long Term outlook. PDF build mechanics
(which `html_helpers.py` function renders which section, chart-vs-table defaults) are
in `reference/report_assembly.md`.

## Sections after the Near/Medium/Long Term outlook

Append these nineteen sections, in this order, after Long Term. Each is conditional — skip
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
default (see `reference/report_assembly.md` for why). It's fine to close the section with a small
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
physical footprint, not an equipment inventory. Sourcing detail is in
`reference/source_playbook.md`'s "Manufacturing locations" section. If no source
discloses specific locations beyond a general headquarters city, say so rather than
guessing from the registered office address alone (a registered office is not
necessarily a manufacturing site). **Always render
as a bullet list, one point per location/fact — never merge into a single paragraph**,
per `reference/report_assembly.md`'s formatting rule.

**Raw Material Sourcing — domestic vs. imported, country-wise where disclosed** —
check whether the company's key raw material (the metal/chemical/component input
specific to its industry — e.g. stainless steel billets for a pipe maker, API
intermediates for a pharma company, glass preform feedstock for a fiber maker) is
imported, domestically sourced, or a mix. Capture:
- The domestic vs. imported **%** split of total raw material consumption.
- **If any portion is imported, break it down by country/region** wherever disclosed
  (e.g. "62% imported: China 40%, South Korea 15%, others 7%") — a single blended
  "imported" % without a country split understates a genuine concentration risk (a
  single-country dependency is a materially different exposure than a diversified
  import basket, even at the same aggregate %). If only the aggregate imported % is
  disclosed with no country breakdown, say so explicitly rather than presenting the
  aggregate as if it were the complete picture.

Sourcing mechanics (where to look, fallback order, and the case where this disclosure
genuinely doesn't exist in the filing) are in `reference/source_playbook.md`'s "Raw
material sourcing" section. State the fact plainly once found — if imports are a
majority of raw-material consumption, or concentrated in one country, this is a real
cost/FX/geopolitical exposure and should be cross-referenced in Key Risks (alongside
the existing commodity/FX-exposure risk category).

**Export Shipment / Customs Data** — for any company that exports (finished goods) or
imports (raw materials/components), always attempt one targeted check of a
shipment-data aggregator (Volza, Seair Exim, ImportGenius, Zauba Corp, Panjiva — see
`reference/source_playbook.md`) rather than treating this as optional. Where records are
found, list the concrete shipment-level detail actually surfaced — consignee/shipper
name, destination/origin country, and product description, and quantity/value if
shown — as its own short list (e.g. "Per Volza shipment records (not company-disclosed):
3 shipments of optical fiber cable to a consignee in Vietnam, Mar-May 2026; 2 shipments
to a consignee in Kenya, Jan 2026"), clearly labeled as third-party customs data rather
than company disclosure. This serves two purposes and should be checked for both: (1)
corroborating or surfacing customer names for Marquee & Niche Customers, and (2)
corroborating or filling the country-of-origin gap for Raw Material Sourcing above. If a
genuinely thorough check turns up nothing usable (site paywalled beyond a preview, no
records indexed for the company), say so explicitly in one line rather than omitting the
attempt silently — this is a check that should always be attempted and reported on, not
a check that's only mentioned when it succeeds.

### 8. Capacity Utilization & Headroom

Only include if a capacity utilization % or the inputs to derive one (installed
capacity, units produced) were disclosed — usually from the concall Q&A or an investor
presentation's operations slide.

**For bespoke/engineered-equipment makers, also capture product size/range capability
as its own distinct fact, separate from throughput capacity.** A company that
manufactures made-to-order equipment (cryogenic tanks, pressure vessels, transformers,
process skids, etc.) often discloses two genuinely different "capacity" concepts, and
both are worth including if disclosed — don't conflate them:
- **Throughput/volume capacity** — units or physical output per year (the
  fiber-km/annum, MT/annum, units/annum framing above).
- **Product size/range capability** — the largest (and smallest) unit the company is
  actually equipped to build, e.g. "manufactures tanks from 1-litre portable dewars to
  1,500,000-litre stationary tanks; transport tanks up to 60,000 litres," or "static LNG
  tanks up to one million litres." This is a real capability constraint distinct from
  annual throughput — a company can be running below its annual unit-volume capacity
  while *also* being one of very few suppliers capable of a specific largest-size
  product, and that size ceiling is itself a competitive/moat fact (cross-reference
  MOATs) as much as a capacity fact. State both where the company discloses each,
  rather than defaulting to only the annual-throughput framing.

Source for the size/range figure: the annual report's "Company Overview"/"Divisional
Review" section in the Management Discussion & Analysis (often phrased as a per-division
product range), the investor presentation's product-portfolio slide, or concall
descriptions of a specific large order (e.g. "the largest-sized tanks, 1,500 m³, in the
industrial gases segment"). A single large project's stated capacity (e.g. "10 x 1,500
m³ LNG storage tanks... largest installation of shop-fabricated, double-walled,
vacuum-insulated cryogenic tanks in the world") is itself worth citing as evidence of
the size ceiling actually being reached in practice, not just claimed.

**Report capacity in the industry's own physical unit first, revenue second.** Every
industry measures capacity differently, and that native unit is the primary figure a
reader needs — a revenue-only framing hides real information (utilization dynamics,
product-mix flexibility, comparability to the company's own historical disclosures and
to peers). Use whatever unit the company itself discloses: fiber-km/annum for an
optical fiber maker, MT/annum for a metals/chemicals/cement producer, MW/MWp for a power
or renewable-equipment company, number of vehicles/looms/spindles/kegs/cylinders for a
discrete-unit manufacturer, bed-days or occupancy % for a hospital, etc. — never force
a single generic "utilization %" without stating what's actually being utilized. If the
company discloses capacity split by sub-type/grade/spec within the same broad unit
(e.g. an optical fiber maker breaking out standard single-mode fiber vs. a specialty
grade like 50-micron/OM-series multi-mode fiber, or a steel maker splitting flat vs.
long products), show that breakdown rather than collapsing it into one aggregate
figure — the utilization dynamics for a specialty/high-margin sub-type are often the
more decision-relevant number than the blended aggregate.

**Flag explicitly if the capacity is a shared, multi-purpose pool** — i.e. the same
production line/plant/asset can be swung between multiple product variants or grades
rather than each variant having dedicated, ring-fenced capacity. This matters because
utilization of the aggregate pool doesn't tell a reader how much of *any one* variant
could be produced if demand shifted toward it — state this plainly (e.g. "the Kalol
line is a multi-purpose asset that can be allocated across standard, hollow-core, and
multi-core fiber depending on order mix — the utilization figure below is for the
shared pool, not any single fiber type") rather than presenting a blended % as if it
described a dedicated line. If the company discloses genuinely dedicated (single-product)
capacity instead, say that explicitly too — the distinction is the point, not a detail
to skip.

Once the physical-unit figures are established, optionally convert to a revenue lens
via `scripts/capacity_utilization.py`: current revenue at current utilization %, and
the max revenue achievable at 100% utilization of *existing* capacity with no further
capex. State both the physical-unit figures and, where realization/pricing data
supports it, the revenue headroom plainly — e.g. "Installed capacity is 50 million
fiber-km/annum (shared across standard and specialty grades); FY26 production was 39
million fiber-km (78% utilization). At full utilization of existing capacity alone,
that implies ~INR302cr of additional revenue headroom before any new capex is needed."
If a revenue conversion isn't supportable (no realization/pricing figure available),
show the physical-unit utilization alone rather than forcing a revenue estimate. If
utilization is already at or above 85% (on the physical-unit basis), reproduce the
script's high-utilization flag verbatim — near-term growth beyond that point depends on
the Capex/Milestones timeline above, not just running the existing plant harder.

**Before vs. after capex, where a post-capex figure exists**: if the Capex/Milestones
timeline (section 2) or the outlook sections already captured a management-disclosed
revenue potential once planned capacity additions complete (e.g. "capacity to support
INR3,000-3,200cr sales by FY28"), pass it to `scripts/capacity_utilization.py` via
`--post-capex-max-revenue-cr` (don't re-derive a number management already gave) so the
section shows both figures side by side: current-capacity ceiling ("before capex") and
the disclosed post-capex potential ("after capex"), plus the revenue the capex itself
unlocks (the gap between the two). If no post-capex revenue figure was disclosed
anywhere, show the before-capex figure alone and say so, rather than estimating one.

**In the visual PDF, this is a `data_table()` only** — columns/rows for installed
capacity (in the industry's native unit), current production/utilization, before-capex
ceiling, after-capex potential, and headroom-unlocked, with a separate row or note for
each disclosed sub-type/grade if the company breaks capacity out that way. No chart by
default, per `reference/report_assembly.md`.

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
Long Term outlook per `reference/report_format.md`'s Status Pointer rule — cross-reference rather than
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
  `reference/report_assembly.md`) embeds a real font and renders ₹ natively, no substitution needed.

### Broker / agency research — inline-tagged, no dedicated section

When the user has uploaded a third-party broker/agency research report (Nuvama,
Motilal Oswal, ICICI Securities, etc. — see "Broker / agency research reports" in
`reference/source_playbook.md` for the sourcing/compliance rule; this pipeline never
fetches broker research off the web), **there is no separate section for it.** Instead,
fold each broker-sourced fact directly into whichever section it naturally belongs to
— a target price and rating into Valuation, a broker's demand-growth read into
Industry Tailwinds/Headwinds, a broker's thesis point into Investment Thesis Summary,
a broker-flagged risk into Key Risks, and so on — exactly where a reader would expect
to find that kind of claim, rather than segregated into its own block.

**What keeps it from getting mixed up with the pipeline's own sourcing is an inline
tag on every broker-sourced point, not physical separation.** Immediately after any
fact, figure, or claim drawn from a broker report, append a tag in this exact format:

```
[<BROKER>_<DDMMYYYY>]
```

`<BROKER>` is the agency name, uppercase, no spaces (`NUVAMA`, `MOTILALOSWAL`,
`ICICISEC`, etc.); `<DDMMYYYY>` is the report's own publication date, not today's
date. Example, from an actual Nuvama Result Update dated 29 April 2026:

> Nuvama raised its 12-month target price to Rs.440, valuing the company at 15x
> Mar-28E EBITDA [NUVAMA_29042026].

Every broker-sourced sentence gets its own tag, even if two consecutive sentences come
from the same report — don't tag a whole paragraph once and leave later sentences in
it untagged, since a reader (or a later edit) may lift one sentence out of context.
A table row or bullet point pulled from a broker report gets the tag at the end of
that row/bullet, same rule. If the same fact is independently corroborated by both a
broker report and a primary source (e.g. the company's own concall), cite both — the
tag doesn't replace the pipeline's own sourcing discipline, it adds to it: `management
guided X on the Q4 concall, later reiterated as Nuvama's base case [NUVAMA_29042026]`.

Never let a broker's estimate or target silently become "the" number in a section that
also carries the pipeline's own independently-derived figure (e.g. Valuation's Forward
PE table) — if both exist, show both, each clearly attributed (the pipeline's own row
unlabeled/as normal, the broker's row carrying its tag), never averaged or merged into
one number. Paraphrase a broker's thesis/risk points in your own words rather than
reproducing paragraphs verbatim (per the compliance note in `source_playbook.md`) —
the tag establishes attribution, it doesn't license copying the source text at length.

### 11. Industry Tailwinds / Headwinds

2-4 bullets, each citing a specific external source (peer concall, sector report, news
on order inflow/pricing/regulation across the industry — not just this company).
Format: `**<Tailwind/Headwind name>**: <one to two sentence factual claim>. (Source:
<name, date>)`. Separate tailwinds from headwinds with a one-line subheading each if
both are present.

### 12. Competitive Positioning: Peer Comparison

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
the disclosed facts. If no direct listed pure-play peer exists (common for a genuinely
niche business), say so explicitly and use the closest adjacent listed comparables
available, labeling them as adjacent rather than direct competitors.

### 13. MOATs

A dedicated section — kept separate from the Peer Comparison table above because a
company's moat is about its own durable structural advantages, not how it stacks up
against named peers on a table. **Render as a bullet list (`flag_list(kind='bull')` in
the visual PDF, plain markdown bullets in the `.md`) — never a merged paragraph.** Cover
whichever of these actually apply, each bullet naming the specific evidence behind it
(never a generic "strong moat" assertion with no support):

- **IP / Technology Moat** — patents, proprietary processes, in-house R&D depth,
  a technology platform/product the company itself claims is differentiated (e.g. a
  specific fiber type, alloy, formulation, or software stack), and the backward
  integration depth already established in `reference/report_format.md`'s Value Chain Positioning section
  (cross-reference rather than re-explain).
- **Entry Barriers** — the barriers a new entrant would actually face in this specific
  business, sourced from the company's own commentary (concalls often address "why
  can't a new entrant just walk in" when analysts ask), peer commentary, or the annual
  report's industry-overview/competitive-strengths section: capital intensity
  (plant/equipment cost to reach minimum viable scale), certification/qualification
  lead time (e.g. aerospace AS9100, defense vendor empanelment, pharma USFDA approval —
  often multi-year processes, a specific number of years if management gave one),
  customer qualification/design-in cycles, proprietary technology or know-how, and
  regulatory barriers specific to the market (e.g. an import-certification regime that
  blocks foreign competitors). Only state a barrier the sources actually support — don't
  assume high barriers just because a business sounds specialized.
- **Product Criticality** — how critical the company's product is to its customer's
  end-use: is it a safety-critical or mission-critical component (aerospace, defense,
  power-plant, pharma) where a failure or substitution carries an outsized cost to the
  customer beyond the product's own price — or is it a more discretionary/substitutable
  input? Source from management's own framing of the product's role, a customer's
  disclosed qualification requirements, or industry context; never invent a criticality
  claim the sources don't support.
- **Switching Costs** — anything disclosed about how costly/slow it is for an existing
  customer to move to a competitor (re-qualification cycles, integration depth,
  contractual lock-in) — this is often the same underlying fact as the entry-barrier and
  criticality points above; cross-reference rather than re-explain if so.

If the research genuinely doesn't support a real moat on one or more of these fronts for
this company, say so plainly for that bullet rather than manufacturing one — a company
can have a real moat on IP/technology while having weak switching costs, and the section
should reflect that honestly rather than presenting a uniformly strong picture.

### 14. Technical Snapshot

Pull, don't compute — get the trend/moving-average/RSI/support-resistance summary from
a technicals-focused source (see source_playbook.md) rather than deriving indicators
from raw OHLC data. State the data-as-of date. Cover: current price, 52-week high/low,
trailing P/E, trend versus 50/200-day moving averages, RSI reading and what it implies
(overbought/neutral/oversold), nearest support and resistance. Always timestamp this
section since it goes stale within days — flag that explicitly if the report is more
than a week old.

**Table or bullet points — never a prose paragraph, in either the `.md` or the PDF.**
This section is a scannable metric dump, not a narrative, so the markdown deliverable
itself must use a markdown table (`Metric | Value | As of`) or a bullet list, one
metric per row/bullet — the same discipline the rest of this spec applies to Order
Book, Segment-wise Performance, and Capacity Utilization. **In the visual PDF, lead
with a `data_table()`** — `Metric | Value | As of`, one row per metric (Price, 52-Week
High, 52-Week Low, Trailing P/E, Moving Averages, RSI, Support/Resistance) — this is
the default format, not a paragraph. If a specific metric (moving averages, RSI,
support/resistance) genuinely wasn't sourced this run, put "Not reliably sourced this
run" as its value rather than omitting the row or guessing a number. It's fine to
follow the table with one short `para()` (normal body text, not the small italic
`.note` style — this section has real numbers a reader needs to read comfortably)
giving context on the 52-week range and the staleness caveat, but the metrics
themselves belong in the table/bullets, not folded into that closing sentence.

### 15. Promoter / Governance Track Record

Sourced from `scripts/guidance_tracker.py`'s output (see SKILL.md workflow). Show a
short table or list of the last 6 quarters (the framework's standard sourcing-depth
lookback, not a per-report choice): guidance given vs. actual delivered,
and whether it was a beat/met/miss. If 2 or more of the last 4 tracked guidance calls
were missed by a meaningful margin, say so plainly — this is exactly the kind of
pattern the section exists to surface, not to soften. Also note, if visible from
screener.in: promoter shareholding trend, any pledged shares, and any auditor
qualification or delayed filing. State facts; do not speculate about motive.

**In the visual PDF, render the shareholding trend as a `data_table()`** (Promoter/FII/
DII/Public % as columns, one row per quarter) — no chart by default, per
`reference/report_assembly.md`. Pull it straight from screener.in's shareholding-pattern table, which already
returns the multi-quarter history in one fetch (see source_playbook.md) — no separate
tracking script needed for this one, unlike guidance/fund-raises/ratings/litigation. Add
a promoter-pledge `card_grid()` metric alongside it if a pledge % is disclosed.

**Promoter Fund Raises** (sub-section, always included once any raise is on record —
unlike guidance, this is not lookback-limited to the standard 18-month window; a
preferential/warrant/debt raise from several years ago is still relevant governance
context). Sourced from
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
`reference/report_assembly.md`, add `charts.donut_chart()` only if the user specifically asks for a
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

### 16. Investment Thesis Summary

**Bullet points by default — `flag_list(kind='bull')` in the visual PDF, markdown
bullets in the `.md`** — not a prose paragraph. Each bullet is one specific, falsifiable
claim, synthesized from what's already been gathered above — not a restatement of the
whole report, and not general enthusiasm. A single short lead-in sentence before the
bullets is fine to frame the overall shape of the case (e.g. "The thesis rests on three
independently-corroborated pillars:"), but the substance belongs in the bullets, each
carrying its own source. Pull from:
- Near/Medium/Long Term bullets currently marked `[On Track]` or `[Delivered]` — these
  are the outlook claims with actual interim evidence behind them, the strongest
  material for a thesis.
- The MOATs section and Competitive Positioning table, if the reporting company leads
  peers on IP, certifications, entry barriers, or niche customers.
- Total Addressable Market headroom and the Capacity Utilization before/after-capex gap,
  if both point the same direction.
- Any independent third-party corroboration surfaced elsewhere (a named customer's own
  capacity guidance, a credit-rating reaffirmation/upgrade, export-shipment data).

Each bullet keeps its source, the same discipline as every other section — this reads as
"here is the specific, evidenced case," not marketing copy. **If the research gathered
above genuinely doesn't support a real thesis, say so plainly in one or two bullets (or
a single short paragraph if bullets would be artificial) rather than padding it out** —
a report that concludes "there isn't a well-evidenced thesis here yet" is more useful
than one that manufactures a story. This applies at the claim level too: if there are
only one or two genuinely strong claims, write one or two bullets, don't stretch to
three or four for the appearance of thoroughness. It's fine to close with one short
tempering paragraph (not a bullet) naming the factor(s) that keep the thesis from being
fully de-risked — that synthesis reads more naturally as prose than as a bullet.

### 17. Key Risks (Red Flags / Bear Case)

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
troubled, this section (not section 16) should dominate the report, and the Verdict
below should say so plainly.

### 18. Verdict

`verdict_box()` in the visual PDF (a short highlighted paragraph in the markdown
deliverable) — one or two honest sentences: the situation classification (see
`reference/report_format.md`'s Situation Classification section),
the single strongest piece of evidence for the thesis, and the single biggest open
question or risk. State confidence level honestly — "well-evidenced but early,"
"speculative," and "not enough here for a real thesis" are all legitimate verdicts; pick
whichever the evidence actually supports, not whichever makes the best-sounding
closing line. **"One or two sentences" means genuinely short** — if drafting this
section pulls in enough supporting detail to exceed the report-wide 10-line paragraph
limit (see `reference/report_format.md`'s "Paragraph length limit"), that's a sign too much evidence-recapping
crept in here rather than staying in the sections that already carry it (Investment
Thesis Summary, Key Risks); trim back to the actual verdict rather than converting an
overlong paragraph into bullets here — a bulleted Verdict undermines the one-line,
closing-statement purpose this section exists for, unlike every other section where
bullets are the default.

### 19. Sources

`sources_list()` in the visual PDF (a numbered, hyperlinked list in the markdown
deliverable) — every URL cited anywhere in the report, numbered, each with a short note
on what it supports (e.g. "3. CRISIL rating rationale, March 2026 — Credit Rating
Snapshot"). This is the reader-facing counterpart to the internal `quotes.json`
traceability already required by `reference/report_format.md`'s Sourcing discipline —
the same mapping, surfaced for the reader instead of kept only in the cache.

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
