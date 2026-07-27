"""
report_agent.py
----------------
The final decision-making layer of the pipeline. Takes the four
AgentResults (security, network, cost, reliability) plus the original
parsed infrastructure and:
  1. Computes an overall weighted health score
  2. Aggregates and de-duplicates findings, sorted by severity
  3. Asks the LLM to write a short executive summary and a consolidated
     "suggested fix" (a corrected version of the config addressing the
     highest-severity findings)

This is intentionally the ONLY agent that talks to the user in prose --
every other agent speaks strict JSON. That separation keeps the "reasoning
modules" independent and the "final decision layer" distinct, per the
multi-agent architecture.
"""

import logging
from typing import List

from models import AgentResult, CloudHealthReport, Finding, ParsedInfra, Severity
from llm_client import call_llm, LLMError

logger = logging.getLogger("cloudops.agents.report")

SEVERITY_WEIGHT = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

# Relative importance of each pillar in the overall score.
PILLAR_WEIGHTS = {
    "security": 0.35,
    "network": 0.20,
    "cost": 0.20,
    "reliability": 0.25,
}

REPORT_SYSTEM_PROMPT = """You are the Report Generator Agent inside CloudOps AI,
the final decision-making layer of an autonomous multi-agent cloud operations
system. You have already received structured findings from four specialist
agents (Security, Network, Cost, Reliability). Your job is NOT to re-analyze
the infrastructure -- it is to:

1. Write a concise executive summary (4-6 sentences) a CTO could read in 20
   seconds, referencing the most important findings and overall risk level.
2. Produce ONE consolidated, corrected configuration snippet that fixes the
   CRITICAL and HIGH severity findings, in the same language/format as the
   original file. If there are no critical/high findings, return null for
   this field.

Respond with STRICT JSON ONLY, no markdown fences, matching exactly:
{
  "executive_summary": "<string>",
  "suggested_fix": "<string or null>"
}
"""


def _aggregate_findings(results: List[AgentResult]) -> List[Finding]:
    all_findings: List[Finding] = []
    for result in results:
        all_findings.extend(result.findings)
    all_findings.sort(key=lambda f: SEVERITY_WEIGHT.get(f.severity, 99))
    return all_findings


def _overall_score(results: List[AgentResult]) -> int:
    total = 0.0
    for result in results:
        weight = PILLAR_WEIGHTS.get(result.agent_name, 0)
        total += result.score * weight
    return round(total)


def _score_by_name(results: List[AgentResult], name: str) -> int:
    for result in results:
        if result.agent_name == name:
            return result.score
    return 0


def _recommended_improvements(findings: List[Finding], limit: int = 8) -> List[str]:
    """Top N recommended fixes, highest severity first, deduplicated by title."""
    seen = set()
    out = []
    for f in findings:
        if f.title in seen:
            continue
        seen.add(f.title)
        out.append(f"[{f.severity.value.upper()}] {f.title} → {f.recommended_fix}")
        if len(out) >= limit:
            break
    return out


def generate_report(infra: ParsedInfra, results: List[AgentResult]) -> CloudHealthReport:
    all_findings = _aggregate_findings(results)
    critical_findings = [f for f in all_findings if f.severity == Severity.CRITICAL]
    overall = _overall_score(results)

    # Ask the LLM for the human-facing narrative + consolidated fix.
    # This step is allowed to degrade gracefully: if it fails, we still
    # return a fully valid report built from the structured agent data.
    executive_summary = (
        f"Analysis of {infra.filename} complete. Overall health score: {overall}/100. "
        f"{len(all_findings)} total findings, {len(critical_findings)} critical."
    )
    suggested_fix = None

    high_severity_context = "\n".join(
        f"- [{f.severity.value}] ({f.agent}) {f.title}: {f.explanation} "
        f"Fix: {f.recommended_fix}"
        for f in all_findings
        if f.severity in (Severity.CRITICAL, Severity.HIGH)
    ) or "No critical or high severity findings."

    user_prompt = (
        f"Original file: {infra.filename} ({infra.kind.value})\n\n"
        f"Agent scores: "
        + ", ".join(f"{r.agent_name}={r.score}" for r in results)
        + f"\nOverall score: {overall}\n\n"
        f"Critical/High findings:\n{high_severity_context}\n\n"
        f"Original file content (for producing the corrected snippet):\n"
        f"{infra.raw_text[:6000]}\n"
    )

    try:
        raw = call_llm(REPORT_SYSTEM_PROMPT, user_prompt, max_tokens=2000)
        import json

        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        parsed = json.loads(cleaned)
        executive_summary = parsed.get("executive_summary", executive_summary)
        suggested_fix = parsed.get("suggested_fix")
    except (LLMError, ValueError, Exception) as exc:  # noqa: BLE001
        logger.warning("Report narrative generation degraded: %s", exc)

    return CloudHealthReport(
        overall_score=overall,
        security_score=_score_by_name(results, "security"),
        network_score=_score_by_name(results, "network"),
        cost_score=_score_by_name(results, "cost"),
        reliability_score=_score_by_name(results, "reliability"),
        critical_findings=critical_findings,
        all_findings=all_findings,
        recommended_improvements=_recommended_improvements(all_findings),
        suggested_fix=suggested_fix,
        executive_summary=executive_summary,
    )
