# Step 3 — Memorize (Save and Verify)

Fourth of four step files — see `reference/step0_perceive.md`'s header for how the
four chain together.

## Save and cache

Save every deliverable — **always both** the `.md` report **and** a PDF, every run,
without waiting to be asked — to `~/.report-generator/output/<company_slug>/` (e.g.
`~/.report-generator/output/td_power_systems/TD_Power_Systems_report.md` and
`~/.report-generator/output/td_power_systems/TD_Power_Systems_report.pdf`), **never**
inside the plugin's own directory. This keeps user-facing deliverables separate from
the skill's own working state in `~/.report-generator/research_cache/`. Create the
`~/.report-generator/output/<company_slug>/` folder if it doesn't exist yet.

**PDF generation is a mandatory last step of every run (full or incremental,
including a freshness-check-only refresh where the report body is reused
unchanged)** — never skip it and never treat it as optional or user-request-gated.

**All reports use the same visual template — WeasyPrint is not optional-if-convenient,
it is the required renderer.** Every company's PDF must look like every other
company's PDF; a batch of reports rendered through two different pipelines (one
visual, one plain-text ReportLab) reads as broken, not as an acceptable fallback.

**Before building anything, verify WeasyPrint actually works — don't assume from a
prior run or a different session.** Run `python3 -c "import weasyprint"` first. If
that fails, run `pip install weasyprint --break-system-packages` (add `matplotlib`
too if `scripts/charts.py` will be used) and re-check with the same import — do not
proceed past this step on a guess. Only after that second check still fails is the
environment considered genuinely unable to run WeasyPrint.

**Primary path — visual PDF via WeasyPrint (required whenever the above check
passes).** Build the HTML body and render the PDF per `reference/report_assembly.md`
— read it now if this is your first run this session; it has the full
`html_helpers.py` function list, a worked code example, and the exact render
command. The one thing worth restating here: a report built by hand-writing plain
HTML instead of calling those functions will still render through WeasyPrint
without error (the render step has no way to know the content is unstyled), which
is exactly why "the PDF exists and WeasyPrint didn't error" is not sufficient
verification on its own — see the mandatory check below.

**Verify before delivering — run `scripts/verify_report.py`, don't rely on your own
judgment call for this.** Full checklist (what to run, in what order, and why each
check exists) is in `reference/guardrails.md` — read it now if this is your first
run this session. Short version: `html` → render PDF → `pdf` → `report` →
`sources` → `freshness` → `extraction` → `depth`, plus `quotes`/`disclaimer`/
`whitespace`/`ratings`/`announcements`/`social`/`paragraphs` before delivery, and a
visual spot-check via `pdftoppm`. **Any FAIL is a stop-and-fix, not a
note-and-continue.** Delete intermediate chart PNGs and `report.html` only after all
checks pass; only the final PDF and `report.md` belong in
`~/.report-generator/output/<company_slug>/`.

**Legacy fallback — reportlab, text-only. Last resort only, and always flagged.** Use
this ONLY if the verify-then-install check above genuinely failed twice (import error
persists after a fresh `pip install`) — never reach for it just because a build step
errored once; retry the WeasyPrint path before giving up on it. If truly falling
back, see `reference/report_assembly.md`'s "Legacy fallback" note for the exact
command. Never let a missing dependency block delivery entirely; fall back rather
than skip the PDF outright — but **explicitly tell the user in your chat response
(not silently) that this report used the plain-text fallback renderer and why**, so
a mismatched look across a multi-company batch is never a surprise discovered after
the fact. Confirm both `.md` and `.pdf` exist in
`~/.report-generator/output/<company_slug>/` before telling the user the report is
ready, whichever path was used.

Save/update `~/.report-generator/research_cache/<company_slug>/quotes.json`, `bullets.json`,
`guidance_history.json`, `fundraise_history.json`, `rating_history.json`,
`litigation_history.json`, and `report.md`, then mark freshness state per
`reference/step0_perceive.md`'s step 3.
