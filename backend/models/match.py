"""
Sports AI — Match Model
Pydantic schemas for match/fixture data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.models.team import TeamBase


class MatchFixture(BaseModel):
    """Match fixture from API-Football."""
    fixture_id: int
    date: datetime
    timestamp: int
    venue: Optional[str] = None
    referee: Optional[str] = None
    status: Optional[str] = None


class MatchLeague(BaseModel):
    """League information for a match."""
    id: int
    name: str
    country: Optional[str] = None
    season: Optional[int] = None
    round: Optional[str] = None
    logo: Optional[str] = None


class MatchResult(BaseModel):
    """Historical match result."""
    fixture_id: int
    date: datetime
    home_team: TeamBase
    away_team: TeamBase
    goals_home: int
    goals_away: int
    league: Optional[MatchLeague] = None


class MatchContext(BaseModel):
    """Full match context for analysis."""
    fixture: MatchFixture
    league: MatchLeague
    home_team: TeamBase
    away_team: TeamBase

    # Context metadata
    is_derby: bool = False
    is_rivalry: bool = False
    competition_stage: Optional[str] = None
    match_importance: float = Field(0.5, ge=0, le=1, description="Match importance 0-1")

    # Historical data
    h2h_matches: List[MatchResult] = []
    home_recent: List[MatchResult] = []
    away_recent: List[MatchResult] = []
