"""
Sports AI — Pipeline Graph
Defines the DAG structure for agent orchestration with parallel execution support.
"""

from typing import Dict, List, Set
from backend.agents.core.contracts import (
    STAGES,
    STAGE_ORDER,
    AGENT_TO_STAGE,
    GATE_STAGES,
    PipelineStage,
)


class PipelineGraph:
    def __init__(self):
        self.stages = STAGES
        self.stage_order = STAGE_ORDER
        self.agent_to_stage = AGENT_TO_STAGE

    def get_stage(self, stage_name: str) -> PipelineStage:
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        raise ValueError(f"Unknown stage: {stage_name}")

    def get_dependencies(self, stage_name: str) -> List[str]:
        stage = self.get_stage(stage_name)
        return stage.dependencies

    def get_stage_agents(self, stage_name: str) -> List[str]:
        stage = self.get_stage(stage_name)
        return stage.agents

    def is_critical_stage(self, stage_name: str) -> bool:
        stage = self.get_stage(stage_name)
        return len(stage.agents) == 1 and stage.agents[0] in GATE_STAGES

    def validate_graph(self) -> bool:
        resolved: Set[str] = set()
        for stage_name in self.stage_order:
            stage = self.get_stage(stage_name)
            for dep in stage.dependencies:
                if dep not in resolved:
                    raise ValueError(f"Stage {stage_name} depends on unresolved {dep}")
            resolved.add(stage_name)
        return True

    def get_execution_order(self) -> List[str]:
        return self.stage_order

    def get_fan_out_stages(self) -> List[str]:
        return [s.name for s in self.stages if len(s.agents) > 1]

    def get_parallel_agents(self, stage_name: str) -> List[str]:
        return self.get_stage_agents(stage_name)

    def should_parallelize(self, stage_name: str) -> bool:
        return len(self.get_stage_agents(stage_name)) > 1
