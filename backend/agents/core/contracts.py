"""
Sports AI — Agent Contracts
Typed contracts for all agents in the pipeline.
"""

from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class AgentContext(BaseModel):
    query: str
    prediction_id: str
    stage: str = "init"
    data: Dict[str, Any] = Field(default_factory=dict)
    timings: Dict[str, float] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def has_error(self, agent_name: str) -> bool:
        return agent_name in self.errors


class AgentOutcome(BaseModel):
    agent_name: str
    agent_key: Optional[str] = None
    status: AgentStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    narrative: Optional[str] = None
    execution_time_ms: float
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def is_success(self) -> bool:
        return self.status == AgentStatus.COMPLETED

    def is_critical_failure(self) -> bool:
        return self.status in {AgentStatus.ERROR, AgentStatus.TIMEOUT}


class PipelineEvent(BaseModel):
    event_type: Literal[
        "agent_start",
        "agent_complete",
        "pipeline_start",
        "pipeline_complete",
        "error",
        "stage_start",
        "stage_complete",
    ]
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_sse(self) -> str:
        import json

        return json.dumps(
            {
                "event": self.event_type,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
            }
        )


class PipelineStage(BaseModel):
    name: str
    agents: List[str]
    dependencies: List[str] = Field(default_factory=list)
    optional: bool = False

    def is_gate(self) -> bool:
        return len(self.agents) == 1 and not self.optional


GATE_STAGES = {"nlp", "fixture_resolver", "context"}

STAGES = [
    PipelineStage(name="parse", agents=["nlp"], dependencies=[]),
    PipelineStage(name="resolve", agents=["fixture_resolver"], dependencies=["parse"]),
    PipelineStage(name="context", agents=["context"], dependencies=["resolve"]),
    PipelineStage(
        name="data_fetch",
        agents=["history", "lineup", "odds"],
        dependencies=["context"],
    ),
    PipelineStage(
        name="analysis",
        agents=["sentiment", "elo", "poisson"],
        dependencies=["data_fetch"],
    ),
    PipelineStage(
        name="features",
        agents=["feature"],
        dependencies=["analysis"],
    ),
    PipelineStage(
        name="prediction",
        agents=["ml", "monte_carlo"],
        dependencies=["features"],
    ),
    PipelineStage(
        name="decision",
        agents=["market_edge", "risk"],
        dependencies=["prediction"],
    ),
    PipelineStage(
        name="synthesis",
        agents=["synthesis"],
        dependencies=["decision"],
    ),
]


AGENT_TO_STAGE: Dict[str, str] = {
    "nlp": "parse",
    "fixture_resolver": "resolve",
    "context": "context",
    "history": "data_fetch",
    "lineup": "data_fetch",
    "odds": "data_fetch",
    "sentiment": "analysis",
    "elo": "analysis",
    "poisson": "analysis",
    "feature": "features",
    "ml": "prediction",
    "monte_carlo": "prediction",
    "market_edge": "decision",
    "risk": "decision",
    "synthesis": "synthesis",
}

STAGE_ORDER = [
    "parse",
    "resolve",
    "context",
    "data_fetch",
    "analysis",
    "features",
    "prediction",
    "decision",
    "synthesis",
]
