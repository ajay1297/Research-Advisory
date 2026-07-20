# Step 2 — Synthesize (Build Each Section)

Second of three step files — see `pipeline/step1_retrieve.md`'s header for how the
four chain together.

## Building each section

**Format rules for every section (tables vs. bullets, what's mandatory, what's
conditional) live in `reference/report_format.md` (the opening sections) and
`reference/report_sections.md` (the eighteen sections after the outlook). Sourcing
steps (which slide, which tab, which script call, which aggregator) live in
`reference/source_playbook.md` — its section headings match these one-to-one.** This
index exists so you can see the whole report's shape and each section's trigger
condition in one pass, without opening any reference file yet — open the matching
`source_playbook.md` section when you actually start sourcing that part, and the
matching format file when you draft it.

In order: **Company Summary** (never invent) · **Value Chain Positioning** (with the
vertical flow diagram — check backward-integration depth explicitly, see
`reference/report_format.md`'s backward-integration rule) · **Situation Classification** (a
judgment call from what's already gathered — re-examine every regeneration, don't
carry forward) · **Near/Medium/Long Term outlook** (verbatim-quoted bullets, each with
a status pointer logged via `guidance_tracker.py add-guidance` — `--supersedes-id`
when a later concall revises an earlier item) · **Marquee & Niche Customers** (bullet
list; if a named customer is itself publicly listed on any exchange, check its last 4
quarters of concalls — see source_playbook.md's "Checking a named customer's own
guidance") · **Capex/Milestones/Certifications Timeline** (also the roll-up table for
every other future-dated commitment elsewhere in the report) · **CDMO Pipeline**
(pharma + explicit CDMO/CRAMS line only, gated at Company Summary — see above) ·
**Financial Performance Summary** (YoY table, exempt from the standard lookback, plus
the balance-sheet anomaly check — debtor days, cash vs. short-term borrowings,
goodwill/net-worth/other-assets scan) · **Segment-wise Performance** (table only, one
per basis if more than one disclosed, plus exports-vs-domestic if found) · **Order
Book** (table with as-of date, composition breakdown if disclosed) · **Manufacturing
Locations & Physical Assets** (bullet list) **+ Raw Material Sourcing** (domestic vs.
imported %, country breakdown if any portion is imported) · **Capacity Utilization & Headroom**
(industry's own physical unit, never a bare %; flag shared multi-purpose pools; run
`capacity_utilization.py`, `--post-capex-max-revenue-cr` if a post-capex figure
already surfaced elsewhere) · **Total Addressable Market** (only if an actual figure,
not a growth rate, was disclosed) · **Valuation/Forward PE** (computed inline, plus
the company's own historical median PE from a secondary aggregator) · **Broker/agency
research** (uploaded OR actively searched — inline `[BROKER_DDMMYYYY]` tags, no
dedicated section, paraphrase never reproduce, never bypass a paywall) ·
**Industry Tailwinds/Headwinds** ·
**MOATs** (bullet points — entry barriers, IP/tech moat, product
criticality, switching costs; never invent one sources don't support) · **Technical
Snapshot** (table or bullets, never prose, normal body-text size) · **Promoter/
Governance Track Record** — guidance reliability (`guidance_tracker.py report`) +
shareholding trend table + **bulk & block deals** (`bulk_block_deals.py`, name only
recognizable institutions/funds/AIFs/FIIs — never every counterparty — checked every
report regardless of whether the company looks active, not lookback-limited) +
**promoter fund raises** (`fundraise_tracker.py add-raise`,
`--investors` whenever named, not lookback-limited) + **credit ratings**
(`rating_tracker.py add-rating`, every report gets checked regardless of visible debt,
not lookback-limited) + **litigation** (`litigation_tracker.py add-case`, watch for
`--status dismissed_appealable` vs. `closed_final`, not lookback-limited) ·
**Investment Thesis Summary** (bullet points, one claim per bullet — or an honest "the
research doesn't support a real thesis" if that's what it shows) · **Key Risks**
(mandatory even in a bullish report — carries through any rating downgrade, appealable
litigation, high-utilization flag, or customer-concentration figure surfaced above) ·
**Verdict** (one short paragraph — situation classification, strongest evidence,
biggest open question, honest confidence level) · **Sources** (numbered, hyperlinked,
reusing `quotes.json`'s traceability).
