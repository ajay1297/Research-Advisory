#!/usr/bin/env python3
"""
pdf_to_text.py — extract text from a local PDF (concall transcript, investor
presentation, or annual report) to a plain text file, page-numbered.

Runs entirely locally, no network required.

Usage:
    python3 pdf_to_text.py <input.pdf> <output.txt> [--pages START-END] \\
        [--expect-name "Bhartiya International"]
    python3 pdf_to_text.py <input.pdf> --words-page N

--pages is optional and 1-indexed inclusive. It exists for a quick scouting pass only
— e.g. --pages 1-10 to read a table of contents and locate a section's page number
before committing to full extraction, or to re-extract an already-located range at
higher fidelity after a full-text grep already found it. It is NOT a substitute for
full-document extraction: an annual report's sections (segment/PP&E/litigation/
shareholding notes, the contingent-liabilities note) are scattered across the entire
document, not clustered in one guessed range, so omit --pages and extract the whole
document for any real (non-scouting) use.

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

--words-page N (1-indexed) is a different mode entirely, for one specific failure:
normal extraction (page.extract_text(), used everywhere else in this script) works by
linearizing every word into a reading-order stream and throwing its on-page position
away. That's fine for paragraphs and real gridded tables, but a chart — a grouped bar
chart's data-labels and axis-category labels, a pie chart's slice labels, anything
drawn as freeform vector shapes rather than a table — has no "reading order" that
means anything; extract_text() will still linearize it into *something*, and that
something can silently pair a number with the wrong label. Confirmed in practice: a
report's segment-revenue figures were pulled from exactly this kind of scrambled
extraction and were wrong — two of three divisions' numbers were mismatched to the
wrong period, discovered only when they didn't sum to the company's own disclosed
consolidated total.

--words-page prints every word on that one page with its exact bounding box
(x0, x1, top) instead of linearized text, sorted top-then-left so words that sit in
the same visual row cluster together in the output. This automates the mechanical
half of the fix — getting the position data — but deliberately does NOT try to
auto-detect which words are axis labels versus data values and pair them: that
requires actually looking at the chart and understanding its layout, and a heuristic
guessing that on an unseen chart risks producing a confidently wrong number, which is
worse than the current scrambled-but-visibly-suspicious output. The recipe (see
reference/data_sources.md's "Chart-derived figures" section) is: skim the printed
positions, identify the axis-category labels' x-ranges by eye, then pair each nearby
numeric label to its nearest-by-x-position axis label — the same technique that
caught the segment-revenue error above, just without hand-writing bounding-box
extraction code from scratch each time it's needed. Always cross-check the
reconstructed figures against a disclosed total before using them (e.g. the segments
should sum to the company's own consolidated revenue) — position-matching removes the
reading-order failure, not the need to verify the result.

Output for --words-page goes to stdout, not a file — this is a diagnostic aid for a
single page, not a document extraction to be saved under sources/<company_slug>/ or
logged in source_manifest.json.
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


def _dump_words(pdf, page_num):
    """Print every word on one page with its exact bounding box, sorted top-then-
    left so words in the same visual row cluster together — the position data
    linearized text extraction throws away. See this script's module docstring
    ("--words-page") for why this exists and how to use the output."""
    if page_num < 1 or page_num > len(pdf.pages):
        print(f"Page {page_num} out of range — this PDF has {len(pdf.pages)} pages.",
              file=sys.stderr)
        sys.exit(2)
    page = pdf.pages[page_num - 1]
    words = page.extract_words()
    if not words:
        print(f"No words found on page {page_num} — either blank or image-based "
              f"(scanned); position data can't help with a scanned page.")
        return
    words.sort(key=lambda w: (round(w["top"]), w["x0"]))
    print(f"=== page {page_num} words, sorted by (top, x0) — text  x0-x1  top-bottom ===")
    for w in words:
        print(f"  {w['text']:<20} x={w['x0']:>6.0f}-{w['x1']:<6.0f}  top={w['top']:>6.0f}-{w['bottom']:<6.0f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_txt", nargs="?",
                         help="required for normal extraction; omit when using --words-page, "
                              "which prints to stdout instead of writing a file")
    parser.add_argument("--pages", help="1-indexed inclusive range, e.g. 40-65")
    parser.add_argument("--expect-name",
                         help="cheap identity check: verify this string appears "
                              "(case-insensitive) in the first 2 pages before doing "
                              "the full extraction. Strongly recommended for any PDF "
                              "not fetched directly from the company's own IR/exchange "
                              "filing page.")
    parser.add_argument("--words-page", type=int,
                         help="1-indexed page number: dump that page's words with exact "
                              "bounding-box positions to stdout instead of doing normal "
                              "linearized extraction. For chart-derived figures only — see "
                              "this script's module docstring.")
    args = parser.parse_args()

    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed. Run: pip install pdfplumber --break-system-packages",
              file=sys.stderr)
        sys.exit(1)

    if args.words_page:
        with pdfplumber.open(args.input_pdf) as pdf:
            _dump_words(pdf, args.words_page)
        return

    if not args.output_txt:
        print("output_txt is required unless --words-page is given.", file=sys.stderr)
        sys.exit(2)

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
        "Per reference/rules_and_validation.md's token-discipline rule: grep -n \"<keyword>\" -C3 this file for the\n"
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
