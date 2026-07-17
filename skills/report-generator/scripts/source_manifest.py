#!/usr/bin/env python3
"""
source_manifest.py — a small, durable record of every source document ever
fetched and extracted for a company, kept in research_cache/ (survives even if
sources/ is later deleted to save space).

Why this exists: sources/<slug>/ holds the bulky raw PDFs/text (regenerable by
refetching, deliberately not backed up) while research_cache/<slug>/ holds the
small synthesized state (worth keeping). But two of verify_report.py's
guardrails — `depth` (counts concalls/investor presentations/annual reports/
press releases) and `extraction` (confirms an annual report's extraction
covered every page) —
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

Usage (log immediately after fetching + extracting, while the source PDF is still on
disk, so page counts are accurate):
    python3 source_manifest.py <company_slug> add-document \\
        --type concall --label "Q4 FY26" --date "2026-04-29" \\
        --filename q4fy26_concall_may2026.txt --pages-total 34 \\
        --pages-extracted-start 1 --pages-extracted-end 34 \\
        --source-url "https://..." --extraction-verified

    python3 source_manifest.py <company_slug> report
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

DOC_TYPES = ["concall", "investor_presentation", "annual_report", "press_release",
             "broker_report", "rating_rationale", "announcement_sweep",
             "social_media_check", "broker_sweep", "other"]

# announcement_sweep/social_media_check/broker_sweep log a *check performed*, not
# a fetched document — there is no real file in sources/<slug>/ for these, so
# --filename is not required for them (see add_document()'s validation below).
# Every other type is a genuine fetched document and --filename stays required.
FILENAME_OPTIONAL_TYPES = {"announcement_sweep", "social_media_check", "broker_sweep"}


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
    # --status/--evidence/--reason exist specifically for the announcement_sweep and
    # social_media_check doc types (see reference/guardrails.md's `announcements`/`social`
    # guardrails, which verify_report.py FAILs if a "performed" entry has no real evidence,
    # or if the most recent entry is a disclosed "skipped"). This was previously documented
    # in SKILL.md but not actually implemented here — a real spec/script mismatch that
    # meant those two guardrails could never have worked as described.
    if args.status == "performed":
        if not args.evidence or not args.evidence.strip():
            print("ERROR: --status performed requires non-empty --evidence describing what "
                  "was actually searched and found (or 'nothing new'). A placeholder like "
                  "'done'/'checked' does not count — this check exists specifically to stop "
                  "a logged sweep from looking the same as real work when it wasn't.",
                  file=sys.stderr)
            sys.exit(1)
        placeholder_evidence = {"done", "checked", "completed", "ok", "yes", "performed"}
        if args.evidence.strip().lower() in placeholder_evidence:
            print(f"ERROR: --evidence '{args.evidence}' reads as a placeholder, not a real "
                  f"finding. Describe what was actually searched and what was found.",
                  file=sys.stderr)
            sys.exit(1)
    if args.status == "skipped" and not args.reason:
        print("ERROR: --status skipped requires --reason.", file=sys.stderr)
        sys.exit(1)
    if args.type not in FILENAME_OPTIONAL_TYPES and not args.filename:
        print(f"ERROR: --filename is required for --type {args.type} (a genuine "
              f"fetched document needs a real filename as saved in sources/<slug>/).",
              file=sys.stderr)
        sys.exit(1)

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
        "status": args.status,
        "evidence": args.evidence,
        "reason": args.reason,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    data["documents"].append(entry)
    _save(args.slug, data)
    filename_bit = f" ({args.filename})" if args.filename else ""
    print(f"Logged document #{next_id}: {args.type} / {args.label}{filename_bit}")
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
    p1.add_argument("--filename",
                     help="filename as saved in sources/<slug>/ — required for every type "
                          "except announcement_sweep/social_media_check/broker_sweep, which log "
                          "a check performed rather than a fetched document")
    p1.add_argument("--pages-total", type=int)
    p1.add_argument("--pages-extracted-start", type=int)
    p1.add_argument("--pages-extracted-end", type=int)
    p1.add_argument("--source-url")
    p1.add_argument("--user-uploaded", action="store_true")
    p1.add_argument("--extraction-verified", action="store_true",
                     help="pass this if scripts/verify_report.py extraction was run and passed")
    p1.add_argument("--status", choices=["performed", "skipped"],
                     help="for announcement_sweep/social_media_check/broker_sweep doc types: "
                          "was the sweep actually performed this run, or explicitly skipped")
    p1.add_argument("--evidence",
                     help="required if --status performed: what was actually searched and found "
                          "(or 'nothing new') — a real finding, not a placeholder")
    p1.add_argument("--reason",
                     help="required if --status skipped: why the sweep couldn't be done this run")
    p1.set_defaults(func=add_document)

    p2 = sub.add_parser("report")
    p2.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
