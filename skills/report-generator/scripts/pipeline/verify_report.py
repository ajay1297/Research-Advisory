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

    python3 verify_report.py filenames <company_slug>
        Checks ~/.report-generator/output/<company_slug>/ contains
        <Company_Name>_report.md and <Company_Name>_report.pdf, per
        pipeline/step3_memorize.md's "Save and cache" naming rule — and FAILs
        if it instead finds the generic report.md/report.pdf (the naming used
        only for the internal research_cache/ working copy, never for the
        output/ deliverable). Catches exactly the mistake already made once in
        practice: saving the deliverable under the generic name instead of the
        company-prefixed one.
"""
import sys
import argparse

from verify import CHECKS

# The order subcommands appear in `--help`. Kept explicit because the checks are
# spread across modules now, so import order alone would not reproduce the
# original ordering — and a reordered help listing reads as a behavior change to
# anyone diffing it. A check registered but missing here is a hard error rather
# than a silently absent subcommand.
ORDER = (
    "html", "pdf", "report", "sources", "freshness", "extraction", "depth",
    "sniff", "slug", "links",
    "scope", "reproduction",
    "quotes", "disclaimer", "filenames", "whitespace",
    "ratings", "announcements", "deals", "shareholding",
    "paragraphs", "gaps", "financials", "social", "brokers",
)


def main():
    missing = set(CHECKS) - set(ORDER)
    if missing:
        raise SystemExit(f"checks registered but absent from ORDER: {sorted(missing)}")
    unknown = set(ORDER) - set(CHECKS)
    if unknown:
        raise SystemExit(f"ORDER names no such check: {sorted(unknown)}")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ORDER:
        p = sub.add_parser(name)
        for arg in CHECKS[name][1]:
            arg.add_to(p)

    args = parser.parse_args()
    kwargs = {k: v for k, v in vars(args).items() if k != "cmd"}
    ok = CHECKS[args.cmd][0](**kwargs)

    print()
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
