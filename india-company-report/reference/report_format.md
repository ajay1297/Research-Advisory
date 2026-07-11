# Report Format Spec

Fixed structure, modeled on the Venus Pipes example (`examples/venus_pipes_report.md`).
Do not deviate from this structure unless the user explicitly asks for a different
template.

## Title

`# <Company Name>`

## Three sections, in this exact order

1. `## Near Term (Next 1 to 2 Quarters)`
2. `## Medium Term (6 to 12 Months)`
3. `## Long Term (1+ Years)`

## Bullet rules (apply to every bullet in every section)

- 2-3 bullets per section. No more than 4.
- Format: `**<Headline, 3-6 words>**: <one to two sentence factual claim in third
  person>. "<verbatim quote from management, attributed only implicitly by context>"`
- The quote must be a real, verbatim line from the concall/transcript/presentation —
  never invented or paraphrased. If no verbatim quote supports a claim, drop the claim.
- The claim sentence states the fact (numbers, dates, %, INR crore figures) and the
  quote substantiates the *tone/certainty* behind it. Numbers belong in the claim
  sentence, not just buried in the quote.
- Near Term bullets should reference concrete near-dated items: this quarter's/next
  quarter's order book, revenue guidance for the current year, near-dated capacity
  coming online, near-dated order wins/LOIs.
- Medium Term bullets should reference 6-12 month items: capex/expansion completion,
  new segment entry, order pipeline over the next few quarters.
- Long Term bullets should reference 1+ year items: new geographies, new end-markets,
  structural margin/mix shift, multi-year growth ranges.

## Sourcing discipline

- Every quote must be traceable to a specific document (concall date, investor
  presentation, or annual report). Keep that mapping in the cached `quotes.json` even
  if it's not printed in the final report, so the user can verify any line if asked.
- If the user wants sourcing shown inline, append `(Q&A, <Month YYYY> concall)` or
  `(Investor Presentation, <Month YYYY>)` after the quote instead of a bare quote mark.
- Never blend two different speakers/documents into a single quote.

## Sections after the Near/Medium/Long Term outlook

Append these five sections, in this order, after Long Term. Each is conditional —
skip a section entirely (don't print an empty heading) if the underlying input isn't
available, and say so in one line under Verification rather than silently omitting it.

### 1. Valuation — Forward PE

Only include if the company gave explicit forward revenue guidance (which the Near/
Medium/Long Term sections should already have captured). Compute via
`scripts/forward_pe.py`:

- Forward EPS = (revenue guidance x PAT margin assumption) / shares outstanding.
- PAT margin assumption: use management's explicitly guided margin if they gave one;
  otherwise fall back to trailing actual PAT margin and label it clearly as an
  **assumption, not guidance**.
- Price: use the current market price fetched from screener.in unless the user
  supplied their own price, in which case use theirs and say so.
- State the formula and every input inline — e.g. "Forward EPS of ₹X (INR<guidance>cr
  revenue x <margin>% assumed PAT margin ÷ <shares>cr shares) implies a forward PE of
  <price>/<EPS> = <N>x at the current price of ₹<price>." Never present forward PE as
  a standalone number without the inputs next to it.
- This is arithmetic on a management estimate, not a valuation call — do not add
  "cheap/expensive" characterization.

### 2. Industry Tailwinds / Headwinds

2-4 bullets, each citing a specific external source (peer concall, sector report, news
on order inflow/pricing/regulation across the industry — not just this company).
Format: `**<Tailwind/Headwind name>**: <one to two sentence factual claim>. (Source:
<name, date>)`. Separate tailwinds from headwinds with a one-line subheading each if
both are present.

### 3. Technical Snapshot

Pull, don't compute — get the trend/moving-average/RSI/support-resistance summary from
a technicals-focused source (see source_playbook.md) rather than deriving indicators
from raw OHLC data. State the data-as-of date. Format: current price, trend versus
50/200-day moving averages, RSI reading and what it implies (overbought/neutral/
oversold), nearest support and resistance. Always timestamp this section since it
goes stale within days — flag that explicitly if the report is more than a week old.

### 4. Promoter / Governance Track Record

Sourced from `scripts/guidance_tracker.py`'s output (see SKILL.md workflow). Show a
short table or list of the last 2 quarters (6 months — the framework's fixed lookback
default for every query, not a per-report choice): guidance given vs. actual delivered,
and whether it was a beat/met/miss. If 2 or more of the last 4 tracked guidance calls
were missed by a meaningful margin, say so plainly — this is exactly the kind of
pattern the section exists to surface, not to soften. Also note, if visible from
screener.in: promoter shareholding trend, any pledged shares, and any auditor
qualification or delayed filing. State facts; do not speculate about motive.

### 5. Key Risks

3-5 bullets covering whichever of these actually apply, sourced from the concall,
filings, or industry context gathered above — never invented:
- Business/execution risk (capacity constraints, customer concentration, single large
  contracts, delivery/quality disputes)
- Financial risk (working capital trend, receivables/payables days, leverage,
  commodity/input-cost exposure, FX exposure)
- Governance risk (from the Promoter/Governance section above, if flagged)
- Macro/industry risk (from the Tailwinds/Headwinds section above, if a headwind rises
  to the level of a real risk to the guidance given)

## What NOT to include

- No buy/sell/hold language, no price targets, no "undervalued/overvalued" framing.
  Forward PE is arithmetic, not a valuation verdict — never follow it with "so the
  stock is cheap/expensive."
- No financial-ratio dumps — only the specific figures a bullet's claim needs.
- No editorializing beyond what management said or what a public filing/data source states.
