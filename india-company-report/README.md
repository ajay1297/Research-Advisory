# India Company Report

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
|  research_cache/<company_slug>/                                         |
|  raw/*.txt|*.pdf   -- fetched source documents                          |
|  *_history.json    -- durable, append-only fact logs (see below)        |
|  state.json         -- freshness marker (last quarter processed)        |
|  report.md          -- the drafted report, source of truth              |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  PDF ASSEMBLY (WeasyPrint via html_helpers.py + assets/report_style.css)|
|  cover badge -> cards -> outlook -> 18 sections -> thesis -> verdict     |
+------------------------------------------------------------------------+
                                  |
                                  v
+------------------------------------------------------------------------+
|  output/<company_slug>/                                                 |
|  <Company>_report.md                                                    |
|  <Company>_report.pdf                                                   |
+------------------------------------------------------------------------+
```

## End-to-end flow — prompt to PDF

This is what actually happens, in order, from the moment you type a prompt to the
moment two files land in `output/`. Branches matter here — most of the token/time
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
     check_freshness.py <slug> --latest-seen "<label>"
       |
       +---------------------+---------------------+
       |                     |                     |
       v                     v                     v
   no_state              up_to_date            new_quarter
   (first run)      (nothing changed)     (a new quarter posted)
       |                     |                     |
       |                     v                     |
       |            Reuse cached report.md          |
       |            as-is. Skip to [8] if only       |
       |            price changed (rerun              |
       |            forward_pe.py alone).            |
       |                                             |
       v                                             v
 [4] FULL SOURCE PIPELINE                  [4'] INCREMENTAL PIPELINE
     Fetch + process everything below           Fetch ONLY the new quarter's
     for the first time.                        concall + investor presentation
                                                 + screener.in's last 1-2 columns.
                                                 Reuse everything else already in
                                                 research_cache/<slug>/ untouched.
       |                                             |
       +---------------------+-----------------------+
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
     Every fetched document is saved to research_cache/<slug>/raw/ first.
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
     Company Summary -> Value Chain Positioning (+ flow diagram) ->
     Situation Classification -> Near/Medium/Long Term outlook (quote-
     verified, status-pointer-tagged) -> Marquee & Niche Customers ->
     Capex/Milestones/Certifications Timeline -> [CDMO Pipeline if
     applicable] -> Financial Performance Summary (+ balance-sheet anomaly
     check) -> Segment-wise Performance -> Order Book -> Manufacturing
     Locations (+ raw-material import dependency) -> Capacity Utilization
     & Headroom -> [TAM if disclosed] -> Valuation/Forward PE (+ median PE)
     -> Industry Tailwinds/Headwinds -> Competitive Positioning (peers,
     entry barriers, product criticality) -> Technical Snapshot ->
     Promoter/Governance (shareholding, fund raises, ratings, litigation)
     -> Investment Thesis Summary -> Key Risks -> Verdict -> Sources.
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
     output/<slug>/<Company>_report.md
     output/<slug>/<Company>_report.pdf
     check_freshness.py --mark-processed "<label>" --price <price>
     research_cache/<slug>/*_history.json updated (durable across future runs)
       |
       v
 [10] YOU get both files, plus a short spoken summary -- not a chat
      re-narration of the whole report.
```

## Directory structure

```
india-company-report/
|-- SKILL.md                      Trigger phrases, the numbered pipeline above,
|                                  Step 0 freshness logic, token-discipline rules
|-- reference/
|   |-- report_format.md          Section-by-section spec: what each section
|   |                             contains, table vs. bullet vs. chart defaults,
|   |                             the Assembly pattern for the visual PDF
|   |-- source_playbook.md        Which tool/site for which fact, fallback paths,
|                                  the 6-month-window and new-quarter-refresh rules
|-- scripts/                      Local Python -- no network except the tracker
|   |-- pdf_to_text.py            scripts explicitly noted below
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
|-- examples/
|   `-- venus_pipes_report.md     Outlook-section style reference
|-- research_cache/<company_slug>/   Working state, one folder per company
|   |-- raw/                      Fetched PDFs/text, source documents
|   |-- guidance_history.json     Every outlook item ever logged + status
|   |-- fundraise_history.json    Every fund raise + named allottees
|   |-- rating_history.json       Every rating action, every agency
|   |-- litigation_history.json   Every case, reopen-risk flagged
|   |-- state.json                Last quarter processed, last price used
|   `-- report.md                 The drafted report (source of truth)
`-- output/<company_slug>/           User-facing deliverables only
    |-- <Company>_report.md
    `-- <Company>_report.pdf
```

`research_cache/` is working memory (safe to regenerate from scratch, never delivered
to you); `output/` is the deliverable (never overwritten with intermediate state).

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

## Script responsibilities

| Script | Role | Network? |
|---|---|---|
| `pdf_to_text.py` | Convert a fetched PDF to plain text | No |
| `extract_theme_quotes.py` | Bucket transcript lines into near/medium/long-term candidate quotes | No |
| `guidance_tracker.py` | Log/report outlook items and their status pointers | No |
| `fundraise_tracker.py` | Log/report fund raises, named allottees, lapse flags | No |
| `rating_tracker.py` | Log/report credit-rating actions, downgrade flags | No |
| `litigation_tracker.py` | Log/report litigation, reopen-risk flags | No |
| `capacity_utilization.py` | Before/after-capex revenue-headroom arithmetic | No |
| `forward_pe.py` | Forward EPS/PE arithmetic | No |
| `check_freshness.py` | Decide `no_state`/`up_to_date`/`new_quarter`, mark state | No |
| `charts.py` | matplotlib chart generators — **opt-in only**, not called by default | No |
| `html_helpers.py` | HTML builders (cover, cards, tables, timeline, verdict box) for the visual PDF | No |
| `report_to_pdf.py` | Legacy markdown→PDF via reportlab, text-only fallback if WeasyPrint is unavailable | No |

All fetching (screener.in, BSE/NSE, PDFs, WebSearch) happens through the platform's own
`WebFetch`/`WebSearch`/browser tools, never through a script — the scripts above only
ever touch local files already saved to `research_cache/<slug>/raw/`.

## Report section pipeline

Each section in the final report maps to a specific source and, where applicable, a
specific script:

| Section | Primary source | Script involved |
|---|---|---|
| Company Summary, Value Chain Positioning | screener.in About, concall opening remarks, annual report | — |
| Situation Classification | Synthesized from everything gathered | — |
| Near/Medium/Long Term outlook | Concall transcript | `extract_theme_quotes.py`, `guidance_tracker.py` |
| Marquee & Niche Customers | Investor presentation, annual report | — |
| Capex/Milestones/Certifications Timeline | Investor presentation, BSE/NSE announcements | — |
| Financial Performance Summary + balance-sheet anomaly check | screener.in, investor presentation | — |
| Segment-wise Performance, Order Book | Investor presentation, concall | — |
| Manufacturing Locations + raw-material import dependency | Annual report PP&E note, investor presentation | — |
| Capacity Utilization & Headroom | Concall Q&A, investor presentation | `capacity_utilization.py` |
| Total Addressable Market | Investor presentation (only if disclosed) | — |
| Valuation — Forward PE (+ median PE) | screener.in, concall guidance, secondary aggregator | `forward_pe.py` |
| Industry Tailwinds/Headwinds | Peer concalls, sector reports (WebSearch) | — |
| Competitive Positioning (peers, entry barriers, criticality) | screener.in Peers tab, peer investor presentations | — |
| Technical Snapshot | Technicals provider (Trendlyne/MoneyControl/etc.) | — |
| Promoter/Governance — guidance reliability | Cached history | `guidance_tracker.py` |
| Promoter/Governance — fund raises | BSE/NSE, credit-rating rationale | `fundraise_tracker.py` |
| Promoter/Governance — credit ratings | CRISIL/ICRA/CARE/India Ratings/Acuite/Brickwork | `rating_tracker.py` |
| Promoter/Governance — litigation | Annual report Contingent Liabilities note | `litigation_tracker.py` |
| Investment Thesis Summary, Key Risks, Verdict | Synthesized from everything above | — |
| Sources | Every citation used above | — |

## Installation

This plugin is distributed as a single `india-company-report.plugin` file.

1. In the Cowork chat where you received this file, look for its rich-preview
   card in the conversation.
2. Click through the preview to browse the plugin's contents, then press the
   install/accept button on the card. This is the same flow used for any
   other Cowork plugin delivered this way.
3. Once installed, the `research` skill is available immediately — no
   further configuration, API keys, or setup steps are required.

If you received this file outside of Cowork (e.g. saved to disk), re-upload
it into a Cowork chat to trigger the same install-preview flow — plugins
are not installed by unzipping manually.

To confirm it installed correctly, say `research <any company name>` (or
`research Astra Microwave`, which already has cached research state — see
Setup below) and check that Claude follows the freshness-check → sourcing →
report pipeline described above.

## Components

**Skills**

- `research` — the core report-generation pipeline described in full above.
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
  order book, manufacturing locations (bullet list) plus raw-material
  import dependency where disclosed, capacity utilization and headroom
  (table), TAM, forward PE (including the company's own historical median
  PE), industry tailwinds/headwinds, a peer comparison table (IP/
  technology moat, niche customers, certifications, entry barriers,
  product criticality), a readable technical snapshot, promoter/
  governance track record (tabled shareholding trend, fund raises with
  named allottees where disclosed, credit ratings, litigation), a
  synthesized Investment Thesis Summary, mandatory Key Risks/Red Flags, a
  Verdict, and a numbered Sources list. **Every run produces both a
  Markdown report and a formatted PDF** in `output/<company_slug>/` — PDF
  export is not optional or request-gated, it happens automatically as the
  last step of every run.

## Setup

No configuration or environment variables required. All sourcing is done
via web search/fetch (screener.in, BSE/NSE, credit-rating agency sites) and
locally bundled Python scripts (PDF extraction, quote mining, guidance/
fundraise/rating/litigation tracking, forward-PE math, chart generation,
PDF report export). The visual PDF pipeline needs `matplotlib` and
`weasyprint` (`pip install matplotlib weasyprint --break-system-packages`,
plus the native `pango`/`poppler` libraries on macOS via
`brew install pango poppler`); if either is missing in a given environment,
the skill falls back to a text-only reportlab PDF rather than skipping PDF
export.

Ships with pre-populated `research_cache/` and finished `output/` reports
(both `.md` and `.pdf`) for a number of companies already, including
**Venus Pipes & Tubes** (see `output/venus_pipes_tubes/`) — check
`output/` and `research_cache/` for the current list. Any company already
present regenerates cheaply via the built-in freshness check (see the flow
diagram above) instead of rebuilding from scratch; a genuinely new company
runs the full pipeline the first time and is cached for every subsequent
refresh.

## Usage

Trigger with natural language, naming the company each time:

- `research <Company Name>`
- `generate a report on <Company Name>`
- `analyse <Company Name>'s concall`
- `regenerate <Company Name>'s report` / `refresh <Company Name>'s report`
- `what's the story with <Company/Ticker>` / `build me a thesis on <Company Name>`
- `rerun for <Company A> and <Company B>` — processes multiple companies
  independently in one request

Uploading a concall transcript, investor presentation, or annual report PDF
directly also triggers the skill, preferring the uploaded document over
fetching one.

Every run ends with both `output/<company_slug>/<Company>_report.md` and
`output/<company_slug>/<Company>_report.pdf` — you don't need to separately
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
