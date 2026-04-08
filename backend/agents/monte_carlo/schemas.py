"""Monte Carlo Agent schemas."""

from pydantic import BaseModel, Field
from typing import Dict, List


class MonteCarloResult(BaseModel):
    simulations: int = 50000
    home_win_pct: float = 0.0
    draw_pct: float = 0.0
    away_win_pct: float = 0.0
    avg_goals_home: float = 0.0
    avg_goals_away: float = 0.0
    most_likely_score: str = "0-0"
    goal_distribution: Dict[str, float] = Field(default_factory=dict)
    score_distribution: List[dict] = Field(default_factory=list)


class MonteCarloOutput(BaseModel):
    mc_simulations: int = 50000
    mc_home_win: float = 0.0
    mc_draw: float = 0.0
    mc_away_win: float = 0.0
    mc_most_likely_score: str = "0-0"
    mc_narrative: str = ""
