"use client";

import { useState } from "react";
import FileUpload from "@/components/FileUpload";
import ReportView from "@/components/ReportView";
import { analyzeFile, AnalyzeError } from "@/lib/api";
import { CloudHealthReport } from "@/lib/types";

export default function DashboardPage() {
  const [report, setReport] = useState<CloudHealthReport | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(file: File) {
    setIsAnalyzing(true);
    setError(null);
    setReport(null);
    setFileName(file.name);
    try {
      const result = await analyzeFile(file);
      setReport(result);
    } catch (err) {
      const message = err instanceof AnalyzeError ? err.message : "Unexpected error during analysis.";
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-10 sm:px-10 lg:px-16">
      <header className="max-w-5xl mx-auto mb-10 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs tracking-widest text-signal uppercase mb-1">
            CloudOps AI
          </p>
          <h1 className="text-2xl font-semibold text-ink">Autonomous Cloud Operations Engineer</h1>
        </div>
        <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-faint">
          <span className="w-2 h-2 rounded-full bg-signal animate-pulseSignal" />
          4 agents online
        </div>
      </header>

      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        <FileUpload onFileSelected={handleFileSelected} isAnalyzing={isAnalyzing} />

        {fileName && !error && (
          <p className="font-mono text-xs text-faint -mt-4">
            {isAnalyzing ? "Analyzing" : "Last analyzed"}: {fileName}
          </p>
        )}

        {error && (
          <div className="border border-critical/40 bg-critical/10 rounded-lg p-4">
            <p className="font-mono text-xs uppercase tracking-widest text-critical mb-1">
              Analysis failed
            </p>
            <p className="text-ink/90 text-sm">{error}</p>
          </div>
        )}

        {report && <ReportView report={report} />}
      </div>
    </main>
  );
}
