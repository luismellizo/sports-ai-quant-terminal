"""
Sports AI — Orchestrator v2
DAG-based orchestrator with parallel execution per stage.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import (
    AgentContext,
    AgentOutcome,
    AgentStatus,
    PipelineEvent,
)
from backend.agents.core.pipeline_graph import PipelineGraph
from backend.agents.registry import discover_agents, get_agent
from backend.agents.shared.context_merge import build_timing_summary, merge_context
from backend.config.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


AGENT_LABELS = {
    "nlp": "Analizando petición",
    "fixture_resolver": "Resolviendo fixture real (sin asumir local/visita)",
    "context": "Obteniendo contexto competitivo (standings + stats)",
    "history": "Analizando datos históricos con IA",
    "lineup": "Inteligencia táctica de alineaciones",
    "sentiment": "Análisis de sentimiento y noticias",
    "elo": "Cálculo e interpretación de rating ELO",
    "odds": "Análisis de cuotas del mercado",
    "feature": "Ingeniería de características",
    "poisson": "Modelo probabilístico de Poisson",
    "ml": "Cross-validación con predicciones de API",
    "monte_carlo": "Simulación Monte Carlo (50K sims)",
    "market_edge": "Detección de ineficiencias del mercado",
    "risk": "Evaluación profesional de riesgo",
    "synthesis": "Generando Executive Summary con IA",
}


class PipelineOrchestrator:
    """
    Orchestrates the full analysis pipeline.

    Discovery happens once at startup so the registry is populated from the
    per-agent packages, while the execution path stays type-safe and DAG-based.
    """

    def __init__(self):
        self.logger = get_logger("Orchestrator")
        self.graph = PipelineGraph()
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_pipelines)
        self._agent_instances: Dict[str, BaseAgent] = {}
        self.graph.validate_graph()
        discover_agents()

    async def run(self, query: str) -> AsyncGenerator[str, None]:
        await self._semaphore.acquire()
        try:
            prediction_id = str(uuid.uuid4())[:8]
            ctx = AgentContext(
                query=query,
                prediction_id=prediction_id,
                stage="init",
            )
            ctx.metadata["pipeline_version"] = "2.0.0"

            agent_results: List[Dict[str, Any]] = []
            pipeline_start = time.time()

            self.logger.info(
                f"═══ Starting pipeline {prediction_id} for: '{query}' ═══",
                extra={"prediction_id": prediction_id, "stage": "pipeline_start"},
            )

            yield self._sse_event(
                "pipeline_start",
                {
                    "id": prediction_id,
                    "query": query,
                    "total_agents": len(self.graph.agent_to_stage),
                    "total_stages": len(self.graph.get_execution_order()),
                },
            )

            for stage_name in self.graph.get_execution_order():
                stage_start = time.time()
                ctx.stage = stage_name
                stage_agents = self.graph.get_stage_agents(stage_name)
                stage_offset = len(agent_results)

                yield self._sse_event(
                    "stage_start",
                    {
                        "prediction_id": prediction_id,
                        "stage": stage_name,
                        "agents": stage_agents,
                    },
                )

                for offset, agent_key in enumerate(stage_agents):
                    agent = self._get_agent(agent_key)
                    yield self._sse_event(
                        "agent_start",
                        {
                            "prediction_id": prediction_id,
                            "stage": stage_name,
                            "index": stage_offset + offset,
                            "name": agent.name if agent else agent_key,
                            "key": agent_key,
                            "label": AGENT_LABELS.get(agent_key, agent_key),
                            "status": "running",
                        },
                    )

                stage_outcomes = await self._execute_stage(ctx, stage_name)
                critical_failure = False

                for offset, (agent_key, outcome) in enumerate(stage_outcomes):
                    event_index = stage_offset + offset
                    self._merge_outcome(ctx, outcome, agent_key)

                    agent_results.append(
                        {
                            "index": event_index,
                            "agent_key": agent_key,
                            "agent_name": outcome.agent_name,
                            "label": AGENT_LABELS.get(agent_key, outcome.agent_name),
                            "status": outcome.status.value,
                            "execution_time_ms": outcome.execution_time_ms,
                            "error": outcome.error,
                        }
                    )

                    yield self._sse_event(
                        "agent_complete",
                        {
                            "prediction_id": prediction_id,
                            "stage": stage_name,
                            "index": event_index,
                            "name": outcome.agent_name,
                            "key": agent_key,
                            "label": AGENT_LABELS.get(agent_key, outcome.agent_name),
                            "status": outcome.status.value,
                            "execution_time_ms": outcome.execution_time_ms,
                            "error": outcome.error,
                        },
                    )

                    if outcome.is_critical_failure() and self.graph.is_critical_stage(stage_name):
                        critical_failure = True
                        self.logger.error(
                            f"Critical gate {agent_key} failed, aborting pipeline",
                            extra={
                                "prediction_id": prediction_id,
                                "stage": stage_name,
                                "agent": agent_key,
                                "status": outcome.status.value,
                                "error_code": outcome.error,
                            },
                        )
                        yield self._sse_event(
                            "error",
                            {
                                "prediction_id": prediction_id,
                                "stage": stage_name,
                                "agent": agent_key,
                                "error": outcome.error,
                            },
                        )
                        break

                stage_elapsed = (time.time() - stage_start) * 1000
                ctx.timings[f"stage_{stage_name}"] = stage_elapsed

                yield self._sse_event(
                    "stage_complete",
                    {
                        "prediction_id": prediction_id,
                        "stage": stage_name,
                        "duration_ms": round(stage_elapsed, 2),
                    },
                )

                if critical_failure:
                    total_time = (time.time() - pipeline_start) * 1000
                    self.logger.error(
                        f"═══ Pipeline {prediction_id} aborted in {total_time:.0f}ms ═══",
                        extra={
                            "prediction_id": prediction_id,
                            "stage": stage_name,
                            "duration_ms": round(total_time, 2),
                            "status": "aborted",
                        },
                    )
                    yield self._sse_event(
                        "pipeline_complete",
                        self._build_prediction(
                            prediction_id,
                            query,
                            ctx,
                            agent_results,
                            total_time,
                        ),
                    )
                    return

            total_time = (time.time() - pipeline_start) * 1000
            prediction = self._build_prediction(
                prediction_id,
                query,
                ctx,
                agent_results,
                total_time,
            )

            yield self._sse_event("pipeline_complete", prediction)
            self.logger.info(
                f"═══ Pipeline {prediction_id} completed in {total_time:.0f}ms ═══",
                extra={
                    "prediction_id": prediction_id,
                    "stage": "pipeline_complete",
                    "duration_ms": round(total_time, 2),
                    "status": "completed",
                },
            )
        finally:
            self._semaphore.release()

    async def run_pipeline(self, query: str) -> AsyncGenerator[str, None]:
        """Backward-compatible entrypoint for existing routes."""
        async for event in self.run(query):
            yield event

    async def _execute_stage(
        self, ctx: AgentContext, stage_name: str
    ) -> List[Tuple[str, AgentOutcome]]:
        agents = self.graph.get_stage_agents(stage_name)
        if not agents:
            return []

        if len(agents) == 1:
            agent_key = agents[0]
            outcome = await self._run_agent(agent_key, ctx)
            return [(agent_key, outcome)]

        tasks: Dict[str, asyncio.Task[AgentOutcome]] = {}
        async with asyncio.TaskGroup() as tg:
            for agent_key in agents:
                tasks[agent_key] = tg.create_task(
                    self._run_agent(agent_key, ctx),
                    name=agent_key,
                )

        return [(agent_key, tasks[agent_key].result()) for agent_key in agents]

    async def _run_agent(self, agent_key: str, ctx: AgentContext) -> AgentOutcome:
        agent = self._get_agent(agent_key)
        if agent is None:
            return AgentOutcome(
                agent_name=agent_key,
                agent_key=agent_key,
                status=AgentStatus.ERROR,
                execution_time_ms=0,
                error=f"Agent not registered: {agent_key}",
            )

        outcome = await agent.run(ctx)
        outcome.agent_key = agent_key
        return outcome

    def _merge_outcome(
        self,
        ctx: AgentContext,
        outcome: AgentOutcome,
        agent_key: str,
    ) -> None:
        if outcome.data:
            ctx.data = merge_context(ctx.data, outcome.data, strategy="replace")

        if outcome.narrative:
            narrative_key = f"{agent_key}_narrative"
            ctx.data[narrative_key] = outcome.narrative

        if outcome.status in {AgentStatus.ERROR, AgentStatus.TIMEOUT} and outcome.error:
            ctx.errors[agent_key] = outcome.error

        ctx.timings[agent_key] = outcome.execution_time_ms
        ctx.data[f"{agent_key}_status"] = outcome.status.value

    def _get_agent(self, name: str) -> Optional[BaseAgent]:
        if name not in self._agent_instances or self._agent_instances[name] is None:
            self._agent_instances[name] = get_agent(name)
        return self._agent_instances[name]

    def _build_prediction(
        self,
        prediction_id: str,
        query: str,
        ctx: AgentContext,
        agent_results: List[Dict[str, Any]],
        total_time: float,
    ) -> Dict[str, Any]:
        model_probs = ctx.data.get("model_probabilities", {})
        fixture_resolution = {
            "fixture_id": ctx.data.get("fixture_id"),
            "status": ctx.data.get("fixture_resolution_status", "unknown"),
            "confidence": ctx.data.get("fixture_resolution_confidence", 0.0),
            "confirmation_message": ctx.data.get(
                "fixture_resolution_confirmation_message", ""
            ),
            "alternatives": ctx.data.get("fixture_resolution_alternatives", []),
            "warnings": ctx.data.get("fixture_resolution_warnings", []),
        }
        agent_timings = {
            key: value
            for key, value in ctx.timings.items()
            if not key.startswith("stage_")
        }
        stage_timings = {
            key.replace("stage_", ""): value
            for key, value in ctx.timings.items()
            if key.startswith("stage_")
        }
        timings = build_timing_summary(agent_timings, stage_timings)

        return {
            "id": prediction_id,
            "query": query,
            "home_team": ctx.data.get("team_home", ""),
            "away_team": ctx.data.get("team_away", ""),
            "league": ctx.data.get("league_name", ""),
            "fixture_id": ctx.data.get("fixture_id"),
            "agents": agent_results,
            "executive_summary": ctx.data.get("executive_summary", ""),
            "verdict": ctx.data.get("verdict", ""),
            "tactical_synthesis": ctx.data.get("tactical_synthesis", ""),
            "critical_data_points": ctx.data.get("critical_data_points", []),
            "decisive_factors": ctx.data.get("decisive_factors", []),
            "risk_warnings": ctx.data.get("risk_warnings", []),
            "final_recommendation": ctx.data.get("final_recommendation", ""),
            "conviction_level": ctx.data.get("conviction_level", ""),
            "insights": {
                "context": ctx.data.get("context_narrative", ""),
                "history": ctx.data.get("history_narrative", ""),
                "lineup": ctx.data.get("lineup_narrative", ""),
                "sentiment": ctx.data.get("sentiment_narrative", ""),
                "elo": ctx.data.get("elo_narrative", ""),
                "poisson": ctx.data.get("poisson_narrative", ""),
                "ml": ctx.data.get("ml_narrative", ""),
                "monte_carlo": ctx.data.get("mc_narrative", ""),
                "market": ctx.data.get("market_narrative", ""),
                "risk": ctx.data.get("risk_narrative", ""),
                "professional_verdict": ctx.data.get("professional_verdict", ""),
                "lineup_summary": ctx.data.get("lineup_narrative", ""),
                "history_summary": ctx.data.get("history_narrative", ""),
                "home_injury_count": ctx.data.get("home_injury_count", 0),
                "away_injury_count": ctx.data.get("away_injury_count", 0),
                "home_stats": ctx.data.get("home_stats", {}),
                "away_stats": ctx.data.get("away_stats", {}),
            },
            "probabilities": {
                "home_win": round(model_probs.get("home_win", 0.0) * 100, 1),
                "draw": round(model_probs.get("draw", 0.0) * 100, 1),
                "away_win": round(model_probs.get("away_win", 0.0) * 100, 1),
            },
            "expected_goals": {
                "home": ctx.data.get("expected_goals_home", 0),
                "away": ctx.data.get("expected_goals_away", 0),
            },
            "score_matrix": ctx.data.get("score_matrix", [])[:15],
            "monte_carlo": {
                "simulations": ctx.data.get("mc_simulations", settings.monte_carlo_simulations),
                "home_win_pct": ctx.data.get("mc_home_win", 0),
                "draw_pct": ctx.data.get("mc_draw", 0),
                "away_win_pct": ctx.data.get("mc_away_win", 0),
                "most_likely_score": ctx.data.get("mc_most_likely_score", ""),
                "goal_distribution": ctx.data.get("mc_goal_distribution", {}),
                "score_distribution": ctx.data.get("mc_score_distribution", [])[:10],
            },
            "market_edges": ctx.data.get("market_edges", []),
            "best_bet": ctx.data.get("best_bet"),
            "elo": {
                "home": ctx.data.get("home_elo", 1500),
                "away": ctx.data.get("away_elo", 1500),
                "difference": ctx.data.get("elo_difference", 0),
            },
            "h2h": ctx.data.get("h2h_summary", {}),
            "sentiment": {
                "home": ctx.data.get("sentiment_home", 0),
                "away": ctx.data.get("sentiment_away", 0),
                "narrative": ctx.data.get("sentiment_narrative", ""),
            },
            "fixture_resolution": fixture_resolution,
            "data_quality": {
                "fixture_resolution": ctx.data.get("fixture_resolution_status", "missing"),
                "context": ctx.data.get("context_data_source", "missing"),
                "history": ctx.data.get("history_data_source", "missing"),
                "lineup": ctx.data.get("lineup_data_source", "missing"),
                "odds": ctx.data.get("odds_data_source", "missing"),
                "ml": ctx.data.get("ml_data_source", "missing"),
                "market_edge": ctx.data.get("market_edge_status", "missing"),
            },
            "timings": timings,
            "errors": ctx.errors,
            "total_execution_time_ms": round(total_time, 0),
        }

    @staticmethod
    def _sse_event(event_type: str, data: Dict[str, Any]) -> str:
        return PipelineEvent(event_type=event_type, data=data).to_sse()
