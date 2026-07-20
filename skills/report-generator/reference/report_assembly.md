# Assembly — building the visual PDF

Read this once, at the point you're about to build the HTML/PDF — after the markdown
report is drafted per `reference/report_format.md` and `reference/report_sections.md`.
This file is purely about rendering what's already been written, not about what goes
in the report.

The default, primary deliverable is an infographic-style PDF assembled as HTML and
rendered with WeasyPrint — the same pattern as `scripts/helpers/charts.py` and
`scripts/helpers/html_helpers.py`'s own docstrings, which live in this plugin's `scripts/`
directory, paired with `assets/report_style.css`. The drafted markdown report (per
`reference/report_sections.md`'s section-by-section spec) is still produced and cached as usual — see
`pipeline/step3_memorize.md`'s "Save and cache" step — the HTML/PDF assembly consumes
the same facts and figures, it doesn't replace the markdown as the source of truth for
what was found.

**Tables are the default; charts are opt-in, not automatic.** Earlier drafts of this
skill defaulted to a matplotlib chart in Financial Performance Summary, Capacity
Utilization, the Promoter/Governance shareholding trend, and Promoter Fund Raises — this
was reversed after the report itself came out too chart-heavy without a corresponding
gain in clarity. **Financial Performance Summary, Order Book, Capacity Utilization &
Headroom, the shareholding trend, and Promoter Fund Raises all render as `data_table()`
only by default — no `charts.*` call for any of them unless the user explicitly asks
for a visual/chart version.** `scripts/helpers/charts.py` still exists and still works if a
chart is specifically requested for a given report, or if a genuinely long time series
(10+ years) makes a table hard to scan — but that's now the exception, not the default.
A one-off list of named allottees with exact amounts, or a detailed litigation/rating
table, was always better as a dense `data_table()` anyway — charting it would lose
precision the reader needs.

**Two standing exceptions, always chart + table together, never chart-only:**
Segment-wise Performance's **by-geography basis** (FY-vs-FY, % of total revenue) and
Order Book's **business-wise composition breakdown** each get a `pie_chart()` call
immediately after their `data_table()` — one pie per period/basis shown in the table
(e.g. FY26 and FY25 each get their own pie for a geography split shown across two
columns). The table stays mandatory regardless — the pie is additive, for the reader's
at-a-glance read, not a replacement for the exact percentages, which belong in the table
alone (see the pie_chart() docstring in `scripts/helpers/charts.py`; use `donut_chart()`
instead, unchanged, for Promoter Fund Raises' fund-raise/ownership breakdowns per the
existing convention above — the two are visually distinct so a reader can tell which
kind of breakdown they're looking at). Only render the pie if the relevant basis is
actually disclosed in a form with clean percentage/proportional splits summing sensibly
to ~100% — don't force a pie onto a partial or non-exhaustive breakdown.

Narrative sections (Company Summary,
Situation Classification, Investment Thesis Summary, Key Risks) stay as text/
`flag_list()`. **Marquee & Niche Customers and Manufacturing Locations & Physical
Assets always render as a bullet list (`flag_list()` with `kind=''` or a plain `<ul>`),
never merged into one paragraph** — each customer/location is its own scannable point.

**Use real Unicode punctuation characters, never HTML entities, anywhere in report
text** — write an actual `—` (em dash), `–` (en dash), `·` (middle dot), `…` (ellipsis)
or `→` (arrow) character in the string, not `&mdash;`, `&ndash;`, `&middot;`, `&hellip;`,
or `&rarr;`. WeasyPrint/DejaVu Sans renders real Unicode punctuation natively (this
pipeline has none of reportlab's base-font glyph-safety problem — see
`reference/report_format.md`'s Value Chain
Positioning section), and typing the HTML-entity form instead is actively unsafe:
several `html_helpers` functions (`cover()`'s `meta_line`, `card_grid()`, `data_table()`,
`sources_list()`) pass their text through `esc()` for safety, which converts the
entity's leading `&` into `&amp;` — so `&middot;` renders as the literal text
"`&middot;`" on the page instead of a middle dot. Only `para()`, `flag_list()`, and
`verdict_box()` accept raw HTML and would render an entity correctly, and relying on
that split is exactly the kind of inconsistency that causes this bug — so just never use
entities, in any field, and the whole class of bug is impossible.

**Keep the page tight — avoid layout choices that create dead whitespace.** Use
`chart_row()` only when you're genuinely placing two or more charts side by side; a
single chart is `chart_block(...)` on its own, never `chart_row([chart_block(...)])` —
wrapping one chart in a flex row buys nothing and can stretch a small chart (e.g. a
donut) wider than intended, leaving an oddly empty-looking block. The cover page
itself should stay short (title, ticker, badge, date) — it's an orientation page, not
a page meant to be mostly blank.

**Never call `page_break()` anywhere in the document — zero calls, not one.** An
earlier version of this rule called for exactly one `page_break()` immediately before
Investment Thesis Summary, so the closing thesis/risks/verdict would run together on
a fresh page. That traded away too much: it **always** produces a gap of dead
whitespace at the bottom of whatever page it interrupts — confirmed in practice (a
page landing at ~30% of the surrounding pages' word density is the direct, guaranteed
result whenever the preceding section doesn't happen to end exactly at a page
boundary, which is most of the time). **Only the cover page is allowed to be
sparse/mostly blank** — every other page must be reasonably filled; a forced page
break is the single most common cause of a violation of that rule, so it's banned
outright rather than limited to one "safe" use. Let content flow naturally between
every section instead, relying on the CSS rules already in `report_style.css`
(`page-break-after: avoid` on headings, `page-break-inside: avoid` on table rows/
timeline items) to prevent an orphaned heading or a split table row — a section
spanning a page boundary normally is preferable to guaranteed dead space, every time.
`scripts/pipeline/verify_report.py whitespace <pdf>` checks this mechanically before delivery
— see `reference/guardrails.md`.

```python
import sys
sys.path.insert(0, '<skill_dir>/scripts')
from charts import revenue_profit_chart, quarterly_trend_chart, shareholding_chart, \
    before_after_chart, donut_chart, pie_chart, line_compare_chart
from html_helpers import *

body = ''
body += cover('Company Name', 'NSE: TICKER | BSE: 000000',
               badge('STRUCTURAL GROWTH', 'growth'), 'Report date: 12 July 2026')
body += section('Company Summary')
body += para('...')
body += card_grid([('Market cap', 'Rs X Cr', ''), ('Price', 'Rs Y', ''), ...])
# ... Value Chain Positioning, flow_diagram(), Situation Classification,
#     Near/Medium/Long Term outlook, sections 1-19 ...
body += section('Financial Performance Summary')
revenue_profit_chart('rp.png', years, revenue, profit)
body += chart_block('rp.png', 'Annual revenue and net profit. Source: screener.in')
body += data_table(['Year', 'Revenue', 'YoY %', 'PBT', 'PAT', 'PAT margin %'], rows)
# ... through section 19 (Sources) ...

html = render(body, '<skill_dir>/assets/report_style.css')
open('report.html', 'w').write(html)
```

Then: `python3 -m weasyprint report.html report.pdf` (`pip install weasyprint
matplotlib --break-system-packages` once, if either is missing).

Save chart PNGs to a working directory alongside the intermediate HTML, and delete both
(along with the HTML) once the PDF is built and verified — only the final PDF and the
source `report.md` belong in `~/.report-generator/output/<company_slug>/`.

**Verify the rendered output before delivering it**: render a few pages to JPEG
(`pdftoppm -jpeg -r 120 report.pdf page`) to visually check charts aren't clipped,
tables aren't overflowing the page width, and page breaks land sensibly.

**Legacy fallback**: `scripts/pipeline/report_to_pdf.py` (markdown → PDF via reportlab, no
charts, no cover/badges) still exists and still works if WeasyPrint genuinely can't be
installed in a given environment — text-only, but never blocks delivery. Prefer the
visual pipeline above whenever both are available.

Two easy mistakes to avoid:
- WeasyPrint needs `pip install weasyprint --break-system-packages` if it's not already
  present — check before assuming it's missing.
- `data_table()`'s `total_row_index` bolds one row (typically a "Total" summary row) —
  pass the row's index within `rows`, not counting the header.
