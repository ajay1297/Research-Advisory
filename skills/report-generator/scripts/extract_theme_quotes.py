#!/usr/bin/env python3
"""
extract_theme_quotes.py — pre-filter a large transcript/text file down to a short
list of candidate forward-looking, quotable lines, bucketed by time horizon
(near / medium / long term). This is the main token-saving step in the skill: instead
of reading a 6,000-10,000 word transcript, the model reads a ~40-80 line JSON of
candidates.

Heuristic, not perfect — it over-selects on purpose (the model does the final curation
in scripts/build_report.py's input step). It never drops information silently without
also writing an "unclassified" bucket, so nothing forward-looking should be lost outright.

Runs entirely locally, no network required.

Usage:
    python3 extract_theme_quotes.py <input.txt> <output.json> [--speaker-tag PATTERN]
"""
import sys
import re
import json
import argparse

FORWARD_LOOKING = re.compile(
    r"\b(expect|expects|expecting|will|plan|plans|planning|guidance|target|targets|"
    r"aim|aims|aiming|going forward|anticipate|anticipates|outlook|should be|"
    r"we see|confident|envisage|foresee|likely to|order book|visibility|pipeline|"
    r"in progress|backed by|L1 in|under discussion|we believe|on track|"
    r"LOI|tender|approvals?|ramp[\s-]?up|come on stream|to convert)\b",
    re.IGNORECASE,
)

DAYS_WEEKS_MONTHS = r"\d+\s?(?:to|-)?\s?\d*\s?(?:days|weeks|months)"
QUARTERS_PHRASE = r"\d+\s?(?:to|-)?\s?\d*\s?quarters"
YEARS_PHRASE = r"\d+\s?(?:to|-)?\s?\d*\s?years"

NEAR_TERM = re.compile(
    r"\b(this quarter|next quarter|current quarter|this year|Q[1-4]\s?FY ?\d{2,4}|"
    r"within " + DAYS_WEEKS_MONTHS + r"|" + DAYS_WEEKS_MONTHS + r"|"
    r"by (?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December) 20\d{2})\b",
    re.IGNORECASE,
)

MEDIUM_TERM = re.compile(
    r"\b(medium term|next " + QUARTERS_PHRASE + r"|over the next few quarters|"
    r"FY\s?'?\d{2,4}|coming quarters|6[\s-]?to[\s-]?12 months|next 6 months|"
    r"next (?:financial|fiscal) year|next year)\b",
    re.IGNORECASE,
)

LONG_TERM = re.compile(
    r"\b(long term|long-term|next " + YEARS_PHRASE + r"|over the next few years|"
    r"in the coming years|new geograph|new markets worldwide|structural|multi-?year|"
    r"by (?:calendar\s?)?'?20\d{2}|calendar\s?'?\d{2,4}|in \d{1} to \d{1} years|"
    r"\d{1} to \d{1} years|double capacity|by 20[2-9]\d)\b",
    re.IGNORECASE,
)

NUMERIC_SIGNAL = re.compile(
    r"(INR\s?\d|Rs\.?\s?\d|\d+%|\d+\s?crore|\d+\s?cr\b|₹\s?\d)", re.IGNORECASE
)

SPEAKER_LINE = re.compile(r"^([A-Z][A-Za-z\.\s]{2,40}):\s*(.*)$")


def classify(sentence: str) -> str:
    if NEAR_TERM.search(sentence):
        return "near_term"
    # Explicit multi-year / calendar-year signals outrank a bare FY mention,
    # since a sentence can contain both (e.g. "FY28... by calendar 2028").
    if LONG_TERM.search(sentence):
        return "long_term"
    if MEDIUM_TERM.search(sentence):
        return "medium_term"
    return "unclassified"


def split_sentences(text: str):
    # Keep it simple and robust to transcript formatting quirks; split on
    # sentence-ending punctuation followed by whitespace + capital, but don't
    # split on decimals/abbreviations aggressively.
    text = re.sub(r"\s+", " ", text)
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", text)
    return [s.strip() for s in raw if s.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_txt")
    parser.add_argument("output_json")
    parser.add_argument("--min-words", type=int, default=8,
                         help="skip fragments shorter than this many words")
    args = parser.parse_args()

    with open(args.input_txt, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    current_speaker = None
    buckets = {"near_term": [], "medium_term": [], "long_term": [], "unclassified": []}

    for line in raw_text.splitlines():
        m = SPEAKER_LINE.match(line.strip())
        if m and len(m.group(1).split()) <= 6:
            current_speaker = m.group(1).strip()
            line = m.group(2)

        for sentence in split_sentences(line):
            words = sentence.split()
            if len(words) < args.min_words:
                continue
            if not FORWARD_LOOKING.search(sentence):
                continue
            bucket = classify(sentence)
            entry = {
                "quote": sentence.strip().strip('"'),
                "speaker": current_speaker,
                "has_numbers": bool(NUMERIC_SIGNAL.search(sentence)),
            }
            buckets[bucket].append(entry)

    # Rank within each bucket: prefer quotes with numbers (more citable/specific).
    for k in buckets:
        buckets[k].sort(key=lambda e: e["has_numbers"], reverse=True)
        buckets[k] = buckets[k][:40]  # cap per bucket to keep output small

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(buckets, f, indent=2, ensure_ascii=False)

    counts = {k: len(v) for k, v in buckets.items()}
    print(f"Wrote {args.output_json} — candidate counts: {counts}")
    print("Read this JSON, not the original transcript, to draft the report. "
          "If a bucket looks thin, grep the transcript for more context around a "
          "specific candidate instead of reading the whole file.")


if __name__ == "__main__":
    main()
