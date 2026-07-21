#!/usr/bin/env python3
"""
shareholding_pattern.py — query BSE's own public-shareholding-pattern API directly
(plain HTTPS), no browser needed. Same confirmed-reachable exception as
bse_announcements.py/bulk_block_deals.py (see either script's docstring and
reference/data_sources.md's "Sandbox constraint" section): api.bseindia.com is a
different subdomain from the policy-blocked bseindia.com corp-pages, and is directly
reachable via a plain HTTPS request from this sandbox. Confirmed working 2026-07-21.

Why this exists: screener.in's shareholding-pattern table (the pipeline's normal
source, per reference/report_sections.md's Promoter/Governance section) gives
Promoter/FII/DII/Public category *percentages* only, never names. This endpoint is
BSE's own public-shareholding table (regulation-mandated, filed quarterly) and names
every public (non-promoter) holder BSE's own disclosure rules require to be named —
typically anyone at or above ~1%. That is real, verifiable, named institutional/HNI
participation the category percentages alone can't show — the same kind of signal
bulk_block_deals.py surfaces for open-market trades, but for standing positions
instead of a single day's trade.

What this script does NOT do: identify which names are "notable" or decide which are
worth naming in the report — that is a judgment call for the report-drafting step,
per reference/report_sections.md's "only name a deal/holder if the counterparty is a
recognizable, named mutual fund, FII/FPI, insurer, AIF, or well-known individual/
entity" rule (the same verifiability bar already applied to Bulk & Block Deals). This
script only fetches and prints/returns whatever BSE itself already named.

Endpoint scope — public/non-promoter holders only. This is BSE's "SHP Pub Shold"
(Shareholding Pattern — Public Shareholding) table; every row returned is already
categorized "Public shareholder" (Institutions or Non-Institutions). It does not
return promoter holdings — promoter shareholding trend still comes from screener.in
as before; this script is additive, not a replacement.

QtrCode — BSE's own quarter index, not the scrip's fiscal quarter. Confirmed by
direct testing (2026-07-21) that this is a single global, company-independent
sequential index incrementing by exactly 1 per *calendar* quarter (Mar/Jun/Sep/Dec
quarter-ends, per SEBI's uniform shareholding-pattern filing calendar — independent
of any company's own fiscal year), filed within ~3 weeks of quarter-end:

    QtrCode 128 -> quarter ended 2025-12-31 (filed ~10 Jan 2026)
    QtrCode 129 -> quarter ended 2026-03-31 (filed ~16-18 Apr 2026)
    QtrCode 130 -> quarter ended 2026-06-30 (filed ~18-20 Jul 2026)

This +1-per-quarter relationship is only confirmed reliable in this *recent* window —
testing QtrCode 100 (filed Oct 2020) against the same arithmetic gave a date that
doesn't reconcile cleanly with 128-130's spacing, almost certainly a relic of SEBI's
COVID-era filing-deadline extensions distorting *when* older quarters were filed
relative to their nominal quarter-end. Never assume the arithmetic holds more than a
handful of quarters from a confirmed-working anchor — this script does not; see
_discover_latest() and _walk_back() below, which discover the current latest QtrCode
by probing rather than trusting long-range arithmetic from a fixed anchor.

Usage:
    python3 shareholding_pattern.py <scrip_code> [--quarters N] [--qtr-code N] [--json]

    Default: fetches the latest quarter (auto-discovered) and prints every named
    public/non-promoter holder plus the Institutions/Non-Institutions category
    totals. --quarters N walks back N consecutive quarters from the latest
    (matching this framework's standard 6-quarter sourcing depth if N=6).
    --qtr-code overrides auto-discovery with an explicit BSE QtrCode, for a specific
    historical quarter or if auto-discovery is ever wrong.

Examples:
    # Latest quarter's named public shareholders for Sangam (India), scrip 514234:
    python3 shareholding_pattern.py 514234

    # Last 6 quarters (standard sourcing depth):
    python3 shareholding_pattern.py 514234 --quarters 6

An empty/all-zero result for the latest QtrCode is a legitimate finding some
companies hit temporarily (filed slightly later than the anchor company this
script's discovery probe used) — this script retries a couple of QtrCodes back
automatically before reporting no data; see _discover_latest().
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

API_BASE = "https://api.bseindia.com/BseIndiaAPI/api/Corp_shpSec_SHPPubShold_ng/w"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://www.bseindia.com",
    "referer": "https://www.bseindia.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Confirmed-working anchor (2026-07-21) — see module docstring. Discovery probes
# forward/backward from here each run rather than trusting this value to stay
# "latest" forever; bump it occasionally if the forward probe below regularly needs
# more than a couple of steps (a sign the anchor has drifted far from current).
ANCHOR_QTRCODE = 130
ANCHOR_QUARTER_END = "2026-06-30"


def _fetch_raw(scrip, qtr_code):
    params = {"SCRIPCODE": str(scrip), "QtrCode": f"{qtr_code:.2f}"}
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body)


def _has_data(raw):
    table = raw.get("Table") or []
    table1 = raw.get("Table1") or []
    if not table or not table[0].get("Fld_AuthoriseDate"):
        return False
    return any((r.get("Fld_TotalNoOfShares") or 0) > 0 for r in table1)


def _discover_latest(scrip):
    """Probe forward from ANCHOR_QTRCODE first (a newer quarter may have been filed
    since the anchor was set), then backward (this scrip may not have filed the
    anchor quarter yet) — returns the highest QtrCode with real data for this scrip.
    Bounded to a handful of steps either way; a script relying on unbounded probing
    would silently hide a genuinely broken anchor instead of surfacing it."""
    qc = ANCHOR_QTRCODE
    while _has_data(_fetch_raw(scrip, qc + 1)) and qc + 1 <= ANCHOR_QTRCODE + 4:
        qc += 1
    if _has_data(_fetch_raw(scrip, qc)):
        return qc
    for back in range(1, 5):
        if _has_data(_fetch_raw(scrip, qc - back)):
            return qc - back
    return None


def _named_holders(raw):
    rows = raw.get("Table1") or []
    out = []
    for r in rows:
        name = (r.get("Fld_ShareHolderName") or "").strip()
        if not name:
            continue
        out.append({
            "name": name,
            "category": r.get("Fld_ShortCatg"),
            # Fld_Level is the granular BSE category ("Mutual Funds", "Foreign
            # Portfolio Investors Category I", "Bodies Corporate", ...) — far more
            # informative than Fld_SubCategory, which is just "Institutions" /
            # "Non-Institutions" for every row regardless of the actual sub-type.
            "sub_category": r.get("Fld_Level") or r.get("Fld_SubCategory"),
            "shares": r.get("Fld_TotalNoOfShares"),
            "percent": r.get("Fld_TotalPercentageOf_A_B_C2"),
        })
    out.sort(key=lambda h: h["percent"] or 0, reverse=True)
    return out


# BSE's own subtotal/grand-total rows within the category hierarchy — excluded from
# the individual-category listing so a reader isn't shown a subtotal alongside the
# line items it's already summing (would double count if taken at face value).
_SUBTOTAL_LEVEL_RE = re.compile(r"^(sub total|total|b\s*=)", re.IGNORECASE)


def _category_totals(raw):
    """Individual-category rows (Fld_ShareHolderName is null, Fld_Level is a real
    category like "Mutual Funds" or "Foreign Portfolio Investors Category I") —
    granular context alongside the named holders. Subtotal/grand-total rows are
    excluded, not just unlabeled duplicates of the same thing."""
    rows = raw.get("Table1") or []
    out = []
    for r in rows:
        if r.get("Fld_ShareHolderName"):
            continue
        level = (r.get("Fld_Level") or "").strip()
        pct = r.get("Fld_TotalPercentageOf_A_B_C2") or 0
        if level and pct > 0 and not _SUBTOTAL_LEVEL_RE.match(level):
            out.append({"sub_category": level, "percent": pct, "shares": r.get("Fld_TotalNoOfShares")})
    return out


def fetch_quarter(scrip, qtr_code):
    raw = _fetch_raw(scrip, qtr_code)
    company = (raw.get("Table2") or [{}])[0].get("sLongName")
    as_of = (raw.get("Table") or [{}])[0].get("Fld_AuthoriseDate")
    return {
        "qtr_code": qtr_code,
        "company": company,
        "authorised": as_of,
        "named_holders": _named_holders(raw),
        "category_totals": _category_totals(raw),
        "has_data": _has_data(raw),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scrip", help="BSE scrip code, e.g. 514234 (numeric part of the BSE URL)")
    p.add_argument("--quarters", type=int, default=1,
                    help="how many consecutive quarters back from the latest to fetch (default 1)")
    p.add_argument("--qtr-code", type=int, default=None,
                    help="explicit BSE QtrCode, overriding auto-discovery of the latest quarter")
    p.add_argument("--json", action="store_true", help="print raw structured JSON instead of a summary")
    args = p.parse_args()

    if args.qtr_code is not None:
        latest = args.qtr_code
    else:
        latest = _discover_latest(args.scrip)
        if latest is None:
            print(f"# Could not find any filed quarter for scrip {args.scrip} within "
                  f"{ANCHOR_QTRCODE - 4}-{ANCHOR_QTRCODE + 4} (anchor {ANCHOR_QTRCODE} = "
                  f"quarter ended {ANCHOR_QUARTER_END}). Either this scrip hasn't filed "
                  f"recently, or the anchor has drifted too far from current — check with "
                  f"--qtr-code against a known-recent value, or bump ANCHOR_QTRCODE in "
                  f"this script if BSE has moved on several quarters since.",
                  file=sys.stderr)
            sys.exit(2)

    quarters = [fetch_quarter(args.scrip, latest - i) for i in range(args.quarters)]

    if args.json:
        print(json.dumps(quarters, indent=2))
        return

    for q in quarters:
        print(f"# {q['company'] or args.scrip} — QtrCode {q['qtr_code']} "
              f"(filed {q['authorised'] or 'not yet filed'})")
        if not q["has_data"]:
            print("  No data for this quarter — not yet filed, or before this scrip's "
                  "listing/reporting history. Not a fetch failure.")
            continue
        if q["category_totals"]:
            print("  Category totals (public/non-promoter):")
            for c in q["category_totals"]:
                print(f"    {c['sub_category']:<28} {c['percent']:>6.2f}%  ({c['shares']:,} shares)")
        if q["named_holders"]:
            print("  Named holders (BSE-disclosed, public/non-promoter):")
            for h in q["named_holders"]:
                print(f"    {h['name']:<45} {h['percent']:>6.2f}%  ({h['shares']:,} shares)  "
                      f"[{h['sub_category']}]")
        else:
            print("  No individually-named public/non-promoter holder this quarter — "
                  "a legitimate finding, not a fetch failure.")
        print()


if __name__ == "__main__":
    main()
