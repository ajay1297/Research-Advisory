#!/usr/bin/env python3
"""
forward_pe.py — compute a forward P/E from management's own revenue guidance.

Only meaningful when the company has actually given forward revenue guidance
(check the Near/Medium/Long Term bullets first). This is pure arithmetic on a
management estimate, not a valuation model — the output must always be shown
with its inputs, never as a bare multiple.

Forward EPS = (revenue_guidance_cr * pat_margin_pct / 100) / shares_outstanding_cr
Forward PE  = price / Forward EPS

Runs entirely locally, no network required.

Usage:
    python3 forward_pe.py --revenue-guidance-cr 2400 --pat-margin-pct 12.9 \
        --shares-cr 15.64 --price 1235 [--margin-source "trailing FY26 actual, not guided"]

If --pat-margin-pct is omitted, pass --trailing-pat-cr and --trailing-revenue-cr
instead and the script derives trailing margin for you (and labels it as an
assumption, not guidance).
"""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revenue-guidance-cr", type=float, required=True,
                         help="Management's guided revenue for the forward period, INR crore")
    parser.add_argument("--pat-margin-pct", type=float,
                         help="PAT margin pct to apply (use management's guided margin if given)")
    parser.add_argument("--trailing-pat-cr", type=float,
                         help="Trailing PAT, INR crore (used to derive margin if --pat-margin-pct not given)")
    parser.add_argument("--trailing-revenue-cr", type=float,
                         help="Trailing revenue, INR crore (used to derive margin if --pat-margin-pct not given)")
    parser.add_argument("--shares-cr", type=float, required=True,
                         help="Shares outstanding, in crore (e.g. equity capital / face value)")
    parser.add_argument("--price", type=float, required=True,
                         help="Current market price, or a user-supplied price")
    parser.add_argument("--price-source", default="current market price",
                         help="e.g. 'current market price (screener.in)' or 'user-supplied'")
    parser.add_argument("--margin-source",
                         help="Free text describing where the margin assumption came from")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    args = parser.parse_args()

    if args.pat_margin_pct is not None:
        margin_pct = args.pat_margin_pct
        margin_is_guided = True
        margin_note = args.margin_source or "management-guided PAT margin"
    elif args.trailing_pat_cr is not None and args.trailing_revenue_cr is not None:
        margin_pct = (args.trailing_pat_cr / args.trailing_revenue_cr) * 100
        margin_is_guided = False
        margin_note = args.margin_source or (
            f"ASSUMED — trailing PAT margin ({args.trailing_pat_cr}cr / "
            f"{args.trailing_revenue_cr}cr revenue), not management-guided"
        )
    else:
        print("Error: provide either --pat-margin-pct, or both --trailing-pat-cr and "
              "--trailing-revenue-cr.", file=sys.stderr)
        sys.exit(1)

    forward_pat_cr = args.revenue_guidance_cr * margin_pct / 100
    forward_eps = forward_pat_cr / args.shares_cr  # crore/crore cancels -> Rs per share
    forward_pe = args.price / forward_eps if forward_eps else None

    result = {
        "revenue_guidance_cr": args.revenue_guidance_cr,
        "pat_margin_pct_used": round(margin_pct, 2),
        "margin_is_guided": margin_is_guided,
        "margin_note": margin_note,
        "forward_pat_cr": round(forward_pat_cr, 2),
        "shares_outstanding_cr": args.shares_cr,
        "forward_eps": round(forward_eps, 2),
        "price": args.price,
        "price_source": args.price_source,
        "forward_pe": round(forward_pe, 2) if forward_pe else None,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Forward EPS = (INR{args.revenue_guidance_cr}cr guided revenue x "
          f"{margin_pct:.2f}% PAT margin [{margin_note}]) / {args.shares_cr}cr shares "
          f"= Rs{forward_eps:.2f}")
    print(f"Forward PE = Rs{args.price} ({args.price_source}) / Rs{forward_eps:.2f} "
          f"= {forward_pe:.1f}x" if forward_pe else "Forward PE = undefined (zero EPS)")
    if not margin_is_guided:
        print("\nNote: margin is an ASSUMPTION (trailing actual), not management guidance. "
              "Say so explicitly in the report.")


if __name__ == "__main__":
    main()
