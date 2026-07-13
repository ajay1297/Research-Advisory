# Report Generator

Generates and refreshes India-listed company research reports from concall
transcripts, investor presentations, annual reports, credit-rating
rationales, and screener.in/BSE/NSE data — as a visual PDF plus its Markdown
source of truth.

## Contents

- [Architecture overview](#architecture-overview)
- [End-to-end flow — prompt to PDF](#end-to-end-flow--prompt-to-pdf)
- [Directory structure](#directory-structure)
- [Persistent state — how regeneration stays cheap](#persistent-state--how-regeneration-stays-cheap)
- [Script responsibilities](#script-responsibilities)
- [Report section pipeline](#report-section-pipeline)
- [Installation](#installation)
- [Components](#components)
- [Setup](#setup)
- [Usage](#usage)
- [Accuracy discipline](#accuracy-discipline)
- [Never drop anything silently](#never-drop-anything-silently)

## Architecture overview

The skill is a **Claude Skill**, not a program with its own runtime — there is no
server, no daemon, no scheduled job. Everything below is a set of markdown
instructions (`SKILL.md` + `reference/*.md`) that a Claude session reads and follows,
plus small local Python scripts it shells out to for the parts that shouldn't consume
model context (PDF text extraction, structured-fact bookkeeping, arithmetic, PDF
rendering). The four moving parts:

```
+------------------------------------------------------------------------+
|  YOU                                                                    |
|  "research <Company>" / "refresh <Company>'s report" / upload a PDF     |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  CLAUDE (this skill's instructions)                                     |
|  SKILL.md          -- the pipeline, step by step                        |
|  reference/         -- report_format.md (what to write, section by      |
|                         section) + source_playbook.md (where to get     |
|                         each fact, and the fallback path if a source    |
|                         is stuck)                                       |
+------------------------------------------------------------------------+
                |                                  |
                v                                  v
+----------------------------------+   +----------------------------------+
|  EXTERNAL SOURCES                 |   |  LOCAL SCRIPTS (scripts/*.py)     |
|  screener.in                      |   |  pdf_to_text.py                  |
|  BSE / NSE (filings, results)     |   |  extract_theme_quotes.py         |
|  Concall transcript (PDF)         |   |  guidance_tracker.py             |
|  Investor presentation (PDF)      |   |  fundraise_tracker.py            |
|  Annual report (PDF)              |   |  rating_tracker.py               |
|  CRISIL / ICRA / CARE / Infomerics|   |  litigation_tracker.py           |
|  Peer companies (WebSearch)       |   |  capacity_utilization.py         |
|  Technicals provider              |   |  forward_pe.py                   |
|  (no raw curl/requests -- always  |   |  check_freshness.py              |
|   via WebFetch/WebSearch/browser) |   |  charts.py (opt-in only)         |
+----------------------------------+   |  html_helpers.py                 |
                |                      |  report_to_pdf.py (legacy         |
                |                      |   fallback, reportlab)            |
                |                      +----------------------------------+
                |                                  |
                v                                  v
+------------------------------------------------------------------------+
|  ~/.report-generator/sources/<company_slug>/  (OUTSIDE the plugin)       |
|  *.txt / *.pdf / *.bm25.pkl -- fetched source documents + search index  |
|  (bulky, regenerable by refetching -- not part of research_cache below, |
|   so research_cache/ stays small and shareable on its own)              |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  ~/.report-generator/research_cache/<company_slug>/  (OUTSIDE the plugin)|
|  *_history.json    -- durable, append-only fact logs (see below)        |
|  state.json         -- freshness marker (last quarter processed)        |
|  quotes.json, bullets.json -- synthesized outlook-quote extracts        |
|  report.md          -- the drafted report, source of truth              |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  PDF ASSEMBLY (WeasyPrint via html_helpers.py + assets/report_style.css)|
|  cover badge -> cards -> outlook -> 19 sections -> thesis -> verdict     |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  ~/.report-generator/output/<company_slug>/  (OUTSIDE the plugin)        |
|  <Company>_report.md                                                    |
|  <Company>_report.pdf                                                   |
+------------------------------------------------------------------------+
```

Nothing in this diagram ever writes inside the plugin's own `skills/report-generator/`
directory — every generated file lands under `~/.report-generator/` instead (see
Directory structure below).

## End-to-end flow — prompt to PDF

This is what actually happens, in order, from the moment you type a prompt to the
moment two files land in `~/.report-generator/output/`. Branches matter here — most of the token/time
savings on a *second* run for the same company come from Step 0's freshness check, not
from anything downstream.

```
 [1] YOU: "research <Company>" / "refresh <Company>'s report" / upload a PDF
       |
       v
 [2] Claude recognizes the trigger phrase (SKILL.md's frontmatter description) --
     no slash command, natural language only. Derives company_slug (lowercase,
     underscores).
       |
       v
 [3] STEP 0 -- FRESHNESS CHECK
     Fetch screener.in's Concalls tab label only (not the transcript yet)
       |
       v
     "...from scratch"/"rebuild"/"ignore the cache" in the request?
       |                                     |
       v yes                                 v no
     check_freshness.py <slug> --force    check_freshness.py <slug> --latest-seen "<label>"
       |                                     |
       v                       +---------------------+---------------------+
   force_full                  |                     |                     |
   (explicit rebuild)          v                     v                     v
       |                   no_state              up_to_date            new_quarter
       |                   (first run)      (nothing changed)     (a new quarter posted)
       |                       |                     |                     |
       |                       |                     v                     |
       |                       |            Reuse cached report.md          |
       |                       |            as-is. Skip to [8] if only       |
       |                       |            price changed (rerun              |
       |                       |            forward_pe.py alone).            |
       |                       |                                             |
       v                       v                                             v
 [4''] FROM-SCRATCH REBUILD  [4] FULL SOURCE PIPELINE            [4'] INCREMENTAL PIPELINE
     Refetch + rebuild every    Fetch + process everything below      Fetch ONLY the new quarter's
     section, same as [4], but  for the first time.                   concall + investor presentation
     trackers (guidance/                                              + screener.in's last 1-2 columns.
     fundraise/rating/                                                Reuse everything else already in
     litigation) keep                                                 ~/.report-generator/research_cache/<slug>/
     accumulating, not reset.                                         untouched.
       |                       |                                             |
       +-----------------------+---------------------+-----------------------+
                             v
 [5] FETCH (WebFetch / WebSearch / Claude Browser as JS-render fallback;
     BSE/NSE direct if screener.in's widgets won't populate)
     - screener.in: About, financials, shareholding, Peers, Documents tab
     - Concall transcript PDF, Investor presentation PDF
     - Annual report PDF (raw-material import note, PP&E, litigation)
     - Credit rating rationales (CRISIL/ICRA/CARE/India Ratings/Acuite/
       Brickwork/Infomerics)
     - BSE/NSE announcements (fund raises, litigation, certifications)
     - Peer companies + technicals provider
     Every fetched document is saved to ~/.report-generator/sources/<slug>/ first.
       |
       v
 [6] LOCAL PROCESSING (no model context spent reading raw documents)
     pdf_to_text.py            -- PDF -> plain text, locally
     extract_theme_quotes.py   -- transcript text -> near/medium/long-term
                                   candidate-quote JSON (only this gets read,
                                   never the full transcript)
     guidance_tracker.py       -- log each outlook item + status pointer
     fundraise_tracker.py      -- log fund raises + named allottees
     rating_tracker.py         -- log rating actions, flag downgrades
     litigation_tracker.py     -- log cases, flag reopen-risk
     capacity_utilization.py   -- before/after-capex headroom arithmetic
     forward_pe.py             -- forward EPS/PE arithmetic
       |
       v
 [7] DRAFT report.md, section by section, per reference/report_format.md:
     Company Summary -> Value Chain Positioning (+ flow diagram, showing
     backward integration inside the company box, not upstream) ->
     Situation Classification -> Near/Medium/Long Term outlook (quote-
     verified, status-pointer-tagged) -> Marquee & Niche Customers ->
     Capex/Milestones/Certifications Timeline -> [CDMO Pipeline if
     applicable] -> Financial Performance Summary (+ balance-sheet anomaly
     check) -> Segment-wise Performance -> Order Book -> Manufacturing
     Locations (+ Raw Material Sourcing: domestic/imported %, country-wise
     breakdown, export-shipment/customs data) -> Capacity Utilization &
     Headroom (industry-specific physical unit, multi-purpose-plant flag)
     -> [TAM if disclosed] -> Valuation/Forward PE (+ median PE;
     third-party broker/agency research -- e.g. Nuvama -- when the user
     supplies a report, folded inline here or wherever else it's
     relevant rather than into its own section, every such point tagged
     `[BROKER_DDMMYYYY]`) -> Industry Tailwinds/Headwinds ->
     Competitive Positioning: Peer
     Comparison -> MOATs (entry barriers, IP/technology moat, product
     criticality, switching costs — bullets) -> Technical Snapshot (table
     or bullets) -> Promoter/Governance (shareholding, fund raises,
     ratings, litigation) -> Investment Thesis Summary (bullets) -> Key
     Risks -> Verdict -> Sources.
     Every quote checked as an exact substring of the source text before
     use; every conditional section either states its finding or says
     explicitly why it's absent.
       |
       v
 [8] BUILD THE VISUAL PDF
     html_helpers.py assembles the HTML body (cover, cards, timeline,
     tables -- tables are the default, charts.py is opt-in only) styled by
     assets/report_style.css, rendered by WeasyPrint.
     pdftoppm renders a few pages back to JPEG so the result gets visually
     checked (no clipped tables, no dead whitespace, no leaked HTML
     entities) before delivery.
       |
       v
 [9] SAVE & MARK
     ~/.report-generator/output/<slug>/<Company>_report.md
     ~/.report-generator/output/<slug>/<Company>_report.pdf
     check_freshness.py --mark-processed "<label>" --price <price>
     ~/.report-generator/research_cache/<slug>/*_history.json updated (durable across future runs)
       |
       v
 [10] YOU get both files, plus a short spoken summary -- not a chat
      re-narration of the whole report.
```

## Directory structure

```
skills/report-generator/           (this skill's directory, inside the Research-Advisory plugin)
|-- SKILL.md                      Trigger phrases, the numbered pipeline above,
|                                  Step 0 freshness logic, token-discipline rules
|-- reference/
|   |-- report_format.md          Section-by-section spec: what each section
|   |                             contains, table vs. bullet vs. chart defaults,
|   |                             the Assembly pattern for the visual PDF
|   |-- source_playbook.md        Which tool/site for which fact, fallback paths,
|                                  the 18-month-window and new-quarter-refresh rules
|-- scripts/                      Local Python -- no network except the tracker
|   |-- pdf_to_text.py            scripts explicitly noted below
|   |-- pdf_to_text_parallel.py   multi-core full extraction for large PDFs
|   |-- semantic_search.py        BM25 relevance search when grep comes up thin
|   |-- verify_report.py          mandatory deterministic pre-delivery checks
|   |                             (html markers, PDF producer, broker tags,
|   |                             sources/cache split, freshness, extraction
|   |                             coverage, sourcing depth -- see below)
|   |-- extract_theme_quotes.py
|   |-- guidance_tracker.py
|   |-- fundraise_tracker.py
|   |-- rating_tracker.py
|   |-- litigation_tracker.py
|   |-- capacity_utilization.py
|   |-- forward_pe.py
|   |-- check_freshness.py
|   |-- charts.py                 matplotlib -- opt-in, not called by default
|   |-- html_helpers.py           HTML builders for the visual PDF
|   |-- report_to_pdf.py          legacy reportlab fallback (text-only)
|   `-- build_report.py           renders the outlook bullets from bullets.json
|-- assets/
|   `-- report_style.css          Visual styling for the WeasyPrint PDF
`-- examples/
    `-- venus_pipes_report.md     Outlook-section style reference

~/.report-generator/                 (OUTSIDE the plugin, in your home directory --
                                       see the repo-level README's Plugin structure)
|-- sources/<company_slug>/          Bulky raw source material, one folder per
|   |                                company -- regenerable by refetching, not
|   |                                meant to be backed up or shared. A single
|   |                                annual report's extracted text alone can run
|   |                                1MB+, which is why this stays separate from
|   |                                research_cache/ below.
|   |-- *.pdf / *.txt             Fetched concalls, investor presentations,
|   |                             annual reports (extracted, full documents)
|   |-- *.bm25.pkl                semantic_search.py's cached relevance index
|   `-- customers/<customer_slug>/  Last 4 quarters of a marquee customer's own
|                                    concalls, if it's itself publicly listed
|                                    (any exchange) -- for demand corroboration only
|-- research_cache/<company_slug>/   Small, synthesized working state -- this is
|   |                                the part worth backing up or sharing; safe
|   |                                to zip/copy on its own without sources/
|   |-- guidance_history.json     Every outlook item ever logged + status
|   |-- fundraise_history.json    Every fund raise + named allottees
|   |-- rating_history.json       Every rating action, every agency
|   |-- litigation_history.json   Every case, reopen-risk flagged
|   |-- candidate_quotes/         extract_theme_quotes.py's raw, per-transcript,
|   |   `-- <label>_candidate_quotes.json  heuristic (over-inclusive) candidate
|   |                             dumps -- kept here (not sources/) because each
|   |                             one is only tens of KB, unlike the .txt/.pdf
|   |                             it's derived from. NOT the same file as the
|   |                             curated quotes.json below.
|   |-- quotes.json               The CURATED quotes that actually made it into
|   |                             the drafted report, mapped to their source --
|   |                             distinct from candidate_quotes/ above
|   |-- bullets.json              Synthesized outlook bullets built from quotes.json
|   |-- state.json                Last quarter processed, last price used
|   `-- report.md                 The drafted report (source of truth)
`-- output/<company_slug>/           User-facing deliverables only, created
    |                                locally on your first run
    |-- <Company>_report.md
    `-- <Company>_report.pdf
```

`sources/`, `research_cache/`, and `output/` are **not part of this skill or the
plugin** — none exists on a fresh clone, and using the skill never adds, modifies, or
deletes anything under `skills/report-generator/` itself; all three directories live
under `~/.report-generator/` instead and are pure local state. `sources/` is bulky raw
material (safe to delete and refetch, never delivered to you and not worth backing
up); `research_cache/<company_slug>/` deliberately excludes `sources/`'s raw PDFs/text
so the whole folder stays small — copy or share just that one folder (e.g. `cp -R
~/.report-generator/research_cache/<company_slug> ~/backup/`) to preserve or hand off
a company's full analysis history without the bulky source documents; `output/` is
the deliverable (never overwritten with intermediate state).

## Persistent state — how regeneration stays cheap

The pipeline's core efficiency trick: facts that don't change quarter to quarter get
logged **once**, into small JSON files, rather than re-derived on every run.

| File | What it durably tracks | Grows by |
|---|---|---|
| `guidance_history.json` | Every outlook item ever drafted, its status (Pending/On Track/Delivered/Delayed/Missed), and `--supersedes-id` links across quarters when a guide is revised | One append per new/revised outlook item |
| `fundraise_history.json` | Every preferential issue/warrant/NCD/term loan, named allottees, conversion/lapse status | One append per raise, `update-status` on outcome |
| `rating_history.json` | Every rating action, every agency, with a currently-in-force summary and a downgrade/negative-outlook flag | One append per rating action |
| `litigation_history.json` | Every case, with a reopen-risk flag for "dismissed but appealable" matters | One append per case, `update-status` on outcome |
| `state.json` | The last concall/quarter label processed and the last price used | Overwritten each run |

On a `no_state` (first) run, all four get built from scratch. On a `new_quarter`
refresh, each tracker only receives an *append* for what's actually new this quarter —
the guidance-reliability history, fund-raise register, rating trajectory, and
litigation docket all carry forward untouched. This is also what makes the
Promoter/Governance section's multi-quarter track record possible at all: the report
can say "guided X in Q3, revised to Y in Q4, now On Track" because the evolution is
reconstructed from this log, not re-read from old transcripts each time.

On a `force_full` run (explicit "regenerate from scratch" request), every *report
section* gets rebuilt from freshly refetched sources — but these four tracker files
are treated the same as any other run: they still only receive appends, never a
reset. "From scratch" describes the report content, not the historical fact log.

## Script responsibilities

| Script | Role | Network? |
|---|---|---|
| `pdf_to_text.py` | Convert a fetched PDF to plain text (full extraction by default; `--pages` only for TOC scouting or re-extracting an already-located range) | No |
| `pdf_to_text_parallel.py` | Same full-document extraction as `pdf_to_text.py`, split across worker processes for large (150+ page) PDFs — verified byte-identical output, refuses to write a partial file if a worker fails | No |
| `semantic_search.py` | BM25-ranked relevance search over an extracted `.txt` when a grep keyword guess plausibly missed something due to phrasing | No |
| `verify_report.py` | **Mandatory** deterministic guardrails, 16 subcommands in 3 tiers — see `SKILL.md`'s "Deterministic Guardrails" section: **Input** (`sniff` classifies an uploaded PDF's type before routing it; `slug` validates a company slug is filesystem-safe) — **Execution** (`scope` confirms no file was written inside the plugin's own directory; `reproduction` confirms no verbatim multi-word copy from a broker source) — **Output** (`html` confirms report.html has the required html_helpers.py CSS markers; `pdf` confirms producer/page-count; `report` confirms sections present + broker tags appear; `quotes` confirms every quoted outlook string is verbatim against a source `.txt`; `disclaimer` confirms the required disclaimer language; `sources` confirms the sources/research_cache split; `freshness` confirms `--mark-processed` was called; `extraction` confirms an annual report's extraction covers page 1 through the real last page; `depth` confirms the standard 6-quarter/2-AR/6-investor-presentation sourcing depth, grouping chunked annual-report extractions by document identity; `whitespace` confirms no interior or final page is dead/mostly-blank — only the cover page may be sparse; `ratings` confirms a rating-agency recency check within the last 6 months, informational only; `paragraphs` flags any paragraph exceeding ~10 rendered lines report-wide, with Verdict-specific "trim, don't bullet" guidance) | No |
| `extract_theme_quotes.py` | Bucket transcript lines into near/medium/long-term candidate quotes | No |
| `guidance_tracker.py` | Log/report outlook items and their status pointers | No |
| `fundraise_tracker.py` | Log/report fund raises, named allottees, lapse flags | No |
| `rating_tracker.py` | Log/report credit-rating actions, downgrade flags | No |
| `litigation_tracker.py` | Log/report litigation, reopen-risk flags | No |
| `capacity_utilization.py` | Before/after-capex revenue-headroom arithmetic | No |
| `forward_pe.py` | Forward EPS/PE arithmetic | No |
| `check_freshness.py` | Decide `no_state`/`up_to_date`/`new_quarter`/`force_full` (`--force`), mark state | No |
| `charts.py` | matplotlib chart generators — **opt-in only**, not called by default | No |
| `html_helpers.py` | HTML builders (cover, cards, tables, timeline, verdict box) for the visual PDF | No |
| `report_to_pdf.py` | Legacy markdown→PDF via reportlab, text-only fallback if WeasyPrint is unavailable | No |

All fetching (screener.in, BSE/NSE, PDFs, WebSearch) happens through the platform's own
`WebFetch`/`WebSearch`/browser tools, never through a script — the scripts above only
ever touch local files already saved to `~/.report-generator/sources/<slug>/`.

## Report section pipeline

Each section in the final report maps to a specific source and, where applicable, a
specific script:

| Section | Primary source | Script involved |
|---|---|---|
| Company Summary, Value Chain Positioning | screener.in About, concall opening remarks, annual report | — |
| Situation Classification | Synthesized from everything gathered | — |
| Near/Medium/Long Term outlook | Concall transcript | `extract_theme_quotes.py`, `guidance_tracker.py` |
| Marquee & Niche Customers | Investor presentation, annual report; last 4 quarters of a marquee customer's own concalls if it's itself publicly listed — checked via Google Finance's universal `TICKER:EXCHANGE` lookup first (works across NASDAQ/NYSE/LON/XETR/NSE/BSE/etc.), then the customer's own IR page | — |
| Capex/Milestones/Certifications Timeline | Investor presentation, BSE/NSE announcements | — |
| Financial Performance Summary + balance-sheet anomaly check | screener.in, investor presentation | — |
| Segment-wise Performance, Order Book | Investor presentation, concall | — |
| Manufacturing Locations + Raw Material Sourcing (domestic/imported %, country-wise, export-shipment data) | Annual report PP&E/raw-material note, investor presentation, shipment-data aggregators | — |
| Capacity Utilization & Headroom (industry-specific physical unit, multi-purpose-plant flag) | Concall Q&A, investor presentation | `capacity_utilization.py` |
| Total Addressable Market | Investor presentation (only if disclosed) | — |
| Valuation — Forward PE (+ median PE) | screener.in, concall guidance, secondary aggregator | `forward_pe.py` |
| Industry Tailwinds/Headwinds | Peer concalls, sector reports (WebSearch) | — |
| Competitive Positioning: Peer Comparison | screener.in Peers tab, peer investor presentations | — |
| MOATs (entry barriers, IP/technology moat, product criticality, switching costs) | Concall Q&A, annual report competitive-strengths section | — |
| Technical Snapshot (table/bullets) | Technicals provider (Trendlyne/MoneyControl/etc.) | — |
| Promoter/Governance — guidance reliability | Cached history | `guidance_tracker.py` |
| Promoter/Governance — fund raises | BSE/NSE, credit-rating rationale | `fundraise_tracker.py` |
| Promoter/Governance — credit ratings | CRISIL/ICRA/CARE/India Ratings/Acuite/Brickwork | `rating_tracker.py` |
| Promoter/Governance — litigation | Annual report Contingent Liabilities note | `litigation_tracker.py` |
| Investment Thesis Summary, Key Risks, Verdict | Synthesized from everything above | — |
| Sources | Every citation used above | — |

**Third-party broker/agency research** (Nuvama, Motilal Oswal, etc.) doesn't have a
row of its own above because it doesn't have a dedicated section — it's never fetched
proactively, only used when the user directly uploads a report, and its facts fold
directly into whichever of the sections above they belong to (a target price into
Valuation, a sector read into Industry Tailwinds/Headwinds, a thesis point into
Investment Thesis Summary, a flagged risk into Key Risks). What keeps it distinguishable
from the pipeline's own independently-sourced numbers is an inline
`[BROKER_DDMMYYYY]` tag on every such point (e.g. `[NUVAMA_29042026]`), not a
separate section.

## Installation

This skill ships as part of the `Research-Advisory` **plugin** — see the
[repo-level README](../../README.md#installation) for cloning and loading
the plugin into Claude Code (`claude --plugin-dir .`, or symlinking into
`~/.claude/plugins/`). Once the plugin is loaded, this skill is available
automatically; there's no separate per-skill installation step.

After loading the plugin, install this skill's own dependencies — see
Setup below — then confirm with `research <any company name>` and check
that Claude follows the freshness-check → sourcing → report pipeline
described above, creating `~/.report-generator/research_cache/<company_slug>/`
and `~/.report-generator/output/<company_slug>/` as it goes.

## Components

**Skills**

- `report-generator` — the core report-generation pipeline described in full above.
  Produces a visual PDF (cover page with a situation badge, metric cards, a
  color-coded timeline, and dense data tables — tables are the default for
  anything with real numbers, charts are opt-in) alongside the Markdown
  source of truth: Company Summary with a headline stat card grid, Value
  Chain Positioning writeup with a flow diagram, a Situation Classification
  (turnaround / steady compounder / cyclical / structural growth /
  structural decline), Near/Medium/Long Term outlook (each bullet sourced
  to a management quote with a status pointer tracked across concalls),
  marquee/niche customers (bullet list), capex/milestones/certifications
  timeline, CDMO pipeline (where applicable), multi-year financial trend
  table plus a balance-sheet anomaly check, segment-wise performance,
  order book, manufacturing locations (bullet list) plus Raw Material
  Sourcing (domestic vs. imported %, country-wise breakdown of any
  imported portion where disclosed, and an export-shipment/customs-data
  check), capacity utilization and headroom measured in the industry's own
  physical unit (table, flagging any shared multi-purpose capacity pool),
  TAM, forward PE (including the company's own historical median PE;
  when the user supplies a third-party broker/agency research report —
  e.g. Nuvama — its facts are folded inline wherever relevant, each
  tagged `[BROKER_DDMMYYYY]` rather than placed in a separate section),
  industry tailwinds/headwinds, a peer comparison table (IP/technology
  moat, niche customers, certifications), a dedicated MOATs section
  (entry barriers, IP/technology moat, product criticality, switching
  costs — bullets), a technical snapshot (table or bullets, never prose),
  promoter/governance track record (tabled shareholding trend, fund raises
  with named allottees where disclosed, credit ratings, litigation), a
  synthesized Investment Thesis Summary (bullets), mandatory Key
  Risks/Red Flags, a Verdict, and a numbered Sources list. **Every run
  produces both a Markdown report and a formatted PDF** in
  `~/.report-generator/output/<company_slug>/` — PDF export is not
  optional or request-gated, it happens automatically as the last step of
  every run.

## Setup

No API keys or environment variables required. All sourcing is done via web
search/fetch (screener.in, BSE/NSE, credit-rating agency sites) and locally
bundled Python 3 scripts — nothing here needs a server or daemon.

**Python packages:**

```bash
pip install pdfplumber weasyprint matplotlib reportlab --break-system-packages
```

| Package | Used by | Required? |
|---|---|---|
| `pdfplumber` | `pdf_to_text.py` — PDF → plain text | Yes, for every source PDF |
| `weasyprint` | Primary visual-PDF renderer (`python3 -m weasyprint ...`) | Yes, for the default PDF pipeline |
| `matplotlib` | `charts.py` | Only if you ask for a chart version of a section — opt-in, not default |
| `reportlab` | `report_to_pdf.py` | Only as the legacy text-only fallback if WeasyPrint can't be installed |

**System packages** (native libraries WeasyPrint and the verification step
need — these aren't pip-installable):

```bash
# macOS
brew install pango poppler

# Debian/Ubuntu
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 poppler-utils
```

`poppler` provides `pdftoppm`, which SKILL.md uses to render a few PDF pages
back to JPEG so the output gets visually checked (no clipped tables, no dead
whitespace) before delivery — not optional, this runs on every report.

If `weasyprint` genuinely can't be installed in a given environment, the
skill falls back to a text-only `reportlab` PDF (`report_to_pdf.py`) rather
than skipping PDF export entirely.

**Known gotcha**: `pdfplumber` occasionally mis-extracts text from PDFs with
non-standard embedded fonts (garbled/scrambled words rather than a clean
extraction — seen on a few Indian small-cap investor decks). If a source PDF
comes out unreadable, `pdftotext -layout <input.pdf> <output.txt>` (from the
same `poppler` package above) is a reliable fallback that has cleanly
recovered every PDF `pdfplumber` garbled so far.

**Verify the install:**

```bash
python3 -c "import pdfplumber, weasyprint; print('ok')"
pdftoppm -v
```

`research_cache/` and `output/` are **not** part of this skill or shipped with
the plugin — neither exists inside `skills/report-generator/` at all; they
live under `~/.report-generator/` in your home directory instead (see the
repo-level README's Plugin structure section), and start out absent on a
fresh clone. The first time you research a given company, the full pipeline
runs and both directories get created there, under
`~/.report-generator/research_cache/<company_slug>/` and
`~/.report-generator/output/<company_slug>/`; every subsequent request for
that same company regenerates cheaply via the
built-in freshness check (see the flow diagram above) instead of rebuilding
from scratch, using whatever you've built up locally.

## Usage

Trigger with natural language, naming the company each time — no slash command. There
are four distinct things you can ask for; the phrasing you use is what tells Claude
which one you mean.

### 1. Generate a report for a new company

First run for this company — goes through the full pipeline (Step 0 reports
`no_state`), fetching every source from scratch and building every tracker file for
the first time.

```
research <Company Name>
generate a report on <Company Name>
analyse <Company Name>'s concall
what's the story with <Company/Ticker>
build me a thesis on <Company Name>
do a deep dive on <Company Name> — is it a buy?
```

### 2. Update the report for an already-generated company

The cheap, default path for a company you've already researched. Only refetches
what's actually new since the last run (`up_to_date` → nothing to do, or
`new_quarter` → just the new concall/results); everything else carries forward from
the cached `report.md`.

```
regenerate <Company Name>'s report
refresh <Company Name>'s report
update <Company Name>'s report
```

### 3. Re-generate the report from scratch for an already-generated company

Explicitly bypasses the cache: every source document gets refetched fresh and every
section gets rebuilt, rather than carrying anything forward from the cached
`report.md`. Use this if you think the last report was built on stale or incomplete
sourcing. The tracker histories (`guidance_history.json`, `fundraise_history.json`,
`rating_history.json`, `litigation_history.json`) are cumulative real-world records
and are **not** wiped by this — they keep accumulating exactly as on any other run.
Only phrasing that explicitly says "from scratch" / "rebuild" / "ignore the cache"
triggers this path — plain "regenerate"/"refresh"/"update" always means option 2 above.

```
regenerate <Company Name>'s report from scratch
rebuild <Company Name> from scratch
redo <Company Name>'s report from scratch
ignore the cache and redo <Company Name>
```

### 4. Invoking without a company name

If you ask for a report without naming a company (e.g. just "research", "generate a
report", "update the report"), Claude won't guess or silently reuse a company from
earlier in the conversation — it asks which company you mean before doing anything
else.

### Other invocation notes

- `rerun for <Company A> and <Company B>` — processes multiple companies
  independently in one request; each can be a new company, an update, or a
  from-scratch rebuild independently.
- Uploading a concall transcript, investor presentation, or annual report PDF
  directly also triggers the skill, preferring the uploaded document over fetching
  one.

Every run ends with both `~/.report-generator/output/<company_slug>/<Company>_report.md` and
`~/.report-generator/output/<company_slug>/<Company>_report.pdf` — you don't need to separately
ask for a PDF.

## Accuracy discipline

A personal research document, not a distributed advisory product — it freely
states a situation classification, a synthesized investment thesis, and a
verdict with a directional read. The discipline that matters is never
manufacturing a view: every material fact traces to a cited source and date,
unverified management claims are flagged as such, and if the research
doesn't support a real thesis the report says so plainly instead of padding
it out. Any directional valuation read stays tied to a specific cited
comparison (peers, history, growth), never a bare adjective.

## Never drop anything silently

A standing rule that applies at every step of the pipeline above, not just the
final report: if a source can't be fetched, a fetch times out, a rate limit or
size/page cap is hit, an extraction comes back empty or garbled, a worker in
`pdf_to_text_parallel.py` fails and the run falls back to something narrower, a
tracker section comes back with nothing, or the visual-PDF pipeline falls back
to the legacy ReportLab renderer — **that gap is stated explicitly, in the
report section it affects, every time.** Never let a gap read the same as a
verified "nothing here." A reader should never have to discover independently
that something was skipped, throttled, capped, or dropped; if in doubt, flag
it. See `SKILL.md`'s "Never drop anything silently" section for the full rule
and worked examples (fetch failures, partial extraction, rate limits, empty
sections, renderer fallbacks, and asymmetric gaps across a multi-company
batch).
