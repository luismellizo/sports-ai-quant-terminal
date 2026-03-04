"""
Sports AI — Agent 11: Monte Carlo Simulation Agent
Runs 50,000 match simulations using Poisson distribution.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent
from backend.services.simulation_service import SimulationService


class MonteCarloAgent(BaseAgent):
    """Runs Monte Carlo match simulations."""

    def __init__(self):
        super().__init__()
        self.sim = SimulationService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        lambda_home = context.get("expected_goals_home", 1.5)
        lambda_away = context.get("expected_goals_away", 1.1)

        # Run simulation
        result = self.sim.simulate_match(lambda_home, lambda_away)

        return {
            "mc_simulations": result.simulations,
            "mc_home_win": result.home_win_pct,
            "mc_draw": result.draw_pct,
            "mc_away_win": result.away_win_pct,
            "mc_avg_goals_home": result.avg_goals_home,
            "mc_avg_goals_away": result.avg_goals_away,
            "mc_most_likely_score": result.most_likely_score,
            "mc_goal_distribution": result.goal_distribution,
            "mc_score_distribution": [s.model_dump() for s in result.score_distribution[:15]],
        }
