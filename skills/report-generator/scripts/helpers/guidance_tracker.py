#!/usr/bin/env python3
"""
guidance_tracker.py — maintain a small local log of what management guided vs. what
was actually delivered, one entry per quarter, and flag a pattern of missed guidance.

This is what powers the "Promoter / Governance Track Record" section (guidance vs.
actual, beat/met/miss) AND the status pointer shown on every Near/Medium/Long Term
outlook bullet (Pending / On Track / Delivered / Delayed / Missed) — instead of
re-reading old transcripts every time a report is regenerated, each report run adds
one entry to ~/.report-generator/research_cache/<company>/guidance_history.json, and this script reads
that small file back.

Two ways an entry gets used:

1. Numeric metric vs. actual (original use) — add-guidance + add-actual for the same
   --metric/--for-period auto-computes a beat/met/miss delta. Still works exactly as
   before; --value-cr stays required for this path.

2. Status-tracked outlook items (for Near/Medium/Long Term bullet pointers) — every
   guided item drafted into the outlook (a revenue number, a facility launch, a TAM
   capture target, a 5-year CAGR aspiration — anything, not just financial metrics)
   gets logged with an explicit --status you assess yourself from what the sources
   say (never auto-derived — the underlying claims are too heterogeneous: a revenue
   miss is comparable across quarters, but "is the Pune facility on track" isn't a
   number you can diff). Use --supersedes-id when a later concall revises an earlier
   guided item (raises/lowers a target, pushes out a date, etc.) so `report` can
   reconstruct the full evolution — "at Q3 FY26 call guided X, at Q4 FY26 call
   revised to Y" — the same way a human analyst would read back through a company's
   guidance history.

Runs entirely locally, no network required.

Usage:
    python3 guidance_tracker.py <slug> add-guidance --given-in "Q4 FY26" --for-period "FY27" \
        --metric revenue --value-cr 2400 --status pending \
        --note "revised FY27 guidance, high probability of further upward revision"
    python3 guidance_tracker.py <slug> add-actual --period "FY27" --metric revenue --value-cr 2510

    python3 guidance_tracker.py <slug> add-guidance --given-in "Q3 FY26" --for-period "FY27-FY29" \
        --metric assembly_business_revenue --status pending \
        --note "New assembly business over 3 years: Rs250-300cr (FY27 Rs70-75cr, FY28 Rs150-200cr, FY29 Rs250-300cr)"

    python3 guidance_tracker.py <slug> add-guidance --given-in "Q4 FY26" --for-period "2-3 years" \
        --metric assembly_business_revenue --status on_track --supersedes-id 3 \
        --note "Revised to Rs250-350cr over a 2-3 year period"

    python3 guidance_tracker.py <slug> report
"""
import argparse
import json
import os

MISS_THRESHOLD_PCT = 10.0  # actual more than this % below guidance counts as a miss
STATUSES = ["pending", "on_track", "delivered", "delayed", "missed"]


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "guidance_history.json")


def load(path: str):
    if os.path.exists(path):
        data = json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else {}
    else:
        data = {}
    data.setdefault("guidances", [])
    data.setdefault("actuals", [])
    # Migrate entries written before "id"/"status"/"supersedes_id" existed (older
    # guidance_history.json files) so chain-building never KeyErrors on them.
    for i, g in enumerate(data["guidances"]):
        g.setdefault("id", i)
        g.setdefault("status", None)
        g.setdefault("supersedes_id", None)
        g.setdefault("value_cr", g.get("value_cr"))
    return data


def save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_guidance(args):
    path = cache_path(args.company_slug)
    data = load(path)
    entry = {
        "id": len(data["guidances"]),
        "given_in": args.given_in,
        "for_period": args.for_period,
        "metric": args.metric,
        "value_cr": args.value_cr,
        "status": args.status,
        "supersedes_id": args.supersedes_id,
        "note": args.note or "",
    }
    data["guidances"].append(entry)
    save(path, data)
    value_bit = f"{args.value_cr}cr" if args.value_cr is not None else "(non-numeric item)"
    print(f"Logged guidance #{entry['id']}: {args.metric}={value_bit} for {args.for_period} "
          f"(given in {args.given_in}) — status: {args.status}"
          + (f", supersedes #{args.supersedes_id}" if args.supersedes_id is not None else ""))


def add_actual(args):
    path = cache_path(args.company_slug)
    data = load(path)
    entry = {"period": args.period, "metric": args.metric, "value_cr": args.value_cr}
    match = next((g for g in data["guidances"]
                  if g["for_period"] == args.period and g["metric"] == args.metric), None)
    if match:
        delta_pct = (args.value_cr - match["value_cr"]) / match["value_cr"] * 100
        entry["guided_value_cr"] = match["value_cr"]
        entry["guided_in"] = match["given_in"]
        entry["delta_pct"] = round(delta_pct, 1)
        entry["verdict"] = (
            "beat" if delta_pct > 1 else
            "miss" if delta_pct < -MISS_THRESHOLD_PCT else
            "met"
        )
        print(f"{args.period} {args.metric}: actual {args.value_cr}cr vs guided "
              f"{match['value_cr']}cr ({match['given_in']}) -> {entry['delta_pct']:+.1f}% "
              f"= {entry['verdict'].upper()}")
    else:
        entry["verdict"] = "no_prior_guidance"
        print(f"{args.period} {args.metric}: actual {args.value_cr}cr — no matching prior "
              f"guidance found to compare against")
    data["actuals"].append(entry)
    save(path, data)


def link_entry(args):
    path = cache_path(args.company_slug)
    data = load(path)
    match = next((g for g in data["guidances"] if g["id"] == args.id), None)
    if not match:
        print(f"No guidance entry with id={args.id} found for {args.company_slug}.")
        return
    if args.status:
        match["status"] = args.status
    if args.supersedes_id is not None:
        match["supersedes_id"] = args.supersedes_id
    save(path, data)
    print(f"Updated entry #{args.id}: status={match['status']}, "
          f"supersedes_id={match['supersedes_id']}")


def _build_chains(guidances):
    """Group guidance entries into chains via supersedes_id, oldest first per chain."""
    by_id = {g["id"]: g for g in guidances}
    superseded_ids = {g["supersedes_id"] for g in guidances if g.get("supersedes_id") is not None}
    chain_heads = [g for g in guidances if g["id"] not in superseded_ids]
    chains = []
    for head in chain_heads:
        chain = [head]
        current = head
        while current.get("supersedes_id") is not None and current["supersedes_id"] in by_id:
            current = by_id[current["supersedes_id"]]
            chain.append(current)
        chain.reverse()  # oldest first
        chains.append(chain)
    return chains


def report(args):
    path = cache_path(args.company_slug)
    data = load(path)

    tracked = [a for a in data["actuals"] if "verdict" in a and a["verdict"] != "no_prior_guidance"]
    tracked = tracked[-args.lookback:]
    if tracked:
        misses = [a for a in tracked if a["verdict"] == "miss"]
        print(f"Last {len(tracked)} tracked guidance-vs-actual calls:")
        for a in tracked:
            print(f"  {a['period']} {a['metric']}: guided {a['guided_value_cr']}cr "
                  f"({a['guided_in']}) -> actual {a['value_cr']}cr "
                  f"({a['delta_pct']:+.1f}%) = {a['verdict'].upper()}")
        if len(misses) >= 2:
            print(f"\nFLAG: {len(misses)} of the last {len(tracked)} tracked guidance calls "
                  f"were missed by more than {MISS_THRESHOLD_PCT}%. State this plainly in "
                  f"the Promoter/Governance section.")
        else:
            print(f"\n{len(misses)} of the last {len(tracked)} tracked guidance calls missed "
                  f"by more than {MISS_THRESHOLD_PCT}% — no strong pattern of over-promising "
                  f"based on tracked history so far.")
    else:
        print("No guidance-vs-actual metric comparisons logged yet for this company.")

    guidances = [g for g in data["guidances"] if g.get("status") is not None]
    if guidances:
        print(f"\nStatus-tracked outlook items ({len(guidances)} entries, "
              f"not lookback-limited — full history shown):")
        for chain in _build_chains(guidances):
            latest = chain[-1]
            print(f"\n  Item: {latest['metric']}  [current status: {latest['status'].upper()}]")
            for g in chain:
                value_bit = f"{g['value_cr']}cr" if g.get("value_cr") is not None else ""
                print(f"    - {g['given_in']} (for {g['for_period']}): {value_bit} "
                      f"{g['note']}".rstrip())
    else:
        print("\nNo status-tracked outlook items logged yet for this company.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-guidance")
    p1.add_argument("--given-in", required=True, help='e.g. "Q4 FY26"')
    p1.add_argument("--for-period", required=True, help='e.g. "FY27"')
    p1.add_argument("--metric", required=True,
                     help='e.g. "revenue", or a short slug for a non-numeric outlook item, '
                          'e.g. "pune_facility_launch"')
    p1.add_argument("--value-cr", type=float,
                     help="numeric value, INR crore — omit for a non-numeric/milestone item")
    p1.add_argument("--status", choices=STATUSES,
                     help="pending/on_track/delivered/delayed/missed — your own assessment "
                          "from the sources, not auto-derived. Required for any item you want "
                          "to show as a status pointer on a Near/Medium/Long Term bullet.")
    p1.add_argument("--supersedes-id", type=int,
                     help="id (from `report`) of an earlier guidance entry for the SAME item "
                          "that this entry revises, so the evolution can be reconstructed")
    p1.add_argument("--note")
    p1.set_defaults(func=add_guidance)

    p2 = sub.add_parser("add-actual")
    p2.add_argument("--period", required=True, help='e.g. "FY27"')
    p2.add_argument("--metric", required=True)
    p2.add_argument("--value-cr", type=float, required=True)
    p2.set_defaults(func=add_actual)

    p4 = sub.add_parser("link", help="retroactively set --status/--supersedes-id on an "
                                      "already-existing entry, e.g. when backfilling status "
                                      "pointers for guidance logged before this feature existed")
    p4.add_argument("--id", type=int, required=True, help="id of the existing entry to update")
    p4.add_argument("--status", choices=STATUSES)
    p4.add_argument("--supersedes-id", type=int)
    p4.set_defaults(func=link_entry)

    p3 = sub.add_parser("report")
    p3.add_argument("--lookback", type=int, default=6,
                     help="how many tracked guidance-vs-actual quarters to show (default 6, "
                          "the standing default as of the 2-annual-reports/6-quarters sourcing "
                          "depth; override only if the user explicitly asks for a shorter "
                          "window). Status-tracked outlook items are always shown in full "
                          "regardless of this setting.")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
