#!/usr/bin/env python3
"""
pdf_to_text.py — extract text from a local PDF (concall transcript, investor
presentation, or annual report) to a plain text file, page-numbered.

Runs entirely locally, no network required.

Usage:
    python3 pdf_to_text.py <input.pdf> <output.txt> [--pages START-END]

--pages is optional and 1-indexed inclusive, e.g. --pages 40-65 to grab only the
MD&A / outlook section of a large annual report instead of the whole document.
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_txt")
    parser.add_argument("--pages", help="1-indexed inclusive range, e.g. 40-65")
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

    lines_out = []
    with pdfplumber.open(args.input_pdf) as pdf:
        total = len(pdf.pages)
        lo = (start - 1) if start else 0
        hi = end if end else total
        lo = max(0, lo)
        hi = min(total, hi)
        for i in range(lo, hi):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            lines_out.append(f"\n--- PAGE {i + 1} ---\n")
            lines_out.append(text)

    with open(args.output_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out))

    print(f"Wrote {args.output_txt} ({hi - lo} pages of {total} total)")


if __name__ == "__main__":
    main()
