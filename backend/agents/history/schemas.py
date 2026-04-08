"""History Agent schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional


class TeamResults(BaseModel):
    fixture_id: int
    date: str
    goals_home: int
    goals_away: int
    is_home: bool


class H2HSummary(BaseModel):
    total_matches: int = 0
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0


class HistoryOutput(BaseModel):
    home_stats: dict = Field(default_factory=dict)
    away_stats: dict = Field(default_factory=dict)
    h2h_summary: H2HSummary = Field(default_factory=H2HSummary)
    history_narrative: str = ""
    history_data_available: bool = False
