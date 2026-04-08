"""Odds Agent schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class MarketOdds(BaseModel):
    home_win: float = 0.0
    draw: float = 0.0
    away_win: float = 0.0


class ImpliedProbabilities(BaseModel):
    home: float = 0.0
    draw: float = 0.0
    away: float = 0.0


class OddsOutput(BaseModel):
    market_odds: MarketOdds = Field(default_factory=MarketOdds)
    implied_probabilities: ImpliedProbabilities = Field(
        default_factory=ImpliedProbabilities
    )
    overround: Optional[float] = None
    bookmaker_count: int = 0
    odds_data_available: bool = False
