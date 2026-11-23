import io
import zipfile

import pytest
from docx import Document
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from knowdoc.parsing import ParseError, chunk_sections, parse, validate_file


def test_markdown_fences_tables_and_exact_offsets():
    source = b"# Indexes\nUse a B-tree.\n```python\n# code is not a section\nprint('index')\n```\n| key | value |\n| a | b |\n## Limits\nKeep writes small."
    sections, _ = parse(source, "markdown")
    assert len(sections) == 2
    assert "# code is not a section" in sections[0].text
    for text, location, _ in chunk_sections(sections, words=10, overlap=2):
        assert sections[location["section_index"]].text[location["start"]:location["end"]] == text
        assert "page" not in location


def test_html_removes_active_and_navigation_content():
    source = b'<html><nav>secret navigation</nav><main><h1>Search</h1><p>Use GIN indexes.</p><pre>SELECT 1;\nSELECT 2;</pre><script>steal()</script></main></html>'
    sections, _ = parse(source, "html")
    content = "\n".join(s.text for s in sections)
    assert "GIN" in content and "SELECT 1;\nSELECT 2;" in content
    assert "steal" not in content and "navigation" not in content


def test_docx_heading_and_table():
    doc = Document()
    doc.add_heading("Retention", level=1)
    doc.add_paragraph("Retain 30 days.")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Tier", "Days"
    buffer = io.BytesIO()
    doc.save(buffer)
    data = buffer.getvalue()
    assert validate_file("rules.docx", data) == "docx"
    sections, _ = parse(data, "docx")
    assert any("Tier | Days" in s.text for s in sections)
    assert all("page" not in s.location for s in sections)


def test_pdf_actual_page_numbers_and_scan_rejection():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(60, 700, "First page: indexes")
    c.showPage()
    c.drawString(60, 700, "Second page: transactions")
    c.save()
    sections, _ = parse(buffer.getvalue(), "pdf")
    assert [s.location["page"] for s in sections] == [1, 2]
    blank = PdfWriter()
    blank.add_blank_page(width=300, height=300)
    out = io.BytesIO()
    blank.write(out)
    with pytest.raises(ParseError, match="requires_ocr"):
        parse(out.getvalue(), "pdf")


@pytest.mark.parametrize("name,data", [("bad.pdf", b"hello"), ("bad.exe", b"MZ"),
                                         ("bad.md", b"%PDF-1.7"), ("bad.html", b"no markup")])
def test_spoofed_and_unsupported_uploads(name, data):
    with pytest.raises(ParseError):
        validate_file(name, data)


def test_docx_expansion_limit():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", b"x" * 80_000_001)
    with pytest.raises(ParseError, match="expansion_limit"):
        validate_file("bomb.docx", buffer.getvalue())
