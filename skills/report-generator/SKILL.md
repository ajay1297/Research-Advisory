---
name: report-generator
description: Generates the visual investment-thesis PDF report pipeline for an Indian
  listed company (concall transcript, investor presentation, annual report,
  screener.in data). Invoke explicitly via /research-advisory:report-generator or /report-generator — not
  intended to auto-trigger from plain-language mentions of a company.
---

# Report Generator

This pipeline generates one company's report at a time — skip straight to Step 0.

Produces a **visual PDF** (metric cards, a color-coded timeline, and dense data
tables — tables are the default for anything with real numbers; charts are opt-in, not
automatic, see `reference/report_assembly.md`) via WeasyPrint,
alongside the markdown source of truth. **The full, authoritative section order and
per-section formatting rules live in three reference files: `reference/report_format.md`
(cover, Company Summary, Value Chain Positioning, Situation Classification, universal
rules), `reference/report_sections.md` (the eighteen sections after the outlook), and
`reference/report_assembly.md` (PDF build mechanics) — these are the single source of
truth for report structure, not this file.** See `examples/Sterlite_Technologies_report.md` for
the outlook-section style.

**Where the rest of the pipeline lives — this file is the entry point and map, not
the full spec.** Each pipeline step has its own file, and each file is read from
exactly one step — no jumping between files mid-step:
- `reference/step0_perceive.md` — check what changed since the last run, decide how
  much of the pipeline needs to run. Also pulls in `reference/sourcing_depth.md`
  (document-set/depth/cadence policy — how many quarters back, what's standard).
- `reference/step1_retrieve.md` — fetch and extract the source documents Step 0
  said are needed. Pulls in `reference/data_sources.md` (fetch mechanics, by source).
- `reference/step2_synthesize.md` — draft all 18 report sections. Pulls in
  `reference/report_format.md`, `reference/report_sections.md` (format specs) and
  `reference/source_playbook.md` (per-topic sourcing).
- `reference/step3_memorize.md` — build the PDF, run the full verify
  checklist. Pulls in `reference/report_assembly.md` (PDF build mechanics) and
  `reference/guardrails.md` (the checklist itself).
- `reference/rules_and_validation.md` — standing constraints that apply throughout a
  run (never load raw documents into context, token discipline, accuracy discipline,
  never drop anything silently) plus a pointer to `reference/guardrails.md`'s scripted
  enforcement layer. Read this once per session, not once per step.

## Pipeline at a glance

**Read this section first if the rest of the file feels like a wall of rules —
this is the actual flow, each of the four `step*.md` files above is detail on one
of these steps.**

```
0. CHECK FRESHNESS  →  1. FETCH + EXTRACT SOURCES  →  2. DRAFT SECTIONS  →  3. SAVE + VERIFY
   check_freshness.py    (data_sources.md, pdf_to_text.py)   report_sections.md      verify_report.py
   decides HOW MUCH               |                          + tracker scripts    → .md + .pdf both
   of steps 1-2 to do        sources/<slug>/                 → research_cache/     → output/<slug>/
        |                                                        <slug>/                  |
        `------------------------------ mark-processed ---------------------------------------'
                     (feeds step 0 on the NEXT regeneration — this is the loop)
```

- **Step 0** (`reference/step0_perceive.md`) is the only step that's ever
  mandatory to run in full — everything after it can be skipped, narrowed, or reused
  from cache depending on what Step 0 finds (`no_state` / `up_to_date` /
  `new_quarter` / `force_full`).
- **Step 1** (`reference/step1_retrieve.md`) is "get the raw
  documents, then turn each fetched PDF into grep-able `.txt`" — fetching and
  extracting happen back-to-back per document, in one file since they're one step.
  Which tool fetches which document type from which source is a full matrix in
  `reference/data_sources.md`'s "What gets fetched from where" section; read that
  once before your first fetch of a run.
- **Step 2** (`reference/step2_synthesize.md`) is drafting
  each of the report's 18 sections from what Step 1 gathered, using
  `reference/report_sections.md`'s per-section spec and logging anything trackable
  (a guidance item, a rating action, a fund raise, a litigation matter) into its
  tracker script as you go.
- **Step 3** (`reference/step3_memorize.md`) builds the PDF, runs
  the full `verify_report.py` checklist, and only then is the run actually done —
  followed by marking freshness processed, which is what makes Step 0 cheap on the
  *next* run.

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
company name also triggers this skill — see `reference/data_sources.md`'s "What gets
fetched from where" section for how uploads and active broker-research search change
the sourcing picture.

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
`reference/report_assembly.md`, `reference/source_playbook.md`, `reference/data_sources.md`,
`reference/sourcing_depth.md`, `reference/step0_perceive.md`,
`reference/step1_retrieve.md`, `reference/step2_synthesize.md`,
`reference/step3_memorize.md`, or `reference/rules_and_validation.md` in full
until you actually need them (i.e. read each step file only when you're on that
step). Read `examples/Sterlite_Technologies_report.md` once, when drafting.
