from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
from docx import Document as DocxDocument


@dataclass
class ParsedBlock:
    text: str
    page_no: int | None = None
    section_path: list[str] = field(default_factory=list)
    paragraph_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None


def parse_document(path: Path) -> list[ParsedBlock]:
    extension = path.suffix.lower()
    if extension == ".pdf":
        return _parse_pdf(path)
    if extension == ".docx":
        return _parse_docx(path)
    if extension == ".md":
        return _parse_markdown(path)
    raise ValueError(f"Unsupported document extension: {extension}")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def _parse_pdf(path: Path) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    document = pymupdf.open(path)
    try:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text")
            for paragraph_index, paragraph in enumerate(text.split("\n\n")):
                normalized = _clean_text(paragraph)
                if normalized:
                    blocks.append(
                        ParsedBlock(
                            text=normalized,
                            page_no=page_index,
                            paragraph_index=paragraph_index,
                        )
                    )
    finally:
        document.close()
    return blocks


def _parse_docx(path: Path) -> list[ParsedBlock]:
    document = DocxDocument(path)
    blocks: list[ParsedBlock] = []
    section_path: list[str] = []

    for paragraph_index, paragraph in enumerate(document.paragraphs):
        text = _clean_text(paragraph.text)
        if not text:
            continue

        style_name = paragraph.style.name if paragraph.style else ""
        heading_level = _heading_level(style_name)
        if heading_level is not None:
            section_path = section_path[: heading_level - 1]
            section_path.append(text)
            continue

        blocks.append(
            ParsedBlock(
                text=text,
                section_path=list(section_path),
                paragraph_index=paragraph_index,
            )
        )
    return blocks


def _parse_markdown(path: Path) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    section_path: list[str] = []
    paragraph_index = 0

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_level = _markdown_heading_level(line)
        if heading_level is not None:
            title = line[heading_level:].strip()
            section_path = section_path[: heading_level - 1]
            section_path.append(title)
            continue

        if line.startswith(("- ", "* ", "+ ")):
            line = line[2:].strip()

        blocks.append(
            ParsedBlock(
                text=line,
                section_path=list(section_path),
                paragraph_index=paragraph_index,
            )
        )
        paragraph_index += 1
    return blocks


def _heading_level(style_name: str) -> int | None:
    if not style_name.lower().startswith("heading"):
        return None
    try:
        return int(style_name.split()[-1])
    except ValueError:
        return None


def _markdown_heading_level(line: str) -> int | None:
    if not line.startswith("#"):
        return None
    level = len(line) - len(line.lstrip("#"))
    if 1 <= level <= 6 and len(line) > level and line[level] == " ":
        return level
    return None
