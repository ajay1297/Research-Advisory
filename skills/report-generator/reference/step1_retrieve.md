# Step 1 — Retrieve (Fetch and Extract Sources)

Second of four step files — see `reference/step0_perceive.md`'s header for how the
four chain together. This step only runs the parts Step 0's `check_freshness.py`
result says are needed.

## Source pipeline (only run the parts Step 0 says are needed)

**Get the source documents.** Read `reference/data_sources.md` for exactly which
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
`pdf_to_text_parallel.py` — see either script's own docstring for why this check
exists and exactly how it works.

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

For a **large annual report (roughly 150+ pages)**, use `pdf_to_text_parallel.py`
instead of `pdf_to_text.py` — see `reference/data_sources.md`'s "PDF fetch-extract-log
pattern" section for when and why (performance numbers, chunk-safety guarantee).

`pdf_to_text.py`'s `--pages START-END` flag is for scouting only, never a substitute
for full-document extraction — see `reference/data_sources.md`'s "PDF fetch-extract-log
pattern" section for exactly when it's safe to use.

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
per `reference/step3_memorize.md`'s "Save and cache" section — that one is the *curated* set of quotes that actually
made it into the drafted report, mapped back to their source for the Sources section.
The `_candidate_` infix and the `candidate_quotes/` subfolder are both what keep the
two from being mistaken for each other.
