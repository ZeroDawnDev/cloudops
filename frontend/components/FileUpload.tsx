"use client";

import { useCallback, useRef, useState } from "react";

const ACCEPTED_EXT = [".tf", ".tfvars", ".yml", ".yaml", ".log", ".txt", ".json"];

interface FileUploadProps {
  onFileSelected: (file: File) => void;
  isAnalyzing: boolean;
}

export default function FileUpload({ onFileSelected, isAnalyzing }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSubmit = useCallback(
    (file: File) => {
      const lower = file.name.toLowerCase();
      const isSupported = ACCEPTED_EXT.some((ext) => lower.endsWith(ext));
      if (!isSupported) {
        setError(
          `Unsupported file type. Upload one of: ${ACCEPTED_EXT.join(", ")}`
        );
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSubmit(file);
  };

  const handleBrowse = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) validateAndSubmit(file);
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !isAnalyzing && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        aria-label="Upload infrastructure file"
        className={`
          relative overflow-hidden cursor-pointer select-none
          border-2 border-dashed rounded-lg
          flex flex-col items-center justify-center text-center
          py-20 px-6 transition-colors
          ${isDragging ? "border-signal bg-signal/5" : "border-panelBorder bg-panel/60"}
          ${isAnalyzing ? "cursor-wait opacity-80" : "hover:border-signal/70"}
        `}
      >
        {isAnalyzing && (
          <div
            className="absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-signal/20 to-transparent animate-scan pointer-events-none"
            aria-hidden="true"
          />
        )}

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(",")}
          className="hidden"
          onChange={handleBrowse}
          disabled={isAnalyzing}
        />

        <div className="font-mono text-signal text-xs tracking-widest uppercase mb-4">
          {isAnalyzing ? "// scanning infrastructure" : "// awaiting input"}
        </div>

        <p className="text-ink text-lg font-medium mb-2">
          {isAnalyzing
            ? "Agents are analyzing your infrastructure…"
            : "Drop your infrastructure file here"}
        </p>
        <p className="text-faint text-sm mb-6">
          Terraform (.tf) · Kubernetes YAML · Docker Compose · Cloud logs
        </p>

        {!isAnalyzing && (
          <span className="font-mono text-xs px-4 py-2 rounded border border-panelBorder text-faint">
            or click to browse
          </span>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm text-critical font-mono">
          {error}
        </p>
      )}
    </div>
  );
}
