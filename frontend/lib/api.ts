import { CloudHealthReport } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class AnalyzeError extends Error {}

/**
 * Uploads a single infra file to the backend and returns the full
 * CloudHealthReport once the multi-agent pipeline finishes.
 */
export async function analyzeFile(file: File): Promise<CloudHealthReport> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    throw new AnalyzeError(
      "Could not reach the CloudOps AI backend. Is it running on " + API_URL + "?"
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* ignore parse failure, use default detail */
    }
    throw new AnalyzeError(detail);
  }

  return (await response.json()) as CloudHealthReport;
}
