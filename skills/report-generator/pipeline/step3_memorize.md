# Step 3 — Memorize (Save and Verify)

Third of three step files — see `pipeline/step1_retrieve.md`'s header for how the
four chain together.

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
too if `scripts/helpers/charts.py` will be used) and re-check with the same import — do not
proceed past this step on a guess. Only after that second check still fails is the
environment considered genuinely unable to run WeasyPrint.

**Primary path — visual PDF via WeasyPrint (required whenever the above check
passes).** Build the HTML body and render the PDF per `reference/report_assembly.md`
— read it now if this is your first run this session; it has the full
`html_helpers.py` function list, a worked code example, and the exact render
command. The one thing worth restating here: a report built by hand-writing plain
HTML instead of calling those functions will still render through WeasyPrint
without error (the render step has no way to know the content is unstyled), which
is exactly why "the PDF exists and WeasyPrint didn't error" is not sufficient
verification on its own — see the mandatory check below.

**Verify before delivering — run `scripts/pipeline/verify_report.py`, don't rely on your own
judgment call for this.** Full checklist (what to run, in what order, and why each
check exists) is in `reference/guardrails.md` — read it now if this is your first
run this session. Short version: `html` → render PDF → `pdf` → `report` →
`sources` → `freshness` → `extraction` → `depth`, plus `quotes`/`disclaimer`/
`filenames`/`whitespace`/`ratings`/`announcements`/`deals`/`social`/`paragraphs`/`gaps` before
delivery, and a visual spot-check via `pdftoppm`. **Any FAIL is a stop-and-fix, not
a note-and-continue.** Delete intermediate chart PNGs and `report.html` only after
all checks pass; only the final PDF and `<Company_Name>_report.md` (never the
generic `report.md`/`report.pdf` — `filenames` checks exactly this) belong in
`~/.report-generator/output/<company_slug>/`.

**Legacy fallback — reportlab, text-only. Last resort only, and always flagged.** Use
this ONLY if the verify-then-install check above genuinely failed twice (import error
persists after a fresh `pip install`) — never reach for it just because a build step
errored once; retry the WeasyPrint path before giving up on it. If truly falling
back, see `reference/report_assembly.md`'s "Legacy fallback" note for the exact
command. Never let a missing dependency block delivery entirely; fall back rather
than skip the PDF outright — but **explicitly tell the user in your chat response
(not silently) that this report used the plain-text fallback renderer and why**, so
a mismatched look across a multi-company batch is never a surprise discovered after
the fact. Confirm both `.md` and `.pdf` exist in
`~/.report-generator/output/<company_slug>/` before telling the user the report is
ready, whichever path was used.

Save/update `~/.report-generator/research_cache/<company_slug>/quotes.json`, `bullets.json`,
`guidance_history.json`, `fundraise_history.json`, `rating_history.json`,
`litigation_history.json`, and `report.md`, then mark freshness state per
`pipeline/step1_retrieve.md`'s step 5.

## What gets recorded, and when

This is the pipeline's memory model — the durable state that makes a later
regeneration cheap and lets a report cite a document that's no longer on disk. Three
kinds, recorded at different times:

**1. The source manifest — written during Step 1, not here.**
`source_manifest.py add-document` fires **immediately after each extraction**, per
`reference/data_sources.md`'s fetch-extract-log pattern, never batched at the end of
the run. The timing is the point: `sources/<company_slug>/` holds raw PDFs and
multi-MB extracted text and gets deleted to save space, but `verify_report.py
depth`/`extraction` still needs to confirm 6 quarters were fetched and that annual
reports were extracted whole. The manifest is what survives that deletion, so a
document extracted but never logged is indistinguishable from one never fetched.

The same call records **sweeps that found nothing** — `--type
broker_sweep`/`deals_sweep`/`announcements_sweep`/`social` with `--status performed
--evidence "<what was searched and found, or 'nothing attributable'>"` (or `--status
skipped --reason "..."`). `verify_report.py brokers`/`deals`/`announcements`/`social`
FAIL if a sweep was never logged or its latest entry is stale — which is how "the
check was skipped" stays distinguishable from "the check ran and came up empty," a
distinction the report itself has to state either way.

**2. The tracker histories — durable records, appended once when first seen.**
`rating_history.json`, `fundraise_history.json`, `litigation_history.json`. These are
**not** per-quarter snapshots: a rating action, a preferential allotment, or a court
case is logged the first time it's found and then left alone. This matters because the
BSE sweeps re-run over their full window on every regeneration and hand back actions
already on file — so add-calls with known items are routine, and blind appending is
what turns a history into noise.

- `rating_tracker.py add-rating` — **safe to call on every sweep result; it's
  idempotent on `(agency, date, instrument)`.** An exact repeat is skipped with a
  message and exit 0; the same agency/date/instrument with *different* terms exits
  non-zero as a conflict to re-check (a misread rationale, or a correction) rather
  than silently creating a second in-force entry. `--force` appends anyway, correct
  only when an agency genuinely took two distinct actions on one instrument in a day.
  State `--action` yourself
  (`first_time`/`reaffirmed`/`upgrade`/`downgrade`/`outlook_revised_positive`/
  `outlook_revised_negative`/`withdrawn`) based on what the rationale itself says
  relative to the prior rating, not by comparing rating-scale notches. A downgrade or
  negative/watch-negative outlook is a first-class risk signal: run `rating_tracker.py
  <slug> report` and reproduce its flag **verbatim** in Promoter/Governance and, if
  material, Key Risks — don't soften it to a passing mention.
- `fundraise_tracker.py add-raise` — idempotent on `(date, instrument, allottee)`; an
  exact repeat is skipped and **the existing status is preserved**, so re-logging can't
  reset a warrant you already marked `lapsed` back to `pending`. Still run
  `update-status` on each regeneration for any `pending` warrant that has since
  converted or lapsed (SEBI ICDR gives 18 months).
- `litigation_tracker.py add-case` — idempotent on `(case_ref, forum)`, matched
  case- and whitespace-insensitively since both are free text re-typed from each
  year's annual report. A **restated amount** is the expected annual change (interest
  and penalty accrue), so that case is refused with a ready-to-run `update-status
  --amount-cr` command: revise the figure in place, never log the case twice. Use
  `--status dismissed_appealable` rather than `closed_final` whenever an appeal window
  or pending higher-forum appeal exists; `report` flags that status so it isn't lost.

All three guards exist for the same reason: `report` **sums** amounts (promoter/debt
totals, total disclosed contingent liability) and picks a single in-force entry per
key. A duplicate doesn't just clutter the history — it silently overstates capital
raised or legal exposure in the report itself.

**3. Guidance — the one genuinely per-quarter history.**
`guidance_tracker.py add-guidance`, one entry per guided item per quarter, with
`--supersedes-id` pointing at the entry it revises. Unlike the trackers above, the
*repetition* is the signal: the chain of successive entries is what shows whether
management walks the talk, so an item reaffirmed across four quarters gets four
entries, not one.
