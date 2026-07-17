# Report Format Spec (universal rules + the report's opening)

Fixed structure, modeled on the Sterlite Technologies example (`examples/Sterlite_Technologies_report.md`).
Do not deviate from this structure unless the user explicitly asks for a different
template. This file covers the report's opening (Title through Value Chain
Positioning) and the rules that apply everywhere. The eighteen sections that follow
the outlook are in `reference/report_sections.md`; PDF build mechanics are in
`reference/report_assembly.md`.

## Title

`# <Company Name>`

## Cover (PDF only)

The visual PDF (see `reference/report_assembly.md`) opens
with a dedicated cover page via `html_helpers.cover()`: company name, ticker(s) and
exchange(s), a **situation badge** (`html_helpers.badge()`), and the report date. The
markdown deliverable doesn't need a literal cover page — just make sure the situation
classification (see below) and the inputs the badge needs (company name, tickers,
exchanges) are unambiguous in the drafted markdown so the PDF-assembly step can pull
them straight through.

Badge kind mapping (`badge(text, kind)`):
- `kind='growth'` — structural growth situation
- `kind='bull'` — steady compounder or a turnaround with solid interim evidence
- `kind='watch'` — cyclical, or a turnaround/growth story still short on evidence
- `kind='bear'` — structural decline / red-flag-heavy situation
- `kind='neutral'` — mixed or genuinely hard to classify; don't force one of the above

## Company Summary (immediately after the title, before Near Term)

A single short paragraph (3-5 sentences) orienting a reader who has never heard of the
company: what it makes/does, its sector/industry, how long it's been in business or
listed, which exchange(s) it trades on, and current market cap. Source from the
screener.in "About" text, the concall's own opening remarks, or the annual report's
business overview — never invent a description. Keep this factual and neutral; it is
scene-setting, not analysis (the analysis is what the rest of the report is for). No
heading needed for this paragraph beyond the title itself — it sits directly under
`# <Company Name>`, before `## Near Term`.

**Headline stat card grid** — immediately follow the paragraph with a `card_grid()` of
3-4 at-a-glance stats: market cap, current price, 52-week range, sector. Pull these
straight from the screener.in fetch already done for this section; don't compute
anything new. This gives a reader the same orientation the paragraph does, but scannable
in under five seconds — the same principle as the cover badge.

## Situation Classification (immediately after Value Chain Positioning, before Near Term)

Before drafting the outlook sections, state plainly — from the evidence gathered so
far, not from assumption — which broad situation the company is actually in right now.
This single classification drives the cover badge above and should be revisited (not
just carried forward unchanged) on every regeneration, since a company's situation can
shift between refreshes. **Render this as bullet points, not a paragraph** — one
opening bullet stating the classification itself, followed by one bullet per
supporting piece of evidence (a specific number, an independent corroborating source,
a named risk that keeps it from being fully de-risked) — per the general "no long
paragraphs" rule below. A short lead-in clause naming the classification is fine, but
the substance (the evidence) belongs in the bullets, same pattern as Investment Thesis
Summary and MOATs elsewhere in this spec.

- **Distress recovery / turnaround** — real financial trouble (debt default, NCLT
  resolution, negative net worth, trade-to-trade classification) with a documented
  reset since.
- **Steady compounder** — consistent revenue/profit growth, stable or improving margins
  and returns on capital, no major structural change — durability and reasonable
  valuation are the story, not a catalyst.
- **Cyclical** — earnings and stock price move with a commodity price, interest rate, or
  capacity-utilization cycle; the question is where in the cycle the company sits now.
- **Structural growth** — riding a multi-year secular trend (market share gains, new
  product category, geographic expansion) with evidence of execution, not just
  narrative.
- **Structural decline / red-flag heavy** — genuine deterioration with no credible
  turnaround evidence yet. It's completely fine, and expected sometimes, for this
  classification to be the honest one — don't force a "turnaround" or "growth" framing
  onto a company that's actually just declining, and don't force red flags onto a
  genuinely boring, healthy compounder just to fill this out.

A mix of two is fine (e.g. "cyclical, currently in a structural-growth phase of the
cycle") if the evidence genuinely points that way — state both rather than picking one
artificially.

## Value Chain Positioning (immediately after Company Summary, before Near Term)

A short paragraph answering: where does this company sit in its industry's value
chain? What does it buy and from whom (upstream — raw materials, components, licensed
technology)? What does it sell and to whom (downstream — OEMs, retailers,
end-consumers, exports)? Is it a raw-material processor, a component/sub-assembly
maker, an OEM, a brand, a pure distributor, or some combination? Name the specific
tier if the company or its customers describe it that way (e.g. "Tier 2 supplier to X
OEMs, who in turn supply Y end market"). Source from the investor presentation's
business-model/value-chain slide (very common in Indian small/midcap decks), concall
description of customers' customers, or the annual report's industry-overview
section — never invent a position that wasn't stated or a reasonably direct inference
from what was disclosed (e.g., "an OEM's own OEM customers are X" is fair to name if
the company said so; don't guess an entire multi-tier chain from a one-line business
description).

**Backward integration must show up as part of "The Company" box, not the Upstream
box.** Before drawing the diagram, check explicitly how far upstream the company's own
manufacturing actually reaches — many companies describe themselves as integrated back
to a raw or semi-processed input (e.g. "from glass preform to pre-terminated
assemblies" for an optical fiber maker, "from billet to finished pipe" for a tube
maker, "from clinker to cement" for a cement maker). If the company states this kind of
backward-integration claim anywhere in the sources reviewed, the "THE COMPANY" box's
detail line must say so explicitly (e.g. "Manufactures its own glass preform in-house,
then draws optical fiber and cables from it — not a preform buyer"), and the UPSTREAM
box should be scoped to only the inputs genuinely bought from outside (e.g. raw
germanium/silica feedstock), not the semi-processed stage the company itself makes. Get
this wrong and the diagram understates the moat — a company that makes its own preform
has a materially different cost/quality/lead-time position than one that buys preform
and only draws fiber, and a reader skimming the diagram alone should not come away
thinking the two are the same. If the sources don't say how far back the company's own
manufacturing goes, say so in the company box rather than guessing.

**Always follow the paragraph with a flow diagram** in a fenced code block (four
backticks... no, three: ```` ``` ````) in the markdown deliverable. Use a **vertical
stacked-box layout**, one box per value-chain stage, connected by a `|` / `v`
arrow — never a wide horizontal side-by-side layout, regardless of which renderer
produces the final PDF (see `reference/report_assembly.md`) — a vertical stack is bounded only by its single
longest line, so it stays safe regardless of content length, while a horizontal
multi-box layout can silently exceed page width for a company with longer names/
descriptions. Size each box's width to its own longest inner line (pad the `+---+`
border to match, at least 2 spaces of padding either side of the text). Standard
four-stage template — adapt the number of stages/wording to what the company actually
described, don't force exactly four if the real chain is shorter or longer:

```
+--------------------------------------------------+
|  UPSTREAM                                         |
|  <inputs bought, and from whom>                   |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  THE COMPANY -- <Company Name>                    |
|  <what it makes/does, in a few words>             |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  DOWNSTREAM CUSTOMERS                             |
|  <who buys directly from the company>             |
+--------------------------------------------------+
                       |
                       v
+--------------------------------------------------+
|  END MARKET                                       |
|  <where the product/service ultimately ends up>   |
+--------------------------------------------------+
```

Only ASCII characters in the diagram (`+`, `-`, `|`, `v`, letters, digits, standard
punctuation) — no Unicode box-drawing characters (─│┌┐ etc.) or arrow glyphs (→, ↓) —
this keeps the markdown deliverable portable and safe if it's ever rendered through the
legacy `scripts/report_to_pdf.py` reportlab path (see `reference/report_assembly.md`), whose base
font renders those glyphs as black boxes. If a stage isn't disclosed clearly enough to
fill in confidently, say so in the box text itself (e.g. `<not disclosed beyond "OEMs
and distributors">`) rather than inventing specifics.

**In the visual PDF** (the default output — see `reference/report_assembly.md`), this same
upstream/company/downstream/end-market breakdown is rendered with `html_helpers.
flow_diagram()` as styled boxes with a real arrow glyph, not the monospace ASCII block —
WeasyPrint embeds a proper font, so the glyph-safety constraint above only binds the
markdown/reportlab path, not the primary visual pipeline. Pass the same stage
label/detail pairs used to build the ASCII block; don't maintain two different
descriptions of the value chain.

## Three sections, in this exact order

1. `## Near Term (Next 1 to 2 Quarters)`
2. `## Medium Term (6 to 12 Months)`
3. `## Long Term (1+ Years)`

## Bullet rules (apply to every bullet in every section)

- 2-3 bullets per section. No more than 4.
- Format: `**<Headline, 3-6 words>** \`[STATUS]\`: <one to two sentence factual claim
  in third person>. "<verbatim quote from management, attributed only implicitly by
  context>"`
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

### Status pointer — `[STATUS]` on every bullet

Every Near/Medium/Long Term bullet carries one of five status pointers, right after
the headline:

- **`[Pending]`** — a forward-looking claim whose horizon hasn't arrived yet, and
  there's no interim evidence yet to judge progress one way or the other. The default
  for anything genuinely new this quarter.
- **`[On Track]`** — horizon hasn't arrived, but interim evidence (an earlier phase
  delivered, a reaffirmed or raised subsequent guide, a milestone hit on schedule)
  supports it happening. This is the one status that most needs cross-checking prior
  concalls, not just the latest one — see below.
- **`[Delivered]`** — the horizon has passed and the actual outcome met or beat it.
- **`[Delayed]`** — a horizon or milestone that was pushed out from what was originally
  guided (a facility launch slipping a quarter, a target period extended).
- **`[Missed]`** — the horizon has passed and the outcome fell short.

**How to assess it, not guess it**: log every outlook item you draft into
`guidance_history.json` via `scripts/guidance_tracker.py add-guidance`, with your own
`--status` assessment based on what the sources actually say (never auto-derived — a
facility-launch milestone and a revenue number aren't comparable the same way). When a
later concall revises an item already logged (raises/lowers a number, extends a
timeline, confirms an earlier phase completed), log the new entry with
`--supersedes-id` pointing at the earlier one, so the item's full evolution can be
reconstructed — the same way the example status cards work: "at the Q3 call, guided
X; at the Q4 call, revised to Y; now considered on track." Run
`scripts/guidance_tracker.py <slug> report` and pull each item's current status and
evolution history from there — this is not lookback-limited to 6 months, since an
item's full guidance history is exactly what determines whether it's genuinely
"on track" or just freshly asserted. If a bullet is being drafted for the first time
with no prior mention anywhere, its status is almost always `[Pending]`.

## Paragraph length limit — no paragraph longer than 10 lines

**Applies everywhere in the report, not just the sections already specified as
bullet lists.** If a paragraph (Company Summary, Value Chain Positioning, Situation
Classification, the narrative portions of Segment-wise Performance, Manufacturing
Locations, Promoter/Governance, or any other section) runs longer than 10 lines at
normal body-text width, break it into bullet points instead — one bullet per
distinct fact/claim, the same pattern already mandatory for MOATs, Investment Thesis
Summary, and Key Risks. A wall of text that long is hard to scan regardless of how
well-evidenced it is, and a reader shouldn't have to parse a dense paragraph to find
the one number or claim that matters to them.

This is a hint to restructure, not to cut content — don't shorten a genuinely
well-evidenced paragraph just to dodge the line count; convert its sentences into
bullets and keep the substance. A short lead-in sentence or clause framing the
bullets that follow is fine (as already established for Investment Thesis Summary
and MOATs) — the rule is about the *body* of the explanation, not about banning
every sentence of prose.

**Check this before delivering**: `scripts/verify_report.py paragraphs
<report.md>` scans for any paragraph exceeding this length and flags it by section,
so this doesn't rely on eyeballing a 60+KB markdown file for one overlong block.

## Sourcing discipline

- Every quote must be traceable to a specific document (concall date, investor
  presentation, or annual report). Keep that mapping in the cached `quotes.json` even
  if it's not printed in the final report, so the user can verify any line if asked.
- If the user wants sourcing shown inline, append `(Q&A, <Month YYYY> concall)` or
  `(Investor Presentation, <Month YYYY>)` after the quote instead of a bare quote mark.
- Never blend two different speakers/documents into a single quote.

## Never mention internal tooling in the report text

This report is built with the help of local scripts (`scripts/guidance_tracker.py`,
`scripts/fundraise_tracker.py`, `scripts/rating_tracker.py`, `scripts/litigation_tracker.py`,
`scripts/forward_pe.py`, `scripts/capacity_utilization.py`, etc.) — those names belong in
SKILL.md and source_playbook.md, which describe *how the report gets built*, never in
the report itself, which is *the finished deliverable*. Write findings directly: "Guidance
reliability (last 2 tracked quarters):" not "Guidance reliability (via
`scripts/guidance_tracker.py report`):"; "The following fund raises are on record:" not
"Sourced from `scripts/fundraise_tracker.py report`." State the fact, the source document
it came from (concall date, filing, rationale), and — where a flag fires — the flag
itself, in plain language. A reader of the final report should never see a file path,
a script name, or a `--flag` value.
