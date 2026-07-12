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
|   `-- plugin.json                   Plugin manifest (name, version, description)
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

**1. Clone the repo:**

```bash
git clone git@github.com:ajay1297/Research-Advisory.git
cd Research-Advisory
```

**2. Test locally without publishing anywhere:**

```bash
claude --plugin-dir .
```

Use `/reload-plugins` inside a running session to pick up changes without
restarting. Every skill under `skills/` becomes available automatically — no
per-skill registration step. Currently that's `report-generator` (fully
implemented) and `portfolio-analysis` (placeholder, not yet implemented).

**3. Make it load automatically every session** (optional, instead of
passing `--plugin-dir` each time) — symlink this repo into your personal
plugins directory so it keeps updating in place on `git pull`:

```bash
mkdir -p ~/.claude/plugins
ln -s "$(pwd)" ~/.claude/plugins/research-advisory
```

**4. Install dependencies** — see [`skills/report-generator/README.md`](skills/report-generator/README.md#setup)
for the Python/system packages that skill needs (PDF extraction, WeasyPrint
rendering, etc.). Not every skill in this plugin will necessarily share the
same dependencies, so check each skill's own README.

**5. Confirm it installed correctly** — say `research <any company name>`
and check that Claude follows the `report-generator` pipeline end to end,
creating `~/.report-generator/research_cache/<company_slug>/` and
`~/.report-generator/output/<company_slug>/` (outside the plugin entirely —
see Plugin structure above) as it goes.
