"""Poisson Agent schemas."""

from pydantic import BaseModel, Field
from typing import List


class ScoreProb(BaseModel):
    home_goals: int
    away_goals: int
    probability: float


class PoissonOutput(BaseModel):
    expected_goals_home: float = 0.0
    expected_goals_away: float = 0.0
    poisson_home_win: float = 0.33
    poisson_draw: float = 0.33
    poisson_away_win: float = 0.33
    score_matrix: List[ScoreProb] = Field(default_factory=list)
    poisson_over_25: float = 0.0
    poisson_btts: float = 0.0
    poisson_narrative: str = ""
