#!/usr/bin/env python3
"""Lexical-semantic search over a large extracted text file (BM25-ranked).

`grep` only finds exact keyword matches. This finds the passages most relevant
to a natural-language query even when the source doesn't use your exact words
(e.g. querying "backward integration" also surfaces "we manufacture our own
preforms in-house"). Use it as a complement to grep, not a replacement — grep
is still faster and exact when you already know the right keyword.

The index is chunked and cached alongside the source file (as
<text_file>.bm25.pkl), so re-querying the same document within or across a run
costs nothing beyond the first build.

Usage:
  python3 semantic_search.py <text_file> "<natural language query>" [--top-k 5] [--chunk-words 250]

Output is a JSON array of the top-k chunks, each with a relevance score, the
approximate line range in the source file (so you can Read/grep that exact
range for full context), and the chunk text itself.
"""
import argparse
import json
import os
import pickle
import re
import sys


def chunk_text(text, chunk_words=250, overlap_words=40):
    lines = text.split("\n")
    words = []
    word_line = []
    for i, line in enumerate(lines):
        for w in line.split():
            words.append(w)
            word_line.append(i + 1)

    if not words:
        return []

    chunks = []
    step = max(chunk_words - overlap_words, 1)
    start = 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunks.append({
            "text": " ".join(words[start:end]),
            "line_start": word_line[start],
            "line_end": word_line[end - 1],
        })
        if end == len(words):
            break
        start += step
    return chunks


def tokenize(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def build_or_load_index(text_file, chunk_words):
    cache_path = text_file + ".bm25.pkl"
    text_mtime = os.path.getmtime(text_file)

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                cached = pickle.load(f)
            if cached.get("mtime") == text_mtime and cached.get("chunk_words") == chunk_words:
                return cached["chunks"], cached["bm25"]
        except (pickle.PickleError, EOFError, KeyError):
            pass  # stale/corrupt cache, rebuild below

    from rank_bm25 import BM25Okapi

    with open(text_file, "r", errors="ignore") as f:
        text = f.read()

    chunks = chunk_text(text, chunk_words=chunk_words)
    if not chunks:
        print(f"error: {text_file} is empty or unreadable", file=sys.stderr)
        sys.exit(1)

    tokenized = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized)

    with open(cache_path, "wb") as f:
        pickle.dump({"mtime": text_mtime, "chunk_words": chunk_words, "chunks": chunks, "bm25": bm25}, f)

    return chunks, bm25


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text_file", help="Path to the extracted .txt file (from pdf_to_text.py)")
    ap.add_argument("query", help="Natural-language query, e.g. 'backward integration into raw material'")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--chunk-words", type=int, default=250, help="Words per chunk (default 250, ~1-2 paragraphs)")
    args = ap.parse_args()

    if not os.path.exists(args.text_file):
        print(f"error: {args.text_file} not found", file=sys.stderr)
        sys.exit(1)

    chunks, bm25 = build_or_load_index(args.text_file, args.chunk_words)
    scores = bm25.get_scores(tokenize(args.query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[: args.top_k]

    results = []
    for i in ranked:
        if scores[i] <= 0:
            continue
        results.append({
            "score": round(float(scores[i]), 3),
            "lines": f"{chunks[i]['line_start']}-{chunks[i]['line_end']}",
            "text": chunks[i]["text"][:1200],
        })

    if not results:
        print("[]  (no chunks scored above zero — try different query wording, or fall back to grep)")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
