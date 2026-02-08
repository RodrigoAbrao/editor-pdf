"""FastAPI application – PDF Editor Backend."""

from __future__ import annotations
from models import ExportRequest, PageText
import quality_check
import pdf_service
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, HTTPException, UploadFile

import os

from dotenv import load_dotenv
load_dotenv()  # Load .env from backend/ or project root


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="PDF Editor API", version="0.1.0")

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Upload ───────────────────────────────────────────────────────────────────

@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(413, "File too large (max 50 MB).")

    try:
        doc_id = pdf_service.save_upload(content)

        # Extract fonts right after upload (async-ready in the future)
        try:
            pdf_service.extract_fonts(doc_id)
        except Exception:
            # font extraction can fail on some PDFs; continue with fallback fonts
            pass

        page_count = pdf_service.get_page_count(doc_id)
        pages = pdf_service.get_page_dimensions(doc_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Upload failed: {exc}")

    return {
        "id": doc_id,
        "filename": file.filename,
        "pageCount": page_count,
        "pages": pages,
    }


# ── Serve original PDF ──────────────────────────────────────────────────────

@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: str):
    p = pdf_service.pdf_path(doc_id)
    if not p.exists():
        raise HTTPException(404, "Document not found.")
    return FileResponse(p, media_type="application/pdf", filename=f"{doc_id}.pdf")


# ── Text extraction ─────────────────────────────────────────────────────────

@app.get("/api/documents/{doc_id}/pages/{page}/text", response_model=PageText)
def get_page_text(doc_id: str, page: int):
    p = pdf_service.pdf_path(doc_id)
    if not p.exists():
        raise HTTPException(404, "Document not found.")
    page_count = pdf_service.get_page_count(doc_id)
    if page < 0 or page >= page_count:
        raise HTTPException(400, f"Invalid page (0..{page_count - 1}).")
    return pdf_service.extract_page_text(doc_id, page)


# ── Fonts ────────────────────────────────────────────────────────────────────

@app.get("/api/documents/{doc_id}/fonts")
def list_fonts(doc_id: str):
    p = pdf_service.pdf_path(doc_id)
    if not p.exists():
        raise HTTPException(404, "Document not found.")
    fonts = pdf_service.list_extracted_fonts(doc_id)
    return {"fonts": fonts}


@app.get("/api/documents/{doc_id}/fonts/{font_name}")
def get_font_file(doc_id: str, font_name: str):
    path = pdf_service.get_font_path(doc_id, font_name)
    if not path or not path.exists():
        raise HTTPException(404, "Font not found.")
    suffix = path.suffix.lower()
    media_types = {
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }
    return FileResponse(path, media_type=media_types.get(suffix, "application/octet-stream"))


# ── Export (overlay) ─────────────────────────────────────────────────────────

@app.post("/api/documents/{doc_id}/export")
def export_document(doc_id: str, body: ExportRequest):
    p = pdf_service.pdf_path(doc_id)
    if not p.exists():
        raise HTTPException(404, "Document not found.")

    try:
        result_bytes = pdf_service.apply_edits(doc_id, body.edits)
    except Exception as exc:
        raise HTTPException(500, f"Export failed: {exc}")

    # Run quality validation if OpenAI key is configured
    try:
        edits_dicts = [e.model_dump() for e in body.edits]
        reports = quality_check.validate_edit_quality(
            str(p), result_bytes, edits_dicts
        )

        # Auto-repair if issues found
        if reports and any(not r.passed for r in reports):
            repaired = quality_check.auto_repair_edits(
                str(p), result_bytes, edits_dicts, reports
            )
            if repaired:
                result_bytes = repaired
    except Exception as exc:
        # Quality check is best-effort; don't block export
        import logging
        logging.getLogger(__name__).warning(
            "Quality check skipped: %s", exc
        )

    return Response(
        content=result_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="edited_{doc_id}.pdf"'},
    )


# ── Quality check (standalone) ───────────────────────────────────────────────

@app.post("/api/documents/{doc_id}/quality-check")
def check_quality(doc_id: str, body: ExportRequest):
    """Run quality validation without downloading — returns report."""
    p = pdf_service.pdf_path(doc_id)
    if not p.exists():
        raise HTTPException(404, "Document not found.")

    try:
        result_bytes = pdf_service.apply_edits(doc_id, body.edits)
        edits_dicts = [e.model_dump() for e in body.edits]
        reports = quality_check.validate_edit_quality(
            str(p), result_bytes, edits_dicts
        )
    except Exception as exc:
        raise HTTPException(500, f"Quality check failed: {exc}")

    return {
        "reports": [
            {
                "edit_index": r.edit_index,
                "page": r.page,
                "passed": r.passed,
                "issues": [
                    {
                        "severity": iss.severity,
                        "description": iss.description,
                        "suggestion": iss.suggestion,
                    }
                    for iss in r.issues
                ],
            }
            for r in reports
        ]
    }
