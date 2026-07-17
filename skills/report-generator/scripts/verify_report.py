#!/usr/bin/env python3
"""
verify_report.py — deterministic pre-delivery checks for a report-generator run.

Every check here replaces a judgment call that has previously failed silently in
practice: an HTML report built by hand instead of through html_helpers.py's
functions still renders through WeasyPrint without error, a partial-page annual
report extraction still "succeeds," a broker PDF's facts can be silently dropped
during drafting, a run can finish without ever calling --mark-processed. None of
these are caught by "the PDF exists" or "the script didn't error." This script
greps/counts the actual artifacts on disk instead of trusting a self-report.

Run the relevant subcommand(s) before declaring a report done — see
reference/guardrails.md for when each one applies. Exits non-zero and
prints FAIL lines if a required check doesn't pass; exits 0 with PASS lines
otherwise. A FAIL is a stop-and-fix, not a note-and-continue.

Organized into three tiers (see reference/guardrails.md for the full rationale of each):

--- 1. INPUT GUARDRAILS (the gatekeepers — run before real processing starts) ---

    python3 verify_report.py sniff <file.pdf>
        Classifies an uploaded PDF's likely type (annual report / concall
        transcript / investor presentation / broker research report / unknown)
        from keyword signals in its first two pages, via `pdftotext`. Catches a
        file being routed into the wrong pipeline branch (e.g. a broker PDF
        processed as if it were an annual report) before that mistake compounds.

    python3 verify_report.py slug <company_slug>
        Validates a company slug is safe to use in filesystem paths under
        ~/.report-generator/ — lowercase letters, digits, and underscores only.
        Catches a malformed/unsanitized slug before it's used to construct paths.

    python3 verify_report.py links
        Not a per-report check — a self-integrity check on this skill's own docs
        (SKILL.md + reference/*.md), via check_reference_links.py. Catches a
        dangling cross-reference left behind after a reference file gets split,
        renamed, or has a heading moved (the exact bug class found repeatedly by
        hand before this check existed). No arguments — always checks this
        skill's own install directory. Run this once per session if you edited
        any reference/*.md or SKILL.md file, not once per report.

--- 2. EXECUTION GUARDRAILS (the boundaries — run during/immediately after a run) ---

    python3 verify_report.py scope <plugin_skill_dir> [--minutes 120]
        Confirms no file under the skill's own install directory was created or
        modified in the last N minutes (default 120). Catches an agent writing
        inside skills/report-generator/ itself instead of ~/.report-generator/,
        which the skill's own rules explicitly forbid.

    python3 verify_report.py reproduction <source.txt> <report.md> [--ngram 12]
        Checks that no N-consecutive-word sequence (default 12) from a broker/
        agency source document appears verbatim in the drafted report. Catches
        over-quoting a source whose own disclaimer restricts reproduction —
        paraphrase is required, not verbatim copying at length.

--- 3. OUTPUT GUARDRAILS (the filters — run right before delivery) ---

    python3 verify_report.py html <report.html>
        Run BEFORE deleting report.html / after generating it, before rendering
        the PDF. Checks that the required html_helpers.py CSS markers are present.

    python3 verify_report.py pdf <report.pdf>
        Run AFTER rendering. Checks the PDF producer (flags a silent ReportLab
        fallback) and that it has a sane page count.

    python3 verify_report.py report <report.md> [--brokers TAG1,TAG2,...]
        Checks report.md has all required canonical section headers, and that
        every broker tag you pass actually appears at least once (catches a
        broker PDF whose facts got silently dropped during drafting).

    python3 verify_report.py quotes <report.md> <sources_dir>
        Extracts every double-quoted string from the Near/Medium/Long Term
        outlook sections and checks each is an exact substring of at least one
        .txt file in sources_dir. Catches a fabricated or subtly-altered quote —
        the report_format.md rule that "every quote is verbatim" enforced
        mechanically instead of by review alone.

    python3 verify_report.py disclaimer <report.md>
        Checks the report ends with the required "not investment advice"
        disclaimer boilerplate.

    python3 verify_report.py sources <company_slug>
        Checks the sources/ vs research_cache/ split wasn't violated (no bulky
        .pdf/.txt/.bm25.pkl leaked into research_cache/, no candidate-quotes JSON
        left loose in sources/ instead of research_cache/candidate_quotes/).

    python3 verify_report.py freshness <company_slug>
        Checks state.json's last_processed_at is today's date (catches a run
        that finished without ever calling check_freshness.py --mark-processed).

    python3 verify_report.py extraction <source.pdf> <extracted.txt>
        Checks the extracted text actually covers page 1 through the PDF's last
        page (catches a silent partial-range extraction — e.g. starting at page
        40 instead of page 1 because a scouting range was mistaken for the full
        extraction).

    python3 verify_report.py depth <company_slug>
        Counts concall and annual-report .txt files actually present in
        sources/<company_slug>/ and compares against the standard sourcing depth
        (6 quarters of concalls, 2 annual reports). WARNs (not a hard FAIL) if
        short, since a newly-listed company can legitimately not have 6 quarters
        of history yet — but the shortfall must then be stated explicitly in the
        report, not silently delivered as if the standard depth was met.
"""
import sys
import os
import re
import json
import subprocess
import argparse
from datetime import datetime, timezone

REQUIRED_REPORT_SECTIONS = [
    "Value Chain Positioning",
    "Situation Classification",
    "Near Term",
    "Medium Term",
    "Long Term",
    "Marquee & Niche Customers",
    "Capex, Milestones & Certifications Timeline",
    "Financial Performance Summary",
    "Manufacturing Locations & Physical Assets",
    "Capacity Utilization & Headroom",
    "Valuation",
    "Industry Tailwinds",
    "MOATs",
    "Technical Snapshot",
    "Promoter",
    "Investment Thesis Summary",
    "Key Risks",
    "Verdict",
    "Sources",
]

# CSS classes only html_helpers.py's functions emit — a hand-written HTML report
# will be missing these even though it renders fine through WeasyPrint.
REQUIRED_HTML_MARKERS = {
    "cover": 'class="cover"',
    "card-grid (headline stats)": 'class="card-grid"',
    "flow-diagram (Value Chain box)": 'class="flow-diagram"',
    "flow-box (individual stage box)": 'class="flow-box"',
    "data table (data_table())": 'class="data"',
    "timeline (Capex/Milestones)": 'class="timeline"',
    "flags (bullet lists, MOATs/Thesis/Risks)": 'class="flags',
    "verdict-box": 'class="verdict-box"',
}


def check_html(path):
    print(f"=== html check: {path} ===")
    if not os.path.exists(path):
        print(f"FAIL: {path} does not exist")
        return False
    with open(path, "r", errors="ignore") as f:
        content = f.read()

    ok = True
    for label, marker in REQUIRED_HTML_MARKERS.items():
        count = content.count(marker)
        if count == 0:
            print(f"FAIL: missing {marker!r} ({label}) — this section of the report "
                  f"was likely hand-written instead of built through html_helpers.py")
            ok = False
        else:
            print(f"PASS: {marker!r} found ({count}x) — {label}")
    return ok


def check_pdf(path):
    print(f"=== pdf check: {path} ===")
    if not os.path.exists(path):
        print(f"FAIL: {path} does not exist")
        return False
    try:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"FAIL: could not run pdfinfo on {path}: {e}")
        return False

    ok = True
    producer_match = re.search(r"^Producer:\s*(.+)$", out, re.MULTILINE)
    producer = producer_match.group(1).strip() if producer_match else "(unknown)"
    if "WeasyPrint" in producer:
        print(f"PASS: Producer is {producer} (primary visual pipeline)")
    elif "ReportLab" in producer:
        print(f"WARN: Producer is {producer} — this is the legacy text-only "
              f"fallback. This is only acceptable if WeasyPrint genuinely failed "
              f"twice (see reference/step3_memorize.md), AND you must state this explicitly in your "
              f"chat response to the user — never let this pass silently.")
        # Not a hard FAIL — ReportLab is an allowed fallback — but it must be
        # surfaced, so callers should treat WARN as requiring explicit disclosure.
    else:
        print(f"FAIL: unrecognized Producer {producer!r} — verify this is a real "
              f"report PDF, not an empty/corrupt file")
        ok = False

    pages_match = re.search(r"^Pages:\s*(\d+)$", out, re.MULTILINE)
    pages = int(pages_match.group(1)) if pages_match else 0
    if pages < 3:
        print(f"FAIL: only {pages} page(s) — a real report is never this short; "
              f"likely a broken/empty render")
        ok = False
    else:
        print(f"PASS: {pages} pages")

    return ok


def check_report(path, broker_tags):
    print(f"=== report.md check: {path} ===")
    if not os.path.exists(path):
        print(f"FAIL: {path} does not exist")
        return False
    with open(path, "r", errors="ignore") as f:
        content = f.read()

    ok = True
    for section in REQUIRED_REPORT_SECTIONS:
        if section.lower() not in content.lower():
            print(f"FAIL: no heading/mention matching {section!r} found — either "
                  f"missing entirely or this section wasn't drafted")
            ok = False
        else:
            print(f"PASS: {section!r} present")

    if broker_tags:
        for tag in broker_tags:
            tag = tag.strip()
            if not tag:
                continue
            pattern = f"[{tag}]"
            count = content.count(pattern)
            if count == 0:
                print(f"FAIL: broker tag {pattern!r} never appears — this broker "
                      f"report's facts were silently dropped during drafting, "
                      f"go back and actually fold them in")
                ok = False
            else:
                print(f"PASS: {pattern!r} appears {count}x")

    return ok


def check_sources(slug):
    base = os.path.expanduser("~/.report-generator")
    sources_dir = os.path.join(base, "sources", slug)
    cache_dir = os.path.join(base, "research_cache", slug)
    print(f"=== sources/research_cache split check: {slug} ===")

    ok = True

    # research_cache/ should never contain bulky raw material
    if os.path.isdir(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            # candidate_quotes/ subfolder is expected and fine
            for fname in files:
                if fname.endswith((".pdf", ".txt", ".bm25.pkl")):
                    full = os.path.join(root, fname)
                    print(f"FAIL: bulky raw file leaked into research_cache/: {full} "
                          f"— should be in sources/{slug}/ instead")
                    ok = False
    else:
        print(f"WARN: {cache_dir} does not exist")

    # sources/ should never have loose candidate-quotes JSON (should be moved to
    # research_cache/<slug>/candidate_quotes/)
    if os.path.isdir(sources_dir):
        for fname in os.listdir(sources_dir):
            full = os.path.join(sources_dir, fname)
            if os.path.isfile(full) and ("candidate_quotes" in fname or
                                          (fname.startswith("quotes_") and fname.endswith(".json"))):
                print(f"FAIL: candidate-quotes JSON left loose in sources/: {full} "
                      f"— should be in research_cache/{slug}/candidate_quotes/ instead "
                      f"(it's small, not bulky raw material)")
                ok = False

    if ok:
        print(f"PASS: no split violations found")
    return ok


def check_freshness(slug):
    base = os.path.expanduser("~/.report-generator")
    state_path = os.path.join(base, "research_cache", slug, "state.json")
    print(f"=== freshness check: {slug} ===")

    if not os.path.exists(state_path):
        print(f"FAIL: {state_path} does not exist — check_freshness.py "
              f"--mark-processed was never called for this run")
        return False

    with open(state_path) as f:
        state = json.load(f)

    ts = state.get("last_processed_at")
    if not ts:
        print(f"FAIL: state.json has no last_processed_at field")
        return False

    try:
        processed_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        print(f"FAIL: could not parse last_processed_at={ts!r}")
        return False

    today = datetime.now(timezone.utc).date()
    if processed_dt.date() != today:
        print(f"FAIL: last_processed_at={ts} is not today ({today}) — "
              f"--mark-processed likely wasn't called at the end of this run")
        return False

    print(f"PASS: last_processed_at={ts} is today")
    return True


def check_extraction(pdf_path, txt_path):
    print(f"=== extraction coverage check: {txt_path} against {pdf_path} ===")
    if not os.path.exists(pdf_path):
        print(f"FAIL: {pdf_path} does not exist")
        return False
    if not os.path.exists(txt_path):
        print(f"FAIL: {txt_path} does not exist")
        return False

    try:
        out = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"FAIL: could not run pdfinfo on {pdf_path}: {e}")
        return False

    pages_match = re.search(r"^Pages:\s*(\d+)$", out, re.MULTILINE)
    if not pages_match:
        print(f"FAIL: could not determine page count of {pdf_path}")
        return False
    total_pages = int(pages_match.group(1))

    with open(txt_path, "r", errors="ignore") as f:
        content = f.read()

    ok = True
    if f"--- PAGE 1 ---" not in content:
        print(f"FAIL: extracted text does not contain 'PAGE 1' — extraction did "
              f"not start at the beginning of the document (a partial/scouting "
              f"range was likely mistaken for the full extraction)")
        ok = False
    else:
        print(f"PASS: extraction starts at page 1")

    if f"--- PAGE {total_pages} ---" not in content:
        print(f"FAIL: extracted text does not contain 'PAGE {total_pages}' "
              f"(the source PDF's last page) — extraction did not reach the end "
              f"of the {total_pages}-page document")
        ok = False
    else:
        print(f"PASS: extraction reaches the final page ({total_pages})")

    return ok


def _load_manifest_counts(slug):
    """Returns (concall_count, ip_count, ar_doc_count, press_release_count,
    had_manifest) from source_manifest.json, so check_depth still works after
    sources/ has been deleted — see source_manifest.py's docstring for why this
    file exists."""
    base = os.path.expanduser("~/.report-generator")
    manifest_path = os.path.join(base, "research_cache", slug, "source_manifest.json")
    if not os.path.exists(manifest_path):
        return 0, 0, 0, 0, False
    with open(manifest_path) as f:
        data = json.load(f)
    docs = data.get("documents", [])
    concalls = sum(1 for d in docs if d.get("type") == "concall")
    ips = sum(1 for d in docs if d.get("type") == "investor_presentation")
    press_releases = sum(1 for d in docs if d.get("type") == "press_release")
    # Annual reports: count distinct labels (e.g. "FY2024-25"), not documents —
    # a manifest entry per chunk would otherwise over-count the same document,
    # same reasoning as the directory-scan de-duplication below.
    ar_labels = {d.get("label") for d in docs if d.get("type") == "annual_report"}
    return concalls, ips, len(ar_labels), press_releases, True


def check_depth(slug):
    base = os.path.expanduser("~/.report-generator")
    sources_dir = os.path.join(base, "sources", slug)
    print(f"=== standard sourcing depth check: {slug} ===")

    manifest_concalls, manifest_ips, manifest_ars, manifest_prs, had_manifest = _load_manifest_counts(slug)

    if not os.path.isdir(sources_dir):
        if had_manifest:
            print(f"NOTE: {sources_dir} does not exist (deleted after processing, "
                  f"per the sources/research_cache split) — falling back entirely "
                  f"to source_manifest.json in research_cache/, which survives "
                  f"deletion. Counts below are metadata-only; nothing here re-reads "
                  f"actual document content (that's what verify_report.py quotes "
                  f"needs sources/ for specifically, and can't be recovered this way).")
            concall_files = [None] * manifest_concalls
            ip_files = [None] * manifest_ips
            pr_files = [None] * manifest_prs
            ar_doc_keys = set(range(manifest_ars))
            ar_files_raw = list(ar_doc_keys)  # count-only, no real filenames once sources/ is gone
            ar_from_manifest = True
        else:
            print(f"FAIL: {sources_dir} does not exist and no source_manifest.json "
                  f"was found in research_cache/{slug}/ either — sourcing depth "
                  f"cannot be verified at all. If sources/ was deliberately "
                  f"deleted, this company's runs predate source_manifest.json "
                  f"logging; nothing to do about that retroactively, but log to "
                  f"the manifest from now on.")
            return False
    else:
        files = os.listdir(sources_dir)
        # Require "concall" explicitly in the filename — the looser "q[1-4]fy\d{2}"
        # fallback pattern also matches non-concall documents that happen to be
        # named for the same quarter (e.g. "Investor-Earnings-Presentation-
        # Q4FY26.txt", "Financial-Results-Q4FY26.txt"), inflating the count with
        # false positives. This assumes the project's own naming convention
        # (every real concall extraction includes "concall" in its filename) — if
        # that convention is ever broken, this check under-counts rather than
        # over-counts, which is the safer failure direction for a depth check.
        concall_files = [f for f in files if f.endswith(".txt") and
                          re.search(r"(?i)concall", f)]
        # Same explicit-naming discipline as concalls — require "presentation" or
        # "ir_deck" style naming rather than a loose quarter-pattern match, for
        # the same false-positive reason.
        ip_files = [f for f in files if f.endswith(".txt") and
                    re.search(r"(?i)presentation|investor.?deck|ir.?deck", f)]
        # Same explicit-naming discipline again — require "press" or "pr_"/"pr-"
        # style naming rather than a loose quarter-pattern match.
        pr_files = [f for f in files if f.endswith(".txt") and
                    re.search(r"(?i)press.?release|\bpr[_-]", f)]

        # Annual reports are sometimes saved as one file per fiscal year
        # (AR_FY2020-21.txt) and sometimes as multiple page-range chunks of the
        # SAME document (ar_40_90.txt, ar_90_140.txt, ...) when
        # pdf_to_text_parallel.py or a manual range-split was used. Counting raw
        # files over-counts a single chunked document as if it were several
        # distinct years. Group by a normalized document key instead: strip any
        # trailing "_<digits>_<digits>" chunk-range suffix before counting, so
        # chunks of one document collapse to one entry.
        ar_files_raw = [f for f in files if f.endswith(".txt") and
                         re.search(r"(?i)\bar[_-]|annual.?report", f)]
        ar_doc_keys = set()
        for f in ar_files_raw:
            key = re.sub(r"_\d+_\d+\.txt$", "", f, flags=re.IGNORECASE)
            ar_doc_keys.add(key.lower())

        # Merge with the manifest by taking the max on each count — either source
        # could be the more complete one (files could exist without ever being
        # logged to the manifest if it predates source_manifest.json; the
        # manifest could know about documents already deleted from disk).
        ar_from_manifest = False
        if had_manifest:
            if manifest_concalls > len(concall_files):
                concall_files = [None] * manifest_concalls
            if manifest_ips > len(ip_files):
                ip_files = [None] * manifest_ips
            if manifest_prs > len(pr_files):
                pr_files = [None] * manifest_prs
            if manifest_ars > len(ar_doc_keys):
                ar_doc_keys = set(range(manifest_ars))
                ar_from_manifest = True

    def _detail(items):
        # Real filenames if we scanned a directory; a count-only note if this
        # came from the manifest after sources/ was deleted (items are `None`
        # placeholders, not real filenames — printing them would be noise).
        if items and items[0] is None:
            return f"(from source_manifest.json only, sources/ not on disk)"
        return f"({items})"

    ok = True
    if len(concall_files) < 6:
        print(f"WARN: only {len(concall_files)} concall transcript(s) found "
              f"{_detail(concall_files)} — standard depth is 6 quarters. This is "
              f"only acceptable if the company genuinely doesn't have 6 quarters "
              f"of history (recently listed, etc.) — and that reason must then be "
              f"stated explicitly in the report, not left unexplained.")
    else:
        print(f"PASS: {len(concall_files)} concall transcripts found")

    if len(ip_files) < 6:
        print(f"WARN: only {len(ip_files)} investor presentation(s) found "
              f"{_detail(ip_files)} — standard depth is 6 quarters, same as "
              f"concalls. The investor presentation is frequently the only source "
              f"for segment-wise revenue, exports/geography split, and TAM — a "
              f"report missing these isn't just thinner, it can be factually "
              f"wrong (e.g. claiming no TAM was disclosed when the presentation "
              f"had one). Only acceptable with a stated reason (company doesn't "
              f"publish one every quarter, etc.).")
    else:
        print(f"PASS: {len(ip_files)} investor presentations found")

    if len(pr_files) < 6:
        print(f"WARN: only {len(pr_files)} press release(s) found "
              f"{_detail(pr_files)} — standard depth is 6 quarters, same as "
              f"concalls. A press release routinely states a standalone-quarter "
              f"figure or a dividend/exceptional-item detail that a secondary "
              f"results-coverage aggregator can drop or garble (see "
              f"reference/sourcing_depth.md's 'Press releases' section) — a "
              f"report relying only on secondary coverage here isn't just "
              f"thinner, it can miss a materially different standalone-quarter "
              f"result. Only acceptable with a stated reason (company doesn't "
              f"issue a separate press release, etc.).")
    else:
        print(f"PASS: {len(pr_files)} press releases found")

    ar_source_note = (f"from source_manifest.json (topped up beyond what's on disk)"
                       if ar_from_manifest
                       else f"from {len(ar_files_raw)} file(s) on disk")
    if len(ar_doc_keys) < 2:
        print(f"WARN: only {len(ar_doc_keys)} distinct annual report(s) found "
              f"({ar_source_note} — chunked page-range extractions of the same "
              f"document are counted once, not per-chunk) — standard depth is 2 "
              f"annual reports (distinct fiscal years). Same caveat as above: "
              f"only acceptable with a stated reason.")
    else:
        print(f"PASS: {len(ar_doc_keys)} distinct annual reports found "
              f"({ar_source_note})")

    # WARN-only checks don't fail the run — they require a stated reason in the
    # report, not a blocked pipeline (see docstring).
    return ok


# --- 1. INPUT GUARDRAILS ----------------------------------------------------

DOC_TYPE_SIGNALS = {
    "annual report": ["annual report", "board of directors", "director's report",
                       "directors' report", "corporate governance report",
                       "statutory reports", "notice of annual general meeting"],
    "concall transcript": ["conference call", "transcript", "moderator", "q&a session",
                            "earnings call", "management commentary"],
    "investor presentation": ["investor presentation", "investor deck", "q1 fy",
                               "q2 fy", "q3 fy", "q4 fy", "disclaimer: this presentation"],
    "broker/agency research report": ["institutional equities", "target price",
                                       "rating: buy", "rating buy", "12 month price target",
                                       "initiating coverage", "result update", "visit note",
                                       "sebi registration", "research analyst"],
}


def check_sniff(pdf_path):
    print(f"=== input sniff: {pdf_path} ===")
    if not os.path.exists(pdf_path):
        print(f"FAIL: {pdf_path} does not exist")
        return False

    try:
        out = subprocess.run(["pdftotext", "-f", "1", "-l", "2", pdf_path, "-"],
                              capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"FAIL: could not run pdftotext on {pdf_path}: {e}")
        return False

    lower = out.lower()
    scores = {doc_type: sum(1 for kw in kws if kw in lower)
              for doc_type, kws in DOC_TYPE_SIGNALS.items()}
    best_type, best_score = max(scores.items(), key=lambda kv: kv[1])

    if best_score == 0:
        print(f"WARN: no recognizable signal for any known document type in the "
              f"first 2 pages — confirm manually what this file actually is before "
              f"routing it into a section-specific pipeline")
        return True  # not a hard fail — some legitimate docs just don't match; but WARN so it gets a human look

    print(f"PASS: looks like a {best_type!r} (score {best_score}, all scores: {scores})")
    return True


def check_slug(slug):
    print(f"=== slug safety check: {slug!r} ===")
    if re.fullmatch(r"[a-z0-9_]+", slug):
        print(f"PASS: slug is safe for filesystem paths")
        return True
    print(f"FAIL: slug contains characters outside [a-z0-9_] — unsafe to use in "
          f"~/.report-generator/ paths as-is; normalize it (lowercase, underscores) "
          f"before using it anywhere")
    return False


def check_links():
    print("=== reference-link integrity check (this skill's own docs) ===")
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_reference_links
    findings = check_reference_links.check(skill_dir)
    if not findings:
        print("PASS: no dangling reference-file or heading pointers found.")
        return True

    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    for severity, name, msg in findings:
        print(f"{severity}: [{name}] {msg}")
    print(f"{len(fails)} FAIL, {len(warns)} WARN.")
    if fails:
        return False
    print("PASS: only WARNs (informational) — review them, not a blocker on their own")
    return True


# --- 2. EXECUTION GUARDRAILS ------------------------------------------------

def check_scope(plugin_dir, minutes):
    import time
    print(f"=== plugin write-scope check: {plugin_dir} (last {minutes} min) ===")
    if not os.path.isdir(plugin_dir):
        print(f"FAIL: {plugin_dir} does not exist")
        return False

    cutoff = time.time() - minutes * 60
    recent = []
    for root, dirs, files in os.walk(plugin_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".git")]
        for fname in files:
            if fname == "__pycache__" or fname.endswith(".pyc"):
                continue
            full = os.path.join(root, fname)
            try:
                if os.path.getmtime(full) > cutoff:
                    recent.append(full)
            except OSError:
                continue

    if recent:
        print(f"FAIL: {len(recent)} file(s) under the plugin's own install "
              f"directory were modified in the last {minutes} minutes — this "
              f"skill must never write inside its own directory, only under "
              f"~/.report-generator/. Recently modified: {recent}")
        return False

    print(f"PASS: no recent writes inside the plugin's own directory")
    return True


def _word_ngrams(text, n):
    words = re.findall(r"\S+", text.lower())
    for i in range(len(words) - n + 1):
        yield " ".join(words[i:i + n])


def check_reproduction(source_path, report_path, ngram):
    print(f"=== reproduction-length check: {source_path} vs {report_path} (n={ngram}) ===")
    if not os.path.exists(source_path):
        print(f"FAIL: {source_path} does not exist")
        return False
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False

    with open(source_path, "r", errors="ignore") as f:
        source_text = f.read()
    with open(report_path, "r", errors="ignore") as f:
        report_text = f.read()

    source_ngrams = set(_word_ngrams(source_text, ngram))
    report_ngrams = set(_word_ngrams(report_text, ngram))
    overlap = source_ngrams & report_ngrams

    if overlap:
        example = next(iter(overlap))
        print(f"FAIL: {len(overlap)} {ngram}-word sequence(s) copied verbatim from "
              f"the source into the report — e.g. {example!r}. Paraphrase this "
              f"content instead; the source's own disclaimer restricts "
              f"reproduction at length.")
        return False

    print(f"PASS: no {ngram}-word verbatim sequences found copied from source")
    return True


# --- 3. OUTPUT GUARDRAILS (in addition to html/pdf/report/sources/freshness/
#        extraction/depth above) ---------------------------------------------

def check_quotes(report_path, sources_dir):
    print(f"=== quote-fabrication check: {report_path} against {sources_dir} ===")
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False
    if not os.path.isdir(sources_dir):
        print(f"FAIL: {sources_dir} does not exist")
        return False

    with open(report_path, "r", errors="ignore") as f:
        report_text = f.read()

    # Scope to the outlook sections only, per report_format.md's verbatim-quote rule.
    # Find "## Near Term", then the next "## " heading that isn't Medium/Long Term
    # (i.e. the first section after the outlook block), and take everything between.
    start = report_text.find("## Near Term")
    if start == -1:
        print("WARN: could not locate Near Term section to check")
        return True

    next_heading = None
    for m in re.finditer(r"\n## ", report_text[start + 1:]):
        heading_line = report_text[start + 1 + m.end(): start + 1 + m.end() + 60]
        if not heading_line.startswith(("Medium Term", "Long Term")):
            next_heading = start + 1 + m.start()
            break
    outlook_text = report_text[start:next_heading] if next_heading else report_text[start:]

    quoted_strings = re.findall(r'"([^"]{15,})"', outlook_text)
    if not quoted_strings:
        print("WARN: no quoted strings found in the outlook sections to check")
        return True

    def normalize(s):
        # PDF extraction wraps lines mid-sentence (e.g. "INR 7,687\ncrores"); a
        # verbatim quote's substance is unaffected by where the source PDF
        # happened to wrap a line, so collapse all whitespace runs (including
        # newlines) to a single space before comparing — this is about ignoring
        # incidental PDF line-wrap artifacts, not about tolerating a genuinely
        # paraphrased or altered quote.
        return re.sub(r"\s+", " ", s).strip()

    all_source_text = ""
    for fname in os.listdir(sources_dir):
        if fname.endswith(".txt"):
            with open(os.path.join(sources_dir, fname), "r", errors="ignore") as f:
                all_source_text += f.read() + "\n"
    normalized_source = normalize(all_source_text)

    ok = True
    for q in quoted_strings:
        if normalize(q) not in normalized_source:
            print(f"FAIL: quoted string not found verbatim in any source .txt "
                  f"(whitespace-normalized): {q!r}")
            ok = False
    if ok:
        print(f"PASS: all {len(quoted_strings)} quoted string(s) verified verbatim against sources")
    return ok


def check_disclaimer(report_path):
    print(f"=== disclaimer check: {report_path} ===")
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False
    with open(report_path, "r", errors="ignore") as f:
        content = f.read().lower()

    if "not investment advice" in content or "not a distributed advisory" in content:
        print("PASS: disclaimer language found")
        return True
    print("FAIL: no 'not investment advice' style disclaimer found — required per "
          "reference/rules_and_validation.md's Accuracy discipline")
    return False


def check_whitespace(pdf_path, ratio=0.5):
    print(f"=== dead-whitespace check: {pdf_path} (interior page threshold: "
          f"{ratio:.0%} of median) ===")
    if not os.path.exists(pdf_path):
        print(f"FAIL: {pdf_path} does not exist")
        return False

    try:
        info = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"FAIL: could not run pdfinfo on {pdf_path}: {e}")
        return False

    pages_match = re.search(r"^Pages:\s*(\d+)$", info, re.MULTILINE)
    if not pages_match:
        print("FAIL: could not determine page count")
        return False
    total_pages = int(pages_match.group(1))

    if total_pages < 4:
        print(f"WARN: only {total_pages} pages — too short to meaningfully check "
              f"interior-page density, skipping")
        return True

    word_counts = {}
    for p in range(1, total_pages + 1):
        try:
            out = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf_path, "-"],
                                  capture_output=True, text=True, check=True).stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"FAIL: could not run pdftotext on page {p}: {e}")
            return False
        word_counts[p] = len(out.split())

    # Only page 1 (the cover) is unconditionally exempt. The last page is allowed
    # to taper off (e.g. a short trailing Sources entry) but NOT to be near-blank —
    # a one-line overflow onto an otherwise-empty final page is exactly the kind of
    # dead space this check exists to catch, just as much as an interior gap. Give
    # it a lower bar than interior pages (last_page_ratio) rather than a full pass.
    interior_pages = {p: wc for p, wc in word_counts.items() if p not in (1, total_pages)}
    if not interior_pages:
        print("WARN: no interior pages to check (document is only cover + one content page)")
        return True

    sorted_counts = sorted(interior_pages.values())
    median = sorted_counts[len(sorted_counts) // 2]
    threshold = median * ratio
    last_page_threshold = median * min(ratio, 0.15)

    ok = True
    for p, wc in interior_pages.items():
        if wc < threshold:
            print(f"FAIL: page {p} has {wc} words, well below the interior-page "
                  f"median of {median} ({wc/median:.0%} of median, threshold "
                  f"{ratio:.0%}) — likely dead whitespace from a forced page_break() "
                  f"or a section wrongly kept-together across a boundary. Only the "
                  f"cover page (page 1) is allowed to be sparse.")
            ok = False

    last_wc = word_counts[total_pages]
    if last_wc < last_page_threshold:
        print(f"FAIL: last page ({total_pages}) has only {last_wc} words "
              f"({last_wc/median:.0%} of the interior median {median}) — a near-blank "
              f"final page from a small content overflow is still dead space; tighten "
              f"spacing or shift content so it doesn't spill a line or two onto an "
              f"otherwise-empty page. Only page 1 (the cover) is allowed to be this sparse.")
        ok = False

    if ok:
        print(f"PASS: all {len(interior_pages)} interior page(s) reasonably filled "
              f"(median {median} words; cover={word_counts[1]}, "
              f"last page={last_wc}, {last_wc/median:.0%} of median)")
    return ok


def check_ratings_recency(slug, months=6):
    base = os.path.expanduser("~/.report-generator")
    path = os.path.join(base, "research_cache", slug, "rating_history.json")
    print(f"=== rating-check recency: {slug} (expect a check within the last "
          f"{months} months) ===")

    if not os.path.exists(path):
        print(f"WARN: {path} does not exist — no rating check was ever logged for "
              f"this company. If genuinely no agency covers it, that must be stated "
              f"explicitly in the report; if it just hasn't been checked, check now.")
        return True

    with open(path) as f:
        history = json.load(f)

    if isinstance(history, list):
        entries = history
    else:
        entries = history.get("ratings") or history.get("entries") or []
    if not entries:
        print("WARN: rating_history.json exists but has no entries — same caveat "
              "as above: state explicitly whether this means 'unrated' or "
              "'not yet checked.'")
        return True

    date_fields = ("date", "rationale_date", "action_date", "logged_at")
    latest = None
    for e in entries:
        for field in date_fields:
            if field in e:
                try:
                    d = datetime.fromisoformat(str(e[field]).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if latest is None or d > latest:
                    latest = d
                break

    if latest is None:
        print("WARN: could not find a parseable date field in rating_history.json "
              "entries — cannot confirm recency mechanically, verify manually")
        return True

    now = datetime.now(timezone.utc) if latest.tzinfo else datetime.now()
    age_days = (now - latest).days
    if age_days > months * 30:
        print(f"WARN: most recent logged rating entry is {latest.date()} "
              f"({age_days} days old, > {months} months) — this does NOT mean the "
              f"rating changed, but it does mean a fresh check for the last "
              f"{months} months genuinely needs to happen this run rather than "
              f"reusing this cached entry silently. Confirm you actively re-checked "
              f"each covering agency's site this run, not just read this file.")
    else:
        print(f"PASS: most recent logged rating entry is {latest.date()} "
              f"({age_days} days old, within {months} months)")
    return True  # informational WARN only — never blocks delivery on its own


def check_announcements(slug, months=6):
    """Checks source_manifest.json for a logged 'announcement_sweep' entry within
    the last N months — mirrors check_ratings_recency's pattern, but per
    reference/guardrails.md this check FAILs (not WARNs) if the sweep was never
    logged, has no evidence, or was logged as an explicit --status skipped. Log a
    sweep via `source_manifest.py <slug> add-document --type announcement_sweep
    --status performed --evidence "<what was actually searched and found>"` each
    run (or --status skipped --reason "..." if it genuinely can't be done)."""
    base = os.path.expanduser("~/.report-generator")
    manifest_path = os.path.join(base, "research_cache", slug, "source_manifest.json")
    print(f"=== BSE/NSE announcements sweep recency: {slug} (expect a sweep "
          f"within the last {months} months) ===")

    if not os.path.exists(manifest_path):
        print(f"FAIL: no source_manifest.json found — no announcement sweep has "
              f"ever been logged for this company. Per reference/source_playbook.md's "
              f"'Announcements sweep' section, this is a standing requirement on "
              f"every run, not optional. Log it via source_manifest.py before "
              f"delivering the report.")
        return False

    with open(manifest_path) as f:
        data = json.load(f)
    sweeps = [d for d in data.get("documents", []) if d.get("type") == "announcement_sweep"]

    if not sweeps:
        print(f"FAIL: source_manifest.json exists but no 'announcement_sweep' entry "
              f"has ever been logged — this sweep is a standing requirement, not "
              f"something to skip because nothing else prompted a look.")
        return False

    dates = []
    for s in sweeps:
        try:
            dates.append(datetime.fromisoformat(str(s.get("date")).replace("Z", "+00:00")))
        except ValueError:
            continue
    if not dates:
        print("FAIL: could not parse a date from any logged announcement_sweep entry")
        return False

    latest_entry = max(sweeps, key=lambda s: s.get("date") or "")
    latest = max(dates)

    if latest_entry.get("status") == "skipped":
        print(f"FAIL: most recent announcement sweep ({latest.date()}) was logged as "
              f"--status skipped (reason: {latest_entry.get('reason') or 'not given'!r}) "
              f"— a disclosed skip must never look the same as a done sweep, and this "
              f"check is designed to FAIL in that case rather than silently pass "
              f"delivery. Perform the sweep, or accept the FAIL and state the gap "
              f"explicitly in the report per reference/rules_and_validation.md's 'Never drop anything silently' rule.")
        return False

    if not latest_entry.get("evidence") or not str(latest_entry.get("evidence")).strip():
        print(f"FAIL: most recent announcement sweep ({latest.date()}) has no "
              f"'evidence' field logged — a 'performed' sweep with no evidence of "
              f"what was actually searched/found is indistinguishable from a sweep "
              f"that never happened.")
        return False

    now = datetime.now(timezone.utc) if latest.tzinfo else datetime.now()
    age_days = (now - latest).days
    if age_days > months * 30:
        print(f"FAIL: most recent logged announcement sweep is {latest.date()} "
              f"({age_days} days old, > {months} months) — a fresh 6-month BSE/NSE "
              f"announcements sweep genuinely needs to happen this run, not just be "
              f"assumed unchanged from an old log entry.")
        return False

    print(f"PASS: most recent logged announcement sweep is {latest.date()} "
          f"({age_days} days old, within {months} months) — evidence: "
          f"{latest_entry.get('evidence')!r}")
    return True


def check_social(slug, report_path=None, months=3):
    """Checks source_manifest.json for a logged 'social_media_check' sweep within
    the last N months (default 3, tighter than the 6-month ratings/announcements
    window — see reference/data_sources.md's LinkedIn/X section for why), and
    if a report_path is given, flags any "LinkedIn post"/"X post" citation in the
    report whose cited date is older than the window — a stale social citation
    should have been refreshed or dropped, not left in from a prior run."""
    base = os.path.expanduser("~/.report-generator")
    manifest_path = os.path.join(base, "research_cache", slug, "source_manifest.json")
    print(f"=== LinkedIn/X check recency: {slug} (expect a check within the last "
          f"{months} months) ===")

    ok = True
    if not os.path.exists(manifest_path):
        print(f"FAIL: no source_manifest.json found — no social media check has "
              f"ever been logged for this company. Per reference/data_sources.md's "
              f"'LinkedIn / X (Twitter)' section, this is a standing requirement on "
              f"every run, not optional. Log it via source_manifest.py before "
              f"delivering the report.")
        ok = False
    else:
        with open(manifest_path) as f:
            data = json.load(f)
        checks = [d for d in data.get("documents", []) if d.get("type") == "social_media_check"]

        if not checks:
            print(f"FAIL: source_manifest.json exists but no 'social_media_check' "
                  f"entry has ever been logged — this check is a standing "
                  f"requirement, not something to skip because nothing else "
                  f"prompted a look.")
            ok = False
        else:
            dates = []
            for c in checks:
                try:
                    dates.append(datetime.fromisoformat(str(c.get("date")).replace("Z", "+00:00")))
                except ValueError:
                    continue
            if not dates:
                print("FAIL: could not parse a date from any logged social_media_check entry")
                ok = False
            else:
                latest_entry = max(checks, key=lambda c: c.get("date") or "")
                latest = max(dates)

                if latest_entry.get("status") == "skipped":
                    print(f"FAIL: most recent social media check ({latest.date()}) was "
                          f"logged as --status skipped (reason: "
                          f"{latest_entry.get('reason') or 'not given'!r}) — a "
                          f"disclosed skip must never look the same as a done check.")
                    ok = False
                elif not latest_entry.get("evidence") or not str(latest_entry.get("evidence")).strip():
                    print(f"FAIL: most recent social media check ({latest.date()}) has "
                          f"no 'evidence' field logged — a 'performed' check with no "
                          f"evidence of what was actually searched/found is "
                          f"indistinguishable from a check that never happened.")
                    ok = False
                else:
                    now = datetime.now(timezone.utc) if latest.tzinfo else datetime.now()
                    age_days = (now - latest).days
                    if age_days > months * 30:
                        print(f"FAIL: most recent logged social media check is "
                              f"{latest.date()} ({age_days} days old, > {months} months) "
                              f"— a fresh LinkedIn/X check genuinely needs to happen this "
                              f"run, not just be assumed unchanged from an old log entry.")
                        ok = False
                    else:
                        print(f"PASS: most recent logged social media check is "
                              f"{latest.date()} ({age_days} days old, within {months} "
                              f"months) — evidence: {latest_entry.get('evidence')!r}")

    if report_path and os.path.exists(report_path):
        with open(report_path, "r", errors="ignore") as f:
            text = f.read()
        cite_pattern = re.compile(
            r"(?:LinkedIn|X)\s+post,?\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
        stale = []
        now = datetime.now()
        for m in cite_pattern.finditer(text):
            try:
                d = datetime.fromisoformat(m.group(1))
            except ValueError:
                continue
            age_days = (now - d).days
            if age_days > months * 30:
                stale.append((m.group(0), age_days))
        if stale:
            for cite, age_days in stale:
                print(f"WARN: report cites {cite!r} which is {age_days} days old "
                      f"(> {months} months) — either this finding is still "
                      f"genuinely relevant (fine, but confirm deliberately) or it's "
                      f"a stale carryover from a prior run that should be dropped.")
        else:
            print(f"PASS: no LinkedIn/X citation in the report is older than "
                  f"{months} months")

    return ok  # FAILs if the sweep was never logged/skipped/evidence-free or stale — see docstring


def check_brokers(slug, months=3):
    """Checks source_manifest.json for a logged 'broker_sweep' entry within the
    last N months (default 3, same window as check_social — see
    reference/data_sources.md's 'Broker / agency research' section for why: a
    broker-forum discovery sweep is a discovery channel, not a formal disclosure
    record, so it needs re-checking every run rather than being trusted stale).
    Same performed/skipped/evidence rules as check_social — a disclosed skip or an
    evidence-free 'performed' entry both FAIL, never silently pass as if the sweep
    happened."""
    base = os.path.expanduser("~/.report-generator")
    manifest_path = os.path.join(base, "research_cache", slug, "source_manifest.json")
    print(f"=== broker-forum sweep recency check: {slug} (expect a check within "
          f"the last {months} months) ===")

    ok = True
    if not os.path.exists(manifest_path):
        print(f"FAIL: no source_manifest.json found — no broker-forum sweep has "
              f"ever been logged for this company. Per reference/data_sources.md's "
              f"'Broker / agency research' section, this is a standing requirement "
              f"on every run, not optional. Log it via source_manifest.py before "
              f"delivering the report.")
        return False

    with open(manifest_path) as f:
        data = json.load(f)
    checks = [d for d in data.get("documents", []) if d.get("type") == "broker_sweep"]

    if not checks:
        print(f"FAIL: source_manifest.json exists but no 'broker_sweep' entry has "
              f"ever been logged — this check is a standing requirement, not "
              f"something to skip because a broker PDF happened to already be on "
              f"file from an earlier run.")
        return False

    dates = []
    for c in checks:
        try:
            dates.append(datetime.fromisoformat(str(c.get("date")).replace("Z", "+00:00")))
        except ValueError:
            continue
    if not dates:
        print("FAIL: could not parse a date from any logged broker_sweep entry")
        return False

    latest_entry = max(checks, key=lambda c: c.get("date") or "")
    latest = max(dates)

    if latest_entry.get("status") == "skipped":
        print(f"FAIL: most recent broker-forum sweep ({latest.date()}) was logged "
              f"as --status skipped (reason: "
              f"{latest_entry.get('reason') or 'not given'!r}) — a disclosed skip "
              f"must never look the same as a done check.")
        ok = False
    elif not latest_entry.get("evidence") or not str(latest_entry.get("evidence")).strip():
        print(f"FAIL: most recent broker-forum sweep ({latest.date()}) has no "
              f"'evidence' field logged — a 'performed' check with no evidence of "
              f"what was actually searched/found is indistinguishable from a check "
              f"that never happened.")
        ok = False
    else:
        now = datetime.now(timezone.utc) if latest.tzinfo else datetime.now()
        age_days = (now - latest).days
        if age_days > months * 30:
            print(f"FAIL: most recent logged broker-forum sweep is {latest.date()} "
                  f"({age_days} days old, > {months} months) — a fresh sweep "
                  f"genuinely needs to happen this run, not just be assumed "
                  f"unchanged from an old log entry.")
            ok = False
        else:
            print(f"PASS: most recent logged broker-forum sweep is {latest.date()} "
                  f"({age_days} days old, within {months} months) — evidence: "
                  f"{latest_entry.get('evidence')!r}")

    return ok  # FAILs if the sweep was never logged/skipped/evidence-free or stale — see docstring


def check_paragraphs(report_path, max_words=160):
    # ~160 words approximates 10 rendered lines of body-text prose at the report's
    # normal column width (roughly 15-16 words/line observed in practice) — a
    # heuristic proxy, not exact typesetting, since markdown source line breaks
    # don't correspond to rendered line breaks.
    print(f"=== paragraph-length check: {report_path} (flag >{max_words} words, "
          f"~10 rendered lines) ===")
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False

    with open(report_path, "r", errors="ignore") as f:
        lines = f.read().split("\n")

    current_section = "(before first heading)"
    block = []
    flagged = []

    def flush():
        if not block:
            return
        text = " ".join(block)
        words = text.split()
        if len(words) > max_words:
            preview = " ".join(words[:12]) + "..."
            flagged.append((current_section, len(words), preview))

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            block = []
            current_section = stripped.lstrip("#").strip()
            continue
        if (not stripped or stripped.startswith(("|", "-", "*", "```")) or
                re.match(r"^\d+[a-z]?\.\s", stripped)):
            flush()
            block = []
            continue
        block.append(stripped)
    flush()

    if flagged:
        for section, wc, preview in flagged:
            if "verdict" in section.lower():
                advice = ("trim to a genuinely short 1-2 sentence verdict instead — "
                           "per report_format.md's Verdict spec, this section stays "
                           "a short paragraph even when other sections convert to "
                           "bullets; excess length here means evidence-recapping "
                           "crept in that belongs in Investment Thesis Summary/Key "
                           "Risks instead")
            else:
                advice = "convert to bullet points"
            print(f"FAIL: paragraph under {section!r} has ~{wc} words "
                  f"(~{wc // 16} rendered lines, over the {max_words}-word/"
                  f"~10-line limit) — {advice}. Starts: {preview!r}")
        return False

    print("PASS: no paragraph exceeds the ~10-rendered-line limit")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("html")
    p1.add_argument("path")

    p2 = sub.add_parser("pdf")
    p2.add_argument("path")

    p3 = sub.add_parser("report")
    p3.add_argument("path")
    p3.add_argument("--brokers", help="comma-separated broker tags to check for, e.g. NUVAMA_29042026,CLSA_24052026")

    p4 = sub.add_parser("sources")
    p4.add_argument("slug")

    p5 = sub.add_parser("freshness")
    p5.add_argument("slug")

    p6 = sub.add_parser("extraction")
    p6.add_argument("pdf_path")
    p6.add_argument("txt_path")

    p7 = sub.add_parser("depth")
    p7.add_argument("slug")

    p8 = sub.add_parser("sniff")
    p8.add_argument("pdf_path")

    p9 = sub.add_parser("slug")
    p9.add_argument("slug")

    sub.add_parser("links")

    p10 = sub.add_parser("scope")
    p10.add_argument("plugin_dir")
    p10.add_argument("--minutes", type=int, default=120)

    p11 = sub.add_parser("reproduction")
    p11.add_argument("source_path")
    p11.add_argument("report_path")
    p11.add_argument("--ngram", type=int, default=12)

    p12 = sub.add_parser("quotes")
    p12.add_argument("report_path")
    p12.add_argument("sources_dir")

    p13 = sub.add_parser("disclaimer")
    p13.add_argument("report_path")

    p14 = sub.add_parser("whitespace")
    p14.add_argument("pdf_path")
    p14.add_argument("--ratio", type=float, default=0.5,
                      help="interior page FAILs if its word count is below this "
                           "fraction of the interior-page median (default 0.5)")

    p15 = sub.add_parser("ratings")
    p15.add_argument("slug")
    p15.add_argument("--months", type=int, default=6)

    p15b = sub.add_parser("announcements")
    p15b.add_argument("slug")
    p15b.add_argument("--months", type=int, default=6)

    p16 = sub.add_parser("paragraphs")
    p16.add_argument("report_path")
    p16.add_argument("--max-words", type=int, default=160)

    p17 = sub.add_parser("social")
    p17.add_argument("slug")
    p17.add_argument("--report-path", default=None)
    p17.add_argument("--months", type=int, default=3)

    p18 = sub.add_parser("brokers")
    p18.add_argument("slug")
    p18.add_argument("--months", type=int, default=3)

    args = parser.parse_args()

    if args.cmd == "html":
        ok = check_html(args.path)
    elif args.cmd == "pdf":
        ok = check_pdf(args.path)
    elif args.cmd == "report":
        tags = args.brokers.split(",") if args.brokers else []
        ok = check_report(args.path, tags)
    elif args.cmd == "sources":
        ok = check_sources(args.slug)
    elif args.cmd == "freshness":
        ok = check_freshness(args.slug)
    elif args.cmd == "extraction":
        ok = check_extraction(args.pdf_path, args.txt_path)
    elif args.cmd == "depth":
        ok = check_depth(args.slug)
    elif args.cmd == "sniff":
        ok = check_sniff(args.pdf_path)
    elif args.cmd == "slug":
        ok = check_slug(args.slug)
    elif args.cmd == "links":
        ok = check_links()
    elif args.cmd == "scope":
        ok = check_scope(args.plugin_dir, args.minutes)
    elif args.cmd == "reproduction":
        ok = check_reproduction(args.source_path, args.report_path, args.ngram)
    elif args.cmd == "quotes":
        ok = check_quotes(args.report_path, args.sources_dir)
    elif args.cmd == "disclaimer":
        ok = check_disclaimer(args.report_path)
    elif args.cmd == "whitespace":
        ok = check_whitespace(args.pdf_path, args.ratio)
    elif args.cmd == "ratings":
        ok = check_ratings_recency(args.slug, args.months)
    elif args.cmd == "announcements":
        ok = check_announcements(args.slug, args.months)
    elif args.cmd == "paragraphs":
        ok = check_paragraphs(args.report_path, args.max_words)
    elif args.cmd == "social":
        ok = check_social(args.slug, args.report_path, args.months)
    elif args.cmd == "brokers":
        ok = check_brokers(args.slug, args.months)
    else:
        parser.print_help()
        sys.exit(2)

    print()
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
