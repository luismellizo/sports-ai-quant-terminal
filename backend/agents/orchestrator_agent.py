"""
Sports AI — Orchestrator Agent
Coordinates the full 14-agent pipeline with SSE event streaming.
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
from backend.agents.synthesis_agent import SynthesisAgent
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
    ContextAgent(),       # 2. Match context + standings + team stats
    HistoryAgent(),       # 3. Historical data + LLM narrative
    LineupAgent(),        # 4. Lineup intelligence + tactical LLM
    SentimentAgent(),     # 5. News & sentiment (LLM)
    EloAgent(),           # 6. ELO ratings + LLM interpretation
    OddsAgent(),          # 7. Market odds
    FeatureAgent(),       # 8. Feature engineering
    PoissonAgent(),       # 9. Poisson model + LLM interpretation
    MLAgent(),            # 10. API-Football predictions + LLM cross-validation
    MonteCarloAgent(),    # 11. Monte Carlo sim + LLM interpretation
    MarketEdgeAgent(),    # 12. Market inefficiency + LLM analysis
    RiskAgent(),          # 13. Risk management + LLM recommendation
    SynthesisAgent(),     # 14. Executive Summary (LLM brain)
]

AGENT_LABELS = {
    "NLPAgent": "Analizando petición",
    "ContextAgent": "Obteniendo contexto competitivo (standings + stats)",
    "HistoryAgent": "Analizando datos históricos con IA",
    "LineupAgent": "Inteligencia táctica de alineaciones",
    "SentimentAgent": "Análisis de sentimiento y noticias",
    "EloAgent": "Cálculo e interpretación de rating ELO",
    "OddsAgent": "Análisis de cuotas del mercado",
    "FeatureAgent": "Ingeniería de características",
    "PoissonAgent": "Modelo probabilístico de Poisson",
    "MLAgent": "Cross-validación con predicciones de API-Football",
    "MonteCarloAgent": "Simulación Monte Carlo (50K sims)",
    "MarketEdgeAgent": "Detección de ineficiencias del mercado",
    "RiskAgent": "Evaluación profesional de riesgo",
    "SynthesisAgent": "Generando Executive Summary con IA",
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

            # ── Executive Summary (from SynthesisAgent) ──
            "executive_summary": context.get("executive_summary", ""),
            "verdict": context.get("verdict", ""),
            "tactical_synthesis": context.get("tactical_synthesis", ""),
            "critical_data_points": context.get("critical_data_points", []),
            "decisive_factors": context.get("decisive_factors", []),
            "risk_warnings": context.get("risk_warnings", []),
            "final_recommendation": context.get("final_recommendation", ""),
            "conviction_level": context.get("conviction_level", ""),

            # ── Agent Narratives ──
            "insights": {
                "context": context.get("context_narrative", ""),
                "history": context.get("history_narrative", ""),
                "lineup": context.get("lineup_narrative", ""),
                "sentiment": context.get("sentiment_narrative", ""),
                "elo": context.get("elo_narrative", ""),
                "poisson": context.get("poisson_narrative", ""),
                "ml": context.get("ml_narrative", ""),
                "monte_carlo": context.get("mc_narrative", ""),
                "market": context.get("market_narrative", ""),
                "risk": context.get("risk_narrative", ""),
                "professional_verdict": context.get("professional_verdict", ""),

                # Legacy fields for frontend compatibility
                "lineup_summary": context.get("lineup_narrative", ""),
                "history_summary": context.get("history_narrative", ""),

                "home_injury_count": context.get("home_injury_count", 0),
                "away_injury_count": context.get("away_injury_count", 0),
                "home_stats": {
                    "wins_last_5": context.get("home_stats", {}).get("wins_last_5", 0),
                    "draws_last_5": context.get("home_stats", {}).get("draws_last_5", 0),
                    "losses_last_5": context.get("home_stats", {}).get("losses_last_5", 0),
                    "goals_scored_last_5": context.get("home_stats", {}).get("goals_scored_last_5", 0),
                    "goals_conceded_last_5": context.get("home_stats", {}).get("goals_conceded_last_5", 0),
                },
                "away_stats": {
                    "wins_last_5": context.get("away_stats", {}).get("wins_last_5", 0),
                    "draws_last_5": context.get("away_stats", {}).get("draws_last_5", 0),
                    "losses_last_5": context.get("away_stats", {}).get("losses_last_5", 0),
                    "goals_scored_last_5": context.get("away_stats", {}).get("goals_scored_last_5", 0),
                    "goals_conceded_last_5": context.get("away_stats", {}).get("goals_conceded_last_5", 0),
                },
            },

            # ── Detailed Agent Data ──
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
