"""Pydantic models for request/response validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Rect(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class TextSpan(BaseModel):
    text: str
    font: str
    size: float
    color: str  # hex "#RRGGBB"
    rect: Rect
    flags: int = 0  # bold / italic bitflags from PyMuPDF
    origin_y: float = 0.0  # baseline Y position


class PageText(BaseModel):
    page: int
    width: float
    height: float
    spans: list[TextSpan]


class PageDimension(BaseModel):
    page: int
    width: float
    height: float


class DocumentInfo(BaseModel):
    id: str
    filename: str
    page_count: int
    pages: list[PageDimension] | None = None


class EditOperation(BaseModel):
    """A single overlay edit to apply on the PDF."""

    page: int = Field(..., ge=0, description="0-based page number")
    rect: Rect
    original_text: str = ""
    new_text: str
    font: str = "helv"
    font_size: float = 11.0
    color: str = "#000000"
    flags: int = 0  # bold/italic bitflags
    origin_y: float = 0.0  # baseline Y


class ExportRequest(BaseModel):
    edits: list[EditOperation]
