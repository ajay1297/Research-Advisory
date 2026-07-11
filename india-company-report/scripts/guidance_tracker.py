#!/usr/bin/env python3
"""
guidance_tracker.py — maintain a small local log of what management guided vs. what
was actually delivered, one entry per quarter, and flag a pattern of missed guidance.

This is what powers the "Promoter / Governance Track Record" section: instead of
re-reading old transcripts every time a report is regenerated, each report run adds
one entry to research_cache/<company>/guidance_history.json, and this script reads
that small file back.

Runs entirely locally, no network required.

Usage:
    # log a guidance statement made in a given quarter's concall
    python3 guidance_tracker.py <company_slug> add-guidance \
        --given-in "Q4 FY26" --for-period "FY27" --metric revenue \
        --value-cr 2400 --note "revised FY27 guidance, high probability of further upward revision"

    # log the actual result once it's out, and auto-compare to any prior guidance for
    # that same period
    python3 guidance_tracker.py <company_slug> add-actual \
        --period "FY27" --metric revenue --value-cr 2510

    # print the last N tracked quarters (default 2 = 6 months, the framework's standing
    # lookback default) and flag repeated misses
    python3 guidance_tracker.py <company_slug> report
"""
import argparse
import json
import os
import sys

MISS_THRESHOLD_PCT = 10.0  # actual more than this % below guidance counts as a miss


def cache_path(company_slug: str) -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "guidance_history.json")


def load(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"guidances": [], "actuals": []}


def save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_guidance(args):
    path = cache_path(args.company_slug)
    data = load(path)
    data["guidances"].append({
        "given_in": args.given_in,
        "for_period": args.for_period,
        "metric": args.metric,
        "value_cr": args.value_cr,
        "note": args.note or "",
    })
    save(path, data)
    print(f"Logged guidance: {args.metric}={args.value_cr}cr for {args.for_period} "
          f"(given in {args.given_in})")


def add_actual(args):
    path = cache_path(args.company_slug)
    data = load(path)
    entry = {"period": args.period, "metric": args.metric, "value_cr": args.value_cr}
    # auto-compare against any prior guidance for the same period+metric
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


def report(args):
    path = cache_path(args.company_slug)
    data = load(path)
    tracked = [a for a in data["actuals"] if "verdict" in a and a["verdict"] != "no_prior_guidance"]
    tracked = tracked[-args.lookback:]
    if not tracked:
        print("No guidance-vs-actual comparisons logged yet for this company.")
        return
    misses = [a for a in tracked if a["verdict"] == "miss"]
    print(f"Last {len(tracked)} tracked guidance calls:")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("add-guidance")
    p1.add_argument("--given-in", required=True, help='e.g. "Q4 FY26"')
    p1.add_argument("--for-period", required=True, help='e.g. "FY27"')
    p1.add_argument("--metric", required=True, help='e.g. "revenue"')
    p1.add_argument("--value-cr", type=float, required=True)
    p1.add_argument("--note")
    p1.set_defaults(func=add_guidance)

    p2 = sub.add_parser("add-actual")
    p2.add_argument("--period", required=True, help='e.g. "FY27"')
    p2.add_argument("--metric", required=True)
    p2.add_argument("--value-cr", type=float, required=True)
    p2.set_defaults(func=add_actual)

    p3 = sub.add_parser("report")
    p3.add_argument("--lookback", type=int, default=2,
                     help="how many tracked quarters to show (default 2 = 6 months, the "
                          "standing framework default; override only if the user explicitly "
                          "asks for a longer history)")
    p3.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
