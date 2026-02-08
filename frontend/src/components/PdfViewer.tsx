import React, { useEffect, useRef, useState, useCallback } from "react";
import * as pdfjsLib from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";

import { getPageText, fontFileUrl, listFonts } from "../api";
import type { DocumentInfo, EditOperation, PageText, TextSpan } from "../types";

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

/* ── helpers ─────────────────────────────────────────────────────────────── */

let _editCounter = 0;
function nextEditKey() {
  return `edit-${++_editCounter}`;
}

/* ── Props ───────────────────────────────────────────────────────────────── */

interface Props {
  docInfo: DocumentInfo;
  pdfUrl: string;
  currentPage: number;
  zoom: number;
  edits: EditOperation[];
  onAddEdit: (edit: EditOperation) => void;
}

/* ── Component ───────────────────────────────────────────────────────────── */

const PdfViewer: React.FC<Props> = ({
  docInfo,
  pdfUrl,
  currentPage,
  zoom,
  edits,
  onAddEdit,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [pdfDoc, setPdfDoc] = useState<PDFDocumentProxy | null>(null);
  const [pageText, setPageText] = useState<PageText | null>(null);
  const [loadedFonts, setLoadedFonts] = useState<Set<string>>(new Set());
  const [editingSpan, setEditingSpan] = useState<TextSpan | null>(null);
  const [editValue, setEditValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  /* ── Load PDF document ────────────────────────────────────────────────── */
  useEffect(() => {
    let cancelled = false;
    pdfjsLib.getDocument(pdfUrl).promise.then((doc) => {
      if (!cancelled) setPdfDoc(doc);
    });
    return () => {
      cancelled = true;
    };
  }, [pdfUrl]);

  /* ── Load & register extracted fonts ──────────────────────────────────── */
  useEffect(() => {
    let cancelled = false;

    async function loadFonts() {
      try {
        const fontNames = await listFonts(docInfo.id);
        for (const name of fontNames) {
          if (loadedFonts.has(name)) continue;
          const url = fontFileUrl(docInfo.id, name);
          try {
            const face = new FontFace(name, `url(${url})`);
            const loaded = await face.load();
            document.fonts.add(loaded);
            if (!cancelled) {
              setLoadedFonts((prev) => new Set(prev).add(name));
            }
          } catch {
            // font load failed – will use fallback
          }
        }
      } catch {
        // listing fonts failed
      }
    }

    loadFonts();
    return () => {
      cancelled = true;
    };
  }, [docInfo.id]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Render page ──────────────────────────────────────────────────────── */
  useEffect(() => {
    if (!pdfDoc) return;
    let cancelled = false;

    async function render() {
      const page: PDFPageProxy = await pdfDoc!.getPage(currentPage + 1);
      const viewport = page.getViewport({ scale: zoom });
      const canvas = canvasRef.current!;
      const ctx = canvas.getContext("2d")!;

      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      await page.render({ canvasContext: ctx, viewport }).promise;

      // Fetch text spans for overlay
      if (!cancelled) {
        try {
          const text = await getPageText(docInfo.id, currentPage);
          setPageText(text);
        } catch {
          setPageText(null);
        }
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [pdfDoc, currentPage, zoom, docInfo.id]);

  /* ── Focus input when editing ─────────────────────────────────────────── */
  useEffect(() => {
    if (editingSpan && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingSpan]);

  /* ── Handle span click → start editing ────────────────────────────────── */
  const handleSpanClick = useCallback(
    (span: TextSpan) => {
      // Check if already edited
      const existing = edits.find(
        (e) =>
          e.page === currentPage &&
          Math.abs(e.rect.x0 - span.rect.x0) < 1 &&
          Math.abs(e.rect.y0 - span.rect.y0) < 1,
      );
      setEditingSpan(span);
      setEditValue(existing?.new_text ?? span.text);
    },
    [edits, currentPage],
  );

  /* ── Confirm edit ─────────────────────────────────────────────────────── */
  const confirmEdit = useCallback(() => {
    if (!editingSpan) return;
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== editingSpan.text) {
      onAddEdit({
        key: nextEditKey(),
        page: currentPage,
        rect: editingSpan.rect,
        original_text: editingSpan.text,
        new_text: trimmed,
        font: editingSpan.font,
        font_size: editingSpan.size,
        color: editingSpan.color,
      });
    }
    setEditingSpan(null);
    setEditValue("");
  }, [editingSpan, editValue, currentPage, onAddEdit]);

  /* ── Cancel edit ──────────────────────────────────────────────────────── */
  const cancelEdit = useCallback(() => {
    setEditingSpan(null);
    setEditValue("");
  }, []);

  /* ── Compute span style (PDF coords → screen coords) ─────────────────── */
  const spanStyle = useCallback(
    (span: TextSpan): React.CSSProperties => {
      if (!pageText) return {};
      const scaleX = zoom;
      const scaleY = zoom;
      return {
        position: "absolute",
        left: `${span.rect.x0 * scaleX}px`,
        top: `${span.rect.y0 * scaleY}px`,
        width: `${(span.rect.x1 - span.rect.x0) * scaleX}px`,
        height: `${(span.rect.y1 - span.rect.y0) * scaleY}px`,
      };
    },
    [pageText, zoom],
  );

  /* ── Check if a span was edited ───────────────────────────────────────── */
  const getEditForSpan = useCallback(
    (span: TextSpan): EditOperation | undefined => {
      return edits.find(
        (e) =>
          e.page === currentPage &&
          Math.abs(e.rect.x0 - span.rect.x0) < 1 &&
          Math.abs(e.rect.y0 - span.rect.y0) < 1,
      );
    },
    [edits, currentPage],
  );

  /* ── Render ────────────────────────────────────────────────────────────── */
  const pageW = pageText ? pageText.width * zoom : 0;
  const pageH = pageText ? pageText.height * zoom : 0;

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-auto pdf-scroll bg-gray-100 flex items-start justify-center p-8"
    >
      <div
        className="relative shadow-2xl shadow-gray-300/50 rounded-sm"
        style={{ width: pageW || undefined, height: pageH || undefined }}
      >
        {/* Canvas */}
        <canvas ref={canvasRef} className="block" />

        {/* Text overlay */}
        <div
          ref={overlayRef}
          className="absolute inset-0"
          style={{ width: pageW, height: pageH }}
        >
          {pageText?.spans.map((span, i) => {
            const edit = getEditForSpan(span);
            const isEditing = editingSpan === span;
            const isEdited = !!edit;

            return (
              <div
                key={`${span.rect.x0}-${span.rect.y0}-${i}`}
                role="button"
                tabIndex={0}
                className={`span-highlight ${isEdited ? "span-edited" : ""}`}
                style={spanStyle(span)}
                onClick={() => handleSpanClick(span)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleSpanClick(span); }}
                title={isEdited ? `"${edit!.original_text}" → "${edit!.new_text}"` : span.text}
              >
                {/* Inline editor */}
                {isEditing && (
                  <div
                    role="presentation"
                    className="absolute left-0 top-full z-50 mt-1 animate-fade-in"
                    style={{ minWidth: "240px" }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="rounded-xl bg-white p-3 shadow-xl border border-gray-200">
                      <p className="mb-1.5 text-[10px] font-medium text-gray-400 uppercase tracking-wider">
                        Editar texto
                      </p>
                      <p className="mb-2 text-[10px] text-gray-400 truncate">
                        Fonte: {span.font} • {span.size}pt
                      </p>
                      <input
                        ref={inputRef}
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") confirmEdit();
                          if (e.key === "Escape") cancelEdit();
                        }}
                        className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 transition"
                        style={{
                          fontFamily: loadedFonts.has(span.font)
                            ? `"${span.font}", sans-serif`
                            : "sans-serif",
                        }}
                      />
                      <div className="mt-2 flex justify-end gap-1.5">
                        <button
                          onClick={cancelEdit}
                          className="rounded-lg px-3 py-1 text-xs text-gray-500 transition hover:bg-gray-100"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={confirmEdit}
                          className="rounded-lg bg-brand-600 px-3 py-1 text-xs font-medium text-white transition hover:bg-brand-700"
                        >
                          Aplicar
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PdfViewer;
