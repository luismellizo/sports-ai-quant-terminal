"""Context Agent schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List


class StandingsData(BaseModel):
    rank: int = 0
    points: int = 0
    played: int = 0
    form: str = ""
    goals_diff: int = 0


class ContextOutput(BaseModel):
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    fixture_id: Optional[int] = None
    league_name: str = ""
    is_rivalry: bool = False
    rivalry_name: Optional[str] = None
    competition_stage: str = "regular_season"
    match_importance: float = 0.5
    context_narrative: str = ""
    home_motivation: str = ""
    away_motivation: str = ""
    key_context_factors: List[str] = Field(default_factory=list)
    tactical_context: str = ""
