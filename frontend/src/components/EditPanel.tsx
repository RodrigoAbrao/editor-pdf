import React from "react";
import { Trash2, Type } from "lucide-react";
import type { EditOperation } from "../types";

interface Props {
  edits: EditOperation[];
  onRemove: (key: string) => void;
  onGoTo: (edit: EditOperation) => void;
}

const EditPanel: React.FC<Props> = ({ edits, onRemove, onGoTo }) => {
  if (edits.length === 0) {
    return (
      <aside className="flex w-72 shrink-0 flex-col border-l border-gray-200 bg-white">
        <div className="border-b border-gray-100 px-4 py-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Edições
          </h2>
        </div>
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100">
            <Type className="h-5 w-5 text-gray-300" />
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Clique sobre qualquer texto no PDF para editá-lo.
          </p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col border-l border-gray-200 bg-white">
      <div className="border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
          Edições ({edits.length})
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto pdf-scroll">
        {edits.map((edit) => (
          <div
            key={edit.key}
            role="button"
            tabIndex={0}
            className="group border-b border-gray-50 px-4 py-3 transition hover:bg-gray-50 cursor-pointer"
            onClick={() => onGoTo(edit)}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onGoTo(edit); }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-medium text-gray-400 mb-1">
                  Pág. {edit.page + 1} • {edit.font} {edit.font_size}pt
                </p>
                <p className="text-xs text-red-400 line-through truncate">
                  {edit.original_text}
                </p>
                <p className="text-xs text-green-600 font-medium truncate mt-0.5">
                  {edit.new_text}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(edit.key);
                }}
                className="mt-1 rounded p-1 text-gray-300 opacity-0 transition group-hover:opacity-100 hover:bg-red-50 hover:text-red-500"
                title="Remover edição"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default EditPanel;
