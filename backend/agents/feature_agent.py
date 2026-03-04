"""
Sports AI — Agent 7: Feature Engineering Agent
Generates the feature vector for ML models from previous agents' data.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.feature_engineering import FeatureEngineeringService


class FeatureAgent(BaseAgent):
    """Assembles the complete feature vector from pipeline context."""

    def __init__(self):
        super().__init__()
        self.fe = FeatureEngineeringService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})
        elo_diff = context.get("elo_difference", 0.0)
        market_movement = context.get("odds_movement", {}).get("home", 0.0)
        injury_home = context.get("home_injury_impact", 0.0)
        injury_away = context.get("away_injury_impact", 0.0)

        features = self.fe.generate_features(
            home_stats=home_stats,
            away_stats=away_stats,
            elo_diff=elo_diff,
            market_movement=market_movement,
            injury_impact_home=injury_home,
            injury_impact_away=injury_away,
        )

        return {"features": features}
