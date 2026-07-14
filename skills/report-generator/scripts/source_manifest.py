#!/usr/bin/env python3
"""
source_manifest.py — a small, durable record of every source document ever
fetched and extracted for a company, kept in research_cache/ (survives even if
sources/ is later deleted to save space).

Why this exists: sources/<slug>/ holds the bulky raw PDFs/text (regenerable by
refetching, deliberately not backed up) while research_cache/<slug>/ holds the
small synthesized state (worth keeping). But two of verify_report.py's
guardrails — `depth` (counts concalls/investor presentations/annual reports)
and `extraction` (confirms an annual report's extraction covered every page) —
currently work by scanning sources/ directly. Delete sources/ and those checks
can no longer prove anything was ever sourced correctly, even though the real
analysis (guidance_history.json, report.md, etc.) is intact. This manifest is
the fix: a lightweight metadata record — type, label, date, page coverage,
where it came from — logged once at fetch/extraction time, so `depth` and
`extraction` can be re-verified from research_cache/ alone, long after the
original PDF is gone.

This does NOT solve everything sources/ deletion costs — `verify_report.py
quotes` still needs the actual source text to re-verify a quote is genuinely
verbatim, and this manifest can't substitute for that (metadata isn't content).
It solves the "was this company's sourcing depth/coverage ever actually
confirmed" question specifically.

Runs entirely locally, no network required.

Usage:
    # log a document immediately after fetching + extracting it (while the
    # source PDF is still on disk, so page counts are accurate)
    python3 source_manifest.py <company_slug> add-document \\
        --type concall --label "Q4 FY26" --date "2026-04-29" \\
        --filename q4fy26_concall_may2026.txt --pages-total 34 \\
        --pages-extracted-start 1 --pages-extracted-end 34 \\
        --source-url "https://..." --extraction-verified

    # print a summary: counts by type, any gaps
    python3 source_manifest.py <company_slug> report
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

DOC_TYPES = ["concall", "investor_presentation", "annual_report", "broker_report",
             "rating_rationale", "announcement_sweep", "social_media_check", "other"]


def _path(slug):
    base = os.path.expanduser("~/.report-generator")
    d = os.path.join(base, "research_cache", slug)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "source_manifest.json")


def _load(slug):
    p = _path(slug)
    if not os.path.exists(p):
        return {"documents": []}
    with open(p) as f:
        return json.load(f)


def _save(slug, data):
    with open(_path(slug), "w") as f:
        json.dump(data, f, indent=2)


def add_document(args):
    data = _load(args.slug)
    next_id = max([d.get("id", -1) for d in data["documents"]], default=-1) + 1

    fully_covered = None
    if args.pages_total and args.pages_extracted_start and args.pages_extracted_end:
        fully_covered = (args.pages_extracted_start == 1 and
                          args.pages_extracted_end == args.pages_total)

    entry = {
        "id": next_id,
        "type": args.type,
        "label": args.label,
        "date": args.date,
        "filename": args.filename,
        "source_url": args.source_url or ("user-uploaded" if args.user_uploaded else None),
        "pages_total": args.pages_total,
        "pages_extracted_start": args.pages_extracted_start,
        "pages_extracted_end": args.pages_extracted_end,
        "full_page_coverage": fully_covered,
        "extraction_verified": bool(args.extraction_verified),
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    data["documents"].append(entry)
    _save(args.slug, data)
    print(f"Logged document #{next_id}: {args.type} / {args.label} ({args.filename})")
    if fully_covered is False:
        print(f"WARN: pages_extracted_start/end ({args.pages_extracted_start}-"
              f"{args.pages_extracted_end}) does not cover the full document "
              f"(1-{args.pages_total}) — this is a partial extraction, logged "
              f"as such, not silently treated as complete.", file=sys.stderr)


def report(args):
    data = _load(args.slug)
    docs = data["documents"]
    if not docs:
        print(f"No documents logged in source_manifest.json for {args.slug}.")
        return

    by_type = {}
    for d in docs:
        by_type.setdefault(d["type"], []).append(d)

    print(f"=== source manifest: {args.slug} ({len(docs)} document(s) logged) ===")
    for t in DOC_TYPES:
        items = by_type.get(t, [])
        if not items:
            continue
        print(f"\n{t} ({len(items)}):")
        for d in sorted(items, key=lambda x: x.get("date") or ""):
            coverage = ""
            if d.get("pages_total"):
                cov_flag = "full" if d.get("full_page_coverage") else "PARTIAL"
                coverage = (f" [{d['pages_extracted_start']}-{d['pages_extracted_end']} "
                            f"of {d['pages_total']} pages, {cov_flag}]")
            verified = "verified" if d.get("extraction_verified") else "not verified"
            src = d.get("source_url") or "(no source recorded)"
            print(f"  - {d.get('label', '?')} ({d.get('date', '?')}) — "
                  f"{d.get('filename', '?')}{coverage} — {verified} — {src}")

    partial = [d for d in docs if d.get("full_page_coverage") is False]
    if partial:
        print(f"\nFLAG: {len(partial)} document(s) have confirmed PARTIAL page "
              f"coverage — this is a real gap, not a false alarm, and should be "
              f"stated explicitly in the report per the 'Never drop anything "
              f"silently' rule.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-document")
    p1.add_argument("--type", required=True, choices=DOC_TYPES)
    p1.add_argument("--label", required=True, help='e.g. "Q4 FY26" or "FY2024-25"')
    p1.add_argument("--date", required=True, help="ISO date of the document itself, not today")
    p1.add_argument("--filename", required=True, help="filename as saved in sources/<slug>/")
    p1.add_argument("--pages-total", type=int)
    p1.add_argument("--pages-extracted-start", type=int)
    p1.add_argument("--pages-extracted-end", type=int)
    p1.add_argument("--source-url")
    p1.add_argument("--user-uploaded", action="store_true")
    p1.add_argument("--extraction-verified", action="store_true",
                     help="pass this if scripts/verify_report.py extraction was run and passed")
    p1.set_defaults(func=add_document)

    p2 = sub.add_parser("report")
    p2.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
