# Research-Advisory

A Claude Code plugin bundling research/advisory skills. Install the whole
plugin and every skill inside it becomes available; each skill is
self-contained under `skills/<skill-name>/` with its own `SKILL.md`,
scripts, and reference docs.

**Using a skill never touches the plugin directory itself.** Any working
state a skill builds up as you use it (fetched documents, drafted reports,
generated PDFs) is written to a dedicated folder in your home directory
instead — e.g. `report-generator` writes to `~/.report-generator/`, outside
this repo entirely. Installing, updating, or removing the plugin is
therefore always a clean operation on this directory alone; nothing a skill
does while running ever adds, modifies, or deletes a file here.

## Skills

| Skill | What it does |
|---|---|
| [`report-generator`](skills/report-generator/README.md) | Generates/refreshes India-listed-company research reports (visual PDF + Markdown) from concall transcripts, investor presentations, annual reports, credit-rating rationales, and screener.in/BSE/NSE data. See its own README for the full pipeline, directory structure, and setup. |
| [`portfolio-analysis`](skills/portfolio-analysis/SKILL.md) | **Placeholder — not yet implemented.** Reserved for future portfolio-level analysis/advisory. |

More skills may be added here over time, each in its own `skills/<name>/` directory.

## Plugin structure

```
Research-Advisory/                    (plugin root -- everything here is the plugin)
|-- .claude-plugin/
|   |-- plugin.json                   Plugin manifest (name, version, description)
|   `-- marketplace.json              Marketplace manifest (self-references "." as
|                                       the plugin source -- lets this same repo be
|                                       added via the Add-marketplace UI/CLI)
|-- .gitignore
`-- skills/
    |-- report-generator/             One skill = one self-contained directory
    |   |-- SKILL.md
    |   |-- README.md
    |   |-- reference/
    |   |-- scripts/
    |   |-- assets/
    |   `-- examples/
    `-- portfolio-analysis/           Placeholder -- not yet implemented
        `-- SKILL.md

~/.report-generator/                  (OUTSIDE the plugin, in your home directory)
|-- research_cache/<company_slug>/    Working state, created the first time
|                                      you research a company
`-- output/<company_slug>/            Your local deliverables
                                       (<Company>_report.md/.pdf)
```

Every skill's working state and deliverables are written to its own
dedicated folder under your home directory (`~/.report-generator/` for
`report-generator`) — never inside `skills/<skill-name>/` itself. This
means the plugin directory is 100% reproducible from git: clone it, and
every file in it is exactly what's tracked, with nothing added, changed, or
removed by using the skill.

## Installation

**Install this plugin only through Cowork's own plugin/marketplace
management flow — never by asking Claude to install it for you inside a
regular chat conversation.** Plugin installs change what's available to
every future session, so they belong in Cowork's dedicated setup surface,
not as a side effect of a chat message. If you're in a chat session and want
this plugin, go to Cowork's plugin management (or use the CLI directly
yourself, as below) rather than asking Claude to run the install commands
on your behalf mid-conversation.

This repo is set up as **both** the marketplace catalog and the plugin
itself (self-referencing via `.claude-plugin/marketplace.json`'s
`"source": "."`), so you can install it either through Claude's plugin UI or
straight from the CLI — pick whichever you're using.

### Option A — via the marketplace (Claude Desktop UI or CLI)

**Add the marketplace:**

```bash
claude plugin marketplace add ajay1297/Research-Advisory
```

Or in the Claude Desktop/Code "Add marketplace" dialog, paste the repo URL
exactly as `https://github.com/ajay1297/Research-Advisory.git` (or the
`owner/repo` short form `ajay1297/Research-Advisory`) and press Sync. If you
still see *"no manifest found at .claude-plugin/marketplace.json"*, you're on
an older clone/cache of the repo from before that file existed — make sure
you've pulled the latest commit that adds it.

**Then install the plugin from it:**

```bash
/plugin install research-advisory@research-advisory
```

(or the equivalent option in the plugin picker once the marketplace is added).

### Option B — local dev/testing, no marketplace needed

```bash
git clone git@github.com:ajay1297/Research-Advisory.git
cd Research-Advisory
claude --plugin-dir .
```

Use `/reload-plugins` inside a running session to pick up changes without
restarting — useful while editing the plugin itself. Every skill under
`skills/` becomes available automatically. To make it load every session
without passing `--plugin-dir` each time, symlink the clone into your
personal plugins directory instead:

```bash
mkdir -p ~/.claude/plugins
ln -s "$(pwd)" ~/.claude/plugins/research-advisory
```

### After installing (either option)

Currently `skills/` has `report-generator` (fully implemented) and
`portfolio-analysis` (placeholder, not yet implemented). Install
dependencies (see Setup below), then confirm it installed correctly:

1. Both `research-advisory:report-generator` and `research-advisory:portfolio-analysis`
   should show up by name in the list of available skills in the system prompt
   (visible to Claude every turn once the plugin is installed) — no need to
   invoke anything first, they're just present.
2. Say `research <any company name>` and check that Claude follows the
   `report-generator` pipeline end to end, creating
   `~/.report-generator/research_cache/<company_slug>/` and
   `~/.report-generator/output/<company_slug>/` (outside the plugin entirely —
   see Plugin structure above) as it goes.

## Setup

No API keys or environment variables required for anything in this plugin.
Not every skill necessarily shares the same dependencies — check each
skill's own README for its full setup section; `report-generator`'s is
summarized here since it's the only implemented skill so far.

### `report-generator`

All sourcing is done via web search/fetch (screener.in, BSE/NSE, credit-rating
agency sites) and locally bundled Python 3 scripts — nothing needs a server or
daemon.

**Python packages:**

```bash
pip install pdfplumber weasyprint matplotlib reportlab --break-system-packages
```

| Package | Used by | Required? |
|---|---|---|
| `pdfplumber` | PDF → plain text extraction | Yes, for every source PDF |
| `weasyprint` | Primary visual-PDF renderer | Yes, for the default PDF pipeline |
| `matplotlib` | Chart generation | Only if you ask for a chart version of a section — opt-in, not default |
| `reportlab` | Legacy text-only PDF fallback | Only if WeasyPrint can't be installed |

**System packages** (native libraries WeasyPrint and the PDF-verification step
need — not pip-installable):

```bash
# macOS
brew install pango poppler

# Debian/Ubuntu
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 poppler-utils
```

`poppler` provides `pdftoppm`, used to visually check the rendered PDF (no
clipped tables, no dead whitespace) before delivery — this runs on every
report, not optional.

**Verify the install:**

```bash
python3 -c "import pdfplumber, weasyprint; print('ok')"
pdftoppm -v
```

Full setup detail (known gotchas, the `pdftotext -layout` fallback for
mis-extracted PDFs, directory-creation behavior) lives in
[`skills/report-generator/README.md`](skills/report-generator/README.md#setup).

## Usage

Every skill in this plugin triggers via natural language — no slash command.
Name the company each time; there is no separate "setup a company" step.

### `report-generator`

Four distinct things you can ask for — the phrasing tells Claude which one you mean:

**1. Generate a report for a new company** — full pipeline, first run:

```
research <Company Name>
generate a report on <Company Name>
analyse <Company Name>'s concall
what's the story with <Company/Ticker>
build me a thesis on <Company Name>
```

**2. Update the report for an already-generated company** — the cheap default
path; only refetches what's actually changed since the last run:

```
regenerate <Company Name>'s report
refresh <Company Name>'s report
update <Company Name>'s report
```

**3. Re-generate the report from scratch for an already-generated company** —
explicitly bypasses the cache and refetches/rebuilds everything (tracker
histories like guidance/fundraise/rating/litigation are cumulative records and
are never wiped, from-scratch or not):

```
regenerate <Company Name>'s report from scratch
rebuild <Company Name> from scratch
redo <Company Name>'s report from scratch
ignore the cache and redo <Company Name>
```

**4. Invoking without a company name** — Claude won't guess or silently reuse
a company from earlier in the conversation; it asks which company you mean
before doing anything else.

Also: `rerun for <Company A> and <Company B>` processes multiple companies
independently in one request, and uploading a concall transcript, investor
presentation, or annual report PDF directly also triggers the skill,
preferring the uploaded document over fetching one.

Every run ends with both `~/.report-generator/output/<company_slug>/<Company>_report.md`
and `~/.report-generator/output/<company_slug>/<Company>_report.pdf` — PDF export
is automatic, never a separate ask. Full detail (architecture, end-to-end
flow diagram, section-by-section source mapping) lives in
[`skills/report-generator/README.md`](skills/report-generator/README.md#usage).

#### Pipeline steps and the files each one touches

The pipeline runs as four steps, each owned by its own file under
`skills/report-generator/reference/`. Files with no extension shown are
`.md`; `.py` files live in `skills/report-generator/scripts/`; JSON/HTML/PDF
files live under `~/.report-generator/` (`research_cache/<slug>/` or
`output/<slug>/`, as noted in Setup above).

| Step | Step file | Reference docs it reads | Scripts it invokes | Data files it reads/writes |
|---|---|---|---|---|
| 0 — Perceive (freshness check) | `step0_perceive.md` | `data_sources.md`, `sourcing_depth.md`, `SKILL.md`, `step1_retrieve.md` | `check_freshness.py`, `forward_pe.py`, `guidance_tracker.py` | `state.json`, `report.md`, `bullets.json`, `guidance_history.json` |
| 1 — Retrieve (fetch + extract) | `step1_retrieve.md` | `data_sources.md`, `step0_perceive.md`, `step3_memorize.md` | `pdf_to_text.py`, `pdf_to_text_parallel.py`, `extract_theme_quotes.py` | `sources/<slug>/`, `candidate_quotes/*.json`, `quotes.json` |
| 2 — Synthesize (draft sections) | `step2_synthesize.md` | `step0_perceive.md`, `report_format.md`, `report_sections.md`, `source_playbook.md` | `guidance_tracker.py`, `capacity_utilization.py`, `forward_pe.py`, `fundraise_tracker.py`, `rating_tracker.py`, `litigation_tracker.py` | `quotes.json`, `guidance_history.json`, `fundraise_history.json`, `rating_history.json`, `litigation_history.json` |
| 3 — Memorize (save + verify) | `step3_memorize.md` | `step0_perceive.md`, `report_assembly.md`, `guardrails.md` | `html_helpers.py`, `charts.py`, `verify_report.py`, `report_to_pdf.py`, `check_freshness.py` | `report.html`, `*_report.pdf`, `report.md`, `quotes.json`, `bullets.json`, 4 tracker histories (guidance/fundraise/rating/litigation), `state.json` |

Two cross-cutting files every step reads but none of them "owns":
`reference/rules_and_validation.md` (standing constraints — token
discipline, never-drop-anything-silently, accuracy discipline) and
`reference/guardrails.md` (the `verify_report.py` checklist reference).
Step 3's Memorize is also where the loop closes: `check_freshness.py
--mark-processed` writes `state.json`, which the *next* run's Step 0/Perceive
reads back to decide how much of the pipeline actually needs to re-run.
