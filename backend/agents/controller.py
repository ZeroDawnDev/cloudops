"""
controller.py
--------------
The Agent Controller is the orchestration layer described in the
architecture diagram:

    Agent Controller
          |
    ------------------------------------
    |        |          |              |
  Security Network     Cost      Reliability
   Agent    Agent      Agent        Agent
    |
    Report Generator Agent
    |
    Final Response

It runs the four specialist agents CONCURRENTLY (they are independent
reasoning modules over the same input) and then hands their combined
output to the Report Generator Agent for the final decision layer.
"""

import asyncio
import logging
from typing import List

from models import AgentResult, CloudHealthReport, ParsedInfra
from agents.security_agent import SecurityAgent
from agents.network_agent import NetworkAgent
from agents.cost_agent import CostAgent
from agents.reliability_agent import ReliabilityAgent
from agents.report_agent import generate_report

logger = logging.getLogger("cloudops.controller")

# Instantiate once; agents are stateless aside from their loaded prompt text.
_SECURITY = SecurityAgent()
_NETWORK = NetworkAgent()
_COST = CostAgent()
_RELIABILITY = ReliabilityAgent()


async def _run_agent_async(agent, infra: ParsedInfra) -> AgentResult:
    """Runs a (synchronous, network-bound) agent in a worker thread so all
    four specialist agents genuinely execute concurrently."""
    return await asyncio.to_thread(agent.analyze, infra)


async def run_pipeline(infra: ParsedInfra) -> CloudHealthReport:
    """
    Full autonomous pipeline: parse -> route -> analyze (parallel) -> report.
    `infra` is already parsed by the time it reaches here (see parsers/).
    """
    logger.info("Routing '%s' (%s) to specialist agents", infra.filename, infra.kind)

    results: List[AgentResult] = await asyncio.gather(
        _run_agent_async(_SECURITY, infra),
        _run_agent_async(_NETWORK, infra),
        _run_agent_async(_COST, infra),
        _run_agent_async(_RELIABILITY, infra),
    )

    logger.info(
        "Agent scores -> security=%s network=%s cost=%s reliability=%s",
        *(r.score for r in results),
    )

    report = generate_report(infra, results)
    return report
