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

Runs entirely locally, no network required.

Usage:
    python3 fundraise_tracker.py <company_slug> add-raise \
        --date "2025-11-15" --instrument warrants --allottee promoter \
        --amount-cr 127.5 --units 1500000 --price-per-unit 850 \
        --upfront-pct 25 --purpose "capex expansion" \
        --source "BSE announcement 15 Nov 2025"

    python3 fundraise_tracker.py <company_slug> update-status --id 0 \
        --status lapsed --note "Promoter did not pay remaining 75% within the 18-month window"

    python3 fundraise_tracker.py <company_slug> report [--cmp 910]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_context import get_run_id  # noqa: E402

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


def add_raise(args):
    path = cache_path(args.company_slug)
    data = load(path)
    default_status = "pending" if args.instrument == "warrants" else "allotted"
    entry = {
        "id": len(data["raises"]),
        "date": args.date,
        "instrument": args.instrument,
        "allottee": args.allottee,
        "amount_cr": args.amount_cr,
        "units": args.units,
        "price_per_unit": args.price_per_unit,
        "upfront_pct": args.upfront_pct,
        "tenure": args.tenure,
        "rate_pct": args.rate_pct,
        "purpose": args.purpose or "",
        "source": args.source or "",
        "status": args.status or default_status,
        "note": args.note or "",
        "investors": args.investors or "",
        "run_id": get_run_id(),
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
        premium_bit = ""
        if args.cmp and r.get("price_per_unit"):
            delta_pct = (r["price_per_unit"] - args.cmp) / args.cmp * 100
            premium_bit = f" ({delta_pct:+.1f}% vs current price INR{args.cmp})"
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
    p1.set_defaults(func=add_raise)

    p2 = sub.add_parser("update-status")
    p2.add_argument("--id", type=int, required=True, help="id shown in `report` output")
    p2.add_argument("--status", required=True, choices=STATUSES)
    p2.add_argument("--note")
    p2.set_defaults(func=update_status)

    p3 = sub.add_parser("report")
    p3.add_argument("--cmp", type=float,
                     help="current market price — if given, shows each issue price as a "
                          "premium/discount to CMP")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
