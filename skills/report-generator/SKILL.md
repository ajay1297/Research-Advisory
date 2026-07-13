---
name: report-generator
description: >
  Generate or refresh a visual, infographic-style investment-thesis PDF (a Company
  Summary with a headline stat card grid, a Value Chain Positioning writeup with a flow
  diagram, and an early situation classification — turnaround/compounder/cyclical/
  structural growth/structural decline — up front; Near/Medium/Long Term outlook backed
  by sourced management quotes, each tagged with a status pointer — Pending/On Track/
  Delivered/Delayed/Missed — tracked across concalls; marquee/niche customers plus their
  own disclosed guidance where corroborating — including, for a marquee customer that
  is itself publicly listed on any exchange (India, US, UK, EU, or elsewhere), the last
  4 quarters of that customer's own concalls/earnings calls for capacity/demand
  corroboration — and corroborated where relevant by export-shipment data; a capex,
  milestones (including awards) and certifications
  timeline that also rolls up every other future-dated commitment disclosed elsewhere in
  the report; a CDMO molecule-pipeline snapshot where applicable; multi-year YoY revenue/
  margin/PBT/PAT trend table plus a balance-sheet anomaly check; segment-wise revenue
  breakdown where reported, including an exports vs. domestic split where disclosed;
  order book with basis and composition breakdown (including exports vs. domestic where
  disclosed); manufacturing locations and physical assets (plants, buildings, notable
  machinery) as bullet points, plus raw material sourcing (domestic vs. imported %,
  country-wise breakdown of any imported portion where disclosed, and export-shipment/
  customs data as a corroborating check); capacity utilization measured in the
  industry's own physical unit (fiber-km, MT, MW, units/annum, etc. — not a bare %),
  flagging shared multi-purpose capacity pools, with before-and-after-capex potential
  (tabled); total addressable market where disclosed; forward PE with a summary table
  (including the company's own historical median PE) and an evidenced directional read
  against peers/history where supportable; third-party broker/agency research
  (e.g. Nuvama), when the user supplies a report, folded inline wherever it's
  relevant rather than into a separate section, every such point carrying an
  inline `[BROKER_DDMMYYYY]` attribution tag; industry
  tailwinds/headwinds; a peer
  comparison table on IP/technology moat, niche/marquee customers, and certifications; a
  dedicated MOATs section (entry barriers, IP/technology moat, product criticality,
  switching costs) as bullet points; a technical snapshot rendered as a table or bullet
  points, never prose; promoter/governance track record — including a tabled
  shareholding-pattern trend, named preferential allottees, warrants, and debt the
  promoter has raised, independent credit-rating actions from CRISIL/ICRA/CARE/India
  Ratings/Acuite/Brickwork, and ongoing or reopenable litigation; a synthesized,
  evidenced Investment Thesis Summary as bullet points; a mandatory Key Risks/Red Flags
  section even in a bullish report; a one-paragraph Verdict on confidence level; and a
  numbered Sources list) for an Indian listed company from its concall transcript,
  investor presentation, annual report, and screener.in data. Activate when the user
  says "research <company>",
  "generate a report on <company>", "regenerate/update/refresh <company>'s report",
  "analyse <company>'s concall", "what's the story with <company/ticker>", "build a
  thesis on <company>", or shares/references concall transcripts, investor
  presentations, or annual reports for a specific company. Personal research document —
  sourced and evidenced.
---

# Report Generator

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
Locations & Physical Assets **(bullet list, plus Raw Material Sourcing — domestic vs.
imported %, country-wise breakdown of any imported portion where disclosed, and an
Export Shipment/Customs Data check)**, Capacity Utilization & Headroom **(table,
reported in the industry's own physical unit — fiber-km, MT, MW, units/annum, etc.,
never a bare % alone — flagging any shared multi-purpose capacity pool)** (before *and*
after planned capex, where disclosed), Total Addressable Market (where disclosed),
Valuation (Forward PE, led by a summary table that also includes the company's own
historical median PE, with an evidenced directional read against peers/history where
supportable), Industry Tailwinds/Headwinds, Competitive Positioning (peer comparison
table on IP/technology moat, niche/marquee customers, and certifications), **MOATs
(bullet points: entry barriers, IP/technology moat, product criticality, switching
costs)**, Technical Snapshot **(table or bullet points, never prose — readable
body-text size, not caption-sized)**, Promoter/Governance Track Record (guidance
reliability + a **tabled** shareholding-pattern trend + promoter fund raises **(table,
with named allottees where disclosed)**: preferential equity, warrants, NCDs/debt +
independent credit-rating actions from CRISIL/ICRA/CARE/India Ratings/Acuite/Brickwork +
ongoing or reopenable litigation), Investment Thesis Summary **(bullet points — a
synthesized, evidenced bull case — or an honest statement that one doesn't hold up)**,
Key Risks / Red Flags (mandatory, even in a bullish report), Verdict (one short
paragraph on confidence level), and Sources (numbered, hyperlinked). See
`examples/venus_pipes_report.md` for the outlook-section style and
`reference/report_format.md` for the full spec including the Company Summary, Value
Chain Positioning, the status-pointer rule, the visual-PDF Assembly pattern, and the
nineteen sections after the outlook.

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

- `research <Company Name>` — new company, first run. Goes through the full pipeline
  (Step 0 reports `no_state`).
- `generate a report on <Company Name>`
- `analyse <Company Name>'s concall`
- `regenerate <Company Name>'s report` / `refresh <Company Name>'s report` /
  `update <Company Name>'s report` — for an **already-generated** company. This reuses
  Step 0's freshness check (`up_to_date` or `new_quarter`) rather than re-running
  everything — only what's actually changed since the last run gets refetched, and
  unchanged sections carry forward from the cached `report.md`. This is the default,
  cheap path for "update" requests — don't treat plain "regenerate/refresh/update"
  as an instruction to rebuild from scratch.
- `regenerate <Company Name>'s report from scratch` / `rebuild <Company Name> from
  scratch` / `redo <Company Name>'s report from scratch` / `ignore the cache and redo
  <Company Name>` — also for an already-generated company, but explicitly asking to
  bypass the cache: call `scripts/check_freshness.py <slug> --force`, which returns
  `force_full`, and refetch every source document fresh and rebuild every section
  rather than carrying anything forward from the cached `report.md`. Tracker histories
  (`guidance_history.json`, `fundraise_history.json`, `rating_history.json`,
  `litigation_history.json`) are cumulative real-world records, not cache — they are
  never wiped, from-scratch or not; keep appending to them as usual. Only go down this
  path when the user's phrasing explicitly says "from scratch" / "rebuild" / "ignore
  the cache" / "redo entirely" — plain "regenerate"/"refresh"/"update" always means the
  cheap incremental path above.
- `rerun for <Company A> and <Company B>` — works for multiple companies in one
  request; each is processed independently through the same pipeline (and each can be
  a new company, an incremental update, or a from-scratch rebuild independently).
  **Default to sequential execution, one company fully finished (both `.md` and
  `.pdf` confirmed on disk) before the next starts.** This guarantees every report in
  the batch renders through the same verified WeasyPrint environment and comes out
  looking identical — running companies as separate parallel background agents has
  produced mismatched output before (one agent's environment silently missing
  WeasyPrint fell back to the plain ReportLab renderer while a sibling agent's didn't,
  so two reports from the same request looked visually inconsistent). Only run
  companies in parallel if the user explicitly asks for it ("in parallel", "at the
  same time") — and if so, verify WeasyPrint is importable in the shared environment
  *before* dispatching any of them (see the Assembly section below), so a dependency
  gap can't cause the same silent drift.
- `what's the story with <Company/Ticker>` / `build me a thesis on <Company Name>` /
  `do a deep dive on <Company Name> — is it a buy?` / `research <Company Name> for a
  turnaround thesis` — informal, non-jargon phrasing also triggers this skill; the user
  doesn't need to say "report" or name a section.

If you've uploaded a concall transcript, investor presentation, annual report PDF, or
a third-party broker/agency research report (e.g. Nuvama, Motilal Oswal, ICICI
Securities) directly instead of naming a company, that also triggers this skill —
sourcing then prefers your uploaded documents over fetching (see "User-uploaded
documents" in `reference/source_playbook.md`). A broker/agency report specifically has
no dedicated section of its own — each fact from it gets folded directly into
whichever existing section it belongs to (Valuation, Industry Tailwinds/Headwinds,
Investment Thesis Summary, Key Risks, etc.), with every such point carrying an inline
`[BROKER_DDMMYYYY]` tag (see `reference/report_format.md`'s "Broker / agency research —
inline-tagged, no dedicated section") so it's never mistaken for the pipeline's own
independently-sourced numbers even without a physically separate section.

**If no company was named** (e.g. just "research", "generate a report", "update the
report" with nothing to identify who) — don't guess a company, don't reuse a company
from earlier in the conversation unless the request is clearly a continuation of that
same thread, and don't start any part of the pipeline. Ask a single direct question
back: which company (name or ticker)? If the user has previously generated reports
this session, listing 2-3 of those as examples in the question is fine, but the user
still has to name one — don't auto-pick the most recent one for them.

There is no separate "setup" step and no config to edit — every run is self-contained
and named by company. **All working state and deliverables live outside this plugin
directory, under `~/.report-generator/`** — never inside the plugin's own folder.
Using this skill should never create, modify, or delete a single file under the
plugin's install location; every file this skill writes goes to `~/.report-generator/`
instead. Two companies' data never mix within that folder: each gets its own
`~/.report-generator/research_cache/<company_slug>/` working state and
`~/.report-generator/output/<company_slug>/` deliverable folder, keyed off a slug
derived from the company name (lowercase, underscores — e.g. "TD Power Systems" ->
`td_power_systems`). Create `~/.report-generator/` (and the two subfolders) the first
time they're needed if they don't already exist.

Do not read `reference/report_format.md` or `reference/source_playbook.md` in full
until you actually need them (step 2+ below). Read `examples/venus_pipes_report.md`
once, when drafting.

## The core rule: never load raw source documents into context

Concall transcripts run 15-40 pages, investor decks 20-50 slides, annual reports
100-300 pages. Every step below exists to avoid reading these directly. Always go
through `scripts/`, never paste a full transcript/PDF into your own reasoning.

## The other core rule: never drop anything silently

Everything below is optimized for token/time efficiency — grepping instead of
reading, caching instead of refetching, skipping what a freshness check says is
unchanged. None of that is license to let a fetch failure, timeout, rate limit,
extraction gap, or skipped section pass without comment. If something couldn't be
gotten, couldn't be verified, or was cut short for any reason, **that gets stated in
the report, in the section it affects** — see the dedicated "Never drop anything
silently" section near the end of this file for the full rule and examples. Keep it
in mind at every step below, not just when assembling the final report.

## Token discipline — this pipeline is read-heavy, don't read more than needed

- **Grep before you Read.** Once a PDF is converted to `.txt`, don't `Read()` it
  top-to-bottom — `grep -n "<keyword>" -C3` for the section you need (order book,
  capex, margin guidance, etc.) and only `Read()` the specific line range that surfaces.
  `extract_theme_quotes.py`'s candidate JSON exists precisely so you never need to read
  the full transcript for the outlook bullets.
- **When grep comes up thin, use `semantic_search.py` before resorting to a full
  Read.** Grep only finds exact keyword matches — a section can exist and still be
  missed because the report phrases it differently than the keyword you guessed (e.g.
  you grep "backward integration" but the annual report only ever says "manufactures
  its own preforms in-house"). `python3 scripts/semantic_search.py <text_file>
  "<natural language query>" --top-k 5` runs a BM25-ranked relevance search over the
  document and returns the most relevant chunks with their line ranges, so you can
  `grep`/`Read` that exact range for full context. The index is chunked and cached
  alongside the source file (`<text_file>.bm25.pkl`), so re-querying the same document
  — including across a `new_quarter` refresh that reuses cached raw text — costs
  nothing beyond the first build. This is a lexical relevance ranker (BM25), not a
  dense-embedding model — it has no external API dependency and nothing to install
  beyond the lightweight `rank_bm25` package (`pip install rank_bm25
  --break-system-packages` once if missing), which is why it's the default semantic
  fallback rather than something heavier. Still prefer grep first when you already
  know the right keyword — it's faster and exact; reach for `semantic_search.py` when
  a keyword search plausibly missed something because of phrasing, not as the default
  first move for every section.
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
2. If the user's request explicitly asked for a from-scratch rebuild (see "How to
   trigger" above), skip straight to running
   `python3 scripts/check_freshness.py <company_slug> --force` — this returns
   `force_full` regardless of the label, and every source gets refetched/rebuilt as
   described there. Otherwise run
   `python3 scripts/check_freshness.py <company_slug> --latest-seen "<label>"`.
   - `no_state` → this is the first run for this company. Do the full pipeline below.
   - `force_full` → user explicitly asked to rebuild from scratch. Refetch every
     source document and rebuild every section — do not reuse anything from the
     cached `report.md`. Tracker histories (guidance/fundraise/rating/litigation
     JSON) are not wiped — keep appending to them as usual, same as any other run.
   - `up_to_date` → nothing has changed since the last run. Reuse
     `~/.report-generator/research_cache/<company_slug>/report.md` as-is. If the user only supplied a new
     price for the valuation section, rerun `scripts/forward_pe.py` alone with the
     cached revenue-guidance/margin/shares inputs (stored in
     `~/.report-generator/research_cache/<company_slug>/bullets.json`) — do not refetch or reprocess
     anything else.
   - `new_quarter` → only fetch and parse the new concall/results (steps 1-3 of the
     source pipeline below). Do NOT reprocess transcripts already sitting in
     `~/.report-generator/sources/<company_slug>/`. Update the Near/Medium/Long Term bullets
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
   - **Standard sourcing depth is the last 2 annual reports and last 6 quarters of
     concalls — this is the default for every `research <company>` / first-time run,
     not a special request.** This applies to `guidance_tracker.py report` (default
     `--lookback` is 6) and to `check_freshness.py`'s `--lookback-months` (default 18,
     ≈6 quarters). It exists specifically so the Promoter/Governance Track Record and
     Situation Classification sections have real multi-quarter evidence for "does
     management walk the talk" and "what has genuinely changed about this business"
     rather than 1-2 isolated data points — see `reference/source_playbook.md`'s
     "Standard sourcing depth" section for exactly what to fetch and why. The
     Near/Medium/Long Term outlook bullets themselves still reflect *current* forward
     guidance regardless — this depth feeds the historical/governance read, not the
     forward-looking bullets. **On a `new_quarter` refresh, this does not mean
     re-fetching 6 quarters again** — per the incremental-regeneration rule below,
     only the new quarter gets fetched; the rolling 6-quarter window is maintained by
     what's already cached in `sources/` from prior runs plus the new addition. Only
     go narrower than this default if the user explicitly asks for something
     lighter/faster in that specific request.
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
`~/.report-generator/sources/<company_slug>/` before processing it.

**Extract text from PDFs — always extract the whole document, never just a guessed
section range.** `python3 scripts/pdf_to_text.py <input.pdf> <output.txt>` — local, no
network. An annual report's sections you need are scattered across the *entire*
document (MD&A near the front, but segment/PP&E/litigation/shareholding notes and the
contingent-liabilities note often sit 100+ pages further back) — extracting only a
guessed page range risks silently missing something the report needs later, and
there's no cheap way to notice the gap after the fact. Full extraction, then grepping
the resulting `.txt`, is the safe default; grep on an already-extracted text file costs
milliseconds regardless of document length, so narrowing what gets *read* is not where
the token/time savings should come from.

For a **large annual report (roughly 150+ pages)** where single-process extraction is
slow (a 380-page report takes ~50s with `pdf_to_text.py`), use
`python3 scripts/pdf_to_text_parallel.py <input.pdf> <output.txt> [--workers N]`
instead — it splits the page range into contiguous chunks that together cover every
page (no gaps, no overlap), extracts them concurrently, and verifies every chunk
came back before writing anything, so the output is the same full-document text,
just faster (~45% faster on an 8-core machine for a 380-page report, and bigger wins
when several of a company's annual reports are extracted in the same run — kick off
all of them as concurrent background processes rather than one at a time). If it
ever fails to account for a chunk it refuses to write a partial file and errors
instead — fall back to `pdf_to_text.py` in that case rather than accepting a gap.

`pdf_to_text.py`'s `--pages START-END` flag still exists for one narrow, safe use:
a **quick scouting pass** — e.g. extracting just the first 5-10 pages to read a
table of contents and locate a named section's page number before committing to
full extraction, or re-extracting one already-located page range at higher fidelity
after the full-text grep already told you where it is. Never use `--pages` as a
substitute for the full-document extraction above.

**Pre-filter to candidate quotes.** `python3 scripts/extract_theme_quotes.py
<transcript.txt> <out.json>` buckets forward-looking lines into near/medium/long-term
candidates. Read `out.json`, not the transcript. If a bucket looks thin, `grep -n -C3`
the transcript for more context around one candidate instead of reading the whole file.

**Naming and placement note — don't confuse this per-transcript output with the
curated `quotes.json` in `research_cache/`.** Name this script's output
`<label>_candidate_quotes.json` (e.g. `q4fy26_candidate_quotes.json`) — it's a raw,
over-inclusive, unfiltered dump straight from one document (heuristic on purpose; the
model does the real curation afterward). Unlike the `.txt`/`.pdf` extraction it's
derived from (which stays in `sources/<company_slug>/` since a full annual report's
text alone can run 1MB+), this candidate-quotes JSON is genuinely small (tens of KB
even across several quarters) — save it to
`~/.report-generator/research_cache/<company_slug>/candidate_quotes/<label>_candidate_quotes.json`
instead, so it travels with the rest of the lean, shareable state rather than the
bulky `sources/` material. This is a **different file** from the single `quotes.json`
(no per-quarter label, no `candidate_quotes/` subfolder) also in `research_cache/<company_slug>/`
per "Save and cache" below — that one is the *curated* set of quotes that actually
made it into the drafted report, mapped back to their source for the Sources section.
The `_candidate_` infix and the `candidate_quotes/` subfolder are both what keep the
two from being mistaken for each other.

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
overview — never invent a multi-tier chain from a one-line description. **Check
explicitly how far upstream the company's own manufacturing reaches** — a company that
describes itself as backward-integrated to a raw/semi-processed stage (e.g. "from glass
preform to finished cable," "from billet to pipe") must show that integration inside
the "THE COMPANY" box itself, not leave it implied only in the prose while the diagram's
UPSTREAM box wrongly shows the company buying that stage from outside — see
`reference/report_format.md`'s backward-integration rule. **Always follow it with a
vertical stacked-box flow diagram** in a fenced code block in the markdown (ASCII only,
for portability), rendered as styled boxes via `html_helpers.flow_diagram()` in the
visual PDF — see `reference/report_format.md`'s layout and width-safety reasoning for
why the stack stays vertical either way.

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
customer, whether anything was found. **If a named marquee customer turns out to be
itself publicly listed — on any exchange, not just Indian ones (e.g. Rossell
Techsys's customer Lam Research, confirmed listed on NASDAQ)** — go beyond the
one-off search and analyze its **last 4 quarterly concalls/earnings calls** for
capacity/demand-relevant commentary, per `reference/source_playbook.md`'s "Checking a
named customer's own guidance" section. **Verify listed status before assuming
it** — don't guess an exchange for a large-sounding customer name; a named customer
can easily turn out to be a private/PE-owned subsidiary with no listing at all.
Check fast via Google Finance (`https://www.google.com/finance/quote/<TICKER>:<EXCHANGE>`
— works across NASDAQ/NYSE/LON/XETR/NSE/BSE/etc. via Claude in Chrome, and its
Earnings tab often has the transcript directly), falling back to the customer's own
IR page, then SEC EDGAR/Motley Fool/Seeking Alpha for US-specific gaps. Save those
transcripts under `~/.report-generator/sources/<company_slug>/customers/<customer_slug>/`,
not `research_cache/` (bulky raw material, same rule as the reporting company's own
concalls). For an exporting company, a quick check of an export-shipment-data
aggregator (Volza/Seair/ImportGenius/Zauba — per `reference/source_playbook.md`) can
corroborate a named customer or surface one the company hasn't itself named — label
anything found this way as third-party shipment data, distinct from company
disclosure. **Always a bullet list in the visual PDF, one point per customer — never
a merged paragraph.**

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
a multi-year trend and is explicitly exempt from the standard 18-month/6-quarter
lookback default that applies elsewhere in the report. **Table only in the visual PDF — no revenue/profit
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

While sourcing this section, also check **Raw Material Sourcing**: is the company's key
input imported, domestic, or mixed, and what % (primary source: the annual report's
"indigenous vs. imported raw material consumed" note per `reference/source_playbook.md`)
— cross-reference to Key Risks if imports are material. **If any portion is imported,
also capture the country-wise breakdown** wherever disclosed (e.g. "62% imported: China
40%, South Korea 15%, others 7%") — a bare aggregate import % without a country split
understates a genuine single-country concentration risk, so always look for the country
detail specifically, not just the headline %. If the annual report isn't accessible or
doesn't break out countries, an export/import shipment-data aggregator can show actual
inbound shipments (with origin country) as a partial substitute (per
`reference/source_playbook.md`). Say so explicitly if no company-specific figure —
or no country breakdown — was found, rather than presenting an aggregate % as if it were
the complete picture.

**Export Shipment / Customs Data** — for any exporting or importing company, always
attempt one targeted shipment-data-aggregator check (Volza/Seair/ImportGenius/Zauba/
Panjiva — per `reference/source_playbook.md`) rather than treating it as optional. Where
records exist, list the actual shipment-level detail found — consignee/shipper name,
country, product description, quantity/value if shown — clearly labeled as third-party
customs data. This feeds two sections at once: corroborating/surfacing names for
Marquee & Niche Customers, and corroborating/filling the country gap for Raw Material
Sourcing above. If nothing usable turns up, say so in one line rather than silently
skipping the attempt.

Also check the investor presentation's "Awards & Accolades" slide (or, quickly,
a WebSearch) for anything genuinely noteworthy to fold into the Capex/Milestones
Timeline as an achieved milestone — don't force this if there's nothing there.

**Capacity Utilization & Headroom** — only if a utilization figure (or the installed
capacity + units-produced inputs to derive one) was disclosed, usually in concall Q&A
or an investor presentation's operations slide. **Report capacity in the industry's own
physical unit first** — fiber-km/annum for an optical fiber maker, MT/annum for
metals/chemicals/cement, MW/MWp for power/renewables, units/annum for a discrete-goods
manufacturer, etc. — never present a bare % with no unit behind it. If the company
breaks capacity out by sub-type/grade (e.g. standard vs. specialty fiber), show that
breakdown rather than one blended figure. **Explicitly flag if the capacity is a
shared, multi-purpose pool** that can be swung across product variants, since an
aggregate utilization % then doesn't tell a reader how much of any one variant is
available — state this plainly rather than presenting a blended number as if it
described dedicated capacity. Once the physical-unit figures are established, run
`scripts/capacity_utilization.py` for the optional revenue-headroom lens and reproduce
its high-utilization flag verbatim if utilization is already at/above 85%. If a
post-capex revenue figure already surfaced elsewhere (Capex/Milestones timeline or an
outlook bullet), pass it via `--post-capex-max-revenue-cr` so the section shows
before-capex and after-capex figures side by side, plus what the capex itself unlocks —
don't derive a new number if management already gave one. **Table only in the visual
PDF — no before/after chart by default.**

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

**Broker/agency research (Nuvama, etc.) — only if the user has directly uploaded a
report; no dedicated section.** This pipeline never fetches broker research off the
web (per `reference/source_playbook.md`'s "Broker/agency research reports" entry —
these are institutional-distribution products with their own reproduction/
redistribution restrictions). When a report is supplied, don't wall it off into its
own section — fold each fact directly into whichever section it belongs to: a target
price and rating into Valuation, a demand/sector read into Industry Tailwinds/
Headwinds, a thesis point into Investment Thesis Summary, a flagged risk into Key
Risks, and so on. What keeps this from blending into the pipeline's own
independently-sourced numbers is an **inline tag on every single broker-sourced
point** — `[<BROKER>_<DDMMYYYY>]`, agency name uppercase/no-spaces plus the report's
own publication date, e.g. `[NUVAMA_29042026]` — appended immediately after the
sentence, table row, or bullet it supports. Tag every sentence individually, even
consecutive ones from the same report; don't tag a whole paragraph once. Paraphrase
thesis/risk points in your own words rather than reproducing paragraphs verbatim (the
source report's own disclaimer restricts reproduction). If a broker's number and the
pipeline's own independently-derived number both exist for the same thing (e.g.
Valuation's Forward PE table already has the pipeline's own forward multiple), show
both as separate, clearly attributed rows — never average or merge them into one
figure.

**Industry Tailwinds/Headwinds** — per `reference/source_playbook.md`, search outward
(peers, sector bodies, rating-agency sector notes), 2-4 bullets, one source each. A
quick LinkedIn/X check on the company's own official page (per
`reference/source_playbook.md`) can also surface something genuinely noteworthy not
yet in any filing — a leadership hire, an order win, a facility inauguration. Fold a
real finding into whichever section it actually belongs to (this one if sector-wide,
Marquee Customers if customer-related, Key Risks if it's a negative development) rather
than forcing a dedicated heading — and don't mention the check at all if nothing
noteworthy turned up.

**Competitive Positioning: Peer Comparison** — pull 3-5 direct peers from screener.in's
Peers tab or the company's own concall references to competitors, per
`reference/source_playbook.md`. Build the comparison table (IP/technology moat,
niche/marquee customers, certifications, other differentiator) including the reporting
company as its own row, then state plainly which side leads on each factor — facts
only, no ranking score. If no direct listed pure-play peer exists, say so and use the
closest adjacent listed comparables, labeled as adjacent rather than direct.

**MOATs** — a dedicated section, kept separate from the Peer Comparison table since a
moat is about the company's own durable advantages, not how it stacks up against named
peers. **Always render as bullet points** (`flag_list(kind='bull')` in the visual PDF)
covering whichever of these actually apply, each with its specific evidence: IP/
technology moat (patents, proprietary process, in-house R&D, and the backward-
integration depth already established in Value Chain Positioning — cross-reference,
don't re-explain), entry barriers (capital intensity, certification/qualification lead
times — a specific number of years if management gave one, customer design-in cycles,
proprietary know-how, regulatory barriers that block competitors), product criticality
(safety/mission-critical vs. discretionary/substitutable), and switching costs. Never
invent a moat claim the sources don't support — a company can have a real moat on one
front and a weak one on another; reflect that honestly rather than presenting a
uniformly strong picture.

**Technical Snapshot** — pull a pre-computed technicals summary (moving averages,
RSI, support/resistance) from a technicals provider per the playbook; don't compute
indicators from scraped OHLC data yourself. Timestamp it. **Render as a table or
bullet points in both the `.md` and the visual PDF — never a prose paragraph.** In the
visual PDF this is normal body text, not the small italic `.note` style — this section
carries real numbers a reader needs to read comfortably, not a one-line caveat.

**Promoter/Governance Track Record** — this reuses the same `guidance_history.json`
already populated for the outlook-bullet status pointers above; no separate logging
step needed here beyond adding this quarter's actual-vs-prior-guidance via
`add-actual` if this quarter's results closed out a previously guided numeric metric.
Run `scripts/guidance_tracker.py <company_slug> report` (default lookback is 6
quarters for the guidance-vs-actual comparisons — the standing default, don't
override it) and reproduce its flag verbatim if it found a pattern of misses.
Add promoter holding trend / pledge / auditor flags from the screener.in fetch —
**render the shareholding-pattern trend as a `data_table()` in the visual PDF, no
chart by default.**

Then cover **promoter fund raises** (preferential equity, warrants, NCDs/debentures,
term loans, promoter loans/guarantees) per `reference/source_playbook.md`'s sourcing
steps: check BSE/NSE announcements and credit-rating rationale for any raise not
already in `~/.report-generator/research_cache/<company_slug>/fundraise_history.json`, log new ones via
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
record, not just what falls inside the standard 18-month window.

Then check **credit ratings** for every report (not only companies with visible debt —
see `reference/source_playbook.md`'s "Credit rating agencies" section for exactly which
agencies to search and what to pull from a rationale). Log any rating action not
already in `~/.report-generator/research_cache/<company_slug>/rating_history.json` via
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
`~/.report-generator/research_cache/<company_slug>/litigation_history.json` via
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
`[Delivered]`, MOATs/Competitive Positioning strengths, TAM headroom, capacity headroom,
independent third-party corroboration (customer guidance, a rating reaffirmation/
upgrade, export-shipment data). **Always render as bullet points** (`flag_list(kind=
'bull')` in the visual PDF) — one claim per bullet, each carrying its own source; a
single short lead-in sentence framing the case is fine, but the substance belongs in
the bullets, not a merged paragraph. Per `reference/report_format.md` — **if the
research genuinely doesn't support a real thesis, say so plainly instead of padding it
out**; that's a legitimate, useful conclusion, not a failure to produce one.

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
without waiting to be asked — to `~/.report-generator/output/<company_slug>/` (e.g.
`~/.report-generator/output/td_power_systems/TD_Power_Systems_report.md` and
`~/.report-generator/output/td_power_systems/TD_Power_Systems_report.pdf`), **never**
inside the plugin's own directory. This keeps user-facing deliverables separate from
the skill's own working state in `~/.report-generator/research_cache/`. Create the
`~/.report-generator/output/<company_slug>/` folder if it doesn't exist yet.

**PDF generation is a mandatory last step of every run (full or incremental,
including a freshness-check-only refresh where the report body is reused
unchanged)** — never skip it and never treat it as optional or user-request-gated.

**All reports use the same visual template — WeasyPrint is not optional-if-convenient,
it is the required renderer.** Every company's PDF must look like every other
company's PDF; a batch of reports rendered through two different pipelines (one
visual, one plain-text ReportLab) reads as broken, not as an acceptable fallback.

**Before building anything, verify WeasyPrint actually works — don't assume from a
prior run or a different session.** Run `python3 -c "import weasyprint"` first. If
that fails, run `pip install weasyprint --break-system-packages` (add `matplotlib`
too if `scripts/charts.py` will be used) and re-check with the same import — do not
proceed past this step on a guess. Only after that second check still fails is the
environment considered genuinely unable to run WeasyPrint.

**Primary path — visual PDF via WeasyPrint (required whenever the above check
passes).** Follow `reference/report_format.md`'s "Assembly" section: build the HTML
body **by calling `scripts/html_helpers.py`'s actual functions** — `cover()`,
`badge()`, `card_grid()`, `flow_diagram()`, `data_table()`, `timeline()`,
`flag_list()`, `verdict_box()`, `sources_list()` — never by hand-writing raw HTML
tables/divs/ASCII-art dumps that merely resemble what those functions would produce.
A report built by hand-writing plain HTML instead of calling these functions will
still render through WeasyPrint without error (the render step has no way to know the
content is unstyled), which is exactly why "the PDF exists and WeasyPrint didn't
error" is not sufficient verification on its own — see the mandatory check below.
Style with `assets/report_style.css`, then render with `python3 -m weasyprint
report.html <output_dir>/<name>_report.pdf`. `scripts/charts.py` (matplotlib) is
available but **opt-in, not default** — only call it if the user specifically asks
for a visual/chart version of a section.

**Verify before delivering — run `scripts/verify_report.py`, don't rely on your own
judgment call for this.** This script exists specifically because "the PDF exists
and WeasyPrint didn't error" has already once looked like success while the report
was actually built with hand-written HTML missing every styled element. Run, in
order:

1. `python3 scripts/verify_report.py html <report.html>` — **before deleting
   `report.html`, before rendering the PDF.** Checks for the CSS classes only
   `html_helpers.py`'s functions emit (`card-grid`, `flow-diagram`/`flow-box`,
   `data`, `timeline`, `flags`, `verdict-box`, `cover`). A FAIL here means the HTML
   was hand-written instead of built through the helper functions — stop, rebuild it
   through the correct function calls (`cover()`, `card_grid()`, `flow_diagram()`,
   `data_table()`, `timeline()`, `flag_list()`, `verdict_box()`), and re-run this
   check before proceeding to render.
2. `python3 scripts/verify_report.py pdf <output_dir>/<name>_report.pdf` — after
   rendering. Confirms the PDF's actual `Producer` metadata (don't assume WeasyPrint
   from memory of what command you ran — check the file). A WARN for ReportLab means
   you must state that explicitly in your chat response to the user, not silently
   proceed. A FAIL (missing/corrupt PDF, too few pages) means the render didn't
   actually work regardless of what the render command's own exit code said.
3. `python3 scripts/verify_report.py report <output_dir>/<name>_report.md --brokers
   <TAG1,TAG2,...>` — pass every broker tag for any broker/agency report supplied
   this run (e.g. `NUVAMA_29042026,CLSA_24052026`). Confirms every canonical section
   is present AND, critically, that every broker's tag actually appears in the
   drafted text at least once — catching the case where a broker PDF was read and
   summarized to yourself but its facts never actually made it into the report.
4. `python3 scripts/verify_report.py sources <company_slug>` — confirms the
   `sources/`/`research_cache/` split (see Directory structure in README.md) wasn't
   violated: no bulky `.pdf`/`.txt`/`.bm25.pkl` leaked into `research_cache/`, no
   candidate-quotes JSON left loose in `sources/` instead of
   `research_cache/<slug>/candidate_quotes/`.
5. `python3 scripts/verify_report.py freshness <company_slug>` — confirms
   `check_freshness.py --mark-processed` was actually called at the end of this run
   (checks `state.json`'s `last_processed_at` is today), not just intended.
6. `python3 scripts/verify_report.py extraction <source.pdf> <extracted.txt>` — run
   this for every annual report extracted this run, **before** deleting/losing the
   source PDF. Confirms the extraction actually starts at page 1 and reaches the
   document's real final page — catches a scouting/partial-range extraction being
   mistaken for the full-document extraction the "always extract the whole
   document" rule requires. This only works if the source PDF is still on disk, so
   **always save a fetched annual report PDF to `sources/<company_slug>/` before
   extracting it**, per the source-fetch rule — don't extract-then-discard.
7. `python3 scripts/verify_report.py depth <company_slug>` — counts concall and
   annual-report `.txt` files actually present in `sources/<company_slug>/` against
   the standard depth (6 quarters, 2 annual reports). A WARN here isn't automatically
   a blocker — a newly-listed company can genuinely lack 6 quarters of history — but
   the shortfall must then be stated explicitly in the report per the "Never drop
   anything silently" rule, not silently delivered as if standard depth was met.

**Also still do a visual spot-check** via `pdftoppm -jpeg -r 120 <name>_report.pdf
page` and `Read()` the cover, Company Summary, Value Chain Positioning, and one
table-heavy page — the script catches missing structural elements, not visual bugs
like overflowing tables, unreadable font sizes, or dead whitespace (a common cause: a
chart PNG saved without tight bounding-box cropping — see `scripts/charts.py`'s
`bbox_inches='tight'` usage — or a chart wrongly wrapped in `chart_row()`). If
regenerating/fixing an existing company, comparing side-by-side against another
company's already-correct PDF from earlier in the same session is a fast way to
catch anything the script and a solo skim would both miss.

**Any FAIL from the script is a stop-and-fix, not a note-and-continue** — same
standing as the "Never drop anything silently" rule below, because a deterministic
check that's allowed to fail without consequence isn't actually deterministic in
effect, it's just another thing to skim past.

Delete any intermediate chart PNGs and `report.html` only after both checks pass;
only the final PDF and `report.md` belong in `~/.report-generator/output/<company_slug>/`.

**Legacy fallback — reportlab, text-only. Last resort only, and always flagged.** Use
this ONLY if the verify-then-install check above genuinely failed twice (import error
persists after a fresh `pip install`) — never reach for it just because a build step
errored once; retry the WeasyPrint path before giving up on it. If truly falling back,
run `python3 scripts/report_to_pdf.py <output_dir>/<name>_report.md
<output_dir>/<name>_report.pdf --title "<Company Name> - Research Report"` instead —
markdown-to-PDF with no charts/cards/badges, but it still fixes the ₹-glyph issue and
strips any internal `scripts/*.py` mention that slipped into the markdown as a backstop.
Never let a missing dependency block delivery entirely; fall back rather than skip the
PDF outright — but **explicitly tell the user in your chat response (not silently)
that this report used the plain-text fallback renderer and why**, so a mismatched
look across a multi-company batch is never a surprise discovered after the fact.
Confirm both `.md` and `.pdf` exist in `~/.report-generator/output/<company_slug>/`
before telling the user the report is ready, whichever path was used.

Save/update `~/.report-generator/research_cache/<company_slug>/quotes.json`, `bullets.json`,
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

## Never drop anything silently

This is a standing rule that overrides convenience everywhere else in this file: if a
source can't be fetched, a fetch times out, a page/quarter/section is skipped for any
reason, a rate limit or size limit is hit, a script errors, an extraction comes back
garbled or empty, a tracker flag can't be verified, or a section is left out — **that
gap gets stated in the report, in the section it affects, every time.** Silently
producing a report that reads as complete when a piece of it wasn't actually gathered
is a worse failure than the gap itself, because the reader has no way to tell a
verified "nothing here" from an unverified "I didn't check."

**This rule has a second half that matters just as much: don't just intend to catch
gaps, mechanically check for the specific ones this pipeline has actually hit.**
`scripts/verify_report.py` (see "Verify before delivering" above) exists because
several of the gaps below have already slipped through on judgment/memory alone in
practice — a hand-written HTML report that still rendered fine through WeasyPrint, an
annual report extraction that silently started at page 40 instead of page 1, a broker
PDF whose facts were read but never actually made it into the drafted text. Wherever
a check below has a scriptable, grep-able signature, run the script; reserve judgment
calls for the gaps that genuinely can't be mechanically checked (e.g. whether a
"Colt-style" customer-listing explanation is specific enough — see the Marquee &
Niche Customers section of `reference/source_playbook.md`).

This applies everywhere a gap can happen, not just document fetches:

- **Fetch failures** — a concall/investor-presentation/annual-report PDF that 404s,
  times out, or a screener.in widget that won't populate after one retry (per the
  Token discipline section's "don't burn more than one retry" rule — stopping the
  retry is fine, silently moving on without noting it is not). State what was
  attempted and what failed, in the relevant section (not buried only in a final
  Sources footnote).
- **Partial extraction / worker failures** — `pdf_to_text_parallel.py` already
  refuses to write a partial file and errors instead if a chunk comes back missing;
  if that error fires and you fall back to something narrower, say so in the report,
  don't quietly present the narrower extraction as if it were the whole document.
- **Rate limits / size limits** — a WebSearch/WebFetch call throttled, truncated, or
  capped by `max_chars`; an aggregator (Volza/Seair/ImportGenius/Zauba/Trendlyne/
  Tijori/etc.) that returned a thin or paywalled preview instead of full data. Note
  the limitation next to whatever partial data *was* usable, rather than presenting
  the partial data as complete.
- **Sections that come back empty** — a tracker report with no entries, a
  `semantic_search.py`/grep pass that found nothing for a section you expected to
  exist. Distinguish explicitly between "checked, genuinely not disclosed" (a
  legitimate, useful finding — see `reference/report_format.md`'s per-section rules
  for when a section is expected to state absence rather than being omitted) and
  "couldn't verify" (a gap, which must say so) — never let the second read like the
  first.
- **Renderer/dependency fallbacks** — e.g. the legacy ReportLab PDF fallback used in
  place of WeasyPrint (see the PDF-assembly rules above) — must be flagged in your
  chat response to the user, not just left for them to notice from how the PDF looks.
- **Multi-company batches** — if one company's report in a batch request hits a gap
  and another's doesn't, that asymmetry itself is worth surfacing in your summary to
  the user, not just inside each report individually.

The bar is: a reader of the report, or a user reading your chat summary, should never
have to independently discover that something was skipped, timed out, capped, or
silently dropped. If in doubt about whether something rises to "worth flagging,"
flag it — the cost of one extra caveat line is far lower than the cost of a reader
trusting a gap they were never told about.

## Deterministic Guardrails

Everything above states rules; this section is the enforcement layer —
`scripts/verify_report.py` (see its own docstring for exact usage) implements every
check named below, tested against real report runs, not written and left
unverified. Three tiers, matching where in the pipeline each one runs:

### 1. Input Guardrails (the gatekeepers) — run before real processing starts

Catch a bad input before it corrupts everything built on top of it:

- **`sniff <file.pdf>`** — classifies an uploaded PDF's likely type (annual report /
  concall transcript / investor presentation / broker research report) from
  first-page keyword signals. Run this on any user-uploaded document before routing
  it into a section-specific pipeline — catches, for example, a broker PDF being
  processed as if it were an annual report.
- **`slug <company_slug>`** — validates a derived company slug is safe to use in
  filesystem paths (`[a-z0-9_]+` only) before it's used to construct any path under
  `~/.report-generator/`.
- **Company/ticker existence** — before running the full pipeline, the Step 0
  freshness check's screener.in fetch already serves as an implicit input gate: if
  the company can't be found there at all, that's the signal to ask the user to
  confirm the name/ticker rather than proceeding to build a report for a company
  that may not exist or may be misspelled.

### 2. Execution Guardrails (the boundaries) — run during / immediately after a run

Bound what the pipeline is allowed to do while it's running, independent of what
it's trying to accomplish:

- **`scope <plugin_skill_dir> [--minutes N]`** — confirms no file under the skill's
  own install directory (`skills/report-generator/`) was created or modified
  recently. This skill must only ever write under `~/.report-generator/` — never
  inside its own plugin directory (a standing rule since the "Directory structure"
  section of `README.md`); this check makes that mechanically verifiable instead of
  just stated.
- **`reproduction <source.txt> <report.md> [--ngram N]`** — checks no N-consecutive-
  word sequence (default 12) from a broker/agency source document was copied
  verbatim into the drafted report. Run this against every broker source used this
  run before delivery — enforces the "paraphrase, don't reproduce at length" rule
  from the Broker/agency research reports section mechanically.
- **Sandbox network boundary** — no raw `curl`/`requests`/`urllib` against arbitrary
  domains (see "Important sandbox constraint" in `reference/source_playbook.md`);
  all fetching goes through the platform's own web tools. This is enforced by the
  sandbox itself (a real call will 403), not by this script — it's an execution
  boundary that doesn't need a separate deterministic check because the environment
  already refuses it.
- **One-retry-per-stuck-source limit** — bounds runaway retry loops against a
  source that isn't going to resolve (Token discipline section) — a judgment-call
  boundary, not separately scriptable, but stated here as an execution guardrail
  alongside the two that are.

### 3. Output Guardrails (the filters) — run right before delivery

Nothing reaches the user without passing these — this is where "Never drop anything
silently" above gets mechanically enforced rather than left to memory:

- **`html <report.html>`** — required `html_helpers.py` CSS markers present (catches
  hand-written HTML that renders fine but is unstyled — see "Verify before
  delivering" above for the full list of markers).
- **`pdf <report.pdf>`** — producer metadata (flags a silent ReportLab fallback) and
  page-count sanity.
- **`report <report.md> [--brokers TAGS]`** — all canonical sections present; every
  supplied broker's tag actually appears in the drafted text.
- **`quotes <report.md> <sources_dir>`** — every double-quoted string in the Near/
  Medium/Long Term outlook sections is an exact (whitespace-normalized) substring of
  at least one source `.txt` — mechanically enforces `report_format.md`'s "every
  quote is verbatim" rule instead of relying on review alone to catch a fabricated
  or subtly-altered quote.
- **`disclaimer <report.md>`** — the required "not investment advice" language is
  present.
- **`sources <company_slug>`** — the `sources/`/`research_cache/` split wasn't
  violated.
- **`freshness <company_slug>`** — `check_freshness.py --mark-processed` was
  actually called this run, not just intended.
- **`extraction <source.pdf> <extracted.txt>`** — an annual report's extraction
  actually covers page 1 through the real last page.
- **`depth <company_slug>`** — concall/annual-report counts against the standard
  6-quarter/2-annual-report sourcing depth.
- **`whitespace <pdf> [--ratio 0.5]`** — every interior page (not the cover, not the
  final page) must have a word count at or above the given fraction of the
  interior-page median; the last page gets a lower but still-nonzero floor (a
  near-blank final page from a one-line overflow is dead space too). **Only the
  cover page is allowed to be sparse/mostly blank — every other page must be
  reasonably filled.** Catches dead whitespace from a forced page break or any
  other layout mistake. Confirmed in practice twice: a `page_break()` call landing
  mid-document produces exactly this signature (one page at ~30% of the
  surrounding pages' density) — which is why `page_break()` is now banned outright
  in `reference/report_format.md`'s Assembly section — and a near-blank final page
  from a small content overflow, which the original last-page exemption missed
  until tightened.
- **`depth <company_slug>`** now also counts **investor presentations** (standard
  depth: 6 quarters, same as concalls), not just concalls and annual reports —
  confirmed in practice that a missing investor presentation isn't just a thinner
  report, it can be factually wrong (Segment-wise Performance, Total Addressable
  Market, and Manufacturing Locations lean heavily on it, and a report built
  without it once incorrectly claimed no TAM was disclosed when the investor
  presentation had one all along). Annual reports are grouped by document identity
  (stripping page-range chunk suffixes) rather than counted per file, so 6 chunks
  of one document correctly count as 1 report, not 6.
- **`ratings <company_slug> [--months 6]`** — checks `rating_history.json`'s most
  recent logged entry is within the last 6 months. This is a **recency-of-check**
  guardrail, not a lookback limit on what gets *shown* (the Promoter/Governance
  section still shows the full rating history, unchanged) — an old cached entry
  isn't evidence nothing happened since; every run should actively re-check each
  covering agency's site for the last 6 months, not just trust a stale cache.
  Always informational (WARN, never FAILs the run) since an old entry could
  legitimately mean nothing changed, not that the check was skipped.
- **`paragraphs <report.md> [--max-words 160]`** — flags any paragraph exceeding
  ~10 rendered lines (approximated as 160 words) anywhere in the report, by
  section. Per `reference/report_format.md`'s "Paragraph length limit" rule, a
  paragraph this long should become bullet points instead — the same pattern
  already mandatory for MOATs, Investment Thesis Summary, and Key Risks, now
  applied report-wide. **One exception baked into the check's own guidance**: a
  flagged Verdict paragraph gets "trim it" advice, not "convert to bullets" advice
  — the Verdict section stays a short paragraph by its own spec even when other
  sections default to bullets, so exceeding the limit there means evidence-
  recapping crept in, not that it needs bulleting.

**Every guardrail above that returns FAIL is a stop-and-fix, not a note-and-continue
— a deterministic check with no consequence for failing isn't actually a guardrail,
it's decoration.** WARN-level results (sourcing-depth shortfalls, a ReportLab
fallback) don't block delivery but must be stated explicitly to the user per "Never
drop anything silently" above — the distinction between FAIL and WARN is "must be
fixed before delivery" vs. "must be disclosed at delivery," never "can be ignored."
