# Data Sources — where and how everything gets fetched (or uploaded)

This is the **mechanics** reference: which tool to use for which source, and the
standard BSE sweep set that covers most of a report's sourcing. `source_playbook.md`'s
per-topic sections tell you *what* to pull for each part of the report and point back
here for *how* to actually get it — read this once per report, not once per topic.

**BSE covers roughly 90% of what a report needs.** Everything a listed Indian company
is required to disclose — annual reports, results, transcripts, presentations, press
releases, rating actions, order wins, governance events — is filed on BSE and
reachable through `scripts/pipeline/bse_announcements.py`. The remaining ~10% is what has no
filing behind it: brokerage research, industry/macro context, and company social
posts. Those go through `WebSearch` / LinkedIn / X. That split is the whole of this
file.

## What gets fetched from where

| Data type | Source |
|---|---|
| **Concall transcripts** | **BSE** |
| **Annual reports** | **BSE** |
| **Financial statements / quarterly results** | **BSE** for the filed document; screener.in for the structured multi-year tables |
| **Press releases** | **BSE** |
| **Order wins** | **BSE** (the unfiltered sweep) |
| **Rating reports** | **BSE** for the disclosure + **`WebSearch`** the agency's own site for the full rationale |
| **Brokerage reports** | **`WebSearch`** |
| **Industry/macro context** (tailwinds, headwinds, sector trends) | **`WebSearch`** |
| **Bulk & block deals** | **BSE** (`scripts/helpers/bulk_block_deals.py`) |
| **Company social posts** | LinkedIn / X directly |
| **Everything else** (ratios, shareholding history, peers, technicals) | screener.in, Trendlyne/Tijori as fallback |

`WebSearch` isn't a source of facts in its own right for the BSE rows — it's the
lookup tool used to *locate* something. Anything found via news or an aggregator is
discovery only; trace it back to the filing before citing a number from it.

## The standard BSE sweep set

Run all seven on a first-time (`no_state`) run. Every category/subcategory pairing
below is confirmed working (2026-07-19, scrip 514234) and is known to
`bse_announcements.py`, so `--category` may be omitted for any of them:

| Sweep | `--category` / `--subcategory` |
|---|---|
| Annual reports | `Others` / `Reg. 34 (1) Annual Report` |
| Financial results | `Result` / `Financial Results` |
| Press releases | `Company Update` / `Press Release / Media Release` |
| Investor presentations | `Company Update` / `Investor Presentation` |
| Earnings call transcripts | `Company Update` / `Earnings Call Transcript` |
| Credit ratings | `Company Update` / `Credit Rating` |
| Everything else | *(both omitted — unfiltered)* |

**The `--from`/`--to` window is not per-sweep policy any more — it comes from
`check_freshness.py`'s `bse_fetch_window`** (see `pipeline/step1_retrieve.md`'s
"Step 1a" section). Use its `from`/`to` for all seven sweeps, except the Annual
Reports sweep, which uses `annual_from` in place of `from`. On a refresh that window
is the last successful run's timestamp minus a 7-day overlap buffer through today; on
a first-time or `--force` run it is the full standard depth (18 months, 24 for annual
reports). Don't hand-roll a window here — the point of the API's date filter is that
the incremental sweep stays genuinely narrow.

```
python3 scripts/pipeline/bse_announcements.py <scrip_code> --from <YYYYMMDD> --to <YYYYMMDD> \
    [--category "..." --subcategory "..."] [--json]
```

Get `<scrip_code>` from the numeric part of the company's BSE URL (screener.in's BSE
link is the quickest way to it) — e.g. `514234` for Sangam (India).

The seventh, unfiltered sweep is what catches order wins, M&A/acquisitions, MoUs,
management changes, dividends, and exchange clarifications — the six targeted sweeps
by design don't. Assess its rows for materiality per `reference/source_playbook.md`'s
"Announcements sweep" section rather than folding everything in.

**An empty result is a finding, not a failure.** Plenty of companies file no
standalone press release, hold calls only twice a year, or carry a single rating.
State that plainly in the report rather than substituting secondary coverage or
silently omitting the check.

## Source trust hierarchy

1. **Primary** — BSE filings (Reg. 30/33/34 disclosures, annual reports, investor
   presentations, transcripts, press releases as filed), NCLT/court orders, credit
   rating agency rationales. Citable as-is.
2. **Structured financial data** — screener.in's P&L/balance sheet/cash flow/ratios/
   shareholding tables, which mirror filed data without editorializing. Reliable for
   numbers; the BSE filing is the source of record if the two ever disagree.
3. **Discovery-only** — news, aggregators, PR syndication, Trendlyne/Moneycontrol.
   Fine for finding a lead; never cite a number from one without tracing it back to
   the filing it came from.
4. **Third-party research** — brokerages (Nuvama, Motilal Oswal, Kotak Institutional,
   etc.), independent platforms (Equitymaster, analyst blogs), market-research firms
   (Ken Research). Another analyst's *opinion and estimates*, never a primary source,
   always attributed with an inline `[BROKER_DDMMYYYY]` tag. Don't confuse a broker's
   institutional-research arm (tier 4) with the same broker's retail quote page
   (tier 3).

A PDF hosted on Scribd or a similar redistribution site is not the primary source
even when the content looks identical — treat it as a pointer to go find the BSE
filing, not something to cite.

Flag an unverified management claim explicitly rather than silently upgrading its
confidence (e.g. "management states X on the concall — not yet corroborated by an
independent filing").

## Sandbox constraint

The shell sandbox's outbound network is allowlisted — raw `curl`/`requests` calls to
screener.in, company IR pages, and `www.bseindia.com` fail with a proxy 403. **Never
write a Python fetch script against those domains.** Two confirmed exceptions, both
already wrapped in `scripts/`:

- **`api.bseindia.com`** — a different subdomain from the policy-blocked
  `www.bseindia.com`, directly reachable via a plain HTTPS request.
  `bse_announcements.py` and `bulk_block_deals.py` are the only scripts that use it.
  Don't generalize this to other domains without testing each the same way.
- **`WebFetch` on a BSE PDF URL** — `bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=...`
  fetches fine because `WebFetch` runs server-side rather than through the Browser
  pane. The binary saves to disk even when `WebFetch`'s own summarizer can't parse the
  digitally-signed PDF structure, so follow up with `pdf_to_text.py` rather than
  treating that summarizer message as a fetch failure.

BSE's corp-announcements *page* (the JS filter UI on `www.bseindia.com`) is blocked in
the Browser pane and unreachable by any method here — don't attempt it. The sweep set
above replaces it entirely.

Everything else goes through the platform's web tools: `WebSearch` to locate →
`WebFetch`/`mcp__workspace__web_fetch` to pull → Claude in Chrome only if a page is
JS-rendered and comes back an empty shell. Don't burn more than one retry on a stuck
source.

## BSE filings — fetch, extract, log

The pattern for every document the sweeps return:

1. **Discover** — the relevant sweep above returns each filing's date, category,
   headline, and direct `AnnPdfOpen.aspx` PDF URL.
2. **Fetch** — `WebFetch` the PDF URL, save to
   `~/.report-generator/sources/<company_slug>/`. Cap is 10MB; over that, see
   "User-uploaded documents" below.
3. **Extract** — `scripts/pipeline/pdf_to_text.py <input.pdf> <output.txt>`, always the
   **whole** document, never a guessed page range (an annual report's segment,
   litigation, and PP&E notes sit well past the MD&A). Pass
   `--expect-name "<company name>"` when the PDF came from a search result rather than
   the BSE sweep. For a large annual report (~150+ pages), use
   `pdf_to_text_parallel.py [--workers N]` instead — same full-document output, ~45%
   faster, and it refuses to write a partial file if a chunk goes missing. Kick off
   several concurrently when extracting multiple annual reports in one run.
   `--pages START-END` exists for one narrow use: a scouting pass to read a table of
   contents and locate a section before committing to full extraction.
4. **Log** — `python3 scripts/helpers/source_manifest.py <company_slug> add-document --type
   <concall|investor_presentation|annual_report|press_release> --label "<e.g. Q4 FY26>"
   --date "<document's own date>" --filename <name.txt>` (add `--pages-total`/
   `--pages-extracted-start`/`--pages-extracted-end`/`--extraction-verified` for annual
   reports), **right after extraction, every time** — not batched at the end of the
   run. See `pipeline/step3_memorize.md`'s "What gets recorded, and when" for why the
   timing matters.

Save an annual report's PDF **before** extracting — `verify_report.py extraction`
needs the source PDF on disk to confirm full-document coverage.

**If a PDF's pages come back blank** from `pdf_to_text.py`, the source is
image-based/scanned. No OCR tool exists here — note the gap (filing and date confirmed
via the API, figures not recoverable) rather than debugging it as a script failure.

**Press releases specifically**: some companies bundle the release into the Reg. 33
results filing rather than filing it separately. If the press-release sweep is empty
but the results filing carries a covering-letter narrative, note in the manifest label
that it's "embedded in results filing" rather than logging a phantom document.

## screener.in — structured financials, not documents

Not the entry point for documents; BSE is. What screener.in remains genuinely primary
for is the data it computes and tabulates: key ratios, the multi-year quarterly/annual
P&L, balance sheet, cash flow, the shareholding-pattern history (typically 8-12
quarters back, which is what feeds `charts.shareholding_chart()`), and the Peers tab.

1. `WebSearch` for `site:screener.in <company name>`, or construct
   `https://www.screener.in/company/<SYMBOL>/consolidated/` if the symbol is known.
2. `mcp__workspace__web_fetch` the page — mostly server-rendered, one fetch returns
   the whole page.
3. Escalate to Chrome only if the data tables (not just the price widget) come back
   empty.

**If screener.in's numeric widgets won't populate** after one retry, don't keep
retrying — go to the BSE filing for the raw numbers (a primary source anyway), or the
investor presentation you're fetching regardless (which usually restates the full P&L
and segment splits), or a secondary quote aggregator for just the one missing figure
(price/market cap/52-week range).

## Bulk & Block Deals

A standing check every run, same recency discipline as credit ratings. This is one of
the only places a *named* institution, FII/FPI, insurer, or HNI shows up trading on
the open market — the shareholding table only ever shows category totals.

```
python3 scripts/helpers/bulk_block_deals.py <scrip_code> --from <YYYYMMDD> --to <YYYYMMDD>
```

Same `api.bseindia.com` exception as the announcements script. Fetches both deal types
in one call (`--type bulk`/`--type block` to narrow) over the standard ~18-month
window; no pagination needed. An empty result is common and legitimate — say "no bulk
or block deals were recorded in the period reviewed."

**What counts as "notable" is a judgment the script doesn't make.** Only name a deal
if the `CLIENT_NAME` is a recognizable mutual fund, FII/FPI, insurance company, AIF, or
a well-known individual/entity already established elsewhere in the report. A
generic-sounding LLP or trust isn't notable just because it traded in size — don't
invent institutional significance for an unfamiliar name.

**Where it belongs**: Promoter/Governance Track Record, as its own `Bulk & Block Deals`
sub-section after Shareholding Pattern and before Promoter Fund Raises.

## Credit rating agencies

Check every report, not just when the company has visibly raised debt — a rating
rationale is one of the few independently-underwritten views in the whole pipeline.
This is the one document type sourced from **both** BSE and `WebSearch`:

1. **BSE** — the `Credit Rating` sweep above. Authoritative for the fact that an
   action happened and its exact disclosure date; the filed PDF often carries the
   agency's press release in full.
2. **`WebSearch` the agency's own site** — `<company name> <agency> rating rationale`
   across all of CRISIL/ICRA/CARE/India Ratings/Acuite/Brickwork. This is where the
   *full* rationale lives (leverage/coverage trend, liquidity assessment,
   promoter-support and related-party commentary) when BSE carries only a one-page
   intimation, and it catches an agency rating unlisted debt with no exchange filing.

Don't assume no result means "unrated" — try all six agencies before concluding none
covers the company, and say so explicitly if genuinely none does.

- **What to extract**: current rating and outlook (e.g. "CRISIL A-/Stable"), the
  instrument it applies to (a company can carry different ratings for bank facilities,
  NCDs, CP), the rationale's date, and 1-2 lines of the agency's own reasoning.
- **Log it**: `scripts/helpers/rating_tracker.py add-rating`, once per action found. Call it
  for every action the sweep returns without checking first whether it's already
  logged — it's idempotent on `(agency, date, instrument)` and skips exact repeats.
  See `pipeline/step3_memorize.md`'s "What gets recorded, and when" for the
  `--action` values and the conflict case.
- **Check for an action in the last 6 months on every run**, even when
  `rating_history.json` already has entries — agencies review on their own schedule, so
  a cached entry goes stale silently. "Checked, no action in the last 6 months" is a
  legitimate finding; skipping the check isn't.
- Rating rationales are point-in-time — state the rationale's own date next to the
  rating, same staleness discipline as the Technical Snapshot.

## Broker / agency research — `WebSearch`, and respect the copyright boundary

Actively search for broker coverage as a standing part of sourcing: `WebSearch` for
`<company name> <broker name> rating target price` or `<company name> brokerage report
rating <year>`. Also pick it up whenever a rating-action or results-reaction search
surfaces a broker's call in passing.

**What you'll find is almost always secondary coverage, not the broker's PDF** — a
news article reporting "Nuvama maintains Buy, raises target to Rs.X," or an aggregator
roundup. That's a legitimate way to learn *that* a call was made and its headline
conclusion, but it isn't the report itself: a target price and rating direction are
usually reported accurately; a detailed thesis paraphrase from a news write-up is not.

**Never bypass a paywall, login gate, or access restriction** to obtain a report.
Active search means searching what's already publicly discoverable. Extracting and
attributing factual content (rating, target price, estimates, thesis and risk points)
is fine; reproducing the source's analysis verbatim at length is not, whether it came
from an upload or a public find.

**How to use what you find:**
1. An actual PDF → extract via `pdf_to_text.py`, save to
   `~/.report-generator/sources/<company_slug>/`. Secondary coverage → cite the article
   as the immediate source, the broker's report as the ultimate origin.
2. Pull the factual snapshot: agency, analyst, report date, report type, rating, price
   at report date, 12-month target, target methodology, headline estimates. These are
   facts, fine to state directly, always attributed. Secondary coverage often won't have
   all of them — state what's available, don't backfill.
3. Paraphrase thesis/risk points in your own words; no more than a short phrase quoted
   verbatim.
4. **No dedicated section.** Fold each fact into the section it belongs to (target
   price into Valuation, sector read into Industry Tailwinds, a flagged risk into Key
   Risks), each tagged inline `[<BROKER>_<DDMMYYYY>]` — agency uppercase/no-spaces, then
   the broker's own publication date (not the news article's, if both are known). Tag
   every sentence individually, even consecutive ones from the same report.
5. A newer call gets its own tag with its own date — both coexist, don't overwrite.
6. If a thorough search turns up nothing, say so in one line rather than silently
   omitting that the check was made.

**Aggregators worth querying directly** beyond a bare broker-name search: **Trendlyne**
(dated broker calls with rating/target — a discovery index of who covers the stock),
**ICICI Direct** (its own house research, fetchable, but **check the report date** — a
stale multi-year-old note is worse than no data if presented without that caveat), and
**scanx.trade / stockopedia / tradebrains.in**-style sites (confirm *that* something
happened; cross-check any load-bearing number against the filing). Before adding a
retail-education site's claim as new coverage, check it isn't just restating a call
already on file under a different headline.

**An unattributed rating claim is not usable** — "one brokerage downgraded to REDUCE"
with no named agency, analyst, or date anywhere in the result chain fails the sourcing
bar. Note it was seen but couldn't be traced, rather than silently including or
dropping it.

**Log the sweep every run**: `source_manifest.py <slug> add-document --type
broker_sweep --status performed --evidence "<what was searched and found, or 'nothing
attributable'>"`. `verify_report.py brokers` checks this within the last 3 months.

## Industry-level and macro sources — `WebSearch`

**A standing requirement.** The failure mode this guards against has already happened:
an entire Industry Tailwinds/Headwinds section sourced from the company's own concall,
because nothing forced an external search. Management's framing is a legitimate data
point but not an independent one, and a section built only from it reads as
corroborated when it isn't. Search each of the following before concluding a
tailwind/headwind lacks independent support:

- **Government/ministry/trade-body sites** — usually where a *quantified* policy
  tailwind actually lives. `tradestat.commerce.gov.in`, `data.gov.in`, the relevant
  ministry (e.g. `texmin.gov.in`), `niti.gov.in`. Search `<sector> <policy scheme>
  India ministry` or `<sector> India trade policy <year> site:gov.in`.
- **Rating agencies' *industry-level* research** — distinct from the company rationale.
  ICRA/CRISIL/CARE/India Ratings publish free sector outlooks with real quantified
  trends. Search `<sector> outlook ICRA OR CRISIL OR CARE <year>`.
- **Trade associations and sector trade publications** — particularly for
  cross-country/cross-competitor structural context no single company would disclose.
  Search `<sector> India vs <competing country> competitiveness`.
- **Sector-wide news** (not company-specific) — a tariff action, an industry order-book
  trend, a competing country's policy shift. Also run the same query for 1-2 peers.
- **The sector's dominant exogenous variable** — the cost or demand driver management
  has no reason to flag, since it isn't a company decision. Identify which applies
  before searching:

  | Sector | Dominant exogenous variable | Where to check |
  |---|---|---|
  | Textiles/apparel (cotton-dependent) | Monsoon/El Niño-La Niña → cotton yield & price | IMD (`mausam.imd.gov.in`), USDA cotton outlook, ICRA/CRISIL textile notes |
  | Chemicals/synthetic fiber/plastics | Crude oil / naphtha cycles | `ppac.gov.in`, EIA/OPEC outlook |
  | Auto components | Semiconductor cycles, OEM production schedules | SIAM data, OEM order-book commentary |
  | Power/utilities | Coal linkage/availability, PLF trends, monsoon (hydro) | CEA generation reports, Ministry of Power, Coal India dispatch |
  | Pharma/API | API/intermediate price swings, USFDA inspection cycles | USFDA warning letters, API price trackers, China API export data |
  | Agri-inputs/agrochemicals | Rainfall/monsoon on sowing and demand | IMD, agri-ministry sowing data |
  | Metals/mining | Global benchmark prices (LME, iron ore index) | LME, `ibm.gov.in`, World Steel Association |
  | Shipping/logistics | Freight rate indices, bunker prices, chokepoint disruptions | Baltic Dry Index, bunker trackers, news |

  For a sector not listed, spend one search working out the equivalent variable rather
  than skipping this silently.

Keep the resulting section tight — 2-4 bullets, not a literature review. If a thorough
attempt across all five turns up nothing beyond management's own commentary, say so
explicitly rather than presenting their framing as independently corroborated.

## News sources — company-specific coverage

All tier 3 (discovery-only): fine for finding a lead, never cited for a number without
tracing it back to the filing.

- **Business news** — Economic Times, Business Standard, Mint, Moneycontrol, Business
  Today, Financial Express. `<company name> <topic>` unscoped is usually better for a
  first pass than `site:`-scoping, since it also shows which outlet covered it.
- **Broadcast/wire-adjacent** — CNBC-TV18, ET Now/ETMarkets, NDTV Profit — often first
  with a management interview that adds color beyond the concall.
- **Wire/PR syndication** — PR Newswire India, Business Wire India, EquityBulls. Useful
  for confirming a release went out, but a mirror of the filing, not a substitute for it.

## LinkedIn / X (Twitter)

Access is page-type-dependent, not platform-dependent:

- **LinkedIn listing pages** (`linkedin.com/company/<name>/posts/`) are login-walled —
  don't try to browse a company feed this way.
- **LinkedIn post permalinks** (`linkedin.com/posts/<company>-...-activity-<id>-...`)
  load fully without login. If you only have the company name, run
  `WebSearch("<company name> linkedin")` and open the `/posts/.../activity-.../` URLs,
  skip the `/company/...` ones.
- **X is login-walled for a direct profile navigation** — the profile chrome loads but
  the timeline renders a logged-out placeholder regardless of whether the account has
  posted. **Treat this as an access limitation, not a finding of no activity** — never
  report "no recent posts" off a bare profile navigation. Get at content via
  `WebSearch` (`site:x.com`, or a third party quoting a post) instead, and say so
  explicitly if nothing surfaces.

**Lookback window: 3 months** — tighter than the 6-month rating/announcement windows,
deliberately: social is a fast discovery channel, not a disclosure record.

The company's own account is a legitimate source for something not yet in a filing (a
leadership hire, a plant inauguration, a product launch) — cite as "company
LinkedIn/X post, <date>". A third-party post is discovery-only. Fold a real finding
into the section it belongs to rather than creating a heading for it; if nothing
noteworthy turns up, don't mention the check.

## YouTube (supplementary, optional)

Some concalls are recording-only. `web_fetch` on a YouTube URL returns nothing usable.
Reading a transcript requires Claude in Chrome (`navigate` → open "Show transcript" via
`find`/`computer` → `get_page_text`); if the extension isn't connected, say so and skip
rather than guessing from the title. If no transcript panel exists (auto-captions off),
don't attempt audio transcription — no such tool here; note the gap.

## Secondary aggregators (Trendlyne, Tijori, MoneyWorks4Me)

For a computed statistic no filing discloses — median PE, moving averages, RSI,
support/resistance. Check screener.in first, then these. If two sources diverge by more
than a couple of points, report the range and cite both rather than picking one; if
none publish it, say so rather than computing your own from a partial price series.
**Always record the as-of date** — this data goes stale fast. No reliable free
historical-OHLC API is reachable here, so get a pre-computed summary rather than
hand-rolling indicators.

Retail-broker quote pages (ICICI Direct, Alice Blue, Finology Ticker) and company-data
aggregators (Alpha Spread, Tracxn) sit in the same tier — fine for a cross-check,
trace anything load-bearing back to the filing.

## User-uploaded documents

If the user has already uploaded a transcript, presentation, annual report, or broker
report, **prefer those over fetching** — check the uploads/workspace folder before
doing any web research for that document type.

**A local file has no size limit — this is the fix for a PDF too large for `WebFetch`
(10MB), not just an alternative.** Confirmed: a 25MB, 272-page annual report that failed
every remote-fetch path extracted cleanly via `pdf_to_text.py` from a local copy (found
already sitting in the user's Downloads, in one case — worth checking there before
asking for a re-download). When a large PDF is blocked by size on every remote path,
don't keep trying fetch variants; ask.

**Batch uploads of the same document type** (several quarters' filings at once) get
processed in one pass: extract each, identify its date/subject from the covering-letter
text (grep for `Re:`/`Sub:` near the top), and log each via `source_manifest.py
add-document --user-uploaded` **individually** — each is a separate dated primary
source, even arriving in one batch.

A user-uploaded **broker/agency report** is a distinct case — see "Broker / agency
research" above for how its facts get folded in. Treat any file with a broker
letterhead, a rating, and a 12-month target as that type rather than an investor
presentation; `scripts/pipeline/verify_report.py sniff` can classify an ambiguous upload.
