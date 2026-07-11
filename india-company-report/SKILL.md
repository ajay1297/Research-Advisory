---
name: india-company-report
description: >
  Generate or refresh a company research report (Near/Medium/Long Term outlook backed
  by sourced management quotes, forward PE, industry tailwinds/headwinds, technical
  snapshot, promoter/governance track record, and key risks) for an Indian listed
  company from its concall transcript, investor presentation, annual report, and
  screener.in data. Activate when the user says "research <company>", "generate a
  report on <company>", "regenerate/update/refresh <company>'s report", "analyse
  <company>'s concall", or shares/references concall transcripts, investor
  presentations, or annual reports for a specific company. Research and educational
  framing only — never investment advice.
---

# India Company Report

Produces a report with these sections, in order: Near Term (1-2Q) / Medium Term
(6-12mo) / Long Term (1+yr) outlook — each bullet a claim + sourced quote — then
Valuation (Forward PE), Industry Tailwinds/Headwinds, Technical Snapshot, Promoter/
Governance Track Record, and Key Risks. See `examples/venus_pipes_report.md` for the
outlook-section style and `reference/report_format.md` for the full spec including
the five sections after it.

Do not read `reference/report_format.md` or `reference/source_playbook.md` in full
until you actually need them (step 2+ below). Read `examples/venus_pipes_report.md`
once, when drafting.

## The core rule: never load raw source documents into context

Concall transcripts run 15-40 pages, investor decks 20-50 slides, annual reports
100-300 pages. Every step below exists to avoid reading these directly. Always go
through `scripts/`, never paste a full transcript/PDF into your own reasoning.

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
     the guidance-reliability history from scratch.
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

**Near/Medium/Long Term outlook** — from the candidate quotes JSON, pick the
strongest 2-3 verbatim-quoted bullets per horizon per `reference/report_format.md`.
Every quote must be checked as an exact substring of the source text — do not
truncate a quote and add punctuation that isn't in the original (that fabricates a
sentence ending). If in doubt, `grep` the exact phrase back against the raw
transcript before finalizing.

**Valuation (Forward PE)** — only if revenue guidance was found above. Pull current
price, shares outstanding (equity capital ÷ face value), and trailing PAT/revenue from
the screener.in fetch already done. Run `scripts/forward_pe.py` with the guided
revenue (and guided margin if management gave one, else trailing margin flagged as an
assumption). If the user supplied their own price, pass that instead and label it.

**Industry Tailwinds/Headwinds** — per `reference/source_playbook.md`, search outward
(peers, sector bodies, rating-agency sector notes), 2-4 bullets, one source each.

**Technical Snapshot** — pull a pre-computed technicals summary (moving averages,
RSI, support/resistance) from a technicals provider per the playbook; don't compute
indicators from scraped OHLC data yourself. Timestamp it.

**Promoter/Governance Track Record** — after logging this quarter's guidance via
`scripts/guidance_tracker.py add-guidance` (and any actual-vs-prior-guidance via
`add-actual` if this quarter's results closed out a previously guided period), run
`scripts/guidance_tracker.py <company_slug> report` (default lookback is 2 quarters /
6 months — the standing default, don't override it) and reproduce its flag verbatim if
it found a pattern of misses. Add promoter holding trend / pledge / auditor flags from
the screener.in fetch.

**Key Risks** — 3-5 bullets pulling from what's already been gathered above (business/
execution, financial, governance, macro) — never invented.

## Save and cache

Save the final report as `.md` (or convert via the docx/pdf skill if the user wants a
formatted document) to the workspace folder. Save/update
`research_cache/<company_slug>/quotes.json`, `bullets.json`, `guidance_history.json`,
and `report.md`, then mark freshness state per Step 0.3.

## Compliance

Research summaries of publicly available information only. Forward PE is arithmetic
on a management estimate, not a valuation call — never follow it with "cheap/
expensive." If the user asks "should I buy/sell X", decline and redirect to a SEBI
registered investment advisor.
