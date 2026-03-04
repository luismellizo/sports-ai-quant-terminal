"""
Sports AI — Agent 12: Market Inefficiency Agent
Detects value bets by comparing model probabilities vs market odds.
"""

from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent
from backend.services.odds_service import OddsService
from backend.models.prediction import MarketEdge


class MarketEdgeAgent(BaseAgent):
    """Detects market inefficiencies and value bets."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Aggregate model probabilities from all sources
        model_probs = self._aggregate_probabilities(context)
        market_odds = context.get("market_odds", {})
        implied = context.get("implied_probabilities", {})

        edges = []

        # Check home win
        home_edge = self._calculate_edge(
            "Gana Local",
            model_probs["home_win"],
            implied.get("home", 0.45),
            market_odds.get("home_win", 2.10),
        )
        edges.append(home_edge)

        # Check draw
        draw_edge = self._calculate_edge(
            "Empate",
            model_probs["draw"],
            implied.get("draw", 0.28),
            market_odds.get("draw", 3.30),
        )
        edges.append(draw_edge)

        # Check away win
        away_edge = self._calculate_edge(
            "Gana Visita",
            model_probs["away_win"],
            implied.get("away", 0.27),
            market_odds.get("away_win", 3.50),
        )
        edges.append(away_edge)

        # Sort by edge value
        edges.sort(key=lambda x: x["edge"], reverse=True)

        # Identify value bets (edge > 5%)
        value_bets = [e for e in edges if e["is_value_bet"]]

        return {
            "market_edges": edges,
            "value_bets": value_bets,
            "best_edge": edges[0] if edges else None,
            "model_probabilities": model_probs,
        }

    def _aggregate_probabilities(self, context: Dict) -> Dict[str, float]:
        """
        Aggregate probabilities from multiple models with weights:
        - Poisson: 25%
        - ML Ensemble: 35%
        - Monte Carlo: 25%
        - ELO: 15%
        """
        weights = {
            "poisson": 0.25,
            "ml": 0.35,
            "mc": 0.25,
            "elo": 0.15,
        }

        home_prob = (
            context.get("poisson_home_win", 0.4) * weights["poisson"]
            + context.get("ml_home_win", 0.4) * weights["ml"]
            + (context.get("mc_home_win", 40.0) / 100.0) * weights["mc"]
            + context.get("elo_expected_home", 0.5) * weights["elo"]
        )

        draw_prob = (
            context.get("poisson_draw", 0.25) * weights["poisson"]
            + context.get("ml_draw", 0.3) * weights["ml"]
            + (context.get("mc_draw", 25.0) / 100.0) * weights["mc"]
            + 0.15 * weights["elo"]  # ELO doesn't predict draws well
        )

        away_prob = (
            context.get("poisson_away_win", 0.35) * weights["poisson"]
            + context.get("ml_away_win", 0.3) * weights["ml"]
            + (context.get("mc_away_win", 35.0) / 100.0) * weights["mc"]
            + context.get("elo_expected_away", 0.5) * weights["elo"]
        )

        # Normalize to sum = 1
        total = home_prob + draw_prob + away_prob
        if total > 0:
            home_prob /= total
            draw_prob /= total
            away_prob /= total

        return {
            "home_win": round(home_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_prob, 4),
        }

    @staticmethod
    def _calculate_edge(
        bet_type: str,
        model_prob: float,
        market_prob: float,
        market_odds: float,
    ) -> Dict:
        """Calculate edge for a specific bet type."""
        edge = model_prob - market_prob
        return {
            "bet_type": bet_type,
            "model_probability": round(model_prob, 4),
            "market_probability": round(market_prob, 4),
            "edge": round(edge, 4),
            "odds": market_odds,
            "is_value_bet": edge > 0.05,  # 5% threshold
        }
