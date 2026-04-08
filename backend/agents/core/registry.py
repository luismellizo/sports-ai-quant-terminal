"""
Sports AI — Agent Registry
Registry for all agents with metadata for orchestration.
"""

from typing import Dict, Type, List, Optional
from dataclasses import dataclass, field

from backend.agents.core.base import BaseAgent


@dataclass
class AgentMetadata:
    name: str
    agent_class: Type[BaseAgent]
    stage: str
    is_critical: bool = True
    timeout_seconds: float = 30.0
    dependencies: List[str] = field(default_factory=list)
    narrative_key: Optional[str] = None


class AgentRegistry:
    _agents: Dict[str, AgentMetadata] = {}
    _stages: Dict[str, List[str]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        agent_class: Type[BaseAgent],
        stage: str,
        is_critical: bool = True,
        timeout_seconds: float = 30.0,
        dependencies: Optional[List[str]] = None,
        narrative_key: Optional[str] = None,
    ) -> None:
        cls._agents[name] = AgentMetadata(
            name=name,
            agent_class=agent_class,
            stage=stage,
            is_critical=is_critical,
            timeout_seconds=timeout_seconds,
            dependencies=dependencies or [],
            narrative_key=narrative_key or f"{name.lower()}_narrative",
        )
        if stage not in cls._stages:
            cls._stages[stage] = []
        cls._stages[stage].append(name)

    @classmethod
    def get(cls, name: str) -> Optional[AgentMetadata]:
        return cls._agents.get(name)

    @classmethod
    def get_by_stage(cls, stage: str) -> List[AgentMetadata]:
        return [cls._agents[name] for name in cls._stages.get(stage, [])]

    @classmethod
    def all_agents(cls) -> List[AgentMetadata]:
        return list(cls._agents.values())

    @classmethod
    def get_stage_order(cls) -> List[str]:
        return list(cls._stages.keys())


def register_agent(
    name: str,
    stage: str,
    is_critical: bool = True,
    timeout_seconds: float = 30.0,
    dependencies: Optional[List[str]] = None,
    narrative_key: Optional[str] = None,
):
    def decorator(cls: Type[BaseAgent]):
        AgentRegistry.register(
            name, cls, stage, is_critical, timeout_seconds, dependencies, narrative_key
        )
        return cls

    return decorator
