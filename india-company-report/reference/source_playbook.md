# Source Playbook

Which tool to use for which source. Read this once per report, not per source.

## Important sandbox constraint

The shell sandbox's outbound network is allowlisted — raw `curl`/`requests`/`urllib`
calls to arbitrary domains (screener.in, bseindia.com, nseindia.com, company IR pages)
will fail with a proxy 403. This is expected, not a bug. **Never write or run a Python
fetch script against these domains.** All fetching goes through the platform's own web
tools (`WebSearch`, `mcp__workspace__web_fetch`, and Claude in Chrome as fallback), which
route through an approved path. Scripts in `scripts/` only ever touch local files.

## Primary source: screener.in

screener.in is the fastest single source for an Indian listed company — it aggregates:
- Key ratios, quarterly/annual financials, shareholding pattern (structured, no PDF
  parsing needed)
- A "Documents" tab linking the company's BSE/NSE-filed annual reports, credit rating
  reports, and (for many companies) concall transcripts and investor presentations

Steps:
1. `WebSearch` for `site:screener.in <company name>` to find the exact company page
   (or construct `https://www.screener.in/company/<BSE_OR_NSE_SYMBOL>/consolidated/`
   if the symbol is already known).
2. `mcp__workspace__web_fetch` the page. screener.in is mostly server-rendered, so
   web_fetch should return real content — ratios table, quarterly results, and the
   Documents section with links.
3. If the fetch returns a mostly-empty shell (JS-rendered widgets like the
   price chart won't matter, but if the *data tables* are missing), escalate to Claude
   in Chrome (`navigate` + `get_page_text`) per the platform's escalation rule.
4. Pull the direct links to the latest concall transcript, investor presentation, and
   annual report from the Documents tab, then fetch/download those individually (see below).

## Concall transcripts

Usually PDFs hosted on BSE announcements, the company's own investor relations page, or
linked from screener.in's Documents tab. Some are also summarized/hosted by third-party
aggregators.
1. Get the direct PDF URL (from screener.in Documents tab or `WebSearch` for
   `<company name> concall transcript <quarter> filetype:pdf`).
2. `mcp__workspace__web_fetch` the PDF URL — if the tool returns the PDF content, save it
   directly to `research_cache/<COMPANY_SLUG>/raw/<file>.pdf`.
3. If web_fetch can't retrieve a binary PDF cleanly, ask the user to download and drop it
   in the workspace folder instead, or use Chrome to navigate + download.
4. Run `scripts/pdf_to_text.py` on the saved PDF (local, no network).

## Investor presentations

Same path as concall transcripts — usually a PDF from the same BSE filing/IR page/
screener.in Documents tab for the same quarter.

## Annual reports

Same path, larger PDF (100-300 pages). Only extract the sections relevant to forward
guidance (Management Discussion & Analysis / Chairman's letter / outlook section) —
don't run the full report through `extract_theme_quotes.py`; grep the extracted text
for the MD&A section heading first and slice to that range before further processing,
to avoid burning tokens on financial statement boilerplate.

## BSE / NSE filings (fallback / verification)

- BSE: `https://www.bseindia.com/stock-share-price/<company>/<code>/corp-announcements/`
- NSE: `https://www.nseindia.com/companies-listing/corporate-filings-announcements`
Use only if screener.in's Documents tab is missing the specific filing (e.g. a very
recent announcement not yet indexed by screener.in). Same web_fetch → Chrome fallback
pattern applies; NSE in particular is heavily JS-rendered and often needs Chrome.

## Forward PE inputs

From screener.in's summary block: current market price, shares outstanding (Equity
Capital ÷ Face Value, both shown on the page), and trailing PAT/revenue (for a
fallback margin assumption if management didn't guide one). Revenue guidance itself
comes from the concall, not screener.in. If the user gives their own price, use that
instead and label it "user-supplied" per `reference/report_format.md`.

## Industry tailwinds / headwinds

Don't infer these from the single company's concall alone — that's already covered
in the Near/Medium/Long Term sections. Look outward:
- `WebSearch` for `<industry/sector> India outlook <year>`, `<industry> order inflow
  trend India`, or the same query for 1-2 direct peers/competitors named in the
  concall or on screener.in's Peers tab.
- Sector-level commentary from industry bodies (e.g. CII, sector-specific
  associations), rating agency sector notes (CRISIL/ICRA/CARE publish free sector
  outlook notes), or a peer's own concall commentary on the same demand drivers.
- Keep this section tight — 2-4 bullets, not a literature review.

## Technical snapshot

Get a pre-computed technicals summary rather than fetching raw daily OHLC data and
calculating indicators yourself — no reliable free historical-price API is reachable
from this sandbox, and hand-rolling RSI/moving averages from scraped data is a poor
use of tokens for what's meant to be a one-line snapshot.
- `WebSearch`/`mcp__workspace__web_fetch` a technicals page for the ticker — Trendlyne,
  MoneyControl's technicals tab, or Screener AI's technical widgets often list
  moving averages, RSI, and support/resistance directly.
- If the page is JS-rendered and web_fetch returns a shell, escalate to Claude in
  Chrome per the platform's own escalation rule.
- Always record the as-of date next to the numbers — this section goes stale fast.

## Promoter / governance track record

Two separate things to check:
1. **Guidance reliability** — use `scripts/guidance_tracker.py` against the cached
   `guidance_history.json` for the company (built up over successive report runs from
   this skill; see SKILL.md). This needs no new fetching once a couple of quarters are
   logged — it's a local comparison.
2. **Other governance signals** — pull directly from screener.in's Shareholding
   Pattern (promoter holding trend, pledge % if shown) and Documents tab (auditor
   qualifications or delayed filings usually show up as flagged BSE/NSE
   announcements). A falling promoter holding % is not automatically a red flag
   (could be a planned OFS/QIP) — state the fact and, if the concall or an
   announcement explains it, cite that; don't speculate.

## YouTube (supplementary, optional — not a primary source)

Some concalls are only available as a recording, not a written transcript (screener.in's
Concalls section links these as "REC" against the relevant quarter, alongside the
Transcript/PPT links). YouTube is also occasionally useful for a management interview
(CNBC/ET Now/ETMarkets) that adds outlook color beyond the concall — treat that as
industry/company color, not as the primary near/medium/long-term source.

**What actually works here, tested in this sandbox:**
- `mcp__workspace__web_fetch` on a `youtube.com/watch?v=...` URL returns nothing usable
  — YouTube is fully JS-rendered, so a plain fetch gets an empty shell, not the video
  transcript. Don't rely on it.
- Reading the actual transcript requires Claude in Chrome (`navigate` to the video,
  open the "Show transcript" panel via `find`/`computer`, then `get_page_text`). This
  is a real path but depends on the Chrome extension being installed and connected —
  it was **not connected** when this was last tested. If it's unavailable when you need
  it, say so explicitly and skip the YouTube source rather than guessing at content
  from the video title/description alone.
- If Chrome is connected: prefer the exact YouTube link screener.in already ties to
  the quarter you need (the "REC" link) over an open-ended YouTube search — this
  guarantees you're watching the right, already-dated recording instead of having to
  filter search results by upload date yourself (see the "Filtering to a 6-month
  window" section below for why this matters).
- If no transcript panel exists for a given video (auto-captions off), don't try to
  transcribe audio — there's no audio-transcription tool in this environment. Skip it
  and note the gap rather than fabricating quotes.

## Filtering to a 6-month window — how it actually works

There's no server-side "give me the last 6 months only" parameter on either
screener.in or YouTube/WebSearch. The 6-month lookback (the framework's fixed default
— see SKILL.md) is enforced by what gets *used and cached*, not by what gets fetched:

- **screener.in**: one `web_fetch` always returns the entire page — the full
  multi-year quarterly table, full P&L/balance sheet history, full shareholding
  history back to 2015-17, and the full concalls list back to whenever the company
  started disclosing them. There is no URL parameter or lighter endpoint that returns
  only recent data. The 6-month filter happens after the fetch: read only the last 1-2
  columns of the quarterly table, only the top 1-2 entries of the Concalls list, and
  only the most recent shareholding-pattern column. Don't cache or carry forward the
  older columns/entries into `research_cache/` — leave them in the one-time fetch and
  discard them once you've pulled what you need. This means the fetch itself isn't
  smaller, but the tokens spent reasoning over the result, and what persists in the
  cache, are scoped to 6 months.
- **YouTube / WebSearch**: `WebSearch`'s schema has no date-range parameter, so you
  can't ask it for "concalls from the last 6 months" directly. Two ways to stay
  scoped: (1) prefer the quarter-linked link from screener.in as above, which is
  already dated by construction; (2) if doing a genuinely open search (e.g. industry
  commentary, not a specific concall), phrase the query with the specific
  month/quarter you want (e.g. "TD Power Systems management interview June 2026") and
  then check the actual publish date shown in the search result or on the fetched
  page before using it — discard anything you can't confirm falls inside the window.

## User-uploaded documents

If the user has already uploaded the concall transcript / investor PPT / annual report
(they said they'd share templates and source documents directly), always prefer those
over fetching — check the uploads/workspace folder first before doing any web research.
