"""
Sports AI — Agent 9: Poisson Goal Model Agent
Calculates goal distribution using Poisson statistical model.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.simulation_service import SimulationService


class PoissonAgent(BaseAgent):
    """Generates Poisson-based goal predictions and score matrix."""

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        home_stats = context.get("home_stats", {})
        away_stats = context.get("away_stats", {})

        # Calculate expected goals
        lambda_home, lambda_away = self.sim.calculate_expected_goals(
            attack_rating_home=home_stats.get("attack_rating", 50.0),
            defense_rating_away=away_stats.get("defense_rating", 50.0),
            attack_rating_away=away_stats.get("attack_rating", 50.0),
            defense_rating_home=home_stats.get("defense_rating", 50.0),
        )

        # Generate score probability matrix
        score_matrix = self.sim.poisson_score_matrix(lambda_home, lambda_away)

        # Calculate outcome probabilities from matrix
        home_win_prob = sum(s.probability for s in score_matrix if s.home_goals > s.away_goals)
        draw_prob = sum(s.probability for s in score_matrix if s.home_goals == s.away_goals)
        away_win_prob = sum(s.probability for s in score_matrix if s.home_goals < s.away_goals)

        return {
            "expected_goals_home": lambda_home,
            "expected_goals_away": lambda_away,
            "poisson_home_win": round(home_win_prob, 4),
            "poisson_draw": round(draw_prob, 4),
            "poisson_away_win": round(away_win_prob, 4),
            "score_matrix": [s.model_dump() for s in score_matrix[:20]],
        }
