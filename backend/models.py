"""
models.py
---------
Shared Pydantic schemas used across the API, agents, and report generator.
Keeping these in one place means every agent speaks the same "language"
when handing results up to the Report Generator Agent.
"""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InfraKind(str, Enum):
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    DOCKER_COMPOSE = "docker_compose"
    LOGS = "logs"
    UNKNOWN = "unknown"


class ParsedInfra(BaseModel):
    """Normalized output of any parser, regardless of source file type."""
    kind: InfraKind
    filename: str
    raw_text: str
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    """A single issue raised by any analysis agent."""
    agent: str  # "security" | "network" | "cost" | "reliability"
    severity: Severity
    title: str
    explanation: str
    resource: Optional[str] = None
    recommended_fix: str
    fixed_snippet: Optional[str] = None


class AgentResult(BaseModel):
    """What each specialized agent returns to the controller."""
    agent_name: str
    score: int = Field(ge=0, le=100)
    findings: List[Finding] = Field(default_factory=list)
    summary: str


class CloudHealthReport(BaseModel):
    """Final combined output returned to the frontend."""
    overall_score: int
    security_score: int
    network_score: int
    cost_score: int
    reliability_score: int
    critical_findings: List[Finding]
    all_findings: List[Finding]
    recommended_improvements: List[str]
    suggested_fix: Optional[str] = None
    executive_summary: str
