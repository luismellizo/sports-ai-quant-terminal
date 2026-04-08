"""
Sports AI — Feature Agent
Generates the feature vector for ML models from previous agents' data.
"""

from typing import Dict, Any

from backend.agents.core.base import BaseAgent
from backend.agents.core.contracts import AgentContext
from backend.services.feature_engineering import FeatureEngineeringService


class FeatureAgent(BaseAgent):
    name = "FeatureAgent"
    is_critical = False
    timeout_seconds = 15.0

    def __init__(self):
        super().__init__()
        self.fe = FeatureEngineeringService()

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        home_stats = ctx.data.get("home_stats", {})
        away_stats = ctx.data.get("away_stats", {})
        elo_diff = ctx.data.get("elo_difference", 0.0)
        market_movement = ctx.data.get("odds_movement", {}).get("home", 0.0)
        injury_home = ctx.data.get("home_injury_impact", 0.0)
        injury_away = ctx.data.get("away_injury_impact", 0.0)

        features = self.fe.generate_features(
            home_stats=home_stats,
            away_stats=away_stats,
            elo_diff=elo_diff,
            market_movement=market_movement,
            injury_impact_home=injury_home,
            injury_impact_away=injury_away,
        )

        return {"features": features}
