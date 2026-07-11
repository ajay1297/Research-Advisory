#!/usr/bin/env python3
"""
build_report.py — render the final markdown report from a small, already-curated
JSON of bullets, following the fixed Near/Medium/Long Term format
(reference/report_format.md). Keeps boilerplate markdown formatting out of the
model's own output so it only has to produce the curated content, not repeat
structure every time.

Runs entirely locally, no network required.

Input JSON shape:
{
  "company": "Venus Pipes",
  "near_term": [
    {"headline": "Spooling Business Launch and Revenue Potential",
     "claim": "Management expects the spooling business to come on stream by "
              "December 2026, backed by an INR185 crore LOI from a single client.",
     "quote": "The order is a new one for us, but further, we are working on it "
              "and see more things to come."}
  ],
  "medium_term": [ ... same shape ... ],
  "long_term": [ ... same shape ... ]
}

Usage:
    python3 build_report.py <bullets.json> <output.md>
"""
import sys
import json
import argparse

SECTION_TITLES = {
    "near_term": "Near Term (Next 1 to 2 Quarters)",
    "medium_term": "Medium Term (6 to 12 Months)",
    "long_term": "Long Term (1+ Years)",
}


def render_bullet(b: dict) -> str:
    headline = b["headline"].strip()
    claim = b["claim"].strip()
    quote = b["quote"].strip().strip('"')
    source = f" ({b['source']})" if b.get("source") else ""
    return f'- **{headline}**: {claim} "{quote}"{source}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bullets_json")
    parser.add_argument("output_md")
    args = parser.parse_args()

    with open(args.bullets_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    company = data.get("company", "Company")
    lines = [f"# {company}", ""]

    for key in ("near_term", "medium_term", "long_term"):
        bullets = data.get(key, [])
        if not bullets:
            continue
        lines.append(f"## {SECTION_TITLES[key]}")
        lines.append("")
        for b in bullets:
            lines.append(render_bullet(b))
            lines.append("")

    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
