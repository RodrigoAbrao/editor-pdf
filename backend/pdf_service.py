"""Core PDF processing: text extraction, font extraction, overlay editing."""

from __future__ import annotations
from models import EditOperation, PageText, Rect, TextSpan

import hashlib
import logging
import os
import re
from pathlib import Path

import fitz  # PyMuPDF

log = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


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


# Map common PDF font names to fitz builtin fontnames.
# fitz builtins: helv, heit (italic), hebo (bold), hebi (bold-italic),
#   cour, coit, cobo, cobi, tiro, tiit, tibo, tibi, symb, zadb
_BUILTIN_FONT_MAP: dict[str, str] = {
    # Helvetica family
    "helvetica": "helv",
    "helvetica-bold": "hebo",
    "helvetica-oblique": "heit",
    "helvetica-boldoblique": "hebi",
    # Arial mapped to Helvetica equivalents
    "arial": "helv",
    "arialmt": "helv",
    "arial-boldmt": "hebo",
    "arial-bold": "hebo",
    "arial-italicmt": "heit",
    "arial-bolditalicmt": "hebi",
    # Times family
    "times-roman": "tiro",
    "timesnewromanpsmt": "tiro",
    "times-bold": "tibo",
    "timesnewromanps-boldmt": "tibo",
    "times-italic": "tiit",
    "times-bolditalic": "tibi",
    # Courier family
    "courier": "cour",
    "courier-bold": "cobo",
    "courier-oblique": "coit",
    "courier-boldoblique": "cobi",
    "couriernewpsmt": "cour",
    "couriernewps-boldmt": "cobo",
    # Symbol / ZapfDingbats
    "symbol": "symb",
    "zapfdingbats": "zadb",
}


def _resolve_builtin_font(font_name: str, flags: int = 0) -> str:
    """Resolve a PDF font name to a fitz builtin fontname.

    Uses the name first, then falls back to flags (bold/italic bits).
    """
    key = font_name.lower().replace(" ", "")
    if key in _BUILTIN_FONT_MAP:
        return _BUILTIN_FONT_MAP[key]

    # Heuristic: check if name contains bold/italic hints
    is_bold = "bold" in key or (flags & 0x10)
    is_italic = "italic" in key or "oblique" in key or (flags & 0x02)

    if is_bold and is_italic:
        return "hebi"
    if is_bold:
        return "hebo"
    if is_italic:
        return "heit"
    return "helv"


# ── save upload ──────────────────────────────────────────────────────────────

def save_upload(file_bytes: bytes) -> str:
    """Save uploaded PDF, return document id (hash)."""
    doc_id = hashlib.sha256(file_bytes).hexdigest()[:16]
    dest = UPLOADS_DIR / f"{doc_id}.pdf"
    dest.write_bytes(file_bytes)
    # Validate PDF
    try:
        with fitz.open(dest):
            pass
    except Exception as exc:
        if dest.exists():
            dest.unlink(missing_ok=True)
        raise ValueError("Invalid PDF file") from exc
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
                # origin is the baseline point (x, y)
                origin = span.get("origin", (bbox[0], bbox[3]))
                spans.append(
                    TextSpan(
                        text=text,
                        font=_clean_font_name(span.get("font", "")),
                        size=round(span.get("size", 11), 2),
                        color=_color_to_hex(span.get("color", 0)),
                        rect=Rect(x0=bbox[0], y0=bbox[1],
                                  x1=bbox[2], y1=bbox[3]),
                        flags=span.get("flags", 0),
                        origin_y=origin[1],
                    )
                )
    return PageText(page=page_num, width=rect.width, height=rect.height, spans=spans)


# ── signature removal ────────────────────────────────────────────────────────

def _remove_signatures(doc: fitz.Document) -> None:
    """Remove all signature widgets and annotation signatures from the PDF.

    This is necessary because signed PDFs may block modifications.
    We strip signature fields so edits can be freely applied.
    """
    removed = 0
    for page in doc:
        # Remove signature widgets
        widgets = page.widgets()
        if widgets:
            for widget in widgets:
                try:
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                        widget_rect = widget.rect
                        page.delete_widget(widget)
                        removed += 1
                        log.info(
                            "  Removed signature widget at %s", widget_rect)
                except Exception as exc:
                    log.warning("  Failed to remove signature widget: %s", exc)

        # Remove signature annotations
        annots = page.annots()
        if annots:
            to_delete = []
            for annot in annots:
                try:
                    if annot.type[0] == fitz.PDF_ANNOT_WIDGET:
                        # Check if it's a signature field via info
                        info = annot.info
                        if info.get("title", "").lower().startswith("sig"):
                            to_delete.append(annot)
                except Exception:
                    pass
            for annot in to_delete:
                try:
                    page.delete_annot(annot)
                    removed += 1
                except Exception:
                    pass

    if removed:
        log.info("  Removed %d signature(s) from PDF", removed)


# ── overlay export ───────────────────────────────────────────────────────────

def apply_edits(doc_id: str, edits: list[EditOperation]) -> bytes:
    """Apply overlay edits and return the resulting PDF bytes."""
    log.info("apply_edits called with %d edits for doc %s", len(edits), doc_id)
    for i, e in enumerate(edits):
        log.info(
            "  edit[%d]: page=%d rect=(%.1f,%.1f,%.1f,%.1f) font=%s size=%.1f '%s' -> '%s'",
            i, e.page, e.rect.x0, e.rect.y0, e.rect.x1, e.rect.y1,
            e.font, e.font_size, e.original_text, e.new_text,
        )

    doc = fitz.open(pdf_path(doc_id))

    # Remove digital signatures so edits can be applied.
    # Signatures lock the PDF content; we need to strip them first.
    _remove_signatures(doc)

    doc_fonts_dir = FONTS_DIR / doc_id

    for edit in edits:
        page = doc[edit.page]
        r = fitz.Rect(edit.rect.x0, edit.rect.y0, edit.rect.x1, edit.rect.y1)

        # If a form field (widget) overlaps, update it directly
        widgets = page.widgets()
        if widgets:
            widget_updated = False
            for widget in widgets:
                try:
                    if widget.rect.intersects(r):
                        log.info("  -> Widget found! field_name=%s old_value='%s' -> '%s'",
                                 widget.field_name, widget.field_value, edit.new_text)
                        widget.field_value = edit.new_text
                        widget.update()
                        widget_updated = True
                except Exception as exc:
                    log.warning("  -> Widget update failed: %s", exc)
                    continue
            if widget_updated:
                continue

        # 1) Cover original text with a precise white rectangle.
        #    Use NO horizontal padding so we don't eat table borders.
        #    Vertically shrink by a tiny amount to preserve horizontal rules.
        log.info("  -> Overlay mode: drawing white rect + text")
        v_shrink = 0.3
        cover_rect = fitz.Rect(
            r.x0, r.y0 + v_shrink,
            r.x1, r.y1 - v_shrink,
        )
        shape = page.new_shape()
        shape.draw_rect(cover_rect)
        shape.finish(color=None, fill=(1, 1, 1))  # white fill
        shape.commit()

        # 2) Determine font to use
        font_name = edit.font
        fontfile = None

        # Try to use the extracted font
        if font_name and doc_fonts_dir.exists():
            extracted = get_font_path(doc_id, font_name)
            if extracted and extracted.exists():
                fontfile = str(extracted)

        # 3) Insert new text using insert_text (absolute position, no padding)
        #    Use the original baseline Y from the span if available.
        text_color = _hex_to_rgb(edit.color)

        if edit.origin_y and edit.origin_y > 0:
            baseline_y = edit.origin_y
        else:
            baseline_y = r.y1 - (edit.font_size * 0.2)

        insert_point = fitz.Point(r.x0, baseline_y)

        # Resolve builtin font name (bold, italic, etc.)
        builtin_name = _resolve_builtin_font(font_name or "", edit.flags)

        try:
            if fontfile:
                log.info("  -> Using extracted font file: %s", fontfile)
                page.insert_text(
                    insert_point,
                    edit.new_text,
                    fontfile=fontfile,
                    fontsize=edit.font_size,
                    color=text_color,
                )
            else:
                log.info("  -> Using builtin font: %s (from '%s', flags=%d)",
                         builtin_name, font_name, edit.flags)
                page.insert_text(
                    insert_point,
                    edit.new_text,
                    fontname=builtin_name,
                    fontsize=edit.font_size,
                    color=text_color,
                )
            log.info("  -> insert_text OK at (%.1f, %.1f)", r.x0, baseline_y)
        except Exception as exc:
            log.warning(
                "  -> insert_text with font failed (%s), using helv fallback", exc)
            # Fallback: use Helvetica
            page.insert_text(
                insert_point,
                edit.new_text,
                fontname="helv",
                fontsize=edit.font_size,
                color=text_color,
            )

    result = doc.tobytes(deflate=True, garbage=4)
    doc.close()
    return result
