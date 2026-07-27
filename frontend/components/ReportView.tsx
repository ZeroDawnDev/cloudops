"use client";

import { CloudHealthReport, Finding, Severity } from "@/lib/types";

const SEVERITY_STYLES: Record<Severity, { text: string; bg: string; label: string }> = {
  critical: { text: "text-critical", bg: "bg-critical/10 border-critical/40", label: "Critical" },
  high: { text: "text-warn", bg: "bg-warn/10 border-warn/40", label: "High" },
  medium: { text: "text-warn", bg: "bg-warn/5 border-warn/25", label: "Medium" },
  low: { text: "text-signal", bg: "bg-signal/5 border-signal/25", label: "Low" },
  info: { text: "text-faint", bg: "bg-panel border-panelBorder", label: "Info" },
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-signal";
  if (score >= 50) return "text-warn";
  return "text-critical";
}

function ScoreDial({ label, score }: { label: string; score: number }) {
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="flex flex-col items-center bg-panel border border-panelBorder rounded-lg p-5">
      <svg width="100" height="100" viewBox="0 0 100 100" className="mb-2">
        <circle cx="50" cy="50" r="42" fill="none" stroke="#232733" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          className={scoreColor(score)}
          stroke="currentColor"
        />
        <text
          x="50"
          y="55"
          textAnchor="middle"
          className={`font-mono font-semibold ${scoreColor(score)}`}
          fontSize="22"
          fill="currentColor"
        >
          {score}
        </text>
      </svg>
      <span className="font-mono text-xs uppercase tracking-wide text-faint">{label}</span>
    </div>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  const style = SEVERITY_STYLES[finding.severity];
  return (
    <div className={`border rounded-md p-4 ${style.bg}`}>
      <div className="flex items-center justify-between gap-3 mb-1">
        <span className={`font-mono text-[11px] uppercase tracking-widest ${style.text}`}>
          {style.label} · {finding.agent}
        </span>
        {finding.resource && (
          <span className="font-mono text-[11px] text-faint truncate">{finding.resource}</span>
        )}
      </div>
      <p className="text-ink font-medium mb-1">{finding.title}</p>
      <p className="text-faint text-sm mb-2">{finding.explanation}</p>
      <p className="text-sm">
        <span className="text-signal font-mono text-xs uppercase mr-2">Fix</span>
        <span className="text-ink/90">{finding.recommended_fix}</span>
      </p>
      {finding.fixed_snippet && (
        <pre className="mt-3 bg-void border border-panelBorder rounded p-3 text-xs overflow-x-auto font-mono text-ink/90">
          {finding.fixed_snippet}
        </pre>
      )}
    </div>
  );
}

export default function ReportView({ report }: { report: CloudHealthReport }) {
  return (
    <div className="w-full flex flex-col gap-8">
      {/* Overall + pillar scores */}
      <section>
        <div className="flex items-baseline gap-4 mb-5">
          <h2 className="font-mono text-xs uppercase tracking-widest text-faint">
            Cloud Health Report
          </h2>
          <div className="h-px flex-1 bg-panelBorder" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="col-span-2 sm:col-span-1 flex flex-col items-center justify-center bg-panel border border-panelBorder rounded-lg p-5">
            <span className={`font-mono text-4xl font-bold ${scoreColor(report.overall_score)}`}>
              {report.overall_score}
            </span>
            <span className="font-mono text-xs uppercase tracking-wide text-faint mt-1">
              Overall
            </span>
          </div>
          <ScoreDial label="Security" score={report.security_score} />
          <ScoreDial label="Network" score={report.network_score} />
          <ScoreDial label="Cost" score={report.cost_score} />
          <ScoreDial label="Reliability" score={report.reliability_score} />
        </div>
      </section>

      {/* Executive summary */}
      <section className="bg-panel border border-panelBorder rounded-lg p-5">
        <h3 className="font-mono text-xs uppercase tracking-widest text-signal mb-2">
          Executive Summary
        </h3>
        <p className="text-ink/90 leading-relaxed">{report.executive_summary}</p>
      </section>

      {/* Recommended improvements */}
      {report.recommended_improvements.length > 0 && (
        <section>
          <h3 className="font-mono text-xs uppercase tracking-widest text-faint mb-3">
            Recommended Improvements
          </h3>
          <ul className="flex flex-col gap-2">
            {report.recommended_improvements.map((item, i) => (
              <li
                key={i}
                className="font-mono text-sm text-ink/90 bg-panel border border-panelBorder rounded px-3 py-2"
              >
                {item}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Findings feed */}
      <section>
        <h3 className="font-mono text-xs uppercase tracking-widest text-faint mb-3">
          Findings ({report.all_findings.length})
        </h3>
        {report.all_findings.length === 0 ? (
          <p className="text-faint text-sm">No issues detected. Clean bill of health.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {report.all_findings.map((f, i) => (
              <FindingRow key={i} finding={f} />
            ))}
          </div>
        )}
      </section>

      {/* Suggested fixed configuration */}
      {report.suggested_fix && (
        <section>
          <h3 className="font-mono text-xs uppercase tracking-widest text-faint mb-3">
            Suggested Fixed Configuration
          </h3>
          <pre className="bg-void border border-panelBorder rounded-lg p-4 text-xs overflow-x-auto font-mono text-ink/90 leading-relaxed">
            {report.suggested_fix}
          </pre>
        </section>
      )}
    </div>
  );
}
