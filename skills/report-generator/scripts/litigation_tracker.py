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

Re-logging is safe: add-case is idempotent on (case_ref, forum), compared
case/whitespace-insensitively since both are free text re-typed from each year's
annual report. The same contingent liability is re-disclosed annually, so re-logging
is routine — an exact repeat is skipped (leaving any status set via update-status
untouched), and a restated amount is refused with a pointer to `update-status
--amount-cr`, which revises the figure in place instead of double-counting it.

Runs entirely locally, no network required.

Usage:
    python3 litigation_tracker.py <company_slug> add-case \
        --case-ref "GST demand FY19-20" --forum "GST Appellate Tribunal" \
        --case-type tax_dispute --parties "Company vs GST Department" \
        --amount-cr 4.2 --status ongoing \
        --note "Demand relates to input tax credit disallowance" \
        --source "FY26 Annual Report, Note 34 - Contingent Liabilities"

    python3 litigation_tracker.py <company_slug> update-status --id 0 \
        --status dismissed_appealable \
        --note "Tribunal ruled in company's favor Mar 2026; department has 90 days to appeal to High Court"

    python3 litigation_tracker.py <company_slug> report
"""
import argparse
import json
import os
import sys

CASE_TYPES = ["tax_dispute", "customer_vendor_dispute", "regulatory", "labor",
              "ip", "criminal", "arbitration", "consumer", "promoter_related", "other"]
STATUSES = ["ongoing", "disposed_favorable", "disposed_unfavorable",
            "settled", "dismissed_appealable", "closed_final"]
OPEN_OR_REOPENABLE = {"ongoing", "dismissed_appealable"}


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
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


def norm(s):
    """Case refs and forums are free text re-typed from each year's annual report, so
    compare them case- and whitespace-insensitively."""
    return " ".join((s or "").lower().split())


def find_same_case(cases, case_ref, forum):
    for c in cases:
        if (norm(c["case_ref"]), norm(c["forum"])) == (norm(case_ref), norm(forum)):
            return c
    return None


def add_case(args):
    path = cache_path(args.company_slug)
    data = load(path)

    # Idempotency guard. Contingent liabilities are re-disclosed in every annual report,
    # so the same case is re-read and re-logged on each refresh by design. Appending
    # blindly would double-count it in `report`'s total disclosed contingent-liability
    # figure -- i.e. silently overstate the company's legal exposure.
    existing = find_same_case(data["cases"], args.case_ref, args.forum)
    if existing and not args.force:
        # Deliberately does NOT compare status/appeal_window/note: those evolve
        # legitimately via update-status, and a re-log must never reset that progress.
        same = (existing["case_type"] == args.case_type
                and norm(existing["parties"]) == norm(args.parties)
                and existing["amount_cr"] == args.amount_cr)
        if same:
            print(f"Already logged as #{existing['id']} ({existing['case_ref']}, "
                  f"{existing['forum']}) — nothing to do. Existing status "
                  f"'{existing['status']}' left untouched.")
            return
        amount_changed = existing["amount_cr"] != args.amount_cr
        print(f"ERROR: #{existing['id']} already logs '{existing['case_ref']}' at "
              f"{existing['forum']}, but with different details:\n"
              f"  logged: {existing['case_type']} / {existing['parties']} / "
              f"INR{existing['amount_cr']}cr\n"
              f"  now:    {args.case_type} / {args.parties} / INR{args.amount_cr}cr\n"
              + (f"The amount changed, which is normal — a contingent liability is "
                 f"restated each year as interest/penalty accrues. Update the existing "
                 f"case in place rather than adding a second one:\n"
                 f"  litigation_tracker.py {args.company_slug} update-status --id "
                 f"{existing['id']} --status {existing['status']} --amount-cr "
                 f"{args.amount_cr}\n"
                 if amount_changed else
                 f"Re-read the disclosure and confirm which is right.\n")
              + f"Pass --force only if this is genuinely a separate case that happens to "
                f"share a reference and forum.", file=sys.stderr)
        sys.exit(1)

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
    old_amount = match.get("amount_cr")
    if args.amount_cr is not None:
        match["amount_cr"] = args.amount_cr
    save(path, data)
    msg = f"Case #{args.id} ({match['case_ref']}): status {old_status} -> {args.status}"
    if args.amount_cr is not None and args.amount_cr != old_amount:
        msg += f", amount INR{old_amount}cr -> INR{args.amount_cr}cr"
    print(msg)


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
    p1.add_argument("--force", action="store_true",
                     help="append even if a case with this ref/forum already exists "
                          "(see the dedupe note in this file's docstring)")
    p1.set_defaults(func=add_case)

    p2 = sub.add_parser("update-status")
    p2.add_argument("--id", type=int, required=True)
    p2.add_argument("--status", required=True, choices=STATUSES)
    p2.add_argument("--appeal-window")
    p2.add_argument("--amount-cr", type=float,
                     help="revised contingent-liability amount, INR crore — use this when "
                          "a new annual report restates the figure, rather than logging "
                          "the case a second time")
    p2.add_argument("--note")
    p2.set_defaults(func=update_status)

    p3 = sub.add_parser("report")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
