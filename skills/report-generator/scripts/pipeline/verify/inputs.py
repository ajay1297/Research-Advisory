"""Tier 1, input guardrails — is what we are about to work on the right thing?
"""
import sys
import os
import re
import subprocess

from .registry import check, Arg, SKILL_DIR, HELPERS_DIR


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

@check("sniff", Arg("pdf_path"))
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

@check("slug", Arg("slug"))
def check_slug(slug):
    print(f"=== slug safety check: {slug!r} ===")
    if re.fullmatch(r"[a-z0-9_]+", slug):
        print(f"PASS: slug is safe for filesystem paths")
        return True
    print(f"FAIL: slug contains characters outside [a-z0-9_] — unsafe to use in "
          f"~/.report-generator/ paths as-is; normalize it (lowercase, underscores) "
          f"before using it anywhere")
    return False

@check("links")
def check_links():
    print("=== reference-link integrity check (this skill's own docs) ===")
    sys.path.insert(0, HELPERS_DIR)
    import check_reference_links
    findings = check_reference_links.check(SKILL_DIR)
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
