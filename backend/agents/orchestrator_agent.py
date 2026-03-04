"""
Sports AI — Orchestrator Agent
Coordinates the full 13-agent pipeline with SSE event streaming.
"""

import time
import uuid
import json
import asyncio
from typing import Dict, Any, AsyncGenerator, List
from backend.agents.base_agent import BaseAgent
from backend.agents.nlp_agent import NLPAgent
from backend.agents.context_agent import ContextAgent
from backend.agents.history_agent import HistoryAgent
from backend.agents.lineup_agent import LineupAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.odds_agent import OddsAgent
from backend.agents.feature_agent import FeatureAgent
from backend.agents.elo_agent import EloAgent
from backend.agents.poisson_agent import PoissonAgent
from backend.agents.ml_agent import MLAgent
from backend.agents.montecarlo_agent import MonteCarloAgent
from backend.agents.market_edge_agent import MarketEdgeAgent
from backend.agents.risk_agent import RiskAgent
from backend.models.prediction import (
    PredictionResult,
    ProbabilityDistribution,
    ExpectedGoals,
    AgentResult,
    AgentStatus,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Agent pipeline in execution order
PIPELINE: List[BaseAgent] = [
    NLPAgent(),           # 1. Parse input
    ContextAgent(),       # 2. Match context
    HistoryAgent(),       # 3. Historical data
    LineupAgent(),        # 4. Lineup intelligence
    SentimentAgent(),     # 5. News & sentiment
    EloAgent(),           # 6. ELO ratings (needed by Odds & Features)
    OddsAgent(),          # 7. Market odds (uses ELO for dynamic fallback)
    FeatureAgent(),       # 8. Feature engineering
    PoissonAgent(),       # 9. Poisson model
    MLAgent(),            # 10. ML ensemble
    MonteCarloAgent(),    # 11. Monte Carlo sim
    MarketEdgeAgent(),    # 12. Market inefficiency
    RiskAgent(),          # 13. Risk management
]

AGENT_LABELS = {
    "NLPAgent": "Analizando petición",
    "ContextAgent": "Obteniendo contexto del partido",
    "HistoryAgent": "Analizando datos históricos",
    "LineupAgent": "Inteligencia de alineaciones",
    "SentimentAgent": "Análisis de sentimiento y noticias",
    "OddsAgent": "Análisis de cuotas del mercado",
    "EloAgent": "Cálculo de rating ELO",
    "FeatureAgent": "Ingeniería de características",
    "PoissonAgent": "Modelo de goles de Poisson",
    "MLAgent": "Predicción de Machine Learning (Ensemble)",
    "MonteCarloAgent": "Simulación de Monte Carlo",
    "MarketEdgeAgent": "Detección de ineficiencias del mercado",
    "RiskAgent": "Evaluación de riesgo",
}


class OrchestratorAgent:
    """
    Orchestrates the full analysis pipeline.

    Yields SSE events as each agent completes for real-time UI updates.
    """

    def __init__(self):
        self.logger = get_logger("Orchestrator")

    async def run_pipeline(self, query: str) -> AsyncGenerator[str, None]:
        """
        Execute the full agent pipeline with SSE streaming.

        Yields:
            JSON-encoded SSE events for each agent completion.
        """
        prediction_id = str(uuid.uuid4())[:8]
        context: Dict[str, Any] = {"query": query}
        agent_results: List[Dict] = []
        pipeline_start = time.time()

        self.logger.info(f"═══ Starting pipeline {prediction_id} for: '{query}' ═══")

        # Send initial event
        yield self._sse_event("pipeline_start", {
            "id": prediction_id,
            "query": query,
            "total_agents": len(PIPELINE),
        })

        # Execute agents sequentially
        for i, agent in enumerate(PIPELINE):
            agent_name = agent.__class__.__name__
            label = AGENT_LABELS.get(agent_name, agent_name)

            # Send agent start event
            yield self._sse_event("agent_start", {
                "index": i,
                "name": agent_name,
                "label": label,
            })

            # Execute agent
            result = await agent.run(context)

            # Merge results into context
            if result.status == AgentStatus.COMPLETED and result.data:
                context.update(result.data)

            agent_results.append({
                "agent_name": agent_name,
                "label": label,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
                "error": result.error,
            })

            # Send agent complete event
            yield self._sse_event("agent_complete", {
                "index": i,
                "name": agent_name,
                "label": label,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
            })

        # Build final prediction
        total_time = (time.time() - pipeline_start) * 1000
        prediction = self._build_prediction(prediction_id, query, context, agent_results, total_time)

        # Send final result
        yield self._sse_event("pipeline_complete", prediction)

        self.logger.info(f"═══ Pipeline {prediction_id} completed in {total_time:.0f}ms ═══")

    def _build_prediction(
        self,
        prediction_id: str,
        query: str,
        context: Dict,
        agent_results: List[Dict],
        total_time: float,
    ) -> Dict:
        """Build the final prediction result from pipeline context."""
        model_probs = context.get("model_probabilities", {})
        best_bet = context.get("best_bet")

        return {
            "id": prediction_id,
            "query": query,
            "home_team": context.get("team_home", ""),
            "away_team": context.get("team_away", ""),
            "league": context.get("league_name", ""),
            "agents": agent_results,
            "probabilities": {
                "home_win": round(model_probs.get("home_win", 0.33) * 100, 1),
                "draw": round(model_probs.get("draw", 0.33) * 100, 1),
                "away_win": round(model_probs.get("away_win", 0.33) * 100, 1),
            },
            "expected_goals": {
                "home": context.get("expected_goals_home", 0),
                "away": context.get("expected_goals_away", 0),
            },
            "score_matrix": context.get("score_matrix", [])[:15],
            "monte_carlo": {
                "simulations": context.get("mc_simulations", 50000),
                "home_win_pct": context.get("mc_home_win", 0),
                "draw_pct": context.get("mc_draw", 0),
                "away_win_pct": context.get("mc_away_win", 0),
                "most_likely_score": context.get("mc_most_likely_score", ""),
                "goal_distribution": context.get("mc_goal_distribution", {}),
                "score_distribution": context.get("mc_score_distribution", [])[:10],
            },
            "market_edges": context.get("market_edges", []),
            "best_bet": best_bet,
            "elo": {
                "home": context.get("home_elo", 1500),
                "away": context.get("away_elo", 1500),
                "difference": context.get("elo_difference", 0),
            },
            "h2h": context.get("h2h_summary", {}),
            "sentiment": {
                "home": context.get("sentiment_home", 0),
                "away": context.get("sentiment_away", 0),
                "narrative": context.get("sentiment_narrative", ""),
            },
            "total_execution_time_ms": round(total_time, 0),
        }

    @staticmethod
    def _sse_event(event_type: str, data: Dict) -> str:
        """Format data as an SSE event string."""
        return json.dumps({"event": event_type, "data": data})
