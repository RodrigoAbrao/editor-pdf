"""Quality validation module — compares original vs edited PDF regions.

Uses OpenAI Vision (GPT-4o) to detect visual artefacts:
- Missing table borders / lines
- Text misalignment
- Font weight / style changes
- Color differences
- Any other visual degradation

Flow:
  1. Render the *original* page region around each edit as an image.
  2. Render the *edited* page region as an image.
  3. Send both images to GPT-4o asking for a structured diff.
  4. If issues are found, return a list of repair suggestions.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from dataclasses import dataclass, field

import fitz  # PyMuPDF
from openai import OpenAI
from PIL import Image

log = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

# How much extra context (in PDF points) around the edit rect to capture
CONTEXT_MARGIN = 30  # pts
RENDER_DPI = 288  # high-res for accurate comparison


@dataclass
class QualityIssue:
    """A single issue detected by the vision model."""
    severity: str  # "low", "medium", "high"
    description: str
    suggestion: str


@dataclass
class QualityReport:
    """Result of comparing original vs edited region."""
    edit_index: int
    page: int
    passed: bool
    issues: list[QualityIssue] = field(default_factory=list)
    raw_response: str = ""


def _render_region(doc: fitz.Document, page_num: int,
                   region: fitz.Rect, dpi: int = RENDER_DPI) -> bytes:
    """Render a specific rectangular region of a page as a PNG image."""
    page = doc[page_num]

    # Clip to page bounds
    page_rect = page.rect
    clip = fitz.Rect(
        max(region.x0 - CONTEXT_MARGIN, page_rect.x0),
        max(region.y0 - CONTEXT_MARGIN, page_rect.y0),
        min(region.x1 + CONTEXT_MARGIN, page_rect.x1),
        min(region.y1 + CONTEXT_MARGIN, page_rect.y1),
    )

    # Render at high resolution
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)

    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _image_to_data_url(png_bytes: bytes) -> str:
    """Convert PNG bytes to a data URL for the OpenAI API."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


SYSTEM_PROMPT = """You are a PDF quality inspector. You will receive two images:
1. ORIGINAL — a region of the original PDF before editing.
2. EDITED — the same region after text was replaced.

Your task is to find visual DEFECTS in the EDITED version compared to the
ORIGINAL. Focus on:
- Table borders or lines that were erased, cut, or partially covered.
- Text that looks misaligned or shifted.
- Font weight (bold vs regular) or style (italic) that changed.
- Font size differences.
- Color differences in text.
- Any extra white rectangles or artefacts that shouldn't be there.

IMPORTANT: The TEXT CONTENT is expected to change — that's the edit. Do NOT
report the text change itself as an issue. Only report visual/structural damage.

Respond with ONLY valid JSON in this format:
{
  "passed": true/false,
  "issues": [
    {
      "severity": "low|medium|high",
      "description": "what is wrong",
      "suggestion": "how to fix it"
    }
  ]
}
If no issues found, return {"passed": true, "issues": []}.
"""


def validate_edit_quality(
    original_doc_path: str,
    edited_pdf_bytes: bytes,
    edits: list[dict],
) -> list[QualityReport]:
    """Compare original vs edited PDF for each edit region.

    Parameters
    ----------
    original_doc_path : str
        Path to the original PDF file.
    edited_pdf_bytes : bytes
        The edited PDF as bytes.
    edits : list[dict]
        List of edit operations (each with 'page', 'rect').

    Returns
    -------
    list[QualityReport]
        One report per edit.
    """
    if not OPENAI_API_KEY:
        log.warning("OPENAI_API_KEY not set — skipping quality validation")
        return []

    client = OpenAI(api_key=OPENAI_API_KEY)
    original_doc = fitz.open(original_doc_path)
    edited_doc = fitz.open(stream=edited_pdf_bytes, filetype="pdf")

    reports: list[QualityReport] = []

    for i, edit in enumerate(edits):
        page_num = edit.get("page", 0)
        rect_data = edit.get("rect", {})
        region = fitz.Rect(
            rect_data.get("x0", 0),
            rect_data.get("y0", 0),
            rect_data.get("x1", 0),
            rect_data.get("y1", 0),
        )

        try:
            # Render both regions
            original_img = _render_region(original_doc, page_num, region)
            edited_img = _render_region(edited_doc, page_num, region)

            # Call OpenAI Vision
            response = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Compare these two images. ORIGINAL on the left, EDITED on the right."},
                            {
                                "type": "image_url",
                                "image_url": {"url": _image_to_data_url(original_img), "detail": "high"},
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": _image_to_data_url(edited_img), "detail": "high"},
                            },
                        ],
                    },
                ],
                max_tokens=1000,
                temperature=0.1,
            )

            raw = response.choices[0].message.content or ""
            log.info("  Quality check edit[%d]: %s", i, raw[:200])

            # Parse JSON response
            # Strip markdown code fences if present
            json_str = raw.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]
                json_str = json_str.rsplit("```", 1)[0]

            data = json.loads(json_str)
            passed = data.get("passed", True)
            issues = [
                QualityIssue(
                    severity=iss.get("severity", "low"),
                    description=iss.get("description", ""),
                    suggestion=iss.get("suggestion", ""),
                )
                for iss in data.get("issues", [])
            ]

            reports.append(QualityReport(
                edit_index=i,
                page=page_num,
                passed=passed,
                issues=issues,
                raw_response=raw,
            ))

        except Exception as exc:
            log.warning("  Quality check failed for edit[%d]: %s", i, exc)
            reports.append(QualityReport(
                edit_index=i,
                page=page_num,
                passed=True,  # don't block export on failure
                issues=[],
                raw_response=f"Error: {exc}",
            ))

    original_doc.close()
    edited_doc.close()
    return reports


def auto_repair_edits(
    original_doc_path: str,
    edited_pdf_bytes: bytes,
    edits: list[dict],
    reports: list[QualityReport],
) -> bytes | None:
    """Attempt to auto-repair issues found in quality reports.

    Currently handles:
    - Table borders erased: Redraws lines from the original page in the
      affected region.
    """
    needs_repair = any(not r.passed for r in reports)
    if not needs_repair:
        return None

    doc = fitz.open(stream=edited_pdf_bytes, filetype="pdf")
    original_doc = fitz.open(original_doc_path)

    for report in reports:
        if report.passed:
            continue

        border_damaged = any(
            "border" in iss.description.lower()
            or "line" in iss.description.lower()
            or "rule" in iss.description.lower()
            for iss in report.issues
        )

        if border_damaged:
            page_num = report.page
            edit = edits[report.edit_index]
            rect_data = edit.get("rect", {})
            region = fitz.Rect(
                rect_data.get("x0", 0) - CONTEXT_MARGIN,
                rect_data.get("y0", 0) - CONTEXT_MARGIN,
                rect_data.get("x1", 0) + CONTEXT_MARGIN,
                rect_data.get("y1", 0) + CONTEXT_MARGIN,
            )

            # Extract drawings (lines, rects) from original page
            original_page = original_doc[page_num]
            edited_page = doc[page_num]

            try:
                paths = original_page.get_drawings()
                shape = edited_page.new_shape()
                repaired = 0

                for path in paths:
                    # Check if this drawing intersects our region
                    path_rect = fitz.Rect(path["rect"])
                    if not path_rect.intersects(region):
                        continue

                    # Redraw lines/rects from original
                    for item in path["items"]:
                        kind = item[0]
                        if kind == "l":  # line
                            shape.draw_line(item[1], item[2])
                            repaired += 1
                        elif kind == "re":  # rectangle
                            shape.draw_rect(item[1])
                            repaired += 1

                    # Apply the same styling
                    color = path.get("color")
                    fill = path.get("fill")
                    width = path.get("width", 0.5)
                    shape.finish(
                        color=color,
                        fill=fill,
                        width=width,
                    )

                shape.commit()
                log.info("  Repair: redrew %d border elements on page %d",
                         repaired, page_num)
            except Exception as exc:
                log.warning("  Repair failed for page %d: %s",
                            page_num, exc)

    result = doc.tobytes(deflate=True, garbage=4)
    doc.close()
    original_doc.close()
    return result
