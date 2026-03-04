"""
Sports AI — Odds Model
Pydantic schemas for betting odds and market data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class BookmakerOdds(BaseModel):
    """Odds from a single bookmaker."""
    bookmaker: str
    home_win: float
    draw: float
    away_win: float


class MarketOdds(BaseModel):
    """Aggregated market odds for a fixture."""
    fixture_id: int
    bookmakers: List[BookmakerOdds] = []

    # Calculated fields
    avg_home_win: float = 0.0
    avg_draw: float = 0.0
    avg_away_win: float = 0.0

    # Implied probabilities (with overround removed)
    implied_prob_home: float = 0.0
    implied_prob_draw: float = 0.0
    implied_prob_away: float = 0.0

    # Market movement
    opening_home: Optional[float] = None
    opening_draw: Optional[float] = None
    opening_away: Optional[float] = None
    movement_home: float = 0.0
    movement_draw: float = 0.0
    movement_away: float = 0.0

    @property
    def overround(self) -> float:
        """Calculate market overround (vig)."""
        if self.avg_home_win and self.avg_draw and self.avg_away_win:
            return (1/self.avg_home_win + 1/self.avg_draw + 1/self.avg_away_win) - 1
        return 0.0
