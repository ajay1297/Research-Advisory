"""Tier 3, output guardrails — is the finished report fit to deliver?

The recency family (ratings/announcements/deals/social/brokers) is tier 3 too,
but lives in recency.py since those five share one shape.
"""
import os
import re
import subprocess

from .registry import check, Arg


@check("quotes", Arg("report_path"), Arg("sources_dir"))
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

@check("disclaimer", Arg("report_path"))
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

@check("filenames", Arg("slug"))
def check_filenames(slug):
    print(f"=== output filename check: {slug!r} ===")
    out_dir = os.path.expanduser(f"~/.report-generator/output/{slug}")
    if not os.path.isdir(out_dir):
        print(f"FAIL: {out_dir} does not exist")
        return False

    entries = os.listdir(out_dir)
    generic = [f for f in entries if f in ("report.md", "report.pdf")]
    if generic:
        print(f"FAIL: found generic filename(s) {generic} in {out_dir} — "
              f"pipeline/step3_memorize.md requires <Company_Name>_report.md/.pdf "
              f"for the output/ deliverable (e.g. TD_Power_Systems_report.md); "
              f"'report.md'/'report.pdf' is only the internal research_cache/ "
              f"working-copy name and must never be the delivered filename. Rename "
              f"before telling the user the report is ready.")
        return False

    md_matches = [f for f in entries if f.endswith("_report.md")]
    pdf_matches = [f for f in entries if f.endswith("_report.pdf")]
    ok = True
    if not md_matches:
        print(f"FAIL: no <Company_Name>_report.md found in {out_dir}")
        ok = False
    if not pdf_matches:
        print(f"FAIL: no <Company_Name>_report.pdf found in {out_dir}")
        ok = False
    if ok:
        print(f"PASS: {md_matches[0]} and {pdf_matches[0]} correctly named")
    return ok

@check("whitespace", Arg("pdf_path"),
       Arg("--ratio", type=float, default=0.5,
           help="interior page FAILs if its word count is below this "
                "fraction of the interior-page median (default 0.5)"))
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

# Case-insensitive marker for a gap the drafting step itself has already flagged as
# closed. A real, still-open gap bullet never needs this word — it's only ever
# written by a drafting pass that fixed a section but forgot to delete the gap
# bullet describing the now-fixed problem (confirmed in practice: this happened on
# a real report, where an Annual Report fetch failure was resolved by a user-supplied
# local copy, three downstream sections got corrected, but the "Sourcing Gaps &
# Limitations" bullet describing the original failure was left in place instead of
# removed, mislabeled "RESOLVED" rather than deleted).
RESOLVED_MARKER = re.compile(r"\bresolved\b", re.IGNORECASE)

GAPS_SECTION_HEADING = re.compile(r"^#{1,3}\s*sourcing gaps", re.IGNORECASE)

@check("gaps", Arg("report_path"))
def check_gaps(report_path):
    """Scans the 'Sourcing Gaps & Limitations' section (if present) for a
    RESOLVED/resolved marker left in a gap bullet — a gap that's been fixed belongs
    removed from this section entirely, not flagged as resolved and kept. FAILs if
    found, since this is a straightforward mechanical mistake with a mechanical fix
    (delete the bullet), not a judgment call worth a WARN."""
    print(f"=== gaps-section staleness check: {report_path} (flag any "
          f"resolved-but-not-removed gap bullet) ===")
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False

    with open(report_path, "r", errors="ignore") as f:
        lines = f.read().split("\n")

    in_gaps_section = False
    flagged = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            in_gaps_section = bool(GAPS_SECTION_HEADING.match(stripped))
            continue
        if in_gaps_section and stripped.startswith(("-", "*")) and RESOLVED_MARKER.search(stripped):
            preview = stripped[:100] + ("..." if len(stripped) > 100 else "")
            flagged.append(preview)

    if flagged:
        for p in flagged:
            print(f"FAIL: gap bullet still present but marked resolved — delete the "
                  f"bullet instead of labeling it resolved: {p!r}")
        return False

    print("PASS: no resolved-but-not-removed gap bullets found "
          "(or no 'Sourcing Gaps & Limitations' section present)")
    return True

@check("financials", Arg("report_path"))
def check_financials(report_path):
    """Flags a Financial Performance Summary row where PBT is filled in but PAT is
    blank (or vice versa) — the two are adjacent line items in almost every source
    results table, so a partial fill is a strong signal the source table wasn't
    fully transcribed, not that PAT genuinely wasn't disclosed. Confirmed in
    practice: a real report carried PBT through for four quarters while silently
    dropping PAT/Tax from the same already-extracted source rows each time.

    Column-position-agnostic by design — finds the PBT/PAT columns by header text
    (case-insensitive, PAT matched as a whole word so it doesn't also match "PAT
    Margin"), so it survives the column set varying report to report (e.g. EBITDA
    Margin swapped in for Gross Margin when gross margin isn't disclosed)."""
    print(f"=== financial-performance completeness check: {report_path} ===")
    if not os.path.exists(report_path):
        print(f"FAIL: {report_path} does not exist")
        return False

    with open(report_path, "r", errors="ignore") as f:
        text = f.read()

    m = re.search(r"^##\s*Financial Performance Summary\s*$", text, re.MULTILINE)
    if not m:
        print("PASS: no 'Financial Performance Summary' section present — nothing to check")
        return True

    tail = text[m.end():]
    next_heading = re.search(r"^##\s", tail, re.MULTILINE)
    section = tail[:next_heading.start()] if next_heading else tail

    table_rows = [ln for ln in section.split("\n") if ln.strip().startswith("|")]
    if len(table_rows) < 3:  # header + separator + at least one data row
        print("WARN: 'Financial Performance Summary' section has no parseable table — "
              "skipping completeness check (nothing to do if the section is prose-only)")
        return True

    def cells(row):
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header = cells(table_rows[0])
    period_idx = next((i for i, h in enumerate(header) if re.search(r"period|quarter|fy", h, re.I)), 0)
    pbt_idx = next((i for i, h in enumerate(header) if re.search(r"\bpbt\b", h, re.I)), None)
    pat_idx = next((i for i, h in enumerate(header)
                     if re.search(r"\bpat\b", h, re.I) and not re.search(r"margin", h, re.I)), None)

    if pbt_idx is None or pat_idx is None:
        print("PASS: no PBT/PAT columns found in the table — nothing to cross-check")
        return True

    def blank(v):
        return v in ("", "-", "—", "–", "n/a", "na")

    flagged = []
    for row in table_rows[2:]:  # skip header + markdown separator row
        c = cells(row)
        if max(pbt_idx, pat_idx, period_idx) >= len(c):
            continue
        pbt_blank, pat_blank = blank(c[pbt_idx].lower()), blank(c[pat_idx].lower())
        if pbt_blank != pat_blank:  # exactly one of the pair is filled in
            have, missing = ("PBT", "PAT") if pat_blank else ("PAT", "PBT")
            flagged.append((c[period_idx], have, missing))

    if flagged:
        for period, have, missing in flagged:
            print(f"WARN: {period}: {have} is filled in but {missing} is blank — "
                  f"if the source table already disclosed both (the common case — "
                  f"PBT and PAT are adjacent line items in almost every results "
                  f"table), this is a transcription gap, not a real source gap. "
                  f"Re-check the source for this period before leaving it blank.")
        return True  # informational WARN only — the gap may be genuine, confirm before treating as FAIL

    print("PASS: no PBT-filled/PAT-blank (or vice versa) rows found in "
          "Financial Performance Summary")
    return True


@check("paragraphs", Arg("report_path"), Arg("--max-words", type=int, default=160))
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
