#!/usr/bin/env python3
"""
pdf_to_text.py — extract text from a local PDF (concall transcript, investor
presentation, or annual report) to a plain text file, page-numbered.

Runs entirely locally, no network required.

Usage:
    python3 pdf_to_text.py <input.pdf> <output.txt> [--pages START-END] \\
        [--expect-name "Bhartiya International"]

--pages is optional and 1-indexed inclusive, e.g. --pages 40-65 to grab only the
MD&A / outlook section of a large annual report instead of the whole document.

--expect-name is a cheap identity check, strongly recommended for any annual
report/large PDF fetched from a search result rather than a company's own IR page.
A wrong-company PDF (e.g. a search result resolving to a different, similarly-named
listed company) is otherwise only caught after a full extraction and a wasted grep
pass — this happened in practice (an Ashiana Ispat Ltd. annual report was fetched and
fully extracted under a different company's slug before the mismatch was noticed).
When passed, this script extracts only the first 2 pages first, checks --expect-name
is present (case-insensitive substring match) in that text, and refuses to proceed to
the full extraction if not found — failing fast instead of burning a full multi-page
extraction + grep cycle on the wrong document.
"""
import sys
import argparse


def _extract_range(pdf, lo, hi):
    lines_out = []
    for i in range(lo, hi):
        page = pdf.pages[i]
        text = page.extract_text() or ""
        lines_out.append(f"\n--- PAGE {i + 1} ---\n")
        lines_out.append(text)
    return lines_out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_txt")
    parser.add_argument("--pages", help="1-indexed inclusive range, e.g. 40-65")
    parser.add_argument("--expect-name",
                         help="cheap identity check: verify this string appears "
                              "(case-insensitive) in the first 2 pages before doing "
                              "the full extraction. Strongly recommended for any PDF "
                              "not fetched directly from the company's own IR/exchange "
                              "filing page.")
    args = parser.parse_args()

    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed. Run: pip install pdfplumber --break-system-packages",
              file=sys.stderr)
        sys.exit(1)

    start, end = None, None
    if args.pages:
        parts = args.pages.split("-")
        start = int(parts[0])
        end = int(parts[1]) if len(parts) > 1 else start

    with pdfplumber.open(args.input_pdf) as pdf:
        total = len(pdf.pages)

        if args.expect_name:
            scout = _extract_range(pdf, 0, min(2, total))
            scout_text = "\n".join(scout).lower()
            if args.expect_name.lower() not in scout_text:
                print(f"IDENTITY CHECK FAILED: '{args.expect_name}' not found in the first "
                      f"2 pages of {args.input_pdf}. This PDF is likely the wrong company's "
                      f"document — refusing to run the full extraction. If this is a false "
                      f"negative (name genuinely doesn't appear on the cover pages), re-run "
                      f"without --expect-name after manually confirming the document identity.",
                      file=sys.stderr)
                sys.exit(2)

        lo = (start - 1) if start else 0
        hi = end if end else total
        lo = max(0, lo)
        hi = min(total, hi)
        lines_out = _extract_range(pdf, lo, hi)

    header = (
        "=== DO NOT Read() THIS FILE DIRECTLY — grep it instead ===\n"
        "This is a full-document text extraction and may run to thousands of lines.\n"
        "Per SKILL.md's token-discipline rule: grep -n \"<keyword>\" -C3 this file for the\n"
        "section you need, then Read() only the specific line range that surfaces. Reading\n"
        "this file top-to-bottom defeats the reason it was extracted this way and will\n"
        "inflate every subsequent turn's context for the rest of this session.\n"
        "===========================================================\n"
    )
    with open(args.output_txt, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(lines_out))

    print(f"Wrote {args.output_txt} ({hi - lo} pages of {total} total)")


if __name__ == "__main__":
    main()
