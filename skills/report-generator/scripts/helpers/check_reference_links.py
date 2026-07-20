#!/usr/bin/env python3
"""
check_reference_links.py — link-checker for this skill's own docs (SKILL.md +
pipeline/*.md + reference/*.md).

Why this exists: every restructuring of this skill's docs (splitting a file, moving a
section between files, moving a file between pipeline/ and reference/, renaming a
heading) has produced dangling cross-references that were only caught by manual
grep/read-through passes — a pointer to a step file surviving after that file was
merged into another, or a heading move leaving an "above"/"below" reference pointing
at the wrong file. This script mechanizes that check instead of relying on
remembering to grep for it every time.

Filenames are unique across pipeline/, reference/, and examples/, so a pointer
resolves whether it is written bare (`step2_synthesize.md`) or folder-qualified
(`pipeline/step2_synthesize.md`).

What it checks (heuristic, not a full markdown parser — false positives are
possible on genuinely ambiguous prose, but a clean run is a real signal):

1. **File existence** — every `reference/<name>.md` or bare `<name>.md` mention
   (for names that match an actual file elsewhere in this skill) resolves to a
   file that exists in reference/ or the skill root (SKILL.md).
2. **Heading existence** — every `<file>`'s "<Heading text>" / `<file>` "<Heading
   text>" style pointer resolves to a `##`/`###` heading that actually exists
   (case-insensitive substring match, since some pointers use a heading's short
   form) in the named file.
3. **Same-file "above"/"below"** — flags every literal "above"/"below" adjacent to
   a quoted heading name or section reference, so a human can eyeball whether it's
   still pointing within the same file after an edit (this script can't reliably
   verify direction/position on its own, so it surfaces candidates rather than
   silently passing or failing them).

Usage:
    python3 check_reference_links.py [skill_dir]

Exits non-zero if any FAIL is found. Run this after any edit that moves, renames,
or deletes a reference file or a `##`/`###` heading within one — the same trigger
that has caused every dangling-reference bug found by hand this session.
"""
import os
import re
import sys


# Deliverable/output filenames that legitimately appear in prose but aren't part
# of this skill's own doc set — never flag these as broken doc references.
DELIVERABLE_NAME_RE = re.compile(r"(^report\.md$|_report\.md$)")


def _load_files(skill_dir):
    """Return {filename: (path, content, headings)} for SKILL.md + pipeline/*.md
    + reference/*.md + examples/*.md. Filenames are unique across these folders, so
    they key the map directly — a pointer may spell a target either bare
    (`step2_synthesize.md`) or folder-qualified (`pipeline/step2_synthesize.md`) and
    both resolve to the same entry."""
    files = {}
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(skill_md):
        files["SKILL.md"] = skill_md
    for sub in ("pipeline", "reference", "examples"):
        d = os.path.join(skill_dir, sub)
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(".md"):
                    files[name] = os.path.join(d, name)

    loaded = {}
    for name, path in files.items():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        headings = re.findall(r"^#{1,3}\s+(.+?)\s*$", content, re.MULTILINE)
        # This codebase also uses **bold lead-ins** as de facto section markers
        # that get referenced by name elsewhere (e.g. "**Legacy fallback**: ...",
        # "**All working state...**") without a real ## heading — treat those as
        # headings too, or every such reference false-positives.
        bold_leadins = re.findall(r"\*\*([^*]{3,150})\*\*", content)
        loaded[name] = {
            "path": path, "content": content,
            "headings": headings + bold_leadins,
        }
    return loaded


def _norm(text):
    """Collapse markdown line-wrapping whitespace/newlines to single spaces so a
    heading or quoted pointer that wraps across source lines still compares
    correctly against the same text reconstructed from a single-line heading."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _heading_exists(target_headings, quoted_text):
    """Case-insensitive substring match either direction, whitespace-normalized —
    pointers often quote a shortened form of the real heading (e.g. "Concall
    transcripts" for a heading literally titled "Concalls, investor
    presentations, annual reports, press releases")."""
    q = _norm(quoted_text)
    for h in target_headings:
        hl = _norm(h)
        if q in hl or hl in q:
            return True
    return False


FILE_REF_RE = re.compile(r"`?(?:(?:reference|pipeline)/)?([A-Za-z0-9_]+\.md)`?")
# `<file>`'s "<Heading>" or `<file>` "<Heading>" — allow a few words of glue text
# between the filename and the opening quote (e.g. "'s ... section) ... \"").
# Quoted text itself may wrap across source lines (markdown line-wrapping), so
# allow newlines inside the quote but not inside the glue text before it.
FILE_HEADING_RE = re.compile(
    r"`(?:(?:reference|pipeline)/)?([A-Za-z0-9_]+\.md)`(?:'s)?[^\"\n]{0,40}\"([^\"]{3,120})\"",
    re.DOTALL,
)
# The reverse ordering also appears in this codebase's prose: "<Heading>"
# (`<file>`) — e.g. `not "how to fetch it" (`reference/data_sources.md`)`. Without
# this, FILE_HEADING_RE's forward search can mis-pair a file with the *next*
# quote in the text even when that quote belongs to a different, later file
# reference. Matched separately and given precedence when both fire nearby.
HEADING_FILE_RE = re.compile(
    r"\"([^\"]{3,120})\"\s*\(?`(?:(?:reference|pipeline)/)?([A-Za-z0-9_]+\.md)`\)?",
    re.DOTALL,
)


def check(skill_dir):
    files = _load_files(skill_dir)
    known_names = set(files.keys())
    findings = []  # (severity, file, message)

    for name, info in files.items():
        content = info["content"]

        # 1. File-existence check: every *.md mention should be a known file.
        for m in FILE_REF_RE.finditer(content):
            ref_name = m.group(1)
            if ref_name == name:
                continue  # self-reference by filename, not useful to flag
            if DELIVERABLE_NAME_RE.search(ref_name):
                continue  # output deliverable, not part of this skill's own docs
            if ref_name not in known_names:
                findings.append((
                    "FAIL", name,
                    f"references '{ref_name}' which does not exist in "
                    f"pipeline/, reference/, examples/, or as SKILL.md"
                ))

        # 2. Heading-existence check. "<Heading>" (`<file>`) ordering is checked
        # first and its quote spans are claimed, so the forward `<file>`'s
        # "<Heading>" pattern below doesn't mis-pair a file with an unrelated
        # later quote that actually belongs to this reverse-ordered pattern.
        #
        # Only flag when the word "section" appears within ~30 chars of the
        # quote — every genuine pointer in this codebase phrases it as
        # `<file>`'s "<Heading>" section (or the reverse), so this filters out
        # rhetorical quoted phrases in ordinary prose that happen to sit near an
        # unrelated file mention, without losing real broken pointers.
        def _looks_like_pointer(span_end):
            return "section" in content[span_end:span_end + 30].lower()

        claimed_spans = []
        for m in HEADING_FILE_RE.finditer(content):
            quoted, ref_name = m.group(1), m.group(2)
            claimed_spans.append(m.span(1))
            if not _looks_like_pointer(m.end(2)):
                continue
            if ref_name not in known_names or DELIVERABLE_NAME_RE.search(ref_name):
                continue
            target_headings = files[ref_name]["headings"]
            if not _heading_exists(target_headings, quoted):
                findings.append((
                    "FAIL", name,
                    f"points at {ref_name}'s \"{quoted}\" section, but no "
                    f"heading matching that text exists in {ref_name}"
                ))

        for m in FILE_HEADING_RE.finditer(content):
            ref_name, quoted = m.group(1), m.group(2)
            if any(s <= m.start(2) < e for s, e in claimed_spans):
                continue  # this quote already belongs to a reverse-ordered pair
            if not _looks_like_pointer(m.end(2)):
                continue
            if ref_name not in known_names:
                continue  # already caught by check 1
            target_headings = files[ref_name]["headings"]
            if not _heading_exists(target_headings, quoted):
                findings.append((
                    "FAIL", name,
                    f"points at {ref_name}'s \"{quoted}\" section, but no "
                    f"heading matching that text exists in {ref_name}"
                ))

        # 3. Same-file above/below candidates — informational only.
        for m in re.finditer(r'"\s*([^"]{3,80})"\s*\)?\s*\b(above|below)\b', content):
            quoted, direction = m.group(1), m.group(2)
            # Only worth surfacing if this quoted text is NOT immediately preceded
            # by a `file.md` reference (that case is already covered by check 2's
            # FILE_HEADING_RE, so this catches the same-file style instead).
            preceding = content[max(0, m.start() - 60):m.start()]
            if re.search(r"[A-Za-z0-9_]+\.md", preceding):
                continue
            if not _heading_exists(info["headings"], quoted):
                findings.append((
                    "WARN", name,
                    f"\"{quoted}\" ({direction}) does not match any heading in "
                    f"this same file — confirm it still points at the right place"
                ))

    return findings


def main():
    skill_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    skill_dir = os.path.abspath(skill_dir)
    findings = check(skill_dir)

    if not findings:
        print("PASS: no dangling reference-file or heading pointers found.")
        return

    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]

    for severity, name, msg in findings:
        print(f"{severity}: [{name}] {msg}")

    print(f"\n{len(fails)} FAIL, {len(warns)} WARN.")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
