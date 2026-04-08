"""
Sports AI — Core Base Agent
Extends contracts with agent implementation.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.agents.core.contracts import AgentContext, AgentOutcome, AgentStatus
from backend.utils.logger import get_logger


class BaseAgent(ABC):
    name: str
    is_critical: bool = True
    timeout_seconds: float = 30.0

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        # Support both the new `name` convention and the older `agent_name`
        # attribute used by a few legacy tests/helpers.
        self.name = getattr(self, "name", getattr(self, "agent_name", self.__class__.__name__))
        self.agent_name = getattr(self, "agent_name", self.name)

    async def run(self, ctx: AgentContext) -> AgentOutcome:
        self.logger.info(f"▶ Starting {self.name}")
        start = time.time()

        try:
            data = await asyncio.wait_for(
                self.execute(ctx),
                timeout=self.timeout_seconds,
            )
            elapsed = max((time.time() - start) * 1000, 1.0)

            return AgentOutcome(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                execution_time_ms=round(elapsed, 2),
                data=data,
            )
        except asyncio.TimeoutError:
            elapsed = max((time.time() - start) * 1000, 1.0)
            self.logger.error(f"✗ {self.name} timed out after {self.timeout_seconds}s")
            return AgentOutcome(
                agent_name=self.name,
                status=AgentStatus.TIMEOUT,
                execution_time_ms=round(elapsed, 2),
                error=f"Timeout after {self.timeout_seconds}s",
            )
        except Exception as e:
            elapsed = max((time.time() - start) * 1000, 1.0)
            self.logger.error(f"✗ {self.name} failed: {e}")
            return AgentOutcome(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                execution_time_ms=round(elapsed, 2),
                error=str(e),
            )

    @abstractmethod
    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        pass

    def merge_outcome(self, ctx: AgentContext, outcome: AgentOutcome) -> None:
        if outcome.data:
            ctx.data.update(outcome.data)
        if outcome.narrative:
            key = f"{self.name.lower()}_narrative"
            ctx.data[key] = outcome.narrative
        if outcome.status == AgentStatus.ERROR and outcome.error:
            ctx.errors[self.name] = outcome.error
        ctx.timings[self.name] = outcome.execution_time_ms
