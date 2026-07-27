"""
reliability_agent.py
---------------------
Reliability Agent: reviews high availability, auto-scaling, disaster
recovery, and monitoring/alerting coverage.
"""

from agents.base_agent import BaseAnalysisAgent


class ReliabilityAgent(BaseAnalysisAgent):
    agent_name = "reliability"
    prompt_filename = "reliability_prompt.txt"
