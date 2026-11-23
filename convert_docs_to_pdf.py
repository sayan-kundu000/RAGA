"""Script to convert RAGA Documentation markdown files into professionally styled PDF documents

using ReportLab Platypus.
"""

import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "RAGA: Systems Architecture & Technical Reference Manual")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        
        self.drawString(54, 32, "Confidential & Proprietary — sayan-kundu000 / RAGA")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()

    # Modify existing BodyText and Normal
    styles['Normal'].textColor = colors.HexColor("#1e293b")
    styles['Normal'].fontSize = 9.5
    styles['Normal'].leading = 13.5

    # Title Style
    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    ))

    # Subtitle Style
    styles.add(ParagraphStyle(
        name='DocSubtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=16
    ))

    # Heading 1
    styles.add(ParagraphStyle(
        name='DocH1',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))

    # Heading 2
    styles.add(ParagraphStyle(
        name='DocH2',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    # Heading 3
    styles.add(ParagraphStyle(
        name='DocH3',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    ))

    # Paragraph Body Text
    styles.add(ParagraphStyle(
        name='DocBody',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=7
    ))

    # Bullet Text
    styles.add(ParagraphStyle(
        name='DocBullet',
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    ))

    # Blockquote Callout
    styles.add(ParagraphStyle(
        name='DocCallout',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=18,
        rightIndent=18,
        spaceBefore=6,
        spaceAfter=8
    ))

    # Code / Monospace Style
    styles.add(ParagraphStyle(
        name='DocCode',
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a")
    ))

    # Table Cell Text
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b")
    ))

    # Table Header Cell
    styles.add(ParagraphStyle(
        name='TableHeaderCell',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#ffffff")
    ))

    return styles


def clean_markdown_inline(text: str) -> str:
    """Escape XML characters and convert common inline markdown to HTML tags supported by ReportLab."""
    # Escape XML essentials
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Re-allow strong and em
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier' color='#0284c7'><b>\1</b></font>", text)
    # Remove markdown link syntax [text](url) -> text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"<b>\1</b>", text)
    return text


def parse_markdown_to_elements(md_text: str, styles):
    elements = []
    lines = md_text.splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                # End of code block
                code_text = "<br/>".join(code_lines)
                code_p = Paragraph(f"<font name='Courier'>{code_text}</font>", styles['DocCode'])
                # Wrap code in background table
                code_table = Table([[code_p]], colWidths=[500])
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('ROUNDEDCORNERS', [4, 4, 4, 4]),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(code_table)
                elements.append(Spacer(1, 6))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            # Escape XML inside code block
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            code_lines.append(escaped)
            continue

        # Handle Tables
        if "|" in line and (line.startswith("|") or stripped.startswith("|")):
            # Check if separator row like |---|---|
            if re.match(r"^\|?\s*[-:]+\s*\|", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            # Table ended, build Platypus table
            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                col_width = 500 / num_cols
                formatted_data = []
                for row_idx, row in enumerate(table_rows):
                    row_cells = []
                    for cell in row:
                        clean_cell = clean_markdown_inline(cell)
                        if row_idx == 0:
                            p = Paragraph(clean_cell, styles['TableHeaderCell'])
                        else:
                            p = Paragraph(clean_cell, styles['TableCell'])
                        row_cells.append(p)
                    # Pad missing columns if any
                    while len(row_cells) < num_cols:
                        row_cells.append(Paragraph("", styles['TableCell']))
                    formatted_data.append(row_cells)

                plat_table = Table(formatted_data, colWidths=[col_width] * num_cols)
                plat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(plat_table)
                elements.append(Spacer(1, 8))
            table_rows = []
            in_table = False

        # Ignore empty lines
        if not stripped:
            elements.append(Spacer(1, 4))
            continue

        # Horizontal Divider
        if stripped in ("---", "***", "___"):
            elements.append(Spacer(1, 4))
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
            continue

        # Headings
        if stripped.startswith("# "):
            title_text = clean_markdown_inline(stripped[2:])
            elements.append(Paragraph(title_text, styles['DocTitle']))
            elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=10))
            continue
        elif stripped.startswith("## "):
            h1_text = clean_markdown_inline(stripped[3:])
            elements.append(Paragraph(h1_text, styles['DocH1']))
            continue
        elif stripped.startswith("### "):
            h2_text = clean_markdown_inline(stripped[4:])
            elements.append(Paragraph(h2_text, styles['DocH2']))
            continue
        elif stripped.startswith("#### "):
            h3_text = clean_markdown_inline(stripped[5:])
            elements.append(Paragraph(h3_text, styles['DocH3']))
            continue

        # Blockquote
        if stripped.startswith("> "):
            quote_text = clean_markdown_inline(stripped[2:])
            quote_p = Paragraph(quote_text, styles['DocCallout'])
            quote_table = Table([[quote_p]], colWidths=[500])
            quote_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor("#3b82f6")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(quote_table)
            elements.append(Spacer(1, 5))
            continue

        # Bullets
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = "&bull;&nbsp;&nbsp;" + clean_markdown_inline(stripped[2:])
            elements.append(Paragraph(bullet_text, styles['DocBullet']))
            continue

        # Numbered list item
        numbered_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if numbered_match:
            num = numbered_match.group(1)
            item_text = f"<b>{num}.</b>&nbsp;&nbsp;" + clean_markdown_inline(numbered_match.group(2))
            elements.append(Paragraph(item_text, styles['DocBullet']))
            continue

        # Normal Paragraph
        clean_p = clean_markdown_inline(stripped)
        elements.append(Paragraph(clean_p, styles['DocBody']))

    return elements


def convert_markdown_file_to_pdf(input_md_path: Path, output_pdf_path: Path):
    """Convert an individual markdown document into a styled PDF."""
    if not input_md_path.exists():
        print(f"Error: {input_md_path} does not exist.")
        return

    md_content = input_md_path.read_text(encoding="utf-8")
    styles = get_custom_styles()
    elements = parse_markdown_to_elements(md_content, styles)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_pdf_path}")


def generate_complete_37_topics_pdf(output_pdf_path: Path):
    """Compile all 37 documentation chapters into a unified publication-grade reference manual PDF."""
    topics_dir = Path("docs/topics")
    styles = get_custom_styles()
    all_elements = []

    # Title Page
    all_elements.append(Spacer(1, 40))
    all_elements.append(Paragraph("RAGA", styles['DocTitle']))
    all_elements.append(Paragraph("Advanced RAG Agent with Context Compression &amp; Semantic Memory", styles['DocSubtitle']))
    all_elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=20))
    
    overview_text = (
        "<b>Complete 37-Chapter Technical Reference Manual</b><br/><br/>"
        "This compendium contains the exhaustive technical specification of the RAGA agent pipeline. "
        "Each chapter provides an in-depth, rigorous exploration spanning architectural mechanics, "
        "algorithmic mathematics, vector space geometry, cognitive memory systems, and enterprise deployment blueprints.<br/><br/>"
        "<b>Author:</b> sayan-kundu000<br/>"
        "<b>Core Stack:</b> Python 3.12, FastAPI, Qdrant, Cohere ReRank v3, Mem0, Okapi BM25, Pydantic V2"
    )
    all_elements.append(Paragraph(overview_text, styles['DocBody']))
    all_elements.append(PageBreak())

    # Read and append each topic
    for i in range(1, 38):
        topic_file = topics_dir / f"topic_{i:02d}.md"
        if topic_file.exists():
            topic_md = topic_file.read_text(encoding="utf-8")
            topic_elements = parse_markdown_to_elements(topic_md, styles)
            all_elements.extend(topic_elements)
            all_elements.append(Spacer(1, 15))
            if i < 37:
                all_elements.append(PageBreak())

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    doc.build(all_elements, canvasmaker=NumberedCanvas)
    print(f"Successfully compiled Complete Reference Manual PDF: {output_pdf_path}")


if __name__ == "__main__":
    # 1. Convert docs/README.md -> docs/README.pdf
    convert_markdown_file_to_pdf(Path("docs/README.md"), Path("docs/README.pdf"))

    # 2. Convert root README.md -> README.pdf
    convert_markdown_file_to_pdf(Path("README.md"), Path("README.pdf"))

    # 3. Generate Complete 37 Topics Reference Manual PDF
    generate_complete_37_topics_pdf(Path("docs/RAGA_Complete_37_Topics_Manual.pdf"))
