import React from "react";
import {
  ZoomIn,
  ZoomOut,
  Download,
  RotateCcw,
  FileText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface Props {
  filename: string;
  currentPage: number;
  pageCount: number;
  zoom: number;
  editCount: number;
  exporting: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onExport: () => void;
  onReset: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
}

const Toolbar: React.FC<Props> = ({
  filename,
  currentPage,
  pageCount,
  zoom,
  editCount,
  exporting,
  onZoomIn,
  onZoomOut,
  onExport,
  onReset,
  onPrevPage,
  onNextPage,
}) => {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4 shadow-sm">
      {/* Left: logo + filename */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
          <FileText className="h-4 w-4 text-white" />
        </div>
        <span className="truncate text-sm font-semibold text-gray-800 max-w-[200px]">
          {filename}
        </span>
      </div>

      {/* Center: page nav + zoom */}
      <div className="flex items-center gap-1">
        <button
          onClick={onPrevPage}
          disabled={currentPage <= 0}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-gray-100 disabled:opacity-30"
          title="Página anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="min-w-[80px] text-center text-xs font-medium text-gray-600">
          {currentPage + 1} / {pageCount}
        </span>
        <button
          onClick={onNextPage}
          disabled={currentPage >= pageCount - 1}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-gray-100 disabled:opacity-30"
          title="Próxima página"
        >
          <ChevronRight className="h-4 w-4" />
        </button>

        <div className="mx-2 h-5 w-px bg-gray-200" />

        <button
          onClick={onZoomOut}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-gray-100"
          title="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <span className="min-w-[48px] text-center text-xs font-medium text-gray-600">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={onZoomIn}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-gray-100"
          title="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {editCount > 0 && (
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100"
            title="Descartar edições"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Limpar ({editCount})
          </button>
        )}
        <button
          onClick={onExport}
          disabled={editCount === 0 || exporting}
          className={`
            flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold text-white
            transition shadow-sm
            ${
              editCount === 0 || exporting
                ? "bg-gray-300 cursor-not-allowed"
                : "bg-brand-600 hover:bg-brand-700 active:bg-brand-800 shadow-brand-200/40"
            }
          `}
        >
          {exporting ? (
            <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <Download className="h-3.5 w-3.5" />
          )}
          Exportar PDF
        </button>
      </div>
    </header>
  );
};

export default Toolbar;
