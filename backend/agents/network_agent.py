"""
network_agent.py
-----------------
Networking Agent: reviews VPC design, subnets, route tables, load
balancers, DNS, firewall rules, and single points of failure.
"""

from agents.base_agent import BaseAnalysisAgent


class NetworkAgent(BaseAnalysisAgent):
    agent_name = "network"
    prompt_filename = "network_prompt.txt"
