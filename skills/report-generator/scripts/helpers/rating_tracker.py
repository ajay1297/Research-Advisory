#!/usr/bin/env python3
"""
rating_tracker.py — maintain a small local log of credit rating actions from
rating agencies (CRISIL, ICRA, CARE, India Ratings, Acuite, Brickwork, etc.) on
a company's bank facilities / NCDs / commercial paper, and flag downgrades or
negative-outlook actions plainly.

Why this exists: rating rationale documents are one of the few genuinely
independent, professionally-underwritten data sources in this whole pipeline —
unlike the concall (management's own words) or screener.in (aggregated public
filings), a rating agency's rationale is a third party's own credit assessment,
often including a liquidity view, leverage/coverage trend, and related-party or
promoter-support commentary the company itself would not volunteer. A
downgrade or a negative outlook/rating-watch action is a first-class, citable
risk signal, not something to soften.

This script deliberately does NOT try to auto-detect upgrade/downgrade by
parsing rating notches itself (long-term and short-term scales differ, and
notch comparison across agencies is not always apples-to-apples) — the caller
(Claude, drafting the report, having just read the actual rationale) states
the action explicitly via --action. The script's job is just to keep the
history and flag the current state plainly.

Re-logging is safe: add-rating is idempotent on (agency, date, instrument). The
18-month Credit Rating sweep re-runs every regeneration and returns actions already
on file, so calling add-rating with a known action is normal, not an error — an exact
repeat is skipped with a message, while the same agency/date/instrument logged with
*different* terms is refused as a conflict to re-check (--force to override).

Runs entirely locally, no network required.

Usage:
    python3 rating_tracker.py <company_slug> add-rating \
        --agency crisil --date "2026-03-15" --instrument "long-term bank facilities" \
        --rating "A-" --outlook stable --action reaffirmed \
        --note "Liquidity assessed as adequate; no promoter guarantee flagged." \
        --source "CRISIL Ratings rationale, 15 Mar 2026"

    python3 rating_tracker.py <company_slug> report
"""
import argparse
import json
import os
import sys

AGENCIES = ["crisil", "icra", "care", "india_ratings", "acuite", "brickwork", "other"]
OUTLOOKS = ["stable", "positive", "negative", "watch_developing",
            "watch_negative", "watch_positive", "na"]
ACTIONS = ["first_time", "reaffirmed", "upgrade", "downgrade",
           "outlook_revised_positive", "outlook_revised_negative", "withdrawn"]
NEGATIVE_OUTLOOKS = {"negative", "watch_negative"}
NEGATIVE_ACTIONS = {"downgrade", "outlook_revised_negative"}


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "rating_history.json")


def load(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ratings": []}


def save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_same_action(ratings, agency, date, instrument):
    """An agency does not issue two different actions on the same instrument on the
    same day, so (agency, date, instrument) is the natural key for a rating action."""
    for r in ratings:
        if (r["agency"], r["date"], r["instrument"]) == (agency, date, instrument):
            return r
    return None


def add_rating(args):
    path = cache_path(args.company_slug)
    data = load(path)

    # Idempotency guard. The 18-month "Credit Rating" BSE sweep re-runs on every
    # regeneration and returns the same actions again, so add-rating is called with
    # already-logged actions as a matter of course, not by mistake. Appending blindly
    # would duplicate them and make `report` double-count the in-force set.
    existing = find_same_action(data["ratings"], args.agency, args.date, args.instrument)
    if existing and not args.force:
        same = (existing["rating"] == args.rating
                and existing["outlook"] == args.outlook
                and existing["action"] == args.action)
        if same:
            print(f"Already logged as #{existing['id']} ({existing['agency'].upper()} "
                  f"{existing['rating']}/{existing['outlook']} on {existing['instrument']}, "
                  f"{existing['date']}) — nothing to do.")
            return
        # Same agency/date/instrument but different terms: a correction, a misread of
        # the rationale, or two genuinely distinct same-day actions. Don't guess.
        print(f"ERROR: #{existing['id']} already logs {existing['agency'].upper()} on "
              f"{existing['instrument']} dated {existing['date']}, but with different "
              f"terms:\n"
              f"  logged: {existing['rating']} / {existing['outlook']} / {existing['action']}\n"
              f"  now:    {args.rating} / {args.outlook} / {args.action}\n"
              f"Re-read the rationale and confirm which is right. Pass --force to append "
              f"this as a separate action anyway (correct only if the agency genuinely "
              f"took two distinct actions on this instrument that day).", file=sys.stderr)
        sys.exit(1)

    entry = {
        "id": len(data["ratings"]),
        "date": args.date,
        "agency": args.agency,
        "instrument": args.instrument,
        "rating": args.rating,
        "outlook": args.outlook,
        "action": args.action,
        "note": args.note or "",
        "source": args.source or "",
    }
    data["ratings"].append(entry)
    save(path, data)
    print(f"Logged rating #{entry['id']}: {args.agency.upper()} {args.rating} "
          f"({args.outlook}) on {args.instrument} — action: {args.action}")


def report(args):
    path = cache_path(args.company_slug)
    data = load(path)
    ratings = data["ratings"]
    if not ratings:
        print("No rating actions logged yet for this company.")
        return

    print(f"All logged rating actions ({len(ratings)} total), oldest first:")
    for r in ratings:
        print(f"  #{r['id']} {r['date']} — {r['agency'].upper()} — {r['instrument']} "
              f"— {r['rating']} / {r['outlook'].upper()} — action: {r['action'].upper()}")
        if r.get("note"):
            print(f"      note: {r['note']}")

    # Latest entry per (agency, instrument) pair is what's "currently in force".
    latest = {}
    for r in ratings:
        key = (r["agency"], r["instrument"])
        if key not in latest or r["id"] > latest[key]["id"]:
            latest[key] = r

    print("\nCurrently in force (latest action per agency/instrument):")
    flags = []
    for (agency, instrument), r in latest.items():
        print(f"  {agency.upper()} — {instrument}: {r['rating']} / {r['outlook'].upper()} "
              f"(as of {r['date']}, last action: {r['action'].upper()})")
        if r["outlook"] in NEGATIVE_OUTLOOKS or r["action"] in NEGATIVE_ACTIONS:
            flags.append(r)

    if flags:
        print(f"\nFLAG: {len(flags)} instrument(s) currently carry a DOWNGRADE and/or "
              f"NEGATIVE/WATCH-NEGATIVE outlook from a rating agency. State this plainly "
              f"in the Promoter/Governance section — an independent rating agency's own "
              f"credit view is one of the few third-party signals in this report, and a "
              f"negative action deserves at least as much weight as management's own "
              f"guidance commentary.")
    else:
        print("\nNo downgrade or negative/watch-negative outlook currently in force.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-rating")
    p1.add_argument("--agency", required=True, choices=AGENCIES)
    p1.add_argument("--date", required=True, help='e.g. "2026-03-15"')
    p1.add_argument("--instrument", required=True,
                     help='e.g. "long-term bank facilities", "NCD", "commercial paper"')
    p1.add_argument("--rating", required=True, help='e.g. "A-", "BBB+", "A1+"')
    p1.add_argument("--outlook", required=True, choices=OUTLOOKS)
    p1.add_argument("--action", required=True, choices=ACTIONS)
    p1.add_argument("--note")
    p1.add_argument("--source", help='e.g. "CRISIL Ratings rationale, 15 Mar 2026"')
    p1.add_argument("--force", action="store_true",
                     help="append even if an action for this agency/date/instrument "
                          "already exists (see the dedupe note in this file's docstring)")
    p1.set_defaults(func=add_rating)

    p2 = sub.add_parser("report")
    p2.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
