"""
Sports AI — Agent 10: Machine Learning Agent
Runs ensemble ML model (LogReg + RF + XGBoost) for match prediction.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.training_service import TrainingService


class MLAgent(BaseAgent):
    """Generates ML ensemble predictions."""

    def __init__(self):
        super().__init__()
        self.training = TrainingService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        features = context.get("features", {})

        if not features:
            self.logger.warning("No features available — skipping ML prediction")
            return {
                "ml_home_win": 0.40,
                "ml_draw": 0.30,
                "ml_away_win": 0.30,
            }

        # Get ensemble prediction
        prediction = self.training.predict(features)

        return {
            "ml_home_win": prediction.get("home_win", 0.33),
            "ml_draw": prediction.get("draw", 0.33),
            "ml_away_win": prediction.get("away_win", 0.33),
        }
