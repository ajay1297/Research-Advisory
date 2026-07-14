# Data Sources — where and how everything gets fetched (or uploaded)

This is the **mechanics** reference: which tool to use for which source, URL
patterns, fallback chains, and how a user-uploaded document changes the picture.
`source_playbook.md`'s per-topic sections tell you *what* to pull for each part of
the report and point back here for *how* to actually get it — read this once per
report, not once per topic.

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
4. **Third-party broker/agency research** (Nuvama, Motilal Oswal, ICICI Securities,
   Kotak Institutional, etc.) — a different category entirely: another analyst's
   *opinion and estimates*, not a filing or a neutral data mirror. Never a primary
   source, never cited as the pipeline's own finding. Only enters the report when
   the user directly uploads one (see "User-uploaded documents" below) — this
   pipeline never fetches broker research proactively.

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

## Concalls, investor presentations, annual reports (PDF fetch-extract-log pattern)

Same fetch pattern for all three — usually PDFs hosted on BSE announcements, the
company's own IR page, or linked from screener.in's Documents tab:

1. Get the direct PDF URL (screener.in Documents tab, or `WebSearch` for
   `<company name> <document type> <quarter> filetype:pdf`).
2. `mcp__workspace__web_fetch` the PDF URL; if it returns content, save directly to
   `~/.report-generator/sources/<company_slug>/`. If web_fetch can't retrieve a
   binary PDF cleanly, ask the user to download and drop it in the workspace, or use
   Chrome to navigate + download.
3. Extract: `scripts/pdf_to_text.py` (or `pdf_to_text_parallel.py` for 150+ page
   annual reports) — always the **whole** document, never a guessed page range (an
   annual report's segment/litigation/PP&E notes sit well past the MD&A). Pass
   `--expect-name "<company name>"` when the PDF came from a search result rather
   than a direct IR/exchange link — see `pdf_to_text.py`'s own docstring for why
   (catches a wrong-company PDF before wasting a full extraction on it).
4. Log it: `python3 scripts/source_manifest.py <company_slug> add-document --type
   <concall|investor_presentation|annual_report> --label "<e.g. Q4 FY26>" --date
   "<document's own date>" --filename <name.txt>` (add `--pages-total`/
   `--pages-extracted-start`/`--pages-extracted-end`/`--extraction-verified` for
   annual reports) — right after extraction, every time. This is what lets
   `verify_report.py depth`/`extraction` keep working even after `sources/` is later
   deleted to save space.

For annual reports specifically: **save the PDF before extracting it** — don't
extract-then-discard, since `verify_report.py extraction` needs the source PDF on
disk to confirm full-document coverage.

## BSE / NSE filings (fallback / verification)

- BSE: `https://www.bseindia.com/stock-share-price/<company>/<code>/corp-announcements/`
- NSE: `https://www.nseindia.com/companies-listing/corporate-filings-announcements`

Use whenever screener.in is giving trouble (a specific filing not yet indexed, or
the numeric-widget failure above) — not only as a last resort. Same web_fetch →
Chrome fallback pattern; NSE in particular is heavily JS-rendered and often needs
Chrome.

## Export/import shipment aggregators (Volza, Seair, ImportGenius, Zauba, Panjiva)

**Verified (2026-07) unreliable as an automated/free source** — worth one quick
attempt, never worth retrying:
- Volza and Zauba sit behind bot-detection challenge pages that block automated
  fetching outright.
- Seair's public page renders a static, years-old teaser sample unrelated to any
  specific company — real querying is gated behind signup/subscription.
- ImportGenius and Panjiva are subscription-only with no usable free tier.

**The check, in order**: one attempt (plain search or direct navigation, don't burn
a retry) → if bot-walled/stale/paywalled, that's a determined outcome, not
inconclusive — stop and fall back to what's actually reliable: the annual report's
own indigenous-vs-imported raw material note (check this first, not after the
aggregator attempt), DGFT/Ministry of Commerce trade statistics
(`tradestat.commerce.gov.in`, `data.gov.in` — free, no bot-wall, but aggregate/
HS-code-level only, not company-specific), or the company's own investor
presentation/concall (export revenue % is often disclosed there directly). If the
user has their own paid subscription/API key, an authenticated fetch can be used
instead — never sign up or pay on the user's behalf. State the outcome explicitly
either way per SKILL.md's "Never drop anything silently" rule.

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

## Credit rating agencies (CRISIL / ICRA / CARE / India Ratings / Acuite / Brickwork)

Each agency publishes free rating-rationale documents (PDF or webpage) on its own
site whenever a rating is assigned/reviewed/revised; for listed companies these are
also frequently mirrored on BSE/NSE as a SEBI LODR disclosure. `WebSearch`/
`web_fetch` the agency's own site first (`<company name> <agency> rating
rationale`); fall back to the BSE/NSE-mirrored copy if the agency's page is
paywalled/JS-gated. Don't assume no result means "unrated" — a different agency may
cover the company instead; try all of CRISIL/ICRA/CARE/India Ratings/Acuite/
Brickwork before concluding none exists.

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
distinct case — see `source_playbook.md`'s "Broker / agency research reports"
section for how its facts get folded into the report (no dedicated section, inline
`[BROKER_DDMMYYYY]` tags). Treat any file carrying a broker/agency letterhead, a
rating (Buy/Hold/Reduce/Sell), and a 12-month target price as this type rather than
as an investor presentation or annual report — `scripts/verify_report.py sniff` can
classify an ambiguous upload if it isn't obvious from the letterhead.
