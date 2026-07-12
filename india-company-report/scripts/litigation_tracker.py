#!/usr/bin/env python3
"""
litigation_tracker.py — maintain a small local log of court cases, tax
disputes, and other legal proceedings disclosed against (or occasionally by)
the company, and flag anything that is still open or could be reopened.

Why this exists: annual reports disclose pending litigation/tax disputes as
"Contingent Liabilities" every year, but a case that was dismissed or decided
in the company's favor at a lower forum is not necessarily over — many such
matters remain open to appeal by the other side (typically the tax/regulatory
authority) for a defined limitation period. A report that only checks "is
there litigation right now" and stops can miss exactly this: an old,
seemingly-closed matter that is still reopenable and therefore still a real
contingent liability. This script exists to keep that distinction explicit
across refreshes, not to re-derive it from scratch each time.

Runs entirely locally, no network required.

Usage:
    # log a case found in an annual report's contingent-liabilities note,
    # a BSE/NSE Regulation 30 disclosure, or news coverage
    python3 litigation_tracker.py <company_slug> add-case \
        --case-ref "GST demand FY19-20" --forum "GST Appellate Tribunal" \
        --case-type tax_dispute --parties "Company vs GST Department" \
        --amount-cr 4.2 --status ongoing \
        --note "Demand relates to input tax credit disallowance" \
        --source "FY26 Annual Report, Note 34 - Contingent Liabilities"

    # update status once an outcome or appeal is known
    python3 litigation_tracker.py <company_slug> update-status --id 0 \
        --status dismissed_appealable \
        --note "Tribunal ruled in company's favor Mar 2026; department has 90 days to appeal to High Court"

    # print the full case list with flags
    python3 litigation_tracker.py <company_slug> report
"""
import argparse
import json
import os

CASE_TYPES = ["tax_dispute", "customer_vendor_dispute", "regulatory", "labor",
              "ip", "criminal", "arbitration", "consumer", "promoter_related", "other"]
STATUSES = ["ongoing", "disposed_favorable", "disposed_unfavorable",
            "settled", "dismissed_appealable", "closed_final"]
OPEN_OR_REOPENABLE = {"ongoing", "dismissed_appealable"}


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "litigation_history.json")


def load(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cases": []}


def save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_case(args):
    path = cache_path(args.company_slug)
    data = load(path)
    entry = {
        "id": len(data["cases"]),
        "case_ref": args.case_ref,
        "forum": args.forum,
        "case_type": args.case_type,
        "parties": args.parties,
        "amount_cr": args.amount_cr,
        "status": args.status,
        "appeal_window": args.appeal_window or "",
        "note": args.note or "",
        "source": args.source or "",
    }
    data["cases"].append(entry)
    save(path, data)
    print(f"Logged case #{entry['id']}: {args.case_ref} ({args.case_type}) — status: {args.status}")


def update_status(args):
    path = cache_path(args.company_slug)
    data = load(path)
    match = next((c for c in data["cases"] if c["id"] == args.id), None)
    if not match:
        print(f"No case with id={args.id} found for {args.company_slug}.")
        return
    old_status = match["status"]
    match["status"] = args.status
    if args.note:
        match["note"] = (match["note"] + " " if match["note"] else "") + args.note
    if args.appeal_window:
        match["appeal_window"] = args.appeal_window
    save(path, data)
    print(f"Case #{args.id} ({match['case_ref']}): status {old_status} -> {args.status}")


def report(args):
    path = cache_path(args.company_slug)
    data = load(path)
    cases = data["cases"]
    if not cases:
        print("No litigation/legal cases logged yet for this company.")
        return

    print(f"All logged cases ({len(cases)} total):")
    for c in cases:
        amount_bit = f" — INR{c['amount_cr']}cr" if c.get("amount_cr") is not None else " — amount not disclosed"
        print(f"  #{c['id']} {c['case_ref']} ({c['case_type']}, {c['forum']}){amount_bit} — "
              f"status: {c['status'].upper()}")
        print(f"      parties: {c['parties']}")
        if c.get("appeal_window"):
            print(f"      appeal window: {c['appeal_window']}")
        if c.get("note"):
            print(f"      note: {c['note']}")

    open_cases = [c for c in cases if c["status"] in OPEN_OR_REOPENABLE]
    reopenable = [c for c in cases if c["status"] == "dismissed_appealable"]
    total_disclosed_amount = sum(c["amount_cr"] for c in open_cases if c.get("amount_cr") is not None)

    print(f"\n{len(open_cases)} of {len(cases)} case(s) are currently OPEN or REOPENABLE "
          f"(status: ongoing / dismissed_appealable).")
    if total_disclosed_amount:
        print(f"Total disclosed contingent-liability amount across open/reopenable cases with a "
              f"stated figure: INR{total_disclosed_amount:.2f}cr (cases without a disclosed amount "
              f"are not included in this sum).")

    if reopenable:
        print(f"\nFLAG: {len(reopenable)} case(s) are DISMISSED/DECIDED BUT STILL APPEALABLE — "
              f"i.e. a matter that looks closed today could reopen within its appeal window. "
              f"State this plainly in the Legal & Litigation section rather than describing these "
              f"as resolved.")
    elif open_cases:
        print(f"\n{len(open_cases)} case(s) remain ongoing; none are currently in a "
              f"dismissed-but-appealable state.")
    else:
        print("\nNo open or reopenable litigation currently on record.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-case")
    p1.add_argument("--case-ref", required=True, help='e.g. "GST demand FY19-20"')
    p1.add_argument("--forum", required=True, help='e.g. "GST Appellate Tribunal", "Calcutta High Court"')
    p1.add_argument("--case-type", required=True, choices=CASE_TYPES)
    p1.add_argument("--parties", required=True, help='e.g. "Company vs GST Department"')
    p1.add_argument("--amount-cr", type=float, help="disclosed contingent liability amount, INR crore")
    p1.add_argument("--status", required=True, choices=STATUSES)
    p1.add_argument("--appeal-window", help='e.g. "appeal period expires Sep 2027"')
    p1.add_argument("--note")
    p1.add_argument("--source", help='e.g. "FY26 Annual Report, Note 34"')
    p1.set_defaults(func=add_case)

    p2 = sub.add_parser("update-status")
    p2.add_argument("--id", type=int, required=True)
    p2.add_argument("--status", required=True, choices=STATUSES)
    p2.add_argument("--appeal-window")
    p2.add_argument("--note")
    p2.set_defaults(func=update_status)

    p3 = sub.add_parser("report")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
