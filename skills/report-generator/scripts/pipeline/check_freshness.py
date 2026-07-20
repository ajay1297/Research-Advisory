#!/usr/bin/env python3
"""
check_freshness.py — decide how much of the pipeline actually needs to re-run, and
compute the exact BSE date window to sweep.

The point: regenerating a report should NOT re-fetch and re-process every historical
concall/annual report every time. Each company has a small state.json recording what
was last processed. On a regenerate request, Claude fetches only the *listing* of
available concalls from screener.in's Documents tab (cheap — one page, no PDFs) and
passes the latest quarter's FULL DATE (YYYY-MM-DD) seen there into this script — never
a month/quarter label like "May 2026" or "Q4 FY26", which is genuinely ambiguous (two
results in the same month collide; screener.in's own label wording can drift). If the
company doesn't hold a concall, use the results filing date instead — see
reference/sourcing_depth.md's "If the company doesn't hold concalls" section. The
script diffs the date against state.json and tells Claude exactly what to do next:

  - "up_to_date": nothing changed, reuse the cached report.md as-is (or just recompute
    the forward PE inline if the user supplied a new price — that alone doesn't need a refetch).
  - "new_quarter": exactly one thing to fetch/parse — the new concall/results — nothing
    else. Old transcripts already in sources/ are NOT reprocessed.
  - "no_state": first time for this company, full pipeline runs, then call
    --mark-processed to write initial state.
  - "force_full": the user explicitly asked to regenerate this company's report *from
    scratch* (not just refresh it). Every source document gets refetched and every
    report section gets rebuilt from those fresh fetches — nothing carries forward from
    the cached report.md. This is a content rebuild, not a data-deletion request: the
    tracker histories (guidance_history.json, fundraise_history.json,
    rating_history.json, litigation_history.json) are a cumulative record of real past
    disclosures and are NOT wiped by --force; they keep accumulating exactly as before.

Every result also carries a `bse_fetch_window` — the `--from`/`--to` (YYYYMMDD) to
pass straight to bse_announcements.py, so the sweep is date-filtered at the API
rather than fetched wide and discarded. How the window is derived:

  - Refresh runs (up_to_date / new_quarter): from = last successful run's timestamp
    minus DELTA_DAYS (default 7), to = today. The backward overlap is deliberate —
    BSE filings land late, get amended, and get recategorized after the fact, so a
    window that starts exactly at the last success silently misses them. Example:
    last success 2026-07-01, running 2026-07-21 → sweep 2026-06-24 to 2026-07-21.
  - First-ever and from-scratch runs (no_state / force_full): the window is floored
    to the full standard depth — STANDARD_LOOKBACK_MONTHS (18) back from today for
    the quarterly sweeps, ANNUAL_LOOKBACK_MONTHS (24) for the annual-report sweep —
    because there is no prior state to be incremental against.

Runs entirely locally, no network required — the actual "what's the latest quarter"
check is a WebSearch/web_fetch call Claude makes separately and passes in here.

Usage:
    python3 check_freshness.py <company_slug> --latest-seen "2026-04-29" (full date, not "May 2026")
    python3 check_freshness.py <company_slug> --force
    python3 check_freshness.py <company_slug> --mark-processed "2026-04-29" --price 1235
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone

STANDARD_LOOKBACK_MONTHS = 18  # ~6 quarters — the default sourcing-depth assumption
ANNUAL_LOOKBACK_MONTHS = 24  # last 2 fiscal years of annual reports
DEFAULT_DELTA_DAYS = 7  # backward overlap on a refresh sweep, for late/amended filings


def _bse(d: datetime) -> str:
    """BSE's API takes dates as YYYYMMDD, not ISO."""
    return d.strftime("%Y%m%d")


def _full_depth_window(today: datetime) -> dict:
    return {
        "mode": "full_depth",
        "from": _bse(today - timedelta(days=STANDARD_LOOKBACK_MONTHS * 30)),
        "to": _bse(today),
        "annual_from": _bse(today - timedelta(days=ANNUAL_LOOKBACK_MONTHS * 30)),
        "note": "No usable prior state — sweep the full standard depth "
                f"({STANDARD_LOOKBACK_MONTHS} months, {ANNUAL_LOOKBACK_MONTHS} for annual "
                "reports). Pass these as --from/--to to bse_announcements.py; use "
                "annual_from for the Annual Report sweep only.",
    }


def _delta_window(last_success_iso: str, delta_days: int, today: datetime) -> dict:
    """Refresh window: last success minus the overlap buffer, through today."""
    if not last_success_iso:
        return _full_depth_window(today)
    try:
        last = datetime.strptime(last_success_iso[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return _full_depth_window(today)
    start = last - timedelta(days=delta_days)
    return {
        "mode": "delta",
        "from": _bse(start),
        "to": _bse(today),
        "annual_from": _bse(start),
        "last_success": last.strftime("%Y-%m-%d"),
        "delta_days": delta_days,
        "note": f"Incremental sweep: last successful run {last.strftime('%Y-%m-%d')} "
                f"minus a {delta_days}-day overlap buffer, through today. The buffer is "
                "there because BSE filings arrive late, get amended, and get "
                "recategorized — do not narrow it to the bare last-success date. Pass "
                "these as --from/--to to bse_announcements.py.",
    }


def _cadence_from_dates(dates_csv: str, today: datetime = None) -> dict:
    """Classify concall cadence from a comma-separated list of ISO dates so the
    standard "6 quarters / 2 annual reports" depth assumption can be flagged as a
    poor fit *before* an agent spends fetch/verification effort discovering that
    itself. A company with only sporadic concalls (multi-year gaps) needs the
    "doesn't hold concalls" fallback path (see reference/sourcing_depth.md) from the start,
    not as a late correction."""
    today = today or datetime.now(timezone.utc)
    if not dates_csv:
        return {"concall_cadence": "unknown", "recommended_sourcing_mode": "standard",
                "note": "No concall dates supplied — pass --concall-dates to get an "
                        "explicit cadence read before assuming standard depth applies."}
    parsed = []
    for d in dates_csv.split(","):
        d = d.strip()
        if not d:
            continue
        try:
            parsed.append(datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc))
        except ValueError:
            continue
    if not parsed:
        return {"concall_cadence": "unknown", "recommended_sourcing_mode": "standard"}
    parsed.sort()
    within_18mo = [d for d in parsed if (today - d).days <= STANDARD_LOOKBACK_MONTHS * 30]
    if len(within_18mo) >= 5:
        cadence = "regular"
        mode = "standard"
    elif len(within_18mo) >= 1:
        cadence = "irregular"
        mode = "reduced_depth_disclose_gap"
    else:
        cadence = "sparse_or_none"
        mode = "no_concall_fallback"
    return {
        "concall_cadence": cadence,
        "concalls_within_18mo": len(within_18mo),
        "most_recent_concall": parsed[-1].strftime("%Y-%m-%d"),
        "recommended_sourcing_mode": mode,
        "note": {
            "standard": "Cadence supports the default 6-quarter/2-annual-report depth.",
            "reduced_depth_disclose_gap": "Concall cadence is sparse — don't wait to "
                "discover this later. Use whatever concalls exist plus results filings/"
                "investor presentations for the outlook sections, and state the sparse "
                "cadence explicitly in the report per reference/sourcing_depth.md's "
                "\"If the company doesn't hold concalls\" section (it applies here too, "
                "even though at least one concall exists).",
            "no_concall_fallback": "No concall within 18 months (or none at all). Use "
                "results filing dates for freshness and follow reference/sourcing_depth.md's "
                "\"If the company doesn't hold concalls\" section from the start.",
        }[mode],
    }


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
    parser.add_argument("--latest-seen",
                         help="the latest quarter's FULL DATE (YYYY-MM-DD), not a month/quarter "
                              "label like 'May 2026' or 'Q4 FY26' — use the concall date if the "
                              "company holds one, otherwise the results filing date. A month-only "
                              "or quarter-only label is genuinely ambiguous (screener.in's own "
                              "label formatting can drift, and 'May 2026' can't distinguish two "
                              "results announced in the same month) — the comparison in this "
                              "script is a plain string match, so precision here is what keeps "
                              "up_to_date/new_quarter detection reliable, not any date logic in "
                              "the script itself.")
    parser.add_argument("--force", action="store_true",
                         help="user asked to regenerate from scratch — ignore cached state, "
                              "return force_full regardless of --latest-seen")
    parser.add_argument("--mark-processed",
                         help="record this FULL DATE (YYYY-MM-DD) as now fully processed — same "
                              "precision requirement as --latest-seen; whatever gets written here "
                              "is exactly what a future run's --latest-seen gets string-compared "
                              "against")
    parser.add_argument("--price", type=float, help="price to record alongside --mark-processed")
    parser.add_argument("--lookback-months", type=int, default=18,
                         help="how far back guidance-tracker/report windows should look on "
                              "refresh. Fixed framework default: 18 months (~6 quarters), "
                              "matching the standard 2-annual-report/6-quarter sourcing depth. "
                              "Do not override unless the user explicitly asks for a "
                              "longer/shorter history.")
    parser.add_argument("--delta-days", type=int, default=DEFAULT_DELTA_DAYS,
                         help="backward overlap applied to the last successful run's "
                              "timestamp when computing the BSE sweep window on a refresh "
                              f"(default {DEFAULT_DELTA_DAYS}). Widen it if a company is known "
                              "to file late or amend often; it costs one wider API query, not "
                              "extra PDF fetches, since already-processed filings are skipped "
                              "by the dedupe in pipeline/step1_retrieve.md.")
    parser.add_argument("--concall-dates",
                         help="comma-separated ISO dates (YYYY-MM-DD) of every concall found "
                              "on screener.in's Documents/Concalls tab — cheap to pass (already "
                              "fetched for --latest-seen), and lets this script flag a sparse/"
                              "irregular cadence upfront instead of an agent discovering it only "
                              "after attempting standard-depth sourcing.")
    args = parser.parse_args()

    path = state_path(args.company_slug)
    state = load(path)
    cadence = _cadence_from_dates(args.concall_dates) if args.concall_dates else None
    today = datetime.now(timezone.utc)

    if args.mark_processed:
        state = state or {}
        state["last_processed_label"] = args.mark_processed
        state["last_processed_at"] = today.isoformat()
        # The window anchor for the *next* run. Distinct from last_processed_label
        # (which is the newest filing date seen) — this is when the run itself
        # succeeded, which is what the delta window counts back from.
        state["last_success_at"] = today.strftime("%Y-%m-%d")
        if args.price is not None:
            state["last_price_used"] = args.price
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"Recorded state: last_processed_label={args.mark_processed}, "
              f"last_success_at={state['last_success_at']}")
        return

    if args.force:
        print(json.dumps({
            "status": "force_full",
            "action": "run_full_pipeline_ignore_cache",
            "previously_processed_label": (state or {}).get("last_processed_label"),
            "lookback_months": args.lookback_months,
            "bse_fetch_window": _full_depth_window(today),
            "note": "User asked to regenerate from scratch. Refetch every source document "
                    "(concall, investor presentation, annual report, screener.in) fresh and "
                    "rebuild every report section from those fetches — do not carry anything "
                    "forward from the cached report.md. Tracker histories (guidance/fundraise/"
                    "rating/litigation JSON) are cumulative real-world records, not stale "
                    "cache — do not wipe or rebuild them from scratch, keep appending as usual.",
            **({"cadence": cadence} if cadence else {}),
        }, indent=2))
        return

    if state is None:
        print(json.dumps({
            "status": "no_state",
            "action": "run_full_pipeline",
            "lookback_months": args.lookback_months,
            "bse_fetch_window": _full_depth_window(today),
            **({"cadence": cadence} if cadence else {}),
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
            "bse_fetch_window": _delta_window(state.get("last_success_at"), args.delta_days, today),
            "note": "No new concall/results since last run. Reuse ~/.report-generator/research_cache/<company>/report.md. "
                    "If the user gave a new price, only recompute the forward PE inline — don't refetch anything.",
            **({"cadence": cadence} if cadence else {}),
        }, indent=2))
    else:
        print(json.dumps({
            "status": "new_quarter",
            "action": "process_only_the_new_quarter",
            "previously_processed_label": state.get("last_processed_label"),
            "now_seen_label": args.latest_seen,
            "lookback_months": args.lookback_months,
            "bse_fetch_window": _delta_window(state.get("last_success_at"), args.delta_days, today),
            "note": "Fetch and parse only the new concall/results. Do not reprocess earlier "
                    "transcripts already under ~/.report-generator/sources/<company>/. Append one new "
                    "guidance_tracker.py entry rather than rebuilding the whole guidance history.",
            **({"cadence": cadence} if cadence else {}),
        }, indent=2))


if __name__ == "__main__":
    main()
