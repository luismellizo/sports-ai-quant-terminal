"""ELO Agent schemas."""

from pydantic import BaseModel, Field


class EloOutput(BaseModel):
    home_elo: float = 1500.0
    away_elo: float = 1500.0
    elo_difference: float = 0.0
    elo_expected_home: float = 0.33
    elo_expected_away: float = 0.33
    elo_narrative: str = ""
    competitive_gap: str = ""
