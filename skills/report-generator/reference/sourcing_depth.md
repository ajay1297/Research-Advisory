# Sourcing Depth — document-set and cadence policy for Step 1

**Read only by `pipeline/step1_retrieve.md`.** This is document-set/depth/cadence
policy — how many quarters back, what counts as standard depth, what changes on a
refresh vs. a from-scratch rebuild, how a no-concall company changes the plan. It
answers "what should get fetched," not "how to fetch it"
(`reference/data_sources.md`) or "what to pull for report topic X"
(`reference/source_playbook.md`).

## Standard sourcing depth — last 2 annual reports, last 6 quarters of everything else

**The default for every `research <company>` / first-time (`no_state`) run, not a
special request the user has to ask for.** The question this depth exists to answer:
**can this promoter actually be trusted — does management walk the talk, and what has
genuinely changed about the business over time?** That needs more history than a
single quarter's tone can show.

The seven BSE sweeps in `reference/data_sources.md` take `--from`/`--to` directly, so
this depth is expressed as two date ranges and enforced server-side — set annual
reports to cover the last 2 fiscal years and everything else to ~18 months:

- **Annual reports: the last 2 fiscal years**, not just the latest. Two consecutive
  years lets you read the Chairman's letter/MD&A narrative *change* year over year —
  did the stated strategy shift, did a previously-flagged risk get addressed, does
  this year's framing contradict last year's — which one year can't show on its own.
- **Concall transcripts: the last 6 quarters.** Specifically to give
  `guidance_history.json` enough successive data points to show a real track record
  rather than 1-2 isolated entries — a promoter who guided X in quarter 1, revised to
  Y in quarter 3, and delivered Z in quarter 6 tells you something 2 quarters can't.
  Log each quarter's items via `guidance_tracker.py add-guidance`, using
  `--supersedes-id` wherever a later quarter revises an earlier one.
  **Many companies file fewer than 6** — some hold calls half-yearly, some never (see
  below). The sweep returning 2 transcripts over 18 months is a finding about the
  company, not a shortfall to fix.
- **Investor presentations: also the last 6 quarters — not optional or secondary.**
  Confirmed in practice: the presentation is frequently the *only* source for the
  segment-wise revenue split, the geographic/exports split, and the disclosed TAM — a
  report built from the transcript and screener.in alone can be genuinely wrong (not
  just thin) on these, having once claimed "no TAM disclosed" when the presentation
  had one all along. Presentations and transcripts are normally filed within a day or
  two of each other, so the same 18-month window catches both.
- **Press releases: the same 6-quarter depth** — see below for why.

This depth feeds the **Situation Classification** (a turnaround call needs multi-year
evidence, not one quarter's tone), **Promoter/Governance**'s guidance-reliability
read, the **Segment-wise Performance**/**TAM**/**Manufacturing Locations** sections,
and the **Investment Thesis Summary**/**Verdict**. It does not change the
Near/Medium/Long Term outlook bullets, which still reflect *current* guidance.

**Check the depth was met, don't just intend it**: `python3 scripts/pipeline/verify_report.py
depth <company_slug>` counts the concall, investor-presentation, and annual-report
`.txt` files actually sitting in `sources/<company_slug>/` and WARNs on a shortfall —
the prompt to either fetch what's missing or state the shortfall explicitly in the
report, not something to discover after delivery.

**Only go narrower** if the user explicitly asks for something lighter in that
request ("just give me a quick take"). State which fiscal years and quarters were
actually pulled either way — exactly the scope decision the "Never drop anything
silently" rule in `reference/rules_and_validation.md` expects stated.

## Press releases — why they're a standard source, not an optional extra

A results press release is the company's own primary-source document, and it
routinely states facts that third-party results-coverage garbles or drops — a
standalone-quarter swing to a loss buried inside an otherwise-profitable full year, a
dividend recommendation, an exceptional item's precise cause. This gap has already
happened in practice: a report built from secondary results-coverage alone correctly
captured a company's full-year profit but never surfaced that the final quarter alone
had swung to a net loss.

**How to use it**: prefer the press release's own figures and framing for **Financial
Performance Summary** over any secondary summary — specifically check for a
standalone-quarter breakout (not just the cumulative figure), a dividend
recommendation, and the company's own stated reason for an exceptional item or YoY
swing. If a secondary aggregator conflicts with the press release, the press release
wins; treat the aggregator as a fallback only when no release can be located, and say
so rather than silently picking whichever number was easiest to find.

**An empty press-release sweep is a real finding** — plenty of companies file only the
bare financial statements with no accompanying narrative, and some bundle the release
into the Reg. 33 results filing itself. State that explicitly rather than substituting
secondary coverage.

## If the company doesn't hold concalls

**Many smaller listed companies never hold an earnings call — common, not an error,
and the pipeline has to keep working without one.** An empty transcript sweep across
the 18-month window establishes this; one check is enough, don't retry.

- **The freshness label** (`check_freshness.py --latest-seen`) uses the latest
  **quarterly/annual results filing date** instead of a concall date — results are
  filed under Reg. 33 regardless. Still a full date (`YYYY-MM-DD`).
- **The Near/Medium/Long Term outlook's source shifts** to whatever written
  forward-looking language the company *does* disclose: the results filing itself
  (some include an MD&A-style paragraph), investor presentations if published
  independently of a call (check — "no concall" doesn't imply "no deck"), the annual
  report's MD&A (which becomes unusually load-bearing, possibly the only place
  management states a forward view), and BSE announcements (an order win or capacity
  expansion can be the closest thing to guidance available). If none yield genuine
  forward-looking language, say so explicitly rather than forcing a bullet from thin
  material — "management does not hold concalls and no forward-looking guidance was
  found in the results filing, investor materials, or recent announcements" is a
  legitimate, statable finding.
- **The guidance-reliability track record will be thinner or absent** — no verbatim
  "we guided X, delivered Y" chain to reconstruct. Say this plainly rather than
  presenting an empty guidance table as a clean track record; a company that never
  states verifiable guidance is a different governance profile from one that guides
  and delivers.
- **State this once, in the Company Summary or Near Term section**, rather than
  leaving the reader to infer it from a thin outlook.

## Annual reports — reading discipline after extraction

Extraction mechanics are in `reference/data_sources.md`. What's specific to depth: the
"don't read the whole thing" discipline applies to what you feed
`extract_theme_quotes.py` and what you `Read()` into context, **not** to what gets
extracted. Grep the fully-extracted text for the MD&A heading and feed only *that*
slice to `extract_theme_quotes.py` (avoids running quote extraction over
financial-statement boilerplate), while the full `.txt` stays on disk for every other
section's grep/`semantic_search.py` pass.

If a section you know should exist (raw-material sourcing note, a value-chain
description, a customer mention) doesn't surface under any keyword, run
`scripts/helpers/semantic_search.py <extracted.txt> "<what you're looking for, in plain
language>"` before giving up on grep — annual reports vary enough in phrasing that a
keyword that worked for one company's report often doesn't for another's.

## Windowing — what filters server-side and what doesn't

**BSE (the seven sweeps): server-side.** `--from`/`--to` are real API parameters, so
the window is enforced at fetch time and nothing outside it is ever returned. This is
the bulk of the pipeline's sourcing.

**Everything else: filter after the fetch.**

- **screener.in** — one `web_fetch` always returns the entire page: full multi-year
  quarterly table, full P&L/balance-sheet history, shareholding back to 2015-17. No
  URL parameter returns less. Read only the last ~6 columns of the quarterly table and
  the recent shareholding columns, and don't carry older columns forward into
  `research_cache/` — leave them in the one-time fetch. (The Financial Performance
  Summary is the deliberate exception: it's explicitly a multi-year trend and exempt
  from the 18-month default.)
- **`WebSearch`** — no date-range parameter. Phrase the query with the specific
  month/quarter you want, then **check the actual publish date** on the result or
  fetched page before using it, and discard anything you can't confirm falls inside
  the window. This matters most for broker calls and industry/macro material, where a
  stale result looks identical to a current one.

## Regenerating for a new quarter — what to actually (re)fetch

The single biggest token-saving lever in the pipeline, and easy to under-use by "just
re-running everything to be safe." When `check_freshness.py` returns `new_quarter`,
re-run the BSE sweeps with `--from` set to just after the last run's date rather than
the full 18 months, and fetch **only**:

- The new quarter's **concall transcript**, **investor presentation**, and **results
  press release** — the three documents that actually changed.
- **screener.in's last 1-2 columns** of the quarterly/annual table and the most recent
  shareholding column — not the full history.
- Any **new** announcement, rating action, or litigation development since the last
  run — check dates against `guidance_history.json`/`fundraise_history.json`/
  `rating_history.json`/`litigation_history.json` and log only what's actually new.

Earlier quarters already in `sources/<company_slug>/` are reused untouched, so the
rolling 6-quarter window maintains itself cheaply rather than being rebuilt each time.

**Do not re-fetch or re-derive** anything that doesn't change quarter to quarter and
is already in `research_cache/<company_slug>/report.md`: manufacturing locations,
certifications, TAM, entry barriers, product criticality, peer identities, the value
chain description, or already-processed annual reports. Carry these forward unmodified
unless the new concall/presentation mentions a change.

**What does need a fresh look every quarter**: the Near/Medium/Long Term outlook,
Financial Performance Summary (append the new row, don't rebuild the table), Order
Book, Capacity Utilization, the Capex/Milestones timeline (append only), Valuation,
Technical Snapshot (always stale, always refresh), and the Promoter/Governance
sub-sections — and even those get a new *entry* appended only if something actually
happened.

## User-uploaded documents

See `reference/data_sources.md`'s "User-uploaded documents" section — always prefer an
upload over fetching for that document type.
