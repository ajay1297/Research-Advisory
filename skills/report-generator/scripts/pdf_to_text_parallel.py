#!/usr/bin/env python3
"""
pdf_to_text_parallel.py — extract text from a local PDF using multiple worker
processes, for large documents (150+ pages) where pdf_to_text.py's single-
process extraction is slow.

This does NOT skip any pages. It splits the full page range into N contiguous
chunks that together cover 100% of the document (no gaps, no overlap), extracts
each chunk in a separate worker process, then concatenates the results back in
page order into one output file — byte-for-byte the same coverage as running
pdf_to_text.py with no --pages flag, just faster on a multi-core machine.

Use this instead of pdf_to_text.py when: the PDF is large (roughly 150+ pages)
and you need the WHOLE document extracted (which is the default, required case
for annual reports — report sections are scattered across the entire document,
not clustered in one range, so a partial/single-range extraction is not a safe
substitute for full extraction).

Runs entirely locally, no network required.

Usage:
    python3 pdf_to_text_parallel.py <input.pdf> <output.txt> [--workers 4]

--workers defaults to min(8, cpu_count()). Each worker opens its own
pdfplumber handle on the same file (pdfplumber/pdfminer objects aren't
fork-safe to share), so memory use scales with --workers on very large PDFs —
lower it if you hit memory pressure on an 800+ page document.
"""
import sys
import os
import argparse
from concurrent.futures import ProcessPoolExecutor


def extract_chunk(args):
    input_pdf, lo, hi = args  # lo/hi are 0-indexed, hi exclusive
    import pdfplumber
    lines_out = []
    with pdfplumber.open(input_pdf) as pdf:
        for i in range(lo, hi):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            lines_out.append(f"\n--- PAGE {i + 1} ---\n")
            lines_out.append(text)
    return lo, "\n".join(lines_out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf")
    parser.add_argument("output_txt")
    parser.add_argument("--workers", type=int, default=None,
                         help="Default: min(8, cpu_count())")
    args = parser.parse_args()

    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed. Run: pip install pdfplumber --break-system-packages",
              file=sys.stderr)
        sys.exit(1)

    with pdfplumber.open(args.input_pdf) as pdf:
        total = len(pdf.pages)

    workers = args.workers or min(8, os.cpu_count() or 4)
    workers = max(1, min(workers, total))

    # Split [0, total) into `workers` contiguous chunks covering every page —
    # this is what guarantees no data loss: the chunks partition the full
    # range exactly, with no gaps and no overlap.
    chunk_size = -(-total // workers)  # ceil division
    chunks = []
    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        chunks.append((args.input_pdf, start, end))

    results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for lo, text in pool.map(extract_chunk, chunks):
            results[lo] = text

    # Verify every chunk came back before writing anything — fail loudly
    # rather than silently write a partial file if a worker died.
    expected_los = sorted(lo for _, lo, _ in chunks)
    missing = [lo for lo in expected_los if lo not in results]
    if missing:
        print(f"error: {len(missing)} chunk(s) failed to extract (starting at pages "
              f"{[m + 1 for m in missing]}) — refusing to write a partial file. "
              f"Retry, or fall back to pdf_to_text.py.", file=sys.stderr)
        sys.exit(1)

    ordered_text = "\n".join(results[lo] for lo in expected_los)
    with open(args.output_txt, "w", encoding="utf-8") as f:
        f.write(ordered_text)

    print(f"Wrote {args.output_txt} ({total} pages of {total} total, "
          f"{workers} workers, full coverage verified)")


if __name__ == "__main__":
    main()
