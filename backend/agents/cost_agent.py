"""
cost_agent.py
-------------
Cost Optimization Agent: flags over-provisioned/expensive/unused
resources and suggests cheaper alternatives using basic heuristics.
"""

from agents.base_agent import BaseAnalysisAgent


class CostAgent(BaseAnalysisAgent):
    agent_name = "cost"
    prompt_filename = "cost_prompt.txt"
