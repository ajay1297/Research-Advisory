# Step 0 — Perceive (Freshness Check)

This is the first of four step files (`step0_perceive.md` → `step1_retrieve.md`
→ `step2_synthesize.md` → `step3_memorize.md`), each owned by exactly one
pipeline step — see `SKILL.md`'s "Pipeline at a glance" for how they chain together.
Standing rules that apply *across* every step (token discipline,
never-drop-anything-silently, accuracy discipline) live in
`reference/rules_and_validation.md`, not here — this file is sequencing only.

## Step 0 — Check freshness before doing anything else

This is the step that makes regeneration cheap. Never re-run the full pipeline on a
report you've already generated for this company.

1. Run the results/transcript sweeps from `reference/data_sources.md`'s "standard BSE
   sweep set" — dates only at this stage, not the documents themselves. This is the
   cheapest possible lookup for these dates: one `bse_announcements.py` call returns
   every filing's date without fetching a single PDF. (screener.in's Documents/Concalls
   tab works as a cross-check if the sweep looks incomplete.)
   Collect the latest quarter's **full date** (e.g. `2026-04-29`, not "May 2026" or
   "Q4 FY26" — see `check_freshness.py`'s own docstring for why a full date is
   required) plus **every concall date shown** on the page (not just the latest).
   If the company doesn't hold a concall at all, use the results filing date instead
   — see `reference/sourcing_depth.md`'s "If the company doesn't hold concalls"
   section. Pass the latest date as `--latest-seen` and the full list as
   `--concall-dates "2026-05-01,2026-02-01,..."` to `check_freshness.py` in the next
   step.
2. If the user's request explicitly asked for a from-scratch rebuild (see
   `SKILL.md`'s "Interpreting the slash-command argument" section), skip straight to running
   `python3 scripts/check_freshness.py <company_slug> --force` — this returns
   `force_full` regardless of the date, and every source gets refetched/rebuilt as
   described there. Otherwise run
   `python3 scripts/check_freshness.py <company_slug> --latest-seen "<YYYY-MM-DD>"
   --concall-dates "<comma-separated dates from step 1>"`. Read the `cadence` field
   in the result before proceeding — if `recommended_sourcing_mode` comes back
   anything other than `standard`, follow its `note` (reduced-depth/no-concall
   fallback) rather than defaulting to the standard 6-quarter assumption below.
   What each returned state means is documented in `check_freshness.py`'s own
   docstring — read that for the definitions; here's what to actually *do* for each,
   beyond what the docstring already says:
   - `no_state` → run the full pipeline (`reference/step1_retrieve.md` onward).
   - `force_full` → refetch every source document and rebuild every section per the
     docstring; nothing extra to add here.
   - `up_to_date` → reuse `~/.report-generator/research_cache/<company_slug>/report.md`
     as-is. If the user only supplied a new price for the valuation section, recompute
     the forward PE inline (formula and labeling rules in
     `reference/report_sections.md`'s "Valuation — Forward PE" section) using the
     cached revenue-guidance/margin/shares inputs stored in
     `~/.report-generator/research_cache/<company_slug>/bullets.json` — carry the
     cached margin's guided-vs-assumed label forward unchanged, and do not refetch or
     reprocess anything else.
   - `new_quarter` → only fetch and parse the new concall/results (see
     `reference/step1_retrieve.md`); do NOT reprocess transcripts already sitting in
     `~/.report-generator/sources/<company_slug>/`. Update the Near/Medium/Long Term
     bullets from the new quarter (they supersede the old ones), but only *append*
     one new entry to `guidance_history.json` via `scripts/guidance_tracker.py`
     rather than rebuilding the guidance-reliability history from scratch — the exact
     fetch checklist for this case is `reference/sourcing_depth.md`'s "Regenerating
     for a new quarter" section.
   - **Standard sourcing depth is the last 2 annual reports and last 6 quarters of
     concalls plus each quarter's official results press release** — the default for
     every `research <company>` / first-time run. Full rationale and exactly what to
     fetch is in `reference/sourcing_depth.md`'s "Standard sourcing depth" section;
     only go narrower if the user explicitly asks for something lighter/faster in
     that specific request.
3. After finishing a run (full or incremental), call
   `python3 scripts/check_freshness.py <company_slug> --mark-processed "<YYYY-MM-DD>"
   --price <price>` — same full-date requirement as step 1, since this is exactly
   what a future run's `--latest-seen` gets string-compared against.
