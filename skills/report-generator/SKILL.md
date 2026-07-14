---
name: report-generator
description: Generates the visual investment-thesis PDF report pipeline for an Indian
  listed company (concall transcript, investor presentation, annual report,
  screener.in data). Invoke explicitly via /research-advisory:report-generator or /report-generator — not
  intended to auto-trigger from plain-language mentions of a company.
---

# Report Generator

**If you're about to run this for more than one company at once (parallel agents/
sessions), or you're not sure whether an earlier run for this company is still going**
— `python3 scripts/run_context.py status <company_slug>` is a cheap check that
doesn't require reading the rest of this file. For the normal case of generating one
company at a time, this doesn't come up; skip straight to Step 0. (Step 0's optional
lock step exists specifically for the concurrent case — see there for what it's
guarding against.)

Produces a **visual PDF** (metric cards, a color-coded timeline, and dense data
tables — tables are the default for anything with real numbers; charts are opt-in, not
automatic, see `reference/report_assembly.md`) via WeasyPrint,
alongside the markdown source of truth. **The full, authoritative section order and
per-section formatting rules live in three reference files: `reference/report_format.md`
(cover, Company Summary, Value Chain Positioning, Situation Classification, universal
rules), `reference/report_sections.md` (the nineteen sections after the outlook), and
`reference/report_assembly.md` (PDF build mechanics) — these are the single source of
truth for report structure, not this file.** See `examples/Sterlite_Technologies_report.md` for
the outlook-section style. The "Building each section" section below covers *sourcing*
guidance (where to pull each fact from) rather than restating format rules already in
those files.

The report text itself never names internal scripts/files (`scripts/guidance_tracker.py`,
`--flag` values, etc.) — see `reference/report_format.md`'s "Never mention internal
tooling in the report text" rule.

## Interpreting the slash-command argument

Invoked via `/research-advisory:report-generator <argument>` or `/report-generator
<argument>` — not auto-triggered from plain conversation (see frontmatter). The
argument is a free-text company name/ticker plus optional intent words; what those
intent words mean:

- **Just a company name** (`research <Company>`, `generate a report on <Company>`, or
  any other phrasing naming a company with no further qualifier) — new company →
  full pipeline (Step 0 reports `no_state`). Already-generated company → same as
  "regenerate" below.
- **"regenerate" / "refresh" / "update"** (no "from scratch" qualifier) — the
  default, cheap path for an existing company: Step 0's freshness check
  (`up_to_date` or `new_quarter`) decides what actually changed; unchanged sections
  carry forward from the cached `report.md`.
- **"from scratch" / "rebuild" / "ignore the cache" / "redo entirely"** — bypass the
  cache explicitly: `scripts/check_freshness.py <slug> --force` → `force_full`,
  refetch every source and rebuild every section. Tracker histories
  (`guidance_history.json`, `fundraise_history.json`, `rating_history.json`,
  `litigation_history.json`) are cumulative real-world records, never wiped either
  way — keep appending regardless of which path ran.
- **Multiple companies in one argument** — process each independently through the
  same pipeline. **Default sequential**, one company's `.md`+`.pdf` fully confirmed
  on disk before the next starts (parallel agents have produced mismatched output
  before — one silently missing WeasyPrint fell back to ReportLab while a sibling
  didn't). Only go parallel if explicitly asked, and verify WeasyPrint first in that
  case.

An uploaded concall transcript, investor presentation, annual report PDF, or
broker/agency research report (Nuvama, Motilal Oswal, etc.) in place of/alongside a
company name also triggers this skill — sourcing then prefers the uploaded documents
over fetching (see "User-uploaded documents" in `reference/source_playbook.md`). A
broker/agency report has no dedicated section: fold each fact into whichever section
it belongs to, tagged inline `[BROKER_DDMMYYYY]` (see `reference/report_sections.md`'s
"Broker / agency research" rule).

**If no company was named** — don't guess, and specifically don't silently reuse a
company from earlier in the conversation unless the request is clearly a continuation
of that same thread (a plausible-looking but wrong default). Ask which company (name
or ticker); the user still has to name one.

**All working state and deliverables live outside this plugin directory, under
`~/.report-generator/`** — never inside the plugin's own folder. Two companies' data
never mix within that folder: each gets its own
`~/.report-generator/research_cache/<company_slug>/` working state and
`~/.report-generator/output/<company_slug>/` deliverable folder, keyed off a slug
derived from the company name (lowercase, underscores — e.g. "TD Power Systems" ->
`td_power_systems`).

Do not read `reference/report_format.md`, `reference/report_sections.md`,
`reference/report_assembly.md`, `reference/source_playbook.md`, or
`reference/data_sources.md` in full until you actually need them (step 2+ below).
Read `examples/Sterlite_Technologies_report.md` once, when drafting.

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

0. **Optional — only relevant if you're running more than one agent/session against
   this company at once** (the default single-company workflow can skip straight to
   step 1): `python3 scripts/run_context.py acquire <company_slug>`. If
   `"acquired": false`, another run is actively processing this same company slug —
   don't start a second concurrent one. If acquired, `export
   REPORT_GEN_RUN_ID=<run_id>` from the result so tracker writes this run makes are
   stamped with that id (helps if a collision ever needs untangling). Release at the
   end (Step 3) if you acquired it.
1. Fetch screener.in's Documents/Concalls tab only (not the transcript itself yet) to
   find the latest quarter's **full date** — e.g. `2026-04-29`, not "May 2026" or
   "Q4 FY26." A month/quarter label is genuinely ambiguous for the string-equality
   comparison `check_freshness.py` does (two results announced in the same month
   collide; screener.in's own label wording can drift) — always resolve to the
   actual filing/call date before passing it in. If the company doesn't hold a
   concall at all, use the results filing date instead — see
   `reference/source_playbook.md`'s "If the company doesn't hold concalls" section.
   **While on this page, also collect every concall date shown** (not just the
   latest) and pass them as `--concall-dates "2026-05-01,2026-02-01,..."` to
   `check_freshness.py` in the next step — this is what lets it flag a sparse/
   irregular cadence upfront (`recommended_sourcing_mode` in its output) instead of
   the standard 6-quarter depth assumption being discovered as a poor fit only after
   sourcing has already started.
2. If the user's request explicitly asked for a from-scratch rebuild (see "How to
   trigger" above), skip straight to running
   `python3 scripts/check_freshness.py <company_slug> --force` — this returns
   `force_full` regardless of the date, and every source gets refetched/rebuilt as
   described there. Otherwise run
   `python3 scripts/check_freshness.py <company_slug> --latest-seen "<YYYY-MM-DD>"
   --concall-dates "<comma-separated dates from step 1>"`. Read the `cadence` field
   in the result before proceeding — if `recommended_sourcing_mode` comes back
   anything other than `standard`, follow its `note` (reduced-depth/no-concall
   fallback) rather than defaulting to the standard 6-quarter assumption below.
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
   `python3 scripts/check_freshness.py <company_slug> --mark-processed "<YYYY-MM-DD>"
   --price <price>` — same full-date requirement as step 1, since this is exactly
   what a future run's `--latest-seen` gets string-compared against. If you acquired
   the optional lock in step 0, release it now: `python3 scripts/run_context.py
   release <company_slug> <run_id>` (a lock left held by a dead process is
   auto-reclaimed after 2 hours regardless, so this isn't critical to get right).

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

**Before extracting any PDF fetched from a search result (not the company's own IR
page or a direct exchange filing link), verify it's actually the right company's
document.** Pass `--expect-name "<company name substring>"` to `pdf_to_text.py` /
`pdf_to_text_parallel.py` — it scouts the first 2 pages and refuses to run the full
extraction if the name isn't found. This has a real failure mode it's guarding
against: a search-result link resolved to a similarly-indexed but entirely different
company's annual report once, and it was only caught after a full multi-page
extraction and several greps came back with nonsensical section contents (a steel
company's segment note under a leather-exporter's slug). The identity check turns
that into an immediate, cheap failure instead of a wasted extraction cycle.

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

**Format rules for every section (tables vs. bullets, what's mandatory, what's
conditional) live in `reference/report_format.md` (the opening sections) and
`reference/report_sections.md` (the nineteen sections after the outlook). Sourcing
steps (which slide, which tab, which script call, which aggregator) live in
`reference/source_playbook.md` — its section headings match these one-to-one.** This
index exists so you can see the whole report's shape and each section's trigger
condition in one pass, without opening any reference file yet — open the matching
`source_playbook.md` section when you actually start sourcing that part, and the
matching format file when you draft it.

In order: **Company Summary** (never invent) · **Value Chain Positioning** (with the
vertical flow diagram — check backward-integration depth explicitly, see
`reference/report_format.md`'s backward-integration rule) · **Situation Classification** (a
judgment call from what's already gathered — re-examine every regeneration, don't
carry forward) · **Near/Medium/Long Term outlook** (verbatim-quoted bullets, each with
a status pointer logged via `guidance_tracker.py add-guidance` — `--supersedes-id`
when a later concall revises an earlier item) · **Marquee & Niche Customers** (bullet
list; if a named customer is itself publicly listed on any exchange, check its last 4
quarters of concalls — see source_playbook.md's "Checking a named customer's own
guidance") · **Capex/Milestones/Certifications Timeline** (also the roll-up table for
every other future-dated commitment elsewhere in the report) · **CDMO Pipeline**
(pharma + explicit CDMO/CRAMS line only, gated at Company Summary — see above) ·
**Financial Performance Summary** (YoY table, exempt from the standard lookback, plus
the balance-sheet anomaly check — debtor days, cash vs. short-term borrowings,
goodwill/net-worth/other-assets scan) · **Segment-wise Performance** (table only, one
per basis if more than one disclosed, plus exports-vs-domestic if found) · **Order
Book** (table with as-of date, composition breakdown if disclosed) · **Manufacturing
Locations & Physical Assets** (bullet list) **+ Raw Material Sourcing** (domestic vs.
imported %, country breakdown if any portion is imported) **+ Export Shipment/Customs
Data** (always attempt one aggregator check for an exporter/importer — feeds both
Marquee Customers and Raw Material Sourcing) · **Capacity Utilization & Headroom**
(industry's own physical unit, never a bare %; flag shared multi-purpose pools; run
`capacity_utilization.py`, `--post-capex-max-revenue-cr` if a post-capex figure
already surfaced elsewhere) · **Total Addressable Market** (only if an actual figure,
not a growth rate, was disclosed) · **Valuation/Forward PE** (`forward_pe.py`, plus
the company's own historical median PE from a secondary aggregator) · **Broker/agency
research** (uploaded only, never fetched — inline `[BROKER_DDMMYYYY]` tags, no
dedicated section, paraphrase never reproduce) · **Industry Tailwinds/Headwinds** ·
**Competitive Positioning: Peer Comparison** (3-5 direct peers, reporting company as
its own row) · **MOATs** (bullet points — entry barriers, IP/tech moat, product
criticality, switching costs; never invent one sources don't support) · **Technical
Snapshot** (table or bullets, never prose, normal body-text size) · **Promoter/
Governance Track Record** — guidance reliability (`guidance_tracker.py report`) +
shareholding trend table + **promoter fund raises** (`fundraise_tracker.py add-raise`,
`--investors` whenever named, not lookback-limited) + **credit ratings**
(`rating_tracker.py add-rating`, every report gets checked regardless of visible debt,
not lookback-limited) + **litigation** (`litigation_tracker.py add-case`, watch for
`--status dismissed_appealable` vs. `closed_final`, not lookback-limited) ·
**Investment Thesis Summary** (bullet points, one claim per bullet — or an honest "the
research doesn't support a real thesis" if that's what it shows) · **Key Risks**
(mandatory even in a bullish report — carries through any rating downgrade, appealable
litigation, high-utilization flag, or customer-concentration figure surfaced above) ·
**Verdict** (one short paragraph — situation classification, strongest evidence,
biggest open question, honest confidence level) · **Sources** (numbered, hyperlinked,
reusing `quotes.json`'s traceability).

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
passes).** Follow `reference/report_assembly.md`: build the HTML
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
judgment call for this.** Full checklist (what to run, in what order, and why each
check exists) is in `reference/guardrails.md` — read it now if this is your first
run this session. Short version: `html` → render PDF → `pdf` → `report` →
`sources` → `freshness` → `extraction` → `depth`, plus `quotes`/`disclaimer`/
`whitespace`/`ratings`/`announcements`/`social`/`paragraphs` before delivery, and a
visual spot-check via `pdftoppm`. **Any FAIL is a stop-and-fix, not a
note-and-continue.** Delete intermediate chart PNGs and `report.html` only after all
checks pass; only the final PDF and `report.md` belong in
`~/.report-generator/output/<company_slug>/`.

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
freely states a situation classification (`reference/report_format.md`), a synthesized
investment thesis, and a verdict with a directional read (both in
`reference/report_sections.md`). No compliance
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
  legitimate, useful finding — see `reference/report_sections.md`'s per-section rules
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

`scripts/verify_report.py` is the enforcement layer for every rule stated above —
three tiers (Input/Execution/Output), each check's exact purpose, and the FAIL-vs-WARN
distinction are all in `reference/guardrails.md`. The "Verify before delivering"
checklist above (Save and cache) is the operational sequence; that file is the full
reference when you need to know *why* a specific check exists or what a WARN vs FAIL
means for one of them.
