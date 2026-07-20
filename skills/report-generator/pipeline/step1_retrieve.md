# Step 1 — Retrieve (Scope the Window, Fetch, Extract)

First of three step files (`step1_retrieve.md` → `step2_synthesize.md` →
`step3_memorize.md`), each owned by exactly one pipeline step — see `SKILL.md`'s
"Pipeline at a glance" for how they chain together. Standing rules that apply
*across* every step (token discipline, never-drop-anything-silently, accuracy
discipline) live in `reference/rules_and_validation.md`, not here — this file is
sequencing only.

This step has two halves that used to be separate pipeline steps and are now one,
because the first half's only output is the input to the second: **1a decides what
window to fetch**, **1b fetches and extracts it**. Do not treat 1a as optional or
skippable — it is what makes 1b cheap.

## Step 1a — Scope: what window, how much

The whole point is that regenerating a report never re-fetches and re-processes
every historical filing. BSE's announcements API is date-filtered at the source, so
the incremental sweep is a genuinely narrow API query, not a wide fetch that gets
discarded client-side.

1. Run `python3 scripts/pipeline/check_freshness.py <company_slug>` with the right
   flags for the request:
   - **From-scratch rebuild explicitly requested** (see `SKILL.md`'s "Interpreting
     the slash-command argument" section) — `--force`.
   - **Otherwise** — `--latest-seen "<YYYY-MM-DD>" --concall-dates
     "<comma-separated dates>"`. Those two dates come from the cheap BSE listing
     sweep described in 1b below: the latest filing's **full date** (e.g.
     `2026-04-29`, never "May 2026" or "Q4 FY26" — `check_freshness.py`'s docstring
     explains why a full date is required) and **every concall date returned**, not
     just the latest. If the company holds no concall at all, use the results filing
     date — see `reference/sourcing_depth.md`'s "If the company doesn't hold
     concalls" section.

   On a refresh there is a chicken-and-egg ordering here: you need a listing sweep to
   get `--latest-seen`. Run that listing sweep first with a deliberately wide window
   (cheap — one API call, no PDFs), read the dates off it, then call
   `check_freshness.py`, and use the window it returns to decide which of those rows
   actually get their PDFs fetched in 1b.

2. **Read the `bse_fetch_window` in the result — that is the `--from`/`--to` for
   every `bse_announcements.py` call in 1b.** Do not hand-compute a window or
   default to a fixed 18 months; the script already applied the policy:
   - `mode: "delta"` (refresh runs) — `from` is the last successful run's timestamp
     minus a 7-day overlap buffer, `to` is today. E.g. last success `2026-07-01`,
     running `2026-07-21` → sweep `20260624` to `20260721`. The backward overlap is
     deliberate and must not be narrowed: BSE filings land late, get amended, and get
     recategorized after the fact, so a window starting exactly at the last success
     silently drops them.
   - `mode: "full_depth"` (`no_state` / `force_full`) — floored to the full standard
     depth, since there is no prior state to be incremental against. Use the separate
     `annual_from` for the Annual Report sweep only; `from` covers everything else.

3. Read the `cadence` field before proceeding — if `recommended_sourcing_mode` comes
   back anything other than `standard`, follow its `note` (reduced-depth or
   no-concall fallback) rather than the standard 6-quarter assumption.

4. Act on the returned `status`. What each state means is in `check_freshness.py`'s
   own docstring; what to actually *do*, beyond that:
   - `no_state` → run the whole pipeline, full-depth window.
   - `force_full` → refetch every source document and rebuild every section,
     full-depth window. Tracker histories are never wiped — see the docstring.
   - `up_to_date` → reuse
     `~/.report-generator/research_cache/<company_slug>/report.md` as-is; skip 1b
     entirely. If the user only supplied a new price for the valuation section,
     recompute the forward PE inline (formula and labeling rules in
     `reference/report_sections.md`'s "Valuation — Forward PE" section) using the
     cached revenue-guidance/margin/shares inputs in
     `~/.report-generator/research_cache/<company_slug>/bullets.json` — carry the
     cached margin's guided-vs-assumed label forward unchanged, and refetch nothing.
   - `new_quarter` → fetch and parse only what falls in the delta window and isn't
     already in `~/.report-generator/sources/<company_slug>/`; do NOT reprocess
     transcripts already sitting there. Update the Near/Medium/Long Term bullets from
     the new quarter (they supersede the old ones), but only *append* one new entry
     to `guidance_history.json` via `scripts/helpers/guidance_tracker.py` rather than
     rebuilding the guidance-reliability history — the exact fetch checklist for this
     case is `reference/sourcing_depth.md`'s "Regenerating for a new quarter" section.

5. After the run finishes (full or incremental), call
   `python3 scripts/pipeline/check_freshness.py <company_slug> --mark-processed
   "<YYYY-MM-DD>" --price <price>` — same full-date requirement as `--latest-seen`,
   since that string is exactly what a future run compares against. This also stamps
   `last_success_at`, which is the anchor the *next* run's delta window counts back
   from. Skipping it doesn't just lose the label — it forces the next run back to a
   full-depth sweep. It belongs at the very end of Step 3, not here; noted here so the
   loop is visible in one place.

**Standard sourcing depth is the last 2 annual reports and last 6 quarters of
concalls plus each quarter's official results press release** — the default for every
first-time run, and what `mode: "full_depth"` encodes. Full rationale and exactly what
to fetch is in `reference/sourcing_depth.md`'s "Standard sourcing depth" section; only
go narrower if the user explicitly asks for something lighter in that request.

**Dedupe before fetching any PDF.** The delta window's overlap buffer means a refresh
sweep re-returns rows that were already processed on the previous run — that is the
buffer working as designed, not a bug. Check each returned row against what is already
in `~/.report-generator/sources/<company_slug>/` and fetch only the genuinely new or
amended ones. The window keeps the *API query* narrow; this dedupe keeps the *PDF
fetches* narrow.

## Step 1b — Fetch and extract

**Get the source documents.** Read `reference/data_sources.md` for exactly which
tool to use for which source (BSE, screener.in, industry/peer sources, technicals
provider). In short:

- **BSE, always** — concall transcripts, annual reports, financial statements/
  quarterly results, press releases, and order wins. Discover with
  `scripts/pipeline/bse_announcements.py` (using 1a's window), fetch the returned
  `AnnPdfOpen.aspx` PDF with `WebFetch`. Company IR pages and screener.in's Documents
  tab are fallbacks for when that path fails, not alternatives to it.
- **BSE + `WebSearch`** — rating reports: the BSE disclosure for the action and its
  date, the rating agency's own site (searched across all six agencies) for the full
  rationale.
- **`WebSearch`** — brokerage/agency research, and all industry/macro context.
- **`WebSearch`/`mcp__workspace__web_fetch`** — screener.in for structured financials
  and everything else; escalate to Claude in Chrome only if a page is JS-rendered and
  web_fetch returns an empty shell.

Never write a raw `curl`/`requests` fetch script — this sandbox's network is
allowlisted and direct calls to arbitrary domains fail with a proxy 403. The only
exceptions are `bse_announcements.py`/`bulk_block_deals.py` against
`api.bseindia.com`, which already exist; don't write new ones. If the user has
uploaded documents, use those instead of fetching. Save whatever raw text/PDF you
obtain to `~/.report-generator/sources/<company_slug>/` before processing it.

**Before extracting any PDF fetched from a search result (not the company's own IR
page or a direct exchange filing link), verify it's actually the right company's
document.** Pass `--expect-name "<company name substring>"` to `pdf_to_text.py` /
`pdf_to_text_parallel.py` — see either script's own docstring for why this check
exists and exactly how it works.

**Extract text from PDFs — always extract the whole document, never just a guessed
section range.** `python3 scripts/pipeline/pdf_to_text.py <input.pdf> <output.txt>` —
local, no network. An annual report's sections you need are scattered across the
*entire* document (MD&A near the front, but segment/PP&E/litigation/shareholding notes
and the contingent-liabilities note often sit 100+ pages further back) — extracting
only a guessed page range risks silently missing something the report needs later, and
there's no cheap way to notice the gap after the fact. Full extraction, then grepping
the resulting `.txt`, is the safe default; grep on an already-extracted text file costs
milliseconds regardless of document length, so narrowing what gets *read* is not where
the token/time savings should come from.

For a **large annual report (roughly 150+ pages)**, use
`scripts/pipeline/pdf_to_text_parallel.py` instead of `pdf_to_text.py` — see
`reference/data_sources.md`'s "BSE filings — fetch, extract, log" section for when and
why (performance numbers, chunk-safety guarantee).

`pdf_to_text.py`'s `--pages START-END` flag is for scouting only, never a substitute
for full-document extraction — see `reference/data_sources.md`'s "BSE filings — fetch,
extract, log" section for exactly when it's safe to use.

**Pre-filter to candidate quotes.** `python3 scripts/pipeline/extract_theme_quotes.py
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
(no per-quarter label, no `candidate_quotes/` subfolder) also in
`research_cache/<company_slug>/` per `step3_memorize.md`'s "Save and cache" section —
that one is the *curated* set of quotes that actually made it into the drafted report,
mapped back to their source for the Sources section. The `_candidate_` infix and the
`candidate_quotes/` subfolder are both what keep the two from being mistaken for each
other.
