#!/usr/bin/env python3
"""
report_to_pdf.py — convert a finished report.md (headings, bullet lists,
bold/italic inline text, and pipe tables) into a formatted PDF via reportlab.

Two things this exists to guard against, learned from generating real reports:

1. BLACK-BOX GLYPHS. reportlab's base font (Helvetica) uses WinAnsiEncoding,
   which does NOT include the Indian Rupee sign (₹, U+20B9) — it renders as a
   solid black box (.notdef) even though the text extracts fine. Every
   character in GLYPH_SAFE_REPLACEMENTS below is swapped for a safe ASCII
   equivalent before layout. If a report ever uses a new symbol that shows as
   a black box in the output PDF, add it to that dict rather than fighting
   font embedding.
2. INTERNAL FILE NAMES LEAKING INTO THE DELIVERABLE. Report prose should never
   say "via `scripts/helpers/guidance_tracker.py report`" — that's an internal
   implementation detail, not something a reader of the PDF needs or wants to
   see. The primary fix is not drafting that text in the first place (see
   reference/report_format.md's rule on this); this script also strips any
   stray `scripts/*.py` mention it finds as a backstop, since a defensive
   filter here is cheap insurance against a report-drafting slip.

Also supports fenced code blocks (```...```), rendered monospace/boxed with no
markdown interpretation — used for ASCII value-chain flow diagrams (see
reference/report_format.md's Value Chain Positioning section). A vertical
stacked-box layout is far safer than a wide horizontal one: at the Code
style's 7.5pt Courier, ~109 characters fit the A4 page width after margins
and border padding — a horizontal 4-column diagram can easily exceed that and
silently overflow the page edge (reportlab doesn't wrap or error on an
oversized Preformatted line, it just draws past the frame), whereas a
vertical stack is bounded by its single longest line, not four columns
multiplied together.

Usage:
    python3 report_to_pdf.py <input.md> <output.pdf> [--title "Document Title"]
"""
import argparse
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem,
    Preformatted
)
from reportlab.lib.enums import TA_LEFT

# Characters not in reportlab's base14/WinAnsi encoding that render as black
# boxes -> safe ASCII replacements. Extend this if a new symbol shows up
# broken in a future report; don't try to chase font embedding instead.
GLYPH_SAFE_REPLACEMENTS = {
    "₹": "Rs. ",   # ₹ INDIAN RUPEE SIGN — the actual black-box culprit found in practice
    "€": "EUR ",   # € just in case a report ever cites a euro figure
    "£": "GBP ",   # £
}

# Backstop filter for internal script/file references that shouldn't reach
# the reader. Matches things like "via `scripts/helpers/guidance_tracker.py report`"
# or a bare "`scripts/helpers/fundraise_tracker.py`" mention.
SCRIPT_MENTION_RE = re.compile(
    r"\s*\(?\b(?:via|using|run(?:ning)?|per)?\s*`scripts/[\w./-]+\.py[^`]*`\)?", re.IGNORECASE
)


def strip_internal_references(text: str) -> str:
    text = SCRIPT_MENTION_RE.sub("", text)
    # tidy up doubled spaces / dangling punctuation left behind by the strip
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([:.,])", r"\1", text)
    return text


def sanitize_glyphs(text: str) -> str:
    for bad, good in GLYPH_SAFE_REPLACEMENTS.items():
        text = text.replace(bad, good)
    return text


def escape_xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_markdown_to_reportlab(text: str) -> str:
    text = sanitize_glyphs(text)
    text = strip_internal_references(text)
    text = escape_xml(text)
    # links [text](url) -> "text (url)"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    # bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # italic *text* (single asterisks only, after bold already consumed)
    text = re.sub(r"(?<!\w)\*(?!\*)([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    # inline code `text` (anything left after the script-mention strip above)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    return text


def split_table_row(line: str):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_separator_row(cells) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells if c.strip() != "") and len(cells) > 0


def build_story(md_text: str, styles, doc_width):
    story = []
    lines = md_text.split("\n")
    i = 0
    n = len(lines)

    body_style = styles["Body"]
    bullet_style = styles["Bullet"]
    table_cell_style = styles["TableCell"]
    table_header_style = styles["TableHeader"]

    while i < n:
        raw = lines[i]
        line = raw.rstrip()

        if line.strip() == "":
            i += 1
            continue

        # Horizontal rule
        if re.fullmatch(r"-{3,}", line.strip()):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#999999")))
            story.append(Spacer(1, 10))
            i += 1
            continue

        # Fenced code block (```...```) — used for ASCII flow/box diagrams and any
        # other content that needs exact whitespace preserved. Rendered monospace,
        # boxed, with NO markdown/bold-italic interpretation — only the glyph-safety
        # substitution (e.g. ₹ -> Rs.) is applied, since a diagram might reference a
        # currency figure.
        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            i += 1  # skip closing fence
            code_text = sanitize_glyphs("\n".join(code_lines))
            story.append(Preformatted(code_text, styles["Code"]))
            story.append(Spacer(1, 10))
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = inline_markdown_to_reportlab(m.group(2))
            style_name = {1: "H1", 2: "H2", 3: "H3"}.get(level, "H3")
            story.append(Spacer(1, 10 if level <= 2 else 6))
            story.append(Paragraph(text, styles[style_name]))
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Table block: consecutive lines starting with '|'
        if line.strip().startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [split_table_row(r) for r in table_lines]
            if len(rows) >= 2 and is_separator_row(rows[1]):
                header = rows[0]
                data_rows = rows[2:]
            else:
                header = rows[0]
                data_rows = rows[1:]
            ncols = max(len(r) for r in rows)
            header = header + [""] * (ncols - len(header))
            data_rows = [r + [""] * (ncols - len(r)) for r in data_rows]

            table_data = [[Paragraph(inline_markdown_to_reportlab(c), table_header_style) for c in header]]
            for r in data_rows:
                table_data.append([Paragraph(inline_markdown_to_reportlab(c), table_cell_style) for c in r])

            col_width = doc_width / ncols
            tbl = Table(table_data, colWidths=[col_width] * ncols, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 10))
            continue

        # Bullet list block: consecutive lines starting with '- ' or '* '
        if re.match(r"^[-*]\s+", line.strip()):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                item_text = re.sub(r"^[-*]\s+", "", lines[i].strip())
                items.append(inline_markdown_to_reportlab(item_text))
                i += 1
            list_flowable = ListFlowable(
                [ListItem(Paragraph(t, bullet_style), leftIndent=6) for t in items],
                bulletType="bullet",
                start="•",
                leftIndent=14,
            )
            story.append(list_flowable)
            story.append(Spacer(1, 6))
            continue

        # Blockquote line starting with '>'
        if line.strip().startswith(">"):
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            text = inline_markdown_to_reportlab(" ".join(quote_lines))
            story.append(Paragraph(text, styles["Quote"]))
            story.append(Spacer(1, 8))
            continue

        # Regular paragraph: gather until blank line / next block start
        para_lines = [line.strip()]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(r"^(#{1,6}\s|\||[-*]\s|>|-{3,}$)", lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        text = inline_markdown_to_reportlab(" ".join(para_lines))
        story.append(Paragraph(text, body_style))
        story.append(Spacer(1, 6))

    return story


def make_styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["H1"] = ParagraphStyle("H1", parent=base["Title"], fontSize=20, leading=24,
                                   textColor=colors.HexColor("#1a2b3c"), spaceAfter=6, alignment=TA_LEFT)
    styles["H2"] = ParagraphStyle("H2", parent=base["Heading2"], fontSize=14, leading=18,
                                   textColor=colors.white, backColor=colors.HexColor("#2c3e50"),
                                   spaceBefore=4, spaceAfter=6, leftIndent=6, borderPadding=6)
    styles["H3"] = ParagraphStyle("H3", parent=base["Heading3"], fontSize=11.5, leading=15,
                                   textColor=colors.HexColor("#1a2b3c"), spaceBefore=4, spaceAfter=4)
    styles["Body"] = ParagraphStyle("Body", parent=base["Normal"], fontSize=9.5, leading=13.5,
                                     spaceAfter=2, alignment=TA_LEFT)
    styles["Bullet"] = ParagraphStyle("Bullet", parent=styles["Body"], fontSize=9.5, leading=13.5)
    styles["Quote"] = ParagraphStyle("Quote", parent=styles["Body"], fontSize=9, leading=12.5,
                                      textColor=colors.HexColor("#444444"), leftIndent=10,
                                      borderColor=colors.HexColor("#999999"), borderWidth=0,
                                      italic=True)
    styles["TableCell"] = ParagraphStyle("TableCell", parent=base["Normal"], fontSize=7.8, leading=10)
    styles["TableHeader"] = ParagraphStyle("TableHeader", parent=styles["TableCell"],
                                            textColor=colors.white, fontName="Helvetica-Bold")
    styles["Code"] = ParagraphStyle("Code", parent=base["Normal"], fontName="Courier", fontSize=7.5,
                                     leading=9.5, textColor=colors.HexColor("#1a2b3c"),
                                     backColor=colors.HexColor("#f4f4f4"),
                                     borderColor=colors.HexColor("#999999"), borderWidth=0.75,
                                     borderPadding=8, spaceBefore=6, spaceAfter=10)
    return styles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_md")
    parser.add_argument("output_pdf")
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    with open(args.input_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        args.output_pdf, pagesize=A4,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        title=args.title or args.input_md,
    )
    styles = make_styles()
    doc_width = A4[0] - doc.leftMargin - doc.rightMargin
    story = build_story(md_text, styles, doc_width)
    doc.build(story)
    print(f"Wrote {args.output_pdf}")


if __name__ == "__main__":
    main()
