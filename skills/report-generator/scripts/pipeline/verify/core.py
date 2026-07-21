"""Core artifact checks — the HTML/PDF/markdown a run produces, the state it
records, and whether the sourcing actually went as deep as it claims.
"""
import os
import re
import json
import subprocess
from datetime import datetime, timezone

from .registry import check, Arg


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

@check("html", Arg("path"))
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

@check("pdf", Arg("path"))
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
              f"twice (see pipeline/step3_memorize.md), AND you must state this explicitly in your "
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

@check("report", Arg("path"),
       Arg("--brokers", help="comma-separated broker tags to check for, e.g. NUVAMA_29042026,CLSA_24052026"))
def check_report(path, brokers=None):
    # Takes the raw --brokers string and splits it here rather than in the CLI
    # layer, so the registry can call every check uniformly as fn(**vars(args)).
    broker_tags = brokers.split(",") if brokers else []
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

@check("sources", Arg("slug"))
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

@check("freshness", Arg("slug"))
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

    # last_success_at is what the NEXT run's delta window counts back from (see
    # check_freshness.py's bse_fetch_window). A state.json written by an older
    # version of --mark-processed won't have it, and the next run would silently
    # fall back to a full-depth sweep instead of the intended 7-day delta — worth a
    # FAIL here rather than a surprise wide refetch later.
    success = state.get("last_success_at")
    if not success:
        print(f"FAIL: state.json has no last_success_at field — the next run's BSE "
              f"delta window has no anchor and will fall back to a full-depth sweep. "
              f"Re-run check_freshness.py --mark-processed to write it.")
        return False
    if success[:10] != today.isoformat():
        print(f"FAIL: last_success_at={success} is not today ({today}) — "
              f"--mark-processed likely wasn't called at the end of this run")
        return False

    print(f"PASS: last_processed_at={ts} is today, last_success_at={success}")
    return True

@check("extraction", Arg("pdf_path"), Arg("txt_path"))
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

@check("depth", Arg("slug"))
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
