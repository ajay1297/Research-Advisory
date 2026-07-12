#!/usr/bin/env python3
"""
capacity_utilization.py — compute the revenue a company could do at full
utilization of its CURRENT installed capacity (no further capex assumed), and
the headroom between that and what it's actually doing today.

This is arithmetic on management-disclosed utilization/capacity figures, not a
forecast — it answers "how much more revenue is available from what's already
built" as distinct from the Capex/Milestones timeline's "what's being added."
Report both together: current-capacity headroom is the near-term growth lever;
the capex timeline is what unlocks growth beyond it.

Optionally also states a POST-CAPEX revenue potential, so the report can show
both numbers side by side: "before capex" (current installed capacity, fully
utilized) vs. "after capex" (once planned capacity additions are online).
Prefer passing management's own disclosed post-capex revenue figure directly
(--post-capex-max-revenue-cr) when they gave one (e.g. "capacity to support
INR3,000-3,200cr sales by FY28") — that's a management estimate, not something
to re-derive. Only use --post-capex-capacity-increase-pct as a fallback when no
such figure was given but a capacity-increase % was.

Runs entirely locally, no network required.

Two input modes for the CURRENT (pre-capex) figure:

  Mode A — utilization % already known (most common; management usually states
  this directly on the concall):
      python3 capacity_utilization.py --current-revenue-cr 248 --utilization-pct 82

  Mode B — derive utilization from installed capacity and units actually
  produced/sold, when a direct utilization % wasn't stated:
      python3 capacity_utilization.py --installed-capacity-units 500000 \
          --units-produced 410000 --realization-per-unit-inr 6200

Add a post-capex figure to either mode, e.g.:
      python3 capacity_utilization.py --current-revenue-cr 248 --utilization-pct 82 \
          --post-capex-max-revenue-cr 3100 \
          --post-capex-note "large-generator capacity, calendar 2027 completion / 2028 ramp-up"

Pass --capacity-label to record what the capacity is measured in (e.g. "MT/annum",
"garments/annum", "MW"), purely for the printed output — it isn't used in the math.
"""
import argparse
import json
import sys

HIGH_UTILIZATION_THRESHOLD_PCT = 85.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-revenue-cr", type=float,
                         help="Revenue actually achieved in the period being assessed, INR crore (Mode A)")
    parser.add_argument("--utilization-pct", type=float,
                         help="Current capacity utilization pct, as stated by management (Mode A)")
    parser.add_argument("--installed-capacity-units", type=float,
                         help="Installed capacity in physical units/annum (Mode B)")
    parser.add_argument("--units-produced", type=float,
                         help="Units actually produced/sold in the period (Mode B)")
    parser.add_argument("--realization-per-unit-inr", type=float,
                         help="Average realization/selling price per unit, plain INR (Mode B)")
    parser.add_argument("--capacity-label", default="units/annum",
                         help='What the capacity is measured in, e.g. "MT/annum", "MW" — cosmetic only')
    parser.add_argument("--utilization-source",
                         help='e.g. "management commentary, May 2026 concall"')
    parser.add_argument("--post-capex-max-revenue-cr", type=float,
                         help="Management's own disclosed revenue potential once planned capex/capacity "
                              "additions are complete, INR crore (preferred over the pct fallback below)")
    parser.add_argument("--post-capex-capacity-increase-pct", type=float,
                         help="Fallback only if no direct post-capex revenue figure was given: pct "
                              "increase in capacity from planned capex, scaled onto the current "
                              "full-utilization revenue figure")
    parser.add_argument("--post-capex-note",
                         help='e.g. "large-generator capacity, calendar 2027 completion"')
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    args = parser.parse_args()

    if args.current_revenue_cr is not None and args.utilization_pct is not None:
        current_revenue_cr = args.current_revenue_cr
        utilization_pct = args.utilization_pct
        mode = "A (direct utilization pct)"
    elif (args.installed_capacity_units is not None and args.units_produced is not None
          and args.realization_per_unit_inr is not None):
        utilization_pct = (args.units_produced / args.installed_capacity_units) * 100
        current_revenue_cr = (args.units_produced * args.realization_per_unit_inr) / 1e7
        mode = "B (derived from installed capacity, units produced, and realization/unit)"
    else:
        print("Error: provide either (--current-revenue-cr and --utilization-pct), or all of "
              "(--installed-capacity-units, --units-produced, --realization-per-unit-inr).",
              file=sys.stderr)
        sys.exit(1)

    if utilization_pct <= 0:
        print("Error: utilization pct must be > 0.", file=sys.stderr)
        sys.exit(1)

    max_revenue_at_full_util_cr = current_revenue_cr / (utilization_pct / 100)
    headroom_cr = max_revenue_at_full_util_cr - current_revenue_cr
    headroom_pct_of_current = (headroom_cr / current_revenue_cr) * 100 if current_revenue_cr else None

    post_capex_max_revenue_cr = None
    post_capex_basis = None
    if args.post_capex_max_revenue_cr is not None:
        post_capex_max_revenue_cr = args.post_capex_max_revenue_cr
        post_capex_basis = "management-disclosed figure"
    elif args.post_capex_capacity_increase_pct is not None:
        post_capex_max_revenue_cr = max_revenue_at_full_util_cr * (1 + args.post_capex_capacity_increase_pct / 100)
        post_capex_basis = f"derived: current full-utilization revenue scaled by +{args.post_capex_capacity_increase_pct:.1f}% capacity increase"
    capex_unlocked_cr = (post_capex_max_revenue_cr - max_revenue_at_full_util_cr) if post_capex_max_revenue_cr is not None else None

    result = {
        "mode": mode,
        "current_revenue_cr": round(current_revenue_cr, 2),
        "utilization_pct": round(utilization_pct, 1),
        "capacity_label": args.capacity_label,
        "before_capex_max_revenue_cr": round(max_revenue_at_full_util_cr, 2),
        "headroom_cr": round(headroom_cr, 2),
        "headroom_pct_of_current_revenue": round(headroom_pct_of_current, 1) if headroom_pct_of_current is not None else None,
        "utilization_source": args.utilization_source or "",
        "high_utilization_flag": utilization_pct >= HIGH_UTILIZATION_THRESHOLD_PCT,
        "after_capex_max_revenue_cr": round(post_capex_max_revenue_cr, 2) if post_capex_max_revenue_cr is not None else None,
        "post_capex_basis": post_capex_basis,
        "post_capex_note": args.post_capex_note or "",
        "capex_unlocked_revenue_cr": round(capex_unlocked_cr, 2) if capex_unlocked_cr is not None else None,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Mode: {mode}")
        print(f"Current revenue: INR{current_revenue_cr:.1f}cr at {utilization_pct:.1f}% utilization "
              f"of installed capacity ({args.capacity_label}).")
        print(f"BEFORE CAPEX — max revenue at 100% utilization of current capacity: "
              f"INR{max_revenue_at_full_util_cr:.1f}cr")
        print(f"Headroom from current capacity alone: INR{headroom_cr:.1f}cr "
              f"({headroom_pct_of_current:.1f}% above current revenue)" if headroom_pct_of_current is not None else "")
        if post_capex_max_revenue_cr is not None:
            note_bit = f" ({args.post_capex_note})" if args.post_capex_note else ""
            print(f"AFTER CAPEX{note_bit} — revenue potential: INR{post_capex_max_revenue_cr:.1f}cr "
                  f"[{post_capex_basis}]")
            print(f"Revenue unlocked by this capex, on top of the current-capacity ceiling: "
                  f"INR{capex_unlocked_cr:.1f}cr")
        else:
            print("No post-capex revenue figure provided — showing before-capex figures only. "
                  "Pass --post-capex-max-revenue-cr (preferred) or "
                  "--post-capex-capacity-increase-pct if the Capex/Milestones timeline discloses one.")

    if result["high_utilization_flag"]:
        msg = (f"\nNOTE: utilization is already at/above {HIGH_UTILIZATION_THRESHOLD_PCT:.0f}% — "
               f"near-term growth beyond INR{max_revenue_at_full_util_cr:.1f}cr requires new capacity "
               f"coming online (see Capex/Milestones Timeline), not just better utilization of what "
               f"already exists. Flag this as a capacity ceiling in the report.")
        print(msg, file=sys.stderr if args.json else sys.stdout)


if __name__ == "__main__":
    main()
