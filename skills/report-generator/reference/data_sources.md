# Data Sources — where and how everything gets fetched (or uploaded)

This is the **mechanics** reference: which tool to use for which source, URL
patterns, fallback chains, and how a user-uploaded document changes the picture.
`source_playbook.md`'s per-topic sections tell you *what* to pull for each part of
the report and point back here for *how* to actually get it — read this once per
report, not once per topic.

## What gets fetched from where

This is the concrete answer to "which source do I use for which document type" —
every cell below has a corresponding how-to in `source_playbook.md` (matching
section headings):

| Data type | Primary source(s) | Also check |
|---|---|---|
| **Concall transcripts** | Company's own IR page; BSE/NSE (`AnnPdfOpen.aspx`-style direct links) | screener.in's Concalls tab links out to the same files |
| **Annual reports** | Company's own IR page; BSE/NSE filing archive | screener.in's Documents tab links out to the same files |
| **Financial statements / quarterly results** | screener.in (structured P&L/balance sheet/cash flow) | screener.in's "Raw PDF" links redirect straight to the underlying BSE filing — no browser needed (see below) |
| **Press releases** | BSE/NSE, filtered to Category "Company Update" / Sub-Category "Press Release / Media Release" | Company's own IR page (sometimes bundled with results, not always a separate document) |
| **Rating reports** | The rating agency's own site (ICRA/CRISIL/CARE/India Ratings/Acuite/Brickwork) — company-specific rationale | The same agencies' free *industry-level* sector special-comment reports (distinct from the company rationale — see "Industry-level and macro sources" below) |
| **Order wins** | BSE/NSE announcements (Category "Company Update," the 6-month sweep) | News search, company's LinkedIn/X (both as discovery, not sole source) |
| **Brokerage reports** | `WebSearch` for `<company> <broker> rating target price` (actively searched now — see "Broker / agency research" below) | User uploads, if the user has one; never bypass a paywall to get the actual PDF |
| **Industry/macro context** (tailwinds, headwinds, sector trends) | Government/ministry/trade-body sites, rating agencies' *industry-level* research, trade publications | General news search on sector-wide (not company-specific) developments |
| **Everything else** (screener.in itself, technicals, secondary price checks) | screener.in, Trendlyne/Tijori as a fallback | — |

`Google`/`WebSearch` isn't its own row — it's the universal lookup tool used to
*locate* the actual document/page for every row above, not a distinct source of
facts in itself. `News`/aggregators (EquityBulls, ScanX, Business Standard, etc.)
work the same way: legitimate for discovery and for the 6-month announcements sweep,
but never cited as the primary source for a number if the primary filing/press
release is reachable instead (see the source-trust-hierarchy below).

An uploaded concall transcript, investor presentation, annual report PDF, or
broker/agency research report (Nuvama, Motilal Oswal, etc.) in place of/alongside a
company name also triggers this skill — sourcing then prefers the uploaded documents
over fetching (see "User-uploaded documents" below). Broker/agency
research is also **actively searched for** as a standing part of sourcing, not only
used when uploaded (see "Broker / agency research" below —
active search finds secondary coverage of a broker's call, not the paywalled report
itself; never bypass a paywall). Either way, a broker/agency finding has no
dedicated section: fold each fact into whichever section it belongs to, tagged
inline `[BROKER_DDMMYYYY]` (see `report_sections.md`'s "Broker / agency research"
rule).

## Source trust hierarchy

Keep this ordering in mind whenever a claim could be pulled from more than one
place — it's what makes a material fact "verified" rather than just "found":

1. **Primary sources** — exchange filings (BSE/NSE Regulation 30 disclosures, annual
   reports, investor presentations as filed), NCLT/court orders, credit-rating agency
   rationales, and the company's own concall transcripts/press releases as filed.
   Citable as-is.
2. **Structured financial data** — screener.in (P&L, balance sheet, cash flow,
   ratios, shareholding-pattern history) or an equivalent aggregator that mirrors
   filed data without editorializing on it. Reliable for numbers; still worth a
   primary-source cross-check for anything landing in Key Risks or Investment Thesis
   Summary.
3. **Discovery-only sources** — news aggregators, PR-syndicated releases, Trendlyne/
   Moneycontrol-style sites. Fine for finding leads (a contract win, a rating action,
   a management interview worth checking) but never cite a number from one without
   tracing it back to the primary filing/press release it originated from —
   aggregators garble numbers more often than the fetch effort to verify would
   suggest.
4. **Third-party broker/agency research** (Nuvama, Motilal Oswal, ICICI Securities'
   institutional research arm, Kotak Institutional, etc.) **and independent
   research platforms/market-research firms** (Equitymaster, analyst blogs, Ken
   Research and similar) — a different category entirely: another analyst's
   *opinion and estimates*, not a filing or a neutral data mirror. Never a primary
   source, never cited as the pipeline's own finding — always attributed to the
   named agency/platform with an inline `[BROKER_DDMMYYYY]` tag (see this file's
   "Broker / agency research" and "Independent research platforms and
   market-research firms" sections above), whether it came from a user upload or
   an active search. Actively searching for this coverage is a standing part of
   sourcing (not upload-only) — but the underlying copyright discipline (never
   reproduce the source's prose verbatim at length, never bypass a paywall)
   applies regardless of how it was obtained. Don't confuse a broker's
   institutional-research arm (tier 4, an opinion) with the same broker's own
   retail stock-quote page (tier 2/3, a data mirror — e.g. ICICI Securities'
   research vs. its ICICI Direct trading-platform quote page are different things
   despite the shared parent).

Flag an unverified management claim explicitly rather than silently upgrading its
confidence (e.g. "management states X on the concall — not yet corroborated by an
independent filing").

## Sandbox constraint (applies to every source below)

The shell sandbox's outbound network is allowlisted — raw `curl`/`requests`/`urllib`
calls to arbitrary domains (screener.in, bseindia.com, nseindia.com, company IR
pages) will fail with a proxy 403. This is expected, not a bug. **Never write or run
a Python fetch script against these domains.** All fetching goes through the
platform's own web tools (`WebSearch`, `mcp__workspace__web_fetch`, and Claude in
Chrome as fallback), which route through an approved path. Scripts in `scripts/`
only ever touch local files.

**The standard escalation pattern, used throughout**: `WebSearch` to locate the page
→ `mcp__workspace__web_fetch` to pull it (works for server-rendered content) → if it
returns a mostly-empty shell (JS-rendered widgets, data tables missing), escalate to
Claude in Chrome (`navigate` + `get_page_text`). Don't burn more than one retry on a
stuck source before falling back to an alternative (see each source's fallback
below) — debugging a stuck fetch costs more than switching sources.

## screener.in (primary source)

Fastest single source for an Indian listed company — aggregates key ratios,
quarterly/annual financials, shareholding pattern (structured, no PDF parsing
needed), and a "Documents" tab linking BSE/NSE-filed annual reports, credit rating
reports, and (for many companies) concall transcripts and investor presentations.

1. `WebSearch` for `site:screener.in <company name>`, or construct
   `https://www.screener.in/company/<BSE_OR_NSE_SYMBOL>/consolidated/` if the symbol
   is already known.
2. `mcp__workspace__web_fetch` the page — mostly server-rendered, should return real
   content.
3. Standard escalation pattern above if the data tables (not just the price chart
   widget) come back empty.
4. Pull direct links to the latest concall transcript, investor presentation, and
   annual report from the Documents tab, then fetch those individually (below).

**If screener.in's numeric widgets won't populate** (price ticker, market cap, P&L,
balance sheet come back masked/blank in both web_fetch and Chrome, even after a
wait) — don't retry repeatedly. Fall back to, in order of preference: BSE/NSE
directly for the raw filing (a primary source anyway, not just a workaround) → the
concall transcript/investor presentation you're fetching regardless (often restates
the full P&L/balance sheet/segment splits) → a secondary quote aggregator
(Tickertape, Trendlyne) for just the one missing number (price/market cap/52-week
range).

**"Raw PDF" links in the Quarterly Results / Profit & Loss tables — a no-browser way
to reach BSE's underlying filing.** Each period column in these tables has a small
"Raw PDF" link at the bottom, e.g. `screener.in/company/source/quarter/<internal_id>/
<month>/<year>/`. This is screener.in's own redirect resolver, not a document itself —
fetching it (via `WebFetch`) returns a 302 redirect straight to the actual BSE filing,
typically an `AnnPdfOpen.aspx?Pname=<uuid>.pdf` link, which `WebFetch` surfaces
explicitly as a "REDIRECT DETECTED" message telling you the exact target URL to fetch
next. **This works with `WebFetch` alone — no Chrome/browser session needed at all**,
unlike BSE's own JS-rendered corp-announcements search page. Two caveats: (1) this is
the **raw quarterly/annual results filing** (the financial-statement schedules as
filed), not the press release specifically — it may or may not be the same document
as the press release for that period, check both if you need the press release's own
narrative framing; (2) some of these raw filings run well past 10MB (full XBRL
financial-statement schedules) and will exceed `WebFetch`'s size limit — if that
happens, this specific document isn't retrievable this way and you should fall back
to whatever narrower source actually has the figure you need (the investor
presentation's own P&L slide, or the press release if smaller).

## Concalls, investor presentations, annual reports, press releases (PDF fetch-extract-log pattern)

Same fetch pattern for all four — usually PDFs hosted on BSE announcements, the
company's own IR page, or linked from screener.in's Documents tab:

1. Get the direct PDF URL (screener.in Documents tab, or `WebSearch` for
   `<company name> <document type> <quarter> filetype:pdf`).
2. `mcp__workspace__web_fetch` the PDF URL; if it returns content, save directly to
   `~/.report-generator/sources/<company_slug>/`. If web_fetch can't retrieve a
   binary PDF cleanly, ask the user to download and drop it in the workspace, or use
   Chrome to navigate + download.
3. Extract: `scripts/pdf_to_text.py` — always the **whole** document, never a guessed
   page range (an annual report's segment/litigation/PP&E notes sit well past the
   MD&A). Pass `--expect-name "<company name>"` when the PDF came from a search
   result rather than a direct IR/exchange link — see `pdf_to_text.py`'s own
   docstring for why (catches a wrong-company PDF before wasting a full extraction
   on it).
   - **For a large annual report (roughly 150+ pages)** where single-process
     extraction is slow (a 380-page report takes ~50s with `pdf_to_text.py`), use
     `python3 scripts/pdf_to_text_parallel.py <input.pdf> <output.txt> [--workers N]`
     instead — it splits the page range into contiguous chunks that together cover
     every page (no gaps, no overlap), extracts them concurrently, and verifies
     every chunk came back before writing anything, so the output is the same
     full-document text, just faster (~45% faster on an 8-core machine for a
     380-page report, and bigger wins when several of a company's annual reports
     are extracted in the same run — kick off all of them as concurrent background
     processes rather than one at a time). If it ever fails to account for a chunk
     it refuses to write a partial file and errors instead — fall back to
     `pdf_to_text.py` in that case rather than accepting a gap.
   - `pdf_to_text.py`'s `--pages START-END` flag exists for one narrow, safe use: a
     **quick scouting pass** — e.g. extracting just the first 5-10 pages to read a
     table of contents and locate a named section's page number before committing to
     full extraction, or re-extracting one already-located page range at higher
     fidelity after the full-text grep already told you where it is. Never use
     `--pages` as a substitute for the full-document extraction above.
4. Log it: `python3 scripts/source_manifest.py <company_slug> add-document --type
   <concall|investor_presentation|annual_report|press_release> --label "<e.g. Q4 FY26>"
   --date "<document's own date>" --filename <name.txt>` (add `--pages-total`/
   `--pages-extracted-start`/`--pages-extracted-end`/`--extraction-verified` for
   annual reports) — right after extraction, every time. This is what lets
   `verify_report.py depth`/`extraction` keep working even after `sources/` is later
   deleted to save space.

For annual reports specifically: **save the PDF before extracting it** — don't
extract-then-discard, since `verify_report.py extraction` needs the source PDF on
disk to confirm full-document coverage.

**Press releases specifically**: often not a standalone PDF on the IR page's own
document archive the way a concall transcript or investor presentation is — check
under a "Press Release"/"Media"/"News" menu item first, but if the IR page bundles it
directly into the same filing as the raw financial results (common for smaller
companies), the press release text may be embedded inside the Regulation 33 results
PDF itself (usually a covering-letter-style page ahead of the raw financial
statements) rather than a separate document — in that case, note in the manifest
label that it's "embedded in results filing" rather than logging a phantom separate
document. If a WebSearch for the company's own press release turns up nothing but
third-party results-coverage instead, that's a legitimate "the company doesn't issue
a standalone press release" finding — state it explicitly (per `reference/sourcing_depth.md`'s
"Press releases" section) rather than silently substituting the third-party coverage
without flagging that the more authoritative primary source wasn't available.

## BSE / NSE filings (fallback / verification)

- BSE: `https://www.bseindia.com/stock-share-price/<company>/<code>/corp-announcements/`
- NSE: `https://www.nseindia.com/companies-listing/corporate-filings-announcements`

Use whenever screener.in is giving trouble (a specific filing not yet indexed, or
the numeric-widget failure above) — not only as a last resort. Same web_fetch →
Chrome fallback pattern; NSE in particular is heavily JS-rendered and often needs
Chrome.

**Finding a specific announcement type (e.g. press releases — see
`reference/sourcing_depth.md`'s "Press releases" section) on BSE's corp-announcements page**:
use the page's own filter form rather than eyeballing the unfiltered list —
**Category: "Company Update"**, **Sub Category: "Press Release / Media Release"**,
plus a From/To Date range covering the lookback window needed. This surfaces exactly
the matching announcements with direct PDF links, one row per filing. The
corp-announcements page itself is JS-rendered (`WebFetch` returns an empty shell), so
filling this form requires a real browser (Claude in Chrome). The resulting PDF links
follow the pattern `bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=<uuid>.pdf` and — unlike
the search page — fetch fine directly with `WebFetch`; the binary saves to disk even
when `WebFetch`'s own summarizer can't parse the digitally-signed PDF structure, so
follow up with `pdf_to_text.py --expect-name "<company name>"` on the saved file
rather than treating that summarizer failure as a fetch failure.

**Raw material import sourcing, when no country/aggregator data is available**: rely on
the annual report's own indigenous-vs-imported raw material note (check this first),
DGFT/Ministry of Commerce trade statistics (`tradestat.commerce.gov.in`, `data.gov.in`
— free, no bot-wall, but aggregate/HS-code-level only, not company-specific), or the
company's own investor presentation/concall (export revenue % is often disclosed there
directly). Export/import shipment-data aggregators (Volza, Seair, ImportGenius, Zauba,
Panjiva) are out of scope for this pipeline — they require a paid subscription this
setup does not have, and are not to be attempted. State any resulting gap explicitly
per `reference/rules_and_validation.md`'s "Never drop anything silently" rule.

## Secondary valuation/technicals aggregators (Trendlyne, Tijori, MoneyWorks4Me)

For a computed historical statistic no filing discloses directly (median PE,
moving averages/RSI/support-resistance): check screener.in first (occasionally
shown directly), then `WebSearch`/`web_fetch` these aggregators, same escalation
pattern as above. These sources don't always agree exactly — if two diverge by more
than a couple of points, report the range and cite both rather than picking one
arbitrarily; if none publish the statistic, say so rather than computing your own
from a partial price series. Always record the as-of date next to any technicals
figure — this data goes stale fast. No reliable free historical-OHLC API is reachable from this
sandbox, so get a pre-computed summary rather than hand-rolling indicators from
scraped data.

**Two more aggregator sub-types, same tier and same treatment as Trendlyne/Tijori
above — never a primary source, fine for a cross-check or a stale-filing fallback:**

- **Retail-broker stock-quote pages** — Alice Blue, ICICI Direct, Nirmal Bang,
  StockeZee, Finology Ticker, and similar. These are the price/quote pages a retail
  brokerage publishes on its own site (not the institutional "broker research"
  reports covered below) — same function as Trendlyne/Tijori, just a different
  publisher. Use the same escalation pattern and the same "always record the as-of
  date" discipline.
- **Company-data/IR aggregators** — Alpha Spread, Tracxn, and similar sites that
  mirror a company's investor-relations material, financials, and peer/competitor
  set into one profile page. Useful for a quick cross-check or for finding a peer
  set to verify against screener.in's own Peers tab, but treat any number pulled
  from one the same as any other aggregator — trace it back to the primary filing
  before citing it if the primary filing is reachable.

## Independent research platforms and market-research firms — same discipline as broker research, different publisher type

Two more source types, both handled with the same opinion/estimate discipline as
"Broker / agency research" below (attribute, paraphrase, never reproduce at length,
never treat as a primary source) even though neither is an institutional broker:

- **Independent equity-research platforms** — Equitymaster and similar Indian
  independent-research houses, plus informal analyst blogs/newsletters (e.g.
  Marketsetup.in-style posts). These publish genuine analysis and opinion, not
  filings — treat exactly like a broker's call: attribute to the named
  platform/author, paraphrase rather than quote at length, and never let their
  thesis stand in for the pipeline's own independently-sourced numbers.
- **Paid market-research firm articles** (Ken Research and similar) — usually a
  free teaser/summary of a larger paid report, covering industry-level sizing or
  trend data rather than a single company. Treat the same as a rating agency's
  *industry-level* special-comment report (see "Industry-level and macro sources"
  below): useful for sector context, always attributed, and don't assume the free
  teaser's headline number is the full picture the paid report actually supports.

**A caution on document-redistribution sites (Scribd and similar):** a PDF hosted on
Scribd is someone else's re-upload, not the primary source, even when its content
looks identical to a company's own filing or presentation. If a WebSearch turns up
a Scribd (or similar) copy of what looks like a primary document, treat it as a
pointer to go find the actual primary source (the company's IR page, BSE/NSE) rather
than citing the redistribution directly — the redistributor's copy could be stale,
altered, or itself infringing, and citing it as the source of record makes that risk
the pipeline's own.

## Credit rating agencies (CRISIL / ICRA / CARE / India Ratings / Acuite / Brickwork)

Check this for every report, not just when the company has visibly raised debt — a
rating rationale is one of the few genuinely independent, professionally-underwritten
views in the whole pipeline (unlike the concall, which is management's own words, or
screener.in, which aggregates public filings without an opinion on them).

Each agency publishes free rating-rationale documents (PDF or webpage) on its own
site whenever a rating is assigned/reviewed/revised; for listed companies these are
also frequently mirrored on BSE/NSE as a SEBI LODR disclosure. `WebSearch`/
`web_fetch` the agency's own site first (`<company name> <agency> rating
rationale`); fall back to the BSE/NSE-mirrored copy if the agency's page is
paywalled/JS-gated. Don't assume no result means "unrated" — a different agency may
cover the company instead; try all of CRISIL/ICRA/CARE/India Ratings/Acuite/
Brickwork before concluding none exists; if genuinely none is found anywhere, say so
explicitly.

- **What to extract from the rationale**: current rating and outlook (e.g. "CRISIL
  A-/Stable"), the instrument it applies to (bank facilities, NCD, commercial paper —
  a company can carry different ratings for different instruments), the date of the
  rationale, and 1-2 lines of the agency's own reasoning — leverage/coverage trend,
  liquidity assessment (strong/adequate/stretched/poor), and any promoter-support,
  personal-guarantee, or related-party-transaction commentary the agency called out.
- **Log it**: use `scripts/rating_tracker.py add-rating` once per rating action found
  (don't re-log an unchanged rating on every regeneration — it's a durable record like
  fund raises, not a per-quarter one like guidance). State the `--action` yourself
  (`first_time`/`reaffirmed`/`upgrade`/`downgrade`/`outlook_revised_positive`/
  `outlook_revised_negative`/`withdrawn`) based on what the rationale itself says
  relative to the company's prior rating — don't try to infer it purely from comparing
  rating-scale notches.
- **Treat a downgrade or negative/watch-negative outlook as a first-class risk signal**:
  run `scripts/rating_tracker.py <slug> report` and reproduce its flag verbatim if the
  currently-in-force rating on any instrument is a downgrade or carries a negative/
  watch-negative outlook — this belongs in both the Promoter/Governance section and, if
  material, the Key Risks section, not softened into a passing mention.
- **Always actively check for a rating action within the last 6 months, every run —
  not just on a regeneration where something else changed.** This is a check-recency
  requirement, distinct from the "not lookback-limited, show the full history" rule
  above for what gets *displayed*: `rating_history.json` showing an old entry from
  a year ago is not evidence that nothing happened since — agencies review ratings on
  their own schedule (annual surveillance reviews, event-driven reviews after a
  material development), so an old cached entry can go stale silently if a run just
  reuses it without a fresh check. On every run (`no_state`, `new_quarter`, or a
  from-scratch rebuild), re-run the agency searches above for each agency already
  known to cover the company, scoped to the last 6 months, even if
  `rating_history.json` already has an entry — if nothing new is found, that's a
  legitimate "checked, no action in the last 6 months" finding, not a reason to skip
  the check.
- **Rating rationales are point-in-time**, usually issued once or twice a year (annual
  surveillance, or on a trigger event like a fund raise) — state the rationale's own
  date next to the rating, the same staleness discipline as the Technical Snapshot.

## Broker / agency research (Nuvama, etc.) — actively search, but respect the copyright boundary

**Actively search for broker/agency coverage of the company as a standing part of
sourcing** (Nuvama, Motilal Oswal, ICICI Securities, Kotak Institutional, Jefferies,
etc.) — `WebSearch` for `<company name> <broker name> rating target price` or
`<company name> brokerage OR broker report rating <year>`, and also check for it
whenever a rating-action/results-reaction search (already done elsewhere in this
playbook) surfaces a broker's call in passing. This is a real policy change from an
earlier, stricter version of this pipeline that only used broker research when a user
directly uploaded a PDF — that restriction is now lifted for *discovery*, but the
underlying copyright/reproduction discipline below is unchanged and still fully
applies regardless of how the report was obtained.

**What you'll actually find via search is almost always secondary coverage of a
broker's call, not the broker's own paywalled PDF** — a business-news article
reporting "Nuvama maintains Buy on <Company>, raises target price to Rs.X citing
Y," a stock-aggregator's "brokerage calls" roundup, or similar. Treat this exactly
like any other secondary/aggregator source in the trust hierarchy (`data_sources.md`)
— it's a legitimate way to *learn that* a broker issued a call and *what its headline
conclusion was* (rating, target price, one-line rationale), but it is not the same as
having the actual report in front of you, and its precision should be trusted
accordingly (a target price and rating direction are usually reported accurately; a
detailed multi-line thesis paraphrase from a news write-up is not fungible with the
broker's own more precise prose).

**If an actual broker report PDF surfaces** (either because the user uploads one, or
because it's genuinely freely accessible — some agencies publish a free-tier or
teaser version, or an aggregator hosts an excerpt) — the same reasons this pipeline
was originally cautious here still apply and must still be respected: these reports
are near-universally paywalled/institutional-distribution products, and every such
report's own disclaimer typically states it is confidential and must not be
"reproduced or redistributed or passed on directly or indirectly in any form to any
other person or published, copied, in whole or in part, for any purpose." **Never
attempt to bypass a paywall, login gate, or access restriction to obtain one** —
active search means searching public web results for what's already publicly
discoverable, not circumventing a broker's distribution controls. Extracting and
attributing the factual content (rating, target price, estimates, thesis points, risk
points) for the user's own personal research report remains fine — that doesn't
extend to reproducing the source document's analysis verbatim at length, whether it
came from an upload or a public find.

**How to use whatever you find — a PDF, or just secondary coverage:**
1. If it's an actual PDF: extract via `pdf_to_text.py` like any other PDF, save to
   `~/.report-generator/sources/<company_slug>/` (e.g.
   `Nuvama_Result_Update_2026-04-29.pdf`/`.txt`). If it's secondary coverage (a news
   article, an aggregator roundup), there's no PDF to extract — just cite the article
   itself as the immediate source, and label the broker's own report as the ultimate
   origin of the claim.
2. Pull the factual snapshot: agency name, analyst name(s) if known, report date,
   report type (Result Update/Company Update/Initiation/Visit Note) if known, rating,
   price at report date, 12-month target price, target methodology (e.g. "15x
   Mar-28E EBITDA") if disclosed, and headline estimates (revenue/EBITDA/PAT/EPS) if
   disclosed — these are facts, not the report's copyrightable prose, and are fine to
   state directly, always attributed. Secondary coverage often won't give you all of
   these (e.g. no target methodology) — state what's actually available, don't
   backfill a gap with an assumption.
3. For thesis/key-risks bullets, **paraphrase in your own words** rather than copying
   verbatim — a one-line factual paraphrase per point ("Nuvama flags [specific risk]
   as a new headwind") captures the substance without reproducing the analyst's actual
   written analysis, whether you're paraphrasing the broker's own prose or a news
   article's paraphrase of it. Do not quote more than a short phrase verbatim.
4. **There is no dedicated section for this.** Fold each fact directly into whichever
   existing report section it belongs to — the target price/rating into Valuation, a
   sector-demand read into Industry Tailwinds/Headwinds, a thesis point into Investment
   Thesis Summary, a flagged risk into Key Risks, and so on — per
   `reference/report_sections.md`'s "Broker / agency research — inline-tagged, no
   dedicated section." What keeps a broker's numbers from blending into the pipeline's
   own independently-sourced Valuation/Financial Performance Summary/Investment Thesis
   figures is an **inline tag on every single point**: `[<BROKER>_<DDMMYYYY>]`
   (agency name uppercase/no-spaces, then the report's own publication date — the
   date the broker's call was made/published, not the date of a news article
   reporting on it, if the two differ and both are known), appended immediately after
   the sentence, table row, or bullet it supports. Tag every sentence individually,
   even consecutive ones from the same report.
5. If a newer report or call from the same or a different agency turns up on a
   regeneration, its points get their own tag with the new report's date — don't
   overwrite an earlier broker-sourced point with a newer one under the same tag; both
   coexist, distinguished by their own dates, same principle as the tracker histories
   elsewhere in this pipeline.
6. If a genuinely thorough search turns up no broker coverage at all, say so
   explicitly in one line (e.g. in Valuation) rather than silently omitting any
   mention that the check was made — same "never drop anything silently" discipline
   as the rest of this pipeline.

## Industry-level and macro sources — don't default to the reporting company's own concall

**This is a standing requirement, not a nice-to-have — the failure mode this guards
against has already happened in practice: a report's entire Industry Tailwinds/
Headwinds section sourced almost solely from the company's own concall commentary,
because nothing forced a genuinely external search.** Management's own framing of
industry conditions is a legitimate secondary data point, but it is not an
independent one, and a section built only from it reads as corroborated when it
isn't. Actively search each of the following before concluding a tailwind/headwind
lacks independent support — treat this with the same "always attempt, state the
outcome either way" discipline as the announcements sweep:

- **Government/regulatory/trade-ministry sources** — these are usually where a
  *quantified* policy tailwind actually lives (an incentive scheme's dollar outlay, a
  tariff schedule, an FTA status), not just a qualitative claim. For India specifically:
  `tradestat.commerce.gov.in`, `data.gov.in` (trade statistics), the relevant central
  ministry's own site (e.g. `texmin.gov.in` for textiles, or the equivalent ministry
  for the company's sector), and `niti.gov.in` (NITI Aayog publishes sector-specific
  "Trade Watch" and policy-tracking documents). `WebSearch` for `<sector> <policy
  scheme name> India ministry` or `<sector> India trade policy <year> site:gov.in`.
- **A rating agency's *industry-level* research** — distinct from the company-specific
  rating rationale already used in Promoter/Governance. ICRA, CRISIL, CARE, and India
  Ratings each publish free sector outlook / special-comment reports independent of
  any single company's rating action, often with real quantified sector trends
  (export growth/decline %, margin direction, capacity utilization trend industry-
  wide). `WebSearch` for `<sector> outlook ICRA OR CRISIL OR CARE <year>` or check the
  agency's own research/publications page directly (e.g. `icra.in/Rating/
  DownloadResearchSpecialCommentReport`-style URLs turn up in search results and are
  directly fetchable).
- **Trade/industry association coverage and sector-specific trade publications** —
  particularly valuable for cross-country/cross-competitor structural context (e.g. a
  comparative operating-metrics table across the company's home country and its
  principal competing sourcing geographies) that no single company would ever state
  in its own disclosures, since it's about the industry's shape, not this company.
  `WebSearch` for `<sector> India vs <competing country> competitiveness` or
  `<sector> industry association report <year>`.
- **General news search for sector-wide, not company-specific, developments** — a
  tariff action, an industry-wide order-book trend, a competing country's policy
  shift. `WebSearch` for `<industry/sector> India outlook <year>` or `<industry>
  order inflow trend India`, and the same query pattern for 1-2 direct peers/
  competitors named in the concall or on screener.in's Peers tab.

Keep the resulting section tight — 2-4 bullets, not a literature review — but the
bullets should draw on whichever of the above genuinely surfaced something, not
default to the concall because that was the source already on hand. If a thorough
attempt across all four genuinely turns up nothing beyond the company's own
commentary, say so explicitly in the report rather than silently presenting
management's framing as independently corroborated.

## LinkedIn / X (Twitter)

**Verified (2026-07) that access is page-type-dependent, not platform-dependent:**
- LinkedIn's listing pages (`linkedin.com/company/<name>/posts/`) are login-walled —
  redirect straight to sign-up, confirmed via direct navigation. Don't try to browse
  a company's feed this way.
- LinkedIn's individual post permalinks (`linkedin.com/posts/<company>-...-
  activity-<id>-...`) work without login — load full content (text, author,
  timestamp, engagement) with no sign-in prompt. If you only have the company name,
  run `WebSearch("<company name> linkedin")` — it returns a mix of both URL types;
  open the `/posts/.../activity-.../` ones, skip the `/company/...` ones.
- X (Twitter) works directly — a public company profile's recent posts load via
  Claude in Chrome with no login required.

## YouTube (supplementary, optional)

Some concalls are recording-only (screener.in's Concalls section links these as
"REC"). `mcp__workspace__web_fetch` on a `youtube.com/watch?v=...` URL returns
nothing usable — fully JS-rendered, don't rely on it. Reading the actual transcript
requires Claude in Chrome (`navigate` to the video, open "Show transcript" via
`find`/`computer`, then `get_page_text`) — depends on the Chrome extension being
connected; if it's unavailable, say so explicitly and skip rather than guessing from
the title/description. Prefer screener.in's own "REC" link tied to the quarter you
need over an open-ended search. If no transcript panel exists (auto-captions off),
don't attempt audio transcription — no such tool in this environment; skip and note
the gap.

## User-uploaded documents

If the user has already uploaded the concall transcript / investor PPT / annual
report / broker report, **always prefer those over fetching** — check the
uploads/workspace folder first before doing any web research for that document type.

A user-uploaded **broker/agency research report** (Nuvama, Motilal Oswal, etc.) is a
distinct case — see this file's "Broker / agency research" section above for
how its facts get folded into the report (no dedicated section, inline
`[BROKER_DDMMYYYY]` tags) — the same handling applies whether the report was
uploaded or found via active search. Treat any file carrying a broker/agency
letterhead, a rating (Buy/Hold/Reduce/Sell), and a 12-month target price as this type
rather than as an investor presentation or annual report — `scripts/verify_report.py
sniff` can classify an ambiguous upload if it isn't obvious from the letterhead.
