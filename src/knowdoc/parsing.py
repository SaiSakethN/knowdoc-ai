"""Conservative parsers: locations refer to normalized text, never invented pagination."""
import io
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from pypdf import PdfReader


class ParseError(ValueError):
    pass


@dataclass
class Section:
    text: str
    location: dict


def validate_file(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    types = {".md": "markdown", ".markdown": "markdown", ".html": "html", ".htm": "html",
             ".pdf": "pdf", ".docx": "docx"}
    if ext not in types or not content:
        raise ParseError("unsupported_or_empty_file")
    kind = types[ext]
    if kind == "pdf" and not content.startswith(b"%PDF-"):
        raise ParseError("invalid_pdf_signature")
    if kind == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ParseError("invalid_docx_structure")
                if len(archive.infolist()) > 2000 or sum(i.file_size for i in archive.infolist()) > 80_000_000:
                    raise ParseError("docx_expansion_limit")
                if any(i.flag_bits & 1 for i in archive.infolist()):
                    raise ParseError("encrypted_docx_unsupported")
        except zipfile.BadZipFile as exc:
            raise ParseError("invalid_docx_archive") from exc
    if kind in {"markdown", "html"}:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ParseError("text_must_be_utf8") from exc
        if "\x00" in decoded or content.startswith((b"%PDF", b"PK\x03\x04")):
            raise ParseError("invalid_text_content")
        if kind == "html" and not re.search(r"<(html|body|article|main|h[1-6]|p|div)\b", decoded, re.I):
            raise ParseError("invalid_html_structure")
    return kind


def ocr_page(content: bytes, page: int) -> str:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise ParseError("ocr_dependencies_unavailable")
    with tempfile.TemporaryDirectory(prefix="knowdoc-ocr-") as tmp:
        source = Path(tmp) / "input.pdf"
        source.write_bytes(content)
        stem = str(Path(tmp) / "page")
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to", "2400",
                        "-singlefile", "-png", str(source), stem],
                       check=True, timeout=30, capture_output=True)
        result = subprocess.run(["tesseract", stem + ".png", "stdout"], check=True,
                                timeout=30, capture_output=True, text=True)
        return result.stdout.strip()


def parse(content: bytes, kind: str, *, ocr: bool = False) -> tuple[list[Section], list[str]]:
    sections: list[Section] = []
    warnings: list[str] = []
    if kind == "pdf":
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise ParseError("encrypted_pdf_unsupported")
        if len(reader.pages) > 300:
            raise ParseError("pdf_page_limit")
        for i, page in enumerate(reader.pages, 1):
            text = (page.extract_text(extraction_mode="layout") or "").strip()
            method = "pdf_text"
            if not text:
                if not ocr:
                    raise ParseError("scanned_pdf_requires_ocr")
                text = ocr_page(content, i)
                method = "ocr"
                warnings.append(f"Page {i}: OCR text requires visual review; layout may be lost")
                if not text:
                    raise ParseError("ocr_no_text")
            sections.append(Section(text, {"page": i, "method": method}))
    elif kind == "docx":
        document = DocxDocument(io.BytesIO(content))
        heading = "Document"
        for i, block in enumerate(document.iter_inner_content(), 1):
            if hasattr(block, "rows"):
                text = "\n".join(" | ".join(c.text for c in row.cells) for row in block.rows)
            else:
                text = block.text
                if block.style and block.style.name.startswith("Heading"):
                    heading = text
            if text.strip():
                sections.append(Section(text.strip(), {"section": heading, "block": i}))
    elif kind == "html":
        soup = BeautifulSoup(content.decode("utf-8-sig"), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "form", "iframe"]):
            tag.decompose()
        main = soup.select_one("main") or soup.select_one("article") or soup.select_one(".chapter") or soup.select_one(".sect1") or soup.body or soup
        heading = "Document"
        for element in main.find_all(["h1", "h2", "h3", "h4", "p", "pre", "table", "li", "dt"]):
            if element.find_parent(["pre", "table", "li"]):
                continue
            if element.name.startswith("h"):
                heading = element.get_text(" ", strip=True)
            text = element.get_text("\n" if element.name in {"pre", "table"} else " ", strip=True)
            if text:
                sections.append(Section(text, {"section": heading, "anchor": element.get("id")}))
    elif kind == "markdown":
        heading = "Document"
        lines: list[str] = []
        fenced = False
        for line in content.decode("utf-8-sig").splitlines():
            if line.lstrip().startswith(("```", "~~~")):
                fenced = not fenced
            if not fenced and re.match(r"^#{1,6}\s", line):
                if lines and "\n".join(lines).strip():
                    sections.append(Section("\n".join(lines).strip(), {"section": heading}))
                heading, lines = line.lstrip("# ").strip(), [line]
            else:
                lines.append(line)
        if lines and "\n".join(lines).strip():
            sections.append(Section("\n".join(lines).strip(), {"section": heading}))
    else:
        raise ParseError("unsupported_parser")
    if not sections or not any(s.text.strip() for s in sections):
        raise ParseError("no_extractable_text")
    return sections, warnings


def chunk_sections(sections: list[Section], words: int = 140, overlap: int = 25):
    """Retain exact section substrings; offsets are normalized section offsets.

    Word budget is conservative for CPU embeddings, not an exact model tokenizer count.
    """
    for section_index, section in enumerate(sections):
        matches = list(re.finditer(r"\S+", section.text))
        for start in range(0, len(matches), words - overlap):
            end = min(start + words, len(matches))
            a, b = matches[start].start(), matches[end - 1].end()
            yield section.text[a:b], {
                **section.location, "section_index": section_index,
                "start": a, "end": b, "offset_basis": "normalized_section",
                "token_count_basis": "word_estimate",
            }, end - start
            if end == len(matches):
                break
