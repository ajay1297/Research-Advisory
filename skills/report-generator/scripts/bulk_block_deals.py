#!/usr/bin/env python3
"""
bulk_block_deals.py — query BSE's own bulk/block deal API directly (plain HTTPS),
no browser needed. Same confirmed-reachable exception as bse_announcements.py (see
that script's docstring and reference/data_sources.md's "Sandbox constraint"
section): api.bseindia.com is a different subdomain from the policy-blocked
bseindia.com corp-pages, and is directly reachable via a plain HTTPS request from
this sandbox.

Why this exists: a bulk deal (>0.5% of a company's equity in a single day, any
counterparty) or a block deal (a large single trade executed through the separate
block window, min. trade value threshold) is one of the few places a report can
find *named, real-money institutional participation* — a mutual fund, FII/FPI, AIF,
insurer, or a well-known HNI actually buying or selling on the open market — that
isn't already covered by the shareholding-pattern percentages (which show category
totals, never names) or the promoter-fund-raise tracker (which only covers
preferential/warrant allotments, not open-market trades). Confirmed in practice
(2026-07): a plain `requests.get`/`urllib` call with a small header set returns real
JSON, no pagination needed — the API returns the complete matching set in one
`Table` array for the date range given, not paginated the way the announcements API
is.

What this script does NOT do: identify which client names are "famous" investors —
that's a judgment call for the report-drafting step, not this script. This script
only fetches and prints/returns the raw deal records (date, client name, buy/sell,
quantity, price) for both bulk and block deal types; the report-drafting step is
responsible for recognizing a named mutual fund/FII/AIF/insurer/well-known HNI
among the client names and deciding whether it's genuinely a marquee, verifiable
signal worth naming in the report (see reference/source_playbook.md's "Bulk & Block
Deals" section for exactly how to use this output and what counts as "notable").

Usage:
    python3 bulk_block_deals.py <scrip_code> --from 20250101 --to 20260719 \\
        [--type both|bulk|block] [--json]

    Prints one line per deal (date, deal type, client name, B/S, quantity, price) by
    default; --json prints the raw list for scripting. Default --type is "both"
    (fetches bulk and block deals in the same run and merges them, each row tagged
    with its own deal_type) since a report should check both, not just one.

Examples:
    # Both bulk and block deals for Sangam (India) (scrip 514234) over the standard
    # ~18-month sourcing-depth window:
    python3 bulk_block_deals.py 514234 --from 20250101 --to 20260719

    # Block deals only:
    python3 bulk_block_deals.py 514234 --from 20250101 --to 20260719 --type block

Get <scrip_code> from screener.in's BSE link on the company's page (the numeric
code in the BSE URL), same as bse_announcements.py.

An empty result (zero rows for both types) is a legitimate, common finding — most
listed companies go long stretches with no bulk/block activity at all. State this
plainly in the report ("no bulk or block deals were recorded for this company in the
period reviewed") rather than treating an empty response as a fetch failure to
retry.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime

API_BASE = "https://api.bseindia.com/BseIndiaAPI/api/BulkblockDeal/w"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://www.bseindia.com",
    "referer": "https://www.bseindia.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# API's own convention: type=1 is bulk deals, type=2 is block deals.
TYPE_CODE = {"bulk": "1", "block": "2"}


def _to_ddmmyyyy(yyyymmdd):
    """API wants DD/MM/YYYY; CLI takes YYYYMMDD like bse_announcements.py for consistency."""
    return datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%d/%m/%Y")


def fetch_deals(scrip, date_from_ddmmyyyy, date_to_ddmmyyyy, deal_type):
    params = {
        "fromdt": date_from_ddmmyyyy,
        "todt": date_to_ddmmyyyy,
        "type": TYPE_CODE[deal_type],
        "scripcode": str(scrip),
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    rows = data.get("Table", []) or []
    return [to_record(r, deal_type) for r in rows]


def to_record(row, deal_type):
    return {
        "deal_type": deal_type,
        "date": row.get("DEAL_DATE"),
        "scrip_code": row.get("SCRIP_CODE"),
        "scrip_name": row.get("scripname") or row.get("ScripName"),
        "client_name": row.get("CLIENT_NAME"),
        "transaction_type": row.get("TRANSACTION_TYPE"),  # "B" or "S"
        "quantity": row.get("QUANTITY"),
        "price": row.get("PRICE"),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scrip", help="BSE scrip code, e.g. 514234 (numeric part of the BSE URL)")
    p.add_argument("--from", dest="date_from", required=True, help="YYYYMMDD")
    p.add_argument("--to", dest="date_to", required=True, help="YYYYMMDD")
    p.add_argument("--type", choices=["both", "bulk", "block"], default="both",
                    help="which deal type(s) to fetch (default: both)")
    p.add_argument("--json", action="store_true", help="print raw JSON records instead of one line per row")
    args = p.parse_args()

    date_from = _to_ddmmyyyy(args.date_from)
    date_to = _to_ddmmyyyy(args.date_to)

    deal_types = ["bulk", "block"] if args.type == "both" else [args.type]
    records = []
    for dt in deal_types:
        records.extend(fetch_deals(args.scrip, date_from, date_to, dt))

    # Most recent first, consistent with bse_announcements.py's ordering convention.
    records.sort(key=lambda r: r["date"] or "", reverse=True)

    if args.json:
        print(json.dumps(records, indent=2))
    else:
        print(f"# {len(records)} bulk/block deal(s) for scrip {args.scrip}, "
              f"{args.date_from}-{args.date_to} (type={args.type})")
        if not records:
            print("# No bulk or block deals recorded for this scrip in the period requested — "
                  "a legitimate, common finding, not a fetch failure.")
        for rec in records:
            print(f"{rec['date']}\t{rec['deal_type']}\t{rec['transaction_type']}\t"
                  f"{rec['client_name']}\tqty={rec['quantity']}\tprice={rec['price']}")


if __name__ == "__main__":
    main()
