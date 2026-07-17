# Sourcing Depth — document-set and cadence policy for Step 0

**Read only by `reference/step0_perceive.md`.** This is document-set/depth/cadence
policy — how many quarters back, what counts as standard depth, what changes on a
refresh vs. a from-scratch rebuild, how an unusual concall cadence or a no-concall
company changes the plan. It answers "what should get fetched," not "how to fetch
it" (`reference/data_sources.md`) or "what to pull for report topic X"
(`reference/source_playbook.md`).

## Concalls, investor presentations, annual reports, press releases

Fetch/extract/log mechanics in `reference/data_sources.md`. Annual-report-specific
processing beyond the generic fetch pattern:

## Press releases — a fourth standard source, fetched for the same 6-quarter depth

**Fetch the company's own official results press release for each of the last 6
quarters, alongside the concall/investor-presentation/annual-report set** — this is
now part of the standard sourcing depth, not an optional extra. The reason this
exists: a results press release is the company's own primary-source document, and it
routinely states facts that third-party results-coverage aggregators (EquityBulls,
ScanX, business-news sites) summarize incompletely or garble — a standalone-quarter
swing to a loss buried inside an otherwise-profitable full year, a dividend
recommendation, an exceptional item's precise cause, are all the kind of thing a
company's own press release states plainly in its headline/first paragraph, but a
secondary aggregator's summary can drop or blend into an annual figure. This gap has
already happened in practice: a report built from secondary results-coverage alone
correctly captured a company's full-year reported profit but never surfaced that the
final quarter alone had swung to an actual net loss — a fact the company's own press
release would very likely have stated as its own line, not left for the reader to
reconstruct by subtracting two other cited numbers.

**Where to find it — primary method, BSE's own Corporate Announcements filter (use
this first, before falling back to anything else):** BSE's corp-announcements page for
any scrip (`bseindia.com/stock-share-price/<company-slug>/<symbol>/<scrip-code>/corp-announcements`
— get the exact slug/symbol/scrip-code from screener.in's BSE link on the company's
own page) has a filter form with **Category: "Company Update"** and **Sub Category:
"Press Release / Media Release"**, plus a From/To Date range. Setting these two
category filters (not a keyword search) surfaces exactly the company's own official
press releases, one row per quarter, each with a direct PDF download link and the
exact exchange-received timestamp — this is far more reliable than guessing search
terms or relying on a third-party aggregator's index of the same filings. Set the date
range to cover the last ~18 months (6 quarters) in one pass rather than querying
quarter-by-quarter. **This page is JS-rendered — `WebFetch`/`mcp__workspace__web_fetch`
returns an empty shell for it, so this specifically requires driving a real browser**
(Claude in Chrome, if connected this session) to fill the filter form and submit;
screener.in's own "Documents → Announcements → Search" panel (login-gated, but mirrors
the same BSE data) is a usable substitute if Chrome isn't available and the user (or
this session) has a screener.in account — it renders as plain HTML servable via a
Browser pane without hitting bseindia.com directly, unlike the BSE page itself. If
neither is available, ask the user to pull the filtered results directly (as
demonstrated in practice: a screenshot or the page's raw HTML naming each release's
PDF link is enough to fetch every quarter's press release in one exchange). Each
resulting PDF link resolves to `bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=<uuid>.pdf`
— confirmed to work directly with `WebFetch` (unlike the corp-announcements search
page itself), even though `WebFetch`'s own text-summarization step cannot parse a
digitally-signed PDF's binary structure — the binary is still saved to disk in that
case, so follow up with `pdf_to_text.py --expect-name "<company name>"` on the saved
file to get real, grep-able text rather than treating the summarizer's failure as a
fetch failure.

If the company genuinely doesn't issue a separate press release (some smaller
companies only file the bare financial statements with no accompanying narrative),
this same filtered search will confirm that (no rows returned for the category) — say
so explicitly per the "never drop anything silently" rule rather than silently
substituting secondary coverage without noting the gap.

**How to use it**: prefer the press release's own stated figures and framing for
**Financial Performance Summary** over a secondary aggregator's summary whenever both
exist — specifically check it for a standalone-quarter breakout (not just the
cumulative/full-year figure), any dividend recommendation, and the company's own
stated reason for any exceptional item or YoY swing. If a secondary aggregator's
figure and the press release's own figure conflict, the press release is the more
authoritative source — treat a secondary aggregator only as a fallback when a press
release genuinely cannot be located, and say so explicitly rather than silently
picking whichever number was easiest to find.

## If the company doesn't hold concalls

**Many smaller listed companies never hold an earnings call at all — this is common,
not an error, and the whole pipeline needs to keep working without one.** Check
screener.in's Documents/Concalls tab: if it's empty, or only ever shows "Transcript
not available" / no entries across several quarters, treat this as confirmed rather
than retrying repeatedly — one check is enough to establish the pattern.

**What changes when there's no concall:**

- **The freshness label** (`check_freshness.py --latest-seen`) uses the latest
  **quarterly/annual results filing date** instead of a concall date — results still
  get filed under Regulation 33 (SEBI LODR) even without a call, and that's a real,
  regularly-recurring date to track freshness against. Still a full date
  (`YYYY-MM-DD`), same requirement as the concall case.
- **The Near/Medium/Long Term outlook's source shifts** — without management's own
  spoken forward-looking commentary, the outlook has to be built from whatever
  written forward-looking language the company *does* disclose:
  - The **results filing itself** — some companies include a short MD&A-style
    paragraph or press release alongside the numbers, even without a call.
  - **Investor presentations**, if published independently of a call (some companies
    that skip calls still publish a slide deck) — check for this specifically,
    don't assume "no concall" means "no investor presentation" too.
  - The **annual report's MD&A section** — this becomes a more load-bearing source
    than usual, since it may be the *only* place management states a forward view in
    their own words.
  - **BSE/NSE announcements** (see `reference/source_playbook.md`'s "Announcements
    sweep" section) — an order win,
    capacity expansion, or management commentary in an announcement can be the closest
    thing to forward guidance available.
  - If none of these yield genuine forward-looking language, the Near/Medium/Long
    Term sections should say so explicitly rather than forcing a bullet from thin
    material — "management does not hold concalls and no forward-looking guidance was
    found in the results filing, investor materials, or recent announcements" is a
    legitimate, statable finding per report_format.md's rule that a bullet needs a
    real verbatim-quotable source.
- **The guidance-reliability track record (Promoter/Governance) will be thinner or
  absent** — without a call, there's no verbatim "we guided X, delivered Y" chain to
  reconstruct via `guidance_tracker.py`. Say this plainly rather than presenting an
  empty guidance-history table as if it were a clean track record; a company that
  simply never states verifiable forward guidance is a different (and worth-noting)
  governance profile from one that guides and delivers reliably.
- **State this explicitly in the Company Summary or Near Term section, once, rather
  than leaving the reader to infer it from a thin outlook** — e.g. "STL Ltd does not
  hold quarterly earnings calls; this report's near-term outlook draws instead from
  [whichever of the above sources actually yielded something]." This is exactly the
  kind of scope fact the "Never drop anything silently" rule in
  `reference/rules_and_validation.md` expects stated, not left implicit.

## Annual reports — processing, beyond the generic fetch pattern

Larger PDF (100-300+ pages) — always run the **whole** thing through
`pdf_to_text.py`/`pdf_to_text_parallel.py`, never a guessed page range: the segment
note, litigation note, shareholding pattern, and PP&E note typically sit much
further back than the MD&A and are just as required as the outlook section.
`verify_report.py extraction` needs the source PDF still on disk to confirm
full-page coverage — save it before extracting, don't extract-then-discard.

The "don't read the whole thing" discipline applies to what you feed
`extract_theme_quotes.py` and what you `Read()` into context, not to what gets
extracted — grep the already-fully-extracted text for the MD&A section heading and
only feed *that* slice to `extract_theme_quotes.py` (avoids burning tokens running
quote-candidate extraction over financial-statement boilerplate), while the full
extracted `.txt` stays on disk for every other section's grep/`semantic_search.py`
pass. If a section you know should exist (raw material sourcing note, a value-chain/
backward-integration description, a specific customer mention) doesn't surface under
any keyword you try, run `scripts/semantic_search.py <extracted.txt> "<what you're
looking for, in plain language>"` before giving up on grep — annual reports vary a
lot in phrasing between companies and a keyword guess that worked for one company's
report often doesn't for another's.

## Standard sourcing depth — last 2 annual reports, last 6 quarters of concalls and investor presentations

**This is the default for every `research <company>` / first-time (`no_state`) run,
not a special request the user has to ask for.** The question this depth exists to
answer: **can this promoter actually be trusted — does management walk the talk, and
what has genuinely changed about the business over time?** That needs more history
than a single quarter's tone can show, so it's built into the standard pipeline
rather than gated behind trigger phrasing:

- **Annual reports: the last 2 fiscal years**, not just the latest one — e.g. if the
  current fiscal year is FY27, fetch and fully extract (`pdf_to_text.py`/
  `pdf_to_text_parallel.py`, per the "always extract the whole document" rule) the FY25
  and FY26 annual reports. Two consecutive years lets you read the Chairman's
  letter/MD&A narrative *change* year over year — did the stated strategy actually
  shift, did a previously-flagged risk get addressed, does this year's framing
  contradict or confirm last year's — which a single year's report can't show on its
  own.
- **Concall transcripts: the last 6 quarters.** This is specifically to give
  `guidance_history.json` enough successive data points to show a genuine track record
  rather than 1-2 isolated entries — a promoter who guided X in quarter 1, revised to Y
  in quarter 3, and delivered Z in quarter 6 tells you something 1-2 quarters can't.
  Extract each transcript and run `extract_theme_quotes.py` on it as usual, then log
  each quarter's guidance items via `guidance_tracker.py add-guidance` (using
  `--supersedes-id` wherever a later quarter revises an earlier one) so the evolution
  is reconstructable, not just the latest snapshot.
- **Investor presentations: also the last 6 quarters, same depth as concalls — this
  is not optional or secondary.** Confirmed in practice on a real report: the investor
  presentation is frequently the *only* source for the segment-wise revenue split, the
  geographic/exports split, and the company's own disclosed TAM figure — a report built
  from the concall transcript and screener.in alone can be genuinely wrong (not just
  thin) on these sections, having incorrectly claimed "no TAM disclosed" when the
  investor presentation had one all along. Fetch and fully extract each quarter's
  investor presentation alongside its concall — they're normally published together on
  screener.in's Documents tab, so this shouldn't require a separate search. If a
  quarter's investor presentation genuinely isn't available (some companies don't
  publish one every quarter), say so explicitly rather than silently having only the
  concall for that quarter.
- This depth feeds the **Situation Classification** (a transformation/turnaround call
  needs multi-year evidence, not one quarter's tone), the **Promoter/Governance Track
  Record** section's guidance-reliability read, the **Segment-wise Performance**/
  **Total Addressable Market**/**Manufacturing Locations** sections (which lean heavily
  on investor presentations specifically), and the **Investment Thesis Summary**/
  **Verdict** — it does not change what goes into the Near/Medium/Long Term outlook
  bullets themselves, which still reflect *current* forward guidance.
- **Check this was actually done, don't just intend it**: `scripts/verify_report.py
  depth <company_slug>` counts both concall and investor-presentation files actually
  sitting in `sources/<company_slug>/` and WARNs if either is short of 6 — the same
  mechanism that would have caught the investor-presentation gap above before delivery
  rather than after a user had to point it out.
- **On a `new_quarter` refresh, this does not mean re-fetching all 6 quarters again**
  — per the incremental-regeneration rule, only the new quarter gets fetched; earlier
  quarters already sitting in `sources/<company_slug>/` from prior runs are reused
  untouched, so the rolling 6-quarter window stays maintained cheaply over successive
  regenerations rather than being rebuilt from scratch each time.
- **Only go narrower than this** if the user explicitly asks for something
  lighter/faster in that specific request (e.g. "just give me a quick take," "don't
  need the full history"). State plainly which fiscal years and quarters were
  actually pulled either way — this is exactly the kind of scope decision the "Never
  drop anything silently" rule in `reference/rules_and_validation.md` expects to be
  stated, not left implicit.
- **Check this depth was actually met before delivering, don't just intend it**:
  `python3 scripts/verify_report.py depth <company_slug>` counts the concall/annual-
  report `.txt` files actually sitting in `sources/<company_slug>/` and flags a
  shortfall — a WARN there is the prompt to either fetch what's missing or state the
  shortfall explicitly in the report, not something to notice only if someone asks
  later why a run came up short.

## Filtering to an 18-month window — how it actually works

There's no server-side "give me the last 18 months only" parameter on either
screener.in or YouTube/WebSearch. The 18-month/6-quarter lookback (the framework's
standard sourcing depth — see `reference/step0_perceive.md` and "Standard sourcing
  depth" above) is
enforced by what gets *used and cached*, not by what gets fetched:

- **screener.in**: one `web_fetch` always returns the entire page — the full
  multi-year quarterly table, full P&L/balance sheet history, full shareholding
  history back to 2015-17, and the full concalls list back to whenever the company
  started disclosing them. There is no URL parameter or lighter endpoint that returns
  only recent data. The window filter happens after the fetch: read only the last 6
  columns of the quarterly table, the top 6 entries of the Concalls list, and the
  recent shareholding-pattern columns spanning the same window. Don't cache or carry
  forward older columns/entries beyond that window into
  `~/.report-generator/research_cache/` — leave them in the one-time fetch and discard
  them once you've pulled what you need. This means the fetch itself isn't smaller,
  but the tokens spent reasoning over the result, and what persists in the cache, are
  scoped to the standard window.
- **YouTube / WebSearch**: `WebSearch`'s schema has no date-range parameter, so you
  can't ask it for "concalls from the last 18 months" directly. Two ways to stay
  scoped: (1) prefer the quarter-linked link from screener.in as above, which is
  already dated by construction; (2) if doing a genuinely open search (e.g. industry
  commentary, not a specific concall), phrase the query with the specific
  month/quarter you want (e.g. "TD Power Systems management interview June 2026") and
  then check the actual publish date shown in the search result or on the fetched
  page before using it — discard anything you can't confirm falls inside the window.

## Regenerating for a new quarter — what to actually (re)fetch

This is the single biggest token-saving lever in the whole pipeline, and it's easy to
under-use by "just re-running everything to be safe." When `check_freshness.py` returns
`new_quarter`, fetch **only**:

- The new quarter's **concall transcript**, **investor presentation**, and **official
  results press release** (the three documents that actually changed) — the press
  release specifically for the standalone-quarter figures and any dividend/exceptional-
  item framing a secondary aggregator might drop, per "Press releases" above.
- **screener.in's last 1-2 columns** of the quarterly/annual results table and the most
  recent shareholding-pattern column — not the full history, per "Filtering to an
  18-month window" above (this incremental fetch stays narrow even though the
  standard *sourcing depth* is 6 quarters — a `new_quarter` refresh only needs
  what's new, since earlier quarters are already cached).
- Any **new** BSE/NSE announcement, rating action, or litigation development since the
  last run — check dates against what's already logged in `guidance_history.json`/
  `fundraise_history.json`/`rating_history.json`/`litigation_history.json` and only
  fetch/log what's actually new, not the full history again.

**Do not re-fetch or re-derive** anything that doesn't change quarter to quarter and is
already sitting in `~/.report-generator/research_cache/<company_slug>/report.md` from the last run:
manufacturing locations, certifications, TAM figures, entry barriers, product
criticality, peer identities (their financials may need a quick refresh if quoted, but
the peer set itself rarely changes), the value chain description, or older annual
reports already processed. Carry these sections forward from the cached `report.md`
unmodified unless the new concall/presentation specifically mentions a change (a new
certification obtained, a new plant, a new peer entering the conversation).

**What does need a fresh look every quarter**: the Near/Medium/Long Term outlook
(supersedes the old bullets, per `reference/step0_perceive.md`), Financial Performance Summary (add the new
quarter/year as a row, don't rebuild the table), Order Book, Capacity Utilization,
the Capex/Milestones timeline (append new rows only), Valuation (new price/guidance),
Technical Snapshot (always stale, always refresh), and the Promoter/Governance
sub-sections — but even those only get a new *entry* appended if something actually
happened (a new rating action, a new fund raise, a new case) rather than a full rebuild
of an unchanged history.

## User-uploaded documents

See `reference/data_sources.md`'s "User-uploaded documents" section — always prefer
an upload over fetching for that document type.
