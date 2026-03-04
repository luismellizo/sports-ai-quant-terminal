"""
Sports AI — Team Model
Pydantic schemas for team data.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TeamBase(BaseModel):
    """Base team data from API-Football."""
    id: int
    name: str
    code: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None


class TeamStats(BaseModel):
    """Calculated team statistics."""
    team: TeamBase
    form_score: float = Field(0.0, description="Recent form score (0-100)")
    goal_average: float = Field(0.0, description="Average goals per match")
    defense_rating: float = Field(0.0, description="Defensive rating (0-100)")
    attack_rating: float = Field(0.0, description="Attack rating (0-100)")
    momentum: float = Field(0.0, description="Momentum trend (-1 to 1)")
    elo_rating: float = Field(1500.0, description="ELO rating")
    expected_goals: float = Field(0.0, description="Expected goals (xG)")
    clean_sheet_pct: float = Field(0.0, description="Clean sheet percentage")
    wins_last_5: int = 0
    draws_last_5: int = 0
    losses_last_5: int = 0
    goals_scored_last_5: int = 0
    goals_conceded_last_5: int = 0


class TeamSearch(BaseModel):
    """Team search result."""
    id: int
    name: str
    country: str
    logo: Optional[str] = None
    league_id: Optional[int] = None
    league_name: Optional[str] = None
