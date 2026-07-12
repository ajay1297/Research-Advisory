#!/usr/bin/env python3
"""
check_freshness.py — decide how much of the pipeline actually needs to re-run.

The point: regenerating a report should NOT re-fetch and re-process every historical
concall/annual report every time. Each company has a small state.json recording what
was last processed. On a regenerate request, Claude fetches only the *listing* of
available concalls from screener.in's Documents tab (cheap — one page, no PDFs) and
passes the latest label seen there into this script. The script diffs that against
state.json and tells Claude exactly what to do next:

  - "up_to_date": nothing changed, reuse the cached report.md as-is (or just rerun
    forward_pe.py if the user supplied a new price — that alone doesn't need a refetch).
  - "new_quarter": exactly one thing to fetch/parse — the new concall/results — nothing
    else. Old transcripts already in research_cache/ are NOT reprocessed.
  - "no_state": first time for this company, full pipeline runs, then call
    --mark-processed to write initial state.

Runs entirely locally, no network required — the actual "what's the latest quarter"
check is a WebSearch/web_fetch call Claude makes separately and passes in here.

Usage:
    # check
    python3 check_freshness.py <company_slug> --latest-seen "May 2026"

    # after finishing processing, record what's now current
    python3 check_freshness.py <company_slug> --mark-processed "May 2026" --price 1235
"""
import argparse
import json
import os
from datetime import datetime, timezone


def state_path(company_slug: str) -> str:
    base = os.path.join(os.path.expanduser("~/.report-generator"), "research_cache", company_slug)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "state.json")


def load(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("company_slug")
    parser.add_argument("--latest-seen", help="latest concall/quarter label seen on screener.in just now")
    parser.add_argument("--mark-processed", help="record this label as now fully processed")
    parser.add_argument("--price", type=float, help="price to record alongside --mark-processed")
    parser.add_argument("--lookback-months", type=int, default=6,
                         help="how far back guidance-tracker/report windows should look on "
                              "refresh. Fixed framework default: 6 months. Do not override "
                              "unless the user explicitly asks for a longer/shorter history.")
    args = parser.parse_args()

    path = state_path(args.company_slug)
    state = load(path)

    if args.mark_processed:
        state = state or {}
        state["last_processed_label"] = args.mark_processed
        state["last_processed_at"] = datetime.now(timezone.utc).isoformat()
        if args.price is not None:
            state["last_price_used"] = args.price
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"Recorded state: last_processed_label={args.mark_processed}")
        return

    if state is None:
        print(json.dumps({
            "status": "no_state",
            "action": "run_full_pipeline",
            "lookback_months": args.lookback_months,
        }, indent=2))
        return

    if args.latest_seen is None:
        print(json.dumps({"status": "state_exists", "state": state}, indent=2))
        return

    if args.latest_seen == state.get("last_processed_label"):
        print(json.dumps({
            "status": "up_to_date",
            "action": "reuse_cached_report",
            "last_processed_label": state.get("last_processed_label"),
            "last_processed_at": state.get("last_processed_at"),
            "note": "No new concall/results since last run. Reuse ~/.report-generator/research_cache/<company>/report.md. "
                    "If the user gave a new price, only rerun forward_pe.py — don't refetch anything.",
        }, indent=2))
    else:
        print(json.dumps({
            "status": "new_quarter",
            "action": "process_only_the_new_quarter",
            "previously_processed_label": state.get("last_processed_label"),
            "now_seen_label": args.latest_seen,
            "lookback_months": args.lookback_months,
            "note": "Fetch and parse only the new concall/results. Do not reprocess earlier "
                    "transcripts already under ~/.report-generator/research_cache/<company>/raw/. Append one new "
                    "guidance_tracker.py entry rather than rebuilding the whole guidance history.",
        }, indent=2))


if __name__ == "__main__":
    main()
