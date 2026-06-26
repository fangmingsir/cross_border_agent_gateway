from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnalyzeSkuRequest:
    sku: str
    marketplace: str
    question: str
    operator_role: str = "operator"


@dataclass
class ToolResult:
    name: str
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class AgentTraceEvent:
    step: str
    detail: str


@dataclass
class CostLog:
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    tool_calls: int
    cache_hits: int
    estimated_cost_usd: float


@dataclass
class AnalyzeSkuResponse:
    sku: str
    marketplace: str
    status: str
    summary: str
    evidence: dict[str, Any]
    recommendations: list[str]
    risk_level: str
    human_review_required: bool
    missing_evidence: list[str]
    tool_results: list[ToolResult]
    trace: list[AgentTraceEvent]
    cost: CostLog

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "marketplace": self.marketplace,
            "status": self.status,
            "summary": self.summary,
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "risk_level": self.risk_level,
            "human_review_required": self.human_review_required,
            "missing_evidence": self.missing_evidence,
            "tool_results": [result.__dict__ for result in self.tool_results],
            "trace": [event.__dict__ for event in self.trace],
            "cost": self.cost.__dict__,
        }

