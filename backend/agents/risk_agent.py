"""
Sports AI — Agent 13: Risk Management Agent
Calculates recommended stake using Kelly Criterion and produces final recommendation.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.odds_service import OddsService
from backend.models.prediction import (
    BetRecommendation,
    ConfidenceLevel,
    RiskLevel,
)


class RiskAgent(BaseAgent):
    """Final agent: calculates stake, confidence, and risk level."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        model_probs = context.get("model_probabilities", {})
        market_odds = context.get("market_odds", {})
        edges = context.get("market_edges", [])
        best_edge = context.get("best_edge")
        team_home = context.get("team_home", "Home")
        team_away = context.get("team_away", "Away")
        match_importance = context.get("match_importance", 0.5)

        if not best_edge:
            return {"best_bet": None}

        # Determine best bet
        bet_type = best_edge["bet_type"]
        if bet_type == "Home Win" or bet_type == "Gana Local":
            bet_type = "Gana Local"
            team = team_home
            prob = model_probs.get("home_win", 0.4)
            odds = market_odds.get("home_win", 2.10)
        elif bet_type == "Away Win" or bet_type == "Gana Visita":
            bet_type = "Gana Visita"
            team = team_away
            prob = model_probs.get("away_win", 0.3)
            odds = market_odds.get("away_win", 3.50)
        else:  # Draw
            bet_type = "Empate"
            team = "Empate"
            prob = model_probs.get("draw", 0.25)
            odds = market_odds.get("draw", 3.30)

        # Kelly Criterion
        kelly_stake = OddsService.kelly_criterion(prob, odds, fraction=0.25)

        # Confidence score (0-10)
        edge = best_edge["edge"]
        confidence_score = self._calculate_confidence(
            edge=edge,
            prob=prob,
            match_importance=match_importance,
            bookmaker_count=context.get("bookmaker_count", 0),
        )

        # Risk level
        risk_level = self._determine_risk_level(kelly_stake, edge)

        # Confidence label
        if confidence_score >= 8.0:
            confidence = ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 6.5:
            confidence = ConfidenceLevel.HIGH
        elif confidence_score >= 4.5:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        recommendation = BetRecommendation(
            bet_type=bet_type,
            team=team,
            probability=round(prob, 4),
            market_odds=odds,
            value_edge=round(edge, 4),
            recommended_stake_pct=round(kelly_stake * 100, 2),
            confidence=confidence,
            risk_level=risk_level,
            confidence_score=round(confidence_score, 1),
        )

        return {
            "best_bet": recommendation.model_dump(),
        }

    @staticmethod
    def _calculate_confidence(
        edge: float,
        prob: float,
        match_importance: float,
        bookmaker_count: int,
    ) -> float:
        """Calculate confidence score on 0-10 scale."""
        score = 5.0  # Base

        # Edge contribution (+/- 2 points)
        score += min(2.0, max(-2.0, edge * 20))

        # Probability certainty (+/- 1.5 points)
        if prob > 0.6:
            score += 1.5
        elif prob > 0.5:
            score += 0.8
        elif prob < 0.3:
            score -= 0.5

        # Match importance (+/- 0.5)
        score += (match_importance - 0.5) * 1.0

        # Market data quality (+/- 1.0)
        if bookmaker_count >= 10:
            score += 1.0
        elif bookmaker_count >= 5:
            score += 0.5
        elif bookmaker_count == 0:
            score -= 1.0

        return max(0.0, min(10.0, score))

    @staticmethod
    def _determine_risk_level(kelly_stake: float, edge: float) -> RiskLevel:
        """Determine risk level based on stake and edge."""
        if kelly_stake <= 0.01 or edge <= 0:
            return RiskLevel.EXTREME
        elif kelly_stake <= 0.02 and edge < 0.05:
            return RiskLevel.HIGH
        elif kelly_stake <= 0.04:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
