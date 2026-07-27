"""
security_agent.py
------------------
Security Agent: detects open security groups, public data stores, exposed
ports, weak IAM, missing encryption, missing backups, hardcoded secrets.
"""

from agents.base_agent import BaseAnalysisAgent


class SecurityAgent(BaseAnalysisAgent):
    agent_name = "security"
    prompt_filename = "security_prompt.txt"
