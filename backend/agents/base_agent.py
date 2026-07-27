"""
base_agent.py
-------------
Base class for every specialized analysis agent (Security, Network, Cost,
Reliability). Each agent:
  1. Loads its own system prompt from /prompts
  2. Builds a user prompt from the parsed infrastructure
  3. Calls the LLM and validates the JSON response into an AgentResult

This is where "autonomous agent" earns its name: each agent reasons
independently over the same input and returns a structured, opinionated
judgement -- not just a chat reply.
"""

import logging
import os
from pathlib import Path

from models import AgentResult, Finding, ParsedInfra
from llm_client import call_llm_json, LLMError

logger = logging.getLogger("cloudops.agents")

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


class BaseAnalysisAgent:
    agent_name: str = "base"
    prompt_filename: str = ""

    def __init__(self):
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        path = PROMPTS_DIR / self.prompt_filename
        if not path.exists():
            raise FileNotFoundError(f"Prompt file missing: {path}")
        return path.read_text(encoding="utf-8")

    def _build_user_prompt(self, infra: ParsedInfra) -> str:
        """
        Builds the input context handed to the LLM. Truncates very large
        files defensively so a single upload can't blow the context window.
        """
        MAX_CHARS = 12000
        content = infra.raw_text
        truncated_note = ""
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS]
            truncated_note = "\n\n[NOTE: input truncated to first 12000 characters]"

        return (
            f"File: {infra.filename}\n"
            f"Detected type: {infra.kind.value}\n"
            f"Resource count: {len(infra.resources)}\n\n"
            f"--- RAW CONFIGURATION / LOGS ---\n"
            f"{content}{truncated_note}\n"
            f"--- END ---\n\n"
            f"Analyze the above according to your role and respond with the "
            f"required JSON schema only."
        )

    def analyze(self, infra: ParsedInfra) -> AgentResult:
        """
        Runs this agent's analysis. On any failure (LLM error, bad JSON,
        validation error) this returns a degraded-but-valid AgentResult
        instead of raising, so one failing agent never crashes the whole
        pipeline -- the Report Generator can note the partial failure.
        """
        user_prompt = self._build_user_prompt(infra)
        try:
            raw = call_llm_json(self.system_prompt, user_prompt)
            findings = [
                Finding(agent=self.agent_name, **f) for f in raw.get("findings", [])
            ]
            return AgentResult(
                agent_name=self.agent_name,
                score=int(raw.get("score", 50)),
                findings=findings,
                summary=raw.get("summary", "No summary returned."),
            )
        except (LLMError, ValueError, TypeError) as exc:
            logger.error("%s agent failed: %s", self.agent_name, exc)
            return AgentResult(
                agent_name=self.agent_name,
                score=0,
                findings=[],
                summary=(
                    f"{self.agent_name.title()} analysis could not be completed "
                    f"due to an internal error: {exc}"
                ),
            )
