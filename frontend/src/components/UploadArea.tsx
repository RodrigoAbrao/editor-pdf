import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { FileUp, FileText } from "lucide-react";

interface Props {
  onFile: (file: File) => void;
  loading: boolean;
}

const UploadArea: React.FC<Props> = ({ onFile, loading }) => {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFile(accepted[0]);
    },
    [onFile],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: loading,
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-brand-100 p-6">
      <div className="w-full max-w-lg animate-fade-in">
        {/* Logo / Title */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600 shadow-lg shadow-brand-300/40">
            <FileText className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            PDF Editor
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            Faça upload de um PDF para visualizar e editar textos.
          </p>
        </div>

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`
            group relative cursor-pointer rounded-2xl border-2 border-dashed
            p-12 text-center transition-all duration-200
            ${
              isDragActive
                ? "border-brand-500 bg-brand-50 shadow-xl shadow-brand-200/30"
                : "border-gray-300 bg-white hover:border-brand-400 hover:bg-brand-50/50 hover:shadow-lg"
            }
            ${loading ? "pointer-events-none opacity-60" : ""}
          `}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center gap-4">
            <div
              className={`
                flex h-14 w-14 items-center justify-center rounded-xl transition-colors
                ${isDragActive ? "bg-brand-100 text-brand-600" : "bg-gray-100 text-gray-400 group-hover:bg-brand-100 group-hover:text-brand-500"}
              `}
            >
              <FileUp className="h-7 w-7" />
            </div>

            {loading ? (
              <>
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
                <p className="text-sm font-medium text-brand-600">
                  Processando PDF…
                </p>
              </>
            ) : isDragActive ? (
              <p className="text-sm font-medium text-brand-600">
                Solte o arquivo aqui
              </p>
            ) : (
              <>
                <p className="text-sm font-medium text-gray-700">
                  Arraste um PDF aqui ou{" "}
                  <span className="text-brand-600 underline decoration-brand-300 underline-offset-2">
                    clique para selecionar
                  </span>
                </p>
                <p className="text-xs text-gray-400">PDF • Máx 50 MB</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadArea;
