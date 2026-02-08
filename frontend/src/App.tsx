import React, { useState, useCallback } from "react";

import UploadArea from "./components/UploadArea";
import Toolbar from "./components/Toolbar";
import PdfViewer from "./components/PdfViewer";
import EditPanel from "./components/EditPanel";

import { uploadDocument, documentFileUrl, exportDocument } from "./api";
import type { DocumentInfo, EditOperation } from "./types";

/* ── Toast ───────────────────────────────────────────────────────────────── */

interface Toast {
  id: number;
  message: string;
  type: "success" | "error";
}

let toastId = 0;

const ToastContainer: React.FC<{ toasts: Toast[]; onDismiss: (id: number) => void }> = ({
  toasts,
  onDismiss,
}) => (
  <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
    {toasts.map((t) => (
      <button
        key={t.id}
        type="button"
        className={`animate-slide-up flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium shadow-lg cursor-pointer transition-opacity
          ${t.type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"}`}
        onClick={() => onDismiss(t.id)}
      >
        {t.message}
      </button>
    ))}
  </div>
);

/* ── App ─────────────────────────────────────────────────────────────────── */

const App: React.FC = () => {
  const [docInfo, setDocInfo] = useState<DocumentInfo | null>(null);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [zoom, setZoom] = useState(1.5);
  const [edits, setEdits] = useState<EditOperation[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);

  /* ── Toasts ────────────────────────────────────────────────────────────── */
  const addToast = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /* ── Upload ────────────────────────────────────────────────────────────── */
  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      try {
        const info = await uploadDocument(file);
        setDocInfo(info);
        setCurrentPage(0);
        setEdits([]);
        addToast(`"${info.filename}" carregado (${info.pageCount} página${info.pageCount > 1 ? "s" : ""})`);
      } catch (err: any) {
        addToast(err?.message ?? "Erro no upload", "error");
      } finally {
        setUploading(false);
      }
    },
    [addToast],
  );

  /* ── Edit management ───────────────────────────────────────────────────── */
  const handleAddEdit = useCallback((edit: EditOperation) => {
    setEdits((prev) => {
      // Replace if same rect already edited
      const idx = prev.findIndex(
        (e) =>
          e.page === edit.page &&
          Math.abs(e.rect.x0 - edit.rect.x0) < 1 &&
          Math.abs(e.rect.y0 - edit.rect.y0) < 1,
      );
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = edit;
        return next;
      }
      return [...prev, edit];
    });
  }, []);

  const handleRemoveEdit = useCallback((key: string) => {
    setEdits((prev) => prev.filter((e) => e.key !== key));
  }, []);

  const handleGoToEdit = useCallback((edit: EditOperation) => {
    setCurrentPage(edit.page);
  }, []);

  const handleResetEdits = useCallback(() => {
    setEdits([]);
  }, []);

  /* ── Export ────────────────────────────────────────────────────────────── */
  const handleExport = useCallback(async () => {
    if (!docInfo || edits.length === 0) return;
    setExporting(true);
    try {
      const blob = await exportDocument(docInfo.id, edits);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edited_${docInfo.filename}`;
      a.click();
      URL.revokeObjectURL(url);
      addToast("PDF exportado com sucesso!");
    } catch (err: any) {
      addToast(err?.message ?? "Erro ao exportar", "error");
    } finally {
      setExporting(false);
    }
  }, [docInfo, edits, addToast]);

  /* ── Zoom ──────────────────────────────────────────────────────────────── */
  const handleZoomIn = useCallback(() => setZoom((z) => Math.min(z + 0.25, 4)), []);
  const handleZoomOut = useCallback(() => setZoom((z) => Math.max(z - 0.25, 0.5)), []);

  /* ── Pages ─────────────────────────────────────────────────────────────── */
  const handlePrevPage = useCallback(() => setCurrentPage((p) => Math.max(p - 1, 0)), []);
  const handleNextPage = useCallback(
    () => setCurrentPage((p) => Math.min(p + 1, (docInfo?.pageCount ?? 1) - 1)),
    [docInfo],
  );

  /* ── Render ────────────────────────────────────────────────────────────── */

  // No document: show upload
  if (!docInfo) {
    return (
      <>
        <UploadArea onFile={handleFile} loading={uploading} />
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </>
    );
  }

  // Editor view
  return (
    <div className="flex h-screen flex-col">
      <Toolbar
        filename={docInfo.filename}
        currentPage={currentPage}
        pageCount={docInfo.pageCount}
        zoom={zoom}
        editCount={edits.length}
        exporting={exporting}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onExport={handleExport}
        onReset={handleResetEdits}
        onPrevPage={handlePrevPage}
        onNextPage={handleNextPage}
      />

      <div className="flex flex-1 min-h-0">
        <PdfViewer
          docInfo={docInfo}
          pdfUrl={documentFileUrl(docInfo.id)}
          currentPage={currentPage}
          zoom={zoom}
          edits={edits}
          onAddEdit={handleAddEdit}
        />
        <EditPanel
          edits={edits}
          onRemove={handleRemoveEdit}
          onGoTo={handleGoToEdit}
        />
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};

export default App;
