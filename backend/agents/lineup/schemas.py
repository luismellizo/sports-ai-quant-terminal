"""Lineup Agent schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional


class LineupData(BaseModel):
    formation: str = "Unknown"
    coach: str = "Unknown"
    starting_xi: List[dict] = Field(default_factory=list)
    substitutes: List[dict] = Field(default_factory=list)


class InjuryData(BaseModel):
    player: str
    type: str
    reason: str


class LineupOutput(BaseModel):
    home_lineup: LineupData = Field(default_factory=LineupData)
    away_lineup: LineupData = Field(default_factory=LineupData)
    home_injury_count: int = 0
    away_injury_count: int = 0
    lineup_narrative: str = ""
    tactical_advantage: str = ""
