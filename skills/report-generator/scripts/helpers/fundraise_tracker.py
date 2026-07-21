#!/usr/bin/env python3
"""
fundraise_tracker.py — maintain a small local log of capital the company (and
specifically the promoter/promoter group) has raised: preferential equity,
convertible warrants, NCDs/debentures, term loans, and promoter loans/guarantees.

This is what powers the "Promoter Fund Raises" part of the Promoter/Governance
Track Record section: instead of re-reading BSE/NSE announcements every time a
report is regenerated, each raise gets logged once to
~/.report-generator/research_cache/<company_slug>/fundraise_history.json, and this script reads
that small file back and flags patterns worth calling out (lapsed promoter
warrants above all — that's the single strongest governance red flag this
script exists to catch).

Why warrants get special treatment: under SEBI ICDR rules, a preferential
warrant holder pays only 25% upfront and has up to 18 months to pay the
remaining 75% and convert to equity. If the promoter lets warrants lapse
(walks away from that remaining 75%), they forfeit the 25% already paid —
which only makes sense if the promoter's own view of the stock soured after
allotment. That is a fact worth stating plainly, not softening.

Re-logging is safe: add-raise is idempotent on (date, instrument, allottee). The BSE
announcements sweep re-runs every regeneration and re-surfaces the same allotments, so
calling add-raise with a known raise is normal, not an error — an exact repeat is
skipped (leaving any status set via update-status untouched), while the same
date/instrument/allottee logged with different amounts/units/price is refused as a
conflict to re-check, since logging both would double-count it in the totals below.

Face value and stock splits — why `report --cmp`'s premium/discount figure is
face-value-normalized, not a raw price ratio. An issue price from years ago and
today's CMP are only directly comparable if the share's face value hasn't changed in
between; a stock split (e.g. 10:1, face value Rs.10 -> Rs.1) changes the *nominal*
price scale without changing anything real, and a raw "issue price vs current price"
percentage across a split is not just imprecise, it can have the wrong *sign* —
confirmed in practice: a pre-split preferential issue price naively compared to a
post-split CMP showed a "+285% premium" when the split-adjusted reality was a
discount. `--face-value` (on add-raise/update-price) records the face value that
priced *this specific raise*; `report --cmp-face-value` records the *current* face
value. `report` normalizes both sides to a multiple of face value before comparing,
and — this is the important part — refuses to print a premium/discount figure at all
if either face value is unknown, rather than silently computing a wrong percentage on
an unstated assumption that both sides share the same basis.

Runs entirely locally, no network required.

Usage:
    python3 fundraise_tracker.py <company_slug> add-raise \
        --date "2025-11-15" --instrument warrants --allottee promoter \
        --amount-cr 127.5 --units 1500000 --price-per-unit 850 --face-value 10 \
        --upfront-pct 25 --purpose "capex expansion" \
        --source "BSE announcement 15 Nov 2025"

    python3 fundraise_tracker.py <company_slug> update-status --id 0 \
        --status lapsed --note "Promoter did not pay remaining 75% within the 18-month window"

    python3 fundraise_tracker.py <company_slug> update-price --id 0 \
        --units 2481592 --price-per-unit 1694.50 --face-value 10 \
        --note "Price per BSE/NSE allotment notice, found after initial logging"

    python3 fundraise_tracker.py <company_slug> report --cmp 439.2 --cmp-face-value 1
"""
import argparse
import json
import os
import sys

INSTRUMENTS = [
    "preferential_equity", "warrants", "ncd", "term_loan",
    "promoter_loan", "rights_issue", "qip", "other",
]
ALLOTTEES = ["promoter", "promoter_group", "public", "institution", "mixed", "other"]
STATUSES = ["allotted", "pending", "converted", "lapsed", "outstanding", "repaid"]
PROMOTER_CATEGORIES = {"promoter", "promoter_group"}
DEBT_INSTRUMENTS = {"ncd", "term_loan", "promoter_loan"}


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "fundraise_history.json")


def load(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raises": []}


def save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_same_raise(raises, date, instrument, allottee):
    """A given allottee doesn't receive two separate allotments of the same instrument
    on the same date, so (date, instrument, allottee) is the natural key for a raise."""
    for r in raises:
        if (r["date"], r["instrument"], r["allottee"]) == (date, instrument, allottee):
            return r
    return None


def add_raise(args):
    path = cache_path(args.company_slug)
    data = load(path)

    # Idempotency guard. The 8-month unfiltered BSE sweep re-runs on every regeneration
    # and re-surfaces the same allotment announcements, so add-raise gets called with
    # already-logged raises routinely. Appending blindly would double-count them in
    # `report`'s promoter/debt totals -- i.e. silently overstate how much was raised.
    existing = find_same_raise(data["raises"], args.date, args.instrument, args.allottee)
    if existing and not args.force:
        # Deliberately does NOT compare status/note: those evolve legitimately via
        # update-status (a warrant goes pending -> converted/lapsed), and a re-log
        # must never reset that progress.
        same = (existing["amount_cr"] == args.amount_cr
                and existing["units"] == args.units
                and existing["price_per_unit"] == args.price_per_unit)
        if same:
            print(f"Already logged as #{existing['id']} ({existing['instrument']}, "
                  f"INR{existing['amount_cr']}cr, allottee={existing['allottee']}, "
                  f"{existing['date']}) — nothing to do. Existing status "
                  f"'{existing['status']}' left untouched.")
            return
        print(f"ERROR: #{existing['id']} already logs a {existing['instrument']} allotment "
              f"to {existing['allottee']} dated {existing['date']}, but with different "
              f"terms:\n"
              f"  logged: INR{existing['amount_cr']}cr / {existing['units']} units / "
              f"INR{existing['price_per_unit']} per unit\n"
              f"  now:    INR{args.amount_cr}cr / {args.units} units / "
              f"INR{args.price_per_unit} per unit\n"
              f"Re-read the allotment notice and confirm which is right — logging both "
              f"would double-count this raise in the promoter/debt totals. Pass --force "
              f"only if these are genuinely two separate allotments on the same date.",
              file=sys.stderr)
        sys.exit(1)

    default_status = "pending" if args.instrument == "warrants" else "allotted"
    entry = {
        "id": len(data["raises"]),
        "date": args.date,
        "instrument": args.instrument,
        "allottee": args.allottee,
        "amount_cr": args.amount_cr,
        "units": args.units,
        "price_per_unit": args.price_per_unit,
        "face_value": args.face_value,
        "upfront_pct": args.upfront_pct,
        "tenure": args.tenure,
        "rate_pct": args.rate_pct,
        "purpose": args.purpose or "",
        "source": args.source or "",
        "status": args.status or default_status,
        "note": args.note or "",
        "investors": args.investors or "",
    }
    data["raises"].append(entry)
    save(path, data)
    print(f"Logged raise #{entry['id']}: {args.instrument} / INR{args.amount_cr}cr "
          f"/ allottee={args.allottee} / status={entry['status']}")


def update_status(args):
    path = cache_path(args.company_slug)
    data = load(path)
    match = next((r for r in data["raises"] if r["id"] == args.id), None)
    if not match:
        print(f"No raise with id={args.id} found for {args.company_slug}.")
        return
    old_status = match["status"]
    match["status"] = args.status
    if args.note:
        match["note"] = (match["note"] + " " if match["note"] else "") + args.note
    save(path, data)
    print(f"Raise #{args.id} ({match['instrument']}, INR{match['amount_cr']}cr): "
          f"status {old_status} -> {args.status}")


def update_price(args):
    """Backfill units/price-per-unit/face-value on an already-logged raise. Exists
    because the source available at add-raise time (often just an investor
    presentation's aggregate-amount slide) frequently doesn't carry the per-share
    price, but the actual BSE/NSE allotment notice or contemporaneous press coverage
    often does — found later, once someone goes looking specifically for it. Only
    touches units/price_per_unit/face_value (and appends to note, same as
    update-status); never touches amount_cr, since a price discrepancy against the
    originally-logged amount is a finding to state in the note, not a reason to
    silently overwrite the amount a primary company source already gave."""
    path = cache_path(args.company_slug)
    data = load(path)
    match = next((r for r in data["raises"] if r["id"] == args.id), None)
    if not match:
        print(f"No raise with id={args.id} found for {args.company_slug}.")
        return
    if args.units is not None:
        match["units"] = args.units
    if args.price_per_unit is not None:
        match["price_per_unit"] = args.price_per_unit
    if args.face_value is not None:
        match["face_value"] = args.face_value
    if args.note:
        match["note"] = (match["note"] + " " if match["note"] else "") + args.note
    save(path, data)
    print(f"Raise #{args.id} ({match['instrument']}, INR{match['amount_cr']}cr): "
          f"units={match['units']}, price_per_unit={match['price_per_unit']}, "
          f"face_value={match.get('face_value')}")


def report(args):
    path = cache_path(args.company_slug)
    data = load(path)
    raises = data["raises"]
    if not raises:
        print("No fund raises logged yet for this company.")
        return

    promoter_raises = [r for r in raises if r["allottee"] in PROMOTER_CATEGORIES]
    debt_raises = [r for r in raises if r["instrument"] in DEBT_INSTRUMENTS]
    lapsed_promoter_warrants = [
        r for r in raises
        if r["instrument"] == "warrants" and r["allottee"] in PROMOTER_CATEGORIES
        and r["status"] == "lapsed"
    ]

    print(f"All logged fund raises ({len(raises)} total):")
    for r in raises:
        price_bit = f" @ INR{r['price_per_unit']}/unit" if r.get("price_per_unit") else ""
        if r.get("price_per_unit"):
            price_bit += f" (FV Rs.{r['face_value']})" if r.get("face_value") else " (FV unknown)"
        premium_bit = ""
        if args.cmp and r.get("price_per_unit"):
            if r.get("face_value") and args.cmp_face_value:
                # Normalize both sides to "multiple of face value" before comparing
                # — a raw price ratio is only valid if face value hasn't changed
                # since this raise (see module docstring's "Face value and stock
                # splits" note). A split between the raise and today changes the
                # nominal price scale on one side only, and comparing the raw
                # numbers directly can flip the sign of the result, not just its
                # magnitude.
                then_multiple = r["price_per_unit"] / r["face_value"]
                now_multiple = args.cmp / args.cmp_face_value
                delta_pct = (then_multiple - now_multiple) / now_multiple * 100
                premium_bit = (f" ({delta_pct:+.1f}% vs current price INR{args.cmp}, "
                               f"face-value-normalized)")
            else:
                premium_bit = (" (premium/discount not shown — face value at issue "
                               "and/or --cmp-face-value not given; a raw price "
                               "comparison risks the wrong sign across a stock "
                               "split, see module docstring)")
        print(f"  #{r['id']} {r['date']} — {r['instrument']} — INR{r['amount_cr']}cr "
              f"— allottee: {r['allottee']}{price_bit}{premium_bit} — status: {r['status'].upper()}")
        if r.get("investors"):
            print(f"      investors: {r['investors']}")
        if r.get("note"):
            print(f"      note: {r['note']}")

    promoter_total = sum(r["amount_cr"] for r in promoter_raises)
    debt_total = sum(r["amount_cr"] for r in debt_raises)
    print(f"\nTotal raised with promoter/promoter-group as allottee: INR{promoter_total:.1f}cr "
          f"across {len(promoter_raises)} instrument(s).")
    print(f"Total raised via debt instruments (NCD/term loan/promoter loan): "
          f"INR{debt_total:.1f}cr across {len(debt_raises)} instrument(s).")

    if lapsed_promoter_warrants:
        print(f"\nFLAG: {len(lapsed_promoter_warrants)} promoter/promoter-group warrant "
              f"allotment(s) LAPSED (forfeited upfront payment rather than converting). "
              f"State this plainly in the Promoter/Governance section — this is a direct "
              f"signal the promoter's own conviction changed after allotment.")
    else:
        pending = [r for r in raises if r["instrument"] == "warrants" and r["status"] == "pending"]
        if pending:
            print(f"\n{len(pending)} warrant allotment(s) still pending conversion — "
                  f"note the conversion deadline in the report and re-check on next refresh.")
        else:
            print("\nNo lapsed promoter warrants on record.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-raise")
    p1.add_argument("--date", required=True, help='e.g. "2025-11-15" or "Q2 FY26"')
    p1.add_argument("--instrument", required=True, choices=INSTRUMENTS)
    p1.add_argument("--allottee", required=True, choices=ALLOTTEES)
    p1.add_argument("--amount-cr", type=float, required=True)
    p1.add_argument("--units", type=int, help="number of shares/warrants/debentures allotted")
    p1.add_argument("--price-per-unit", type=float, help="issue price per share/warrant, INR")
    p1.add_argument("--face-value", type=float,
                     help="face value per share at the time of THIS raise, INR (e.g. 10) — "
                          "needed to compare this raise's price against a current CMP that "
                          "may be on a different face value after a stock split; see module "
                          "docstring's 'Face value and stock splits' note")
    p1.add_argument("--upfront-pct", type=float,
                     help="pct paid upfront (relevant for warrants, typically 25 per SEBI ICDR)")
    p1.add_argument("--tenure", help='for debt, e.g. "5 years"')
    p1.add_argument("--rate-pct", type=float, help="coupon/interest rate pct, for debt instruments")
    p1.add_argument("--purpose")
    p1.add_argument("--source", help="citation, e.g. \"BSE announcement 15 Nov 2025\"")
    p1.add_argument("--status", choices=STATUSES,
                     help="defaults to 'pending' for warrants, 'allotted' for everything else")
    p1.add_argument("--investors",
                     help="named individual/institutional investors who participated, comma-"
                          "separated, e.g. \"Rakesh Jhunjhunwala, Nomura, ICICI Prudential MF\" "
                          "— only named allottees actually disclosed in the BSE/NSE allotment "
                          "notice or shareholding pattern, never inferred")
    p1.add_argument("--note")
    p1.add_argument("--force", action="store_true",
                     help="append even if a raise for this date/instrument/allottee "
                          "already exists (see the dedupe note in this file's docstring)")
    p1.set_defaults(func=add_raise)

    p2 = sub.add_parser("update-status")
    p2.add_argument("--id", type=int, required=True, help="id shown in `report` output")
    p2.add_argument("--status", required=True, choices=STATUSES)
    p2.add_argument("--note")
    p2.set_defaults(func=update_status)

    p2b = sub.add_parser("update-price")
    p2b.add_argument("--id", type=int, required=True, help="id shown in `report` output")
    p2b.add_argument("--units", type=int, help="number of shares/warrants/debentures allotted")
    p2b.add_argument("--price-per-unit", type=float, help="issue price per share/warrant, INR")
    p2b.add_argument("--face-value", type=float,
                      help="face value per share at the time of this raise, INR — see "
                           "add-raise's --face-value help")
    p2b.add_argument("--note")
    p2b.set_defaults(func=update_price)

    p3 = sub.add_parser("report")
    p3.add_argument("--cmp", type=float,
                     help="current market price — if given (with --cmp-face-value), shows "
                          "each issue price as a face-value-normalized premium/discount to CMP")
    p3.add_argument("--cmp-face-value", type=float,
                     help="the share's CURRENT face value, INR — required alongside --cmp to "
                          "show a premium/discount figure at all; without it, report prints "
                          "the raw issue price only rather than risk a wrong-sign comparison "
                          "across an intervening stock split")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
