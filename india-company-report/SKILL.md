---
name: india-company-report
description: >
  Generate or refresh a visual, infographic-style investment-thesis PDF (a Company
  Summary with a headline stat card grid, a Value Chain Positioning writeup with a flow
  diagram, and an early situation classification — turnaround/compounder/cyclical/
  structural growth/structural decline — up front; Near/Medium/Long Term outlook backed
  by sourced management quotes, each tagged with a status pointer — Pending/On Track/
  Delivered/Delayed/Missed — tracked across concalls; marquee/niche customers plus their
  own disclosed guidance where corroborating, corroborated where relevant by export-
  shipment data; a capex, milestones (including awards) and certifications
  timeline that also rolls up every other future-dated commitment disclosed elsewhere in
  the report; a CDMO molecule-pipeline snapshot where applicable; multi-year YoY revenue/
  margin/PBT/PAT trend table plus a balance-sheet anomaly check; segment-wise revenue
  breakdown where reported, including an exports vs. domestic split where disclosed;
  order book with basis and composition breakdown (including exports vs. domestic where
  disclosed); manufacturing locations and physical assets (plants, buildings, notable
  machinery) as bullet points, plus raw-material import dependency (% imported and
  country of origin, where disclosed); capacity utilization with before-and-after-capex
  revenue potential (tabled); total addressable market where disclosed; forward PE with
  a summary table (including the company's own historical median PE) and an evidenced
  directional read against peers/history where supportable; industry tailwinds/
  headwinds; a peer comparison table on IP/technology moat, niche/marquee customers, and
  certifications, plus disclosed entry barriers and product criticality; a readable
  technical snapshot; promoter/governance track record — including a tabled
  shareholding-pattern trend, named preferential allottees, warrants, and debt the
  promoter has raised, independent credit-rating actions from CRISIL/ICRA/CARE/India
  Ratings/Acuite/Brickwork, and ongoing or reopenable litigation; a synthesized,
  evidenced Investment Thesis Summary; a mandatory Key Risks/Red Flags section even in a
  bullish report; a one-paragraph Verdict on confidence level; and a numbered Sources
  list) for an Indian listed company from its concall transcript, investor presentation,
  annual report, and screener.in data. Activate when the user says "research <company>",
  "generate a report on <company>", "regenerate/update/refresh <company>'s report",
  "analyse <company>'s concall", "what's the story with <company/ticker>", "build a
  thesis on <company>", or shares/references concall transcripts, investor
  presentations, or annual reports for a specific company. Personal research document —
  sourced and evidenced.
---

# India Company Report

Produces a **visual PDF** (metric cards, a color-coded timeline, and dense data
tables — tables are the default for anything with real numbers; charts are opt-in, not
automatic, see `reference/report_format.md`'s Assembly section) via WeasyPrint,
alongside the markdown source of truth. The report opens with a cover page (situation
badge + report date), then the company's name, a short Company Summary paragraph with
a headline stat card grid, a Value Chain Positioning paragraph with a flow diagram, and
a Situation Classification paragraph (turnaround / steady compounder / cyclical /
structural growth / structural decline — drives the cover badge), then these sections
in order: Near Term (1-2Q) / Medium Term (6-12mo) / Long Term (1+yr) outlook — each
bullet a claim + sourced quote + a status pointer (`[Pending]`/`[On Track]`/
`[Delivered]`/`[Delayed]`/`[Missed]`) tracked across concalls — then Marquee & Niche
Customers **(bullet list)** (plus their own disclosed guidance, if any), Capex/
Milestones/Certifications Timeline, CDMO Pipeline (only if applicable), Financial
Performance Summary (YoY revenue/margin/PBT/PAT table, plus a balance-sheet anomaly
check), Segment-wise Performance **(always a table, one table per disclosed basis/
period if the company discloses more than one)**, Order Book **(always a table, with
as-of date, basis, and composition breakdown where disclosed)**, Manufacturing
Locations & Physical Assets **(bullet list, plus raw-material import dependency where
disclosed)**, Capacity Utilization & Headroom **(table)** (before *and* after planned
capex, where disclosed), Total Addressable Market (where disclosed), Valuation
(Forward PE, led by a summary table that also includes the company's own historical
median PE, with an evidenced directional read against peers/history where
supportable), Industry Tailwinds/Headwinds, Competitive Positioning (peer comparison
table on IP/technology moat, niche/marquee customers, and certifications; disclosed
entry barriers; product criticality), Technical Snapshot **(readable body-text size,
not caption-sized)**, Promoter/Governance Track Record (guidance reliability + a
**tabled** shareholding-pattern trend + promoter fund raises **(table, with named
allottees where disclosed)**: preferential equity, warrants, NCDs/debt + independent
credit-rating actions from CRISIL/ICRA/CARE/India Ratings/Acuite/Brickwork + ongoing or
reopenable litigation), Investment Thesis Summary (a
synthesized, evidenced bull case — or an honest statement that one doesn't hold up),
Key Risks / Red Flags (mandatory, even in a bullish report), Verdict (one short
paragraph on confidence level), and Sources (numbered, hyperlinked). See
`examples/venus_pipes_report.md` for the outlook-section style and
`reference/report_format.md` for the full spec including the Company Summary, Value
Chain Positioning, the status-pointer rule, the visual-PDF Assembly pattern, and the
eighteen sections after the outlook.

**The report text itself never names internal scripts/files** (no
`scripts/guidance_tracker.py`, no `--flag` values) — those belong in this file and in
`reference/source_playbook.md`, which describe how the report gets built, not in the
report, which is the finished deliverable a reader sees. See
`reference/report_format.md`'s "Never mention internal tooling in the report text"
rule.

## How to trigger this — exact phrasing and company name

This is a Claude Skill, not a slash command — there is no `/command`, only natural
language. Say one of these, naming the company each time (full name, or the name
you'd search screener.in with — a stock symbol like "KARNIKA" or "TDPOWERSYS" also
works):

- `research <Company Name>`
- `generate a report on <Company Name>`
- `analyse <Company Name>'s concall`
- `regenerate <Company Name>'s report` / `refresh <Company Name>'s report` /
  `update <Company Name>'s report` — for an already-generated company, this reuses
  Step 0's freshness check rather than re-running everything from scratch.
- `rerun for <Company A> and <Company B>` — works for multiple companies in one
  request; each is processed independently through the same pipeline.
- `what's the story with <Company/Ticker>` / `build me a thesis on <Company Name>` /
  `do a deep dive on <Company Name> — is it a buy?` / `research <Company Name> for a
  turnaround thesis` — informal, non-jargon phrasing also triggers this skill; the user
  doesn't need to say "report" or name a section.

If you've uploaded a concall transcript, investor presentation, or annual report PDF
directly instead of naming a company, that also triggers this skill — sourcing then
prefers your uploaded documents over fetching (see "User-uploaded documents" in
`reference/source_playbook.md`).

There is no separate "setup" step and no config to edit — every run is self-contained
and named by company. Two companies' data never mix: each gets its own
`research_cache/<company_slug>/` working state and `output/<company_slug>/`
deliverable folder, keyed off a slug derived from the company name (lowercase,
underscores — e.g. "TD Power Systems" -> `td_power_systems`).

Do not read `reference/report_format.md` or `reference/source_playbook.md` in full
until you actually need them (step 2+ below). Read `examples/venus_pipes_report.md`
once, when drafting.

## The core rule: never load raw source documents into context

Concall transcripts run 15-40 pages, investor decks 20-50 slides, annual reports
100-300 pages. Every step below exists to avoid reading these directly. Always go
through `scripts/`, never paste a full transcript/PDF into your own reasoning.

## Token discipline — this pipeline is read-heavy, don't read more than needed

- **Grep before you Read.** Once a PDF is converted to `.txt`, don't `Read()` it
  top-to-bottom — `grep -n "<keyword>" -C3` for the section you need (order book,
  capex, margin guidance, etc.) and only `Read()` the specific line range that surfaces.
  `extract_theme_quotes.py`'s candidate JSON exists precisely so you never need to read
  the full transcript for the outlook bullets.
- **Don't re-fetch what's already in this session.** If screener.in, a concall PDF, or a
  rating rationale was already fetched this run, reuse what you extracted instead of
  fetching it again "to double check" — the sourcing discipline is about citing real
  documents, not about re-fetching the same one repeatedly.
- **Cap page-text/web-fetch reads to what you need.** Don't pull a full-page dump when a
  targeted `WebSearch` snippet or a smaller `max_chars` already answers the question
  (price, a single rating action, a single peer's market cap).
- **Batch independent fetches.** If you need screener.in, a concall PDF, and a rating
  rationale and none depends on another's result, fire them in parallel rather than
  sequentially.
- **Don't dump full JSON caches to stdout.** `guidance_tracker.py report` and friends
  already print a human-readable summary — that's what you read; you don't also need to
  `cat` the underlying `.json` file unless you're specifically debugging a tracker entry.
- **Write once.** Draft `report.md` in one pass per section rather than writing then
  re-reading then re-writing the same section multiple times — the Read-after-Edit habit
  is unnecessary here since the harness already confirms edits succeeded.
- **On a `new_quarter` refresh, fetch only what changed.** New concall + new investor
  presentation + screener.in's last 1-2 columns — full checklist in
  `reference/source_playbook.md`'s "Regenerating for a new quarter" section. Everything
  else (manufacturing locations, certifications, TAM, entry barriers, peer identities,
  value chain) carries forward from the cached `report.md` unchanged. This is the
  single biggest token lever in the pipeline — a full-history re-fetch on every
  quarterly refresh defeats the entire point of caching.
- **Don't burn more than one retry on a stuck source.** If screener.in's numeric
  widgets won't populate after one wait/retry, stop retrying it and fall back per
  `reference/source_playbook.md`'s "BSE / NSE filings" section (exchange filing
  directly, the concall/investor presentation you're already fetching, or a secondary
  quote aggregator for just the price) — debugging a stuck fetch costs more than
  switching sources.

## Step 0 — Check freshness before doing anything else

This is the step that makes regeneration cheap. Never re-run the full pipeline on a
report you've already generated for this company.

1. Fetch screener.in's Documents/Concalls tab only (not the transcript itself yet) to
   see the latest concall label (e.g. "May 2026").
2. Run `python3 scripts/check_freshness.py <company_slug> --latest-seen "<label>"`.
   - `no_state` → this is the first run for this company. Do the full pipeline below.
   - `up_to_date` → nothing has changed since the last run. Reuse
     `research_cache/<company_slug>/report.md` as-is. If the user only supplied a new
     price for the valuation section, rerun `scripts/forward_pe.py` alone with the
     cached revenue-guidance/margin/shares inputs (stored in
     `research_cache/<company_slug>/bullets.json`) — do not refetch or reprocess
     anything else.
   - `new_quarter` → only fetch and parse the new concall/results (steps 1-3 of the
     source pipeline below). Do NOT reprocess transcripts already sitting in
     `research_cache/<company_slug>/raw/`. Update the Near/Medium/Long Term bullets
     from the new quarter (they supersede the old ones — this is a forward outlook,
     not a running log), but only *append* one new entry to
     `guidance_history.json` via `scripts/guidance_tracker.py` rather than rebuilding
     the guidance-reliability history from scratch. **This is the main token-saving
     lever in the whole pipeline — see `reference/source_playbook.md`'s "Regenerating
     for a new quarter" section for the exact checklist of what to fetch (new concall +
     investor presentation + last 1-2 screener.in columns) vs. what to carry forward
     unchanged from the cached `report.md`** (manufacturing locations, certifications,
     TAM, entry barriers, peer identities, value chain description — none of that
     changes quarter to quarter, so don't re-derive it).
   - **Lookback window is fixed at 6 months (last 2 quarters) for every query, always**
     — this is a standing framework default, not a per-report decision. It applies to
     `guidance_tracker.py report` (its default `--lookback` is already 2) and to
     `check_freshness.py`'s `--lookback-months` (already defaults to 6). Only change
     either value if the user explicitly asks for a longer or shorter history in that
     specific request — never default to anything else.
3. After finishing a run (full or incremental), call
   `python3 scripts/check_freshness.py <company_slug> --mark-processed "<label>" --price <price>`.

## Source pipeline (only run the parts Step 0 says are needed)

**Get the source documents.** Read `reference/source_playbook.md` for exactly which
tool to use for which source (screener.in, BSE/NSE, industry/peer sources, technicals
provider). In short: `WebSearch`/`mcp__workspace__web_fetch` for screener.in and PDF
concalls/presentations/annual reports; escalate to Claude in Chrome only if a page is
JS-rendered and web_fetch returns an empty shell. Never write a raw `curl`/`requests`
fetch script — this sandbox's network is allowlisted and direct calls to arbitrary
domains fail with a proxy 403. If the user has uploaded documents, use those instead
of fetching. Save whatever raw text/PDF you obtain to
`research_cache/<company_slug>/raw/` before processing it.

**Extract text from PDFs.** `python3 scripts/pdf_to_text.py <input.pdf> <output.txt>`
— local, no network. For annual reports, grep for the MD&A/outlook section heading
first and only extract that page range instead of the whole 100-300 pages.

**Pre-filter to candidate quotes.** `python3 scripts/extract_theme_quotes.py
<transcript.txt> <out.json>` buckets forward-looking lines into near/medium/long-term
candidates. Read `out.json`, not the transcript. If a bucket looks thin, `grep -n -C3`
the transcript for more context around one candidate instead of reading the whole file.

## Building each section

**Company Summary** — a short paragraph right under the title, before Near Term: what
the company does, sector, listing history, exchange, market cap. Pull from
screener.in's "About" text, the concall's opening remarks, or the annual report
business overview per `reference/report_format.md` — never invent it.

**Value Chain Positioning** — a short paragraph right after Company Summary: what the
company buys/from whom upstream, what it sells/to whom downstream, and which tier it
occupies (component maker, OEM, brand, distributor, etc.), per
`reference/report_format.md`. Source from the investor presentation's business-model
slide, concall descriptions of customers' customers, or the annual report's industry
overview — never invent a multi-tier chain from a one-line description. **Always
follow it with a vertical stacked-box flow diagram** in a fenced code block in the
markdown (ASCII only, for portability), rendered as styled boxes via `html_helpers.
flow_diagram()` in the visual PDF — see `reference/report_format.md`'s layout and
width-safety reasoning for why the stack stays vertical either way.

**Situation Classification** — right after Value Chain Positioning, before Near Term:
one short paragraph stating which broad situation the company is in right now
(turnaround / steady compounder / cyclical / structural growth / structural decline, or
an explicit mix), with the evidence for that call, per `reference/report_format.md`.
This is a judgment call made from what's already gathered, not a separate fetch — but
make it explicitly and re-examine it on every regeneration rather than carrying last
run's classification forward unchanged. Drives the cover-page situation badge.

**Near/Medium/Long Term outlook** — from the candidate quotes JSON, pick the
strongest 2-3 verbatim-quoted bullets per horizon per `reference/report_format.md`.
Every quote must be checked as an exact substring of the source text — do not
truncate a quote and add punctuation that isn't in the original (that fabricates a
sentence ending). If in doubt, `grep` the exact phrase back against the raw
transcript before finalizing.

Every bullet also gets a **status pointer** — `[Pending]`/`[On Track]`/`[Delivered]`/
`[Delayed]`/`[Missed]` — right after the headline. Log the underlying item into
`guidance_history.json` via `scripts/guidance_tracker.py add-guidance` with your own
`--status` assessment (numeric metric or not — the `--value-cr` flag is optional for
milestone-style items). When a later concall revises something already logged, use
`--supersedes-id` to link the revision so the item's full evolution can be
reconstructed, the same way a human analyst reads back through a company's guidance
history. Run `scripts/guidance_tracker.py <slug> report` and use its status/evolution
output to set each bullet's pointer — this is not lookback-limited, since an item's
full history (not just the latest quarter) is what determines "on track" vs. freshly
asserted.

**Marquee & Niche Customers** — pull named clients from the investor presentation's
customer slide, annual report business overview, or explicit concall mentions per
`reference/source_playbook.md`. Only name a customer a source document actually names.
Capture any disclosed customer-concentration % here too. Then, per named customer, do
one targeted search for that customer's own public guidance/capacity plans that would
corroborate future demand (per `reference/source_playbook.md`) — state plainly, per
customer, whether anything was found. For an exporting company, a quick check of an
export-shipment-data aggregator (Volza/Seair/ImportGenius/Zauba — per
`reference/source_playbook.md`) can corroborate a named customer or surface one the
company hasn't itself named — label anything found this way as third-party shipment
data, distinct from company disclosure. **Always a bullet list in the visual PDF, one
point per customer — never a merged paragraph.**

**Capex, Milestones & Certifications Timeline** — build a chronological table (achieved
first, then planned) from the investor presentation's capex slide, concall Q&A timing
color, BSE/NSE Regulation 30 announcements, and the annual report MD&A. Use whatever
date precision management actually gave — a horizon like "H2 FY27" is fine if that's
all that was stated; don't invent a specific date. This is also the roll-up table for
every other future-dated commitment surfaced anywhere else in the report — a
TAM-capture horizon, a new-geography/segment entry date, a product-launch or
qualification-cycle date, a JV/subsidiary milestone — add each as its own row with a
one-line cross-reference back to the section carrying the fuller context, rather than
limiting this table to capex/certifications alone.

**CDMO Pipeline** — only if the company describes itself as a CDMO/CRAMS business.
Pull the Phase 1/2/3/Commercial molecule counts from the investor presentation's
pipeline slide or concall updates. Never attempt to identify molecule/sponsor names —
report counts and therapeutic-area splits only, as disclosed. For a non-CDMO company,
skip this section with no heading and no mention (the one section allowed to be
silently absent, since it's simply not applicable rather than data that's missing).

**Financial Performance Summary** — build the YoY revenue/margin/PBT/PAT table
straight from the screener.in quarterly/annual results tables already fetched; this is
a multi-year trend and is explicitly exempt from the 6-month lookback default that
applies elsewhere in the report. **Table only in the visual PDF — no revenue/profit
chart by default** (see `reference/report_format.md`'s Assembly section). While the
balance sheet is in front of you for this section, also run the **balance sheet
anomaly check**: compute debtor days per year (receivables ÷ revenue × 365) and look
for a jump, check whether cash stays thin relative to short-term borrowings across
multiple years, and scan for any goodwill write-off, negative net worth, or an
unexplained spike in "other assets"/"loans and advances." State whatever you find, or
state explicitly that nothing anomalous was found — don't skip the check silently.

**Segment-wise Performance** — only if the company actually reports revenue by
segment (Ind AS 108 note in the annual report, a segment breakout on screener.in, or
management's own segment commentary). Always a markdown table, never prose — if the
company discloses splits on more than one basis (product line vs. end-market) or for
more than one period, render one table per basis/period rather than blending them.
Check specifically for an **exports vs. domestic** split (often disclosed informally on
the concall/investor presentation even when there's no formal geography segment note)
and render it as its own table alongside any product-line/end-market table if found. If
it's a single-segment business, say so and skip the table rather than forcing a
product/SKU breakdown that wasn't reported as a segment.

**Order Book** — only if the company discloses an order book/backlog figure. Always a
markdown table with the as-of date, since this is a point-in-time snapshot, not a
period figure. If disclosed on more than one basis (standalone vs. consolidated, a
JV/subsidiary's order book reported separately, or composition broken out by both
order-type and end-market), show each as its own row/table rather than blending.
Include an **exports vs. domestic** composition breakdown if disclosed, the same way as
any other composition basis. A same-period order **inflow** figure (new orders booked
in the quarter) is a different metric from the order book level — note it in one line
under the table if disclosed, don't fold it into the order-book number itself.

**Manufacturing Locations & Physical Assets** — only if plant/facility locations are
actually disclosed. List each one (city/state, owned/leased, area if given, what it
houses) from the annual report's Property, Plant & Equipment note, the investor
presentation's facilities slide, and concall Q&A about plant locations. A registered
office alone is not a manufacturing site — don't infer one from the other. **Always a
bullet list in the visual PDF, one point per location — never a merged paragraph.**
While sourcing this section, also check **raw material import dependency**: is the
company's key input imported, domestic, or mixed, and what % and country if disclosed
(primary source: the annual report's "indigenous vs. imported raw material consumed"
note per `reference/source_playbook.md`) — cross-reference to Key Risks if imports are
material. If the annual report isn't accessible, an export/import shipment-data
aggregator can show actual inbound shipments as a partial substitute (per
`reference/source_playbook.md`). Say so explicitly if no company-specific figure was
found. Also check the investor presentation's "Awards & Accolades" slide (or, quickly,
a WebSearch) for anything genuinely noteworthy to fold into the Capex/Milestones
Timeline as an achieved milestone — don't force this if there's nothing there.

**Capacity Utilization & Headroom** — only if a utilization % (or the installed
capacity + units-produced inputs to derive one) was disclosed, usually in concall Q&A
or an investor presentation's operations slide. Run `scripts/capacity_utilization.py`
and reproduce its high-utilization flag verbatim if utilization is already at/above
85%. If a post-capex revenue figure already surfaced elsewhere (Capex/Milestones
timeline or an outlook bullet), pass it via `--post-capex-max-revenue-cr` so the
section shows before-capex and after-capex figures side by side, plus what the capex
itself unlocks — don't derive a new number if management already gave one. **Table
only in the visual PDF — no before/after chart by default.**

**Total Addressable Market** — only if an actual TAM figure (not just a growth rate)
was disclosed, per `reference/report_format.md`. Break it down by segment if
management did, state the disclosed time horizon, and flag if the figure looks dated
(>~2 years old). If a specific TAM-capture target has its own timeline, that also
becomes a status-pointer-tagged Long Term bullet — cross-reference, don't duplicate.

**Valuation (Forward PE)** — only if revenue guidance was found above. Pull current
price, shares outstanding (equity capital ÷ face value), and trailing PAT/revenue from
the screener.in fetch already done. Run `scripts/forward_pe.py` with the guided
revenue (and guided margin if management gave one, else trailing margin flagged as an
assumption). If the user supplied their own price, pass that instead and label it.
Also pull the company's own **historical median PE** from a secondary aggregator
(Trendlyne/Tijori/MoneyWorks4Me — see `reference/source_playbook.md`) and add it as a
row in the same table, so the forward multiple has a same-company historical reference
point, not just a bare number. Lead with the summary table per
`reference/report_format.md`, followed by one short sentence — not a full paragraph
restating every input.

**Industry Tailwinds/Headwinds** — per `reference/source_playbook.md`, search outward
(peers, sector bodies, rating-agency sector notes), 2-4 bullets, one source each. A
quick LinkedIn/X check on the company's own official page (per
`reference/source_playbook.md`) can also surface something genuinely noteworthy not
yet in any filing — a leadership hire, an order win, a facility inauguration. Fold a
real finding into whichever section it actually belongs to (this one if sector-wide,
Marquee Customers if customer-related, Key Risks if it's a negative development) rather
than forcing a dedicated heading — and don't mention the check at all if nothing
noteworthy turned up.

**Competitive Positioning: Peer Comparison, Entry Barriers & Product Criticality** —
pull 3-5 direct peers from screener.in's Peers tab or the company's own concall
references to competitors, per `reference/source_playbook.md`. Build the comparison
table (IP/technology moat, niche/marquee customers, certifications, other
differentiator) including the reporting company as its own row, then state plainly
which side leads on each factor — facts only, no ranking score. Cover entry barriers
(capital intensity, certification/qualification lead times, customer design-in cycles,
proprietary know-how, switching costs) and product criticality (safety/mission-critical
vs. discretionary/substitutable) from the same sources plus the company's own framing
of its product's role — never invent a barrier or criticality claim the sources don't
support.

**Technical Snapshot** — pull a pre-computed technicals summary (moving averages,
RSI, support/resistance) from a technicals provider per the playbook; don't compute
indicators from scraped OHLC data yourself. Timestamp it. **Render as normal body
text in the visual PDF, not the small italic `.note` style** — this section carries
real numbers a reader needs to read comfortably, not a one-line caveat.

**Promoter/Governance Track Record** — this reuses the same `guidance_history.json`
already populated for the outlook-bullet status pointers above; no separate logging
step needed here beyond adding this quarter's actual-vs-prior-guidance via
`add-actual` if this quarter's results closed out a previously guided numeric metric.
Run `scripts/guidance_tracker.py <company_slug> report` (default lookback is 2
quarters / 6 months for the guidance-vs-actual comparisons — the standing default,
don't override it) and reproduce its flag verbatim if it found a pattern of misses.
Add promoter holding trend / pledge / auditor flags from the screener.in fetch —
**render the shareholding-pattern trend as a `data_table()` in the visual PDF, no
chart by default.**

Then cover **promoter fund raises** (preferential equity, warrants, NCDs/debentures,
term loans, promoter loans/guarantees) per `reference/source_playbook.md`'s sourcing
steps: check BSE/NSE announcements and credit-rating rationale for any raise not
already in `research_cache/<company_slug>/fundraise_history.json`, log new ones via
`scripts/fundraise_tracker.py add-raise` — **including named allottees via `--investors`
whenever the allotment notice or a news writeup actually names them** (recognizable
HNIs, FPIs, mutual funds), not just the promoter/public/institution category — update
any pending warrant's status via
`update-status` if it has since converted or lapsed, then run
`scripts/fundraise_tracker.py <company_slug> report` (add `--cmp <price>` to show issue
price vs. current price) and reproduce its output — and any LAPSED-warrant flag,
verbatim — in the Promoter Fund Raises sub-section per `reference/report_format.md`.
**Table only in the visual PDF, including the named-investor column — no donut chart
by default.** Unlike guidance, this is not lookback-limited: show every raise on
record, not just the last 6 months.

Then check **credit ratings** for every report (not only companies with visible debt —
see `reference/source_playbook.md`'s "Credit rating agencies" section for exactly which
agencies to search and what to pull from a rationale). Log any rating action not
already in `research_cache/<company_slug>/rating_history.json` via
`scripts/rating_tracker.py add-rating`, stating `--action` yourself based on what the
rationale says (reaffirmed/upgrade/downgrade/outlook revised/withdrawn/first-time —
don't infer it purely from comparing rating notches). Run
`scripts/rating_tracker.py <company_slug> report` and reproduce its downgrade/
negative-outlook flag verbatim if it fires, in the Credit Rating Snapshot sub-section
per `reference/report_format.md`. If genuinely no rating rationale can be found for the
company from any agency, say so explicitly rather than omitting the sub-section
silently. Like fund raises, this is not lookback-limited — show the full rating history.

Then check for **litigation** on every report (see `reference/source_playbook.md`'s
"Legal & litigation" section — the annual report's Contingent Liabilities note is
usually the richest source and may already be fetched). Log any case not already in
`research_cache/<company_slug>/litigation_history.json` via
`scripts/litigation_tracker.py add-case`. Pay particular attention to a case described
as "dismissed" or "decided in the company's favor" — check whether an appeal window or
pending higher-forum appeal is also mentioned, and if so log it as
`--status dismissed_appealable`, not `closed_final`. Run
`scripts/litigation_tracker.py <company_slug> report` and reproduce its reopen-risk
flag verbatim if it fires, in the Legal & Litigation sub-section per
`reference/report_format.md`. If genuinely no litigation is found, say so explicitly.
Not lookback-limited, same as fund raises and ratings.

**Investment Thesis Summary** — after Promoter/Governance, synthesize the specific,
falsifiable case from what's already gathered: outlook bullets currently `[On Track]`/
`[Delivered]`, Competitive Positioning strengths, TAM headroom, capacity headroom,
independent third-party corroboration (customer guidance, a rating reaffirmation/
upgrade). Per `reference/report_format.md` — **if the research genuinely doesn't
support a real thesis, say so plainly instead of padding it out**; that's a legitimate,
useful conclusion, not a failure to produce one.

**Key Risks (Red Flags / Bear Case)** — 3-5 bullets pulling from what's already been
gathered above (business/execution, financial, governance, macro) — never invented.
Carry through any credit-rating downgrade or negative/watch-negative outlook flagged
above, and any dismissed-but-appealable or ongoing litigation with a disclosed amount;
give each at least as much weight as a guidance miss, since these are independent,
third-party or externally-verifiable facts. Also carry through a high-utilization flag
from Capacity Utilization (growth capped until new capacity comes online) and any
material customer-concentration figure from Marquee & Niche Customers, if either
applies. **This section is mandatory even when the Investment Thesis Summary above is
strongly positive** — don't let a good bull case soften the bear case.

**Verdict** — one short paragraph closing the report: the situation classification, the
single strongest piece of evidence, the single biggest open question/risk, and an
honest confidence level ("well-evidenced but early" / "speculative" / "not enough here
for a real thesis" are all legitimate). Per `reference/report_format.md` — pick whatever
the evidence actually supports, not the best-sounding closing line.

**Sources** — a numbered, hyperlinked list of every URL cited anywhere in the report,
each with a short note on what it supports. This is the reader-facing surface of the
same traceability already kept in `quotes.json` — reuse that mapping rather than
reconstructing it from scratch.

## Save and cache

Save every deliverable — **always both** the `.md` report **and** a PDF, every run,
without waiting to be asked — to `output/<company_slug>/` (e.g.
`output/td_power_systems/TD_Power_Systems_report.md` and
`output/td_power_systems/TD_Power_Systems_report.pdf`), **not** the workspace root.
This keeps user-facing deliverables separate from the skill's own working state in
`research_cache/`. Create the `output/<company_slug>/` folder if it doesn't exist yet.

**PDF generation is a mandatory last step of every run (full or incremental,
including a freshness-check-only refresh where the report body is reused
unchanged)** — never skip it and never treat it as optional or user-request-gated.

**Primary path — visual PDF via WeasyPrint.** Follow
`reference/report_format.md`'s "Assembly" section: build the HTML body with
`scripts/html_helpers.py` (cover, cards, tables, timeline, verdict box, sources list —
`data_table()` is the workhorse here, used far more than any chart) styled by
`assets/report_style.css`, then render with `python3 -m weasyprint report.html
<output_dir>/<name>_report.pdf`. `scripts/charts.py` (matplotlib) is available but
**opt-in, not default** — only call it if the user specifically asks for a visual/
chart version of a section. Install once if missing: `pip install weasyprint
matplotlib --break-system-packages`. Verify the rendered PDF before delivering it —
`pdftoppm -jpeg -r 120 <name>_report.pdf page` and check a few pages for overflowing
tables, unreadable font sizes, or dead whitespace (a common cause: a chart PNG that
wasn't saved with tight bounding-box cropping — see `scripts/charts.py`'s
`bbox_inches='tight'` usage — or a single chart wrongly wrapped in `chart_row()`).
Delete any intermediate chart PNGs and `report.html` once verified; only the final PDF
and `report.md` belong in `output/<company_slug>/`.

**Legacy fallback — reportlab, text-only.** If WeasyPrint genuinely can't be installed
in a given environment, run `python3 scripts/report_to_pdf.py <output_dir>/<name>_report.md
<output_dir>/<name>_report.pdf --title "<Company Name> - Research Report"` instead —
markdown-to-PDF with no charts/cards/badges, but it still fixes the ₹-glyph issue and
strips any internal `scripts/*.py` mention that slipped into the markdown as a backstop.
Never let a missing dependency block delivery entirely; fall back rather than skip the
PDF. Confirm both `.md` and `.pdf` exist in `output/<company_slug>/` before telling the
user the report is ready, whichever path was used.

Save/update `research_cache/<company_slug>/quotes.json`, `bullets.json`,
`guidance_history.json`, `fundraise_history.json`, `rating_history.json`,
`litigation_history.json`, and `report.md`, then mark freshness state per Step 0.3.

## Accuracy discipline

This is a personal research document, not a distributed advisory product — the report
freely states a situation classification, a synthesized investment thesis, and a
verdict with a directional read, per `reference/report_format.md`. No compliance
hedging, no refusal to give a view. The one discipline that still matters is **never
manufacturing evidence**: every material fact traces to a cited source and date, every
quote is verbatim, unverified management claims are flagged as such ("management
states X — not yet corroborated by an independent filing"), and if the research
genuinely doesn't support a real thesis, the Investment Thesis Summary and Verdict say
so plainly rather than padding it out. Any directional read on valuation (Forward PE)
stays tied to a specific cited comparison (peers, history, growth) rather than floating
free as a bare adjective — this is about the thesis being real, not about softening it.
