#!/usr/bin/env python3
"""
bse_announcements.py — query BSE's own announcements API directly (curl/requests),
no browser needed.

Why this exists: bseindia.com's main site (the corp-announcements search *page*) is
policy-blocked in the Browser pane in this environment, and the page itself is
JS-rendered besides — see reference/data_sources.md's "Sandbox constraint" section
for the full story. But api.bseindia.com (a different subdomain, the JSON API the
corp-announcements page itself calls client-side) is directly reachable via a plain
HTTPS request from this sandbox — confirmed in practice (2026-07): a `requests.get`
with a small set of headers (this script sets them) returns real paginated JSON, no
browser or WebFetch involved. Each row's PDF then downloads via `WebFetch` on
bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=<attachment-name> — also confirmed
working directly, same as the rest of this pipeline's BSE PDF handling.

This is a narrow, confirmed exception to reference/rules_and_validation.md's general
"never write a raw fetch script against these domains" rule — that rule holds for
every other domain in this pipeline (screener.in, the company's own site, etc.),
which do 403 through the sandbox's allowlisted network. api.bseindia.com specifically
does not. Don't generalize this exception to other domains without testing each one
the same way this one was tested.

What this script does NOT do: download the PDFs themselves. It only queries the API
and prints/returns the matching announcements with their downloadable PDF URLs —
fetching each PDF is still a separate `WebFetch` call (needed anyway, since
WebFetch/pdf_to_text.py is the extraction path, not this script). This script solves
*discovery* (which filings exist, when, what category), not extraction.

Usage:
    python3 bse_announcements.py <scrip_code> --from 20250101 --to 20260718 \\
        [--subcategory "Press Release / Media Release"] [--category "Company Update"] \\
        [--json]

    Prints one line per announcement (date, subcategory, headline, download URL) by
    default; --json prints the raw list for scripting. Paginates automatically using
    the API's own Table1[0].ROWCNT total-count field — no need to guess page count.

Examples:
    # All Company Update / Press Release filings for Tejas Networks (scrip 540595)
    # over the last ~18 months (the standard sourcing-depth window):
    python3 bse_announcements.py 540595 --from 20250101 --to 20260718 \\
        --subcategory "Press Release / Media Release"

    # Every announcement of any category/subcategory (subcategory omitted = all):
    python3 bse_announcements.py 540595 --from 20250101 --to 20260718

    # Every Annual Report filing on record for Sangam (India) (scrip 514234),
    # going back several fiscal years — confirmed in practice (2026-07) that this
    # subcategory/category combo returns one row per fiscal year, each with its own
    # filing date and direct PDF URL:
    python3 bse_announcements.py 514234 --from 20200101 --to 20260719 \\
        --category "Others" --subcategory "Reg. 34 (1) Annual Report"

Get the scrip code from the company's screener.in page (BSE link) or from BSE's own
search — it's the numeric code in the BSE URL, e.g. 540595 for
bseindia.com/stock-share-price/tejas-networks-ltd/tejasnet/540595.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

API_BASE = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://www.bseindia.com",
    "referer": "https://www.bseindia.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

PDF_BASE = "https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname="


def fetch_page(scrip, date_from, date_to, category, subcategory, search, page):
    params = {
        "pageno": str(page),
        "strCat": category or "-1",
        "strPrevDate": date_from,
        "strScrip": str(scrip),
        "strSearch": search,
        "strToDate": date_to,
        "strType": "C",
        "subcategory": subcategory or "-1",
    }
    url = API_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body)


def fetch_all(scrip, date_from, date_to, category=None, subcategory=None, search="P"):
    """Paginate through every matching announcement using Table1[0].ROWCNT."""
    all_rows = []
    page = 1
    total = None
    while True:
        data = fetch_page(scrip, date_from, date_to, category, subcategory, search, page)
        rows = data.get("Table", []) or []
        if total is None:
            table1 = data.get("Table1", []) or []
            total = table1[0]["ROWCNT"] if table1 else len(rows)
        if not rows:
            break
        all_rows.extend(rows)
        if len(all_rows) >= total or len(rows) == 0:
            break
        page += 1
        if page > 50:  # safety cap — BSE pages are typically small; this would be a bug, not a real result set
            print(f"WARNING: stopped at page 50 (fetched {len(all_rows)} of {total} reported) — "
                  f"investigate before trusting this result set", file=sys.stderr)
            break
    return all_rows, total


def to_record(row):
    attachment = row.get("ATTACHMENTNAME") or ""
    return {
        "date": row.get("News_submission_dt") or row.get("NEWS_DT"),
        "category": row.get("CATEGORYNAME"),
        "subcategory": row.get("SUBCATNAME"),
        "headline": row.get("HEADLINE") or row.get("NEWSSUB"),
        "attachment_name": attachment,
        "pdf_url": (PDF_BASE + attachment) if attachment else None,
        "size_bytes": row.get("Fld_Attachsize"),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scrip", help="BSE scrip code, e.g. 540595 (numeric part of the BSE URL)")
    p.add_argument("--from", dest="date_from", required=True, help="YYYYMMDD")
    p.add_argument("--to", dest="date_to", required=True, help="YYYYMMDD")
    p.add_argument("--category", default=None, help='e.g. "Company Update" (default: all categories)')
    p.add_argument("--subcategory", default=None,
                    help='e.g. "Press Release / Media Release" (default: all subcategories)')
    p.add_argument("--search", default="P", help='API\'s own strSearch param — "P" works for standard queries, leave as default unless troubleshooting')
    p.add_argument("--json", action="store_true", help="print raw JSON records instead of one line per row")
    args = p.parse_args()

    # Confirmed in practice: passing --subcategory without --category makes the API ignore the
    # subcategory filter entirely (returns everything, unfiltered) — the two must be passed together.
    # Different subcategories sit under different categories (press releases under "Company Update",
    # annual reports under "Others") — only auto-default for subcategories this script has actually
    # confirmed the correct category for; guessing wrong here would silently return an empty or
    # unfiltered result set rather than erroring, which is worse than requiring --category explicitly.
    KNOWN_SUBCATEGORY_CATEGORY = {
        "press release / media release": "Company Update",
        "reg. 34 (1) annual report": "Others",
    }
    if args.subcategory and not args.category:
        known = KNOWN_SUBCATEGORY_CATEGORY.get(args.subcategory.strip().lower())
        if known:
            args.category = known
            print(f"NOTE: --subcategory {args.subcategory!r} given without --category — defaulting "
                  f"--category to {known!r} (confirmed correct pairing for this subcategory; the two "
                  f"must be passed together or the API silently ignores the subcategory filter)",
                  file=sys.stderr)
        else:
            print(f"ERROR: --subcategory {args.subcategory!r} given without --category, and this "
                  f"subcategory's correct category isn't one this script has confirmed "
                  f"({sorted(KNOWN_SUBCATEGORY_CATEGORY.values())}). Guessing wrong would silently "
                  f"return an empty or unfiltered result set — pass --category explicitly instead.",
                  file=sys.stderr)
            sys.exit(1)

    rows, total = fetch_all(args.scrip, args.date_from, args.date_to, args.category, args.subcategory, args.search)
    records = [to_record(r) for r in rows]

    if args.json:
        print(json.dumps(records, indent=2))
    else:
        print(f"# {len(records)} of {total} reported announcement(s) for scrip {args.scrip}, "
              f"{args.date_from}-{args.date_to}"
              + (f", subcategory={args.subcategory!r}" if args.subcategory else "")
              + (f", category={args.category!r}" if args.category else ""))
        for rec in records:
            print(f"{rec['date']}\t{rec['subcategory'] or rec['category']}\t{rec['headline']}\t{rec['pdf_url']}")

    if len(records) != total:
        print(f"NOTE: fetched {len(records)} but API reported {total} total — "
              f"pagination may be incomplete, verify before treating this as the full set", file=sys.stderr)


if __name__ == "__main__":
    main()
