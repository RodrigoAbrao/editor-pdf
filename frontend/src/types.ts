/* ── Shared types ────────────────────────────────────────────────────────── */

export interface Rect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface TextSpan {
  text: string;
  font: string;
  size: number;
  color: string;
  rect: Rect;
  flags: number;
}

export interface PageText {
  page: number;
  width: number;
  height: number;
  spans: TextSpan[];
}

export interface PageDimension {
  page: number;
  width: number;
  height: number;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  pageCount: number;
  pages: PageDimension[];
}

export interface EditOperation {
  /** unique client-side key */
  key: string;
  page: number;
  rect: Rect;
  original_text: string;
  new_text: string;
  font: string;
  font_size: number;
  color: string;
}
