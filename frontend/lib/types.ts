// Mirrors backend/models.py so the frontend and backend never drift apart.

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Finding {
  agent: string;
  severity: Severity;
  title: string;
  explanation: string;
  resource: string | null;
  recommended_fix: string;
  fixed_snippet: string | null;
}

export interface CloudHealthReport {
  overall_score: number;
  security_score: number;
  network_score: number;
  cost_score: number;
  reliability_score: number;
  critical_findings: Finding[];
  all_findings: Finding[];
  recommended_improvements: string[];
  suggested_fix: string | null;
  executive_summary: string;
}
