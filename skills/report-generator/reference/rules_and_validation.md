# Rules and Validation — standing constraints that apply across every step

These aren't sequencing — they're discipline that holds throughout every step —
`reference/step0_perceive.md` → `step1_retrieve.md` → `step2_synthesize.md`
→ `step3_memorize.md` — not something to apply only at one point in the run. The scripted enforcement
layer for all of this is `scripts/verify_report.py`; see `reference/guardrails.md`
for the full tier-by-tier reference (what each check does, FAIL vs. WARN) — this
file is the *why*, that file is the *how it's checked*.

## The core rule: never load raw source documents into context

Concall transcripts run 15-40 pages, investor decks 20-50 slides, annual reports
100-300 pages. Every pipeline step exists to avoid reading these
directly. Always go through `scripts/`, never paste a full transcript/PDF into your
own reasoning.

## The other core rule: never drop anything silently

Everything in this pipeline is optimized for token/time efficiency — grepping instead
of reading, caching instead of refetching, skipping what a freshness check says is
unchanged. None of that is license to let a fetch failure, timeout, rate limit,
extraction gap, or skipped section pass without comment. If something couldn't be
gotten, couldn't be verified, or was cut short for any reason, **that gets stated in
the report, in the section it affects** — see the full "Never drop anything silently"
section below for the exact rule and examples. Keep it in mind at every step, not
just when assembling the final report.

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
- **On a `new_quarter` refresh, fetch only what changed** — the single biggest token
  lever in the pipeline; see `reference/step0_perceive.md`'s `new_quarter` case
  for the exact checklist of what to fetch vs. what carries forward unchanged.
- **Don't burn more than one retry on a stuck source.** If screener.in's numeric
  widgets won't populate after one wait/retry, stop retrying it and fall back per
  `reference/data_sources.md`'s "BSE / NSE filings" section (exchange filing
  directly, the concall/investor presentation you're already fetching, or a secondary
  quote aggregator for just the price) — debugging a stuck fetch costs more than
  switching sources.

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

This is a standing rule that overrides convenience everywhere else in this pipeline: if
a source can't be fetched, a fetch times out, a page/quarter/section is skipped for any
reason, a rate limit or size limit is hit, a script errors, an extraction comes back
garbled or empty, a tracker flag can't be verified, or a section is left out — **that
gap gets stated in the report, in the section it affects, every time.** Silently
producing a report that reads as complete when a piece of it wasn't actually gathered
is a worse failure than the gap itself, because the reader has no way to tell a
verified "nothing here" from an unverified "I didn't check."

**This rule has a second half that matters just as much: don't just intend to catch
gaps, mechanically check for the specific ones this pipeline has actually hit.**
`scripts/verify_report.py` (see `reference/guardrails.md`) exists because several of
the gaps below have already slipped through on judgment/memory alone in practice — a
hand-written HTML report that still rendered fine through WeasyPrint, an annual report
extraction that silently started at page 40 instead of page 1, a broker PDF whose
facts were read but never actually made it into the drafted text. Wherever a check
below has a scriptable, grep-able signature, run the script; reserve judgment calls
for the gaps that genuinely can't be mechanically checked (e.g. whether a "Colt-style"
customer-listing explanation is specific enough — see the Marquee & Niche Customers
section of `reference/source_playbook.md`).

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
  capped by `max_chars`; an aggregator (Trendlyne/Tijori/etc.) that returned a thin or
  paywalled preview instead of full data. Note the limitation next to whatever partial
  data *was* usable, rather than presenting the partial data as complete.
- **Sections that come back empty** — a tracker report with no entries, a
  `semantic_search.py`/grep pass that found nothing for a section you expected to
  exist. Distinguish explicitly between "checked, genuinely not disclosed" (a
  legitimate, useful finding — see `reference/report_sections.md`'s per-section rules
  for when a section is expected to state absence rather than being omitted) and
  "couldn't verify" (a gap, which must say so) — never let the second read like the
  first.
- **Renderer/dependency fallbacks** — e.g. the legacy ReportLab PDF fallback used in
  place of WeasyPrint (see `reference/step3_memorize.md`'s "Save and cache"
  section) — must be
  flagged in your chat response to the user, not just left for them to notice from how
  the PDF looks.
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
distinction are all in `reference/guardrails.md`. `reference/step3_memorize.md`'s
"Verify before
delivering" checklist (Save and cache) is the operational sequence; that file is the
full reference when you need to know *why* a specific check exists or what a WARN vs
FAIL means for one of them.
