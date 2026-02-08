"""Core PDF processing: text extraction, font extraction, overlay editing."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import fitz  # PyMuPDF

from models import EditOperation, PageText, Rect, TextSpan

# ── directories ──────────────────────────────────────────────────────────────
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
UPLOADS_DIR = DATA_DIR / "uploads"
FONTS_DIR = DATA_DIR / "fonts"

for _d in (UPLOADS_DIR, FONTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _color_to_hex(color: int | float | tuple) -> str:
    """Convert PyMuPDF colour value to hex string."""
    if isinstance(color, (int, float)):
        v = int(color * 255)
        return f"#{v:02X}{v:02X}{v:02X}"
    if isinstance(color, (list, tuple)) and len(color) == 3:
        r, g, b = (int(c * 255) for c in color)
        return f"#{r:02X}{g:02X}{b:02X}"
    return "#000000"


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """'#RRGGBB' → (r, g, b) in 0..1"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255, g / 255, b / 255


def _clean_font_name(raw: str) -> str:
    """Strip subset prefix (e.g. 'BCDEEE+ArialMT' → 'ArialMT')."""
    return re.sub(r"^[A-Z]{6}\+", "", raw)


# ── save upload ──────────────────────────────────────────────────────────────

def save_upload(file_bytes: bytes) -> str:
    """Save uploaded PDF, return document id (hash)."""
    doc_id = hashlib.sha256(file_bytes).hexdigest()[:16]
    dest = UPLOADS_DIR / f"{doc_id}.pdf"
    dest.write_bytes(file_bytes)
    return doc_id


def pdf_path(doc_id: str) -> Path:
    return UPLOADS_DIR / f"{doc_id}.pdf"


# ── document info ────────────────────────────────────────────────────────────

def get_page_count(doc_id: str) -> int:
    with fitz.open(pdf_path(doc_id)) as doc:
        return doc.page_count


def get_page_dimensions(doc_id: str) -> list[dict]:
    dims: list[dict] = []
    with fitz.open(pdf_path(doc_id)) as doc:
        for i, page in enumerate(doc):
            r = page.rect
            dims.append({"page": i, "width": r.width, "height": r.height})
    return dims


# ── font extraction ─────────────────────────────────────────────────────────

def extract_fonts(doc_id: str) -> dict[str, str]:
    """Extract embedded fonts from a PDF. Returns {clean_name: file_path}."""
    fonts_map: dict[str, str] = {}
    doc_fonts_dir = FONTS_DIR / doc_id
    doc_fonts_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path(doc_id)) as doc:
        seen_xrefs: set[int] = set()
        for page in doc:
            for xref, _ext, _type, _basefont, name, _enc in page.get_fonts(full=True):
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    basename, ext, _subtype, content = doc.extract_font(xref)
                except Exception:
                    continue
                if not content:
                    continue
                clean = _clean_font_name(basename or name)
                if not clean:
                    continue
                ext = ext or "ttf"
                font_file = doc_fonts_dir / f"{clean}.{ext}"
                font_file.write_bytes(content)
                fonts_map[clean] = str(font_file)
    return fonts_map


def get_font_path(doc_id: str, font_name: str) -> Path | None:
    """Return path to an extracted font file, or None."""
    doc_fonts_dir = FONTS_DIR / doc_id
    for ext in ("ttf", "otf", "cff", "woff", "woff2"):
        p = doc_fonts_dir / f"{font_name}.{ext}"
        if p.exists():
            return p
    return None


def list_extracted_fonts(doc_id: str) -> list[str]:
    doc_fonts_dir = FONTS_DIR / doc_id
    if not doc_fonts_dir.exists():
        return []
    return [p.stem for p in doc_fonts_dir.iterdir() if p.is_file()]


# ── text extraction ──────────────────────────────────────────────────────────

def extract_page_text(doc_id: str, page_num: int) -> PageText:
    """Extract all text spans from a page with full font metadata."""
    with fitz.open(pdf_path(doc_id)) as doc:
        page = doc[page_num]
        rect = page.rect
        data = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    spans: list[TextSpan] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                bbox = span["bbox"]
                spans.append(
                    TextSpan(
                        text=text,
                        font=_clean_font_name(span.get("font", "")),
                        size=round(span.get("size", 11), 2),
                        color=_color_to_hex(span.get("color", 0)),
                        rect=Rect(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]),
                        flags=span.get("flags", 0),
                    )
                )
    return PageText(page=page_num, width=rect.width, height=rect.height, spans=spans)


# ── overlay export ───────────────────────────────────────────────────────────

def apply_edits(doc_id: str, edits: list[EditOperation]) -> bytes:
    """Apply overlay edits and return the resulting PDF bytes."""
    doc = fitz.open(pdf_path(doc_id))

    doc_fonts_dir = FONTS_DIR / doc_id

    for edit in edits:
        page = doc[edit.page]
        r = fitz.Rect(edit.rect.x0, edit.rect.y0, edit.rect.x1, edit.rect.y1)

        # 1) Cover original text with white rectangle
        shape = page.new_shape()
        shape.draw_rect(r)
        shape.finish(color=None, fill=(1, 1, 1))  # white fill
        shape.commit()

        # 2) Determine font to use
        font_name = edit.font
        fitz_fontname = "helv"  # fallback
        fontfile = None

        # Try to use the extracted font
        if font_name and doc_fonts_dir.exists():
            extracted = get_font_path(doc_id, font_name)
            if extracted and extracted.exists():
                fontfile = str(extracted)
                fitz_fontname = None  # will use fontfile instead

        # 3) Insert new text
        text_color = _hex_to_rgb(edit.color)

        try:
            if fontfile:
                page.insert_textbox(
                    r,
                    edit.new_text,
                    fontfile=fontfile,
                    fontsize=edit.font_size,
                    color=text_color,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            else:
                page.insert_textbox(
                    r,
                    edit.new_text,
                    fontname=fitz_fontname,
                    fontsize=edit.font_size,
                    color=text_color,
                    align=fitz.TEXT_ALIGN_LEFT,
                )
        except Exception:
            # Fallback: use Helvetica
            page.insert_textbox(
                r,
                edit.new_text,
                fontname="helv",
                fontsize=edit.font_size,
                color=text_color,
                align=fitz.TEXT_ALIGN_LEFT,
            )

    result = doc.tobytes(deflate=True, garbage=4)
    doc.close()
    return result
