"""Tier 3, recency guardrails — was each standing sweep actually re-run this time?

Four of these five checks (announcements, deals, social, brokers) ask exactly the
same question of source_manifest.json: is there a logged sweep of type X, is it
recent enough, and is it distinguishable from a sweep that never happened? They
were four near-identical copies of the same forty lines, which meant a fix to the
date parsing or the tz-aware/naive comparison had to be applied four times — and
the copies had already drifted apart in small ways. _manifest_sweep() is that
shared shape; each check now declares only what genuinely differs.

The fifth (ratings) reads a different file, rating_history.json, and is
deliberately WARN-only, so it shares the date helpers but not the sweep logic.

FAIL-not-WARN discipline is preserved exactly as before: for the four sweeps, a
never-logged sweep, an explicit --status skipped, an evidence-free "performed"
entry, and a stale entry all FAIL. A disclosed skip must never look the same as a
done sweep.
"""
import os
import re
import json
from datetime import datetime, timezone

from .registry import check, Arg

def _manifest_path(slug):
    base = os.path.expanduser("~/.report-generator")
    return os.path.join(base, "research_cache", slug, "source_manifest.json")


def _parse(value):
    """Parse one logged date, tolerating a trailing Z. Returns None if unusable."""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(latest):
    """Age in days, matching latest's tz-awareness so the subtraction is legal."""
    now = datetime.now(timezone.utc) if latest.tzinfo else datetime.now()
    return (now - latest).days


SKIP_TAIL_LONG = (", and this check is designed to FAIL in that case rather than "
                  "silently pass delivery. Perform the sweep, or accept the FAIL and "
                  "state the gap explicitly in the report per "
                  "reference/rules_and_validation.md's 'Never drop anything silently' "
                  "rule.")


def _manifest_sweep(slug, *, doc_type, heading, noun, requirement_ref, months,
                    no_entry_because, stale_because, evidence_extra="",
                    unit="sweep", skip_tail=SKIP_TAIL_LONG, long_noun=None,
                    evidence_verb="searched/found"):
    """Shared body of the four source_manifest.json sweep-recency checks.

    doc_type         the --type value the sweep is logged under
    heading          banner text, e.g. "Bulk/block deals sweep recency"
    noun             how the sweep is named mid-sentence, e.g. "deals sweep"
    requirement_ref  the reference/ doc that makes this sweep a standing rule
    no_entry_because trailing clause of the never-logged-at-all FAIL
    stale_because    trailing clause of the too-old FAIL
    evidence_extra   optional parenthetical for the missing-evidence FAIL
    unit             "sweep" or "check" — the two halves of this family word the
                     same concept differently, and the wording is preserved rather
                     than normalized so this refactor stays byte-identical in output
    skip_tail        the disclosed-skip FAIL's trailing clause; announcements/deals
                     spell out the remedy, social/brokers stop at the principle
    long_noun        fuller name used only in the never-logged FAIL, where deals
                     spells out "bulk/block deals sweep"; defaults to noun
    evidence_verb    what the evidence would attest to ("searched/found", or just
                     "found" for deals, whose sweep is a lookup rather than a search)

    unit/skip_tail/long_noun/evidence_verb exist purely to preserve each check's
    exact pre-refactor wording — the four copies had drifted, and normalizing them
    would have made this refactor a behavior change rather than a pure dedup.
    """
    manifest_path = _manifest_path(slug)
    print(f"=== {heading}: {slug} (expect a {unit} within the last "
          f"{months} months) ===")

    if not os.path.exists(manifest_path):
        print(f"FAIL: no source_manifest.json found — no {long_noun or noun} has ever been "
              f"logged for this company. Per {requirement_ref}, this is a "
              f"standing requirement on every run, not optional. Log it via "
              f"source_manifest.py before delivering the report.")
        return False

    with open(manifest_path) as f:
        data = json.load(f)
    sweeps = [d for d in data.get("documents", []) if d.get("type") == doc_type]

    if not sweeps:
        print(f"FAIL: source_manifest.json exists but no {doc_type!r} entry has "
              f"ever been logged — {no_entry_because}")
        return False

    dates = [d for d in (_parse(s.get("date")) for s in sweeps) if d]
    if not dates:
        print(f"FAIL: could not parse a date from any logged {doc_type} entry")
        return False

    latest_entry = max(sweeps, key=lambda s: s.get("date") or "")
    latest = max(dates)

    if latest_entry.get("status") == "skipped":
        print(f"FAIL: most recent {noun} ({latest.date()}) was logged as --status "
              f"skipped (reason: {latest_entry.get('reason') or 'not given'!r}) — a "
              f"disclosed skip must never look the same as a done {unit}{skip_tail}")
        return False

    if not str(latest_entry.get("evidence") or "").strip():
        print(f"FAIL: most recent {noun} ({latest.date()}) has no 'evidence' field "
              f"logged — a 'performed' {unit} with no evidence of what was actually "
              f"{evidence_verb}{evidence_extra} is indistinguishable from a {unit} "
              f"that never happened.")
        return False

    age = _age_days(latest)
    if age > months * 30:
        print(f"FAIL: most recent logged {noun} is {latest.date()} ({age} days old, "
              f"> {months} months) — {stale_because}")
        return False

    print(f"PASS: most recent logged {noun} is {latest.date()} ({age} days old, "
          f"within {months} months) — evidence: {latest_entry.get('evidence')!r}")
    return True


@check("ratings", Arg("slug"), Arg("--months", type=int, default=6))
def check_ratings_recency(slug, months=6):
    """Unlike the four sweep checks below, this one is WARN-only and never blocks
    delivery: a company can legitimately be unrated, and rating_history.json is a
    cumulative record rather than a per-run sweep log."""
    path = os.path.join(os.path.expanduser("~/.report-generator"),
                        "research_cache", slug, "rating_history.json")
    print(f"=== rating-check recency: {slug} (expect a check within the last "
          f"{months} months) ===")

    if not os.path.exists(path):
        print(f"WARN: {path} does not exist — no rating check was ever logged for "
              f"this company. If genuinely no agency covers it, that must be stated "
              f"explicitly in the report; if it just hasn't been checked, check now.")
        return True

    with open(path) as f:
        history = json.load(f)
    entries = (history if isinstance(history, list)
               else history.get("ratings") or history.get("entries") or [])
    if not entries:
        print("WARN: rating_history.json exists but has no entries — same caveat "
              "as above: state explicitly whether this means 'unrated' or "
              "'not yet checked.'")
        return True

    latest = None
    for e in entries:
        for field in ("date", "rationale_date", "action_date", "logged_at"):
            if field in e:
                d = _parse(e[field])
                if d and (latest is None or d > latest):
                    latest = d
                break

    if latest is None:
        print("WARN: could not find a parseable date field in rating_history.json "
              "entries — cannot confirm recency mechanically, verify manually")
        return True

    age = _age_days(latest)
    if age > months * 30:
        print(f"WARN: most recent logged rating entry is {latest.date()} "
              f"({age} days old, > {months} months) — this does NOT mean the "
              f"rating changed, but it does mean a fresh check for the last "
              f"{months} months genuinely needs to happen this run rather than "
              f"reusing this cached entry silently. Confirm you actively re-checked "
              f"each covering agency's site this run, not just read this file.")
    else:
        print(f"PASS: most recent logged rating entry is {latest.date()} "
              f"({age} days old, within {months} months)")
    return True  # informational WARN only — never blocks delivery on its own


@check("announcements", Arg("slug"), Arg("--months", type=int, default=6))
def check_announcements(slug, months=6):
    """Log via `source_manifest.py <slug> add-document --type announcement_sweep
    --status performed --evidence "<what was actually searched and found>"`."""
    return _manifest_sweep(
        slug, months=months,
        doc_type="announcement_sweep",
        heading="BSE/NSE announcements sweep recency",
        noun="announcement sweep",
        requirement_ref="reference/source_playbook.md's 'Announcements sweep' section",
        no_entry_because="this sweep is a standing requirement, not something to "
                         "skip because nothing else prompted a look.",
        stale_because="a fresh 6-month BSE/NSE announcements sweep genuinely needs "
                      "to happen this run, not just be assumed unchanged from an "
                      "old log entry.")


@check("deals", Arg("slug"), Arg("--months", type=int, default=6))
def check_deals(slug, months=6):
    """Log via `source_manifest.py <slug> add-document --type deals_sweep --status
    performed --evidence "<what scripts/helpers/bulk_block_deals.py returned>"`."""
    return _manifest_sweep(
        slug, months=months,
        doc_type="deals_sweep",
        heading="Bulk/block deals sweep recency",
        noun="deals sweep",
        requirement_ref="reference/data_sources.md's 'Bulk & Block Deals' section",
        no_entry_because="this sweep is a standing requirement, not something to "
                         "skip because nothing else prompted a look.",
        stale_because="a fresh bulk/block deals sweep genuinely needs to happen "
                      "this run, not just be assumed unchanged from an old log entry.",
        evidence_extra=" (or 'no deals found')",
        long_noun="bulk/block deals sweep", evidence_verb="found")


@check("shareholding", Arg("slug"), Arg("--months", type=int, default=6))
def check_shareholding(slug, months=6):
    """Log via `source_manifest.py <slug> add-document --type shareholding_sweep
    --status performed --evidence "<what scripts/helpers/shareholding_pattern.py
    returned>"`. Default window matches deals_sweep's, not brokers/social's tighter
    3-month one — BSE's public-shareholding filing is itself only quarterly (SEBI-
    mandated), so a fresh sweep can be at most one quarter stale regardless."""
    return _manifest_sweep(
        slug, months=months,
        doc_type="shareholding_sweep",
        heading="Named public/non-promoter holders sweep recency",
        noun="shareholding sweep",
        requirement_ref="reference/report_sections.md's Promoter/Governance "
                        "'Named public/non-promoter holders' section",
        no_entry_because="this sweep is a standing requirement, not something to "
                         "skip because the company doesn't look institutionally held.",
        stale_because="a fresh named-holders sweep genuinely needs to happen this "
                      "run — BSE's public-shareholding filing updates quarterly, so "
                      "an old log entry can already be a full quarter out of date.",
        evidence_extra=" (or 'no named holder this quarter')",
        long_noun="shareholding sweep", evidence_verb="found")


@check("brokers", Arg("slug"), Arg("--months", type=int, default=3))
def check_brokers(slug, months=3):
    """Default window is 3 months, not 6: a broker-forum sweep is a discovery
    channel rather than a formal disclosure record, so it needs re-checking every
    run rather than being trusted stale."""
    return _manifest_sweep(
        slug, months=months,
        doc_type="broker_sweep",
        heading="broker-forum sweep recency check",
        noun="broker-forum sweep",
        requirement_ref="reference/data_sources.md's 'Broker / agency research' section",
        no_entry_because="this check is a standing requirement, not something to "
                         "skip because a broker PDF happened to already be on file "
                         "from an earlier run.",
        stale_because="a fresh sweep genuinely needs to happen this run, not just "
                      "be assumed unchanged from an old log entry.",
        unit="check", skip_tail=".")


# A social citation in the report carries its own date, so this check has a second
# half the other four don't: the manifest says the sweep happened, but a stale
# LinkedIn/X citation left in from a prior run is a separate failure mode.
SOCIAL_CITE = re.compile(r"(?:LinkedIn|X)\s+post,?\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


@check("social", Arg("slug"), Arg("--report-path", default=None),
       Arg("--months", type=int, default=3))
def check_social(slug, report_path=None, months=3):
    """Default window is 3 months, tighter than the 6-month ratings/announcements
    window — see reference/data_sources.md's LinkedIn/X section for why."""
    ok = _manifest_sweep(
        slug, months=months,
        doc_type="social_media_check",
        heading="LinkedIn/X check recency",
        noun="social media check",
        requirement_ref="reference/data_sources.md's 'LinkedIn / X (Twitter)' section",
        no_entry_because="this check is a standing requirement, not something to "
                         "skip because nothing else prompted a look.",
        stale_because="a fresh LinkedIn/X check genuinely needs to happen this run, "
                      "not just be assumed unchanged from an old log entry.",
        unit="check", skip_tail=".")

    if report_path and os.path.exists(report_path):
        with open(report_path, "r", errors="ignore") as f:
            text = f.read()
        now = datetime.now()
        stale = []
        for m in SOCIAL_CITE.finditer(text):
            d = _parse(m.group(1))
            if d and (now - d).days > months * 30:
                stale.append((m.group(0), (now - d).days))
        if stale:
            for cite, age in stale:
                print(f"WARN: report cites {cite!r} which is {age} days old "
                      f"(> {months} months) — either this finding is still "
                      f"genuinely relevant (fine, but confirm deliberately) or it's "
                      f"a stale carryover from a prior run that should be dropped.")
        else:
            print(f"PASS: no LinkedIn/X citation in the report is older than "
                  f"{months} months")

    return ok
