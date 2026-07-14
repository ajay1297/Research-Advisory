# Deterministic Guardrails — the enforcement layer

Everything else in this skill states rules; this file is what actually checks them.
`scripts/verify_report.py` (see its own docstring for exact usage) implements every
check named below, tested against real report runs, not written and left unverified.

**The standing rule for all of it: any FAIL is a stop-and-fix, not a note-and-continue**
— a deterministic check with no consequence for failing isn't actually a guardrail,
it's decoration. WARN-level results (sourcing-depth shortfalls, a ReportLab fallback)
don't block delivery but must be stated explicitly to the user per SKILL.md's "Never
drop anything silently" rule — the distinction between FAIL and WARN is "must be fixed
before delivery" vs. "must be disclosed at delivery," never "can be ignored."

Three tiers, matching where in the pipeline each one runs.

## 1. Input Guardrails — run before real processing starts

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

## 2. Execution Guardrails — run during / immediately after a run

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
  domains (see "Important sandbox constraint" in `source_playbook.md`); all fetching
  goes through the platform's own web tools. This is enforced by the sandbox itself
  (a real call will 403), not by this script — it's an execution boundary that
  doesn't need a separate deterministic check because the environment already
  refuses it.
- **One-retry-per-stuck-source limit** — bounds runaway retry loops against a source
  that isn't going to resolve (SKILL.md's Token discipline section) — a judgment-call
  boundary, not separately scriptable, but stated here as an execution guardrail
  alongside the two that are.

## 3. Output Guardrails — run right before delivery, in this order

Nothing reaches the user without passing these — this is where "Never drop anything
silently" gets mechanically enforced rather than left to memory.

1. **`html <report.html>`** — **before deleting `report.html`, before rendering the
   PDF.** Checks for the CSS classes only `html_helpers.py`'s functions emit
   (`card-grid`, `flow-diagram`/`flow-box`, `data`, `timeline`, `flags`,
   `verdict-box`, `cover`). A FAIL here means the HTML was hand-written instead of
   built through the helper functions — a report built this way will still render
   through WeasyPrint without error (the render step has no way to know the content
   is unstyled), which is exactly why "the PDF exists and WeasyPrint didn't error"
   is not sufficient verification on its own. Stop, rebuild it through the correct
   function calls (`cover()`, `card_grid()`, `flow_diagram()`, `data_table()`,
   `timeline()`, `flag_list()`, `verdict_box()`), and re-run this check before
   proceeding to render.
2. **`pdf <output_dir>/<name>_report.pdf`** — after rendering. Confirms the PDF's
   actual `Producer` metadata (don't assume WeasyPrint from memory of what command
   you ran — check the file) and page-count sanity. A WARN for ReportLab means you
   must state that explicitly in your chat response to the user, not silently
   proceed. A FAIL (missing/corrupt PDF, too few pages) means the render didn't
   actually work regardless of what the render command's own exit code said.
3. **`report <output_dir>/<name>_report.md --brokers <TAG1,TAG2,...>`** — pass every
   broker tag for any broker/agency report supplied this run (e.g.
   `NUVAMA_29042026,CLSA_24052026`). Confirms every canonical section is present AND,
   critically, that every broker's tag actually appears in the drafted text at least
   once — catching the case where a broker PDF was read and summarized to yourself
   but its facts never actually made it into the report.
4. **`sources <company_slug>`** — confirms the `sources/`/`research_cache/` split
   (see Directory structure in README.md) wasn't violated: no bulky
   `.pdf`/`.txt`/`.bm25.pkl` leaked into `research_cache/`, no candidate-quotes JSON
   left loose in `sources/` instead of `research_cache/<slug>/candidate_quotes/`.
5. **`freshness <company_slug>`** — confirms `check_freshness.py --mark-processed`
   was actually called at the end of this run (checks `state.json`'s
   `last_processed_at` is today), not just intended.
6. **`extraction <source.pdf> <extracted.txt>`** — run this for every annual report
   extracted this run, **before** deleting/losing the source PDF. Confirms the
   extraction actually starts at page 1 and reaches the document's real final page —
   catches a scouting/partial-range extraction being mistaken for the full-document
   extraction SKILL.md's "always extract the whole document" rule requires. This
   only works if the source PDF is still on disk, so always save a fetched annual
   report PDF to `sources/<company_slug>/` before extracting it — don't
   extract-then-discard.
7. **`depth <company_slug>`** — counts concall/annual-report/investor-presentation
   `.txt` files actually present in `sources/<company_slug>/` against the standard
   depth (6 quarters, 2 annual reports, 6 investor presentations). A WARN here isn't
   automatically a blocker — a newly-listed company can genuinely lack 6 quarters of
   history — but the shortfall must then be stated explicitly in the report per
   "Never drop anything silently," not silently delivered as if standard depth was
   met. Annual reports are grouped by document identity (stripping page-range chunk
   suffixes) rather than counted per file, so 6 chunks of one document correctly
   count as 1 report, not 6. **Survives `sources/` being deleted**: falls back to
   `research_cache/<slug>/source_manifest.json` — a small, durable log of every
   document ever fetched/extracted, logged via `scripts/source_manifest.py
   add-document` right after each fetch (see `source_playbook.md`'s "Concall
   transcripts" and "Annual reports" sections). If both `sources/` and the manifest
   have counts, it takes the max of the two. Confirmed in practice that a missing
   investor presentation isn't just a thinner report, it can be factually wrong
   (Segment-wise Performance, TAM, and Manufacturing Locations lean heavily on it) —
   this is why investor presentations count toward depth too, not just concalls and
   annual reports.

Plus these, not part of the sequential build-then-verify flow above but still
mandatory before delivery:

- **`quotes <report.md> <sources_dir>`** — every double-quoted string in the Near/
  Medium/Long Term outlook sections is an exact (whitespace-normalized) substring of
  at least one source `.txt` — mechanically enforces `report_format.md`'s "every
  quote is verbatim" rule instead of relying on review alone to catch a fabricated
  or subtly-altered quote.
- **`disclaimer <report.md>`** — the required "not investment advice" language is
  present.
- **`whitespace <pdf> [--ratio 0.5]`** — every interior page (not the cover, not the
  final page) must have a word count at or above the given fraction of the
  interior-page median; the last page gets a lower but still-nonzero floor (a
  near-blank final page from a one-line overflow is dead space too). **Only the
  cover page is allowed to be sparse/mostly blank.** Catches dead whitespace from a
  forced page break or any other layout mistake — a `page_break()` call landing
  mid-document produces exactly this signature (one page at ~30% of the surrounding
  pages' density), which is why `page_break()` is banned outright in
  `reference/report_assembly.md`.
- **`ratings <company_slug> [--months 6]`** — checks `rating_history.json`'s most
  recent logged entry is within the last 6 months. This is a **recency-of-check**
  guardrail, not a lookback limit on what gets *shown* (the Promoter/Governance
  section still shows the full rating history, unchanged) — an old cached entry
  isn't evidence nothing happened since; every run should actively re-check each
  covering agency's site for the last 6 months, not just trust a stale cache.
  Always informational (WARN, never FAILs the run) since an old entry could
  legitimately mean nothing changed, not that the check was skipped.
- **`announcements <company_slug> [--months 6]`** and **`social <company_slug>
  [--report-path report.md] [--months 3]`** — same recency-of-check pattern as
  `ratings`, for the BSE/NSE announcements sweep and the LinkedIn/X sweep
  respectively (see `source_playbook.md`'s "Announcements sweep" and "LinkedIn / X
  (Twitter)" sections); `social` uses a tighter 3-month window since social posts are
  a discovery channel, not a formal disclosure record. **Unlike `ratings`, these two
  are not purely informational**: log the sweep every run via `source_manifest.py
  <slug> add-document --type announcement_sweep` (or `social_media_check`)
  `--status performed --evidence "<what was actually searched and found, or
  'nothing new'>"` — `source_manifest.py` itself rejects a `performed` entry with
  placeholder evidence (`"done"`, `"checked"`, etc.) at write time, and
  `verify_report.py announcements`/`social` **FAILs** (not WARNs) if the most recent
  entry is a disclosed `--status skipped --reason "..."` or has no evidence at all.
  A disclosed skip must never look the same as a done sweep to this check — if the
  sweep genuinely can't be done this run, log it as skipped and accept the resulting
  FAIL rather than working around it.
- **`paragraphs <report.md> [--max-words 160]`** — flags any paragraph exceeding
  ~10 rendered lines (approximated as 160 words) anywhere in the report, by section.
  Per `report_format.md`'s "Paragraph length limit" rule, a paragraph this long
  should become bullet points instead. **One exception**: a flagged Verdict
  paragraph gets "trim it" advice, not "convert to bullets" advice — the Verdict
  section stays a short paragraph by its own spec.

## Also do a visual spot-check (not scripted)

`pdftoppm -jpeg -r 120 <name>_report.pdf page` and `Read()` the cover, Company
Summary, Value Chain Positioning, and one table-heavy page. The script catches
missing structural elements, not visual bugs like overflowing tables, unreadable
font sizes, or dead whitespace (a common cause: a chart PNG saved without tight
bounding-box cropping — see `scripts/charts.py`'s `bbox_inches='tight'` usage — or a
chart wrongly wrapped in `chart_row()`). If regenerating/fixing an existing company,
comparing side-by-side against another company's already-correct PDF from earlier in
the same session is a fast way to catch anything the script and a solo skim would
both miss.

Delete any intermediate chart PNGs and `report.html` only after these checks pass;
only the final PDF and `report.md` belong in `~/.report-generator/output/<company_slug>/`.
